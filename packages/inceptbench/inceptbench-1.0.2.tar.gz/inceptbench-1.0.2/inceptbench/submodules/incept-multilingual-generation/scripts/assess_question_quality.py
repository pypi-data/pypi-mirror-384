#!/usr/bin/env python3
"""
Assess question quality based on logical completeness.

Usage:
    python scripts/assess_question_quality.py --limit 100
    python scripts/assess_question_quality.py --source textbook
    python scripts/assess_question_quality.py --grade 3

Requirements:
    pip install supabase python-dotenv pydantic tqdm

Environment variables (in .env):
    SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
    SUPABASE_SERVICE_KEY=[YOUR-SERVICE-ROLE-KEY]
    OPENAI_API_KEY=[YOUR-OPENAI-KEY]
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel, Field
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llms import produce_structured_response

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


class QualityAssessment(BaseModel):
    """Quality assessment for a single question."""
    question_id: str = Field(description="The question ID being assessed")
    quality_score: float = Field(description="Quality score from 0-10, where 10 is perfect. Based on logical completeness: is the question complete and coherent? Penalize for truncation, cut-off text, missing context, or logical inconsistencies.")
    requires_image: bool = Field(description="True if the question requires an image/diagram to be complete (e.g., 'look at the figure', 'based on the graph'). This does NOT lower the quality score.")
    is_complete: bool = Field(description="True if the question is logically complete and not truncated")
    reasoning: str = Field(description="Brief explanation of the quality score (2-3 sentences)")


class QualityAssessmentBatch(BaseModel):
    """Batch of quality assessments."""
    assessments: List[QualityAssessment]


def assess_question_quality(question: dict) -> Optional[QualityAssessment]:
    """
    Assess the quality of a single question using GPT-4o.

    Args:
        question: Question dict from database

    Returns:
        QualityAssessment object or None if assessment fails
    """
    question_id = question["id"]
    question_text = question.get("question_en") or question.get("question_ar") or ""
    answer_text = question.get("answer_en") or question.get("answer_ar") or ""

    # Build context
    context_parts = []
    if question.get("domain"):
        context_parts.append(f"Domain: {question['domain']}")
    if question.get("unit_name"):
        context_parts.append(f"Unit: {question['unit_name']}")
    if question.get("lesson_title"):
        context_parts.append(f"Lesson: {question['lesson_title']}")

    context = " | ".join(context_parts) if context_parts else "No context"

    # Prepare input for LLM
    llm_input = {
        "question_id": question_id,
        "grade": question.get("grade"),
        "context": context,
        "question_text": question_text,
        "answer_text": answer_text,
        "has_images": bool(question.get("images"))
    }

    system_instructions = """You are an expert educational content quality assessor. Your task is to evaluate whether a question is logically complete and coherent.

Quality scoring criteria (0-10):
- **10**: Perfect - Question is complete, clear, coherent, and self-contained
- **8-9**: Good - Question is complete with minor clarity issues
- **6-7**: Acceptable - Question is mostly complete but has some ambiguity
- **4-5**: Poor - Question has significant issues (vague, unclear) but is not truncated
- **2-3**: Very Poor - Question appears truncated or has missing critical information
- **0-1**: Incomplete - Question is clearly cut off, truncated, or unintelligible

Important notes:
- Questions that reference "the figure", "the diagram", "the image", etc. are FINE if they have images field populated
- Such questions should get high scores (8-10) and requires_image=true
- Only penalize for logical incompleteness, truncation, or incoherence
- Do NOT penalize for difficulty, pedagogical quality, or curriculum alignment
- Focus ONLY on: Is this question complete and understandable?

Common signs of truncation/incompleteness:
- Text ends mid-sentence
- Missing punctuation at end
- Garbled or nonsensical text
- Question asks about something not mentioned
- Answer choices cut off (if applicable)"""

    user_content = f"""Assess this question for logical completeness:

Grade: {llm_input['grade']}
Context: {llm_input['context']}
Has Images: {llm_input['has_images']}

Question:
{llm_input['question_text']}

