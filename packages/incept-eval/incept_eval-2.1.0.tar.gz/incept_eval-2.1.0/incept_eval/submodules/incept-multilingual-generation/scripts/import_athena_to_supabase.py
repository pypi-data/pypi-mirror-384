#!/usr/bin/env python3
"""
Import Athena extracted questions into Supabase questions table.

Usage:
    python scripts/import_athena_to_supabase.py

Requirements:
    pip install supabase openai python-dotenv

Environment variables (in .env):
    SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
    SUPABASE_SERVICE_KEY=[YOUR-SERVICE-ROLE-KEY]
    OPENAI_API_KEY=[YOUR-OPENAI-KEY]  # For embeddings
"""

import json
import hashlib
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from supabase import create_client, Client
import openai
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize clients
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
openai.api_key = OPENAI_API_KEY


def parse_direct_instruction(di_text: str) -> Dict[str, Any]:
    """Parse Direct Instruction markdown into structured fields."""
    if not di_text:
        return {}

    result = {
        "prerequisite_skills": [],
        "microskills": [],
        "vocabulary": [],
        "question_stems": [],
        "step_by_step_explanations": []
    }

    # Extract Prerequisite Skills
    prereq_match = re.search(r'## Prerequisite [Ss]kills?\n(.*?)(?=\n##|\Z)', di_text, re.DOTALL)
    if prereq_match:
        lines = prereq_match.group(1).strip().split('\n')
        result["prerequisite_skills"] = [
            line.strip('- •').strip()
            for line in lines
            if line.strip() and (line.startswith('-') or line.startswith('•'))
        ]

    # Extract Microskills
    micro_match = re.search(r'## Microskills?\n(.*?)(?=\n##|\Z)', di_text, re.DOTALL)
    if micro_match:
        lines = micro_match.group(1).strip().split('\n')
        result["microskills"] = [
            line.strip('- •').strip()
            for line in lines
            if line.strip() and (line.startswith('-') or line.startswith('•'))
        ]

    # Extract Precise Vocabulary
    vocab_match = re.search(r'## Precise Vocabulary\n(.*?)(?=\n##|\Z)', di_text, re.DOTALL)
    if vocab_match:
        lines = vocab_match.group(1).strip().split('\n')
        for line in lines:
            if line.strip() and (line.startswith('-') or line.startswith('•')):
                # Parse "**Term**: Definition" format
                term_def = re.match(r'[•\-]\s*\*\*([^*]+)\*\*:\s*(.+)', line.strip())
                if term_def:
                    result["vocabulary"].append({
                        "term": term_def.group(1).strip(),
                        "definition": term_def.group(2).strip()
                    })

    # Extract Question Stems
    stems_match = re.search(r'## Question Stems?\n(.*?)(?=\n##|\Z)', di_text, re.DOTALL)
    if stems_match:
        lines = stems_match.group(1).strip().split('\n')
        result["question_stems"] = [
            re.sub(r'^\d+\.\s*', '', line.strip('- •').strip())
            for line in lines
            if line.strip() and (re.match(r'^\d+\.', line.strip()) or line.startswith('-') or line.startswith('•'))
        ]

    # Extract Step-by-Step Explanations
    steps_match = re.search(r'## Step-by-Step Explanations?\n(.*?)(?=\n##|\Z)', di_text, re.DOTALL)
    if steps_match:
        lines = steps_match.group(1).strip().split('\n')
        current_step = []
        for line in lines:
            if line.strip().startswith('**STEP') or line.strip().startswith('STEP'):
                if current_step:
                    result["step_by_step_explanations"].append(' '.join(current_step))
                current_step = [line.strip()]
            elif line.strip() and current_step:
                current_step.append(line.strip())
        if current_step:
            result["step_by_step_explanations"].append(' '.join(current_step))

    return result


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate OpenAI embedding for text."""
    if not OPENAI_API_KEY or not text:
        return None

    try:
        response = openai.embeddings.create(
            model="text-embedding-ada-002",
            input=text[:8000]  # OpenAI limit
        )
        return response.data[0].embedding
    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}")
        return None


def build_searchable_text(row: Dict) -> str:
    """Build optimized searchable text for embeddings."""
    parts = []

    # Add hierarchical context (ensure strings only)
    if row.get("unit_name") and isinstance(row.get("unit_name"), str):
        parts.append(row["unit_name"])
    if row.get("lesson_name") and isinstance(row.get("lesson_name"), str):
        parts.append(row["lesson_name"])
    if row.get("level_name") and isinstance(row.get("level_name"), str):
        parts.append(row["level_name"])

    # Add question text (most important)
    question_obj = json.loads(row.get("question", "{}")) if isinstance(row.get("question"), str) else row.get("question", {})
    if isinstance(question_obj, dict):
        q_text = question_obj.get("question", "")
        if q_text and isinstance(q_text, str):
            # Strip HTML tags
            q_text = re.sub(r'<[^>]+>', ' ', q_text)
            parts.append(q_text)

    # Add learning objective
    for attr in row.get("extended_attributes", []):
        if isinstance(attr, dict) and attr.get("type") == "LearningObjective":
            value = attr.get("value", "")
            if value and isinstance(value, str):
                parts.append(value)
            break

    return " ".join(parts).strip()


def compute_content_hash(question_text: str) -> str:
    """Generate SHA256 hash for deduplication."""
    # Normalize text: lowercase, remove extra whitespace
    normalized = re.sub(r'\s+', ' ', question_text.lower().strip())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def extract_question_data(athena_row: Dict) -> Dict[str, Any]:
    """Extract and transform Athena row into database schema."""

    # Parse question JSON
    question_obj = json.loads(athena_row.get("question", "{}")) if isinstance(athena_row.get("question"), str) else athena_row.get("question", {})

    # Extract question text
    question_text = question_obj.get("question", "") if isinstance(question_obj, dict) else ""
    question_text = re.sub(r'<[^>]+>', ' ', question_text)  # Strip HTML

    # Extract answer (handle multiple formats)
    answer = question_obj.get("answer", []) if isinstance(question_obj, dict) else []
    answer_text = ""

    if isinstance(answer, list):
        if len(answer) > 0 and isinstance(answer[0], dict):
            # Multi-blank format: [{"blank-1": "28", "blank-2": "14"}]
            # Extract all values from the dict
            answer_dict = answer[0]
            # Sort by blank number to maintain order
            sorted_blanks = sorted(answer_dict.items(), key=lambda x: x[0])
            answer_text = ", ".join([str(v) for k, v in sorted_blanks])
        elif all(isinstance(a, str) for a in answer):
            # Simple string array: ["3"]
            answer_text = ", ".join(answer)
        else:
            # Mixed or other format - convert all to strings
            answer_text = ", ".join([str(a) for a in answer])
    else:
        answer_text = str(answer)

    # Extract explanation
    explanation_obj = question_obj.get("explanation", {}) if isinstance(question_obj, dict) else {}
    explanation_text = explanation_obj.get("text", "") if isinstance(explanation_obj, dict) else ""

    # Extract worked example
    worked_example = question_obj.get("worked_example", {}) if isinstance(question_obj, dict) else {}

    # Extract images from stimulus
    images = []
    stimulus = question_obj.get("stimulus", []) if isinstance(question_obj, dict) else []
    for item in stimulus if isinstance(stimulus, list) else []:
        if isinstance(item, dict) and item.get("type") == "image":
            img_data = item.get("image", {})
            if isinstance(img_data, dict):
                images.append({
                    "url": img_data.get("url", ""),
                    "alt": question_text[:100]  # Use question as alt text
                })

    # Extract extended attributes
    direct_instruction_raw = ""
    common_misconceptions = []
    learning_objective = ""
    stimulus_description = ""

    for attr in athena_row.get("extended_attributes", []):
        if not isinstance(attr, dict):
            continue

        attr_type = attr.get("type", "")
        attr_value = attr.get("value", "")

        if attr_type == "DirectInstruction":
            direct_instruction_raw = attr_value
        elif attr_type == "CommonMisconception":
            common_misconceptions.append(attr_value)
        elif attr_type == "LearningObjective":
            learning_objective = attr_value
        elif attr_type == "StimulusTypeSpecification":
            stimulus_description = attr_value

    # Parse Direct Instruction
    di_parsed = parse_direct_instruction(direct_instruction_raw)

    # Extract difficulty from attributes
    difficulty = None
    for attr in athena_row.get("attributes", []):
        if isinstance(attr, dict) and attr.get("attributeName") == "difficulty":
            difficulty = attr.get("attributeValue", "").lower()
            break

    # Determine language
    is_arabic = bool(re.search(r'[\u0600-\u06FF]', question_text))
    language = "ar" if is_arabic else "en"

    # Build searchable text
    searchable_text = build_searchable_text(athena_row)

    # Generate content hash
    content_hash = compute_content_hash(question_text)

    # Build database row
    db_row = {
        # Core Identification
        "content_hash": content_hash,
        "source_name": "athena",
        "source_type": "athena_api",

        # Academic Classification
        "subject": athena_row.get("subject"),
        "grade": int(athena_row.get("grade")) if athena_row.get("grade") else None,
        "unit_name": athena_row.get("unit_name"),
        "cluster": athena_row.get("lesson_name"),  # Athena lesson_name = curriculum cluster
        "lesson_title": athena_row.get("level_name"),  # Athena level_name = curriculum lesson_title

        # Question Content
        "question_en": question_text if language == "en" else None,
        "question_ar": question_text if language == "ar" else None,
        "answer_en": answer_text if language == "en" else None,
        "answer_ar": answer_text if language == "ar" else None,
        "explanation_en": explanation_text if language == "en" else None,
        "explanation_ar": explanation_text if language == "ar" else None,
        "language": language,
        "images": images if images else None,
        "stimulus_description": stimulus_description if stimulus_description else None,

        # Question Metadata
        "question_type": athena_row.get("content_type_name", "").lower().replace(" ", "_"),
        "difficulty": difficulty,
        "stimulus_needed": len(images) > 0,

        # Direct Instruction & Pedagogy
        "direct_instruction_raw": direct_instruction_raw if direct_instruction_raw else None,
        "prerequisite_skills": di_parsed.get("prerequisite_skills") if di_parsed.get("prerequisite_skills") else None,
        "microskills": di_parsed.get("microskills") if di_parsed.get("microskills") else None,
        "vocabulary": di_parsed.get("vocabulary") if di_parsed.get("vocabulary") else None,
        "question_stems": di_parsed.get("question_stems") if di_parsed.get("question_stems") else None,
        "step_by_step_explanations": di_parsed.get("step_by_step_explanations") if di_parsed.get("step_by_step_explanations") else None,
        "common_misconceptions": common_misconceptions if common_misconceptions else None,
        "learning_objective": learning_objective if learning_objective else None,
        "worked_example": worked_example if worked_example else None,

        # RAG & Search
        "searchable_text": searchable_text,

        # Source-Specific Metadata
        "athena_content_id": athena_row.get("content_id"),
        "athena_level_id": athena_row.get("level_id"),
        "athena_unit_id": athena_row.get("unit_id"),
        "athena_lesson_id": athena_row.get("lesson_id"),

        # Tracking & Quality
        "raw_data": athena_row,
        "extracted_at": athena_row.get("extracted_at"),
        "validation_status": "unvalidated",
    }

    return db_row


def import_athena_file(file_path: Path, batch_size: int = 100, generate_embeddings: bool = False) -> Dict[str, int]:
    """Import a single Athena JSONL file into Supabase."""

    logger.info(f"Processing {file_path.name}...")

    stats = {
        "total": 0,
        "inserted": 0,
        "skipped": 0,
        "errors": 0
    }

    batch = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            stats["total"] += 1

            try:
                athena_row = json.loads(line)
                db_row = extract_question_data(athena_row)

                # Generate embedding if requested
                if generate_embeddings and OPENAI_API_KEY:
                    embedding = generate_embedding(db_row["searchable_text"])
                    db_row["dense_vector"] = embedding

                batch.append(db_row)

                # Insert batch when full
                if len(batch) >= batch_size:
                    result = insert_batch(batch)
                    stats["inserted"] += result["inserted"]
                    stats["skipped"] += result["skipped"]
                    stats["errors"] += result["errors"]
                    batch = []

                    logger.info(f"Progress: {stats['total']} processed, {stats['inserted']} inserted")

            except Exception as e:
                logger.error(f"Error processing line {line_num}: {e}")
                stats["errors"] += 1

    # Insert remaining batch
    if batch:
        result = insert_batch(batch)
        stats["inserted"] += result["inserted"]
        stats["skipped"] += result["skipped"]
        stats["errors"] += result["errors"]

    return stats


def insert_batch(batch: List[Dict]) -> Dict[str, int]:
    """Insert a batch of rows into Supabase."""
    result = {"inserted": 0, "skipped": 0, "errors": 0}

    try:
        # Use upsert to handle duplicates based on content_hash
        response = supabase.table("extracted_questions").upsert(
            batch,
            on_conflict="content_hash",
            ignore_duplicates=True
        ).execute()

        result["inserted"] = len(batch)

    except Exception as e:
        logger.error(f"Batch insert failed: {e}")
        # Try individual inserts
        for row in batch:
            try:
                supabase.table("extracted_questions").insert(row).execute()
                result["inserted"] += 1
            except Exception as insert_error:
                # Check if it's a duplicate
                if "duplicate" in str(insert_error).lower() or "unique" in str(insert_error).lower():
                    result["skipped"] += 1
                else:
                    logger.error(f"Failed to insert row: {insert_error}")
                    result["errors"] += 1

    return result


def main():
    """Main import function."""

    # Find all Athena extracted files
    data_dir = Path(__file__).parent.parent / "data" / "athena_extracted"
    athena_files = list(data_dir.glob("math_questions_grade_*.jsonl"))

    if not athena_files:
        logger.error(f"No Athena files found in {data_dir}")
        return

    logger.info(f"Found {len(athena_files)} Athena files to import")

    # Ask about embeddings
    generate_embeddings = False
    if OPENAI_API_KEY:
        response = input("Generate embeddings? (y/n, default: n): ").lower()
        generate_embeddings = response == 'y'
        if generate_embeddings:
            logger.info("⚠️  Embedding generation enabled - this will be slower and use OpenAI credits")

    # Import all files
    total_stats = {"total": 0, "inserted": 0, "skipped": 0, "errors": 0}

    for file_path in sorted(athena_files):
        file_stats = import_athena_file(file_path, generate_embeddings=generate_embeddings)

        for key in total_stats:
            total_stats[key] += file_stats[key]

        logger.info(f"✓ {file_path.name}: {file_stats['inserted']} inserted, {file_stats['skipped']} skipped, {file_stats['errors']} errors")

    # Final summary
    logger.info("\n" + "="*60)
    logger.info("IMPORT COMPLETE")
    logger.info("="*60)
    logger.info(f"Total rows processed: {total_stats['total']}")
    logger.info(f"Successfully inserted: {total_stats['inserted']}")
    logger.info(f"Skipped (duplicates): {total_stats['skipped']}")
    logger.info(f"Errors: {total_stats['errors']}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
