#!/usr/bin/env python3
"""
Populate direct_instructions_raw for textbook questions using DI formats from MongoDB.

This script:
1. Fetches textbook questions from Supabase that don't have direct_instructions_raw
2. Uses DiFormatModel to find relevant DI formats from MongoDB
3. Uses GPT-4o with structured output to generate direct instruction content
4. Updates the questions in Supabase

Usage:
    python scripts/populate_textbook_di.py --limit 100
    python scripts/populate_textbook_di.py --grade 3
    python scripts/populate_textbook_di.py --min-quality 6.0

Requirements:
    pip install supabase python-dotenv pydantic tqdm pymongo
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

from src.direct_instruction.di_formats import DiFormat
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


class VocabularyItem(BaseModel):
    """Vocabulary term with definition."""
    term: str = Field(description="The mathematical or educational term")
    definition: str = Field(description="Clear, grade-appropriate definition")


class DirectInstructionContent(BaseModel):
    """Structured Direct Instruction content generated from DI formats."""
    prerequisite_skills: List[str] = Field(description="List of prerequisite skills needed (2-4 items)")
    microskills: List[str] = Field(description="Breakdown of micro-skills for this problem (2-5 items)")
    vocabulary: List[VocabularyItem] = Field(description="Key vocabulary terms with definitions (2-4 items)")
    question_stems: List[str] = Field(description="Alternative question formulations or prompts (2-4 items)")
    step_by_step_explanations: List[str] = Field(description="Step-by-step teaching sequence (3-6 steps)")
    has_relevant_content: bool = Field(description="True if relevant DI content was found, False otherwise")


def generate_di_content_from_knowledge_base(question: dict) -> Optional[DirectInstructionContent]:
    """
    Generate Direct Instruction content using GPT-4o's knowledge base when no DI formats are found.

    Args:
        question: Question dict from database

    Returns:
        DirectInstructionContent object or None if generation fails
    """
    question_id = question["id"]
    question_text = question.get("question_en") or question.get("question_ar") or ""
    answer_text = question.get("answer_en") or question.get("answer_ar") or ""
    grade = question.get("grade", 3)
    domain = question.get("domain", "")
    subject = question.get("substandard_description") or domain or "Mathematics"

    system_instructions = f"""You are an expert educator specializing in Direct Instruction pedagogy.

Generate comprehensive Direct Instruction teaching content for this Grade {grade} question.

**IMPORTANT - Grade-Appropriate Content:**
- For Grades 1-2: Use very simple language, concrete examples, basic vocabulary
- For Grades 3-4: Use clear language, relatable examples, age-appropriate terms
- For Grades 5-6: Can introduce more abstract concepts, but keep explanations clear
- For Grades 7-8: Can use more sophisticated vocabulary and complex reasoning

**Question (Grade {grade}):**
{question_text}

**Subject/Domain:** {subject}
{f"**Answer:** {answer_text}" if answer_text else ""}

**Your task:**
Generate Direct Instruction content that includes:

1. **Prerequisite Skills** (2-4 skills):
   - What foundational skills must students already have to approach this problem?
   - Consider what they learned in previous grades
   - Be specific and concrete

2. **Microskills** (2-5 skills):
   - Break down THIS specific problem into small, teachable steps
   - Each microskill should be a discrete, measurable action
   - Order them logically from first to last

3. **Vocabulary** (2-4 terms with definitions):
   - Identify key mathematical/educational terms in this question
   - Provide clear, grade-appropriate definitions
   - Focus on terms essential to understanding this problem

4. **Question Stems** (2-4 alternative formulations):
   - Provide different ways to ask the same type of question
   - Vary the context but keep the mathematical structure the same
   - Use grade-appropriate scenarios and language

5. **Step-by-Step Explanations** (3-6 steps):
   - Create a clear teaching sequence that guides students
   - Each step should build on the previous one
   - NEVER reveal the final answer - guide students to discover it
   - Use Direct Instruction principles: clear, explicit, scaffolded
   - For younger grades (1-3): More concrete, visual steps
   - For older grades (4-8): Can include more abstract reasoning

**Direct Instruction Principles to Follow:**
- Clear and explicit instruction
- Break complex tasks into small steps
- Model thinking processes
- Provide immediate feedback opportunities
- Build from concrete to abstract
- Ensure mastery before moving forward

Set has_relevant_content to True.
"""

    user_content = f"""Generate Direct Instruction content for:

Question: {question_text}
Grade: {grade}
Subject: {subject}

