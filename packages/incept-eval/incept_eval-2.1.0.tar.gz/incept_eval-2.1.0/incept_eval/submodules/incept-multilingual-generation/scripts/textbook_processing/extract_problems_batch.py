#!/usr/bin/env python3
"""
Batch extract mathematics problems from all PDFs in a directory.
Outputs all problems to a single JSONL file.
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

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.llms import produce_structured_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models
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

def extract_grade_from_filename(filename: str) -> Optional[int]:
    """Extract grade number from filename."""
    match = re.search(r'ص ?([٠-٩0-9]+)', filename)
    if match:
        grade_str = match.group(1)
        ar_to_en = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        grade = int(grade_str.translate(ar_to_en))
        return grade
    return None

def extract_page_text(page, page_num: int) -> str:
    """Extract text from a single page with OCR fallback."""
    try:
        text = page.get_text()

        if not text.strip():
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
- Translate accurately to English while preserving mathematical notation.
- ONLY extract COMPLETE questions that can be answered. DO NOT extract:
  * Section headers or titles (e.g., "قياسات الزوايا التالية" / "The following angles")
  * Instructions without specific problems (e.g., "Solve the following")
  * Incomplete prompts that don't contain actual data/numbers to work with
- A valid question must contain specific information to solve (numbers, diagrams described, specific scenarios)"""

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

def is_book_complete(pdf_file: Path, output_file: Path) -> bool:
    """Check if a book has been fully processed in the single output file."""
    if not output_file.exists():
        return False

    try:
        doc = fitz.open(pdf_file)
        total_pages = len(doc)
        doc.close()

        # Check last page for this specific book
        last_page = 0
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if record.get('source_file') == pdf_file.name:
                        last_page = max(last_page, record.get('page', 0))

        return last_page >= total_pages

    except Exception:
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_problems_batch.py <directory> [provider] [--no-resume]")
        print("\nExamples:")
        print("  python extract_problems_batch.py data/textbooks/Mathematics")
        print("  python extract_problems_batch.py data/textbooks/Mathematics openai")
        print("  python extract_problems_batch.py data/textbooks/Mathematics openai --no-resume")
        sys.exit(1)

    input_dir = Path(sys.argv[1])
    provider = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else "openai"
    resume = '--no-resume' not in sys.argv

    if not input_dir.exists():
        logger.error(f"❌ Directory not found: {input_dir}")
        sys.exit(1)

    # Get all PDFs (exclude _ungraded subdirectory)
    pdf_files = sorted([f for f in (list(input_dir.glob('*.pdf')) + list(input_dir.glob('*.PDF'))) if f.is_file()])

    if not pdf_files:
        logger.error(f"❌ No PDF files found in {input_dir}")
        sys.exit(1)

    # Single output file for all problems
    output_file = input_dir / "all_problems.jsonl"

    logger.info(f"🚀 Batch Problem Extraction")
    logger.info(f"{'='*80}")
    logger.info(f"   Input directory: {input_dir}")
    logger.info(f"   Output file: {output_file}")
    logger.info(f"   Provider: {provider}")
    logger.info(f"   Resume mode: {'ENABLED' if resume else 'DISABLED'}")
    logger.info(f"   Total PDFs: {len(pdf_files)}")
    logger.info(f"{'='*80}\n")

    # Check which books are already complete
    if resume:
        complete_books = [pdf for pdf in pdf_files if is_book_complete(pdf, output_file)]
        if complete_books:
            logger.info(f"📋 Found {len(complete_books)} already completed books (will skip):")
            for book in complete_books[:5]:
                logger.info(f"   ✓ {book.name}")
            if len(complete_books) > 5:
                logger.info(f"   ... and {len(complete_books) - 5} more")
            logger.info("")

    # Process each PDF
    processed = 0
    skipped = 0
    total_problems = 0

    for idx, pdf_file in enumerate(pdf_files, 1):
        # Skip if already complete
        if resume and is_book_complete(pdf_file, output_file):
            logger.info(f"\n{'#'*80}")
            logger.info(f"FILE {idx}/{len(pdf_files)}: {pdf_file.name}")
            logger.info(f"   ✓ Already complete, skipping")
            logger.info(f"{'#'*80}")
            skipped += 1
            continue

        logger.info(f"\n{'#'*80}")
        logger.info(f"FILE {idx}/{len(pdf_files)}: {pdf_file.name}")
        logger.info(f"{'#'*80}")

        # Extract grade from filename
        grade = extract_grade_from_filename(pdf_file.name)

        if not grade:
            logger.warning(f"   ⚠️  No grade found in filename, skipping")
            continue

        logger.info(f"   Grade: {grade}")

        try:
            # Open PDF
            doc = fitz.open(pdf_file)
            total_pages = len(doc)
            logger.info(f"   Total pages: {total_pages}")

            # Determine start page for resume
            start_page = 0
            if resume and output_file.exists():
                last_page = 0
                with open(output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            if record.get('source_file') == pdf_file.name:
                                last_page = max(last_page, record.get('page', 0))

                if last_page > 0:
                    start_page = last_page
                    logger.info(f"   📌 RESUMING from page {start_page + 1}")

            # Process each page
            book_problems = 0
            for page_num in range(start_page, total_pages):
                logger.info(f"\n   📄 Processing Page {page_num + 1}/{total_pages}")
                logger.info(f"   {'-'*76}")

                try:
                    page = doc[page_num]
                    page_text = extract_page_text(page, page_num + 1)

                    if not page_text.strip():
                        logger.warning(f"      ⚠️  Page {page_num + 1}: No text extracted, skipping")
                        continue

                    # Extract problems
                    problems = extract_problems_from_page(page_text, page_num + 1, provider=provider)

                    if not problems:
                        logger.info(f"      ℹ️  Page {page_num + 1}: No problems found")
                        continue

                    # Write to single JSONL file
                    with open(output_file, 'a', encoding='utf-8') as f:
                        for prob_idx, problem in enumerate(problems, 1):
                            record = {
                                "source_file": pdf_file.name,
                                "grade": grade,
                                "page": page_num + 1,
                                "problem_index": prob_idx,
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

                            f.write(json.dumps(record, ensure_ascii=False) + '\n')
                            f.flush()

                            book_problems += 1
                            total_problems += 1

                            logger.info(f"      ✍️  Problem {prob_idx}: {problem.skill_english}")
                            logger.info(f"         Topic: {problem.topic_english}")
                            logger.info(f"         💾 Written to JSONL")

                    logger.info(f"      ✅ Page {page_num + 1}: {len(problems)} problems extracted")

                except Exception as e:
                    logger.error(f"      ❌ Page {page_num + 1}: Processing failed - {e}")
                    logger.debug(traceback.format_exc())
                    continue

            doc.close()
            logger.info(f"\n   ✅ BOOK COMPLETE: {book_problems} problems extracted")
            processed += 1

        except Exception as e:
            logger.error(f"   ❌ Failed to process {pdf_file.name}: {e}")
            logger.debug(traceback.format_exc())
            continue

    logger.info(f"\n{'='*80}")
    logger.info(f"🎉 BATCH EXTRACTION COMPLETE!")
    logger.info(f"{'='*80}")
    logger.info(f"   Total PDFs: {len(pdf_files)}")
    logger.info(f"   Processed: {processed}")
    logger.info(f"   Skipped (already complete): {skipped}")
    logger.info(f"   Total problems extracted: {total_problems}")
    logger.info(f"   Output file: {output_file}")
    logger.info(f"{'='*80}\n")

if __name__ == "__main__":
    main()
