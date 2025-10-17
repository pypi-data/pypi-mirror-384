#!/usr/bin/env python3
"""
Templatize questions using GPT-4o to create reusable question templates.

Usage:
    python scripts/templatize_questions.py --limit 100
    python scripts/templatize_questions.py --source textbook --grade 3
    python scripts/templatize_questions.py --min-quality 6.0

Requirements:
    pip install supabase python-dotenv pydantic tqdm

Environment variables (in .env):
    SUPABASE_URL=https://[YOUR-PROJECT-REF].supabase.co
    SUPABASE_SERVICE_KEY=[YOUR-SERVICE-ROLE-KEY]
    OPENAI_API_KEY=[YOUR-OPENAI-KEY]
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel, Field
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llms import produce_structured_response

# Load environment variables
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


class ParameterConstraint(BaseModel):
    """Constraint definition for a template parameter."""
    name: str = Field(description="Name of the parameter (e.g., 'num1', 'name', 'object')")
    type: str = Field(description="Type of parameter: 'integer', 'decimal', 'string', 'name', 'object', 'unit', 'pronoun', etc.")
    min_value: Optional[float] = Field(default=None, description="Minimum value for numeric parameters")
    max_value: Optional[float] = Field(default=None, description="Maximum value for numeric parameters")
    options: Optional[List[str]] = Field(default=None, description="Valid options for categorical parameters (e.g., ['he', 'she', 'they'] for pronouns)")
    description: Optional[str] = Field(default=None, description="Human-readable description of this parameter")


class QuestionTemplate(BaseModel):
    """Template for a question with parameter constraints."""
    question_id: str = Field(description="The question ID being templatized")
    template: str = Field(description="Handlebars-style template with {{variable}} placeholders. Replace ALL specific values: numbers, names, objects, units, pronouns, etc.")
    answer_template: Optional[str] = Field(default=None, description="Template for the answer (if applicable)")
    parameters: List[ParameterConstraint] = Field(description="Constraints for each parameter in the template")
    variability_score: float = Field(description="Score 0-1 indicating how variable/reusable this template is. More parameters = higher score. Simple templates with 1-2 params = 0.3-0.5, complex with 5+ params = 0.8-1.0")
    reasoning: str = Field(description="Brief explanation of the templatization (1-2 sentences)")


class TemplatizationResult(BaseModel):
    """Result of templatizing a single question."""
    templates: List[QuestionTemplate]


def templatize_question(question: dict) -> Optional[QuestionTemplate]:
    """
    Templatize a question using GPT-4o.

    Args:
        question: Question dict from database

    Returns:
        QuestionTemplate object or None if templatization fails
    """
    question_id = question["id"]
    question_text = question.get("question_en") or question.get("question_ar") or ""
    answer_text = question.get("answer_en") or question.get("answer_ar") or ""

    # Build context
    context_parts = []
    if question.get("grade"):
        context_parts.append(f"Grade: {question['grade']}")
    if question.get("domain"):
        context_parts.append(f"Domain: {question['domain']}")
    if question.get("substandard_description"):
        context_parts.append(f"Standard: {question['substandard_description']}")

    context = " | ".join(context_parts) if context_parts else "No context"

    system_instructions = """You are an expert at creating reusable question templates for educational content.

Your task is to convert a specific question into a template with variables that can generate infinite variations.

**What to templatize (replace with {{variable}}):**
1. **Numbers**: Any numeric values → {{num1}}, {{num2}}, etc.
2. **Names**: Person names → {{name}}, {{name1}}, {{name2}}
3. **Objects**: Countable/measurable things → {{object}}, {{object_plural}}
4. **Units**: Measurement units → {{unit}} (meters, kilograms, etc.)
5. **Pronouns**: he/she/they → {{pronoun}}
6. **Locations**: Places → {{location}}
7. **Times**: Time values → {{time}}
8. **Any other specific values** that can vary while keeping the mathematical structure

**Example:**
Original: "Sarah has 5 apples. She gives 2 to Tom. How many apples does Sarah have left?"
Template: "{{name1}} has {{num1}} {{object_plural}}. {{pronoun1}} gives {{num2}} to {{name2}}. How many {{object_plural}} does {{name1}} have left?"

**Parameter constraints:**
- Define realistic ranges for numbers (consider grade level)
- Provide options for categorical variables (names, objects, pronouns)
- Ensure constraints maintain mathematical validity

**Variability score:**
- 0.2-0.4: Simple templates (1-2 parameters, limited variability)
- 0.5-0.7: Moderate templates (3-5 parameters, good variability)
- 0.8-1.0: High templates (6+ parameters, excellent variability)

**Important:**
- Keep the mathematical structure/operation identical
- Preserve the difficulty level
- Ensure the template can generate valid questions"""

    user_content = f"""Templatize this question:

Context: {context}

Question:
{question_text}

