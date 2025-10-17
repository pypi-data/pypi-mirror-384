#!/usr/bin/env python3
"""
Generate embeddings for questions in the extracted_questions table.

This script:
1. Fetches questions from Supabase that don't have embeddings
2. Generates embeddings using OpenAI text-embedding-3-small (1536 dimensions)
3. Updates the dense_vector column in batches
4. Supports resuming from failures with progress tracking
"""

import os
import sys
import logging
import time
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from supabase import create_client, Client
from src.embeddings import Embeddings
from src.config import Config

logging.basicConfig(
    level=logging.WARNING,  # Reduce verbosity to not interfere with progress bar
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # But keep our script's logs at INFO


class QuestionEmbeddingGenerator:
    """Generates and stores embeddings for questions in PostgreSQL."""

    def __init__(self, batch_size: int = 100, max_workers: int = 5):
        """
        Initialize the generator.

        Args:
            batch_size: Number of questions to process per batch
            max_workers: Number of parallel workers for embedding generation
        """
        self.batch_size = batch_size
        self.max_workers = max_workers

        # Initialize clients
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

        if not all([supabase_url, supabase_key]):
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")

        self.supabase: Client = create_client(supabase_url, supabase_key)
        self.embeddings = Embeddings()

        logger.info("✓ Initialized QuestionEmbeddingGenerator")
        logger.info(f"  Embedding model: OpenAI text-embedding-3-small (1536 dimensions)")
        logger.info(f"  Batch size: {batch_size}")
        logger.info(f"  Max workers: {max_workers}")

    def build_searchable_text(self, question: Dict[str, Any]) -> str:
        """
        Build searchable text from question data.

        Combines relevant fields to create rich context for embedding.
        """
        parts = []

        # Add grade and subject
        if question.get('grade'):
            parts.append(f"Grade {question['grade']}")
        if question.get('subject'):
            parts.append(question['subject'])

        # Add curriculum info
        if question.get('domain'):
            parts.append(f"Domain: {question['domain']}")
        if question.get('lesson_title'):
            parts.append(f"Lesson: {question['lesson_title']}")
        if question.get('standard_description'):
            parts.append(f"Standard: {question['standard_description']}")
        if question.get('substandard_description'):
            parts.append(f"Substandard: {question['substandard_description']}")

        # Add question text (most important)
        question_text = question.get('question_en') or question.get('question_ar') or ''
        if question_text:
            parts.append(f"Question: {question_text}")

        # Add answer for context
        answer_text = question.get('answer_en') or question.get('answer_ar') or ''
        if answer_text:
            parts.append(f"Answer: {answer_text}")

        return " | ".join(parts)

    def get_total_count(self) -> int:
        """Get total number of questions without embeddings."""
        response = self.supabase.table("extracted_questions") \
            .select("*", count="exact") \
            .is_("dense_vector", "null") \
            .execute()
        return response.count

    def fetch_batch(self, offset: int) -> List[Dict[str, Any]]:
        """
        Fetch a batch of questions without embeddings.

        Args:
            offset: Number of records to skip

        Returns:
            List of question dictionaries
        """
        response = self.supabase.table("extracted_questions") \
            .select("*") \
            .is_("dense_vector", "null") \
            .range(offset, offset + self.batch_size - 1) \
            .execute()

        return response.data if response.data else []

    def generate_embedding_for_question(self, question: Dict[str, Any]) -> tuple[str, List[float], str]:
        """
        Generate embedding for a single question.

        Args:
            question: Question dictionary

        Returns:
            Tuple of (question_id, embedding_vector, searchable_text)
        """
        try:
            searchable_text = self.build_searchable_text(question)

            if not searchable_text.strip():
                # Silently skip - will be counted in stats
                return (question['id'], None, None)

            # Generate embedding (use OpenAI for 1536 dimensions to match DB schema)
            vector = self.embeddings.get_openai_embedding(searchable_text)

            return (question['id'], vector, searchable_text)

        except Exception as e:
            # Only log errors, not warnings
            tqdm.write(f"ERROR: Failed to generate embedding for {question.get('id')}: {e}")
            return (question['id'], None, None)

    def update_question_embedding(self, question_id: str, vector: List[float], searchable_text: str):
        """
        Update a single question with its embedding.

        Args:
            question_id: Question UUID
            vector: Embedding vector
            searchable_text: Text used for embedding
        """
        try:
            self.supabase.table("extracted_questions") \
                .update({
                    "dense_vector": vector,
                    "searchable_text": searchable_text
                }) \
                .eq("id", question_id) \
                .execute()

        except Exception as e:
            tqdm.write(f"ERROR: Failed to update question {question_id}: {e}")
            raise

    def process_batch(self, batch: List[Dict[str, Any]], pbar: tqdm = None) -> Dict[str, int]:
        """
        Process a batch of questions in parallel.

        Args:
            batch: List of question dictionaries
            pbar: Progress bar to update after each question

        Returns:
            Stats dictionary with counts
        """
        stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'skipped': 0
        }

        # Generate embeddings in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.generate_embedding_for_question, q): q
                for q in batch
            }

            for future in as_completed(futures):
                question_id, vector, searchable_text = future.result()
                stats['processed'] += 1

                if vector is None:
                    stats['skipped'] += 1
                else:
                    try:
                        # Update in database
                        self.update_question_embedding(question_id, vector, searchable_text)
                        stats['succeeded'] += 1
                    except Exception as e:
                        tqdm.write(f"ERROR: Failed to update {question_id}: {e}")
                        stats['failed'] += 1

                # Update progress bar after EACH question
                if pbar:
                    pbar.update(1)
                    pbar.set_postfix({
                        'succeeded': stats['succeeded'],
                        'failed': stats['failed'],
                        'skipped': stats['skipped']
                    })

        return stats

    def run(self, limit: int = None):
        """
        Main execution loop to process all questions.

        Args:
            limit: Optional limit on total questions to process
        """
        logger.info("="*80)
        logger.info("🚀 Starting question embedding generation")
        logger.info("="*80)

        # Get total count
        total_count = self.get_total_count()
        logger.info(f"📊 Total questions without embeddings: {total_count}")

        if limit:
            total_count = min(total_count, limit)
            logger.info(f"📊 Limited to: {limit} questions")

        if total_count == 0:
            logger.info("✅ All questions already have embeddings!")
            return

        # Process in batches
        offset = 0
        total_stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'skipped': 0
        }

        start_time = time.time()

        # Create progress bar
        with tqdm(total=total_count, desc="Generating embeddings", unit="questions") as pbar:
            while offset < total_count:
                batch_start = time.time()

                # Fetch batch
                tqdm.write(f"Fetching batch (offset={offset}, size={self.batch_size})...")
                batch = self.fetch_batch(offset)

                if not batch:
                    break

                tqdm.write(f"Processing {len(batch)} questions with {self.max_workers} workers...")
                # Process batch (updates progress bar after each question)
                batch_stats = self.process_batch(batch, pbar)

                # Update totals
                for key in total_stats:
                    total_stats[key] += batch_stats[key]

                offset += len(batch)

                # Rate limiting to avoid API throttling
                if batch_stats['succeeded'] > 0:
                    time.sleep(1)

        # Final summary
        total_time = time.time() - start_time
        logger.info("\n" + "="*80)
        logger.info("🏁 EMBEDDING GENERATION COMPLETE")
        logger.info("="*80)
        logger.info(f"✅ Total processed: {total_stats['processed']}")
        logger.info(f"✅ Succeeded: {total_stats['succeeded']}")
        logger.info(f"❌ Failed: {total_stats['failed']}")
        logger.info(f"⏭️  Skipped: {total_stats['skipped']}")
        logger.info(f"⏱️  Total time: {total_time/60:.1f} minutes")
        logger.info(f"⏱️  Average rate: {total_stats['processed']/total_time:.1f} questions/s")
        logger.info("="*80)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate embeddings for questions")
    parser.add_argument("--batch-size", type=int, default=20,
                       help="Batch size for processing (default: 20)")
    parser.add_argument("--workers", type=int, default=10,
                       help="Number of parallel workers (default: 10)")
    parser.add_argument("--limit", type=int, default=None,
                       help="Limit total questions to process (for testing)")

    args = parser.parse_args()

    try:
        generator = QuestionEmbeddingGenerator(
            batch_size=args.batch_size,
            max_workers=args.workers
        )
        generator.run(limit=args.limit)

        print("\n✅ Embedding generation completed successfully!")

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user. Progress has been saved.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
