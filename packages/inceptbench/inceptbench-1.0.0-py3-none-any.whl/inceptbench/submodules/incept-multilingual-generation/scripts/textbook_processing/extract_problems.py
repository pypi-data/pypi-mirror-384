#!/usr/bin/env python3
"""
Extract mathematics problems from textbook PDFs page by page.
Writes to JSONL with one problem per line.
"""
import sys
import json
import re
import io
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.llms import produce_structured_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for structured response
class GradeDetection(BaseModel):
    """Grade level detected from textbook."""
    grade: Optional[int] = Field(None, description="Grade level (1-12) if found, null if not found")
    confidence: str = Field(..., description="Confidence level: high, medium, or low")

class MathProblem(BaseModel):
    """Single mathematics problem with bilingual fields."""
    topic_arabic: str = Field(..., description="General mathematical topic in Arabic (e.g., الجبر, الهندسة, الأعداد)")
    topic_english: str = Field(..., description="General mathematical topic in English (e.g., Algebra, Geometry, Numbers)")
    skill_arabic: str = Field(..., description="Specific skill being tested in Arabic (e.g., حل المعادلات الخطية, حساب محيط المثلثات)")
    skill_english: str = Field(..., description="Specific skill being tested in English (e.g., Solving linear equations, Calculating triangle perimeter)")
    question_arabic: str = Field(..., description="Complete question text in Arabic")
    question_english: str = Field(..., description="Complete question text translated to English")
    answer_arabic: Optional[str] = Field(None, description="Answer in Arabic if provided on the page, otherwise null")
    answer_english: Optional[str] = Field(None, description="Answer translated to English if provided, otherwise null")

class MathProblemsPage(BaseModel):
    """Collection of problems from a single page."""
    problems: List[MathProblem] = Field(default_factory=list, description="List of all mathematics problems found on the page")

def extract_grade_from_filename(filename: str) -> int:
    """Extract grade number from filename."""
    match = re.search(r'ص ?([٠-٩0-9]+)', filename)
    if match:
        grade_str = match.group(1)
        ar_to_en = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        grade = int(grade_str.translate(ar_to_en))
        return grade
    return None

def extract_page_text(page, page_num: int, use_ocr: bool = False) -> str:
    """Extract text from a single page with OCR fallback."""
    try:
        # Try text extraction first
        text = page.get_text()

        if not text.strip() or use_ocr:
            logger.info(f"      🔍 Page {page_num}: No text found, using OCR...")
            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                text = pytesseract.image_to_string(img, lang='ara+eng')
                logger.info(f"      ✅ Page {page_num}: OCR extracted {len(text)} characters")
            except Exception as ocr_error:
                logger.error(f"      ❌ Page {page_num}: OCR failed - {ocr_error}")
                text = ""
        else:
            logger.info(f"      📄 Page {page_num}: Direct text extraction ({len(text)} chars)")

        return text
    except Exception as e:
        logger.error(f"      ❌ Page {page_num}: Text extraction failed - {e}")
        return ""

def extract_problems_from_page(page_text: str, page_num: int, provider: str = "openai") -> List[MathProblem]:
    """Use LLM to extract mathematics problems from page text with structured output."""

    if not page_text.strip():
        logger.warning(f"      ⚠️  Page {page_num}: Empty text, skipping problem extraction")
        return []

    instructions = """You are an expert at extracting mathematics problems from Arabic textbook pages.

Your task is to identify and extract ALL mathematics problems from the given page text.

For each problem, extract:
1. topic_arabic: The general mathematical topic in Arabic (e.g., "الجبر", "الهندسة", "الأعداد")
2. topic_english: The general mathematical topic in English (e.g., "Algebra", "Geometry", "Numbers")
3. skill_arabic: The specific skill being tested in Arabic (e.g., "حل المعادلات الخطية", "حساب محيط المثلثات")
4. skill_english: The specific skill being tested in English (e.g., "Solving linear equations", "Calculating triangle perimeter")
5. question_arabic: The complete question text in Arabic
6. question_english: The complete question text translated to English
7. answer_arabic: The answer in Arabic if provided on the page, otherwise null
8. answer_english: The answer translated to English if provided, otherwise null

Extract ALL problems you find. If no problems are found, return an empty list.

IMPORTANT:
- The topic is BROAD (e.g., Algebra, Geometry, not specific operations)
- The skill is SPECIFIC (e.g., calculating perimeter of triangles, not just "geometry")
- Translate accurately to English while preserving mathematical notation."""

    user_prompt = f"""Extract all mathematics problems from this page:

{page_text}"""

    try:
        logger.info(f"      🤖 Page {page_num}: Calling LLM to extract problems (structured)...")

        response = produce_structured_response(
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            structure_model=MathProblemsPage,
            instructions=instructions,
            temperature=0.3,
            max_output_tokens=6000,
            provider=provider
        )

        # Response is a Pydantic model
        if isinstance(response, MathProblemsPage):
            problems = response.problems
            logger.info(f"      ✅ Page {page_num}: Extracted {len(problems)} problems (validated)")
            return problems
        else:
            logger.error(f"      ❌ Page {page_num}: Unexpected response type: {type(response)}")
            return []

    except Exception as e:
        logger.error(f"      ❌ Page {page_num}: LLM extraction failed - {e}")
        logger.debug(traceback.format_exc())
        return []

