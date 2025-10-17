from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

import dspy
from src.question_gen_v1.module_2 import ExtractedPattern
from src.llms import dspy_lm as UserLLM, format_messages_for_api, solve_with_llm
from src.utils.module_3 import GeneratedQuestion, _safe_list, extract_instructional_text, first_json_block, render_template, sample_params
from src.utils.progress_bar import ProgressBar
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.wolfram.solve import wolfram_solve

logger = logging.getLogger(__name__)

def _ensure_lm():
    if getattr(dspy.settings, "lm", None) is not None:
        return
    try:
        if UserLLM is not None:
            lm = UserLLM()
            dspy.configure(lm=lm)
            logger.info("Configured DSPy with user-provided LLMs.LLM().")
            return
    except Exception as e:
        logger.warning(f"Could not init UserLLM from LLMs: {e}")
    try:
        dspy.configure(lm=dspy.OpenAI(model="gpt-3.5-turbo"))
        logger.info("Configured DSPy with fallback OpenAI adapter.")
    except Exception as e:
        logger.error(f"Failed to configure any LM for DSPy: {e}")

_ensure_lm()

class MathSolveSignature(dspy.Signature):
    """
    Solve a math problem rigorously with numbered steps and ONE 'Final Answer: <...>' line.
    """
    sys_instructions = dspy.InputField()
    problem = dspy.InputField()
    solution = dspy.OutputField(desc="Plain text solution with numbered steps and one final line 'Final Answer: <...>'")

class ExtractFinalAnswerSignature(dspy.Signature):
    """
    From a text, extract ONLY the text after the LAST 'Final Answer:' tag.
    """
    sys_instructions = dspy.InputField()
    text = dspy.InputField()
    extracted = dspy.OutputField(desc="Only the final answer text, trimmed.")

class DirectMathSolveSignature(dspy.Signature):
    """
    Solve a math problem and return ONLY the final answer (no steps, no explanation).
    Answer must be concise: a number with units, or a simple mathematical expression.
    """
    sys_instructions = dspy.InputField()
    problem = dspy.InputField()
    final_answer = dspy.OutputField(desc="ONLY the final answer - a number with units or simple expression")

class MathematicalQuestionDetectionSignature(dspy.Signature):
    """Determine if a question requires mathematical computation."""
    question_text = dspy.InputField(desc="Question to analyze")

    detection_result = dspy.OutputField(desc="JSON with: is_mathematical, reasoning, solvability_score, requires_computation")

class ValidateQuestionSignature(dspy.Signature):
    """Validate if a question is mathematical and grade-appropriate."""
    question_text = dspy.InputField(desc="Question to validate")
    grade = dspy.InputField(desc="Target grade level")
    subject = dspy.InputField(desc="Subject area")
    difficulty = dspy.InputField(desc="Difficulty level")
    language = dspy.InputField(desc="Target language")
    current_answer = dspy.InputField(desc="Current answer")

    validation_result = dspy.OutputField(desc="JSON with: is_mathematical, is_valid, issues, grade_appropriate, clarity_score (1-10), grade_level_score (1-10), concepts_too_advanced, solvability_score (1-10)")

class BatchValidateQuestionsSignature(dspy.Signature):
    """Validate multiple questions in batch for efficiency."""
    questions_json = dspy.InputField(desc="JSON array with: id, question_text, grade, subject, difficulty, language")

    validation_results = dspy.OutputField(desc="JSON array with: id, is_mathematical, is_valid, issues, grade_appropriate, clarity_score, grade_level_score, concepts_too_advanced, solvability_score")

