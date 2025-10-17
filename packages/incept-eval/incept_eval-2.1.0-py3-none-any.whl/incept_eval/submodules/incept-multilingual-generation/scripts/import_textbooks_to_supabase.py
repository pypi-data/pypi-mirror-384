#!/usr/bin/env python3
"""
Import textbook extracted questions into Supabase extracted_questions table.

Usage:
    python scripts/import_textbooks_to_supabase.py

Requirements:
    pip install supabase openai python-dotenv

Environment variables (in .env):
    SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
    SUPABASE_SERVICE_KEY=[YOUR-SERVICE-ROLE-KEY]
    OPENAI_API_KEY=[YOUR-OPENAI-KEY]  # Optional, for embeddings
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


def build_searchable_text(textbook_row: Dict) -> str:
    """Build optimized searchable text for embeddings."""
    parts = []

    # Add topic (most general)
    topic = textbook_row.get("topic_english") or textbook_row.get("topic_arabic")
    if topic and isinstance(topic, str):
        parts.append(topic)

    # Add skill (more specific)
    skill = textbook_row.get("skill_english") or textbook_row.get("skill_arabic")
    if skill and isinstance(skill, str):
        parts.append(skill)

    # Add question text (most important)
    question = textbook_row.get("question_english") or textbook_row.get("question_arabic")
    if question and isinstance(question, str):
        parts.append(question)

    return " ".join(parts).strip()


def compute_content_hash(question_text: str) -> str:
    """Generate SHA256 hash for deduplication."""
    # Normalize text: lowercase, remove extra whitespace
    normalized = re.sub(r'\s+', ' ', question_text.lower().strip())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def extract_source_name(source_file: str) -> str:
    """Extract clean source name from PDF filename."""
    # Remove .pdf extension
    name = source_file.replace('.pdf', '')
    # Remove path if present
    name = name.split('/')[-1]
    return name


def detect_language(textbook_row: Dict) -> str:
    """Detect primary language of the question."""
    has_english = bool(textbook_row.get("question_english"))
    has_arabic = bool(textbook_row.get("question_arabic"))

    if has_english and has_arabic:
        return "both"
    elif has_arabic:
        return "ar"
    elif has_english:
        return "en"
    else:
        # Default based on topic/skill
        topic = str(textbook_row.get("topic_arabic", ""))
        if re.search(r'[\u0600-\u06FF]', topic):
            return "ar"
        return "en"


def extract_question_data(textbook_row: Dict) -> Dict[str, Any]:
    """Extract and transform textbook row into database schema."""

    # Determine language
    language = detect_language(textbook_row)

    # Get question text for hash
    question_text = textbook_row.get("question_english") or textbook_row.get("question_arabic") or ""

    # Build searchable text
    searchable_text = build_searchable_text(textbook_row)

    # Generate content hash
    content_hash = compute_content_hash(question_text)

    # Extract source name from file
    source_file = textbook_row.get("source_file", "")
    source_name = extract_source_name(source_file)

    # Build database row
    db_row = {
        # Core Identification
        "content_hash": content_hash,
        "source_name": source_name,
        "source_type": "textbook_pdf",

        # Academic Classification
        "subject": "mathematics",  # All textbook extractions are math
        "grade": int(textbook_row.get("grade")) if textbook_row.get("grade") else None,
        # Note: unit_name, cluster, lesson_title will be mapped later via curriculum matching
        # For now, we'll use topic/skill as temporary placeholders
        "unit_name": textbook_row.get("topic_english"),  # Temporary - will be remapped

        # Question Content
        "question_en": textbook_row.get("question_english"),
        "question_ar": textbook_row.get("question_arabic"),
        "answer_en": textbook_row.get("answer_english"),
        "answer_ar": textbook_row.get("answer_arabic"),
        "language": language,

        # Question Metadata
        # Note: difficulty, question_type will need to be inferred or set later

        # RAG & Search
        "searchable_text": searchable_text,

        # Source-Specific Metadata
        "textbook_page": textbook_row.get("page"),
        "textbook_file": source_file,

        # Tracking & Quality
        "raw_data": textbook_row,
        "extracted_at": textbook_row.get("extracted_at"),
        "validation_status": "unvalidated",

        # Add topic/skill as metadata for later curriculum mapping
        # We'll store these in a JSONB field for now
        "raw_data": {
            **textbook_row,
            "topic_english": textbook_row.get("topic_english"),
            "topic_arabic": textbook_row.get("topic_arabic"),
            "skill_english": textbook_row.get("skill_english"),
            "skill_arabic": textbook_row.get("skill_arabic"),
        }
    }

    return db_row


def import_textbook_file(file_path: Path, batch_size: int = 100, generate_embeddings: bool = False) -> Dict[str, int]:
    """Import a textbook JSONL file into Supabase."""

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
                textbook_row = json.loads(line)
                db_row = extract_question_data(textbook_row)

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

    # Find textbook files
    data_dir = Path(__file__).parent.parent / "data" / "textbooks" / "Mathematics"
    textbook_file = data_dir / "all_problems.jsonl"

    if not textbook_file.exists():
        logger.error(f"Textbook file not found: {textbook_file}")
        return

    logger.info(f"Found textbook file: {textbook_file}")

    # Ask about embeddings
    generate_embeddings = False
    if OPENAI_API_KEY:
        response = input("Generate embeddings? (y/n, default: n): ").lower()
        generate_embeddings = response == 'y'
        if generate_embeddings:
            logger.info("⚠️  Embedding generation enabled - this will be slower and use OpenAI credits")

    # Import file
    file_stats = import_textbook_file(textbook_file, generate_embeddings=generate_embeddings)

    # Final summary
    logger.info("\n" + "="*60)
    logger.info("IMPORT COMPLETE")
    logger.info("="*60)
    logger.info(f"Total rows processed: {file_stats['total']}")
    logger.info(f"Successfully inserted: {file_stats['inserted']}")
    logger.info(f"Skipped (duplicates): {file_stats['skipped']}")
    logger.info(f"Errors: {file_stats['errors']}")
    logger.info("="*60)
    logger.info("\nNote: unit_name, cluster, lesson_title, and standards fields")
    logger.info("will need to be mapped to curriculum using a separate script.")


if __name__ == "__main__":
    main()
