#!/usr/bin/env python3
"""
Read uncategorized PDFs and categorize them based on content.
"""
import os
import shutil
import logging
from pathlib import Path
from typing import Dict, Optional
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Subject keywords for classification
SUBJECT_KEYWORDS = {
    'Mathematics': [
        'رياضيات', 'جمع', 'طرح', 'ضرب', 'قسمة', 'معادلة', 'هندسة', 'جبر',
        'mathematics', 'algebra', 'geometry', 'equation', 'calculation'
    ],
    'Science': [
        'علوم', 'فيزياء', 'كيمياء', 'أحياء', 'تجربة', 'مختبر',
        'science', 'experiment', 'laboratory', 'biology', 'chemistry', 'physics'
    ],
    'English_Language': [
        'english', 'grammar', 'vocabulary', 'reading', 'writing', 'language arts',
        'انجليزي', 'انجليزية'
    ],
    'Arabic_Language': [
        'لغة عربية', 'نحو', 'صرف', 'قراءة', 'كتابة', 'إملاء', 'تعبير',
        'arabic language', 'قواعد اللغة'
    ],
    'Islamic_Education': [
        'تربية اسلامية', 'فقه', 'عقيدة', 'حديث', 'سيرة',
        'islamic', 'fiqh', 'aqeedah', 'hadith'
    ],
    'Quran': [
        'قرآن', 'تجويد', 'تلاوة', 'حفظ', 'quran', 'tajweed'
    ],
    'Social_Studies': [
        'دراسات اجتماعية', 'تاريخ', 'جغرافيا', 'وطنية',
        'social studies', 'history', 'geography', 'civics'
    ],
    'Information_Technology': [
        'تقنية المعلومات', 'حاسوب', 'برمجة', 'كمبيوتر',
        'computer', 'programming', 'technology', 'it', 'coding'
    ],
    'Digital_Technology': [
        'عالمنا الرقمي', 'تكنولوجيا', 'رقمي',
        'digital', 'technology'
    ],
    'Physics': [
        'فيزياء', 'physics', 'mechanics', 'electricity', 'motion'
    ],
    'Chemistry': [
        'كيمياء', 'chemistry', 'reaction', 'compound', 'element'
    ],
    'Biology': [
        'أحياء', 'biology', 'cell', 'organism', 'ecology'
    ],
    'Geology': [
        'جيولوجيا', 'geology', 'earth science', 'rocks', 'minerals'
    ],
    'French_Language': [
        'فرنسية', 'français', 'french'
    ],
    'Kuwait_Studies': [
        'بلادي الكويت', 'kuwait', 'الكويت'
    ],
    'Grammar_Morphology': [
        'نحو وصرف', 'قواعد النحو', 'grammar', 'morphology'
    ],
    'Rhetoric_Arts': [
        'بلاغة', 'rhetoric', 'فنون البلاغة'
    ],
    'Home_Economics': [
        'اقتصاد منزلي', 'home economics', 'الاقتصاد المنزلي'
    ],
    'Psychology_Sociology': [
        'علم النفس', 'علم الاجتماع', 'psychology', 'sociology'
    ],
    'Philosophy': [
        'فلسفة', 'philosophy'
    ],
    'Technology': [
        'عالم التقنية', 'تقنية', 'technology'
    ],
    'Geography_Economics': [
        'جغرافيا', 'اقتصاد', 'geography', 'economics', 'علم الجغرافيا', 'علم الاقتصاد'
    ],
    'Kindergarten': [
        'رياض الاطفال', 'kindergarten', 'كراسة الطفل'
    ],
    'Islamic_History': [
        'تاريخ اسلامي', 'التاريخ الاسلامي', 'islamic history'
    ]
}

