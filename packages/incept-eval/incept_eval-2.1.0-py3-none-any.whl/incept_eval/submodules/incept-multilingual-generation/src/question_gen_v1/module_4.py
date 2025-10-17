#!/usr/bin/env python3
"""
Module 4: Multiple Choice Conversion using Falcon LLM
Takes questions and answers from Module 3 and converts them into multiple choice.
Correct answer + PLAUSIBLE incorrect ones. Uses Falcon endpoint for all generations.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from enum import Enum
import time
import json
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.llms import produce_structured_response, format_messages_for_api
from src.utils.json_repair import model_to_json, parse_json
from src.utils.progress_bar import ProgressBar


logger = logging.getLogger(__name__)


class OptionPosition(str, Enum):
    """Valid option positions for multiple choice questions"""
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class GeneratedQuestion:
    """Generated question with complete solution and metadata."""
    question_id: str
    question_text: str
    answer: str
    working_steps: List[str]
    mathematical_proof: str
    parameter_values: Dict[str, Any]
    difficulty_score: float
    cognitive_load: str
    subject: str
    grade: int
    operation_type: str
    validation_status: str

class MultipleChoiceSchema(BaseModel):
    """Structured schema for multiple choice question generation"""
    question: str = Field(description="The question text in Arabic")
    option_a: str = Field(description="Text for option A")
    option_b: str = Field(description="Text for option B")
    option_c: str = Field(description="Text for option C")
    option_d: str = Field(description="Text for option D")
    correct_answer: OptionPosition = Field(
        description="Which option (A, B, C, or D) is correct")
    backup_option: str = Field(
        description="Backup incorrect option in case of duplicates")
    diffulty: Optional[str] = Field(
        description="Difficulty level: easy, medium, hard, expert", default=None)

class BatchMultipleChoiceSchema(BaseModel):
    """Batch schema for multiple choice question generation"""
    questions: List[MultipleChoiceSchema] = Field(description="List of multiple choice questions")


@dataclass
class MultipleChoiceOption:
    """Single multiple choice option."""
    option_id: str  # A, B, C, D
    text: str
    is_correct: bool
    plausibility_reason: str


@dataclass
class MultipleChoiceQuestion:
    """Complete multiple choice question with plausible distractors."""
    question_id: str
    question_text: str
    options: Dict[str, str]  # New format: {"A": "4 cm", "B": "0.4 cm", "C": "0.04 cm", "D": "1 cm"}
    correct_answer: str  # The actual answer text (e.g., "4 cm")
    correct_answer_choice: str  # A, B, C, or D (which option is correct)
    subject: str
    grade: int
    difficulty: str
    distractor_quality: str
    conversion_status: str


class Module4MultipleChoiceConverter:
    """
    Module 4: Convert questions to multiple choice using Gemini Flash.
    Run Gemini once per question for reusability.
    Generate PLAUSIBLE incorrect options.
    """

    def __init__(self):
        self.conversion_history = []
        self._structured_output_available = True

    def convert_to_multiple_choice(
        self,
        questions: List[GeneratedQuestion],
        language: str = "arabic",
        provider_requested: str = "openai",
        max_workers: int = 10,
    ) -> List[MultipleChoiceQuestion]:
        """Convert questions in batches for efficiency."""
        BATCH_SIZE = 8
        ordered: list[MultipleChoiceQuestion | None] = [None] * len(questions)

        # Progress bar to track conversion
        mcq_progress = ProgressBar(len(questions), f"🔄 Converting to MCQ ({provider_requested.upper()})")
        if len(questions) == 0:
            return []

        # Process in batches
        # max_workers is passed from orchestrator
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {}
            for batch_start in range(0, len(questions), BATCH_SIZE):
                batch_end = min(batch_start + BATCH_SIZE, len(questions))
                batch = questions[batch_start:batch_end]
                batch_indices = list(range(batch_start, batch_end))

                future = ex.submit(self._convert_batch_questions, batch, batch_indices, language, provider_requested)
                futures[future] = (batch_start, batch_end)

            for fut in as_completed(futures):
                batch_start, batch_end = futures[fut]
                try:
                    batch_results = fut.result()
                    for idx, result in batch_results:
                        ordered[idx] = result
                        mcq_progress.update(1, f"✓ Q{idx+1}")
                except Exception as e:
                    # On batch failure, fallback to individual conversion
                    logger.warning(f"Batch {batch_start}-{batch_end} failed: {e}, falling back to individual conversion")
                    for i in range(batch_start, batch_end):
                        try:
                            result = self._convert_single_question(questions[i], i, language, provider_requested)
                            ordered[i] = result
                            mcq_progress.update(1, f"✓ Q{i+1}")
                        except Exception as e2:
                            mcq_progress.update(1, f"✗ Q{i+1}")
                            logger.error(f"Q{i+1} conversion failed: {str(e2)[:100]}...")

        results = [mc for mc in ordered if mc is not None]
        success_rate = len(results) / len(questions) * 100
        mcq_progress.complete(f"Success: {len(results)}/{len(questions)} ({success_rate:.1f}%)")
        return results

    def _convert_batch_questions(
        self,
        questions: List[GeneratedQuestion],
        indices: List[int],
        language: str = 'arabic',
        provider_requested: str = 'openai'
    ) -> List[tuple[int, Optional[MultipleChoiceQuestion]]]:
        """
        Convert multiple questions in a single LLM call for efficiency.
        Returns list of (index, question) tuples.
        """
        try:
            # Build batch prompt
            batch_inputs = []
            for question, index in zip(questions, indices):
                random.seed(index)
                correct_position = random.choice(["A", "B", "C", "D"])
                batch_inputs.append({
                    'index': index,
                    'question_text': question.question_text,
                    'answer': question.answer,
                    'correct_position': correct_position
                })

            # Create batch prompt
            prompt = f"""Create multiple choice options for {len(batch_inputs)} questions. ALL options must be PLAUSIBLE answers.