Use your knowledge of pedagogy, child development, and grade-appropriate teaching methods.
"""

    try:
        result = produce_structured_response(
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_content}
            ],
            structure_model=DirectInstructionContent,
            model="gpt-4o",
            temperature=0.3,
            provider="openai"
        )

        if result.has_relevant_content:
            logger.info(f"Generated DI content from knowledge base for question {question_id}")
            return result
        else:
            logger.warning(f"Failed to generate DI content from knowledge base for question {question_id}")
            return None

    except Exception as e:
        logger.error(f"Failed to generate DI content from knowledge base for question {question_id}: {e}")
        return None


def generate_di_content_for_question(question: dict, di_format: DiFormat) -> Optional[tuple[DirectInstructionContent, str]]:
    """
    Generate Direct Instruction content for a question using DI formats from MongoDB.
    Falls back to GPT-4o knowledge base if no DI formats are found.

    Args:
        question: Question dict from database
        di_format: DiFormat instance for searching formats

    Returns:
        DirectInstructionContent object or None if generation fails
    """
    question_id = question["id"]
    question_text = question.get("question_en") or question.get("question_ar") or ""
    grade = question.get("grade", 3)
    domain = question.get("domain", "")
    subject = question.get("substandard_description") or domain or "Mathematics"

    try:
        # Use the existing get_di_insights_for_scaffolding_rag method
        di_insights = di_format.get_di_insights_for_scaffolding_rag(
            question_text=question_text,
            subject=subject,
            grade=grade
        )

        # Check if we got relevant insights
        if not di_insights or not di_insights.source_formats:
            logger.warning(f"No relevant DI formats found for question {question_id}, falling back to knowledge base")
            # Fallback to GPT-4o knowledge base
            kb_result = generate_di_content_from_knowledge_base(question)
            if kb_result:
                return (kb_result, "knowledge_base")
            return None

        # Extract information from source formats
        formats_context = di_insights.source_formats

        # Build the system instructions
        system_instructions = f"""You are a Direct Instruction pedagogy expert.

Your task is to generate Direct Instruction teaching content for the following question based on the DI formats and insights provided.

**Question (Grade {grade}):**
{question_text}

**Subject/Domain:** {subject}

**DI Insights:**
{di_insights.insights_text}

**Available DI Formats:**
{formats_context}

**Your task:**
Generate comprehensive Direct Instruction content that includes:

1. **Prerequisite Skills**: What skills must students already have? (2-4 skills)
2. **Microskills**: Break down this specific problem into teachable micro-steps (2-5 skills)
3. **Vocabulary**: Key terms students need to understand (2-4 terms with definitions)
4. **Question Stems**: Alternative ways to ask this type of question (2-4 stems)
5. **Step-by-Step Explanations**: Clear teaching sequence that guides without revealing the answer (3-6 steps)

**Important Guidelines:**
- Content must be grade-appropriate for Grade {grade}
- Use the DI formats and insights as inspiration but adapt to this specific question
- Keep language clear and accessible
- Don't reveal the answer in the steps - guide students to discover it
- The step-by-step explanations should align with the DI insights provided
- Set has_relevant_content to True since we already validated relevance
"""

        user_content = f"""Generate Direct Instruction content for this question:

Question: {question_text}
Grade: {grade}
Subject: {subject}

