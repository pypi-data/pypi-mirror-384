#!/usr/bin/env python3
"""
Module 2: Simplified DSPy-Powered Question Generator
Converts RetrievedSample objects directly into GeneratedQuestion objects with variety.
Subject-agnostic, grade-aware, and focused on question diversity.
"""

import json
import hashlib
import logging
import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import dspy
from src.question_gen_v1.module_1 import RetrievedSample
from src.utils.json_repair import parse_json
from src.utils.progress_bar import ProgressBar

logger = logging.getLogger(__name__)


# DSPy Signature for converting samples to multiple questions in batch
class SampleToMultipleQuestionsConverter(dspy.Signature):
    """Convert educational sample into multiple mathematically accurate, well-structured questions.

    MATHEMATICAL ACCURACY:
    - Verify all calculations and expressions are correct
    - Ensure proper mathematical notation and terminology
    - Check that questions have clear, unambiguous solutions
    - Use grade-appropriate mathematical concepts and vocabulary

    QUESTION TYPES:
    - MCQ: Standard multiple choice questions with options
    - Fill-in: Questions with blanks (___) for students to complete

    QUESTION QUALITY:
    - Create clear, specific question text without ambiguity
    - For fill-in questions: Place blanks strategically where answers belong
    - Provide comprehensive working steps for complex problems
    - Include educational rationale explaining learning objectives
    - Generate diverse question types (calculation, explanation, application)

    BATCH GENERATION:
    - Generate exactly the requested number of questions
    - Ensure variety across generated questions (different angles, contexts, formats)
    - Maintain consistency in difficulty and grade appropriateness
    """

    sample_text = dspy.InputField(desc="Original educational sample content")
    subject = dspy.InputField(desc="Subject area (mathematics, science, etc.)")
    grade = dspy.InputField(desc="Target grade level (1-12)")
    difficulty = dspy.InputField(desc="Difficulty level (easy, medium, hard)")
    language = dspy.InputField(desc="Target language for the question")
    question_type = dspy.InputField(desc="Question type: 'mcq' for multiple choice or 'fill-in' for fill-in-the-blank")
    count = dspy.InputField(desc="Number of questions to generate from this sample")
    existing_questions = dspy.InputField(desc="List of existing questions to ensure variety")

    generated_questions = dspy.OutputField(desc="""JSON array of question objects, each with:
    - question_text: Precise, clear question with proper mathematical language. For 'fill-in' type: include blanks (___) where students fill answers. For 'mcq' type: standard question format.
    - topic: Specific skill area (e.g., "Order of Operations", "Pythagorean Theorem")
    - parameter_values: Dict of mathematical values/expressions used
    - working_steps: Detailed solution steps with explanations
    - rationale: Educational purpose and learning objectives addressed
    - constraints: Mathematical constraints or requirements
    - variety_score: 0.0-1.0 indicating uniqueness from existing questions""")


class QuestionVarietyEnhancer(dspy.Signature):
    """Enhance question variety by modifying format, context, or approach while maintaining educational value.

    INSTRUCTIONAL CLARITY:
    - Use precise, unambiguous language appropriate for the grade level
    - Ensure questions have single, clear correct answers
    - Provide sufficient context without unnecessary complexity
    - Maintain consistent terminology throughout

    FORMAT DIVERSITY:
    - Create varied presentations: word problems, direct calculations, real-world scenarios
    - Ensure different question types test same learning objective
    - Avoid repetitive phrasing or structure patterns
    - Generate contextually appropriate examples and scenarios

    EDUCATIONAL VALUE:
    - Preserve core learning objectives while varying presentation
    - Include practical applications when appropriate
    - Ensure mathematical concepts are properly represented
    - Create meaningful distractors that reveal common misconceptions
    """

    base_question = dspy.InputField(desc="Original question text")
    subject = dspy.InputField(desc="Subject area")
    grade = dspy.InputField(desc="Grade level")
    existing_formats = dspy.InputField(desc="List of question formats already used")

    enhanced_question = dspy.OutputField(desc="""JSON object with:
    - question_text: Enhanced question with clear, unambiguous language
    - format_type: Type of format used (word_problem, direct_calculation, scenario_based, etc.)
    - enhancement_rationale: Specific educational benefit this format provides
    - clarity_improvements: How this version improves question clarity""")


