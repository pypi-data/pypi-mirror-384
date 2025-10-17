#!/usr/bin/env python3
"""
Import curriculum standards into Supabase curriculum table.

Usage:
    python scripts/import_curriculum_to_supabase.py

Requirements:
    pip install supabase google-genai python-dotenv

Environment variables (in .env):
    SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
    SUPABASE_SERVICE_KEY=[YOUR-SERVICE-ROLE-KEY]
    GOOGLE_API_KEY=[YOUR-GEMINI-API-KEY]
"""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from supabase import create_client, Client
from src.embeddings import Embeddings

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

if not all([SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embeddings_service = Embeddings()


def generate_embedding(text: str) -> Optional[List[float]]:
    """Generate OpenAI text-embedding-3-large embedding for text (1536 dims)."""
    if not text:
        return None

    try:
        return embeddings_service.get_openai_embedding(text)
    except Exception as e:
        logger.warning(f"Failed to generate embedding: {e}")
        return None


def build_searchable_text(row: Dict) -> str:
    """Build optimized searchable text for embeddings."""
    parts = []

    # Add hierarchical context
    if row.get("unit_name"):
        parts.append(row["unit_name"])
    if row.get("cluster"):
        parts.append(row["cluster"])
    if row.get("lesson_title"):
        parts.append(row["lesson_title"])
    if row.get("substandard_description"):
        parts.append(row["substandard_description"])

    return " ".join(parts).strip()


def extract_curriculum_data(curriculum_row: Dict, grade: int) -> Dict[str, Any]:
    """Extract and transform curriculum row into database schema."""

    # Build searchable text
    searchable_text = build_searchable_text(curriculum_row)

    # Extract prerequisites (if array)
    prerequisites = curriculum_row.get("prerequisites", [])
    if not isinstance(prerequisites, list):
        prerequisites = []

    # Extract common misconceptions (if array)
    misconceptions = curriculum_row.get("common_misconceptions", [])
    if not isinstance(misconceptions, list):
        misconceptions = []

    # Build database row
    db_row = {
        # Grade (from filename)
        "grade": grade,

        # Domain
        "domain": curriculum_row.get("domain"),
        "domain_id": curriculum_row.get("domain_id"),

        # Unit
        "unit_number": int(float(curriculum_row["unit_number"])) if curriculum_row.get("unit_number") else None,
        "unit_name": curriculum_row.get("unit_name"),

        # Cluster
        "cluster_id": curriculum_row.get("cluster_id"),
        "cluster": curriculum_row.get("cluster"),

        # Lesson
        "lesson_title": curriculum_row.get("lesson_title"),
        "lesson_order": curriculum_row.get("lesson_order"),

        # Standards (Level 1)
        "standard_id_l1": curriculum_row.get("standard_id_l1"),
        "standard_description_l1": curriculum_row.get("standard_description_l1"),

        # Substandard (most granular)
        "substandard_id": curriculum_row.get("substandard_id"),
        "substandard_description": curriculum_row.get("substandard_description"),

        # Additional metadata
        "prerequisites": prerequisites if prerequisites else None,
        "instructional_approach": curriculum_row.get("instructional_approach"),
        "common_misconceptions": misconceptions if misconceptions else None,
        "worked_examples": curriculum_row.get("worked_examples"),
        "assessment_boundary": curriculum_row.get("assessment_boundary"),

        # Searchable text
        "searchable_text": searchable_text,

        # Raw data
        "raw_data": curriculum_row,
    }

    return db_row


def import_curriculum_file(file_path: Path, grade: int, batch_size: int = 50) -> Dict[str, int]:
    """Import a single curriculum JSONL file into Supabase."""

    logger.info(f"Processing {file_path.name} (Grade {grade})...")

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
                curriculum_row = json.loads(line)

                # Skip rows without substandard_id (incomplete/placeholder rows)
                if not curriculum_row.get("substandard_id"):
                    stats["skipped"] += 1
                    continue

                db_row = extract_curriculum_data(curriculum_row, grade)

                # Generate embedding
                embedding = generate_embedding(db_row["searchable_text"])
                if embedding:
                    db_row["embedding"] = embedding
                else:
                    logger.warning(f"No embedding generated for row {line_num}")

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
        # Use upsert to handle duplicates based on substandard_id
        response = supabase.table("curriculum").upsert(
            batch,
            on_conflict="substandard_id",
            ignore_duplicates=True
        ).execute()

        result["inserted"] = len(batch)

    except Exception as e:
        logger.error(f"Batch insert failed: {e}")
        # Try individual inserts
        for row in batch:
            try:
                supabase.table("curriculum").insert(row).execute()
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

    # Find all curriculum files
    curriculum_dir = Path(__file__).parent.parent / "edu_configs"
    curriculum_files = sorted(curriculum_dir.glob("curriculum_grade_*.jsonl"))

    if not curriculum_files:
        logger.error(f"No curriculum files found in {curriculum_dir}")
        return

    logger.info(f"Found {len(curriculum_files)} curriculum files to import")

    # Import all files
    total_stats = {"total": 0, "inserted": 0, "skipped": 0, "errors": 0}

    for file_path in curriculum_files:
        # Extract grade from filename (e.g., curriculum_grade_3.jsonl -> 3)
        match = re.search(r'curriculum_grade_(\d+)\.jsonl', file_path.name)
        if not match:
            logger.warning(f"Could not extract grade from {file_path.name}, skipping")
            continue

        grade = int(match.group(1))

        file_stats = import_curriculum_file(file_path, grade)

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
