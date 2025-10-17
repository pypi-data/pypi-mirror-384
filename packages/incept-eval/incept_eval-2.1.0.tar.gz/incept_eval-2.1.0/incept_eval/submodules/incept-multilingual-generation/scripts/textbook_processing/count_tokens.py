#!/usr/bin/env python3
"""
Count tokens in PDF files using tiktoken.
"""
import sys
import json
import re
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import tiktoken

def extract_all_text_with_ocr(pdf_path: Path) -> str:
    """Extract all text from PDF with OCR fallback."""
    try:
        doc = fitz.open(pdf_path)
        text = ""

        print(f"   Extracting text from {len(doc)} pages...")

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()

            # If no text, try OCR (but only for first 50 pages to save time)
            if not page_text.strip() and page_num < 50:
                try:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    page_text = pytesseract.image_to_string(img, lang='ara+eng')
                except Exception:
                    page_text = ""

            text += page_text + "\n"

            # Progress indicator every 50 pages
            if (page_num + 1) % 50 == 0:
                print(f"   ... processed {page_num + 1}/{len(doc)} pages")

        doc.close()
        return text

    except Exception as e:
        print(f"   ❌ Error reading {pdf_path.name}: {e}")
        return ""

def extract_grade_from_filename(filename: str) -> int:
    """Extract grade number from filename."""
    # Look for ص followed by Arabic or Western numerals
    match = re.search(r'ص ?([٠-٩0-9]+)', filename)
    if match:
        grade_str = match.group(1)
        # Convert Arabic numerals to Western
        ar_to_en = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
        grade = int(grade_str.translate(ar_to_en))
        return grade
    return None

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    """Count tokens using tiktoken."""
    try:
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return len(tokens)
    except Exception as e:
        print(f"   ⚠️  Error counting tokens: {e}")
        return 0

def process_file(pdf_path: Path, subject: str, grade_detection_file: Path = None) -> dict:
    """Process a single PDF to count tokens."""
    print(f"\n📖 Processing: {pdf_path.name}")

    # Extract grade from filename
    grade = extract_grade_from_filename(pdf_path.name)

    # If no grade in filename, check detection results
    if grade is None and grade_detection_file and grade_detection_file.exists():
        with open(grade_detection_file, 'r', encoding='utf-8') as f:
            detection_results = json.load(f)
            for result in detection_results:
                if result['filename'] == pdf_path.name and result['grade']:
                    grade = result['grade']
                    print(f"   Using detected grade: {grade}")
                    break

    # Extract all text
    text = extract_all_text_with_ocr(pdf_path)

    if not text.strip():
        print(f"   ⚠️  No text extracted")
        return {
            'filename': pdf_path.name,
            'grade': grade,
            'subject': subject,
            'token_count': 0,
            'character_count': 0,
            'status': 'no_text'
        }

    # Count tokens
    print(f"   Counting tokens...")
    token_count = count_tokens(text)
    char_count = len(text)

    print(f"   ✅ Characters: {char_count:,} | Tokens: {token_count:,}")

    return {
        'filename': pdf_path.name,
        'grade': grade,
        'subject': subject,
        'token_count': token_count,
        'character_count': char_count,
        'status': 'success'
    }

def main():
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])
    else:
        directory = Path("Mathematics")

    subject = directory.name

    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        sys.exit(1)

    # Get all PDF files
    pdf_files = sorted(list(directory.glob('*.pdf')) + list(directory.glob('*.PDF')))

    print(f"📚 Found {len(pdf_files)} PDF files in {subject}/")
    print("="*60)

    # Check for grade detection results
    grade_detection_file = directory / "grade_detection_results.json"

    # Output files
    output_file = directory / "token_counts.json"
    aggregate_file = directory / "token_counts_aggregate.json"

    results = []
    for idx, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{idx}/{len(pdf_files)}]")
        result = process_file(pdf_file, subject, grade_detection_file)
        results.append(result)

        # Write results after each file
        successful = [r for r in results if r['status'] == 'success']
        no_text = [r for r in results if r['status'] == 'no_text']

        total_tokens = sum(r['token_count'] for r in successful)
        total_chars = sum(r['character_count'] for r in successful)

        # Save individual results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Save aggregate
        by_grade = {}
        for r in successful:
            if r['grade']:
                g = r['grade']
                if g not in by_grade:
                    by_grade[g] = {'count': 0, 'tokens': 0, 'characters': 0}
                by_grade[g]['count'] += 1
                by_grade[g]['tokens'] += r['token_count']
                by_grade[g]['characters'] += r['character_count']

        aggregate = {
            'subject': subject,
            'total_files': len(pdf_files),
            'processed_files': len(results),
            'successful_files': len(successful),
            'no_text_files': len(no_text),
            'total_tokens': total_tokens,
            'total_characters': total_chars,
            'average_tokens_per_book': total_tokens / len(successful) if successful else 0,
            'by_grade': by_grade
        }

        with open(aggregate_file, 'w', encoding='utf-8') as f:
            json.dump(aggregate, f, indent=2, ensure_ascii=False)

        print(f"   💾 Progress saved ({idx}/{len(pdf_files)} files processed)")

    # Summary
    print("\n" + "="*60)
    print("📊 FINAL SUMMARY")
    print("="*60)

    # Read final aggregate
    with open(aggregate_file, 'r', encoding='utf-8') as f:
        final_aggregate = json.load(f)

    print(f"✅ Successful: {final_aggregate['successful_files']}")
    print(f"⚠️  No text: {final_aggregate['no_text_files']}")
    print(f"📝 Total characters: {final_aggregate['total_characters']:,}")
    print(f"🎯 Total tokens: {final_aggregate['total_tokens']:,}")
    print(f"📊 Average tokens per book: {final_aggregate['average_tokens_per_book']:,.0f}")

    if final_aggregate['by_grade']:
        print(f"\n📋 By Grade:")
        for grade in sorted(final_aggregate['by_grade'].keys(), key=int):
            grade_data = final_aggregate['by_grade'][grade]
            print(f"   Grade {int(grade):2d}: {grade_data['count']} books, {grade_data['tokens']:,} tokens")

    print(f"\n💾 Results saved to:")
    print(f"   Individual: {output_file}")
    print(f"   Aggregate: {aggregate_file}")

if __name__ == "__main__":
    main()
