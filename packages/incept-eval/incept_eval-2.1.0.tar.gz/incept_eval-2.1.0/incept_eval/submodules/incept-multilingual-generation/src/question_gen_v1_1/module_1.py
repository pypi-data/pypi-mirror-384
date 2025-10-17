#!/usr/bin/env python3
"""
Module 1: PostgreSQL-based Question Retrieval (V1.1)
Subject/grade agnostic. Retrieves samples from Supabase PostgreSQL.

Features:
- Direct match on skills/standards
- Vector similarity search (parallel)
- Quality filtering (textbook >=6.0, athena: no filter)
- LLM-based curation for relevance filtering
- DI content extraction (prefer DB, fallback to RAG)
"""

import os
import logging
import time
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

# PostgreSQL retriever
from src.question_gen_v1_1.psql_retriever import PSQLQuestionRetriever, RetrievedSample

# DI format for enrichment
from src.direct_instruction.di_formats import DiFormat

# LLM imports for curation
from src.llms import produce_structured_response
from src.utils.json_repair import to_dict
from src.utils.error_logger import get_error_logger

os.environ["TOKENIZERS_PARALLELISM"] = "false"

error_logger = get_error_logger()
logger = logging.getLogger(__name__)


# ---------------------------------
# Module 1 PostgreSQL Retriever (V1.1)
# ---------------------------------
class Module1RAGRetriever:
    """
    Module 1 V1.1: PostgreSQL-based question retrieval.

    Features:
    - Direct match on skills/standards (exact filtering)
    - Vector similarity search (parallel)
    - Quality filtering (textbook >=6.0, athena: no filter)
    - DI content extraction (prefer DB, fallback to RAG)
    """

    def __init__(self, enable_compilation: bool = False, accuracy_mode: bool = False):
        """
        Initialize Module 1 PostgreSQL Retriever.

        Args:
            enable_compilation: Ignored (kept for compatibility)
            accuracy_mode: Ignored (kept for compatibility)
        """
        self.psql_retriever = PSQLQuestionRetriever()
        self.di_format = DiFormat()
        logger.info("✓ Module 1 V1.1 initialized with PostgreSQL retrieval")

    # --------------------------------------
    # Public: get N retrieved samples
    # --------------------------------------
    def retrieve_samples(
        self,
        grade: int,
        subject: str,
        limit: int = 10,
        skill_id: Optional[str] = None,
        skill_title: Optional[str] = None,
        unit_name: Optional[str] = None,
        lesson_title: Optional[str] = None,
        substandard_description: Optional[str] = None,
        instructions: Optional[str] = None,
        language: str = "arabic",
        provider: str = "openai",
        exclude_question_texts: Optional[set] = None,
    ) -> List[RetrievedSample]:
        """
        Return up to `limit` retrieved samples using PostgreSQL hybrid retrieval.

        Strategy:
        1. Direct match on skills/standards (exact filtering)
        2. Vector similarity search (parallel)
        3. Quality filtering (textbook >=6.0, athena: no filter)
        4. LLM-based curation for relevance filtering
        5. DI content extraction (prefer DB, fallback to RAG)

        Args:
            grade: Target grade level
            subject: Subject area
            limit: Maximum samples to return (default: 10)
            skill_id: Skill/substandard ID for exact matching (e.g., CCSS.MATH.CONTENT.3.OA.A.2+2)
            skill_title: Skill title for filtering (e.g., "Rounding")
            unit_name: Unit name for context (e.g., "Place Value and Rounding")
            lesson_title: Lesson title for context (e.g., "Round to the nearest 10 or 100.")
            substandard_description: Substandard description for specific matching
            instructions: User instructions for relevance checking
            language: Target language
            provider: LLM provider for curation (e.g., "openai", "gpt-4o", "dspy")
            exclude_question_texts: Set of question texts to exclude

        Returns:
            List of RetrievedSample objects with DI content
        """
        logger.info(f"📚 Module 1 V1.1: Retrieving {limit} samples (grade={grade}, subject={subject})")

        # Track timing for each step
        timing: Dict[str, float] = {}

        try:
            # Step 1: Retrieval
            retrieval_start = time.time()
            samples = self.psql_retriever.retrieve_samples(
                grade=grade,
                subject=subject,
                limit=limit,
                skill_id=skill_id,
                skill_title=skill_title,
                unit_name=unit_name,
                lesson_title=lesson_title,
                substandard_description=substandard_description,
                language=language,
                exclude_question_texts=exclude_question_texts or set()
            )
            timing['retrieval'] = time.time() - retrieval_start

            logger.info(f"✓ Retrieved {len(samples)} samples from PostgreSQL ({timing['retrieval']:.2f}s)")

            # Log retrieved questions (BEFORE curation)
            logger.info("=" * 80)
            logger.info(f"📋 MODULE 1: RETRIEVED QUESTIONS BEFORE CURATION ({len(samples)} total)")
            logger.info("=" * 80)
            for i, sample in enumerate(samples, 1):
                question_text = sample.question_text or "N/A"
                logger.info(f"[{i}] Question: {question_text[:100]}...")
                logger.info(f"    Topic: {sample.topic or 'N/A'}")
                logger.info(f"    Source: {sample.source}")
                logger.info("")
            logger.info("=" * 80)

            # Build query and skill_focus for curation (matching V1 pattern)
            query_parts = [f"grade {grade} {subject}"]
            if substandard_description:
                query_parts.append(substandard_description)
            elif lesson_title:
                query_parts.append(lesson_title)
            elif skill_title:
                query_parts.append(skill_title)
            query = " - ".join(query_parts)

            skill_focus = (
                (substandard_description or "").strip()
                or (lesson_title or "").strip()
                or (skill_title or "").strip()
                or (unit_name or "").strip()
                or subject
            )

            # Step 2: Curation
            curation_start = time.time()
            curated_samples = self.evaluate_and_update_samples(
                samples=samples,
                grade=grade,
                subject=subject,
                query=query,
                skill_focus=skill_focus,
                instructions=instructions,
                provider=provider,
                limit=limit,
                language=language
            )
            timing['curation'] = time.time() - curation_start

            logger.info(f"✓ Curation: {len(samples)} → {len(curated_samples)} samples (filtered out {len(samples) - len(curated_samples)}) ({timing['curation']:.2f}s)")

            # Step 3: DI Enrichment
            di_start = time.time()
            if curated_samples:
                curated_samples = self._enrich_samples_with_di(curated_samples, grade, subject)
            timing['di_enrichment'] = time.time() - di_start

            # Log curated questions (AFTER curation)
            logger.info("=" * 80)
            logger.info(f"📋 MODULE 1: CURATED QUESTIONS AFTER FILTERING ({len(curated_samples)} total)")
            logger.info("=" * 80)
            for i, sample in enumerate(curated_samples, 1):
                question_text = sample.question_text or "N/A"
                logger.info(f"[{i}] Question: {question_text[:100]}...")
                logger.info(f"    Topic: {sample.topic or 'N/A'}")
                logger.info(f"    Source: {sample.source}")
                logger.info("")
            logger.info("=" * 80)

            # Log timing summary
            total_time = sum(timing.values())
            logger.info("⏱️  MODULE 1 TIMING:")
            logger.info(f"   Retrieval: {timing.get('retrieval', 0):.2f}s")
            logger.info(f"   Curation: {timing.get('curation', 0):.2f}s")
            logger.info(f"   DI Enrichment: {timing.get('di_enrichment', 0):.2f}s")
            logger.info(f"   Total: {total_time:.2f}s")

            return curated_samples

        except Exception as e:
            logger.error(f"✗ PostgreSQL retrieval failed: {e}")
            return []

    def _generate_synthetic_samples(
        self,
        grade: int,
        subject: str,
        skill_focus: str,
        query: str,
        instructions: Optional[str],
        provider: str,
        limit: int,
        language: str
    ) -> List[RetrievedSample]:
        """
        Generate synthetic sample questions when curation filters out all retrieved samples.

        Uses the same LLM provider from the request to generate diverse, relevant examples
        that can be used by Module 2 for question generation.
        """
        try:
            logger.info(f"🎨 SYNTHETIC GENERATION START: Creating {limit} samples with GPT-4o")

            class SyntheticQuestion(BaseModel):
                question_text: str
                answer: str
                difficulty: str
                explanation: str

            class SyntheticSamplesResponse(BaseModel):
                questions: List[SyntheticQuestion]

            # Build generation prompt
            generation_prompt = f"""Generate {limit} diverse sample questions for grade {grade} {subject}.

Target Skill: {skill_focus}
Context: {query}"""

            if instructions:
                generation_prompt += f"""
User Instructions: {instructions}"""

            generation_prompt += f"""

Generate {limit} DIVERSE sample questions that:
1. Cover the target skill from different angles
2. Include a variety of difficulty levels (easy, medium, hard)
3. Show different ways to test the same concept
4. Are age-appropriate for grade {grade}
5. Include clear, concise answers

For each question, provide:
- question_text: The full question text
- answer: The correct answer
- difficulty: easy, medium, or hard
- explanation: Brief explanation of the solution

Make the questions DIFFERENT from each other to provide maximum variety."""

            messages = [
                {"role": "system", "content": "You are an expert educational content creator specializing in creating diverse, high-quality sample questions."},
                {"role": "user", "content": generation_prompt}
            ]

            response = produce_structured_response(
                messages=messages,
                structure_model=SyntheticSamplesResponse,
                provider="openai",  # Always use GPT-4o for synthetic generation
                max_output_tokens=3000
            )

            response = to_dict(response)

            # Convert to RetrievedSample objects
            synthetic_samples = []
            for i, q in enumerate(response["questions"][:limit]):
                sample = RetrievedSample(
                    question_text=q["question_text"],
                    subject_area=subject,
                    grade=grade,
                    topic=skill_focus,
                    difficulty=q.get("difficulty", "medium"),
                    language=language,
                    answer=q["answer"],
                    explanation=q.get("explanation", ""),
                    source="synthetic_generation",
                    di_content=None  # No DI content for synthetic samples
                )
                synthetic_samples.append(sample)

            logger.info("=" * 80)
            logger.info(f"🎨 SYNTHETIC SAMPLES GENERATED ({len(synthetic_samples)} total)")
            logger.info("=" * 80)
            for i, sample in enumerate(synthetic_samples, 1):
                logger.info(f"[{i}] Question: {sample.question_text[:100]}...")
                logger.info(f"    Answer: {sample.answer}")
                logger.info(f"    Difficulty: {sample.difficulty}")
                logger.info("")
            logger.info("=" * 80)

            return synthetic_samples

        except Exception as e:
            logger.error(f"❌ Synthetic generation failed: {e}")
            raise

    def _enrich_samples_with_di(
        self,
        samples: List[RetrievedSample],
        grade: int,
        subject: str
    ) -> List[RetrievedSample]:
        """
        Enrich curated samples with DI content.

        This is called AFTER curation to only enrich samples that will be used for generation.

        Strategy:
        1. If direct_instruction_raw exists in DB → use it
        2. Otherwise → fallback to RAG-based DI retrieval

        Args:
            samples: List of curated samples to enrich
            grade: Target grade level
            subject: Subject area

        Returns:
            List of enriched samples
        """
        logger.info(f"📚 Enriching {len(samples)} curated samples with DI content...")

        for idx, sample in enumerate(samples, 1):
            logger.info(f"   [{idx}/{len(samples)}] Enriching: {sample.question_text[:80]}...")

            # Check if DI content already exists in DB
            if sample.direct_instruction_raw and sample.direct_instruction_raw.strip():
                sample.di_content = sample.direct_instruction_raw
                logger.info(f"       ✓ DI: Using from database ({len(sample.direct_instruction_raw)} chars)")
            else:
                # Fallback: Use RAG-based DI retrieval
                try:
                    logger.info(f"       → DI: Fetching via RAG...")
                    di_insights = self.di_format.get_di_insights_for_scaffolding_rag(
                        question_text=sample.question_text,
                        subject=subject,
                        grade=grade
                    )

                    if di_insights and di_insights.insights_text:
                        sample.di_content = di_insights.insights_text
                        logger.info(f"       ✓ DI: Fetched via RAG ({len(di_insights.insights_text)} chars)")
                    else:
                        logger.info(f"       ✗ DI: No relevant content found via RAG")

                except Exception as e:
                    logger.warning(f"       ✗ DI: RAG fetch failed: {e}")

        logger.info(f"✓ DI enrichment complete: {sum(1 for s in samples if s.di_content)}/{len(samples)} samples with DI")
        return samples

    def evaluate_and_update_samples(
        self,
        samples: List[RetrievedSample],
        grade: int,
        subject: str,
        query: str,
        skill_focus: str,
        instructions: Optional[str],
        provider: str,
        limit: int,
        language: str
    ) -> List[RetrievedSample]:
        """
        LLM-based curation: evaluate and filter samples for relevance.
        Ported from V1 module_1.py lines 306-339.
        Enhanced to include user instructions for relevance checking.
        """
        passed_samples = []
        try:
            class EvaluatedSampleLightweight(BaseModel):
                index: int
                is_appropriate: bool
                relevance_score: float  # 0.0-1.0 score for relevance to instructions/topic
                reason: str

            class EvaluationResponse(BaseModel):
                samples: List[EvaluatedSampleLightweight]

            # Build system prompt with instructions
            system_prompt = f"""You are an expert educational question validator evaluator for grade {grade} and subject {subject}.

Target Skill: {skill_focus.replace('"', '')}
Query Context: {query.replace('"', '')}"""

            if instructions:
                system_prompt += f"""\nUser Instructions: {instructions.replace('"', '')}"""

            system_prompt += """

EVALUATION CRITERIA:
Evaluate each sample based on whether it can serve as a useful example for generating similar questions about the target skill.

For EACH sample, provide:
1. is_appropriate (boolean): TRUE if relevant, FALSE if not
2. relevance_score (float 0.0-1.0): Quantitative score for how well the question matches the instructions/topic
3. reason (string): Brief explanation of your judgment

RELEVANCE SCORING (0.0-1.0):
- 1.0 = Perfect match - directly addresses the exact skill/topic
- 0.8-0.9 = Strong match - clearly relevant to the concept, minor differences in approach/phrasing
- 0.6-0.7 = Good match - addresses the same general concept, could be useful as inspiration
- 0.4-0.5 = Weak match - tangentially related, may require significant adaptation
- 0.2-0.3 = Poor match - different concept but same subject area
- 0.0-0.1 = No match - completely irrelevant or different subject

Mark is_appropriate as TRUE if relevance_score >= 0.5 (useful as inspiration)
Mark is_appropriate as FALSE if relevance_score < 0.5 (too different to be useful)

AUTOMATIC REJECTION CRITERIA (set is_appropriate=FALSE and relevance_score=0.0):
ONLY reject if the answer requires selecting between multiple visual options/images:
- Answer options are images or diagrams (e.g., "A) [diagram X] B) [diagram Y]")
- Answer is a label referencing a visual (e.g., "Figure A", "Model B", "Image 2", "Diagram C")
- Question explicitly asks to "select the figure/image/model/diagram that..." where the choices are visual

ACCEPTABLE (DO NOT REJECT):
- Questions that reference an image/figure/diagram in the question stem, as long as the answer is text, numeric, or a standard MCQ with text options
- Examples: "What is the perimeter of the polygon shown?", "How many vertices does the shape have?", "What type of angle is displayed?"
- Questions about visual content are FINE as long as answers are not visual selections
- Questions may reference images without including dimensions in text - the visual provides this information

SCORING FACTORS:
- Alignment with user instructions (if provided): 50%
- Match to target skill/topic: 50%

IMPORTANT NOTES:
1. Do NOT be overly literal - a question can be highly relevant (0.8+) even if it doesn't use the exact wording from the skill description
2. Consider the mathematical concept, not just the surface-level phrasing
3. Ignore the language of the question text - questions in any language (English, Arabic, etc.) can score high if they match the concept
4. Questions that reference "the figure", "the image", "shown", etc. are ACCEPTABLE unless the answer options are visual selections
5. Do NOT reject questions for "lacking dimensions" or "not providing context" - questions with accompanying images are valid

Focus on conceptual relevance, not exact wording. Only reject if answer options are images/visual labels."""

            # Create lightweight samples with only fields needed for curation
            # (exclude large di_content field to avoid context window issues)
            lightweight_samples = []
            for i, sample in enumerate(samples):
                lightweight_samples.append({
                    "index": i,
                    "question_text": sample.question_text,
                    "topic": sample.topic,
                    "answer": sample.answer,
                    "source": sample.source
                })

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Samples: {lightweight_samples}"}
            ]

            logger.info(f"🔍 CURATION START: Evaluating {len(samples)} samples with GPT-4o")

            response = produce_structured_response(
                messages=messages,
                structure_model=EvaluationResponse,
                provider="openai",  # Always use GPT-4o for curation
                max_output_tokens=2048
            )

            response = to_dict(response)

            logger.info("=" * 80)
            logger.info(f"📊 CURATION RESULTS ({len(response['samples'])} samples evaluated)")
            logger.info("=" * 80)

            for sample_eval in response["samples"]:
                idx = sample_eval['index']
                original_sample = samples[idx]
                question_text = original_sample.question_text or 'N/A'
                is_appropriate = sample_eval['is_appropriate']
                relevance_score = sample_eval.get('relevance_score', 0.0)
                reason = sample_eval.get('reason', 'No reason provided')

                # Store relevance score in sample
                original_sample.relevance_score = relevance_score

                status = "✅ PASS" if is_appropriate else "❌ FAIL"
                logger.info(f"[{idx + 1}] {status} (relevance: {relevance_score:.2f})")
                logger.info(f"    Question: {question_text[:150]}...")
                logger.info(f"    Reason: {reason}")
                logger.info("")

                if is_appropriate:
                    passed_samples.append(original_sample)
                else:
                    # Log curation rejection
                    error_logger.log_module_4_curation_failure(
                        question_id=str(idx),
                        question_text=question_text,
                        substandard_id=skill_focus,
                        rejection_reason=reason,
                        llm_response=sample_eval,
                        curation_request={
                            "grade": grade,
                            "subject": subject,
                            "query": query,
                            "skill_focus": skill_focus,
                            "instructions": instructions,
                            "relevance_score": relevance_score
                        }
                    )

            # Calculate relevance score statistics
            if passed_samples:
                relevance_scores = [s.relevance_score for s in passed_samples if s.relevance_score is not None]
                if relevance_scores:
                    avg_score = sum(relevance_scores) / len(relevance_scores)
                    min_score = min(relevance_scores)
                    max_score = max(relevance_scores)
                    logger.info(f"✓ CURATION COMPLETE: {len(passed_samples)}/{len(samples)} samples passed")
                    logger.info(f"   Relevance scores - Avg: {avg_score:.2f}, Min: {min_score:.2f}, Max: {max_score:.2f}")
                else:
                    logger.info(f"✓ CURATION COMPLETE: {len(passed_samples)}/{len(samples)} samples passed")
            else:
                logger.info(f"✓ CURATION COMPLETE: {len(passed_samples)}/{len(samples)} samples passed")
            logger.info("=" * 80)

            # Fallback: generate synthetic samples if curation filtered everything
            if not passed_samples and samples:
                logger.warning(f"⚠️  CURATION FALLBACK: All samples filtered out, generating {limit} synthetic samples")
                synthetic_samples = self._generate_synthetic_samples(
                    grade=grade,
                    subject=subject,
                    skill_focus=skill_focus,
                    query=query,
                    instructions=instructions,
                    provider=provider,
                    limit=limit,
                    language=language
                )
                return synthetic_samples

            return passed_samples

        except Exception as e:
            logger.warning(f"⚠️  Curation failed: {e}, generating synthetic samples as fallback")
            # Generate synthetic samples on exception
            try:
                synthetic_samples = self._generate_synthetic_samples(
                    grade=grade,
                    subject=subject,
                    skill_focus=skill_focus,
                    query=query,
                    instructions=instructions,
                    provider=provider,
                    limit=limit,
                    language=language
                )
                return synthetic_samples
            except Exception as gen_error:
                logger.error(f"❌ Synthetic generation also failed: {gen_error}, returning no samples")
                return []