For each question below, generate 4 options following these rules:

OPTION GENERATION RULES:
✓ Direct answer values matching the correct answer's format
✓ Use the same units, notation, and structure as the correct answer
✓ Generate plausible incorrect alternatives
✓ Match the exact format and units of the correct answer

QUESTIONS:
"""
            for item in batch_inputs:
                prompt += f"""\n--- Question {item['index']} ---
QUESTION: {item['question_text']}
CORRECT ANSWER: {item['answer']}
PLACE CORRECT ANSWER IN: option_{item['correct_position'].lower()}
correct_answer: "{item['correct_position']}"
"""

            prompt += f"""\n\nReturn JSON array with {len(batch_inputs)} questions in this exact format:
{{
  "questions": [
    {{
      "question": "<question text>",
      "option_a": "<answer>",
      "option_b": "<answer>",
      "option_c": "<answer>",
      "option_d": "<answer>",
      "correct_answer": "A|B|C|D",
      "backup_option": "<backup answer>",
      "diffulty": "medium"
    }},
    ...
  ]
}}"""

            messages = format_messages_for_api(
                system_message=f"You are an expert at creating clean, simple multiple choice questions in {language}. Follow all instructions precisely.",
                user_message=prompt
            )

            # Use structured response
            structured_response = produce_structured_response(
                messages=messages,
                structure_model=BatchMultipleChoiceSchema,
                provider=provider_requested,
                temperature=0.1,
                max_output_tokens=8000
            )

            # Parse batch results
            results = []
            # Handle both dict and Pydantic object responses
            questions_list = None
            if isinstance(structured_response, dict):
                questions_list = structured_response.get('questions', [])
            elif hasattr(structured_response, 'questions'):
                questions_list = structured_response.questions

            if questions_list:
                for item, orig_q, idx in zip(questions_list, questions, indices):
                    mc_q = self._from_schema_obj(item, orig_q, idx)
                    results.append((idx, mc_q))
            else:
                logger.error(f"Batch conversion returned unexpected format: {type(structured_response)}")
                # Fallback: return empty for all
                results = [(idx, None) for idx in indices]

            return results

        except Exception as e:
            logger.error(f"Batch conversion failed: {e}")
            # Return empty results, will fallback to individual conversion
            return [(idx, None) for idx in indices]

    def _convert_single_question(
        self,
        question: GeneratedQuestion,
        index: int,
        language: str = 'arabic',
        provider_requested: str = 'openai'
    ) -> Optional[MultipleChoiceQuestion]:
        """
        Convert single question using GPT-4o with structured output.
        Generate PLAUSIBLE incorrect options with validated schema.
        """
        try:
            # Randomly select which option position gets the correct answer
            # Ensure variation by using question index to influence position
            positions = ["A", "B", "C", "D"]
            # Use index to ensure different questions get different correct positions
            # generate a pseudo-random but deterministic position based on index
            random.seed(index)
            correct_position = random.choice(positions)

            # Create specialized prompt for multiple choice conversion
            prompt = self._create_structured_conversion_prompt(
                question, correct_position, language)

            # Format messages for API
            messages = format_messages_for_api(
                system_message=f"You are an expert at creating clean, simple multiple choice questions in {language}. Follow all instructions precisely.",
                user_message=prompt
            )

            # Use structured response utility function with configured provider
            structured_response = produce_structured_response(
                messages=messages,
                structure_model=MultipleChoiceSchema,
                provider=provider_requested,
                temperature=0.1,
                max_output_tokens=2100
            )
            mc_question = self._from_schema_obj(
                structured_response, question, index)

            return mc_question

        except Exception as e:
            logger.error(
                f"❌ MODULE 4 Q{index+1}: Single question conversion failed: {e}")
            return None

    def _create_structured_conversion_prompt(self, question: GeneratedQuestion, correct_position: str, language: str = 'arabic') -> str:
        """
        Create concise prompt for generating multiple choice options.
        Grade and subject agnostic with positive instructions.
        """

        prompt = f"""Create multiple choice options. ALL options must be PLAUSIBLE answers.

