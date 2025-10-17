#!/usr/bin/env python3
"""
Batch Scaffolding Evaluator
Processes questions from database in batches of 20, evaluates with v2.py, and uploads results to evaluation_scaffolding
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.evaluator.v2 import call_single_shot_evaluator, EvaluationDimension
from src.dto.question_generation import GenerateQuestionsRequest, GeneratedQuestion, SkillInfo

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Get PostgreSQL database connection"""
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        raise RuntimeError("POSTGRES_URI environment variable not set")
    return psycopg2.connect(postgres_uri)


def evaluate_with_v2(question_data: Dict[str, Any], request: GenerateQuestionsRequest, question_id: int) -> Dict[str, Any]:
    """
    Evaluate a single question using v2.py evaluator

    Args:
        question_data: Dictionary containing question information
        request: GenerateQuestionsRequest object
        question_id: ID of the question being evaluated

    Returns:
        Dictionary with evaluation results
    """
    try:
        logger.info(f"  Question {question_id}: Starting v2 scaffolding evaluation...")

        # Create GeneratedQuestion object from question_data
        generated_question = GeneratedQuestion(
            type=question_data.get("type", "mcq"),
            question=question_data.get("question", ""),
            answer=question_data.get("answer", ""),
            difficulty=question_data.get("difficulty", "medium"),
            explanation=question_data.get("explanation", ""),
            options=question_data.get("options"),
            skill=SkillInfo(
                id=f"skill_{question_id}",
                title=question_data.get("subtopic", "General"),
                unit=question_data.get("broad_topic", "General"),
                grade=question_data.get("grade", 8)
            ) if question_data.get("subtopic") or question_data.get("broad_topic") else None
        )

        logger.info(f"  Question {question_id}: Calling v2 evaluator...")

        # Call v2 evaluator
        result = call_single_shot_evaluator(
            q=generated_question,
            request=request,
            total_questions=1
        )

        logger.info(f"  Question {question_id}: ✓ Evaluation complete")

        # Format result for storage
        evaluation_result = {
            "scores": {
                "correctness": result["scores"].get(EvaluationDimension.CORRECTNESS, 0.0),
                "grade_alignment": result["scores"].get(EvaluationDimension.GRADE_ALIGNMENT, 0.0),
                "difficulty_alignment": result["scores"].get(EvaluationDimension.DIFFICULTY_ALIGNMENT, 0.0),
                "language_quality": result["scores"].get(EvaluationDimension.LANGUAGE_QUALITY, 0.0),
                "pedagogical_value": result["scores"].get(EvaluationDimension.PEDAGOGICAL_VALUE, 0.0),
                "explanation_quality": result["scores"].get(EvaluationDimension.EXPLANATION_QUALITY, 0.0),
                "instruction_adherence": result["scores"].get(EvaluationDimension.INSTRUCTION_ADHERENCE, 0.0),
                "format_compliance": result["scores"].get(EvaluationDimension.FORMAT_COMPLIANCE, 0.0),
                "di_compliance": result["scores"].get(EvaluationDimension.DI_COMPLIANCE, 0.0),
            },
            "overall": result.get("overall", 0.0),
            "recommendation": result.get("recommendation", "revise"),
            "issues": result.get("issues", []),
            "strengths": result.get("strengths", []),
            "suggested_improvements": result.get("suggested_improvements", []),
            "di_scores": result.get("di_scores", {}),
            "timestamp": datetime.now().isoformat()
        }

        return evaluation_result

    except Exception as e:
        logger.error(f"  Question {question_id}: Error in v2 evaluation: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def fetch_batch_questions(conn, batch_size=20, offset=0):
    """
    Fetch a batch of questions from database that haven't been evaluated yet

    Args:
        conn: Database connection
        batch_size: Number of questions to fetch
        offset: Offset for pagination

    Returns:
        List of question rows
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query = """
            SELECT
                id,
                question_text,
                question_text_arabic,
                correct_answer,
                answer_explanation,
                difficulty_level,
                grade_level,
                normalized_grade,
                subject_area,
                broad_topic,
                subtopic,
                scaffolding,
                language,
                evaluation_scaffolding,
                options
            FROM uae_educational_questions_cleaned_duplicate
            WHERE scaffolding IS NOT NULL
            AND options IS NOT NULL
            AND normalized_grade > 5
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (batch_size, offset))
        return cur.fetchall()


def update_evaluation_result(conn, question_id: int, evaluation_result: Dict[str, Any]):
    """
    Update the evaluation_scaffolding column for a question

    Args:
        conn: Database connection
        question_id: ID of the question to update
        evaluation_result: Evaluation result dictionary
    """
    with conn.cursor() as cur:
        query = """
            UPDATE uae_educational_questions_cleaned_duplicate
            SET evaluation_scaffolding = %s
            WHERE id = %s
        """
        cur.execute(query, (json.dumps(evaluation_result), question_id))
    conn.commit()


