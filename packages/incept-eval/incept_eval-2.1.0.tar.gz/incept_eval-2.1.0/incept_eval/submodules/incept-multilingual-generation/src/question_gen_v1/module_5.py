#!/usr/bin/env python3
"""
Module 5: Step-by-Step Solution with Scaffolding (Optional)
Generates detailed explanations and gradual hints for problem solving.
Uses LLM to handle any question - nothing hardcoded.
Can be used standalone or as part of the pipeline.
"""

from typing import Dict, Any, List
import json
import time
import logging
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from src.llms import format_messages_for_api, solve_with_llm, produce_structured_response
from src.question_gen_v1.module_4 import MultipleChoiceQuestion
from typing import Any, Dict, List, Optional
from src.utils.module_5 import DetailedExplanation, VoiceoverScript, ScaffoldingResponse, BatchScaffoldingResponse, ScaffoldedSolution
from src.utils.json_repair import _safe_get, model_to_json, parse_json, to_dict
from src.utils.progress_bar import ProgressBar
from src.direct_instruction.di_formats import DiFormat
from src.direct_instruction.principles_constants import GRADE_VOCABULARY_EXAMPLES_EN, GRADE_VOCABULARY_EXAMPLES_AR
from src.utils.translate import execute_translate

logger = logging.getLogger(__name__)

# Custom thread pool for Module 5 parallel scaffolding
# Will be initialized with Config.MAX_WORKERS on first use
_SCAFFOLDING_THREAD_POOL = None

def _get_scaffolding_thread_pool(max_workers: int):
    """Get or create the scaffolding thread pool with specified max_workers."""
    global _SCAFFOLDING_THREAD_POOL

    # Recreate pool if max_workers changed
    if _SCAFFOLDING_THREAD_POOL is None or getattr(_SCAFFOLDING_THREAD_POOL, '_max_workers', None) != max_workers:
        if _SCAFFOLDING_THREAD_POOL is not None:
            _SCAFFOLDING_THREAD_POOL.shutdown(wait=False)
        _SCAFFOLDING_THREAD_POOL = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="Module5-Scaffolding")
        _SCAFFOLDING_THREAD_POOL._max_workers = max_workers

    return _SCAFFOLDING_THREAD_POOL


