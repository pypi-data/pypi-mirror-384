#!/usr/bin/env python3
"""
Orchestrator: Dual-pipeline question generation with containerized modules.

Architecture:
- Container 1: DI Fetch (background)
- Container 2: Modules 0-2 (DB + Generation)
- Pipeline A: DB questions → Module 4 + 5 (parallel)
- Pipeline B: Generated questions → Module 3 → Module 4 + 5 (parallel)

All pipelines run in parallel for maximum throughput.
"""

ENABLE_PARALLEL_PROCESSING = True

import json
import time
import logging
import asyncio
import concurrent.futures
from src.question_gen_v1.module_0 import Module0DatabaseRetriever
from src.question_gen_v1.module_1 import Module1RAGRetriever
from src.question_gen_v1.module_2 import get_extractor
from src.question_gen_v1.module_3_mathematics import Module3MathematicsGenerator
from src.question_gen_v1.module_4 import Module4MultipleChoiceConverter
from src.question_gen_v1.module_5 import Module5ScaffoldingGenerator
from src.utils.dev_upload_util import dev_uploader
from src.config import Config
from src.image_gen_module import ImageGenModule

logger = logging.getLogger(__name__)

class Orchestrator:
    """Dual-pipeline orchestrator for question generation with scaffolding."""

    def __init__(self, accuracy_mode: bool = False, max_workers: int = None):
        """
        Initialize orchestrator with all modules.

        Args:
            accuracy_mode: If True, use GPT-4o for accuracy. If False, use DSPy for speed/cost.
            max_workers: Max parallel workers for all operations. Defaults to Config.MAX_WORKERS.
        """
        self.accuracy_mode = accuracy_mode
        self.max_workers = max_workers if max_workers is not None else Config.MAX_WORKERS
        self.module_1 = Module1RAGRetriever(accuracy_mode=accuracy_mode)
        self.module_2_factory = get_extractor
        self.module_3_math = Module3MathematicsGenerator()
        self.module_4 = Module4MultipleChoiceConverter()
        self.module_5 = Module5ScaffoldingGenerator()

        if accuracy_mode:
            try:
                from src.dspy_improvements.accuracy_optimizer import enable_accuracy_mode
                enable_accuracy_mode()
                logger.info("🎯 Orchestrator initialized [MODE: ACCURACY, PROVIDER: GPT-4o]")
            except Exception as e:
                logger.warning(f"⚠️  Accuracy mode failed to enable: {e}")
        else:
            logger.info("🎯 Orchestrator initialized [MODE: PRODUCTION, PROVIDER: DSPy]")
    
    async def execute_question_generation_pipeline(self, grade: int, subject: str, quantity: int, difficulty: str = 'medium', skill_title: str = None, language: str = 'arabic', provider_requested: str = 'openai', question_type: str = 'mcq', existing_ratio: float = 0.0, partial_match_threshold: float = 0.7) -> list:
        """
        PUBLIC API: Execute Modules 0-2 pipeline (DB fetch + question generation).

        Complete pipeline: Module0 (DB) -> Module1 (RAG) -> Module2 (Generate) -> Module3 (Validate)
        Execute them, move structured output from one to input of next.
        Now includes mathematical validation BEFORE MCQ conversion.

        Args:
            existing_ratio: Ratio of existing questions to pull from DB (0.0-1.0)
                           e.g., 0.5 = 50% from DB, 50% newly generated

        Returns:
            List of questions (mix of DB + generated, marked by metadata.source)
        """
        existing_questions_from_db = []
        db_question_texts = set()

        if existing_ratio > 0:
            from src.utils.dev_upload_util import retrieve_existing_questions_for_mixing
            existing_count = int(quantity * existing_ratio)

            logger.info(f"📦 MODULE 0 START: Fetching {existing_count} DB questions [grade={grade}, subject={subject}]")
            db_start = time.time()

            existing_questions_from_db = retrieve_existing_questions_for_mixing(
                grade=grade,
                subject=subject,
                quantity_needed=existing_count,
                skill_title=skill_title,
                language=language,
                provider=provider_requested,
                partial_match_threshold=partial_match_threshold
            )

            logger.info(f"📦 MODULE 0 COMPLETE: Retrieved {len(existing_questions_from_db)} questions ({time.time() - db_start:.2f}s)")
            db_question_texts = {q['question_text'].lower().strip() for q in existing_questions_from_db}

        new_quantity = quantity - len(existing_questions_from_db)
        logger.info(f"🚀 PIPELINE START: {len(existing_questions_from_db)} from DB, {new_quantity} to generate")

        validated_questions = []
        samples = []

        if new_quantity > 0:
            logger.info(f"📚 MODULE 1 START: Retrieving samples [grade={grade}, subject={subject}, skill={skill_title}]")
            module1_start = time.time()

            samples = self.module_1.retrieve_samples(
                grade=grade,
                subject=subject,
                limit=10,
                skill_title=skill_title,
                language=language,
                provider=provider_requested,
                exclude_question_texts=db_question_texts if db_question_texts else None
            )

            logger.info(f"📚 MODULE 1 COMPLETE: Retrieved {len(samples) if samples else 0} samples ({time.time() - module1_start:.2f}s)")

            logger.info(f"🔍 MODULE 2 START: Generating {new_quantity} questions [difficulty={difficulty}, type={question_type}]")
            module2_start = time.time()

            module_2_generator = self.module_2_factory(subject=subject)
            questions = module_2_generator.generate_questions_from_samples(
                samples=samples,
                quantity=new_quantity,
                subject=subject,
                grade=grade,
                difficulty=difficulty,
                language=language,
                question_type=question_type
            )

            logger.info(f"🔍 MODULE 2 COMPLETE: Generated {len(questions) if questions else 0} questions ({time.time() - module2_start:.2f}s)")

            if not questions and len(existing_questions_from_db) == 0:
                raise ValueError("❌ MODULE 2 FAILED: No questions generated and no DB questions available")

            unvalidated_questions = questions
        else:
            logger.info(f"⏭️  SKIPPING MODULE 2: All {quantity} questions from DB")
            unvalidated_questions = []

        from src.question_gen_v1.module_2 import GeneratedQuestion
        import uuid

        db_as_generated_questions = []
        for db_q in existing_questions_from_db:
            db_as_generated_questions.append(GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                pattern_id=f"db_{db_q.get('index', 0)}",
                subject=db_q['subject_area'],
                topic=db_q.get('subtopic') or db_q.get('broad_topic', 'General'),
                grade=db_q['grade'],
                difficulty=db_q['difficulty'],
                language=db_q['language'],
                question_text=db_q['question_text'],
                parameter_values={},
                answer=db_q['answer'],
                working_steps=[db_q['explanation']] if db_q.get('explanation') else [],
                rationale="Retrieved from existing database",
                constraints=[],
                metadata={
                    'source': 'database',
                    'db_question_type': db_q.get('question_type'),
                    'db_options': db_q.get('options'),
                    'skip_module_4': True
                }
            ))

        all_questions = db_as_generated_questions + unvalidated_questions
        logger.info(f"✅ CONTAINER 2 COMPLETE: {len(all_questions)} questions total ({len(db_as_generated_questions)} DB, {len(unvalidated_questions)} generated)")

        self.question_images = {}
        return all_questions[:quantity]
    
    async def _internal_convert_questions_to_mcq(self, questions, language, provider_requested):
        """INTERNAL: Legacy MCQ conversion wrapper (not used in dual-pipeline)."""
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            logger.info(f"🔄 MODULE 4 START: Converting {len(questions)} questions to MCQ [language={language}]")
            start = time.time()

            mc_questions = await loop.run_in_executor(
                executor,
                self.module_4.convert_to_multiple_choice,
                questions,
                language,
                provider_requested
            )

            logger.info(f"🔄 MODULE 4 COMPLETE: Converted {len(mc_questions) if mc_questions else 0} MCQs ({time.time() - start:.2f}s)")
            return mc_questions


    async def execute_complete_pipeline_with_scaffolding(
        self,
        grade: int,
        subject: str,
        quantity: int,
        difficulty: str = 'medium',
        skill_title: str = None,
        language: str = 'arabic',
        question_type: str = 'mcq',
        provider_requested: str = 'openai',
        translate: bool = False,
        existing_ratio: float = 0.0,
        partial_match_threshold: float = 0.7
    ) -> list:
        """
        PUBLIC API: Execute complete dual-pipeline processing with scaffolding.

        PIPELINE ARCHITECTURE:
        1. DI Fetch (background) + Modules 0-2 (parallel)
        2. Split into two independent pipelines:
           - Pipeline A (DB questions): Module 4 + Module 5 (parallel)
           - Pipeline B (Generated questions): Module 3 → Module 4 + Module 5 (parallel)
        3. Merge results and return

        Args:
            grade: Educational grade level
            subject: Subject (e.g., 'mathematics', 'science')
            quantity: Total number of questions to generate
            difficulty: Question difficulty ('easy', 'medium', 'hard')
            skill_title: Optional specific skill to focus on
            language: Output language ('arabic', 'english')
            question_type: 'mcq' or 'fill-in'
            provider_requested: LLM provider ('dspy', 'openai', etc.)
            translate: Whether to translate scaffolding
            existing_ratio: Ratio of questions from DB (0.0-1.0), e.g., 0.5 = 50% DB, 50% generated
            partial_match_threshold: Similarity threshold for deduplication

        Returns:
            List of fully structured questions with scaffolded solutions ready for API response
        """
        start_time = time.time()
        logger.info(f"🚀 PIPELINE START: {quantity} questions [existing_ratio={existing_ratio}, grade={grade}, subject={subject}]")
        logger.info(f"⏱️  t=0.00s - PIPELINE START")

        async def _container_fetch_di_insights():
            """CONTAINER 1: Fetch DI insights in background."""
            try:
                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - DI FETCH LAUNCHED (background, parallel with Module 0)")
                loop = asyncio.get_event_loop()

                di_result = await loop.run_in_executor(
                    None,
                    lambda: self.module_5.di_format.get_di_insights_for_scaffolding(
                        question_text=f"Grade {grade} {subject}",
                        subject=subject,
                        grade=grade,
                        type="rag"
                    )
                )

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - DI FETCH COMPLETE (ready for Module 5)")
                return di_result
            except Exception as e:
                logger.warning(f"⚠️  t={time.time() - start_time:.2f}s - DI FETCH FAILED: {e}")
                return None

        logger.info(f"⏱️  t={time.time() - start_time:.2f}s - LAUNCHING DI FETCH + MODULE 0 IN PARALLEL")
        di_task = asyncio.create_task(_container_fetch_di_insights())

        logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 0 START: Fetching DB questions (parallel with DI)")

        from src.utils.dev_upload_util import retrieve_existing_questions_for_mixing
        from src.question_gen_v1.module_2 import GeneratedQuestion
        import uuid

        db_questions_raw = []
        if existing_ratio > 0:
            existing_count = int(quantity * existing_ratio)
            db_questions_raw = retrieve_existing_questions_for_mixing(
                grade=grade,
                subject=subject,
                quantity_needed=existing_count,
                skill_title=skill_title,
                language=language,
                provider=provider_requested,
                partial_match_threshold=partial_match_threshold
            )
            logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 0 COMPLETE: Retrieved {len(db_questions_raw)} DB questions")

        db_questions = []
        for db_q in db_questions_raw:
            db_questions.append(GeneratedQuestion(
                question_id=str(uuid.uuid4()),
                pattern_id=f"db_{db_q.get('index', 0)}",
                subject=db_q['subject_area'],
                topic=db_q.get('subtopic') or db_q.get('broad_topic', 'General'),
                grade=db_q['grade'],
                difficulty=db_q['difficulty'],
                language=db_q['language'],
                question_text=db_q['question_text'],
                parameter_values={},
                answer=db_q['answer'],
                working_steps=[db_q['explanation']] if db_q.get('explanation') else [],
                rationale="Retrieved from existing database",
                constraints=[],
                metadata={'source': 'database', 'db_question_type': db_q.get('question_type'), 'db_options': db_q.get('options'), 'skip_module_4': True}
            ))

        new_quantity = quantity - len(db_questions)
        db_question_texts = {q.question_text.lower().strip() for q in db_questions}

        logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 0 COMPLETE: {len(db_questions)} DB questions ready")
        logger.info(f"⏱️  t={time.time() - start_time:.2f}s - LAUNCHING BOTH PIPELINES NOW (parallel)")
        logger.info(f"⏱️  t={time.time() - start_time:.2f}s - PIPELINE A: {len(db_questions)} DB → Module 4+5 (NO Module 1,2,3)")
        logger.info(f"⏱️  t={time.time() - start_time:.2f}s - PIPELINE B: {new_quantity} to generate → Module 1→2→3 → Module 4+5")

        parallel_start = time.time()

        async def _orchestrate_dual_pipeline_execution():
            """Orchestrate parallel execution of Pipeline A and Pipeline B."""
            loop = asyncio.get_event_loop()

            async def _helper_await_di_for_module5(num_questions: int):
                """Helper: AWAIT DI for Module 5 (blocks Module 5 only)."""
                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 5: Waiting for DI (does NOT block Module 4)")
                try:
                    di_result = await di_task
                    if di_result:
                        logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 5: DI ready, using cached DI")
                        return {i: di_result for i in range(num_questions)}
                except Exception as e:
                    logger.warning(f"⚠️  t={time.time() - start_time:.2f}s - MODULE 5: DI error: {e}")
                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 5: No DI, will fetch on-demand")
                return {}

            async def _container_convert_questions_to_mcq(questions, pipeline_name):
                """CONTAINER 4: Convert questions to MCQ format."""
                if not questions or question_type == 'fill-in':
                    return questions

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 4 START (Pipeline {pipeline_name})")
                start = time.time()

                mc_questions = await loop.run_in_executor(
                    None,
                    lambda: self.module_4.convert_to_multiple_choice(questions, language, provider_requested, max_workers=self.max_workers)
                )

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 4 COMPLETE (Pipeline {pipeline_name}: {len(mc_questions)} MCQs)")
                return mc_questions

            async def _container_generate_scaffolded_solutions(questions, pipeline_name):
                """CONTAINER 5: Generate scaffolded solutions."""
                if not questions:
                    return []

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 5 START (Pipeline {pipeline_name})")

                self.module_5.batch_di_cache = await _helper_await_di_for_module5(len(questions))
                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 5 (Pipeline {pipeline_name}) - DI awaited, starting scaffolding")

                scaffolded = await self.module_5.generate_parallel_scaffolded_solutions(
                    questions, language, provider_requested, translate, max_workers=self.max_workers
                )

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 5 COMPLETE (Pipeline {pipeline_name}: {len(scaffolded)} scaffolds)")
                return scaffolded

            async def _pipeline_process_db_questions():
                """PIPELINE A: Process DB questions (skip validation)."""
                if not db_questions:
                    return [], []

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - PIPELINE A START: {len(db_questions)} DB questions (NO Module 3)")

                mcq_task = asyncio.create_task(_container_convert_questions_to_mcq(db_questions, "A"))
                scaffold_task = asyncio.create_task(_container_generate_scaffolded_solutions(db_questions, "A"))

                mcq_results, scaffold_results = await asyncio.gather(mcq_task, scaffold_task)
                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - PIPELINE A COMPLETE")
                return mcq_results, scaffold_results

            async def _pipeline_process_generated_questions():
                """PIPELINE B: Process generated questions (Module 1→2→3→4+5)."""
                if new_quantity == 0:
                    return [], []

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - PIPELINE B START: Generating {new_quantity} questions")

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 1 START (Pipeline B)")
                samples = await loop.run_in_executor(
                    None,
                    lambda: self.module_1.retrieve_samples(
                        grade=grade, subject=subject, limit=10, skill_title=skill_title,
                        language=language, provider=provider_requested,
                        exclude_question_texts=db_question_texts if db_question_texts else None
                    )
                )
                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 1 COMPLETE (Pipeline B): {len(samples)} samples")

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 2 START (Pipeline B)")
                module_2_generator = self.module_2_factory(subject=subject)
                generated_questions = await loop.run_in_executor(
                    None,
                    lambda: module_2_generator.generate_questions_from_samples(
                        samples=samples, quantity=new_quantity, subject=subject, grade=grade,
                        difficulty=difficulty, language=language, question_type=question_type,
                        max_workers=self.max_workers
                    )
                )
                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 2 COMPLETE (Pipeline B): {len(generated_questions)} questions")

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 3 START (Pipeline B)")
                module_3 = self.module_3_math if hasattr(self, 'module_3_math') else self.module_3
                validated = await loop.run_in_executor(
                    None,
                    lambda: module_3.validate_questions(generated_questions, len(generated_questions), provider_requested, max_workers=self.max_workers)
                )
                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - MODULE 3 COMPLETE (Pipeline B): {len(validated)} validated")

                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - PIPELINE B: Launching Module 4 + Module 5 in parallel")
                mcq_task = asyncio.create_task(_container_convert_questions_to_mcq(validated, "B"))
                scaffold_task = asyncio.create_task(_container_generate_scaffolded_solutions(validated, "B"))

                mcq_results, scaffold_results = await asyncio.gather(mcq_task, scaffold_task)
                logger.info(f"⏱️  t={time.time() - start_time:.2f}s - PIPELINE B COMPLETE")
                return mcq_results, scaffold_results

            pipeline_a_task = asyncio.create_task(_pipeline_process_db_questions())
            pipeline_b_task = asyncio.create_task(_pipeline_process_generated_questions())

            (mcq_a, scaffold_a), (mcq_b, scaffold_b) = await asyncio.gather(pipeline_a_task, pipeline_b_task)
            logger.info(f"⏱️  t={time.time() - start_time:.2f}s - BOTH PIPELINES COMPLETE")

            mc_questions = mcq_a + mcq_b
            scaffolded_all = scaffold_a + scaffold_b

            logger.info(f"✅ PARALLEL COMPLETE: {len(mc_questions)} MCQs + {len(scaffolded_all)} scaffolds ready")

            images = []
            if Config.ENABLE_IMAGE_GENERATION:
                logger.info(f"🖼️  IMAGE GEN START: Generating images for {len(base_questions)} questions")
                images = await self._internal_generate_images_with_agent(base_questions, grade, subject)

            mcq_map = {mcq.question_id: mcq for mcq in mc_questions}
            scaffold_map = {item.get('question_id'): item for item in scaffolded_all if item.get('question_id')}

            combined = []
            for qid, mcq in mcq_map.items():
                scaffold = scaffold_map.get(qid)
                if not scaffold:
                    continue

                result = {**scaffold}
                result['question_id'] = mcq.question_id
                result['question'] = mcq.question_text
                result['answer'] = mcq.correct_answer
                result['difficulty'] = mcq.difficulty

                if hasattr(mcq, 'options') and mcq.options:
                    result['options'] = mcq.options
                    result['answer_choice'] = mcq.correct_answer_choice
                    result['type'] = 'mcq'
                else:
                    result['type'] = 'fill-in'

                combined.append(result)

            return images, combined

        images, generated_questions = await _orchestrate_dual_pipeline_execution()

        logger.info(f"⏱️  PARALLEL COMPLETE: All tasks finished ({time.time() - parallel_start:.2f}s)")

        self.question_images = {i: images[i] for i in range(len(images)) if images[i]}

        try:
            for i, generated_question in enumerate(generated_questions):
                if "type" not in generated_question:
                    generated_question["type"] = question_type
        except Exception as e:
            logger.warning(f"⚠️  Error setting question type: {e}")

        if Config.ENABLE_IMAGE_GENERATION and hasattr(self, 'question_images') and self.question_images:
            for i, generated_question in enumerate(generated_questions):
                if i in self.question_images and self.question_images[i]:
                    gemini_image = self.question_images[i].get('gemini')
                    if gemini_image:
                        generated_question['image_url'] = gemini_image

            image_count = len([q for q in generated_questions if q.get('image_url')])
            logger.info(f"🖼️  IMAGE INTEGRATION: Added URLs to {image_count} questions")
        elif Config.ENABLE_IMAGE_GENERATION:
            logger.warning(f"⚠️  IMAGE GEN: Enabled but no images available")

        if generated_questions:
            upload_params = {
                'grade': grade,
                'subject': subject,
                'difficulty': difficulty,
                'skill_title': skill_title,
                'language': language,
                'quantity': quantity,
                'question_type': question_type
            }
            upload_result = dev_uploader.upload_questions(generated_questions, upload_params)
            if upload_result.get('uploaded', 0) > 0:
                logger.info(f"💾 DEV UPLOAD: Saved {upload_result['uploaded']}/{upload_result['total']} questions to database")

        self._internal_log_dspy_performance_metrics()

        logger.info(f"🏁 PIPELINE COMPLETE: {len(generated_questions)} questions ready ({time.time() - start_time:.2f}s total)")

        return generated_questions

    def _internal_log_dspy_performance_metrics(self):
        """INTERNAL: Log DSPy performance metrics and cache statistics."""
        try:
            from src.dspy_improvements import cache_manager
            stats = cache_manager.stats()

            if stats['search']['hits'] + stats['search']['misses'] > 0:
                logger.info(f"📊 DSPY CACHE: Search {stats['search']['hit_rate']:.1%} hit rate "
                          f"({stats['search']['hits']}/{stats['search']['hits'] + stats['search']['misses']}), "
                          f"Rewrite {stats['rewrite']['hit_rate']:.1%} hit rate "
                          f"({stats['rewrite']['hits']}/{stats['rewrite']['hits'] + stats['rewrite']['misses']})")

            if hasattr(self.module_1.rag, 'stage_metrics') and self.module_1.rag.stage_metrics:
                for metric in self.module_1.rag.stage_metrics:
                    logger.info(f"📊 DSPY STAGE ({metric['stage']}): {metric['latency_ms']}ms, "
                              f"{metric['tokens_allocated']} tokens, "
                              f"{metric['tokens_utilization']:.1%} utilization")
        except Exception as e:
            logger.debug(f"⚠️  DSPy metrics unavailable: {e}")
    
    async def _internal_generate_images_with_agent(self, questions, grade: int, subject: str):
        """INTERNAL: Generate images using parallel image generation module."""
        if not Config.ENABLE_IMAGE_GENERATION:
            return []

        image_module = ImageGenModule()
        logger.info(f"🖼️  IMAGE GEN: Starting parallel generation for {len(questions)} questions")

        images = await image_module.generate_images_async(questions, grade, subject)

        formatted_images = []
        for img in images:
            if img and 'url' in img:
                formatted_images.append({'gemini': img['url']})
            else:
                formatted_images.append(None)

        self.question_images = {i: img for i, img in enumerate(formatted_images) if img}
        logger.info(f"🖼️  IMAGE GEN COMPLETE: Generated {len(self.question_images)} images")

        return formatted_images