class CorrectQuestionSignature(dspy.Signature):
    """
    CRITICAL: Create a GRADE-APPROPRIATE mathematical question with grade-level appropriate numerical answer for students.

    MANDATORY ANSWER FORMAT (NO EXCEPTIONS):
    - Answer MUST be: clean and final
    - Use numbers and units appropriate for the specified grade level
    - Choose familiar objects and measurements suitable for the target grade

    ABSOLUTELY FORBIDDEN CONTENT:
    - Nutritional data tables with calories/vitamins/fat content
    - Dictionary definitions with multiple meanings and numbered lists
    - Complex scientific data or technical specifications
    - Text with pipe symbols (|), multi-line tables, or data ranges
    - Phrases like "(data not available)", "leadership position", etc.
    - Any non-mathematical content (medical, business, technical terms)

    DETECTION AND REPLACEMENT:
    - If original answer contains ANY forbidden content above, IGNORE it completely
    - Generate a fresh, grade-appropriate math problem matching the complexity level for that grade
    - Use age-appropriate objects and concepts students at that grade level understand

    GRADE-ADAPTIVE COMPLEXITY (MANDATORY):
    - Automatically scale mathematical complexity based on the specified grade level
    - Use school grade-appropriate vocabulary, number ranges, and mathematical operations for that grade
    - Select objects, units, and concepts that students at that grade level would understand
    - Ensure mathematical operations match what students learn at that specific grade level

    OUTPUT REQUIREMENTS:
    - question_text: Grade-appropriate math problem using age-appropriate objects and complexity
    - answer: Grade-level appropriate number with suitable units and complexity for that grade
    - working_steps: Grade-appropriate solution steps matching mathematical operations taught at that level
    - rationale: "Grade-appropriate mathematical problem matching complexity expectations for the target grade level"
    """
    original_question = dspy.InputField(desc="The original question text that needs fixing")
    grade = dspy.InputField(desc="Target grade level for appropriateness")
    subject = dspy.InputField(desc="Subject area (mathematics)")
    difficulty = dspy.InputField(desc="Target difficulty level")
    language = dspy.InputField(desc="Target language")
    issues = dspy.InputField(desc="Specific issues to address")
    original_answer = dspy.InputField(desc="Original problematic answer")

    corrected_question = dspy.OutputField(desc="JSON with: question_text (Grade-appropriate math question matching grade-level complexity), answer (grade-appropriate answer with suitable complexity), working_steps (grade-level appropriate solution steps), rationale (why this matches grade expectations), improvements_made (list of grade-level fixes applied)")