class Module5ScaffoldingGenerator:
    """
    Module 5: Generate step-by-step solutions with scaffolding.
    Optional module - can work standalone or as part of pipeline.
    Enhanced with improved multilingual translation capabilities.
    """


    def __init__(self):
        self.generation_history = []
        self.di_format = DiFormat()

    def generate_scaffolded_solution(
        self,
        question_text: str,
        correct_answer: str,
        subject: str = "general",
        grade: int = 8,
        language: str = "english",
        provider_requested: str = 'openai',
        question_index: Optional[int] = None
    ) -> Optional[ScaffoldedSolution]:
        """
        Generate scaffolded solution for any question.
        Accept 1 question only, use LLM, return structured output.
        """
        import time

        method_start = time.time()
        try:
            validated_answer = correct_answer

            prompt_start = time.time()
            scaffolding_instructions = self._create_scaffolding_input(
                question_text, correct_answer, subject, grade, language, question_index)
            prompt_time = time.time() - prompt_start
            logger.debug(f"⏱️ MODULE 5: Prompt creation took {prompt_time:.2f}s")

            llm_start = time.time()
            scaffolding_response = produce_structured_response(
                messages=[
                    {"role": "system",
                        "content": "Respond with ONLY valid JSON that exactly matches the schema. No prose, no code fences."},
                    {"role": "user", "content": scaffolding_instructions}
                ],
                structure_model=ScaffoldingResponse,
                provider=provider_requested,
                temperature=0.3,
                max_output_tokens=1500
            )
            llm_time = time.time() - llm_start
            logger.info(f"⏱️ MODULE 5: LLM scaffolding call took {llm_time:.2f}s")
            scaffolding_response = model_to_json(scaffolding_response)

            # Extract structured data (response is already the parsed object)
            if scaffolding_response:
                # Handle both dict and object responses
                if isinstance(scaffolding_response, dict):
                    detailed_explanation = scaffolding_response.get(
                        "detailed_explanation", DetailedExplanation(steps=[], personalized_academic_insights=[]))
                    voiceover_script = scaffolding_response.get("voiceover_script", VoiceoverScript(
                        question_script="", explanation_step_scripts=[]))
                    explanation = scaffolding_response.get("explanation", "")
                elif hasattr(scaffolding_response, 'detailed_explanation'):
                    detailed_explanation = scaffolding_response.detailed_explanation
                    voiceover_script = scaffolding_response.voiceover_script
                    explanation = getattr(
                        scaffolding_response, 'explanation', "")
                else:
                    # Fallback to empty scaffolding
                    logger.warning(
                        f"📝 MODULE 5: Unexpected scaffolding format, using defaults for {scaffolding_response}")
                    detailed_explanation = DetailedExplanation(
                        steps=[], personalized_academic_insights=[])
                    voiceover_script = VoiceoverScript(
                        question_script="", explanation_step_scripts=[])
                    explanation = ""

                # Convert to ScaffoldedSolution format with validated answer
                scaffolded_solution = ScaffoldedSolution(
                    question=question_text,
                    answer=validated_answer,  # Use validated answer from first request
                    explanation=explanation or "Solution explanation",
                    detailed_explanation=detailed_explanation,
                    voiceover_script=voiceover_script,
                    grade=grade,
                    subject=subject,
                    language=language,
                    generation_status="independently_solved",
                    di_formats_used=self.last_di_source_formats  # Use the actual source formats from DI, not what LLM claims
                )

                self.generation_history.append(scaffolded_solution)
                method_time = time.time() - method_start
                return scaffolded_solution
            else:
                method_time = time.time() - method_start
                logger.error(
                    f"❌ MODULE 5 CORE: Failed to generate scaffolding after {method_time:.2f}s. Error: {scaffolding_response}")
                return None

        except Exception as e:
            method_time = time.time() - method_start
            logger.error(
                f"❌ MODULE 5 CORE: Scaffolded solution generation failed after {method_time:.2f}s: {e}")
            return None

    def generate_batch_scaffolded_solutions(
        self,
        questions_batch: List[tuple],  # List of (question_text, correct_answer, subject, grade, language, question_index)
        provider_requested: str = 'openai'
    ) -> List[Optional[ScaffoldedSolution]]:
        """
        Generate scaffolding for multiple questions in a single LLM call.
        10x faster than individual calls for batches of 10 questions.

        Args:
            questions_batch: List of tuples (question_text, correct_answer, subject, grade, language, question_index)
            provider_requested: LLM provider to use

        Returns:
            List of ScaffoldedSolution objects in same order as input
        """
        import time

        batch_start = time.time()
        batch_size = len(questions_batch)

        try:
            # Build batch prompt
            batch_questions = []
            for idx, (question_text, correct_answer, subject, grade, language, question_index) in enumerate(questions_batch):
                scaffolding_input = self._create_scaffolding_input(
                    question_text, correct_answer, subject, grade, language, question_index
                )
                batch_questions.append(f"### Question {idx + 1}:\n{scaffolding_input}")

            combined_prompt = (
                f"Generate scaffolding for {batch_size} questions below. "
                f"Return a JSON array with exactly {batch_size} scaffolding objects in the SAME ORDER.\n\n"
                + "\n\n".join(batch_questions)
            )

            # Single LLM call for entire batch
            # Calculate safe max_output_tokens based on context window
            messages = [
                {"role": "system",
                 "content": f"Respond with ONLY valid JSON array containing exactly {batch_size} scaffolding objects. No prose, no code fences."},
                {"role": "user", "content": combined_prompt}
            ]

            # Use limit_tokens to calculate safe output tokens
            from src.llms import limit_tokens
            requested_tokens = 1500 * batch_size  # 1500 tokens per question
            safe_output_tokens = limit_tokens(messages, requested_tokens, provider_requested)

            batch_response = produce_structured_response(
                messages=messages,
                structure_model=BatchScaffoldingResponse,
                provider=provider_requested,
                temperature=0.3,
                max_output_tokens=safe_output_tokens
            )

            batch_response = model_to_json(batch_response)

            # Parse batch response and create ScaffoldedSolution objects
            results = []
            scaffoldings = batch_response.get('scaffoldings', []) if isinstance(batch_response, dict) else batch_response.scaffoldings

            for idx, (question_data, scaffolding) in enumerate(zip(questions_batch, scaffoldings)):
                question_text, correct_answer, subject, grade, language, question_index = question_data

                try:
                    # Extract structured data
                    if isinstance(scaffolding, dict):
                        detailed_explanation = scaffolding.get("detailed_explanation", DetailedExplanation(steps=[], personalized_academic_insights=[]))
                        voiceover_script = scaffolding.get("voiceover_script", VoiceoverScript(question_script="", explanation_step_scripts=[]))
                        explanation = scaffolding.get("explanation", "")
                    else:
                        detailed_explanation = scaffolding.detailed_explanation
                        voiceover_script = scaffolding.voiceover_script
                        explanation = getattr(scaffolding, 'explanation', "")

                    scaffolded_solution = ScaffoldedSolution(
                        question=question_text,
                        answer=correct_answer,
                        explanation=explanation or "Solution explanation",
                        detailed_explanation=detailed_explanation,
                        voiceover_script=voiceover_script,
                        grade=grade,
                        subject=subject,
                        language=language,
                        generation_status="batch_generated",
                        di_formats_used=self.last_di_source_formats
                    )

                    results.append(scaffolded_solution)

                except Exception as e:
                    logger.error(f"❌ MODULE 5 BATCH: Failed to parse scaffolding {idx + 1}: {e}")
                    results.append(None)

            batch_time = time.time() - batch_start
            logger.info(f"✅ MODULE 5 BATCH: Generated {len(results)} scaffoldings in {batch_time:.2f}s ({batch_time/batch_size:.2f}s per question)")

            return results

        except Exception as e:
            batch_time = time.time() - batch_start
            logger.error(f"❌ MODULE 5 BATCH: Batch scaffolding failed after {batch_time:.2f}s: {e}")
            # Fallback to individual generation
            logger.info(f"📝 MODULE 5 BATCH: Falling back to individual scaffolding generation")
            return [None] * batch_size

    def generate_from_multiple_choice_question(
        self,
        mc_question: MultipleChoiceQuestion,
        language: str = 'arabic',
        provider_requested: str = 'openai',
        progress: ProgressBar = None,
        question_index: Optional[int] = None
    ) -> Optional[ScaffoldedSolution]:
        """
        Generate scaffolded solution from MultipleChoiceQuestion.
        Integration point with Module 4.
        """
        import time

        generation_start = time.time()
        logger.info(f"⏱️ MODULE 5: Starting scaffolding for question")

        # Handle both MCQ and fill-in questions
        prep_start = time.time()
        if hasattr(mc_question, 'options') and mc_question.options:
            # MCQ format - use the correct_answer field directly
            correct_answer_text = mc_question.correct_answer
        else:
            # Fill-in format - use the answer directly
            logger.debug(f"🧩 MODULE 5: Fill-in question data: {mc_question}")
            correct_answer_text = getattr(mc_question, 'correct_answer', '') or getattr(mc_question, 'answer', '')
            if not correct_answer_text:
                logger.error(f"🧩 MODULE 5: No correct answer found in fill-in question.")
                return None

        # Format question based on type
        if hasattr(mc_question, 'options') and mc_question.options:
            # MCQ format - include options (now dictionary format)
            option_lines = [f"{option_id}) {option_text}" for option_id, option_text in mc_question.options.items()]
            question_with_options = (
                f"{mc_question.question_text}\n\n"
                "OPTIONS:\n" + "\n".join(option_lines)
            )
        else:
            # Fill-in format - use question as-is
            question_with_options = mc_question.question_text

        prep_time = time.time() - prep_start
        logger.debug(f"⏱️ MODULE 5: Question prep took {prep_time:.2f}s")

        scaffolding_start = time.time()
        result = self.generate_scaffolded_solution(
            question_text=question_with_options,
            correct_answer=correct_answer_text,
            subject=mc_question.subject,
            grade=mc_question.grade,
            language=language,
            provider_requested=provider_requested,
            question_index=question_index
        )
        scaffolding_time = time.time() - scaffolding_start

        progress.update(1)

        total_time = time.time() - generation_start
        logger.info(f"⏱️ MODULE 5: Question complete in {total_time:.2f}s (scaffolding: {scaffolding_time:.2f}s)")

        return result

    async def generate_parallel_scaffolded_solutions(
        self,
        mc_questions: List[MultipleChoiceQuestion],
        language: str = "arabic",
        provider_requested: str = 'openai',
        translate: bool = False,
        max_workers: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Parallel, minimal, no logging.
        Runs generate_from_multiple_choice_question for all questions and
        returns structured results.
        OPTIMIZED: Retrieves DI formats once per batch instead of per question.
        """
        import asyncio

        # OPTIMIZATION: Fetch DI insights asynchronously in background while processing questions
        # This allows Module 5 to run in parallel with Module 3+4
        self.batch_di_cache = {}  # Cache DI insights

        async def fetch_di_insights_async():
            """Fetch DI insights asynchronously without blocking question processing"""
            if not mc_questions:
                return

            batch_start = time.time()
            first_q = mc_questions[0]
            all_same_grade_subject = all(
                q.grade == first_q.grade and q.subject == first_q.subject
                for q in mc_questions
            )

            if all_same_grade_subject:
                # ALL questions share grade/subject - retrieve DI formats ONCE for entire batch
                grade = first_q.grade
                subject = first_q.subject

                # Use first 5 questions as representative sample
                sample_questions = mc_questions[:5]
                combined_query = " ".join([q.question_text[:100] for q in sample_questions])

                logger.info(f"📚 MODULE 5: Retrieving DI formats for grade={grade}, subject={subject}")

                # Run in thread to not block
                batch_di_insights = await asyncio.to_thread(
                    self.di_format.get_di_insights_for_scaffolding,
                    question_text=combined_query,
                    subject=subject,
                    grade=grade,
                    type="rag"
                )

                # Cache for ALL questions
                for q_idx in range(len(mc_questions)):
                    self.batch_di_cache[q_idx] = batch_di_insights

                logger.info(f"📚 MODULE 5: DI retrieval completed in {time.time() - batch_start:.2f}s")
            else:
                # Mixed grades/subjects - retrieve per-question (lazy loading in _create_scaffolding_input)
                logger.info(f"📚 MODULE 5: Mixed grades/subjects detected - using lazy DI retrieval")

        # Start DI fetch in background (don't await yet)
        di_fetch_task = asyncio.create_task(fetch_di_insights_async())

        progress = ProgressBar(len(mc_questions), f"🔄 Processing {len(mc_questions)} MCQs in parallel")

        # Ensure DI insights are ready before starting parallel processing
        await di_fetch_task

        # Create ALL tasks at once for true parallel processing
        # Use custom thread pool with 50 workers instead of default (~8-16)
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(
                _get_scaffolding_thread_pool(max_workers),
                lambda mc_q=mc_q, idx=idx: self.generate_from_multiple_choice_question(
                    mc_q, language, provider_requested, progress, idx
                )
            )
            for idx, mc_q in enumerate(mc_questions)
        ]

        # Run all questions in parallel
        results = await asyncio.gather(*tasks)

        progress.complete(f"Parallel scaffolding complete: {len(results)} items ready")

        out: List[Dict[str, Any]] = []

        # Process results with progress tracking
        for idx, (mc_q, scaffolded) in enumerate(zip(mc_questions, results)):
            s = to_dict(scaffolded) if scaffolded else {}

            # options / answer from mc question payload  
            if hasattr(mc_q, 'options') and mc_q.options:
                # New dict format: {"A": "4 cm", "B": "0.4 cm", ...}
                options = list(mc_q.options.values())  # Get just the option texts
                answer = mc_q.correct_answer_choice  # A, B, C, or D
            else:
                options = []
                answer = getattr(mc_q, 'correct_answer', '')
            
            # Handle different question types
            if options:
                # MCQ format - we already have the correct answer text and choice
                answer = mc_q.correct_answer  # This is the actual answer text like "4 cm"
            else:
                # Fill-in format - use answer directly
                answer = getattr(mc_q, 'correct_answer', '')

            # ----- detailed_explanation -----
            detailed_explanation = None
            de = s.get("detailed_explanation")
            if isinstance(de, dict):
                steps_in = _safe_get(de, "steps", []) or []
                steps = []
                for step in steps_in:
                    # after to_dict, each step is a dict
                    content = _safe_get(step, "content", "")
                    if "corrected" in str(content).lower():
                        continue
                    steps.append({
                        "title": _safe_get(step, "title"),
                        "content": content
                    })

                insights_in = _safe_get(
                    de, "personalized_academic_insights", []) or []
                insights = [
                    {
                        "answer": _safe_get(ins, "answer"),
                        "insight": _safe_get(ins, "insight"),
                    }
                    for ins in insights_in
                ]

                detailed_explanation = {
                    "steps": steps,
                    "personalized_academic_insights": insights
                }

            # ----- voiceover_script -----
            voiceover_script = None
            vos = s.get("voiceover_script")
            if isinstance(vos, dict):
                # ess = _safe_get(vos, "explanation_step_scripts", []) or []
                # explanation_step_scripts = [
                #     {
                #         "step_number": _safe_get(step, "step_number"),
                #         "script": _safe_get(step, "script"),
                #     }
                #     for step in ess
                # ]
                voiceover_script = {
                    "question_script": _safe_get(vos, "question_script"),
                    "explanation_step_scripts": [],
                    "answer_choice_scripts": [f"Option {chr(65 + j)}: {opt}" for j, opt in enumerate(options[:4])] if options else [],
                }

            # Determine question type based on presence of options
            question_type = "mcq" if options else "fill-in"

            question_dict = {
                "question_id": mc_q.question_id,  # Add question_id for tracking
                "type": question_type,
                "question": mc_q.question_text,
                "answer": answer,
                "difficulty": mc_q.difficulty,
                "explanation": s.get("explanation") or "Solution explanation",
                "detailed_explanation": detailed_explanation,
                "voiceover_script": voiceover_script,
                "di_formats_used": s.get("di_formats_used"),  # Include DI formats
            }
            
            # Only add options field for MCQ questions
            if question_type == "mcq":
                # Convert options list back to dictionary format for compatibility
                options_dict = {}
                if hasattr(mc_q, 'options') and mc_q.options:
                    options_dict = mc_q.options  # Already in dict format
                question_dict["options"] = options_dict
                question_dict["answer_choice"] = mc_q.correct_answer_choice  # A, B, C, or D
            
            out.append(question_dict)

        # filter out the questions where detailed_explanation is None or null or "null" or missing
        out = [item for item in out if item.get("detailed_explanation") not in [
            None, "null", "Null"]]

        # translate each item in parallel if translate is enabled
        if translate:
            translation_progress = ProgressBar(len(out), f"🌐 Translating {len(out)} items to {language}")
            translations = [
                asyncio.to_thread(
                    execute_translate, item, target_language=language, provider_requested="google", progress=translation_progress
                )
                for item in out
            ]
            out = await asyncio.gather(*translations)
            translation_progress.complete(f"Translation to {language} completed")

        return out

    def _create_scaffolding_input(
        self,
        question_text: str,
        correct_answer: str,
        subject: str,
        grade: int,
        language: str,
        question_index: Optional[int] = None
    ) -> str:
        """Create instructions for independent problem solving and scaffolding with UAE 'spiky' infusion."""
        import time

        # OPTIMIZATION: Use cached DI insights from mini-batch if available
        if question_index is not None and hasattr(self, 'batch_di_cache') and question_index in self.batch_di_cache:
            # Use cached insights from mini-batch retrieval
            di_insights_obj = self.batch_di_cache[question_index]
            logger.debug(f"📚 MODULE 5: Using cached DI insights for question {question_index}")
        else:
            # Fallback: Get DI insights for this specific question (backwards compatibility)
            di_start = time.time()
            di_insights_obj = self.di_format.get_di_insights_for_scaffolding(question_text, subject, grade, type="rag")
            di_time = time.time() - di_start
            logger.info(f"⏱️ MODULE 5: DI format retrieval took {di_time:.2f}s")
            logger.debug(f"📚 MODULE 5: Retrieved fresh DI insights for question")

        # Extract just the text for the prompt (not the source formats)
        di_insights = di_insights_obj.insights_text if hasattr(di_insights_obj, 'insights_text') else str(di_insights_obj)
        # Store the source formats for later use (not sent to prompt)
        self.last_di_source_formats = di_insights_obj.source_formats if hasattr(di_insights_obj, 'source_formats') else None
        # Get grade-appropriate language examples
        grade_examples = self._get_grade_language_examples(grade, language)
        english_prompt = f"""
            You are an expert {subject} teacher for grade {grade}. You will receive a question and must:

            YOUR TASK IS TO **BUILD SCAFFOLDING** — concise, step-by-step reasoning with natural Arabic/UAE cultural integration.

            CORE REQUIREMENTS:
            - Align directly with UAE curriculum concepts already taught
            - Include complete categorization: subject, grade, standard, difficulty
            - Ensure QTI-mappable components: stem, options, key, metadata
            - Advance specific learning objectives effectively

            SCAFFOLDING QUALITY STANDARDS:
            - Each step must be factually accurate and unambiguous
            - All misconceptions must be clearly incorrect under any interpretation
            - Base insights on common student misconceptions that provide learning value
            - Maintain clear justification for correctness and incorrectness

            CRITICAL REQUIREMENTS:
            - Accuracy is the UTMOST priority
            - Respond at a grade {grade} level
            - **ABSOLUTELY FORBIDDEN**: NEVER EVER reveal, state, or give away the correct answer in ANY step. Steps must guide thinking WITHOUT giving the final answer.
            - Each step should provide thinking guidance, NOT the solution itself
            - Steps should help students discover the answer through their own efforts
            - NEVER include any names of people or objects that don't exist in the question.
            - In the Text Fields NEVER INCLUDE any non-{language} text
            - Each step MUST add some value. Not just repeat parts of the question.
            
            {grade_examples}
            
            {di_insights}

            LANGUAGE & PRESENTATION STANDARDS:
            - Use grade-level appropriate language following the examples above
            - Keep vocabulary simple and direct as shown in the GOOD examples
            - Avoid complex wording patterns shown in the AVOID examples
            - Maintain consistent wording throughout (same terms, no synonym variation)
            - Ensure grammatical correctness in target language
            - Verify proper formatting: alignment, spacing, notation standards
            - Define technical terms clearly when necessary
            - Prioritize clarity over cleverness always

            CULTURAL INFUSION RULES:
            - Use Arabic names (Ahmed, Fatima, Khalid) ONLY when examples need names
            - Reference UAE contexts naturally (dirhams, local landmarks, dates/camels for word problems)
            - Keep cultural additions under 10 words but make them authentic
            - Cultural elements must enhance understanding by providing relevant context, never distract from learning objectives

            CONTENT INTEGRITY REQUIREMENTS:
            - Include clear thinking prompts that guide students toward the solution process
            - Provide step-by-step thinking guidance appropriate for grade level
            - Focus on the methodology and approach, not the final answer
            - Verify factual accuracy of guidance steps when applicable

            SCAFFOLDING STRUCTURE:
            - EXACTLY 3 steps (60-70 tokens per step)
            - Each step: one sentence for WHAT (with cultural element if natural), one for WHY
            - Use problem numbers with Arabic/UAE context where fitting
            - 1 misconception (10 words max)
            - Insights must be under 15 words each
            - Strictly follow the DI insights if provided

            SUBJECT-SPECIFIC ADAPTATION:
            - Mathematics: Focus on numerical reasoning and formula application
            - Sciences: Emphasize concept application and experimental reasoning
            - Language Arts: Target comprehension and analysis skills
            - Social Studies: Address factual understanding and interpretation

            PRODUCTION BENCHMARKS:
            - Generate scaffolded solutions efficiently while maintaining quality validation
            - Target clear, educational explanations that help students learn from mistakes
            - Track scaffolding effectiveness: clarity, cultural integration, learning value
            - Ensure step-by-step reasoning appropriate for grade level and subject
        """

        arabic_prompt = f"""
            أنت معلم خبير في مادة {subject} للصف {grade}. ستتلقى سؤالًا ويجب عليك:

            مهمتك هي **بناء التدرّج التعليمي (Scaffolding)** — شرح موجز، خطوة بخطوة مع دمج طبيعي للثقافة العربية/الإماراتية.

            **المتطلبات الأساسية:**
            - محاذاة مباشرة مع مفاهيم المنهاج الإماراتي المدرّسة مسبقاً
            - تضمين تصنيف كامل: المادة، الصف، المعيار، الصعوبة
            - ضمان مكونات قابلة للتخطيط QTI: المقدمة، الخيارات، المفتاح، البيانات الوصفية
            - تطوير أهداف التعلم المحددة بفعالية

            **معايير جودة التدرّج التعليمي:**
            - كل خطوة يجب أن تكون دقيقة وواضحة المعنى
            - جميع المفاهيم الخاطئة يجب أن تكون خاطئة بوضوح تحت أي تفسير
            - بناء الرؤى على مفاهيم خاطئة شائعة لدى الطلاب توفر قيمة تعليمية
            - الحفاظ على تبرير واضح للصحة وعدم الصحة

            **المتطلبات الحرجة:**
            - الدقة هي الأولوية القصوى
            - يجب أن يكون الرد بمستوى الصف {grade}
            - **ممنوع تماماً**: لا تكشف أو تذكر أو تعطي الإجابة الصحيحة في أي خطوة. الخطوات يجب أن توجه التفكير دون إعطاء الحل النهائي.
            - كل خطوة يجب أن تقدم إرشاد تفكير، وليس الحل نفسه
            - الخطوات يجب أن تساعد الطلاب على اكتشاف الإجابة من خلال جهودهم الخاصة
            - لا تُدرج أبداً أي أسماء أشخاص أو أشياء غير موجودة في السؤال
            - في الحقول النصية لا تُدرج أي نص غير {language}
            - كل خطوة يجب أن تضيف قيمة حقيقية، وليس مجرد تكرار لأجزاء من السؤال

            
            {grade_examples}
            
            {di_insights}
            **قواعد دمج الثقافة:**

            * استخدم أسماء عربية (أحمد، فاطمة، خالد، مريم) فقط عندما تحتاج إلى أسماء
            * أدرج السياق الإماراتي بشكل طبيعي (الدرهم، المعالم المحلية، التمور)
            * يُطبَّق فقط عندما يكون ذا صلة حقيقية بالهدف التعليمي؛ مع الالتزام بـ"إرشادات التكييف" للحفاظ على التوازن التعليمي.
            * إذا كان الجواب بالإنجليزية، يمكن إدخال بعض المصطلحات العربية الرئيسة بخفة (بين أقواس) لتعميق الفهم؛ وإذا كان بالعربية، فاكتب بالكامل بالعربية وفضّل المصطلحات العربية.

            **معايير اللغة والعرض:**
            - استخدام لغة مناسبة لمستوى الصف حسب الأمثلة أعلاه
            - اجعل المفردات بسيطة ومباشرة كما هو موضح في الأمثلة الجيدة
            - تجنب أنماط الصياغة المعقدة الموضحة في قسم "تجنب"
            - الحفاظ على صياغة متسقة (نفس المصطلحات، بدون تغيير المرادفات)
            - ضمان الصحة النحوية في اللغة المستهدفة
            - التحقق من التنسيق السليم: المحاذاة، المسافات، معايير التدوين
            - تعريف المصطلحات التقنية بوضوح عند الضرورة
            - إعطاء الأولوية للوضوح على الذكاء دائماً

            **متطلبات سلامة المحتوى:**
            - تضمين إرشادات تفكير واضحة توجه الطلاب نحو عملية الحل
            - توفير إرشاد تفكير خطوة بخطوة مناسب لمستوى الصف
            - التركيز على المنهجية والطريقة، وليس الإجابة النهائية
            - التحقق من الدقة الواقعية لخطوات الإرشاد عند الحاجة

            **هيكل التدرّج التعليمي:**
            - 3 خطوات بالضبط (60-70 كلمة لكل خطوة تعادل 60-70 كلمة لكل خطوة)
            - كل خطوة: جملة واحدة لـ"ماذا" (مع عنصر ثقافي إن كان طبيعياً)، جملة واحدة لـ"لماذا"
            - استخدم أرقام المسائل مع السياق العربي/الإماراتي حيثما يناسب
            - مفهوم خاطئ واحد (10 كلمات كحد أقصى)
            - الرؤى يجب أن تكون أقل من 15 كلمة لكل منها
            - اتبع رؤى التعليم المباشر بدقة إن تم توفيرها

            **التكيف حسب المادة:**
            - الرياضيات: التركيز على التفكير العددي وتطبيق الصيغ
            - العلوم: التأكيد على تطبيق المفاهيم والتفكير التجريبي
            - فنون اللغة: استهداف مهارات الفهم والتحليل
            - الدراسات الاجتماعية: معالجة الفهم الواقعي والتفسير

            **معايير الإنتاج:**
            - توليد حلول متدرجة بكفاءة مع الحفاظ على التحقق من الجودة
            - استهداف شروحات واضحة وتعليمية تساعد الطلاب على التعلم من الأخطاء
            - تتبع فعالية التدرج: الوضوح، التكامل الثقافي، القيمة التعليمية
            - ضمان التفكير المتدرج المناسب لمستوى الصف والمادة

        """

        # Build the final instruction prompt (preserves your JSON output schema)
        final_prompt = f"""
            {arabic_prompt if language.strip().lower() == "arabic" else english_prompt}

            QUESTION:
            {question_text}

            CORRECT ANSWER:
            {correct_answer}
            
            OUTPUT FIELDS:
            - detailed_explanation.steps
            - detailed_explanation.personalized_academic_insights

            JSON FORMAT:
            {{
            "detailed_explanation": {{
                "steps": [
                {{
                    "title": "Step 1: Analyze the Problem",
                    "content": <80-100 words. COMPREHENSIVE mini-lesson that:
                        1) Identifies all key information given in the question
                        2) Highlights what we need to find
                        3) Connects to relevant concepts/formulas without revealing calculation
                        4) Includes metacognitive prompts like "Think about..." or "Ask yourself..."
                        5) Uses grade-appropriate language
                        DO NOT state the final answer. Guide thinking deeply.>,
                    "image": <leave blank>,
                    "image_alt_text": <leave blank>
                }},
                {{
                    "title": "Step 2: Develop the Strategy",
                    "content": <80-100 words. DETAILED reasoning guidance that:
                        1) Explains the approach to solving (e.g., "think about equal groups")
                        2) Breaks down thought process into logical sub-steps
                        3) Shows how concepts connect without revealing the answer
                        4) Provides clear thinking prompts appropriate for grade level
                        5) References prerequisite knowledge if helpful ("Remember when we learned...")
                        DO NOT reveal the answer. Make the methodology crystal clear.>,
                    "image": <leave blank>,
                    "image_alt_text": <leave blank>
                }},
                {{
                    "title": "Step 3: Apply and Verify",
                    "content": <80-100 words. COMPLETE verification guidance that:
                        1) Describes how to check if approach makes sense
                        2) Explains what the final answer should represent (without stating it)
                        3) Connects back to the question context
                        4) Reinforces key learning points
                        5) Builds confidence through transparent reasoning
                        DO NOT give away the answer. Make the verification process clear.>,
                    "image": <leave blank>,
                    "image_alt_text": <leave blank>
                }}
                ],
                "personalized_academic_insights": [
                {{
                    "answer": <incorrect answer 1>,
                    "insight": <15-20 words explaining: 1) the specific conceptual error, 2) WHY it's incorrect, 3) a hint toward correct reasoning>
                }},
                {{
                    "answer": <incorrect answer 2>,
                    "insight": <15-20 words explaining: 1) the specific conceptual error, 2) WHY it's incorrect, 3) a hint toward correct reasoning>
                }},
                {{
                    "answer": <incorrect answer 3>,
                    "insight": <15-20 words explaining: 1) the specific conceptual error, 2) WHY it's incorrect, 3) a hint toward correct reasoning>
                }}
                ]
            }},
            "voiceover_script": {{
                "question_script": <script for reading the question>,
                "answer_choice_scripts": [<string for option A>, <string for option B>, <string for option C>, <string for option D>],
            }},
            "explanation": <15 words MAX summarizing the solution method>
            }}
        """
 
        return final_prompt

    def _get_grade_language_examples(self, grade: int, language: str) -> str:
        """Get grade-appropriate language examples for scaffolding."""
        grade_key = f"Grade{grade}"
        
        if grade_key not in GRADE_VOCABULARY_EXAMPLES_EN:
            # Default to closest available grade
            available_grades = [int(k.replace('Grade', '')) for k in GRADE_VOCABULARY_EXAMPLES_EN.keys()]
            closest_grade = min(available_grades, key=lambda x: abs(x - grade))
            grade_key = f"Grade{closest_grade}"
        
        examples = GRADE_VOCABULARY_EXAMPLES_EN[grade_key]
        
        if language.strip().lower() == "arabic":
            # Get Arabic examples from constant, using same grade_key logic
            arabic_examples = GRADE_VOCABULARY_EXAMPLES_AR[grade_key]
            
            # Arabic version of grade examples
            grade_examples_section = f"""
أمثلة لغة الصف {grade}:
استخدم هذه الأنماط للغة المناسبة لمستوى الصف في خطوات التدرج التعليمي:

أمثلة جيدة (استخدم هذا الأسلوب):
{chr(10).join(arabic_examples['positive_examples'])}

تجنب (معقد جداً لمستوى الصف):
{chr(10).join(arabic_examples['negative_examples'])}

طبق مستوى اللغة هذا على خطوات التدرج - اجعل الصياغة بسيطة ومباشرة ومناسبة للعمر.
"""
        else:
            # English version
            grade_examples_section = f"""
GRADE {grade} LANGUAGE EXAMPLES:
Use these patterns for grade-appropriate language in your scaffolding steps:

GOOD examples (use this style):
{chr(10).join(examples['positive_examples'])}

AVOID (too complex for grade level):
{chr(10).join(examples['negative_examples'])}

Apply this language level to your scaffolding steps - keep wording simple, direct, and age-appropriate.
"""
        return grade_examples_section