def extract_text_from_pdf(pdf_path: Path, max_pages: int = 5) -> str:
    """Extract text from first few pages of PDF, with OCR fallback."""
    try:
        doc = fitz.open(pdf_path)
        text = ""

        # Extract text from first few pages
        for page_num in range(min(max_pages, len(doc))):
            page = doc[page_num]
            page_text = page.get_text()

            # If no text extracted (scanned image), try OCR
            if not page_text.strip():
                logger.info(f"   🔍 Page {page_num + 1} has no text, attempting OCR...")
                try:
                    # Render page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))

                    # Run OCR with Arabic and English
                    page_text = pytesseract.image_to_string(img, lang='ara+eng')
                    logger.info(f"   ✅ OCR extracted {len(page_text)} characters")
                except Exception as ocr_error:
                    logger.warning(f"   ⚠️  OCR failed on page {page_num + 1}: {ocr_error}")
                    page_text = ""

            text += page_text

        doc.close()
        return text.lower()

    except Exception as e:
        logger.error(f"   ❌ Error reading {pdf_path.name}: {e}")
        return ""

def classify_by_content(text: str) -> Optional[str]:
    """Classify document based on text content."""
    text_lower = text.lower()

    # Score each subject based on keyword matches
    scores = {}
    for subject, keywords in SUBJECT_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        if score > 0:
            scores[subject] = score

    # Return subject with highest score
    if scores:
        return max(scores.items(), key=lambda x: x[1])[0]

    return None

def categorize_pdf(pdf_path: Path, base_dir: Path) -> Optional[str]:
    """Read PDF and determine its subject category."""

    # Extract text from PDF
    text = extract_text_from_pdf(pdf_path, max_pages=5)

    if not text.strip():
        logger.warning(f"   ⚠️  No text extracted from {pdf_path.name}")
        return None

    # Classify based on content
    subject = classify_by_content(text)

    return subject

def process_uncategorized(base_dir: Path, dry_run: bool = False):
    """Process all uncategorized PDFs."""

    uncategorized_dir = base_dir / "Uncategorized"

    if not uncategorized_dir.exists():
        logger.error(f"Uncategorized directory not found: {uncategorized_dir}")
        return

    pdf_files = list(uncategorized_dir.glob("*.pdf"))
    logger.info(f"📚 Found {len(pdf_files)} uncategorized PDFs")

    if dry_run:
        logger.info("🔍 DRY RUN - Analyzing files...\n")
    else:
        logger.info("📖 Reading and categorizing files...\n")

    categorized_count = 0
    still_uncategorized = 0
    category_counts = {}

    for idx, pdf_file in enumerate(pdf_files, 1):
        logger.info(f"[{idx}/{len(pdf_files)}] {pdf_file.name}")

        subject = categorize_pdf(pdf_file, base_dir)

        if subject:
            logger.info(f"   ✅ Classified as: {subject}")
            category_counts[subject] = category_counts.get(subject, 0) + 1

            if not dry_run:
                # Move to subject directory
                subject_dir = base_dir / subject
                subject_dir.mkdir(exist_ok=True)

                dest_path = subject_dir / pdf_file.name

                # Handle duplicates
                if dest_path.exists():
                    counter = 1
                    while dest_path.exists():
                        stem = pdf_file.stem
                        dest_path = subject_dir / f"{stem}_{counter}.pdf"
                        counter += 1

                shutil.move(str(pdf_file), str(dest_path))
                categorized_count += 1
        else:
            logger.info(f"   ❓ Could not determine subject")
            still_uncategorized += 1

        logger.info("")  # Blank line for readability

    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 SUMMARY")
    logger.info("="*60)

    if dry_run:
        logger.info(f"Would categorize: {len([s for s in category_counts.values() if s])}")
        logger.info(f"Would remain uncategorized: {still_uncategorized}")
    else:
        logger.info(f"✅ Categorized: {categorized_count}")
        logger.info(f"❓ Still uncategorized: {still_uncategorized}")

    logger.info("\nBy subject:")
    for subject, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        logger.info(f"   {subject}: {count}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Categorize uncategorized PDFs by reading content")
    parser.add_argument("--dry-run", action="store_true", help="Analyze without moving files")
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    process_uncategorized(base_dir, dry_run=args.dry_run)