def process_single_question(question: Dict[str, Any], conn, request: GenerateQuestionsRequest) -> bool:
    """
    Process a single question - evaluate and save to database

    Args:
        question: Question dictionary
        conn: Database connection
        request: GenerateQuestionsRequest object

    Returns:
        True if successful, False otherwise
    """
    try:
        # # Check if already evaluated (shouldn't happen with new query, but double-check)
        # if question.get('evaluation_scaffolding'):
        #     logger.info(f"Question {question['id']} already evaluated, skipping...")
        #     return False

        # Prepare question data
        question_data = {
            "type": "mcq",
            "question": question['question_text_arabic'] if question['language'] == 'ar' else question['question_text'],
            "answer": question['correct_answer'] or "",
            "explanation": json.dumps(question['scaffolding']) if question['scaffolding'] else question['answer_explanation'] or "",
            "difficulty": question['difficulty_level'] or "medium",
            "grade": question.get('normalized_grade') or question.get('grade_level', 8),
            "subject": question['subject_area'],
            "broad_topic": question['broad_topic'],
            "subtopic": question['subtopic'],
            "options": question.get('options')  # Now we have options from the query
        }

        logger.info(f"Evaluating question {question['id']}...")

        # Evaluate with v2
        evaluation_result = evaluate_with_v2(question_data, request, question['id'])

        # Add metadata
        evaluation_result['evaluated_at'] = datetime.now().isoformat()
        evaluation_result['question_id'] = question['id']

        logger.info(f"  Question {question['id']}: Saving to database...")
        # Upload to database
        update_evaluation_result(conn, question['id'], evaluation_result)

        logger.info(f"✓ Question {question['id']} fully evaluated and saved")
        return True

    except Exception as e:
        logger.error(f"Error processing question {question['id']}: {e}")
        return False


def process_batch(batch_questions: List[Dict[str, Any]], conn, request: GenerateQuestionsRequest, max_workers=20) -> int:
    """
    Process a batch of questions in parallel

    Args:
        batch_questions: List of question dictionaries
        conn: Database connection
        request: GenerateQuestionsRequest object
        max_workers: Maximum number of parallel workers

    Returns:
        Number of questions processed
    """
    processed_count = 0

    # Process questions in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all questions for processing
        futures = {
            executor.submit(process_single_question, question, conn, request): question
            for question in batch_questions
        }

        # Collect results as they complete
        for future in as_completed(futures):
            question = futures[future]
            try:
                success = future.result()
                if success:
                    processed_count += 1
            except Exception as e:
                logger.error(f"Exception processing question {question['id']}: {e}")

    return processed_count


def main():
    """Main execution loop"""
    logger.info("🚀 Starting Batch Scaffolding Evaluator (Parallel Mode)")

    batch_size = 20
    max_workers = 20  # Number of parallel workers per batch
    total_processed = 0

    try:
        conn = get_db_connection()
        logger.info("✓ Connected to database")

        # Create a generic request object for evaluation context
        # This will be used for all questions
        request = GenerateQuestionsRequest(
            grade=8,  # Will be overridden per question
            instructions="Evaluate question quality and scaffolding",
            count=1,
            question_type="mcq",
            language="arabic",
            difficulty="mixed",
            subject="General"
        )

        # Since we're filtering for NULL evaluation_scaffolding, we don't need offset-based pagination
        # Just keep fetching until no more results
        batch_num = 0
        while True:
            batch_num += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing batch #{batch_num}")
            logger.info(f"{'='*60}")

            # Fetch batch (always from offset 0 since we're filtering NULL)
            batch_questions = fetch_batch_questions(conn, batch_size, offset=0)

            if not batch_questions:
                logger.info("No more questions to process")
                break

            logger.info(f"Fetched {len(batch_questions)} unevaluated questions")

            # Process batch in parallel
            processed = process_batch(batch_questions, conn, request, max_workers=max_workers)
            total_processed += processed

            logger.info(f"Processed {processed}/{len(batch_questions)} questions in this batch")
            logger.info(f"Total processed so far: {total_processed}")

            # Small delay between batches
            time.sleep(1)

        logger.info(f"\n{'='*60}")
        logger.info(f"✓ Evaluation complete!")
        logger.info(f"Total questions processed: {total_processed}")
        logger.info(f"{'='*60}")

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("✓ Database connection closed")


if __name__ == "__main__":
    main()
