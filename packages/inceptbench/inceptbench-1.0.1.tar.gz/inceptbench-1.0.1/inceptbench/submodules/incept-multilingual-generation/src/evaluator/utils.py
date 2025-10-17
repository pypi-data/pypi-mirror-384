#!/usr/bin/env python3
"""
EduBench-style Evaluator v2
Normalizes GeneratedQuestion objects to EduBench format and evaluates with 12-dimension rubric
"""

from __future__ import annotations
import os
import sys
import json
import re
import argparse
import random
import statistics
import time
import logging
from typing import Optional, List, Dict, Any, Literal, Tuple

from src.dto.question_generation import GenerateQuestionResponse, GenerateQuestionsRequest, GeneratedQuestion, SkillInfo
# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)

try:
    from datasets import load_dataset
except Exception:
    load_dataset = None  # Optional for baseline sampling


# -----------------------------
# EduBench metrics configuration
# -----------------------------

# 12 EduBench sub-metrics
METRICS = [
    # Scenario / Instructional Quality
    "IFTC",  # Instruction Following & Task Completion
    "RTC",   # Role & Tone Consistency
    "CRSC",  # Content Relevance & Scope Control
    "SEI",   # Scenario Element Integration
    # Factual & Reasoning Accuracy
    "BFA",   # Basic Factual Accuracy
    "DKA",   # Domain Knowledge Accuracy
    "RPR",   # Reasoning Process Rigor
    "EICP",  # Error Identification & Correction Precision
    # Pedagogical Effectiveness
    "CSI",   # Clarity, Simplicity & Inspiration
    "MGP",   # Motivation, Guidance & Positive feedback
    "PAS",   # Personalization, Adaptation & Learning Support
    "HOTS",  # Higher-Order Thinking & Skill Development
]

# Dynamic weights for QG scenario
QG_WEIGHTS = {
    "IFTC": 1.0, "RTC": 0.5, "CRSC": 1.0, "SEI": 0.5,
    "BFA": 1.0, "DKA": 1.0, "RPR": 1.5, "EICP": 0.0,
    "CSI": 0.7, "MGP": 0.3, "PAS": 0.3, "HOTS": 1.0
}

DEFAULT_SCENARIO = "QG"

def judge_prompt_for_qg() -> str:
    """Generate the evaluation prompt for QG scenario"""
    return (
        "You are an EduBench-style evaluator for the Question Generation (QG) scenario.\n"
        "Given a *prompt* (the instruction the generator followed) and a *response* (the generated question), "
        "score the response on the following 12 metrics from 1–10 (10 is best). Keep scores integer.\n\n"
        "The response should contain:\n"
        "- A clear educational question\n"
        "- An answer (may be a letter like 'A' or the actual answer)\n"
        "- A step-by-step explanation (may be in JSON format with scaffolding steps)\n\n"
        "Instructional Quality:\n"
        "• IFTC: Did it follow the instruction and complete the task (generate the question correctly, with answer & explanation)?\n"
        "• RTC: Role/tone appropriateness for an educator and the target grade.\n"
        "• CRSC: Topic relevance and scope control vs. subject/difficulty/grade.\n"
        "• SEI: Effective use of scenario elements (e.g., grade, difficulty).\n\n"
        "Factual & Reasoning Accuracy:\n"
        "• BFA: Basic factual correctness of content.\n"
        "• DKA: Domain knowledge accuracy and appropriateness.\n"
        "• RPR: Reasoning rigor (e.g., explanation logic, solution steps if implied).\n"
        "• EICP: Error identification & correction precision (mostly N/A for QG; if not applicable use 1).\n\n"
        "Pedagogical Effectiveness:\n"
        "• CSI: Clarity/conciseness; easy for the target learner.\n"
        "• MGP: Constructive guidance/feedback tone.\n"
        "• PAS: Adaptation to grade/level; learning support.\n"
        "• HOTS: Encouragement of higher-order thinking (beyond recall).\n\n"
        "Return STRICT JSON with keys: IFTC, RTC, CRSC, SEI, BFA, DKA, RPR, EICP, CSI, MGP, PAS, HOTS, and comments (string)."
    )

def extract_json(s: str) -> Dict[str, Any]:
    """Extract JSON from string"""
    m = re.search(r"\{.*\}", s, flags=re.S)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}

# -----------------------------
# Normalization to EduBench format
# -----------------------------

