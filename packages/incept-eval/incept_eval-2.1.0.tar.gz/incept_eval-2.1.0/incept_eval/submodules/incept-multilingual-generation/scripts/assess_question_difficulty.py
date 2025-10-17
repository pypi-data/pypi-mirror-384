#!/usr/bin/env python3
"""
Assess difficulty level of questions in extracted_questions table using LLM.

Usage:
    python scripts/assess_question_difficulty.py --grade 3 --batch-size 50
    python scripts/assess_question_difficulty.py --all --provider openai
    python scripts/assess_question_difficulty.py --grade 4 --subject mathematics --resume

Requirements:
    pip install supabase python-dotenv

Environment variables (in .env):
    SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
    SUPABASE_SERVICE_KEY=[YOUR-SERVICE-ROLE-KEY]
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from supabase import create_client, Client
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llms import produce_structured_response, format_messages_for_api, solve_with_llm
from src.utils.progress_bar import ProgressBar

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def assess_question_difficulty(
    question_text: str,
    grade: int,
    subject: str,
    answer: Optional[str] = None,
    explanation: Optional[str] = None,
    provider: str = "openai"
) -> Dict[str, Any]:
    """
    Use LLM to assess the difficulty level of a question.

    Returns:
        Dict with:
        - difficulty: str ('easy', 'medium', 'hard')
        - confidence: float (0.0-1.0)
        - reasoning: str (brief explanation)
    """
    system_content = f"""You are an expert educational content assessor specializing in {subject} for grade {grade}.

Your task is to assess the difficulty level of questions relative to the grade level and subject.

DIFFICULTY LEVELS:
- **easy**: Basic recall, simple one-step problems, foundational concepts
  * Grade {grade} students should solve this quickly with minimal effort
  * Requires only basic understanding of core concepts
  * Examples: Simple arithmetic, basic definitions, straightforward recall

- **medium**: Multi-step problems, application of concepts, moderate reasoning
  * Grade {grade} students need to think and apply learned concepts
  * May involve 2-3 steps or combining multiple concepts
  * Examples: Word problems with clear structure, standard procedures, basic analysis

- **hard**: Complex multi-step problems, advanced reasoning, synthesis of concepts
  * Challenging for grade {grade} students, requires deep understanding
  * Involves multiple concepts, non-obvious approaches, or creative thinking
  * Examples: Complex word problems, multi-step reasoning, pattern recognition, problem-solving

ASSESSMENT CRITERIA:
1. Cognitive demand relative to grade level
2. Number of steps/concepts required
3. Clarity and complexity of problem presentation
4. Mathematical reasoning required
5. Whether it's typical, below, or above grade-level expectations

Return JSON with:
- difficulty: "easy", "medium", or "hard"
- confidence: 0.0-1.0 (how confident you are in this assessment)
- reasoning: Brief 1-2 sentence explanation of why you chose this difficulty"""

    user_content = f"""Assess the difficulty of this question for grade {grade} {subject}:

QUESTION:
{question_text}"""

    if answer:
        user_content += f"\n\nANSWER: {answer}"

    if explanation:
        user_content += f"\n\nEXPLANATION: {explanation[:200]}"

    messages = format_messages_for_api(system_content, user_content)

    try:
        result = solve_with_llm(
            messages=messages,
            max_tokens=200,
            provider=provider,
            do_not_parse_json=False
        )

        if not result or not isinstance(result, dict):
            return {
                "difficulty": "medium",
                "confidence": 0.0,
                "reasoning": "Failed to parse LLM response"
            }

        # Normalize difficulty value
        difficulty = result.get("difficulty", "medium").lower()
        if difficulty not in ["easy", "medium", "hard"]:
            difficulty = "medium"

        confidence = float(result.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        return {
            "difficulty": difficulty,
            "confidence": confidence,
            "reasoning": result.get("reasoning", "")
        }

    except Exception as e:
        logger.error(f"LLM assessment failed: {e}")
        return {
            "difficulty": "medium",
            "confidence": 0.0,
            "reasoning": f"Error: {str(e)}"
        }


def fetch_questions_batch(
    grade: Optional[int] = None,
    subject: Optional[str] = None,
    source_types: Optional[List[str]] = None,
    batch_size: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """Fetch a batch of questions from the database."""
    try:
        query = supabase.table("extracted_questions").select(
            "id, question_en, question_ar, grade, subject, difficulty, "
            "answer_en, answer_ar, explanation_en, explanation_ar, source_type, language"
        )

        # Apply filters
        if grade is not None:
            query = query.eq("grade", grade)

        if subject:
            query = query.ilike("subject", f"%{subject}%")

        if source_types:
            if len(source_types) == 1:
                query = query.eq("source_type", source_types[0])
            else:
                query = query.in_("source_type", source_types)

        # Order by id for consistent pagination
        query = query.order("id")
        query = query.range(offset, offset + batch_size - 1)

        response = query.execute()
        return response.data if response.data else []

    except Exception as e:
        logger.error(f"Failed to fetch batch: {e}")
        return []


def update_question_difficulty(
    question_id: str,
    difficulty: str,
    confidence: float,
    reasoning: str
) -> bool:
    """Update question difficulty in the database."""
    try:
        response = supabase.table("extracted_questions").update({
            "difficulty": difficulty,
            "metadata": {
                "difficulty_confidence": confidence,
                "difficulty_reasoning": reasoning,
                "difficulty_assessed_at": time.time()
            }
        }).eq("id", question_id).execute()

        return bool(response.data)

    except Exception as e:
        logger.error(f"Failed to update question {question_id}: {e}")
        return False


def process_single_question(
    question: Dict[str, Any],
    provider: str
) -> Optional[Dict[str, Any]]:
    """Process a single question and return assessment."""
    question_id = question.get("id")

    # Determine which language to use
    language = question.get("language", "en")
    question_text = question.get("question_en") if language == "en" else question.get("question_ar")
    answer = question.get("answer_en") if language == "en" else question.get("answer_ar")
    explanation = question.get("explanation_en") if language == "en" else question.get("explanation_ar")

    if not question_text:
        # Fallback to the other language
        question_text = question.get("question_ar") or question.get("question_en")

    if not question_text:
        logger.warning(f"Question {question_id} has no text, skipping")
        return None

    grade = question.get("grade", 5)
    subject = question.get("subject", "mathematics")

    # Assess difficulty
    assessment = assess_question_difficulty(
        question_text=question_text,
        grade=grade,
        subject=subject,
        answer=answer,
        explanation=explanation,
        provider=provider
    )

    return {
        "question_id": question_id,
        "difficulty": assessment["difficulty"],
        "confidence": assessment["confidence"],
        "reasoning": assessment["reasoning"],
        "previous_difficulty": question.get("difficulty")
    }


def main():
    parser = argparse.ArgumentParser(
        description="Assess difficulty level of questions using LLM"
    )
    parser.add_argument(
        "--grade",
        type=int,
        help="Filter by single grade (e.g., 3, 4, 5)"
    )
    parser.add_argument(
        "--grades",
        nargs="+",
        type=int,
        help="Process multiple grades (e.g., --grades 3 4 5 6 7 8)"
    )
    parser.add_argument(
        "--subject",
        type=str,
        default="mathematics",
        help="Filter by subject (default: mathematics)"
    )
    parser.add_argument(
        "--source-type",
        nargs="+",
        type=str,
        choices=["athena_api", "textbook_pdf"],
        help="Filter by source type(s) (e.g., --source-type athena_api textbook_pdf)"
    )
    parser.add_argument(
        "--textbooks-only",
        action="store_true",
        help="Process only textbook questions (shorthand for --source-type textbook_pdf)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all questions (ignores grade/subject filters)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for fetching questions (default: 100)"
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=5,
        help="Number of parallel workers (default: 5)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="openai",
        choices=["openai", "dspy", "falcon"],
        help="LLM provider to use (default: openai)"
    )
    parser.add_argument(
        "--no-resume",
        dest="resume",
        action="store_false",
        default=True,
        help="Process all questions, including those already assessed (default: skip already assessed)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't update database, just print assessments"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit total number of questions to process (for testing)"
    )

    args = parser.parse_args()

    # Determine which grades to process
    if args.grades:
        grades_to_process = args.grades
    elif args.grade:
        grades_to_process = [args.grade]
    elif args.all:
        grades_to_process = [None]  # Process all grades
    else:
        parser.error("Must specify --grade, --grades, or --all")

    subject = None if args.all else args.subject

    # Handle textbooks-only flag
    if args.textbooks_only:
        source_types = ["textbook_pdf"]
    elif args.source_type:
        source_types = args.source_type
    else:
        source_types = None

    logger.info("🚀 Starting difficulty assessment")
    logger.info(f"   Grades: {grades_to_process if grades_to_process != [None] else 'ALL'}")
    logger.info(f"   Subject: {subject or 'ALL'}")
    logger.info(f"   Source Types: {source_types or 'ALL'}")
    logger.info(f"   Provider: {args.provider}")
    logger.info(f"   Batch Size: {args.batch_size}")
    logger.info(f"   Max Workers: {args.max_workers}")
    logger.info(f"   Mode: {'Resume (skip already assessed)' if args.resume else 'Full (reprocess all)'}")
    logger.info(f"   Dry Run: {args.dry_run}")

    # Overall statistics across all grades
    overall_processed = 0
    overall_updated = 0
    overall_skipped = 0
    overall_distribution = {"easy": 0, "medium": 0, "hard": 0}
    grade_summaries = []

    # Process each grade
    for grade_idx, grade in enumerate(grades_to_process, 1):
        if len(grades_to_process) > 1:
            logger.info(f"\n{'='*60}")
            logger.info(f"📚 Processing Grade {grade} ({grade_idx}/{len(grades_to_process)})")
            logger.info(f"{'='*60}")

        total_processed = 0
        total_updated = 0
        total_skipped = 0
        difficulty_distribution = {"easy": 0, "medium": 0, "hard": 0}
        offset = 0

        # Initialize progress bar (unknown total initially)
        progress = ProgressBar(
            total=args.limit if args.limit else None,
            description=f"Grade {grade}" if grade else "All grades"
        )

        try:
            while True:
                # Fetch batch
                logger.info(f"\n📦 Fetching batch (offset={offset}, size={args.batch_size})...")
                questions = fetch_questions_batch(
                    grade=grade,
                    subject=subject,
                    source_types=source_types,
                    batch_size=args.batch_size,
                    offset=offset
                )

                if not questions:
                    logger.info("   No more questions to process")
                    break

                logger.info(f"   Fetched {len(questions)} questions")

                # Filter out questions with existing difficulty if resume mode
                if args.resume:
                    questions_to_process = [
                        q for q in questions
                        if not q.get("difficulty") or q.get("difficulty") == "medium"
                    ]
                    skipped = len(questions) - len(questions_to_process)
                    total_skipped += skipped
                    if skipped > 0:
                        logger.info(f"   Skipped {skipped} questions (already assessed)")
                else:
                    questions_to_process = questions

                if not questions_to_process:
                    offset += len(questions)
                    continue

                # Process batch in parallel
                logger.info(f"   Processing {len(questions_to_process)} questions...")
                assessments = []

                with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
                    futures = {
                        executor.submit(process_single_question, q, args.provider): q
                        for q in questions_to_process
                    }

                    for future in as_completed(futures):
                        question = futures[future]
                        try:
                            result = future.result()
                            if result:
                                assessments.append(result)
                                total_processed += 1

                                # Update difficulty distribution
                                difficulty_distribution[result["difficulty"]] += 1

                                # Update database
                                if not args.dry_run:
                                    if update_question_difficulty(
                                        result["question_id"],
                                        result["difficulty"],
                                        result["confidence"],
                                        result["reasoning"]
                                    ):
                                        total_updated += 1

                                # Update progress bar
                                prev = result["previous_difficulty"] or "None"
                                progress.update(
                                    1,
                                    details=f"{result['difficulty']} (was: {prev}) - E:{difficulty_distribution['easy']} M:{difficulty_distribution['medium']} H:{difficulty_distribution['hard']}"
                                )

                        except Exception as e:
                            logger.error(f"      Error processing question: {e}")

                # Check limit
                if args.limit and total_processed >= args.limit:
                    logger.info(f"\n✋ Reached limit of {args.limit} questions")
                    break

                offset += len(questions)

        except KeyboardInterrupt:
            logger.info("\n\n⚠️  Interrupted by user")
            progress.complete(f"Interrupted - assessed {total_processed} questions")
            break  # Break out of grade loop
        else:
            # Complete progress bar (only if not interrupted)
            progress.complete(f"Assessed {total_processed} questions")

        # Per-grade summary
        if len(grades_to_process) > 1:
            logger.info(f"\n📊 Grade {grade} Summary:")
            logger.info(f"   Processed: {total_processed}, Updated: {total_updated}, Skipped: {total_skipped}")
            logger.info(f"   Distribution: E:{difficulty_distribution['easy']}, "
                       f"M:{difficulty_distribution['medium']}, H:{difficulty_distribution['hard']}")

        # Update overall statistics
        overall_processed += total_processed
        overall_updated += total_updated
        overall_skipped += total_skipped
        overall_distribution['easy'] += difficulty_distribution['easy']
        overall_distribution['medium'] += difficulty_distribution['medium']
        overall_distribution['hard'] += difficulty_distribution['hard']

        grade_summaries.append({
            'grade': grade,
            'processed': total_processed,
            'updated': total_updated,
            'skipped': total_skipped,
            'distribution': difficulty_distribution.copy()
        })

    # Final overall summary
    logger.info("\n" + "="*60)
    logger.info("✨ Assessment complete!")
    logger.info(f"   Total Processed: {overall_processed}")
    logger.info(f"   Total Updated: {overall_updated}")
    logger.info(f"   Total Skipped: {overall_skipped}")
    logger.info(f"\n   📊 Overall Difficulty Distribution:")
    logger.info(f"      Easy: {overall_distribution['easy']} "
               f"({100*overall_distribution['easy']/max(1,overall_processed):.1f}%)")
    logger.info(f"      Medium: {overall_distribution['medium']} "
               f"({100*overall_distribution['medium']/max(1,overall_processed):.1f}%)")
    logger.info(f"      Hard: {overall_distribution['hard']} "
               f"({100*overall_distribution['hard']/max(1,overall_processed):.1f}%)")

    # Show per-grade breakdown if multiple grades processed
    if len(grade_summaries) > 1:
        logger.info(f"\n   📚 Per-Grade Breakdown:")
        for summary in grade_summaries:
            logger.info(f"      Grade {summary['grade']}: "
                       f"Processed={summary['processed']}, "
                       f"E={summary['distribution']['easy']}, "
                       f"M={summary['distribution']['medium']}, "
                       f"H={summary['distribution']['hard']}")

    logger.info("="*60)


if __name__ == "__main__":
    main()