Answer:
{llm_input['answer_text']}"""

    try:
        result = produce_structured_response(
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_content}
            ],
            structure_model=QualityAssessmentBatch,
            model="gpt-4o",
            temperature=0.0,
            provider="openai"
        )

        if result.assessments and len(result.assessments) > 0:
            return result.assessments[0]
        else:
            logger.warning(f"No assessment returned for question {question_id}")
            return None

    except Exception as e:
        logger.error(f"Failed to assess question {question_id}: {e}")
        return None


def update_question_quality(question_id: str, assessment: QualityAssessment):
    """Update question in database with quality assessment."""
    # Create a new Supabase client for this update to avoid connection pooling issues
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # Fetch existing raw_data to preserve it
        existing = client.table("extracted_questions").select("raw_data").eq("id", question_id).execute()
        existing_raw_data = existing.data[0].get("raw_data", {}) if existing.data else {}

        # Merge quality assessment into raw_data
        updated_raw_data = {
            **existing_raw_data,
            "quality_assessment": {
                "quality_score": assessment.quality_score,
                "requires_image": assessment.requires_image,
                "is_complete": assessment.is_complete,
                "reasoning": assessment.reasoning,
                "assessed_at": datetime.utcnow().isoformat()
            }
        }

        update_data = {
            "quality_score": assessment.quality_score,
            "raw_data": updated_raw_data
        }

        client.table("extracted_questions").update(update_data).eq("id", question_id).execute()

    except Exception as e:
        logger.error(f"Failed to update question {question_id}: {e}")
        raise


def fetch_questions_to_assess(
    limit: Optional[int] = None,
    source: str = "both",
    grade: Optional[int] = None
) -> List[dict]:
    """Fetch questions from Supabase that need quality assessment."""

    query = supabase.table("extracted_questions").select("*")

    # Filter by source
    if source == "athena":
        query = query.eq("source_type", "athena_api")
    elif source == "textbook":
        query = query.eq("source_type", "textbook_pdf")

    # Filter by grade
    if grade:
        query = query.eq("grade", grade)

    # Only assess questions without quality scores
    query = query.is_("quality_score", "null")

    # Order by created_at (desc=True means descending)
    query = query.order("created_at", desc=True)

    # Apply limit with pagination if needed
    all_questions = []
    if limit:
        page_size = 1000
        offset = 0

        while len(all_questions) < limit:
            batch_size = min(page_size, limit - len(all_questions))

            batch_query = query.range(offset, offset + batch_size - 1)
            response = batch_query.execute()
            batch = response.data

            if not batch:
                break

            all_questions.extend(batch)
            offset += len(batch)

            if len(batch) < batch_size:
                break
    else:
        # No limit - fetch all (up to reasonable amount)
        response = query.limit(10000).execute()
        all_questions = response.data

    logger.info(f"Fetched {len(all_questions)} questions to assess")
    return all_questions


def main():
    parser = argparse.ArgumentParser(description="Assess question quality based on logical completeness")
    parser.add_argument("--limit", type=int, help="Number of questions to assess (default: all unassessed)")
    parser.add_argument("--source", type=str, default="both", choices=["athena", "textbook", "both"],
                        help="Which source to process")
    parser.add_argument("--grade", type=int, help="Filter by grade")
    parser.add_argument("--workers", type=int, default=10, help="Number of concurrent workers (default: 10)")

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("QUESTION QUALITY ASSESSMENT STARTED")
    logger.info("="*60)

    if args.limit:
        logger.info(f"Assessing up to {args.limit} questions")
    else:
        logger.info("Assessing all unassessed questions")

    # Fetch questions
    questions = fetch_questions_to_assess(
        limit=args.limit,
        source=args.source,
        grade=args.grade
    )

    if not questions:
        logger.info("No questions to assess")
        return

    stats = {
        "total": len(questions),
        "assessed": 0,
        "failed": 0,
        "high_quality": 0,  # 8-10
        "medium_quality": 0,  # 5-7
        "low_quality": 0,  # 0-4
        "requires_image": 0
    }

    def process_question(question):
        """Process a single question."""
        assessment = assess_question_quality(question)

        if assessment:
            update_question_quality(question["id"], assessment)

            # Categorize by quality
            if assessment.quality_score >= 8:
                category = "high_quality"
            elif assessment.quality_score >= 5:
                category = "medium_quality"
            else:
                category = "low_quality"

            return ("success", category, assessment.requires_image)
        else:
            return ("failed", None, False)

    # Process questions in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_question, q): q for q in questions}

        with tqdm(total=len(futures), desc="Assessing quality", unit=" questions", ncols=100) as pbar:
            for future in as_completed(futures):
                status, category, requires_image = future.result()

                if status == "success":
                    stats["assessed"] += 1
                    if category:
                        stats[category] += 1
                    if requires_image:
                        stats["requires_image"] += 1
                else:
                    stats["failed"] += 1

                pbar.update(1)
                pbar.set_postfix_str(f"✓ {stats['assessed']} | ✗ {stats['failed']}")

    # Final Summary
    logger.info("\n" + "="*60)
    logger.info("QUALITY ASSESSMENT COMPLETE")
    logger.info("="*60)
    logger.info(f"Total processed: {stats['total']}")
    logger.info(f"Successfully assessed: {stats['assessed']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info("")
    logger.info("Quality Distribution:")
    logger.info(f"  High Quality (8-10): {stats['high_quality']} ({stats['high_quality']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    logger.info(f"  Medium Quality (5-7): {stats['medium_quality']} ({stats['medium_quality']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    logger.info(f"  Low Quality (0-4): {stats['low_quality']} ({stats['low_quality']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    logger.info(f"  Requires Image: {stats['requires_image']} ({stats['requires_image']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    logger.info("="*60)


if __name__ == "__main__":
    main()
