#!/usr/bin/env python3
"""
Extract curriculum data from MATH DATA MODEL.xlsx to JSONL files.
Creates one JSONL file per grade with normalized column names.
"""

import pandas as pd
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

EXCEL_FILE = project_root / "edu_configs" / "MATH DATA MODEL.xlsx"
OUTPUT_DIR = project_root / "edu_configs"

# Normalized column mapping (maps various column names across grades to standard keys)
COLUMN_MAPPING = {
    # Core identifiers
    'domain_id': ['Domain Id', 'domain_id'],
    'domain': ['Domain', 'domain'],
    'cluster_id': ['Cluster Id', 'cluster_id'],
    'cluster': ['Cluster', 'cluster'],
    'unit_number': ['Unit Number', 'unit_number'],
    'unit_name': ['Unit Name', 'unit_name'],

    # Standards
    'standard_id_l1': ['Standard ID (L1)', 'Standard Id (L1)', 'standard_id_l1'],
    'standard_description_l1': ['Standard Description (L1)', 'standard_description_l1'],
    'standard_id_l2': ['Standard ID (L2)', 'Standard Id (L2)', 'standard_id_l2'],
    'standard_description_l2': ['Standard Description (L2)', 'standard_description_l2'],

    # Substandards & Lessons
    'substandard_id': ['Substandard ID', 'substandard_id', 'Substandard Id'],
    'substandard_description': ['Substandard Description', 'substandard_description'],
    'lesson_order': ['Lesson Order', 'Lesson #', 'lesson_order', 'Lesson Number'],
    'lesson_title': ['Lesson Title', 'lesson_title'],

    # Question details
    'question_types': ['Question Types', 'question_types', 'MVP Question Types'],
    'example_question': ['Example Question', 'General Example Questions', 'example_question'],
    'tasks': ['Tasks', 'tasks'],
    'assessment_boundary': ['Assessment Boundary', 'assessment_boundary'],
    'difficulty_matrix': ['Difficulty Matrix', 'difficulty_matrix'],

    # Pedagogical content
    'step_by_step_explanation': ['Step By Step Explanation', 'Step by Step Explanation', 'step_by_step_explanation'],
    'direct_instruction': ['Direct Instruction', 'direct_instruction'],
    'common_misconception_1': ['Common Misconception 1', 'common_misconception_1'],
    'common_misconception_2': ['Common Misconception 2', 'common_misconception_2'],
    'common_misconception_3': ['Common Misconception 3', 'common_misconception_3'],
    'common_misconception_4': ['Common Misconception 4', 'common_misconception_4'],

    # IXL alignment
    'ixl_lesson_alignment': ['IXL Lesson Alignment', 'IXL Lesson', 'ixl_lesson_alignment'],

    # Metadata
    'subject': ['Subject', 'subject'],
    'grade': ['Grade', 'grade'],
    'course': ['Course', 'course'],
    'category': ['Category', 'category'],
    'active': ['Active', 'active'],
    'stimulus_needed': ['Stimulus Needed', 'stimulus_needed'],
    'stimuli_categorization': ['Stimuli Categorization', 'stimuli_categorization'],

    # Article/Template
    'article_template': ['Article Template', 'article_template'],
    'notes': ['Notes', 'NOTES', 'notes']
}

def normalize_column_name(col_name, mapping):
    """Map a column name to its normalized key."""
    col_name_clean = str(col_name).strip()

    for normalized_key, variants in mapping.items():
        if col_name_clean in variants:
            return normalized_key

    # If not found in mapping, return snake_case version
    return col_name_clean.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('.', '')

def extract_grade_to_jsonl(grade_name, excel_file, output_dir):
    """Extract a single grade sheet to JSONL."""
    print(f"📚 Processing {grade_name}...")

    try:
        # Read the grade sheet
        df = pd.read_excel(excel_file, sheet_name=grade_name)

        # Normalize column names
        normalized_columns = {col: normalize_column_name(col, COLUMN_MAPPING) for col in df.columns}
        df = df.rename(columns=normalized_columns)

        # Extract grade number from sheet name (e.g., "3rd Grade" -> 3)
        grade_num = grade_name.split()[0].replace('rd', '').replace('th', '').replace('st', '').replace('nd', '')

        # Output JSONL file
        output_file = output_dir / f"curriculum_grade_{grade_num}.jsonl"

        # Write each row as a JSON line
        rows_written = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for idx, row in df.iterrows():
                # Convert row to dict, filtering out NaN values
                row_dict = {}
                for key, value in row.items():
                    if pd.notna(value):
                        # Convert numpy types to Python types
                        if isinstance(value, (pd.Timestamp,)):
                            row_dict[key] = value.isoformat()
                        elif isinstance(value, (int, float)):
                            row_dict[key] = float(value) if isinstance(value, float) else int(value)
                        else:
                            row_dict[key] = str(value)

                # Only write if row has content (skip empty rows)
                if row_dict:
                    f.write(json.dumps(row_dict, ensure_ascii=False) + '\n')
                    rows_written += 1

        print(f"  ✅ Wrote {rows_written} rows to {output_file.name}")
        return True

    except Exception as e:
        print(f"  ❌ Error processing {grade_name}: {e}")
        return False

def main():
    """Main extraction function."""
    print(f"🔍 Starting curriculum extraction from {EXCEL_FILE}")
    print(f"📁 Output directory: {OUTPUT_DIR}\n")

    # Check if Excel file exists
    if not EXCEL_FILE.exists():
        print(f"❌ Excel file not found: {EXCEL_FILE}")
        sys.exit(1)

    # Grade sheets to process
    grade_sheets = ['3rd Grade', '4th Grade', '5th Grade', '6th Grade', '7th Grade', '8th Grade']

    # Process each grade
    success_count = 0
    for grade in grade_sheets:
        if extract_grade_to_jsonl(grade, EXCEL_FILE, OUTPUT_DIR):
            success_count += 1

    print(f"\n{'='*60}")
    print(f"✨ Extraction complete: {success_count}/{len(grade_sheets)} grades processed")
    print(f"📂 JSONL files saved to: {OUTPUT_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