def normalize_generated_question_to_edubench_qg(req: GenerateQuestionsRequest, gq: GeneratedQuestion) -> Dict[str, Any]:
    """
    Convert a GeneratedQuestion to EduBench-style QG item format
    """
    subj = req.subject or "general"
    diff = gq.difficulty or (req.difficulty or "mixed")
    grade = req.grade
    lang = (req.language or "english").lower()

    # Map grade to level
    if grade <= 5:
        level = "Elementary School"
    elif grade <= 8:
        level = "Middle School"
    else:
        level = "High School"

    # Build the information dict in the expected format
    info = {
        "Subject": subj.capitalize(),
        "Level": level,
        "Question": gq.question.strip()
    }

    # Build the prompt in the expected format
    instruction = (
        f'{json.dumps(info)}\n'
        f'Question: {gq.question.strip()}\n'
        f'Student\'s Answer: {gq.answer.strip()}\n'
        f'Please provide "Score", "Scoring Details", and "Personalized Feedback" based on the question and student\'s answer, in JSON format.'
    )

    # Handle explanation - it might be JSON scaffolding data for reasoning
    reasoning_text = ""
    try:
        scaffolding_data = json.loads(gq.explanation)
        if isinstance(scaffolding_data, list):
            # Convert scaffolding steps to reasoning
            reasoning_parts = []
            for i, step in enumerate(scaffolding_data, 1):
                if isinstance(step, dict):
                    title = step.get('title', f'Step {i}')
                    content = step.get('content', '')
                    reasoning_parts.append(f"{i}. {title}: {content}")
            reasoning_text = "\\n".join(reasoning_parts)
        else:
            reasoning_text = str(scaffolding_data)
    except (json.JSONDecodeError, TypeError):
        # If not JSON, use as-is
        reasoning_text = gq.explanation.strip()

    # Create response in the expected JSON format
    response_obj = {
        "Score": 1,  # Placeholder score
        "Scoring_Details": f"Answer evaluation for grade {grade} {subj} question.",
        "Personalized_Feedback": f"This question tests {subj} concepts at the {level.lower()} level."
    }

    response_text = f"```json\n{json.dumps(response_obj, indent=2)}\n```"

    item = {
        "information": info,
        "prompt": instruction,
        "model_predictions": [
            {
                "model": "qwen2.5-14b-instruct",
                "reasoning": reasoning_text if reasoning_text else None,
                "response": response_text
            }
        ]
    }
    return item

# -----------------------------
# Baseline sampling from EduBench
# -----------------------------

def sample_qg_baselines(n: int, seed: int = 0) -> List[Tuple[str, str]]:
    """
    Sample QG baselines from DirectionAI/EduBench dataset
    """
    if load_dataset is None:
        raise RuntimeError("`datasets` not installed. Run: pip install datasets")

    url = "https://huggingface.co/datasets/DirectionAI/EduBench/resolve/main/en_data/QG.jsonl"
    ds = load_dataset("json", data_files=url, split="train")
    total = len(ds)
    idxs = list(range(total))
    random.Random(seed).shuffle(idxs)
    idxs = idxs[:max(0, min(n, total))]

    pairs: List[Tuple[str,str]] = []
    for i in idxs:
        row = ds[i]
        prompt = row.get("prompt") or ""
        preds = row.get("model_predictions") or []
        if isinstance(preds, list) and preds:
            r = preds[0]
            resp = r.get("response") or ""
            if prompt and resp:
                pairs.append((prompt, resp))
    return pairs

def percentile(x: float, population: List[float]) -> float:
    """Calculate percentile of x in population"""
    if not population:
        return 0.0
    less = sum(1 for v in population if v <= x)
    return round(100.0 * less / len(population), 2)

# -----------------------------
# IO and main runner
# -----------------------------

def load_reqresp(path: str) -> Tuple[GenerateQuestionsRequest, GenerateQuestionResponse]:
    """Load request/response from JSON file"""
    with open(path, "r", encoding="utf-8") as f:
        blob = json.load(f)

    if "request" not in blob or "response" not in blob:
        raise ValueError("Input JSON must have top-level keys: 'request' and 'response'.")

    req = GenerateQuestionsRequest(**blob["request"])

    # Parse response
    raw_resp = blob["response"]
    data = []
    for q in raw_resp["data"]:
        data.append(GeneratedQuestion(**q))
    resp = GenerateQuestionResponse(
        data=data,
        request_id=raw_resp["request_id"],
        total_questions=raw_resp["total_questions"],
        grade=raw_resp["grade"]
    )
    return req, resp

