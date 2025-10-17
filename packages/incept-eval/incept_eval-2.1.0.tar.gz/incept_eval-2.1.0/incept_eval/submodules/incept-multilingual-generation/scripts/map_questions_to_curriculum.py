#!/usr/bin/env python3
"""
Map extracted questions to curriculum standards using hybrid approach.

Usage:
    python scripts/map_questions_to_curriculum.py --limit 5  # QC mode
    python scripts/map_questions_to_curriculum.py           # Full run

Requirements:
    pip install supabase python-dotenv numpy pydantic tqdm

Environment variables (in .env):
    SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
    SUPABASE_SERVICE_KEY=[YOUR-SERVICE-ROLE-KEY]
    OPENAI_API_KEY=[YOUR-OPENAI-KEY]  # Used by src/embeddings.py and src/llms.py
"""

import json
import logging
import os
import sys
import argparse
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import numpy as np
from difflib import SequenceMatcher
from pydantic import BaseModel, Field
from tqdm import tqdm
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.embeddings import Embeddings
from src.llms import produce_structured_response

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
    raise ValueError("Missing required environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
embeddings_service = Embeddings()


# Pydantic models for structured LLM response
class CurriculumMatch(BaseModel):
    """Single question-to-curriculum match."""
    question_id: str = Field(description="UUID of the question being matched")
    selected_substandard_id: Optional[str] = Field(description="Matched curriculum substandard ID, or null if no good match")
    confidence: float = Field(description="Confidence score 0.0-1.0")
    reasoning: str = Field(description="Brief explanation of the match")


class CurriculumMatchResults(BaseModel):
    """Batch of curriculum matches."""
    matches: List[CurriculumMatch]


class CurriculumMapper:
    def __init__(self):
        self.curriculum_by_grade = {}
        self.load_curriculum_from_db()

    def load_curriculum_from_db(self):
        """Load curriculum from Supabase database."""
        logger.info("Loading curriculum from database...")

        for grade in range(3, 9):
            response = supabase.table("curriculum").select("*").eq("grade", grade).execute()
            rows = response.data
            self.curriculum_by_grade[grade] = rows
            logger.info(f"Loaded {len(rows)} curriculum rows for grade {grade}")

        total = sum(len(rows) for rows in self.curriculum_by_grade.values())
        logger.info(f"Total curriculum rows loaded: {total}")

    def exact_match(self, question: Dict, grade: int) -> Optional[Tuple[Dict, float, str]]:
        """Try exact text matching for Athena questions."""
        if not question.get("lesson_title") or not question.get("cluster"):
            return None

        curriculum = self.curriculum_by_grade.get(grade, [])

        for curr_row in curriculum:
            # Match on lesson_title (Athena level_name = curriculum lesson_title)
            if (question["lesson_title"] == curr_row.get("lesson_title") and
                question["cluster"] == curr_row.get("cluster")):
                return curr_row, 1.0, "exact_match"

        return None

    def fuzzy_match(self, question: Dict, grade: int, threshold: float = 0.85) -> Optional[Tuple[Dict, float, str]]:
        """Try fuzzy text matching for near-exact matches."""
        if not question.get("lesson_title"):
            return None

        curriculum = self.curriculum_by_grade.get(grade, [])
        best_match = None
        best_score = 0.0

        for curr_row in curriculum:
            if not curr_row.get("lesson_title"):
                continue

            # Calculate similarity
            similarity = SequenceMatcher(
                None,
                question["lesson_title"].lower(),
                curr_row["lesson_title"].lower()
            ).ratio()

            if similarity > best_score:
                best_score = similarity
                best_match = curr_row

        if best_score >= threshold:
            return best_match, best_score, "fuzzy_match"

        return None

    def embedding_search(self, question: Dict, grade: int, k: int = 20) -> List[Dict]:
        """Find top-k curriculum candidates using database embeddings."""
        curriculum = self.curriculum_by_grade.get(grade, [])
        if not curriculum:
            return []

        # Generate question embedding using OpenAI text-embedding-3-small (matches curriculum)
        try:
            question_text = question.get("searchable_text", "")[:8000]
            question_embedding = np.array(
                embeddings_service.get_openai_embedding(question_text, model="text-embedding-3-small")
            )
        except Exception as e:
            logger.error(f"Failed to embed question {question['id']}: {e}")
            return []

        # Calculate cosine similarities with curriculum embeddings from DB
        candidates = []
        for curr_row in curriculum:
            if not curr_row.get("embedding"):
                continue

            # Parse embedding (may be stored as string/JSON in database)
            embedding_data = curr_row["embedding"]
            if isinstance(embedding_data, str):
                # Parse JSON string to list
                embedding_data = json.loads(embedding_data)
            curr_embedding = np.array(embedding_data, dtype=np.float32)

            similarity = np.dot(question_embedding, curr_embedding) / (
                np.linalg.norm(question_embedding) * np.linalg.norm(curr_embedding)
            )
            candidates.append({
                "row": curr_row,
                "similarity": float(similarity),
                "text": curr_row.get("searchable_text", "")
            })

        # Sort by similarity and return top-k
        candidates.sort(key=lambda x: x["similarity"], reverse=True)
        return candidates[:k]

    def llm_select_best_match(self, questions_with_candidates: List[Dict]) -> List[CurriculumMatch]:
        """Use GPT-4o to select best curriculum match from candidates."""

        # Prepare batch for LLM
        llm_input = []
        for item in questions_with_candidates:
            question = item["question"]
            candidates = item["candidates"]

            llm_input.append({
                "question_id": question["id"],
                "grade": question["grade"],
                "question_text": question.get("question_en") or question.get("question_ar") or "",
                "current_metadata": {
                    "unit": question.get("unit_name"),
                    "cluster": question.get("cluster"),
                    "lesson": question.get("lesson_title"),
                    "source": question.get("source_type")
                },
                "candidates": [
                    {
                        "substandard_id": c["row"].get("substandard_id"),
                        "substandard_description": c["row"].get("substandard_description"),
                        "lesson_title": c["row"].get("lesson_title"),
                        "cluster": c["row"].get("cluster"),
                        "unit_name": c["row"].get("unit_name"),
                        "standard_id": c["row"].get("standard_id_l1"),
                        "similarity_score": c.get("similarity", 0.0)
                    }
                    for c in candidates
                ]
            })

        # Build prompt
        system_instructions = """You are an expert educational curriculum mapper. Your task is to match educational questions to the most appropriate curriculum standard.

Selection criteria:
1. Grade-level appropriateness (must match exactly)
2. Mathematical topic alignment (multiplication, fractions, etc.)
3. Skill specificity (prefer more specific matches)
4. Contextual similarity (word problems vs computation)

If no good match exists (confidence < 0.5), set selected_substandard_id to null."""

        user_content = f"""Match these questions to curriculum standards:

{json.dumps(llm_input, indent=2)}"""

        try:
            result = produce_structured_response(
                messages=[
                    {"role": "system", "content": system_instructions},
                    {"role": "user", "content": user_content}
                ],
                structure_model=CurriculumMatchResults,
                model="gpt-4o",
                temperature=0.0,
                provider="openai"
            )
            return result.matches

        except Exception as e:
            logger.error(f"LLM mapping failed: {e}")
            return []


def fetch_questions_to_map(limit_per_type: Optional[int] = None, source: str = "both") -> Tuple[List[Dict], List[Dict]]:
    """Fetch questions from Supabase that need curriculum mapping."""

    athena_questions = []
    textbook_questions = []

    # Fetch Athena questions (only unmapped ones)
    if source in ["athena", "both"]:
        # Supabase has 1000-row default limit, need pagination for larger requests
        target_limit = limit_per_type if limit_per_type else 10000  # Default to 10k if no limit
        page_size = 1000
        offset = 0
        athena_questions = []

        while len(athena_questions) < target_limit:
            batch_size = min(page_size, target_limit - len(athena_questions))

            athena_query = (supabase.table("extracted_questions")
                            .select("*")
                            .eq("source_type", "athena_api")
                            .is_("substandard_id", "null")
                            .range(offset, offset + batch_size - 1))

            athena_response = athena_query.execute()
            batch = athena_response.data

            if not batch:
                break  # No more data

            athena_questions.extend(batch)
            offset += len(batch)

            if len(batch) < batch_size:
                break  # Last page

        logger.info(f"Fetched {len(athena_questions)} unmapped Athena questions")

    # Fetch Textbook questions (need full mapping) - only grades 3-8, only unmapped
    if source in ["textbook", "both"]:
        # Supabase has 1000-row default limit, need pagination for larger requests
        target_limit = limit_per_type if limit_per_type else 10000  # Default to 10k if no limit
        page_size = 1000
        offset = 0
        textbook_questions = []

        while len(textbook_questions) < target_limit:
            batch_size = min(page_size, target_limit - len(textbook_questions))

            textbook_query = (supabase.table("extracted_questions")
                              .select("*")
                              .eq("source_type", "textbook_pdf")
                              .gte("grade", 3)
                              .lte("grade", 8)
                              .is_("substandard_id", "null")
                              .range(offset, offset + batch_size - 1))

            textbook_response = textbook_query.execute()
            batch = textbook_response.data

            if not batch:
                break  # No more data

            textbook_questions.extend(batch)
            offset += len(batch)

            if len(batch) < batch_size:
                break  # Last page

        logger.info(f"Fetched {len(textbook_questions)} unmapped Textbook questions (grades 3-8)")

    return athena_questions, textbook_questions


def update_question_mapping(question_id: str, curriculum_row: Dict, confidence: float, method: str, reasoning: str = ""):
    """Update question in database with curriculum mapping."""

    try:
        # First, fetch the existing raw_data to preserve it
        existing = supabase.table("extracted_questions").select("raw_data").eq("id", question_id).execute()
        existing_raw_data = existing.data[0].get("raw_data", {}) if existing.data else {}

        # Merge mapping metadata into existing raw_data
        updated_raw_data = {
            **existing_raw_data,  # Preserve original extraction data
            "mapping_confidence": confidence,
            "mapping_method": method,
            "mapping_reasoning": reasoning,
            "mapped_at": datetime.utcnow().isoformat()
        }

        update_data = {
            # Curriculum hierarchy
            "domain": curriculum_row.get("domain"),
            "domain_id": curriculum_row.get("domain_id"),
            "unit_number": curriculum_row.get("unit_number"),
            "unit_name": curriculum_row.get("unit_name"),
            "cluster": curriculum_row.get("cluster"),
            "cluster_id": curriculum_row.get("cluster_id"),
            "lesson_title": curriculum_row.get("lesson_title"),
            "lesson_order": curriculum_row.get("lesson_order"),

            # Standards
            "standard_id": curriculum_row.get("standard_id_l1"),
            "standard_description": curriculum_row.get("standard_description_l1"),
            "substandard_id": curriculum_row.get("substandard_id"),
            "substandard_description": curriculum_row.get("substandard_description"),

            # Metadata (merged with original)
            "raw_data": updated_raw_data
        }

        supabase.table("extracted_questions").update(update_data).eq("id", question_id).execute()
        logger.debug(f"Updated question {question_id} with {method} (confidence: {confidence:.2f})")
    except Exception as e:
        logger.error(f"Failed to update question {question_id}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Map questions to curriculum standards")
    parser.add_argument("--limit", type=int, default=None, help="Limit questions per type for QC (e.g., 5)")
    parser.add_argument("--source", type=str, default="both", choices=["athena", "textbook", "both"],
                        help="Which source to process: athena, textbook, or both (default: both)")
    args = parser.parse_args()

    logger.info("="*60)
    logger.info("CURRICULUM MAPPING STARTED")
    logger.info("="*60)

    if args.limit:
        logger.info(f"🔍 QC MODE: Processing {args.limit} questions per type")
    else:
        logger.info("📊 FULL MODE: Processing all questions")

    logger.info("📝 Detailed audit logs will be output to console")

    # Initialize mapper
    mapper = CurriculumMapper()

    # Fetch questions
    athena_questions, textbook_questions = fetch_questions_to_map(limit_per_type=args.limit, source=args.source)
    all_questions = athena_questions + textbook_questions

    logger.info(f"\nProcessing {len(all_questions)} questions ({len(athena_questions)} Athena, {len(textbook_questions)} textbook)\n")

    stats = {
        "athena_exact": 0,
        "athena_llm": 0,
        "textbook_llm": 0,
        "total_mapped": 0,
        "failed": 0
    }

    def process_single_question(question):
        """Process a single question completely in one thread: exact match → embedding → LLM → database."""
        question_id = question["id"]
        question_text = question.get("question_en", "")[:100]
        grade = question.get("grade")
        is_athena = question["source_type"] == "athena_api"

        # Validate grade
        if not grade or grade not in mapper.curriculum_by_grade:
            return ("failed", question_id, f"Invalid grade: {grade}", question_text)

        # Try exact match (Athena only)
        if is_athena:
            match_result = mapper.exact_match(question, grade)
            if match_result:
                curr_row, confidence, method = match_result
                update_question_mapping(question_id, curr_row, confidence, method)
                return ("athena_exact", question_id, None, None)

        # Embedding search
        candidates = mapper.embedding_search(question, grade, k=20)
        if not candidates:
            return ("failed", question_id, "No embedding candidates found", question_text)

        # LLM selection
        item = {"question": question, "candidates": candidates}
        results = mapper.llm_select_best_match([item])

        if not results:
            return ("failed", question_id, "No LLM results returned", question_text)

        # Process LLM result
        for result in results:
            substandard_id = result.selected_substandard_id
            confidence = result.confidence
            reasoning = result.reasoning

            if not substandard_id:
                return ("failed", question_id, f"LLM returned null substandard_id | Confidence: {confidence:.2f} | Reasoning: {reasoning}", question_text)

            if confidence < 0.5:
                return ("failed", question_id, f"Low confidence: {confidence:.2f} | Substandard: {substandard_id} | Reasoning: {reasoning}", question_text)

            # Find full curriculum row
            curr_row = next(
                (c["row"] for c in candidates if c["row"].get("substandard_id") == substandard_id),
                None
            )

            if not curr_row:
                return ("failed", question_id, f"LLM selected substandard {substandard_id} not in candidates | Confidence: {confidence:.2f}", question_text)

            method = "semantic_llm"
            update_question_mapping(question_id, curr_row, confidence, method, reasoning)

            return ("athena_llm" if is_athena else "textbook_llm", question_id, None, None)

        return ("failed", question_id, "No result processed", question_text)

    # Process questions in parallel (10 concurrent max)
    max_workers = 10
    failure_details = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        from concurrent.futures import as_completed

        # Submit all questions but only 10 will run concurrently
        futures = {executor.submit(process_single_question, q): q for q in all_questions}

        # Use tqdm progress bar - covers ALL steps (exact match, embedding, LLM, DB update)
        with tqdm(total=len(futures), desc="Processing questions", unit=" q", ncols=100) as pbar:
            for future in as_completed(futures):
                result_type, question_id, failure_reason, question_text = future.result()

                if result_type == "athena_exact":
                    stats["athena_exact"] += 1
                    stats["total_mapped"] += 1
                elif result_type == "athena_llm":
                    stats["athena_llm"] += 1
                    stats["total_mapped"] += 1
                elif result_type == "textbook_llm":
                    stats["textbook_llm"] += 1
                    stats["total_mapped"] += 1
                elif result_type == "failed":
                    stats["failed"] += 1
                    failure_details.append({
                        "question_id": question_id,
                        "reason": failure_reason,
                        "question_text": question_text
                    })

                pbar.update(1)
                pbar.set_postfix_str(f"✓ {stats['total_mapped']} | ✗ {stats['failed']}")

    # Final Summary
    logger.info("\n" + "="*60)
    logger.info("MAPPING COMPLETE")
    logger.info("="*60)
    logger.info(f"Athena - Exact matches (bypassed LLM): {stats['athena_exact']}")
    logger.info(f"Athena - LLM matches: {stats['athena_llm']}")
    logger.info(f"Textbook - LLM matches: {stats['textbook_llm']}")
    logger.info(f"Total mapped: {stats['total_mapped']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info("="*60)

    # Failure Analysis
    if failure_details:
        logger.info("\n" + "="*60)
        logger.info("FAILURE ANALYSIS")
        logger.info("="*60)

        # Group by failure reason
        from collections import Counter
        failure_reasons = Counter([f["reason"].split("|")[0].strip() for f in failure_details])

        logger.info("\nFailure Breakdown:")
        for reason, count in failure_reasons.most_common():
            logger.info(f"  {reason}: {count}")

        # Separate LLM errors from legitimate rejections
        llm_errors = [f for f in failure_details if "not in candidates" in f["reason"] or "No LLM results" in f["reason"] or "No result processed" in f["reason"]]
        legitimate_rejections = [f for f in failure_details if f not in llm_errors]

        # Show LLM errors separately (these are actual bugs)
        if llm_errors:
            logger.info(f"\n⚠️  LLM ERRORS (potential bugs): {len(llm_errors)}")
            for i, failure in enumerate(llm_errors[:10], 1):
                logger.info(f"\n  [{i}] Question ID: {failure['question_id']}")
                logger.info(f"      Question: {failure['question_text']}...")
                logger.info(f"      Error: {failure['reason']}")

        # Show random sample of legitimate rejections
        logger.info(f"\n📊 LEGITIMATE REJECTIONS (random sample of 10 from {len(legitimate_rejections)}):")
        sample_size = min(10, len(legitimate_rejections))
        sample = random.sample(legitimate_rejections, sample_size) if legitimate_rejections else []

        for i, failure in enumerate(sample, 1):
            logger.info(f"\n  [{i}] Question ID: {failure['question_id']}")
            logger.info(f"      Question: {failure['question_text']}...")
            logger.info(f"      Reason: {failure['reason']}")

        logger.info("\n" + "="*60)


if __name__ == "__main__":
    main()
