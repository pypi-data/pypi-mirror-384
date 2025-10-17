#!/usr/bin/env python3
"""
Organize textbooks into subject-specific directories.
"""
import os
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

# Subject mapping: Arabic keyword -> English directory name
SUBJECT_MAPPING = {
    'الرياضيات': 'Mathematics',
    'العلوم': 'Science',
    'اللغة العربية': 'Arabic_Language',
    'لغتي العربية': 'Arabic_Language',
    'لغة عربية': 'Arabic_Language',
    'اللغة الانجليزية': 'English_Language',
    'الانجليزية': 'English_Language',
    'انجليزي': 'English_Language',
    'لغة انجليزية': 'English_Language',
    'لغة_انجليزية': 'English_Language',
    'التربية الاسلامية': 'Islamic_Education',
    'القرآن الكريم': 'Quran',
    'القرأن الكريم': 'Quran',  # Alternate spelling
    'مادة القرآن': 'Quran',
    'الدراسات الاجتماعية': 'Social_Studies',
    'الدراسات_الاجتماعية': 'Social_Studies',
    'تاريخ دولة الكويت': 'Kuwait_History',
    'الفيزياء': 'Physics',
    'الكيمياء': 'Chemistry',
    'الاحياء': 'Biology',
    'الجيولوجيا': 'Geology',
    'عالمنا الرقمي': 'Digital_Technology',
    'تقنية المعلومات': 'Information_Technology',
    'اللغة الفرنسية': 'French_Language',
    'بلادي الكويت': 'Kuwait_Studies',
    'فنون البلاغة': 'Rhetoric_Arts',
    'البلاغة': 'Rhetoric_Arts',
    'قواعد النحو': 'Grammar_Morphology',
    'النحو والصرف': 'Grammar_Morphology',
    'منهج المساند': 'Supporting_Curriculum',
    'المنهج_المساند': 'Supporting_Curriculum',
}

def detect_subject(filename: str) -> str:
    """Detect subject from filename based on Arabic keywords."""
    filename_lower = filename.lower()

    # Try to match each subject keyword
    for arabic_keyword, english_dir in SUBJECT_MAPPING.items():
        if arabic_keyword in filename:
            return english_dir

    # Default to Uncategorized if no match
    return 'Uncategorized'

def organize_books(base_dir: Path, dry_run: bool = False):
    """Organize PDF files into subject directories."""

    # Get all PDF files in the base directory (not in subdirectories)
    # Case-insensitive matching for .pdf and .PDF
    pdf_files = list(base_dir.glob('*.pdf')) + list(base_dir.glob('*.PDF'))

    logger.info(f"Found {len(pdf_files)} PDF files to organize")

    # Count files per subject
    subject_counts = {}

    for pdf_file in pdf_files:
        subject = detect_subject(pdf_file.name)
        subject_counts[subject] = subject_counts.get(subject, 0) + 1

    # Display summary
    logger.info("\n📊 Subject Distribution:")
    for subject, count in sorted(subject_counts.items(), key=lambda x: -x[1]):
        logger.info(f"   {subject}: {count} files")

    if dry_run:
        logger.info("\n🔍 DRY RUN - No files will be moved")
        return

    # Create subject directories and move files
    logger.info("\n📁 Creating directories and moving files...")
    moved_count = 0

    for pdf_file in pdf_files:
        subject = detect_subject(pdf_file.name)
        subject_dir = base_dir / subject

        # Create directory if it doesn't exist
        subject_dir.mkdir(exist_ok=True)

        # Move file
        dest_path = subject_dir / pdf_file.name

        # Handle duplicate filenames
        if dest_path.exists():
            logger.warning(f"   ⚠️  File already exists: {dest_path.name}")
            # Add counter to filename
            counter = 1
            while dest_path.exists():
                stem = pdf_file.stem
                dest_path = subject_dir / f"{stem}_{counter}.pdf"
                counter += 1

        shutil.move(str(pdf_file), str(dest_path))
        moved_count += 1

        if moved_count % 50 == 0:
            logger.info(f"   Moved {moved_count}/{len(pdf_files)} files...")

    logger.info(f"\n✅ Successfully organized {moved_count} files into {len(subject_counts)} subject directories")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Organize textbooks by subject")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without moving files")
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    organize_books(base_dir, dry_run=args.dry_run)