def load_from_postgres(
    limit: int = 50,
    grade: Optional[int] = None,
    subject: Optional[str] = None,
    hours_ago: int = 24,
    extracted_by_model: Optional[str] = 'orchestrator-pipeline'
) -> Tuple[GenerateQuestionsRequest, GenerateQuestionResponse]:
    """
    Load recent questions from PostgreSQL database that were uploaded by DevQuestionUploader

    Args:
        limit: Maximum number of questions to retrieve
        grade: Filter by grade level (optional)
        subject: Filter by subject area (optional)
        hours_ago: Get questions from last N hours (default 24)

    Returns:
        Tuple of (GenerateQuestionsRequest, GenerateQuestionResponse) in standard format
    """
    import psycopg2
    import uuid
    from datetime import datetime, timedelta

    logger.info("🗄️  Loading questions from PostgreSQL database...")
    logger.info(f"   Filters: limit={limit}, grade={grade}, subject={subject}, hours_ago={hours_ago}")

    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        raise RuntimeError("POSTGRES_URI environment variable not set")

    logger.info(f"📡 Connecting to database: {postgres_uri[:50]}...")
    try:
        conn = psycopg2.connect(postgres_uri)
        cur = conn.cursor()
        logger.info("✓ Database connection successful")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {type(e).__name__}: {e}")
        raise

    # Build query with optional filters
    query = """
        SELECT
            question_text,
            question_text_arabic,
            correct_answer,
            answer_explanation,
            difficulty_level,
            grade_level,
            subject_area,
            broad_topic,
            subtopic,
            scaffolding,
            language
        FROM uae_educational_questions_cleaned_duplicate
        WHERE created_at > NOW() - INTERVAL '%s hours'
        AND extracted_by_model = %s
        AND scaffolding IS NOT NULL
    """
    params = [hours_ago, extracted_by_model]

    if grade is not None:
        query += " AND normalized_grade = %s"
        params.append(grade)

    if subject:
        query += " AND subject_area ILIKE %s"
        params.append(f"%{subject}%")

    query += " ORDER BY created_at DESC LIMIT %s"
    params.append(limit)

    logger.info("🔍 Executing database query...")

    start_time = time.time()
    try:
        cur.execute(query, params)
        rows = cur.fetchall()
        elapsed = time.time() - start_time
        logger.info(f"✓ Query executed in {elapsed:.2f}s, retrieved {len(rows)} rows")
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Query failed after {elapsed:.2f}s: {type(e).__name__}: {e}")
        raise
    finally:
        cur.close()
        conn.close()
        logger.info("✓ Database connection closed")

    if not rows:
        logger.error(f"❌ No questions found in database for last {hours_ago} hours")
        raise ValueError(f"No questions found in database for last {hours_ago} hours")

    # Convert DB rows to GeneratedQuestion objects
    logger.info("🔄 Converting database rows to GeneratedQuestion objects...")
    questions = []
    detected_grade = None
    detected_subject = None
    detected_language = None

    for i, row in enumerate(rows):
        if i == 0:
            logger.info(f"   Processing {len(rows)} database rows...")
        elif i % 10 == 0:
            logger.info(f"   Processed {i}/{len(rows)} questions...")
        (q_text, q_text_ar, answer, explanation, difficulty,
         grade_str, subject_area, broad_topic, subtopic, scaffolding,lang ) = row

        # Use first non-null values for request metadata
        if detected_grade is None and grade_str:
            detected_grade = int(grade_str)
        if detected_subject is None and subject_area:
            detected_subject = subject_area
        if detected_language is None and lang:
            detected_language = "arabic" if lang == "ar" else "english"

        # Determine which text to use
        question_text = q_text_ar if lang == "ar" and q_text_ar else q_text

        answer_text = answer or ""


        # Create GeneratedQuestion with answer_text preserved
        questions.append(GeneratedQuestion(
            type="mcq",
            question=question_text or "",
            answer=answer_text,  # Store full answer text, not just letter
            difficulty=difficulty or "medium",
            explanation=json.dumps(scaffolding) if scaffolding else explanation or "",
            options=None,  # DB doesn't store options separately, but answer has full text
            skill=SkillInfo(
                id=f"skill_{i}",
                title=subtopic or broad_topic or "General",
                unit=broad_topic or "General",
                grade=detected_grade or grade or 8
            ) if (subtopic or broad_topic) else None
        ))

    # Build synthetic request (cap count at 100 for validation)
    req = GenerateQuestionsRequest(
        grade=detected_grade or grade or 8,
        instructions=f"Questions retrieved from database (last {hours_ago}h)",
        count=min(len(questions), 100),  # Cap at 100 to satisfy validation
        question_type="mcq",
        language=detected_language or "english",
        difficulty="mixed",
        subject=detected_subject or subject or "General"
    )

    # Build response
    resp = GenerateQuestionResponse(
        data=questions,
        request_id=f"db_retrieve_{uuid.uuid4().hex[:8]}",
        total_questions=len(questions),
        grade=detected_grade or grade or 8
    )

    logger.info(f"✓ Successfully created {len(questions)} GeneratedQuestion objects")
    logger.info(f"   Detected metadata: grade={detected_grade}, subject={detected_subject}, language={detected_language}")

    return req, resp

