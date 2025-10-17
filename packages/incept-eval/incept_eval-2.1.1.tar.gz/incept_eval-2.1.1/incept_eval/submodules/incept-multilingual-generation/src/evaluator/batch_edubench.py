#!/usr/bin/env python3
"""
Batch EduBench Evaluator
Processes questions from database in batches of 20, evaluates with EduBench, and uploads results
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

# Add EduBench code path
edu_bench_path = Path(__file__).parent / "EduBench" / "code" / "evaluation"
sys.path.insert(0, str(edu_bench_path))

import requests

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


def query_hf_model(payload, max_retries=3, timeout=700):
    """Query the HuggingFace model endpoint with retry logic"""
    HUGGINGFACE_TOKEN = (
        os.getenv('HUGGINGFACE_TOKEN') or
        os.getenv('HUGGINGFACE_TOKEN') or
        os.getenv('HF_API_TOKEN')
    )

    if not HUGGINGFACE_TOKEN:
        raise ValueError("HuggingFace API token not found in environment variables")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {HUGGINGFACE_TOKEN}",
        "Content-Type": "application/json"
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://ifkx7sxcl1f3j6k6.us-east-1.aws.endpoints.huggingface.cloud",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}, retrying...")
                continue
            else:
                logger.error(f"Failed after {max_retries} attempts due to timeout")
                raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                logger.warning(f"Request error on attempt {attempt + 1}/{max_retries}: {e}, retrying...")
                continue
            else:
                logger.error(f"Failed after {max_retries} attempts")
                raise


def get_normal_answer(prompt, model_name="EDU-Qwen2.5-7B"):
    """Call HF model and return a result"""
    try:
        output = query_hf_model({
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.7,
                "do_sample": True
            }
        })

        # Handle different response formats
        response_text = ""
        if isinstance(output, list) and len(output) > 0:
            if 'generated_text' in output[0]:
                response_text = output[0]['generated_text']
            elif 'text' in output[0]:
                response_text = output[0]['text']
            else:
                response_text = str(output[0])
        elif isinstance(output, dict):
            if 'generated_text' in output:
                response_text = output['generated_text']
            elif 'text' in output:
                response_text = output['text']
            else:
                response_text = str(output)
        else:
            response_text = str(output)

        # Remove prompt echo if present
        if response_text.startswith(prompt):
            response_text = response_text[len(prompt):].strip()

        return response_text

    except Exception as e:
        logger.error(f"Error calling {model_name}: {e}")
        return f"Error from {model_name}: {str(e)}"


def evaluate_with_edubench(question_data: Dict[str, Any], question_id: int, task_types=["QA", "EC", "IP"]) -> Dict[str, Any]:
    """
    Evaluate a single question using EduBench tasks

    Args:
        question_data: Dictionary containing question information
        question_id: ID of the question being evaluated
        task_types: List of EduBench task types to evaluate (QA, EC, IP)

    Returns:
        Dictionary with evaluation results
    """
    from src.evaluator.EduBench.code.evaluation.evaluation import TASK_PROMPT_TEMPLATES

    results = {}

    for task_type in task_types:
        try:
            logger.info(f"  Question {question_id}: Starting {task_type} evaluation...")

            # Build prompt based on task type
            if task_type == "QA":
                prompt_content = TASK_PROMPT_TEMPLATES["QA"](question_data.get("question", ""))
            elif task_type == "EC":
                prompt_content = TASK_PROMPT_TEMPLATES["EC"](
                    question_data.get("question", ""),
                    question_data.get("answer", "")
                )
            elif task_type == "IP":
                prompt_content = TASK_PROMPT_TEMPLATES["IP"](question_data.get("question", ""))
            else:
                continue

            # Get model response
            logger.info(f"  Question {question_id}: Calling model for {task_type}...")
            response = get_normal_answer(prompt_content, "EDU-Qwen2.5-7B")
            logger.info(f"  Question {question_id}: ✓ {task_type} complete (response length: {len(response)})")

            results[task_type] = {
                "prompt": prompt_content,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"  Question {question_id}: Error evaluating {task_type}: {e}")
            results[task_type] = {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    return results


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
                subject_area,
                broad_topic,
                subtopic,
                scaffolding,
                language,
                evaluation_edubench
            FROM uae_educational_questions_cleaned_duplicate
            WHERE scaffolding IS NOT NULL
            AND evaluation_edubench IS NULL
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(query, (batch_size, offset))
        return cur.fetchall()


def update_evaluation_result(conn, question_id: int, evaluation_result: Dict[str, Any]):
    """
    Update the evaluation_edubench column for a question

    Args:
        conn: Database connection
        question_id: ID of the question to update
        evaluation_result: Evaluation result dictionary
    """
    with conn.cursor() as cur:
        query = """
            UPDATE uae_educational_questions_cleaned_duplicate
            SET evaluation_edubench = %s
            WHERE id = %s
        """
        cur.execute(query, (json.dumps(evaluation_result), question_id))
    conn.commit()


def process_single_question(question: Dict[str, Any], conn) -> bool:
    """
    Process a single question - evaluate and save to database

    Args:
        question: Question dictionary
        conn: Database connection

    Returns:
        True if successful, False otherwise
    """
    try:
        # Check if already evaluated (shouldn't happen with new query, but double-check)
        if question.get('evaluation_edubench'):
            logger.info(f"Question {question['id']} already evaluated, skipping...")
            return False

        # Prepare question data
        question_data = {
            "question": question['question_text_arabic'] if question['language'] == 'ar' else question['question_text'],
            "answer": question['correct_answer'] or "",
            "explanation": question['answer_explanation'] or "",
            "difficulty": question['difficulty_level'] or "medium",
            "grade": question['grade_level'],
            "subject": question['subject_area'],
        }

        logger.info(f"Evaluating question {question['id']}...")

        # Evaluate with EduBench
        evaluation_result = evaluate_with_edubench(question_data, question['id'])

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


def process_batch(batch_questions: List[Dict[str, Any]], conn, max_workers=5) -> int:
    """
    Process a batch of questions in parallel

    Args:
        batch_questions: List of question dictionaries
        conn: Database connection
        max_workers: Maximum number of parallel workers

    Returns:
        Number of questions processed
    """
    processed_count = 0

    # Process questions in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all questions for processing
        futures = {
            executor.submit(process_single_question, question, conn): question
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
    logger.info("🚀 Starting Batch EduBench Evaluator (Parallel Mode)")

    batch_size = 60
    max_workers = batch_size  # Number of parallel workers per batch
    total_processed = 0

    try:
        conn = get_db_connection()
        logger.info("✓ Connected to database")

        # Since we're filtering for NULL evaluation_edubench, we don't need offset-based pagination
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
            processed = process_batch(batch_questions, conn, max_workers=max_workers)
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
        raise
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("✓ Database connection closed")


if __name__ == "__main__":
    main()
