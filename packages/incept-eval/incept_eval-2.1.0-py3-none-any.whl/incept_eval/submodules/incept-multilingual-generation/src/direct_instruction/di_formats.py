from __future__ import annotations

import json
import os
import logging
import traceback
import time
from typing import List, Tuple, Optional, Dict, Any

from src.direct_instruction.types import (
    DIFormatsData,
    DIInsightsResponse,
    UsedDIFormat,
    SkillMappingResponse,
    PipelineState,
    ExtractInput,
    ExtractOutput,
    InsightsInput,
    InsightsOutput,
    DIScaffoldingInsights,
)
from src.direct_instruction.di_format_model import DiFormatModel
from src.llms import produce_structured_response_openai, format_messages_for_api
from src.direct_instruction.principles_constants import DI_SCAFFOLDING_PRINCIPLES, INSIGHTS_SYS, EXTRACT_STEPS_SYS
from src.dspy_rag import DSPyMongoRAG

logger = logging.getLogger(__name__)

class DiFormat():
    di_formats: DIFormatsData
    skills: List[str]
    rag: DSPyMongoRAG

    def __init__(self):
        data = self.load_di_formats()
        self.di_formats = DIFormatsData(**data)
        self.skills = list(self.di_formats.skills.keys())
        self.skill_mapping_cache = {}

        self.rag = DSPyMongoRAG(
            vector_store=None,
            db_name="chatter",
            collection_name="di_formats",
            index_name="di_formats_vector_index",
            text_key="text_content",
            embedding_key="vector",
            title_key="title",
            topic_key="skill_name",
            grade_key="grade",
        )

    def list_skills(self):
        return self.skills

    def get_formats_for_skill(self, skill_name: str):
        return self.di_formats.skills[skill_name].formats

    def get_formats_for_skill_grade(self, skill_name: str, grade: int):
        """Get formats for a specific skill that are assigned to a specific grade."""
        skill = self.di_formats.skills[skill_name]
        return [f for f in skill.formats if f.assigned_grade == grade]

    def get_progression_for_skill_grade(self, skill_name: str, grade: int):
        """Get progression items for a specific skill and grade."""
        skill = self.di_formats.skills[skill_name]
        if skill.progression:
            for prog in skill.progression:
                if prog.grade == grade:
                    return prog
        return None

    
    def map_skill_to_di(self, requested_skill: str, grade: int, question_text: Optional[str] = None) -> Tuple[bool, Optional[str], float]:
        """
        Use LLM to intelligently map requested skill to DI skill.
        Returns (is_mappable, di_skill_name, confidence)
        """
        # Check cache first
        cache_key = f"{requested_skill}_{grade}"
        if cache_key in self.skill_mapping_cache:
            return self.skill_mapping_cache[cache_key]
        
        question_context = f"\n\nQuestion context: {question_text}" if question_text else ""
        
        mapping_prompt = f"""
        You need to determine if the requested skill maps to one of the Direct Instruction skills.
        
        Requested skill: "{requested_skill}"
        Grade level: {grade}{question_context}
        
        Available Direct Instruction skills:
        {json.dumps(self.skills, indent=2)}
        
        IMPORTANT RULES:
        1. First, extract the main skill name from the requested skill (ignore formatting like "Skill: X, Unit: Y, Lesson: Z")
        2. If question context is provided, use it to clarify the specific skill (e.g., "Add 9 and 17" clearly indicates Addition)
        3. Only map if there's a STRONG, CLEAR connection between the extracted skill and a DI skill
        4. Do NOT force-fit mappings that are only vaguely related
        5. Consider the grade level - skills should be grade-appropriate
        6. If uncertain, return is_mappable=false
        
        Examples of skill extraction and mapping:
        - "Skill: Addition, Unit: Arithmetic, Lesson: Addition" → Extract "Addition" → Maps to "Addition"
        - "Addition problems" → Extract "Addition" → Maps to "Addition" 
        - "Adding numbers" → Extract "Addition" → Maps to "Addition"
        - "Fraction operations" → Extract "Fractions" → Maps to "Fractions"
        - "Skip counting" → Extract "Counting" → Maps to "Counting"
        
        Examples of BAD mappings (should return false):
        - "Quadratic equations" → Too advanced for DI content
        - "Calculus derivatives" → Not covered in DI skills
        - "Essay writing" → Different subject entirely
        - "Advanced trigonometry" → Too different from available skills
        
        First extract the core skill from the requested skill, then determine if it genuinely maps to a DI skill.
        Be conservative - only map skills that are clearly related.
        """
        
        try:
            response = produce_structured_response_openai(
                messages=format_messages_for_api(
                    system_message="You are an expert at curriculum mapping. Be conservative - only map skills that are clearly related.",
                    user_message=mapping_prompt
                ),
                model="gpt-4o",
                structure_model=SkillMappingResponse,
                instructions=None,
                temperature=1,
                max_output_tokens=None
            )
            
            
            result = (response.is_mappable, response.di_skill_name, response.confidence)
            
            # Only cache if we're confident
            if response.confidence > 0.7:
                self.skill_mapping_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            return (False, None, 0.0)
    
    def get_di_insights_for_scaffolding_rag(self, question_text: str, subject: str, grade: int) -> DIScaffoldingInsights:
        """Extract DI insights using vector search and use GPT-5 to generate relevant teaching steps for scaffolding."""
        try:
            # Map the subject/question to a DI skill first
            is_mappable, di_skill_name, confidence = self.map_skill_to_di(subject, grade, question_text)
            
            # Use vector search to find relevant formats
            with DiFormatModel() as model:
                # Search for formats relevant to the question and grade
                search_query = f"Grade {grade} {subject} {question_text}"
                
                # Use skill name if mapping was successful and confident
                skill_filter = di_skill_name if (is_mappable and di_skill_name and confidence > 0.5) else None
                
                vector_results = model.vector_search_formats(
                    search_query, 
                    limit=3, 
                    grade=grade, 
                    skill_name=skill_filter
                )
                
                # Found relevant formats
                
                if not vector_results:
                    # No relevant formats found
                    return DIScaffoldingInsights()
                
                # Extract relevant data from search results
                relevant_formats = []
                for result in vector_results:
                    if result.get('score', 0) > 0.5:  # Only use high-confidence matches
                        format_data = {
                            "title": result.get('title', 'Teaching Format'),
                            "skill_name": result.get('skill_name', ''),
                            "format_number": result.get('format_number', ''),
                            "score": result.get('score', 0),
                            "steps": []
                        }
                        
                        # Extract teaching steps from parts
                        if result.get('parts'):
                            for part in result['parts']:
                                if part.get('steps'):
                                    for step in part['steps']:
                                        if step.get('teacher_action'):
                                            format_data["steps"].append(step['teacher_action'])
                        
                        relevant_formats.append(format_data)
                
                if not relevant_formats:
                    # No high-confidence format matches found
                    return DIScaffoldingInsights()
                
                # Get pitfalls for the top-matching skill
                top_skill = relevant_formats[0]['skill_name']
                pitfalls = self.get_pitfalls_for_skill(top_skill) if top_skill else []
                
                # Prepare data for GPT-5 analysis
                analysis_data = {
                    "question": question_text,
                    "grade": grade,
                    "subject": subject,
                    "relevant_formats": relevant_formats,
                    "pitfalls": pitfalls[:4] if pitfalls else []  # Limit to top 4 pitfalls
                }
                
                # Use GPT-5 to generate relevant teaching insights
                analysis_prompt = f"""
                You are a Direct Instruction pedagogy expert. Based on the following DI formats and data, generate the most relevant teaching guidance for this specific question.

                QUESTION: {question_text}
                GRADE: {grade}
                SUBJECT: {subject}

                DIRECT INSTRUCTION DATA:
                {json.dumps(analysis_data, indent=2)}

                TASK: Generate concise, actionable teaching insights that directly apply to this question. Focus on:
                1. Most relevant teaching steps from the formats
                2. Key pitfalls to avoid for this specific problem
                3. Specific guidance for scaffolding this concept

                REQUIREMENTS:
                - Only include insights that directly relate to the question
                - Keep each point under 100 characters
                - Maximum 3 total insights
                - If no relevant insights exist, return "NONE"
                - IMPORTANT: In the 'formats_used' field, list the exact format numbers and titles that you actually referenced to generate your insights. Only include formats you actually used.
                - CRITICAL: For each format used, specify the exact step numbers (1-indexed) and step text that you referenced. Look at the "steps" array in each format and identify which specific steps influenced your insights.

                CRITICAL:
                - The insights should be in the form of 3 sequential stepwise hintes towards finding the answer
                - They should NEVER reveal the actual answer, or partial answers

                FORMAT: Return insights as a simple list, one per line, starting with "- "
                """
                
                # Sending analysis to GPT-5
                gpt5_start = time.time()
                logger.info(f"⏱️ DI FORMAT: Starting GPT-5 analysis for DI insights")

                response = produce_structured_response_openai(
                    messages=format_messages_for_api(
                        system_message=analysis_prompt
                    ),
                    structure_model=DIInsightsResponse,
                    model="gpt-4o",
                    instructions=None,
                    temperature=1,
                    max_output_tokens=None
                )

                # response = produce_structured_response_gemini(
                #     prompt=analysis_prompt,
                #     structure_model=DIInsightsResponse,
                #     llm_model="gemini-2.5-flash"
                # )

                gpt5_time = time.time() - gpt5_start
                logger.info(f"⏱️ DI FORMAT: GPT-5 analysis took {gpt5_time:.2f}s")
                # GPT-5 analysis completed
                
                if response and response.has_relevant_insights and response.insights:
                    # Format insights as bullet points
                    formatted_insights = "\n".join([f"- {insight}" for insight in response.insights])
                    
                    insights_section = f"""DIRECT INSTRUCTION PEDAGOGICAL INSIGHTS
                        Follow these proven DI principles when creating the detailed_explanation steps but NEVER revealing the answer:
                        {DI_SCAFFOLDING_PRINCIPLES}
                        {formatted_insights}
                    """
                    
                    # Filter source formats to only include what GPT-5 said it used with specific steps
                    actually_used_formats = []
                    if response.formats_used:
                        for used_fmt in response.formats_used:
                            # Find the matching format from relevant_formats
                            for orig_fmt in relevant_formats:
                                if (orig_fmt.get('format_number') == used_fmt.format_number or 
                                    orig_fmt.get('title') == used_fmt.title):
                                    # Create a copy with specific step information
                                    format_with_steps = orig_fmt.copy()
                                    format_with_steps['step_numbers_used'] = used_fmt.step_numbers_used
                                    format_with_steps['steps_used'] = used_fmt.steps_used
                                    actually_used_formats.append(format_with_steps)
                                    break
                    
                    # If GPT-5 didn't specify formats used, include all relevant ones
                    if not actually_used_formats:
                        actually_used_formats = relevant_formats
                    
                    # Generated insights
                    return DIScaffoldingInsights(
                        insights_text=insights_section,
                        source_formats=actually_used_formats
                    )
                else:
                    # No relevant insights found
                    return DIScaffoldingInsights()
            
        except Exception as e:
            logger.error(f"[DI INSIGHTS] Failed to get DI insights for {subject} Grade {grade}: {e}")
            logger.error(f"[DI INSIGHTS] Traceback: {traceback.format_exc()}")
            return DIScaffoldingInsights()


    def get_di_insights_for_scaffolding_dspy(self, question_text: str, subject: str, grade: int) -> DIScaffoldingInsights:
        """
        End-to-end pipeline (map → retrieve → extract → insights) in one function.
        - Hard-coded MongoDB Atlas Vector Search params for chatter.di_formats.
        - Returns your original formatted DI insights block (or "" if none).

        Args:
            question_text: the specific student question/prompt
            subject: requested skill/topic string (e.g., "Addition")
            grade: integer grade

        Returns:
            str: Formatted DI insights section (or "" if nothing relevant).
        """

        # -----------------------------
        # Build optimized grouped stages
        # -----------------------------

        # Snapshot holder to mirror Module 1 flow
        _snapshots: Dict[str, Any] = {}

        # STAGE 1: Map skill and merge in one step (PipelineState → PipelineState)
        def _map_and_merge(state: PipelineState) -> PipelineState:
            # Store initial state
            _snapshots["pre_map"] = state

            # Create map output manually using the same logic
            mapping_prompt = f"""
            You need to determine if the requested skill maps to one of the Direct Instruction skills.

            Requested skill: "{state.subject}"
            Grade level: {state.grade}
            Question context: {state.question}

            Available Direct Instruction skills:
            {json.dumps(state.available_skills, indent=2)}

            IMPORTANT RULES:
            1. First, extract the main skill name from the requested skill (ignore formatting like "Skill: X, Unit: Y, Lesson: Z")
            2. If question context is provided, use it to clarify the specific skill (e.g., "Add 9 and 17" clearly indicates Addition)
            3. Only map if there's a STRONG, CLEAR connection between the extracted skill and a DI skill
            4. Do NOT force-fit mappings that are only vaguely related
            5. Consider the grade level - skills should be grade-appropriate
            6. If uncertain, return is_mappable=false

            First extract the core skill from the requested skill, then determine if it genuinely maps to a DI skill.
            Be conservative - only map skills that are clearly related.
            """

            try:
                response = produce_structured_response_openai(
                    messages=format_messages_for_api(
                        system_message="You are an expert at curriculum mapping. Be conservative - only map skills that are clearly related.",
                        user_message=mapping_prompt
                    ),
                    model="gpt-5",
                    structure_model=SkillMappingResponse,
                    instructions=None,
                    temperature=1,
                    max_output_tokens=None
                )

                state.mapping = {
                    "is_mappable": response.is_mappable,
                    "di_skill_name": response.di_skill_name,
                    "confidence": response.confidence,
                    "reasoning": getattr(response, 'reasoning', '')
                }
            except Exception as e:
                state.mapping = {
                    "is_mappable": False,
                    "di_skill_name": None,
                    "confidence": 0.0,
                    "reasoning": f"Error during mapping: {str(e)}"
                }

            _snapshots["after_map_state"] = state
            return state

        stage_map_combined = DSPyMongoRAG.StageSpec(
            name="map_skill_combined",
            input_model=PipelineState,
            output_model=PipelineState,
            sys_instructions="(combined mapping stage; internal LLM call)",
            retrieval=None,
            rounds=0,
            deterministic=True,
            compute=_map_and_merge,
        )

        # STAGE 2: Combined retrieval pipeline (PipelineState → PipelineState)
        def _retrieve_combined(state: PipelineState) -> PipelineState:
            _snapshots["after_map_state"] = state

            # Build retrieval query
            query = f"Grade {state.grade} {state.subject} {state.question}"

            # Perform retrieval using the RAG system
            try:
                retrieval_input = DSPyMongoRAG.RetrievalInput(question=query, grade=state.grade)

                # Use the existing stage_retrieve logic
                stage_retrieve = self.rag.stage_retrieve(
                    k=3,
                    filters={},
                    query_field="question",
                    rewrite=True,
                    rewrite_instructions="Rewrite the question into a short retrieval query including grade, subject, and key task cues.",
                    deterministic=True,
                )

                # Run retrieval
                selected_passages = self.rag.run(stages=[stage_retrieve], initial_input=retrieval_input)

                # Merge results back into state
                if isinstance(selected_passages, DSPyMongoRAG.SelectedPassages):
                    state.passages = selected_passages.passages or ""
                    state.doc_ids = selected_passages.doc_ids or []
                elif hasattr(selected_passages, 'passages'):
                    state.passages = getattr(selected_passages, 'passages', "")
                    state.doc_ids = getattr(selected_passages, 'doc_ids', [])
                else:
                    state.passages = ""
                    state.doc_ids = []

            except Exception as e:
                logger.warning(f"Retrieval failed: {e}")
                state.passages = ""
                state.doc_ids = []

            _snapshots["after_retrieve_state"] = state
            return state

        stage_retrieve_combined = DSPyMongoRAG.StageSpec(
            name="retrieve_combined",
            input_model=PipelineState,
            output_model=PipelineState,
            sys_instructions="(combined retrieval stage; internal retrieval)",
            retrieval=None,
            rounds=0,
            deterministic=True,
            compute=_retrieve_combined,
        )

        # STAGE 3: Combined extraction pipeline (PipelineState → PipelineState)
        def _extract_combined(state: PipelineState) -> PipelineState:
            _snapshots["before_extract_state"] = state

            # Build extraction input
            extract_input = ExtractInput(question=state.question, passages=state.passages)

            try:
                # Run extraction using existing stage logic
                extract_output = produce_structured_response_openai(
                    messages=format_messages_for_api(
                        system_message=EXTRACT_STEPS_SYS,
                        user_message=f"Question: {extract_input.question}\nPassages: {extract_input.passages}"
                    ),
                    model="gpt-5",
                    structure_model=ExtractOutput,
                    instructions=None,
                    temperature=1,
                    max_output_tokens=None
                )

                state.extracted_formats = extract_output.extracted_formats or []
            except Exception as e:
                logger.warning(f"Extraction failed: {e}")
                state.extracted_formats = []

            _snapshots["after_extract_state"] = state
            return state

        stage_extract_combined = DSPyMongoRAG.StageSpec(
            name="extract_combined",
            input_model=PipelineState,
            output_model=PipelineState,
            sys_instructions="(combined extraction stage; internal LLM call)",
            retrieval=None,
            rounds=0,
            deterministic=True,
            compute=_extract_combined,
        )

        # STAGE 4: Combined insights pipeline (PipelineState → PipelineState)
        def _insights_combined(state: PipelineState) -> PipelineState:
            # Compute pitfalls
            if state.extracted_formats:
                top_skill = (state.extracted_formats[0].skill_name or "").strip()
                state.pitfalls = self.get_pitfalls_for_skill(top_skill)[:4]
            else:
                state.pitfalls = []

            # Build insights input
            insights_input = InsightsInput(
                question=state.question,
                grade=state.grade,
                subject=state.subject,
                extracted_formats=state.extracted_formats,
                pitfalls=state.pitfalls or [],
            )
            _snapshots["before_insights_state"] = state

            try:
                # Run insights generation
                insights_output = produce_structured_response_openai(
                    messages=format_messages_for_api(
                        system_message=INSIGHTS_SYS,
                        user_message=f"Question: {insights_input.question}\nGrade: {insights_input.grade}\nSubject: {insights_input.subject}\nExtracted Formats: {json.dumps([f.model_dump() for f in insights_input.extracted_formats], indent=2)}\nPitfalls: {insights_input.pitfalls}"
                    ),
                    model="gpt-5",
                    structure_model=InsightsOutput,
                    instructions=None,
                    temperature=1,
                    max_output_tokens=None
                )

                state.insights = insights_output.insights or []
                state.has_relevant_insights = bool(insights_output.has_relevant_insights)
            except Exception as e:
                logger.warning(f"Insights generation failed: {e}")
                state.insights = []
                state.has_relevant_insights = False

            return state

        stage_insights_combined = DSPyMongoRAG.StageSpec(
            name="insights_combined",
            input_model=PipelineState,
            output_model=PipelineState,
            sys_instructions="(combined insights stage; internal LLM call)",
            retrieval=None,
            rounds=0,
            deterministic=True,
            compute=_insights_combined,
        )

        # Reduced from 12 stages to 4 grouped stages
        stages: List[DSPyMongoRAG.StageSpec] = [
            stage_map_combined,
            stage_retrieve_combined,
            stage_extract_combined,
            stage_insights_combined,
        ]

        # ===== Single run =====
        initial_state = PipelineState(
            question=question_text,
            subject=subject,
            grade=grade,
            available_skills=self.skills
        )
        _snapshots["pre_map"] = initial_state
        final_state = self.rag.run(stages=stages, initial_input=initial_state)

        # If the RAG returned a FinalAnswer error wrapper, bail out gracefully
        if isinstance(final_state, DSPyMongoRAG.FinalAnswer):
            if str(final_state.answer).lower().startswith("error:"):
                logger.error(f"[DI INSIGHTS] Pipeline failed: {final_state.answer}")
                return DIScaffoldingInsights()
        # ===== Post-formatting (same output style you expect) =====
        try:
            out = final_state if isinstance(final_state, PipelineState) else PipelineState.model_validate(final_state.model_dump())
        except Exception:
            logger.error(f"[DI INSIGHTS] Failed to post-format insights for {subject} Grade {grade}: Traceback: {traceback.format_exc()}")
            return DIScaffoldingInsights()

        hints = (out.insights or [])[:3]
        hints = [h[:100] for h in hints]
        if not hints:
            logger.error(f"[DI INSIGHTS] No hints found for {subject} Grade {grade}")
            return DIScaffoldingInsights()

        # Final formatted section (matches your original)
        formatted = "\n".join([f"- {s}" for s in hints])
        section = (
            "DIRECT INSTRUCTION PEDAGOGICAL INSIGHTS\n"
            "Follow these proven DI principles when creating the detailed_explanation steps but NEVER revealing the answer:\n"
            f"{DI_SCAFFOLDING_PRINCIPLES}"
            f"{formatted}\n"
        )

        # Extract source formats from the pipeline state
        source_formats = []
        if out.extracted_formats:
            for fmt in out.extracted_formats:
                source_formats.append({
                    "title": fmt.title,
                    "skill_name": fmt.skill_name,
                    "format_number": fmt.format_number,
                    "steps": fmt.steps
                })

        return DIScaffoldingInsights(
            insights_text=section,
            source_formats=source_formats
        )

    def get_di_insights_for_scaffolding(self, question_text: str, subject: str, grade: int, type: str = "rag") -> DIScaffoldingInsights:
        if type == "rag":
            return self.get_di_insights_for_scaffolding_rag(question_text, subject, grade)
        elif type == "dspy":
            return self.get_di_insights_for_scaffolding_dspy(question_text, subject, grade)
        else:
            insights_text = (
                "DIRECT INSTRUCTION PEDAGOGICAL INSIGHTS\n"
                "Follow these proven DI principles when creating the detailed_explanation steps but NEVER revealing the answer:\n"
                f"{DI_SCAFFOLDING_PRINCIPLES}"
            )
            return DIScaffoldingInsights(insights_text=insights_text)
    


    def load_di_formats(self):
        """Load the Direct Instruction formats from edu_configs."""
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(os.path.dirname(current_dir))
        json_path = os.path.join(project_root, "edu_configs", "di_formats.json")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_pitfalls_for_skill(self, skill_name: str) -> List[str]:
        if not skill_name:
            return []
        try:
            skill = self.di_formats.skills.get(skill_name)
            if not skill:
                return []
            return list(skill.pitfalls or [])
        except Exception:
            return []