def process_book(pdf_path: Path, output_dir: Path, provider: str = "openai", grade_detection_file: Path = None, resume: bool = True):
    """Process a single book page by page to extract problems."""

    filename = pdf_path.name
    logger.info(f"\n{'='*80}")
    logger.info(f"📖 PROCESSING BOOK: {filename}")
    logger.info(f"{'='*80}")

    # Extract grade
    grade = extract_grade_from_filename(filename)

    # Check grade detection file if no grade in filename
    if grade is None and grade_detection_file and grade_detection_file.exists():
        with open(grade_detection_file, 'r', encoding='utf-8') as f:
            detection_results = json.load(f)
            for result in detection_results:
                if result['filename'] == filename and result['grade']:
                    grade = result['grade']
                    logger.info(f"   Grade: {grade} (from detection)")
                    break

    if grade:
        logger.info(f"   Grade: {grade}")
    else:
        logger.warning(f"   Grade: UNKNOWN")

    # Open PDF
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        logger.info(f"   Total pages: {total_pages}")
    except Exception as e:
        logger.error(f"   ❌ Failed to open PDF: {e}")
        return

    # Create output file
    output_file = output_dir / f"{pdf_path.stem}_problems.jsonl"
    logger.info(f"   Output: {output_file}")

    # Check for resume
    start_page = 0
    if resume and output_file.exists():
        # Find last processed page
        last_page = 0
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        last_page = max(last_page, record.get('page', 0))

            if last_page > 0:
                start_page = last_page
                logger.info(f"   📌 RESUMING from page {start_page + 1} (found {last_page} completed pages)")
        except Exception as e:
            logger.warning(f"   ⚠️  Could not parse existing file for resume: {e}")
            start_page = 0

    logger.info(f"\n{'='*80}")

    total_problems = 0

    # Process each page
    for page_num in range(start_page, total_pages):
        logger.info(f"\n   📄 Processing Page {page_num + 1}/{total_pages}")
        logger.info(f"   {'-'*76}")

        try:
            page = doc[page_num]

            # Extract text
            page_text = extract_page_text(page, page_num + 1)

            if not page_text.strip():
                logger.warning(f"      ⚠️  Page {page_num + 1}: No text extracted, skipping")
                continue

            # Extract problems using LLM with structured output
            problems = extract_problems_from_page(page_text, page_num + 1, provider=provider)

            if not problems:
                logger.info(f"      ℹ️  Page {page_num + 1}: No problems found")
                continue

            # Write each problem to JSONL
            with open(output_file, 'a', encoding='utf-8') as f:
                for idx, problem in enumerate(problems, 1):
                    # problem is a Pydantic MathProblem object
                    # Build output record
                    record = {
                        "source_file": filename,
                        "grade": grade,
                        "page": page_num + 1,
                        "problem_index": idx,
                        "topic_arabic": problem.topic_arabic,
                        "topic_english": problem.topic_english,
                        "skill_arabic": problem.skill_arabic,
                        "skill_english": problem.skill_english,
                        "question_arabic": problem.question_arabic,
                        "question_english": problem.question_english,
                        "answer_arabic": problem.answer_arabic,
                        "answer_english": problem.answer_english,
                        "extracted_at": datetime.now().isoformat()
                    }

                    # Write to JSONL
                    f.write(json.dumps(record, ensure_ascii=False) + '\n')
                    f.flush()

                    total_problems += 1

                    # Log the problem
                    logger.info(f"      ✍️  Problem {idx}: {problem.skill_english}")
                    logger.info(f"         Topic: {problem.topic_english} ({problem.topic_arabic})")
                    logger.info(f"         Skill: {problem.skill_arabic}")
                    logger.info(f"         Question (AR): {problem.question_arabic[:100]}...")
                    logger.info(f"         Question (EN): {problem.question_english[:100]}...")
                    if problem.answer_arabic:
                        logger.info(f"         Answer (AR): {problem.answer_arabic[:100]}...")
                        logger.info(f"         Answer (EN): {problem.answer_english[:100]}...")
                    logger.info(f"         💾 Written to JSONL")

            logger.info(f"      ✅ Page {page_num + 1}: {len(problems)} problems extracted and saved")

        except Exception as e:
            logger.error(f"      ❌ Page {page_num + 1}: Processing failed - {e}")
            logger.debug(traceback.format_exc())
            continue

    doc.close()

    # Summary
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ BOOK COMPLETE: {filename}")
    logger.info(f"{'='*80}")
    logger.info(f"   Total pages processed: {total_pages}")
    logger.info(f"   Total problems extracted: {total_problems}")
    logger.info(f"   Output file: {output_file}")
    logger.info(f"{'='*80}\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_problems.py <pdf_file> [provider] [output_dir] [--no-resume]")
        print("\nExamples:")
        print("  python extract_problems.py Mathematics/الرياضيات_ص_6_ج_1.pdf")
        print("  python extract_problems.py Mathematics/الرياضيات_ص_6_ج_1.pdf openai")
        print("  python extract_problems.py Mathematics/الرياضيات_ص_6_ج_1.pdf dspy output/")
        print("  python extract_problems.py Mathematics/الرياضيات_ص_6_ج_1.pdf openai output/ --no-resume")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    provider = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "openai"
    output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith('--') else pdf_path.parent
    resume = '--no-resume' not in sys.argv

    if not pdf_path.exists():
        logger.error(f"❌ File not found: {pdf_path}")
        sys.exit(1)

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Created output directory: {output_dir}")

    # Check for grade detection file
    grade_detection_file = pdf_path.parent / "grade_detection_results.json"

    logger.info(f"🚀 Starting problem extraction")
    logger.info(f"   PDF: {pdf_path}")
    logger.info(f"   Provider: {provider}")
    logger.info(f"   Output directory: {output_dir}")
    logger.info(f"   Resume mode: {'ENABLED' if resume else 'DISABLED'}")

    process_book(pdf_path, output_dir, provider=provider, grade_detection_file=grade_detection_file, resume=resume)

    logger.info("🎉 Extraction complete!")

if __name__ == "__main__":
    main()