@dataclass
class GeneratedQuestion:
    """Generated question data structure."""
    question_id: str
    pattern_id: str
    subject: str
    topic: str
    grade: Optional[int]
    difficulty: str
    language: str
    question_text: str
    parameter_values: Dict[str, Any]
    answer: str
    working_steps: List[str] = field(default_factory=list)
    rationale: str = ""
    constraints: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Module2QuestionGenerator:
    """Simplified Module 2: Direct sample-to-question conversion using DSPy."""

    def __init__(self):
        self.batch_converter = dspy.ChainOfThought(SampleToMultipleQuestionsConverter)
        self.variety_enhancer = dspy.ChainOfThought(QuestionVarietyEnhancer)
        logger.info("Module2QuestionGenerator initialized with DSPy components")

    def generate_questions_from_samples(
        self,
        samples: List[RetrievedSample],
        quantity: int,
        subject: str,
        grade: int,
        difficulty: str = "medium",
        language: str = "english",
        question_type: str = "mcq",
        max_workers: int = 10
    ) -> List[GeneratedQuestion]:
        """
        Convert samples directly into GeneratedQuestion objects with variety.

        Args:
            samples: Retrieved educational samples
            quantity: Number of questions to generate
            subject: Subject area
            grade: Target grade level
            difficulty: Difficulty level
            language: Target language

        Returns:
            List of GeneratedQuestion objects
        """
        if not samples:
            logger.warning("No samples provided to generate questions")
            return []

        logger.info(f"Generating {quantity} questions from {len(samples)} samples")

        # Use progress bar for tracking
        progress = ProgressBar(total=quantity, description="Generating questions")

        # Calculate distribution of questions per sample
        questions_per_batch = max(1, quantity // max(1, len(samples)))

        # Prepare all tasks upfront for maximum parallelization
        tasks = []
        remaining = quantity
        for i, sample in enumerate(samples):
            if remaining <= 0:
                break

            batch_size = min(questions_per_batch, remaining)
            if i == len(samples) - 1:
                batch_size = remaining

            tasks.append((sample, batch_size, subject, grade, difficulty, language, question_type))
            remaining -= batch_size

        # Execute all tasks in parallel with maximum worker count
        # max_workers is passed from orchestrator
        generated_questions = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                executor.submit(
                    self._generate_questions_from_single_sample,
                    sample, count, subj, gr, diff, lang, [], q_type
                )
                for sample, count, subj, gr, diff, lang, q_type in tasks
            ]

            # Collect results as they complete with per-future timeout
            for future in as_completed(futures, timeout=300):  # 5 min total timeout
                try:
                    batch_questions = future.result(timeout=120)  # 2 minute timeout per sample
                    generated_questions.extend(batch_questions)
                    progress.update(len(batch_questions),
                                  details=f"Generated {len(generated_questions)}/{quantity}")
                except TimeoutError:
                    logger.error(f"Question generation timeout after 2 minutes")
                    progress.update(0, details="Timeout")
                except Exception as e:
                    logger.error(f"Question generation failed: {e}")
                    progress.update(0, details="Failed")

        # Handle additional questions in parallel if needed
        shortage = quantity - len(generated_questions)
        if shortage > 0:
            logger.info(f"Need {shortage} more questions, generating in parallel")
            additional = self._generate_additional_questions_parallel(
                samples, shortage, subject, grade, difficulty, language, generated_questions, max_workers
            )
            generated_questions.extend(additional)
            progress.update(len(additional), details=f"Added {len(additional)} additional")

        progress.complete(f"Generated {len(generated_questions)} questions")
        logger.info(f"Module 2 complete: Generated {len(generated_questions)} questions")
        return generated_questions[:quantity]

    def _generate_questions_from_single_sample(
        self,
        sample: RetrievedSample,
        count: int,
        subject: str,
        grade: int,
        difficulty: str,
        language: str,
        existing_questions: List[str],
        question_type: str = "mcq"
    ) -> List[GeneratedQuestion]:
        """Generate multiple questions from a single sample in one batch."""
        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                # Generate all questions in a single batch call
                result = self.batch_converter(
                    sample_text=sample.question_text,
                    subject=subject,
                    grade=str(grade),
                    difficulty=difficulty,
                    language=language,
                    question_type=question_type,
                    count=str(count),
                    existing_questions=str(existing_questions)
                )

                # Parse batch response
                questions_data = parse_json(result.generated_questions)
                if not questions_data or not isinstance(questions_data, list):
                    continue

                # Convert to GeneratedQuestion objects
                questions = []
                for i, q_data in enumerate(questions_data[:count]):
                    try:
                        question = GeneratedQuestion(
                            question_id=str(uuid.uuid4()),
                            pattern_id=self._generate_pattern_id(sample.question_text + str(i)),
                            subject=subject,
                            topic=q_data.get("topic", "General"),
                            grade=grade,
                            difficulty=difficulty,
                            language=language,
                            question_text=q_data.get("question_text", ""),
                            parameter_values=q_data.get("parameter_values", {}),
                            answer="",  # Will be filled by Module 3
                            working_steps=q_data.get("working_steps", []),
                            rationale=q_data.get("rationale", ""),
                            constraints=q_data.get("constraints", []),
                            metadata={
                                "source_sample": sample.question_text,
                                "variety_score": q_data.get("variety_score", 0.5),
                                "generation_method": "dspy_batch",
                                "generation_attempts": attempt + 1,
                                "original_source": getattr(sample, 'source', 'unknown'),
                                "batch_index": i
                            }
                        )
                        questions.append(question)
                    except Exception as e:
                        logger.debug(f"Failed to parse question {i} in batch: {e}")
                        continue

                if questions:
                    return questions

            except Exception as e:
                logger.debug(f"Batch generation attempt {attempt + 1} failed: {e}")
                continue

        return []

    def _generate_additional_questions_parallel(
        self,
        samples: List[RetrievedSample],
        needed: int,
        subject: str,
        grade: int,
        difficulty: str,
        language: str,
        existing_questions: List[GeneratedQuestion],
        max_workers: int = 10
    ) -> List[GeneratedQuestion]:
        """Generate additional questions in parallel when we don't have enough."""
        # Cycle through samples to generate more questions
        sample_cycle = samples * ((needed // len(samples)) + 1)
        existing_formats = [q.metadata.get("format_type", "standard") for q in existing_questions]

        # Generate all tasks in parallel with maximum workers
        # max_workers is passed from caller
        additional_questions = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in range(needed):
                if i < len(sample_cycle):
                    sample = sample_cycle[i]
                    future = executor.submit(
                        self._generate_single_enhanced_question,
                        sample, i, subject, grade, difficulty, language, existing_formats
                    )
                    futures.append(future)

            # Collect results
            for future in as_completed(futures):
                try:
                    question = future.result(timeout=180)  # 3 minute timeout per question
                    if question:
                        additional_questions.append(question)
                except TimeoutError:
                    logger.error(f"Additional question generation timeout after 3 minutes")
                except Exception as e:
                    logger.warning(f"Failed to generate additional question: {e}")

        logger.info(f"Generated {len(additional_questions)} additional questions in parallel")
        return additional_questions

    def _generate_single_enhanced_question(
        self,
        sample: RetrievedSample,
        index: int,
        subject: str,
        grade: int,
        difficulty: str,
        language: str,
        existing_formats: List[str]
    ) -> Optional[GeneratedQuestion]:
        """Generate a single enhanced question."""
        try:
            base_question = sample.question_text
            enhanced_result = self.variety_enhancer(
                base_question=base_question,
                subject=subject,
                grade=str(grade),
                existing_formats=str(existing_formats)
            )

            enhanced_data = parse_json(enhanced_result.enhanced_question) or {}

            return GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                pattern_id=self._generate_pattern_id(sample.question_text + str(index)),
                subject=subject,
                topic=getattr(sample, 'topic', 'General'),
                grade=grade,
                difficulty=difficulty,
                language=language,
                question_text=enhanced_data.get("question_text", base_question),
                parameter_values={},
                answer="",
                working_steps=[],
                rationale=enhanced_data.get("enhancement_rationale", ""),
                constraints=[],
                metadata={
                    "source_sample": sample.question_text,
                    "generation_method": "dspy_variety_enhanced",
                    "format_type": enhanced_data.get("format_type", "enhanced"),
                    "clarity_improvements": enhanced_data.get("clarity_improvements", ""),
                    "additional_generation": True
                }
            )
        except Exception as e:
            logger.warning(f"Failed to enhance question: {e}")
            return None

    def _generate_pattern_id(self, text: str) -> str:
        """Generate a pattern ID from text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]

# Factory function for compatibility
def get_extractor(_subject: Optional[str] = None, **_kwargs) -> Module2QuestionGenerator:
    """Factory function to create a question generator (compatibility with old interface)."""
    return Module2QuestionGenerator()


# Legacy compatibility - return empty patterns list since we now generate questions directly
@dataclass
class ExtractedPattern:
    """Legacy compatibility class."""
    template: str = ""
    parameter_ranges: Dict[str, Any] = field(default_factory=dict)
    mathematical_formula: str = ""
    constraints: List[str] = field(default_factory=list)
    subject: str = ""
    grade: Optional[int] = None
    difficulty: str = ""
    pattern_id: str = ""
    source_samples: int = 0
    topic: str = ""
    language: str = ""
    learning_objectives: List[str] = field(default_factory=list)
    prerequisite_skills: List[str] = field(default_factory=list)
    solution_steps: List[str] = field(default_factory=list)
    common_errors: List[str] = field(default_factory=list)
    cross_curricular_links: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    rag_confidence: Optional[float] = None
    rag_mode_used: str = ""
    rag_metadata: Dict[str, Any] = field(default_factory=dict)