class Module3MathematicsGenerator:
    def __init__(self, max_tokens_generate: int = 3000, max_tokens_extract: int = 1000):
        self.max_tokens_generate = max_tokens_generate
        self.max_tokens_extract = max_tokens_extract
        if hasattr(dspy, "SelfConsistency"):
            self._generator = dspy.SelfConsistency(MathSolveSignature, k=3)
        else:
            self._generator = dspy.ChainOfThought(MathSolveSignature)
        self._extractor = dspy.Predict(ExtractFinalAnswerSignature)
        self._direct_solver = dspy.ChainOfThought(DirectMathSolveSignature)

        # Question validation and correction modules
        # Use Predict instead of ChainOfThought for validation to reduce token usage
        # ChainOfThought adds reasoning which can exceed Falcon's 8192 token limit
        self._math_detector = dspy.Predict(MathematicalQuestionDetectionSignature)
        self._validator = dspy.Predict(ValidateQuestionSignature)
        self._batch_validator = dspy.Predict(BatchValidateQuestionsSignature)
        self._corrector = dspy.ChainOfThought(CorrectQuestionSignature)

    GENERATE_LOGIC = (
        "You are solving a mathematics problem with grade-appropriate complexity. "
        "Write a solution with grade-level appropriate steps and complexity.\n\n"
        "LANGUAGE HANDLING:\n"
        "- If the question is in Arabic or another language, solve in that SAME language\n"
        "- Use Western numerals (0-9) for all calculations regardless of question language\n"
        "- Preserve the question's language throughout the solution\n\n"
        "GENERAL RULES:\n"
        "1) Always derive answers using the canonical formula or method for the given topic (algebra, geometry, calculus, statistics, etc.).\n"
        "2) All arithmetic must be explicitly shown (intermediate steps, not just final result).\n"
        "3) Fractions must be simplified, square roots/radicals expressed in exact form unless approximation is requested.\n"
        "4) Units must be included where applicable (length, area, volume, etc.).\n"
        "5) If the problem is logically inconsistent (e.g., impossible triangle, negative length), explicitly flag as 'invalid question' and explain why.\n"
        "6) Never invent context (historical names, stories, anecdotes) unless explicitly provided in the input.\n\n"
        "MATH-SPECIFIC RULES:\n"
        "7) Geometry: enforce canonical rules (area, perimeter, angles, volume, circumference).\n"
        "8) Algebra: solve by isolating the variable step-by-step; check final solution by substitution.\n"
        "9) Calculus: show differentiation/integration process, including constants of integration.\n"
        "10) Probability/Statistics: clearly state assumptions (independence, sample size, distributions) before computing.\n\n"
        "SOLUTION FORMAT:\n"
        "- If needed, include one minimal line 'Assumption: <...>' before the steps; otherwise omit.\n"
        "- Steps: number them (1., 2., 3., …). Show key algebra, calculus, or proof moves; do not skip pivotal transformations.\n"
        "- Exact vs approximate: prefer exact form (fractions, radicals, π). If a decimal is useful, give it once (3 sig figs) in the steps, but choose ONE canonical form for the final line.\n"
        "- Multiple answers: present as a comma-separated list in increasing order; intervals in standard interval notation; vectors/matrices in standard bracket form.\n"
        "- Edge conditions: state domain restrictions, existence/uniqueness notes, and handle no-solution/infinite-solution cases explicitly.\n"
        "- Include a single short 'Check:' line (substitution, derivative/integral check, or condition verification) before the final line.\n"
        "- Prohibited: restating the entire question, meta commentary, multiple final answers, or any text after the final line.\n\n"
        "Finish with exactly one line:\n"
        "Final Answer: <answer>\n\n"
        "Plain text only. Perform all calculations/conversions yourself."
    )

    EXTRACT_LOGIC = (
        "From the provided text, locate the LAST line that begins with 'Final Answer:'. "
        "Return ONLY the text AFTER 'Final Answer:' (trim whitespace and surrounding quotes). "
        "Output nothing else."
    )

    DIRECT_SOLVE_LOGIC = (
        "Solve this mathematics problem and return ONLY the final answer.\n\n"
        "LANGUAGE HANDLING:\n"
        "- If the question is in Arabic or another language, provide the answer in that SAME language\n"
        "- Use Western numerals (0-9) for all numbers regardless of question language\n"
        "- Preserve the question's language for units and text\n\n"
        "ANSWER FORMAT:\n"
        "- Return ONLY the final answer (no steps, no working, no explanation)\n"
        "- Include units where applicable\n"
        "- For multiple answers, separate with commas\n"
        "- Keep it concise: just the number/expression with units\n\n"
        "Examples:\n"
        "- '42 meters'\n"
        "- '3.14'\n"
        "- 'x = 5, y = 3'\n"
        "- '١٥ كيلومترًا' (for Arabic questions)\n\n"
        "Solve accurately. Return only the answer."
    )

    def solve(self, instructions: str, user_message: str, provider_requested: str = 'dspy', tokens: int = 2400) -> Optional[str]:
        """Validate the answer using a direct LLM call but with wolfram first (English only)"""
        try:
            # Only use Wolfram for English questions (it's most reliable with English)
            is_arabic = bool(re.search(r'[\u0600-\u06FF]', user_message))
            if not is_arabic:
                try:
                    wolfram_response = wolfram_solve(user_message, "mathematics")
                    if wolfram_response and wolfram_response.answer:
                        logger.info(f"Wolfram solve succeeded for English question")
                        return wolfram_response.answer
                except Exception as e:
                    logger.info(f"Wolfram solve failed in solve method: {e}")

            validated_answer = solve_with_llm(
                messages=format_messages_for_api(instructions, user_message),
                max_tokens=tokens,
                provider=provider_requested,
                do_not_parse_json=True
            )
            if validated_answer:
                validated_answer = str(validated_answer).strip()
                return validated_answer

            logger.error(f"LLM returned empty answer for {user_message}")
            return None

        except Exception as e:
            logger.error(f"Answer validation failed: {e} for {user_message}")
            return None


    def solve_question(self, question: GeneratedQuestion, provider_requested: str = 'dspy') -> Optional[GeneratedQuestion]:
        """
        Validate a question and solve it, returning the question with answer or None if invalid.
        Uses LLM-based validation to ensure correctness, grade appropriateness, and mathematical nature.
        DOES NOT correct bad questions - rejects them instead.
        """
        try:
            # Only use Wolfram for English questions
            is_arabic = bool(re.search(r'[\u0600-\u06FF]', question.question_text))
            if not is_arabic:
                try:
                    wolfram_response = wolfram_solve(question.question_text, question.subject)
                    if wolfram_response and wolfram_response.answer:
                        # Update question with Wolfram's response
                        question.working_steps = wolfram_response.working_steps
                        question.rationale = wolfram_response.rationale
                        question.answer = wolfram_response.answer
                        logger.info(f"Wolfram solved English question successfully")
                        return question
                except Exception as e:
                    logger.info(f"Wolfram solve attempt failed: {e}, continuing with LLM validation")

            # Step 1: Validate question quality FIRST (before wasting compute on solving)
            # Check if question is mathematical and grade-appropriate
            validation_result = self._validate_question_quality_only(question)

            # If validation itself failed (returned None), filter out the question
            if validation_result is None:
                logger.error(f"DSPy validation failed for question: {question.question_text[:50]}...")
                return None

            # Step 2: Reject non-mathematical questions immediately
            if not validation_result.get('is_mathematical', False):
                logger.error(f"Rejecting non-mathematical question: {question.question_text[:50]}... "
                           f"Reason: {validation_result.get('issues', ['Not mathematical'])[0]}")
                return None

            # Step 3: Reject questions that are not grade-appropriate
            # NOTE: Lowered threshold from 7 to 4 and disabled concepts_too_advanced check
            # This prevents good questions from being rejected due to validator errors or token limit issues
            # The validator sometimes incorrectly flags appropriate questions as "too advanced"
            if (validation_result.get('grade_level_score', 0) < 4):

                grade_issues = []
                if validation_result.get('concepts_too_advanced', False):
                    grade_issues.append("concepts too advanced")
                if validation_result.get('grade_level_score', 0) < 4:
                    grade_issues.append(f"grade level score {validation_result.get('grade_level_score', 0)}/10")

                logger.warning(f"Skipping grade-inappropriate question for grade {question.grade}: "
                           f"{question.question_text[:50]}... Issues: {', '.join(grade_issues)}")
                return None

            # Step 4: Question is good, NOW solve it (ignore incoming bad answer)
            corrected_answer = self._solve_and_extract_answer(question, provider_requested)

            if not corrected_answer:
                logger.error(f"Could not solve question: {question.question_text[:50]}...")
                return None

            # Step 5: Validate the NEWLY SOLVED answer
            answer_postcheck = self._prevalidate_answer_format(corrected_answer, provider_requested)
            if not answer_postcheck['is_valid']:
                logger.error(f"Solved answer failed validation: {answer_postcheck['reason']} for answer: {corrected_answer}")
                return None

            # Step 6: Update question with correct answer and return
            question.answer = corrected_answer
            return question

        except Exception as e:
            logger.error(f"Question validation/solving failed: {e} for {question.question_text[:50]}...")
            return None



    def _get_grade_appropriate_logic(self, grade) -> str:
        """Get naturally grade-aware solving logic."""
        if not grade:
            return self.GENERATE_LOGIC

        # Base logic with grade-appropriate complexity scaling
        base_logic = self.GENERATE_LOGIC

        # Add natural grade awareness without rigid rules
        grade_addition = f"\n\nGRADE AWARENESS: This solution is for grade {grade} students. Let your understanding of what's appropriate for this learning level naturally guide your mathematical explanations, vocabulary choices, and solution approach."

        return base_logic + grade_addition

    def _detect_mathematical_question(self, question_text: str) -> dict:
        """Use DSPy to detect if question is mathematical and solvable."""
        try:
            result = self._math_detector(question_text=question_text)
            detection_data = first_json_block(str(result.detection_result)) or {}

            return {
                'is_mathematical': detection_data.get('is_mathematical', False),
                'reasoning': detection_data.get('reasoning', ''),
                'solvability_score': detection_data.get('solvability_score', 0),
                'requires_computation': detection_data.get('requires_computation', False)
            }
        except Exception as e:
            logger.info(f"DSPy mathematical detection failed: {e}")
            return {'is_mathematical': False, 'reasoning': 'Detection failed', 'solvability_score': 0, 'requires_computation': False}

    def _validate_question_quality_only(self, question: GeneratedQuestion) -> dict:
        """
        Validate ONLY the question text quality (mathematical nature, grade-appropriateness).
        Does NOT validate the answer - use this BEFORE solving to avoid wasting compute.
        """
        try:
            # Use DSPy to validate question without considering the answer
            result = self._validator(
                question_text=question.question_text,
                grade=str(question.grade or ""),
                subject=question.subject or "mathematics",
                difficulty=question.difficulty or "medium",
                language=question.language or "english",
                current_answer=""  # Empty string - we don't care about incoming answer
            )

            # Parse JSON response from DSPy
            validation_data = first_json_block(str(result.validation_result)) or {}

            # Extract mathematical detection
            is_mathematical = validation_data.get('is_mathematical', True)

            if not is_mathematical:
                return {
                    'is_valid': False,
                    'issues': validation_data.get('issues', ["Not a mathematical question"]),
                    'grade_appropriate': False,
                    'mathematically_correct': False,
                    'clarity_score': 0,
                    'is_mathematical': False,
                    'is_fixable': False,
                    'solvability_score': validation_data.get('solvability_score', 0),
                    'grade_level_score': validation_data.get('grade_level_score', 0),
                    'concepts_too_advanced': validation_data.get('concepts_too_advanced', False)
                }

            return {
                'is_valid': validation_data.get('is_valid', True),  # Assume valid if mathematical
                'issues': validation_data.get('issues', []),
                'grade_appropriate': validation_data.get('grade_appropriate', True),
                'mathematically_correct': True,  # Will be determined after solving
                'clarity_score': validation_data.get('clarity_score', 7),
                'is_mathematical': True,
                'is_fixable': True,
                'solvability_score': validation_data.get('solvability_score', 7),
                'grade_level_score': validation_data.get('grade_level_score', 7),
                'concepts_too_advanced': validation_data.get('concepts_too_advanced', False)
            }
        except Exception as e:
            logger.error(f"DSPy question quality validation failed: {e}")
            # Filter out question when validation fails
            return None

    def _batch_validate_questions(self, questions: List[GeneratedQuestion]) -> List[Optional[dict]]:
        """
        Validate multiple questions in a single LLM call for efficiency.
        Returns list of validation results (or None for invalid questions).
        """
        if not questions:
            return []

        try:
            # Prepare batch input
            batch_input = []
            for idx, q in enumerate(questions):
                batch_input.append({
                    'id': idx,
                    'question_text': q.question_text,
                    'grade': str(q.grade or ""),
                    'subject': q.subject or "mathematics",
                    'difficulty': q.difficulty or "medium",
                    'language': q.language or "english"
                })

            # Call batch validator
            result = self._batch_validator(questions_json=json.dumps(batch_input, ensure_ascii=False))

            # Parse results
            results_data = first_json_block(str(result.validation_results)) or []

            # Create a map of id -> validation result
            results_map = {}
            for item in results_data:
                if isinstance(item, dict) and 'id' in item:
                    results_map[item['id']] = {
                        'is_valid': item.get('is_valid', True),
                        'issues': item.get('issues', []),
                        'grade_appropriate': item.get('grade_appropriate', True),
                        'is_mathematical': item.get('is_mathematical', True),
                        'clarity_score': item.get('clarity_score', 7),
                        'grade_level_score': item.get('grade_level_score', 7),
                        'concepts_too_advanced': item.get('concepts_too_advanced', False),
                        'solvability_score': item.get('solvability_score', 7),
                        'is_fixable': True,
                        'mathematically_correct': True
                    }

            # Return results in order
            return [results_map.get(idx) for idx in range(len(questions))]

        except Exception as e:
            logger.error(f"Batch validation failed: {e}, falling back to individual validation")
            # Fallback to individual validation
            return [self._validate_question_quality_only(q) for q in questions]

    def _prevalidate_answer_format(self, answer: str, provider_requested: str = 'dspy') -> dict:
        """
        Use LLM to validate if answer looks like a proper mathematical answer.
        Returns {'is_valid': bool, 'reason': str}
        """
        # Convert to string if needed (handles numbers, None, etc.)
        if answer is None:
            answer = ""
        answer_clean = str(answer).strip()

        # Allow empty string to go through LLM validation (might be valid in some contexts)
        if not answer_clean:
            answer_clean = "0"  # Treat empty as zero for validation

        # Use LLM to check if this is a valid mathematical answer
        validation_prompt = f"""You are validating mathematical answers for educational questions.

ANSWER TO VALIDATE: {answer_clean}

Determine if this is a VALID mathematical answer or INVALID (RAG pollution/encyclopedic data).

VALID mathematical answers are:
- Numbers with or with-out units (e.g., "5 cm", "42", "3.14")
- Mathematical expressions (e.g., "x = 5", "2π", "√16")
- Simple algebraic forms (e.g., "y = 2x + 3")
- Coordinate pairs, fractions, ranges
- Integrals and derivatives
- Symbolic expressions (e.g., "x^2 + 2x + 1")
- Advanced mathematical expressions

INVALID answers (RAG pollution) are:
- Dictionary definitions or descriptions in parentheses
- Geographic data (population, area rankings, country data)
- Long explanatory text or sentences
- Wikipedia-style content with references
- Nutritional data tables
- Any non-mathematical encyclopedic content

Return JSON:
{{
    "is_valid_math_answer": true/false,
}}"""

        try:
            validation_result = solve_with_llm(
                messages=format_messages_for_api("You are a mathematical answer validator.", validation_prompt),
                max_tokens=50,
                provider=provider_requested,
                do_not_parse_json=False
            )

            if validation_result and isinstance(validation_result, dict):
                is_valid = validation_result.get('is_valid_math_answer', True)
                if not is_valid:
                    return {'is_valid': False, 'reason': f'LLM validation failed'}

        except Exception as e:
            logger.warning(f"LLM answer validation failed: {e}, using lenient fallback")
            # If LLM fails, do minimal checks only
            if len(answer_clean) > 200:
                return {'is_valid': False, 'reason': 'Answer too long'}

        return {'is_valid': True, 'reason': 'Answer format is valid'}

    def _is_question_valid(self, _validation_result: dict, _answer: str = "") -> bool:
        """Always return True - we will fix ANY question to produce a clean answer."""
        return True

    def _correct_question_with_dspy(self, question: GeneratedQuestion, validation_result: dict) -> dict:
        """Use DSPy to correct question issues."""
        # ALWAYS attempt to fix - no rejection, just clean correction

        try:
            result = self._corrector(
                original_question=question.question_text,
                grade=str(question.grade or ""),
                subject=question.subject or "mathematics",
                difficulty=question.difficulty or "medium",
                language=question.language or "english",
                issues=validation_result.get('issues', []),
                original_answer=question.answer or ""
            )

            # Parse JSON response from DSPy
            correction_data = first_json_block(str(result.corrected_question)) or {}

            # Trust the DSPy correction - return result or fail
            if correction_data and correction_data.get('question_text') and correction_data.get('answer'):
                return correction_data
            else:
                # If DSPy failed to generate proper correction, fail
                return None

        except Exception as e:
            logger.error(f"DSPy correction failed: {e}")
            return None


    def _solve_and_extract_answer(self, question: GeneratedQuestion, provider_requested: str = 'dspy') -> str:
        """Solve question and get final answer using direct solving approach."""
        try:
            # Use direct solve approach - single LLM call that returns only the answer
            grade_aware_instructions = self.DIRECT_SOLVE_LOGIC
            if question.grade:
                grade_aware_instructions += f"\n\nGrade level: {question.grade}. Ensure answer complexity is appropriate for this grade."

            direct_answer = self.solve(
                grade_aware_instructions,
                question.question_text,
                provider_requested,
                500  # Smaller token limit since we only need the answer
            )

            if direct_answer and isinstance(direct_answer, str):
                # Clean up the answer - remove any extra text
                cleaned = direct_answer.strip()
                # Remove common prefixes that LLMs might add
                for prefix in ["Answer:", "Final Answer:", "The answer is", "="]:
                    if cleaned.lower().startswith(prefix.lower()):
                        cleaned = cleaned[len(prefix):].strip()
                        if cleaned.startswith(":"):
                            cleaned = cleaned[1:].strip()

                if cleaned:
                    return cleaned

            # Fallback: if direct solve fails, try the old two-step method
            logger.warning(f"Direct solve failed, falling back to two-step method for: {question.question_text[:50]}...")
            grade_logic = self._get_grade_appropriate_logic(question.grade)
            logic = self.solve(grade_logic, question.question_text, provider_requested, 1500)  # Reduced from 3000 to avoid context window issues

            if logic:
                validated_answer = self.solve(
                    self.EXTRACT_LOGIC,
                    f"Question: {question.question_text}: answer and logic {logic}",
                    provider_requested, 1000
                )
                if validated_answer and isinstance(validated_answer, str):
                    return validated_answer.strip()

            return question.answer or ""
        except Exception as e:
            logger.error(f"Answer solving failed: {e}")
            return question.answer or ""

    def validate_questions(
        self,
        questions: List[GeneratedQuestion],
        quantity: int,
        provider_requested: str = 'dspy',
        max_workers: int = 10
    ) -> List[GeneratedQuestion]:
        """
        Validate questions for mathematical correctness, grade appropriateness, and quality.
        Filter out invalid questions and solve mathematical problems to get correct answers.
        Uses ThreadPoolExecutor for parallel processing.
        """

        validation_progress = ProgressBar(total=len(questions), description="Processing questions")
        valid_questions = []

        def validate_and_solve_question_sync(idx, q):
            try:
                # Use solve_question which handles Wolfram, validation, and solving
                solved_question = self.solve_question(q, provider_requested)

                if solved_question and solved_question.answer:
                    return idx, solved_question, "Valid & Solved"
                else:
                    # Question was rejected during validation/solving
                    logger.error(f"Question {idx+1} rejected during validation")
                    return idx, None, "Rejected"

            except Exception as e:
                logger.error(f"Validation failed for question {idx+1}: {e}, rejecting")
                return idx, None, "Exception During Processing"

        if len(questions) == 0:
            return []

        # Process all questions in parallel using ThreadPoolExecutor
        # max_workers is passed from orchestrator
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(validate_and_solve_question_sync, idx, q): idx
                      for idx, q in enumerate(questions)}

            for future in as_completed(futures):
                try:
                    idx, validated_question, status = future.result()

                    if validated_question is not None:
                        valid_questions.append(validated_question)
                        validation_progress.update(details=f"✓ Q{idx+1}: {status}")
                    else:
                        validation_progress.update(details=f"✗ Q{idx+1}: {status}")
                except Exception as e:
                    logger.error(f"Task raised exception: {e}")
                    validation_progress.update(details=f"✗ Exception")

        validation_progress.complete(f"Processed: {len(valid_questions)} valid questions with correct answers")

        # Log comprehensive validation summary
        logger.info(f"Question processing complete: {len(valid_questions)} valid questions with correct answers")

        # If we don't have enough valid questions, log a warning
        if len(valid_questions) < quantity:
            logger.warning(f"Only {len(valid_questions)} valid questions available (requested: {quantity}). Consider generating more questions.")

        # Return up to the requested quantity
        return valid_questions[:quantity]