def main():
    logger.info("🚀 Starting EduBench Evaluator v2...")
    logger.info(f"   Python version: {sys.version}")
    logger.info(f"   Working directory: {os.getcwd()}")

    ap = argparse.ArgumentParser(
        description="Normalize & evaluate generated MCQs with EduBench-style rubric, using OpenAI as evaluator."
    )
    ap.add_argument("--in", dest="in_path", help="Path to JSON with {'request','response'}")
    ap.add_argument("--from-db", action="store_true", help="Load questions from PostgreSQL database")
    ap.add_argument("--db-limit", type=int, default=50, help="Max questions to fetch from DB (default: 50)")
    ap.add_argument("--db-grade", type=int, default=None, help="Filter DB questions by grade")
    ap.add_argument("--db-subject", default=None, help="Filter DB questions by subject")
    ap.add_argument("--db-hours", type=int, default=24, help="Get questions from last N hours (default: 24)")
    ap.add_argument("--out", dest="out_path", default=None, help="Where to write the JSON report")
    ap.add_argument("--pretty", action="store_true", help="Prints a human-friendly summary")
    ap.add_argument("--judge-model", default="gpt-5", help="OpenAI model to use as evaluator")
    ap.add_argument("--scenario", default="QG", help="Scenario for metric weights (default: QG)")
    ap.add_argument("--ref", type=int, default=0, help="Sample N EduBench QG baselines for percentiles")
    ap.add_argument("--seed", type=int, default=0, help="Random seed for baseline sampling")
    args = ap.parse_args()

    # Validate inputs
    if not args.in_path and not args.from_db:
        ap.error("Must specify either --in (JSON file) or --from-db (load from PostgreSQL)")
    if args.in_path and args.from_db:
        ap.error("Cannot specify both --in and --from-db")

    # Load data
    if args.from_db:
        req, resp = load_from_postgres(
            limit=args.db_limit,
            grade=args.db_grade,
            subject=args.db_subject,
            hours_ago=args.db_hours
        )
        print(f"Loaded {len(resp.data)} questions from database (last {args.db_hours} hours)")
    else:
        logger.info("📁 Loading questions from JSON file...")
        req, resp = load_reqresp(args.in_path)
        logger.info(f"✓ Loaded {len(resp.data)} questions from file")

    logger.info(f"⚙️  Configuration:")
    logger.info(f"   Scenario: {args.scenario}")
    logger.info(f"   Judge model: {args.judge_model}")
    logger.info(f"   Questions to evaluate: {len(resp.data)}")
    logger.info(f"   Baseline samples: {args.ref}")


    # 1) Normalize to EduBench format
    logger.info("🔄 Normalizing questions to EduBench format...")
    items = [normalize_generated_question_to_edubench_qg(req, q) for q in resp.data]
    logger.info(f"✓ Normalized {len(items)} items")

    # 2) Evaluate with OpenAI
    logger.info("🤖 Starting OpenAI evaluation of questions...")
    evaluated = []
    total_start_time = time.time()

    print('='*100)
    print(items)
    print('='*100)
    return

    # # Write/print output
    # if args.out_path:
    #     logger.info(f"💾 Saving detailed report to: {args.out_path}")
    #     with open(args.out_path, "w", encoding="utf-8") as f:
    #         f.write(json.dumps(out, ensure_ascii=False, indent=2))
    #     logger.info("✓ Report saved successfully")

if __name__ == "__main__":
    main()