Answer:
{answer_text}"""

    try:
        result = produce_structured_response(
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_content}
            ],
            structure_model=TemplatizationResult,
            model="gpt-4o",
            temperature=0.0,
            provider="openai"
        )

        if result.templates and len(result.templates) > 0:
            return result.templates[0]
        else:
            logger.warning(f"No template returned for question {question_id}")
            return None

    except Exception as e:
        logger.error(f"Failed to templatize question {question_id}: {e}")
        return None


def update_question_template(question_id: str, template: QuestionTemplate):
    """Update question in database with template."""
    # Create a new Supabase client for this update to avoid connection pooling issues
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # Fetch existing raw_data to preserve it
        existing = client.table("extracted_questions").select("raw_data").eq("id", question_id).execute()
        existing_raw_data = existing.data[0].get("raw_data", {}) if existing.data else {}

        # Convert parameters to dict for JSON storage
        parameters_dict = {
            param.name: {
                "type": param.type,
                "min_value": param.min_value,
                "max_value": param.max_value,
                "options": param.options,
                "description": param.description
            }
            for param in template.parameters
        }

        # Merge template info into raw_data
        updated_raw_data = {
            **existing_raw_data,
            "templatization": {
                "template": template.template,
                "answer_template": template.answer_template,
                "parameters": parameters_dict,
                "variability_score": template.variability_score,
                "reasoning": template.reasoning,
                "templatized_at": datetime.utcnow().isoformat()
            }
        }

        update_data = {
            "template": template.template,
            "parameter_constraints": parameters_dict,
            "variability_score": template.variability_score,
            "raw_data": updated_raw_data
        }

        client.table("extracted_questions").update(update_data).eq("id", question_id).execute()

    except Exception as e:
        logger.error(f"Failed to update question {question_id}: {e}")
        raise


def fetch_questions_to_templatize(
    limit: Optional[int] = None,
    source: str = "both",
    grade: Optional[int] = None,
    min_quality: float = 6.0
) -> List[dict]:
    """Fetch questions from Supabase that need templatization."""

    query = supabase.table("extracted_questions").select("*")

    # Filter by source
    if source == "athena":
        query = query.eq("source_type", "athena_api")
    elif source == "textbook":
        query = query.eq("source_type", "textbook_pdf")

    # Filter by grade
    if grade:
        query = query.eq("grade", grade)

    # Only good quality questions
    query = query.gte("quality_score", min_quality)

    # Only questions without templates
    query = query.is_("template", "null")

    # Order by quality score (best first)
    query = query.order("quality_score", desc=True)

    # Apply limit with pagination if needed
    all_questions = []
    if limit:
        page_size = 1000
        offset = 0

        while len(all_questions) < limit:
            batch_size = min(page_size, limit - len(all_questions))

            batch_query = query.range(offset, offset + batch_size - 1)
            response = batch_query.execute()
            batch = response.data

            if not batch:
                break

            all_questions.extend(batch)
            offset += len(batch)

            if len(batch) < batch_size:
                break
    else:
        # No limit - fetch all (up to reasonable amount)
        response = query.limit(10000).execute()
        all_questions = response.data

    logger.info(f"Fetched {len(all_questions)} questions to templatize (quality >= {min_quality})")
    return all_questions


def main():
    parser = argparse.ArgumentParser(description="Templatize questions to create reusable templates")
    parser.add_argument("--limit", type=int, help="Number of questions to templatize (default: all untemplatized)")
    parser.add_argument("--source", type=str, default="both", choices=["athena", "textbook", "both"],
                        help="Which source to process")
    parser.add_argument("--grade", type=int, help="Filter by grade")
    parser.add_argument("--min-quality", type=float, default=6.0, help="Minimum quality score (default: 6.0)")
    parser.add_argument("--workers", type=int, default=10, help="Number of concurrent workers (default: 10)")

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("QUESTION TEMPLATIZATION STARTED")
    logger.info("="*60)

    if args.limit:
        logger.info(f"Templatizing up to {args.limit} questions")
    else:
        logger.info("Templatizing all untemplatized questions")

    logger.info(f"Minimum quality score: {args.min_quality}")

    # Fetch questions
    questions = fetch_questions_to_templatize(
        limit=args.limit,
        source=args.source,
        grade=args.grade,
        min_quality=args.min_quality
    )

    if not questions:
        logger.info("No questions to templatize")
        return

    stats = {
        "total": len(questions),
        "templatized": 0,
        "failed": 0,
        "high_variability": 0,  # 0.8-1.0
        "medium_variability": 0,  # 0.5-0.7
        "low_variability": 0  # 0-0.4
    }

    def process_question(question):
        """Process a single question."""
        template = templatize_question(question)

        if template:
            update_question_template(question["id"], template)

            # Categorize by variability
            if template.variability_score >= 0.8:
                category = "high_variability"
            elif template.variability_score >= 0.5:
                category = "medium_variability"
            else:
                category = "low_variability"

            return ("success", category, template.variability_score)
        else:
            return ("failed", None, None)

    # Process questions in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_question, q): q for q in questions}

        with tqdm(total=len(futures), desc="Templatizing", unit=" questions", ncols=100) as pbar:
            for future in as_completed(futures):
                status, category, variability = future.result()

                if status == "success":
                    stats["templatized"] += 1
                    if category:
                        stats[category] += 1
                else:
                    stats["failed"] += 1

                pbar.update(1)
                pbar.set_postfix_str(f"✓ {stats['templatized']} | ✗ {stats['failed']}")

    # Final Summary
    logger.info("\n" + "="*60)
    logger.info("TEMPLATIZATION COMPLETE")
    logger.info("="*60)
    logger.info(f"Total processed: {stats['total']}")
    logger.info(f"Successfully templatized: {stats['templatized']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info("")
    logger.info("Variability Distribution:")
    logger.info(f"  High Variability (0.8-1.0): {stats['high_variability']} ({stats['high_variability']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    logger.info(f"  Medium Variability (0.5-0.7): {stats['medium_variability']} ({stats['medium_variability']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    logger.info(f"  Low Variability (0.0-0.4): {stats['low_variability']} ({stats['low_variability']*100//stats['total'] if stats['total'] > 0 else 0}%)")
    logger.info("="*60)


if __name__ == "__main__":
    main()