QUESTION: {question.question_text}
CORRECT ANSWER: {question.answer}

CRITICAL PLACEMENT:
1. Place "{question.answer}" EXACTLY in option_{correct_position.lower()}
2. Set correct_answer to "{correct_position}"

OPTION GENERATION RULES:

✓ VALID OPTIONS:
- Direct answer values matching the correct answer's format
- Use the same units, notation, and structure as the correct answer

DISTRACTOR STRATEGY:
• Generate plausible incorrect alternatives
• Match the exact format and units of the correct answer
• Ensure each option could reasonably be selected

Return ONLY this JSON:
{{
"question": "{question.question_text}",
"option_a": "clean highly relevant to the question answer",
"option_b": "clean highly relevant to the question answer",
"option_c": "clean highly relevant to the question answer",
"option_d": "clean highly relevant to the question answer",
"correct_answer": "{correct_position}",
"backup_option": "clean highly relevant to the question answer",
"diffulty": "medium"
}}

FINAL CHECK:
✓ option_{correct_position.lower()} = "{question.answer}" exactly
✓ All options are clean numbers/units only
✓ No dictionary text, pipes, or complex phrases
✓ All options use same format/units"""

        return prompt

    def _from_schema_obj(
        self,
        schema_obj: MultipleChoiceSchema,
        original_question: GeneratedQuestion,
        index: int
    ) -> MultipleChoiceQuestion:
        try:
            try:
                schema_obj = model_to_json(schema_obj)
                if isinstance(schema_obj, dict):
                    pass
                else:
                    schema_obj = parse_json(schema_obj)
            except Exception as e:
                logger.warning(f"Schema conversion failed: {str(e)[:50]}...")

            """Map Pydantic schema object to our internal MultipleChoiceQuestion format"""

            # Create options mapping
            options_map = {
                "A": str(schema_obj["option_a"]),
                "B": str(schema_obj["option_b"]),
                "C": str(schema_obj["option_c"]),
                "D": str(schema_obj["option_d"]),
            }
            # Check for duplicates and replace with backup if needed
            correct_pos = schema_obj["correct_answer"]
            correct_text = str(options_map[correct_pos]).strip()
            backup = str(schema_obj["backup_option"])

            # Trust the prompt to generate clean options - minimal validation only
            for opt_id, opt_text in list(options_map.items()):
                opt_str = str(opt_text).strip()
                # Only check for obvious failures (empty options)
                if not opt_str or len(opt_str) < 1:
                    logger.warning(f"Empty option detected at {opt_id}")
                    if backup and backup.strip():
                        options_map[opt_id] = backup
                        logger.info(f"Replaced empty option {opt_id} with backup")
                    else:
                        # Generate a simple fallback
                        fallback = self._generate_fallback_option(correct_text, opt_id)
                        options_map[opt_id] = fallback
                        logger.info(f"Generated fallback for {opt_id}: {fallback}")

            # CRITICAL: Enforce correct answer placement
            # First, ensure correct answer is in the right position
            if str(options_map[correct_pos]).strip() != correct_text:
                logger.warning(f"Correct answer not in position {correct_pos}! Fixing placement.")
                # Find where the correct answer actually is
                for opt_id, opt_text in options_map.items():
                    if str(opt_text).strip() == correct_text and opt_id != correct_pos:
                        # Swap the positions
                        options_map[correct_pos], options_map[opt_id] = options_map[opt_id], options_map[correct_pos]
                        logger.info(f"Swapped correct answer from {opt_id} to {correct_pos}")
                        break
                else:
                    # Correct answer not found anywhere, force it into correct position
                    logger.error(f"Correct answer '{correct_text}' not found in any option. Forcing placement.")
                    options_map[correct_pos] = correct_text

            # Now check for duplicates in wrong positions
            for opt_id, opt_text in list(options_map.items()):
                if opt_id != correct_pos and str(opt_text).strip() == correct_text:
                    if backup and backup.strip() != correct_text:
                        options_map[opt_id] = backup
                        logger.info(f"Replaced duplicate correct answer at {opt_id} with backup")
                    else:
                        # Generate a simple fallback based on correct answer
                        fallback = self._generate_fallback_option(correct_text, opt_id)
                        options_map[opt_id] = fallback
                        logger.info(f"Generated fallback for duplicate at {opt_id}: {fallback}")
                    break

            # Create option objects with plausibility analysis
            option_objects = []
            for option_id, option_text in options_map.items():
                is_correct = (option_id == schema_obj["correct_answer"])
                plausibility = self._analyze_plausibility(
                    option_text,
                    original_question.answer,
                    is_correct
                )

                option_objects.append(MultipleChoiceOption(
                    option_id=option_id,
                    text=option_text,
                    is_correct=is_correct,
                    plausibility_reason=plausibility
                ))

            # Preserve original question_id for matching with Module 5 scaffolding
            mc_question_id = original_question.question_id

            # FINAL VERIFICATION: Ensure correct answer is in the right position
            final_correct_option = None
            for option in option_objects:
                if option.option_id == schema_obj["correct_answer"] and option.is_correct:
                    final_correct_option = option
                    break

            if not final_correct_option:
                logger.error(f"CRITICAL: Final verification failed - correct answer not properly placed!")
                # Emergency fix: force correct answer into right position
                for option in option_objects:
                    if option.option_id == schema_obj["correct_answer"]:
                        option.text = original_question.answer
                        option.is_correct = True
                        logger.error(f"Emergency fix: Forced correct answer into position {option.option_id}")
                        break

            # Create options dictionary in new format
            options_dict = {}
            correct_answer_text = ""
            
            for option in option_objects:
                options_dict[option.option_id] = option.text
                if option.is_correct:
                    correct_answer_text = option.text
            
            return MultipleChoiceQuestion(
                question_id=mc_question_id,
                question_text=schema_obj["question"],
                options=options_dict,  # New dict format: {"A": "4 cm", "B": "0.4 cm", ...}
                correct_answer=correct_answer_text,  # Actual answer text: "4 cm"
                correct_answer_choice=schema_obj["correct_answer"],  # A, B, C, or D
                subject=original_question.subject,
                grade=original_question.grade,
                difficulty=schema_obj["diffulty"] or self._map_difficulty_score_to_level(
                    original_question.difficulty_score),
                distractor_quality=1,
                conversion_status="sdk_structured_validated_quality_controlled"
            )

        except Exception as e:
            logger.error(f"{e} in _from_schema_obj for {schema_obj}")
            return schema_obj

    def _generate_fallback_option(self, correct_answer: str, option_id: str) -> str:
        """Generate a simple mathematical fallback option when invalid content is detected."""
        import re

        # Extract numbers from correct answer
        numbers = re.findall(r'\d+\.?\d*', correct_answer)

        if numbers:
            try:
                correct_num = float(numbers[0])
                # Generate plausible alternatives based on option position
                multipliers = {"A": 0.5, "B": 1.5, "C": 2.0, "D": 0.75}
                fallback_num = int(correct_num * multipliers.get(option_id, 1.2))

                # Preserve units/format from correct answer
                if "cm²" in correct_answer:
                    return f"{fallback_num} cm²"
                elif "cm³" in correct_answer:
                    return f"{fallback_num} cm³"
                elif "cm" in correct_answer:
                    return f"{fallback_num} cm"
                else:
                    return str(fallback_num)
            except (ValueError, IndexError):
                pass

        # If no numbers found, generate generic mathematical alternatives
        generic_options = {
            "A": "Option not available",
            "B": "Cannot be determined",
            "C": "Insufficient information",
            "D": "None of the above"
        }

        return generic_options.get(option_id, "Invalid option")

    def _analyze_plausibility(
        self,
        option_text: str,
        correct_answer: str,
        is_correct: bool
    ) -> str:
        """Analyze plausibility of option."""

        if is_correct:
            return "correct_answer"

        # Extract numerical values for comparison
        import re
        option_numbers = re.findall(r'\d+\.?\d*', option_text)
        correct_numbers = re.findall(r'\d+\.?\d*', correct_answer)

        if option_numbers and correct_numbers:
            try:
                option_val = float(option_numbers[0])
                correct_val = float(correct_numbers[0])

                # Analyze the relationship
                ratio = option_val / correct_val if correct_val != 0 else 0

                if 0.3 <= ratio <= 0.7:
                    return "plausible_underestimate"
                elif 1.3 <= ratio <= 3.0:
                    return "plausible_overestimate"
                elif 0.8 <= ratio <= 1.2:
                    return "very_close_error"
                else:
                    return "potentially_implausible"

            except ValueError:
                return "non_numerical_comparison"

        return "plausible_distractor"

    def _map_difficulty_score_to_level(self, difficulty_score: float) -> str:
        """Map difficulty score to difficulty level."""
        if difficulty_score <= 0.3:
            return 'easy'
        elif difficulty_score <= 0.6:
            return 'medium'
        elif difficulty_score <= 0.8:
            return 'hard'
        else:
            return 'expert'

    def _get_language_specific_instructions(self, language: str) -> str:
        """Get specific instructions for different languages in multiple choice generation"""
        language_instructions = {
            'arabic': """
                ARABIC-SPECIFIC REQUIREMENTS FOR REGIONAL AUTHENTICITY (DOK1-DOK4):
                - DOK1: Produce all text in Modern Standard Arabic, with correct grammar and grade-level vocabulary verified through production testing with actual student populations
                - DOK1: Maintain right-to-left layout conventions and use Arabic punctuation: الفاصلة العربية (،)؛ الفاصلة المنقوطة (؛)؛ علامة الاستفهام (؟)
                - DOK2: Use consistent terminology; do not vary synonyms across stem and options to maintain wording consistency
                - DOK2: Use Arabic-Indic digits (٠١٢٣٤٥٦٧٨٩) when pedagogically appropriate; Western numerals acceptable in formulas when standard
                - DOK3: Preserve standard notation; symbols (×, ÷, =, ^) may remain in Latin script for global literacy
                - DOK3: Cultural contexts must be appropriate for UAE students, including names, scenarios, and examples that enhance understanding
                - DOK4 SPIKY: Mixed-script approach with standard notation embedded in Arabic text maintains global literacy
                - DOK4 SPIKY: Cultural elements must enhance understanding by providing relevant context, never distract from learning objectives
            """,
            'english': """
                - All question text and options must be in proper English with correct grammar
                - Use appropriate terminology for the subject area
                - Numbers should use Western Arabic numerals (0123456789)
                - Options should be labeled as A) B) C) D)
                - Question structure should follow English syntax
            """
        }

        return language_instructions.get(language.lower(), language_instructions['english'])
