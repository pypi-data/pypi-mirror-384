#!/usr/bin/env python3
"""
Detect grade level from PDF content using text extraction and OCR.
"""
import sys
import re
from pathlib import Path
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import json

def extract_text_with_ocr(pdf_path: Path, max_pages: int = 15) -> str:
    """Extract text from PDF with OCR fallback for first N pages."""
    try:
        doc = fitz.open(pdf_path)
        text = ""

        for page_num in range(min(max_pages, len(doc))):
            page = doc[page_num]
            page_text = page.get_text()

            # If no text, try OCR
            if not page_text.strip():
                try:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    page_text = pytesseract.image_to_string(img, lang='ara+eng')
                except Exception:
                    page_text = ""

            text += page_text + "\n"

        doc.close()
        return text

    except Exception as e:
        print(f"   ❌ Error reading {pdf_path.name}: {e}")
        return ""

def detect_grade_from_text(text: str) -> dict:
    """Detect grade level from text content."""
    grade_patterns = [
        # Arabic patterns
        (r'الصف\s+([٠-٩]+|الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|الحادي عشر|الثاني عشر)', 'ar_explicit'),
        (r'صف\s+([٠-٩]+|الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|الحادي عشر|الثاني عشر)', 'ar_explicit'),
        (r'للصف\s+([٠-٩]+|الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|الحادي عشر|الثاني عشر)', 'ar_for_grade'),
        (r'صـ\s*([٠-٩]+)', 'ar_abbreviated'),

        # English patterns
        (r'Grade\s+([0-9]+)', 'en_grade'),
        (r'Class\s+([0-9]+)', 'en_class'),
        (r'Year\s+([0-9]+)', 'en_year'),

        # Mixed patterns
        (r'G([0-9]+)', 'abbrev_g'),
    ]

    # Arabic number words to digits
    arabic_word_to_num = {
        'الأول': '1', 'الثاني': '2', 'الثالث': '3', 'الرابع': '4',
        'الخامس': '5', 'السادس': '6', 'السابع': '7', 'الثامن': '8',
        'التاسع': '9', 'العاشر': '10', 'الحادي عشر': '11', 'الثاني عشر': '12'
    }

    # Arabic to Western numeral conversion
    ar_to_en = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

    results = []

    for pattern, pattern_type in grade_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            grade_str = match.strip()

            # Convert Arabic word to number
            if grade_str in arabic_word_to_num:
                grade_num = int(arabic_word_to_num[grade_str])
            # Convert Arabic numerals to Western
            elif re.match(r'[٠-٩]+', grade_str):
                grade_num = int(grade_str.translate(ar_to_en))
            # Western numerals
            elif grade_str.isdigit():
                grade_num = int(grade_str)
            else:
                continue

            # Validate grade range (1-12)
            if 1 <= grade_num <= 12:
                results.append({
                    'grade': grade_num,
                    'pattern_type': pattern_type,
                    'matched_text': match
                })

    # Return most common grade found
    if results:
        # Count occurrences of each grade
        grade_counts = {}
        for r in results:
            g = r['grade']
            grade_counts[g] = grade_counts.get(g, 0) + 1

        # Get most frequent grade
        most_common_grade = max(grade_counts.items(), key=lambda x: x[1])

        return {
            'grade': most_common_grade[0],
            'confidence': most_common_grade[1],
            'all_matches': results
        }

    return None

def process_file(pdf_path: Path) -> dict:
    """Process a single PDF to detect grade."""
    print(f"\n📖 Processing: {pdf_path.name}")

    text = extract_text_with_ocr(pdf_path, max_pages=10)

    if not text.strip():
        print(f"   ⚠️  No text extracted")
        return {
            'filename': pdf_path.name,
            'grade': None,
            'confidence': 0,
            'status': 'no_text'
        }

    grade_info = detect_grade_from_text(text)

    if grade_info:
        print(f"   ✅ Detected: Grade {grade_info['grade']} (confidence: {grade_info['confidence']} matches)")
        return {
            'filename': pdf_path.name,
            'grade': grade_info['grade'],
            'confidence': grade_info['confidence'],
            'status': 'detected',
            'matches': grade_info['all_matches']
        }
    else:
        print(f"   ❓ Could not detect grade")
        return {
            'filename': pdf_path.name,
            'grade': None,
            'confidence': 0,
            'status': 'not_detected'
        }

def main():
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])
    else:
        directory = Path("Mathematics")

    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        sys.exit(1)

    # Get files without grade info in filename
    all_pdfs = list(directory.glob('*.pdf')) + list(directory.glob('*.PDF'))
    files_without_grade = [f for f in all_pdfs if 'ص' not in f.name]

    print(f"📚 Found {len(files_without_grade)} files without grade in filename\n")
    print("="*60)

    results = []
    for pdf_file in sorted(files_without_grade):
        result = process_file(pdf_file)
        results.append(result)

    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)

    detected = [r for r in results if r['status'] == 'detected']
    not_detected = [r for r in results if r['status'] == 'not_detected']
    no_text = [r for r in results if r['status'] == 'no_text']

    print(f"✅ Detected: {len(detected)}")
    print(f"❓ Not detected: {len(not_detected)}")
    print(f"⚠️  No text: {len(no_text)}")

    if detected:
        print("\n📋 Detected grades:")
        for r in sorted(detected, key=lambda x: x['grade']):
            print(f"   Grade {r['grade']:2d}: {r['filename']}")

    # Save results to JSON
    output_file = directory / "grade_detection_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Results saved to: {output_file}")

if __name__ == "__main__":
    main()