Number of relevant DI formats found: {len(formats_context)}
"""

        # Use GPT-4o with structured output
        result = produce_structured_response(
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": user_content}
            ],
            structure_model=DirectInstructionContent,
            model="gpt-4o",
            temperature=0.3,
            provider="openai"
        )

        if result.has_relevant_content:
            logger.info(f"Generated DI content for question {question_id} using DI formats")
            return (result, "di_formats")
        else:
            logger.warning(f"Generated DI content marked as not relevant for question {question_id}")
            return None

    except Exception as e:
        logger.error(f"Failed to generate DI content for question {question_id}: {e}")
        return None


def format_di_content_as_markdown(di_content: DirectInstructionContent) -> str:
    """Format DirectInstructionContent as markdown text."""
    markdown = "# Direct Instruction\n\n"

    if di_content.prerequisite_skills:
        markdown += "## Prerequisite Skills\n"
        for skill in di_content.prerequisite_skills:
            markdown += f"- {skill}\n"
        markdown += "\n"

    if di_content.microskills:
        markdown += "## Microskills\n"
        for skill in di_content.microskills:
            markdown += f"- {skill}\n"
        markdown += "\n"

    if di_content.vocabulary:
        markdown += "## Precise Vocabulary\n"
        for vocab in di_content.vocabulary:
            markdown += f"- **{vocab.term}**: {vocab.definition}\n"
        markdown += "\n"

    if di_content.question_stems:
        markdown += "## Question Stems\n"
        for stem in di_content.question_stems:
            markdown += f"- {stem}\n"
        markdown += "\n"

    if di_content.step_by_step_explanations:
        markdown += "## Step-by-Step Explanation\n"
        for idx, step in enumerate(di_content.step_by_step_explanations, 1):
            markdown += f"{idx}. {step}\n"
        markdown += "\n"

    return markdown


def update_question_di(question_id: str, di_content: DirectInstructionContent):
    """Update question in database with Direct Instruction content."""
    # Create a new Supabase client for this update
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    try:
        # Format as markdown
        di_markdown = format_di_content_as_markdown(di_content)

        # Fetch existing raw_data to preserve it
        existing = client.table("extracted_questions").select("raw_data").eq("id", question_id).execute()
        existing_raw_data = existing.data[0].get("raw_data", {}) if existing.data else {}

        # Merge DI info into raw_data
        updated_raw_data = {
            **existing_raw_data,
            "direct_instruction": {
                "prerequisite_skills": di_content.prerequisite_skills,
                "microskills": di_content.microskills,
                "vocabulary": [{"term": v.term, "definition": v.definition} for v in di_content.vocabulary],
                "question_stems": di_content.question_stems,
                "step_by_step_explanations": di_content.step_by_step_explanations,
                "generated_at": datetime.utcnow().isoformat()
            }
        }

        update_data = {
            "direct_instruction_raw": di_markdown,
            "raw_data": updated_raw_data
        }

        client.table("extracted_questions").update(update_data).eq("id", question_id).execute()
        logger.info(f"Updated question {question_id} with DI content")

    except Exception as e:
        logger.error(f"Failed to update question {question_id}: {e}")
        raise


def fetch_textbook_questions(
    limit: Optional[int] = None,
    grade: Optional[int] = None,
    min_quality: float = 6.0
) -> List[dict]:
    """Fetch textbook questions from Supabase that need DI content."""

    query = supabase.table("extracted_questions").select("*")

    # Only textbook questions
    query = query.eq("source_type", "textbook_pdf")

    # Filter by grade (only grades 1-8)
    if grade:
        if grade < 1 or grade > 8:
            logger.warning(f"Grade {grade} is outside the valid range (1-8). No questions will be fetched.")
            return []
        query = query.eq("grade", grade)
    else:
        # Only grades 1-8
        query = query.gte("grade", 1).lte("grade", 8)

    # Only good quality questions
    query = query.gte("quality_score", min_quality)

    # Only questions without DI content
    query = query.is_("direct_instruction_raw", "null")

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

    logger.info(f"Fetched {len(all_questions)} textbook questions without DI content (quality >= {min_quality})")
    return all_questions


def main():
    parser = argparse.ArgumentParser(description="Populate Direct Instruction content for textbook questions (Grades 1-8)")
    parser.add_argument("--limit", type=int, help="Number of questions to process (default: all)")
    parser.add_argument("--grade", type=int, choices=range(1, 9), metavar="1-8", help="Filter by grade (1-8)")
    parser.add_argument("--min-quality", type=float, default=6.0, help="Minimum quality score (default: 6.0)")
    parser.add_argument("--workers", type=int, default=5, help="Number of concurrent workers (default: 5)")

    args = parser.parse_args()

    logger.info("="*60)
    logger.info("TEXTBOOK DI CONTENT GENERATION STARTED (Grades 1-8)")
    logger.info("="*60)

    if args.limit:
        logger.info(f"Processing up to {args.limit} questions")
    else:
        logger.info("Processing all textbook questions without DI content")

    if args.grade:
        logger.info(f"Grade filter: {args.grade}")
    else:
        logger.info("Grades: 1-8 (all)")

    logger.info(f"Minimum quality score: {args.min_quality}")

    # Fetch questions
    questions = fetch_textbook_questions(
        limit=args.limit,
        grade=args.grade,
        min_quality=args.min_quality
    )

    if not questions:
        logger.info("No questions to process")
        return

    stats = {
        "total": len(questions),
        "processed": 0,
        "failed": 0,
        "no_relevant_formats": 0,
        "from_di_formats": 0,
        "from_knowledge_base": 0
    }

    # Initialize DiFormat once (it manages its own connections)
    di_format = DiFormat()

    def process_question(question):
        """Process a single question."""
        question_id = question["id"]

        result = generate_di_content_for_question(question, di_format)

        if result:
            di_content, source = result
            update_question_di(question_id, di_content)
            return ("success", source)
        else:
            return ("failed", None)

    # Process questions in parallel
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_question, q): q for q in questions}

        with tqdm(total=len(futures), desc="Processing", unit=" questions", ncols=100) as pbar:
            for future in as_completed(futures):
                try:
                    status, source = future.result()

                    if status == "success":
                        stats["processed"] += 1
                        if source == "di_formats":
                            stats["from_di_formats"] += 1
                        elif source == "knowledge_base":
                            stats["from_knowledge_base"] += 1
                except Exception as e:
                    logger.error(f"Error processing question: {e}")
                    stats["failed"] += 1

                pbar.update(1)
                pbar.set_postfix_str(f"✓ {stats['processed']} (DI: {stats['from_di_formats']} | KB: {stats['from_knowledge_base']}) | ✗ {stats['failed']}")

    # Final Summary
    logger.info("\n" + "="*60)
    logger.info("DI CONTENT GENERATION COMPLETE")
    logger.info("="*60)
    logger.info(f"Total processed: {stats['total']}")
    logger.info(f"Successfully generated: {stats['processed']}")
    logger.info(f"  - From DI formats: {stats['from_di_formats']}")
    logger.info(f"  - From knowledge base: {stats['from_knowledge_base']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info("="*60)


if __name__ == "__main__":
    main()
