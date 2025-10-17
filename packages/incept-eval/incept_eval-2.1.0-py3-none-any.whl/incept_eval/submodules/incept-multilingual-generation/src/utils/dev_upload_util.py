#!/usr/bin/env python3
"""
Development Upload Utility
Uploads generated questions to uae_educational_questions_cleaned_duplicate table in development mode only.
"""

import os
import logging
import psycopg2
import json
import uuid
import hashlib
import random
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class DevQuestionUploader:
    """
    Uploads generated questions to the database in development mode only.
    IMPORTANT: Only works when ENVIRONMENT=development or DEV_MODE=true
    """
    
    def __init__(self):
        self.POSTGRES_URI = os.getenv('POSTGRES_URI')

    def upload_questions(
        self, 
        questions: List[Any], 
        generation_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Upload generated questions to database (development mode only).
        
        Args:
            questions: List of generated questions (MCQ or complete questions)
            generation_params: Parameters used for generation (grade, subject, etc.)
            
        Returns:
            Dict with upload results
        """
        
        if not questions:
            logger.warning("🚫 DEV UPLOAD SKIPPED: No questions to upload")
            return {"uploaded": 0, "skipped": "no_questions"}
        
        try:
            logger.info(f"🔧 DEV UPLOAD START: Uploading {len(questions)} questions")
            
            conn = psycopg2.connect(self.POSTGRES_URI)
            cur = conn.cursor()
            
            uploaded_count = 0
            errors = []
            
            # Prepare all question data first
            valid_questions = []
            for i, question in enumerate(questions):
                try:
                    question_data = self._extract_question_data(question, generation_params)
                    if question_data:
                        valid_questions.append((i+1, question_data))
                    else:
                        logger.warning(f"  ⚠️ Q{i+1}: Could not extract data, skipping")
                except Exception as e:
                    error_msg = f"Q{i+1}: {type(e).__name__}: {e}"
                    errors.append(error_msg)
                    logger.warning(f"  ❌ Data extraction failed: {error_msg}")
            
            # Batch insert valid questions
            if valid_questions:
                try:
                    # Use execute_values for efficient batch insertion
                    from psycopg2.extras import execute_values

                    # Get the starting ID (max existing ID or 20000)
                    cur.execute("SELECT COALESCE(MAX(id), 19999) FROM uae_educational_questions_cleaned_duplicate WHERE id >= 20000")
                    start_id = cur.fetchone()[0] + 1

                    insert_query = """
                        INSERT INTO uae_educational_questions_cleaned_duplicate (
                            id, grade_level, subject_area, broad_topic, subtopic, textbook_name,
                            question_text, question_text_arabic, question_type, difficulty_level,
                            correct_answer, answer_explanation, language, quality_score,
                            extracted_by_model, extraction_confidence, human_verified, normalized_grade,
                            created_at, updated_at, scaffolding, options, di_formats_used, generation_params
                        ) VALUES %s
                    """

                    template = """(
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )"""

                    # Prepare values for batch insert
                    from datetime import datetime
                    current_time = datetime.now()

                    values = []
                    for idx, (q_num, q_data) in enumerate(valid_questions):
                        values.append((
                            start_id + idx,  # Generate sequential IDs starting from 20000+
                            q_data['grade_level'], q_data['subject_area'], q_data['broad_topic'],
                            q_data['subtopic'], q_data['textbook_name'], q_data['question_text'],
                            q_data['question_text_arabic'], q_data['question_type'], q_data['difficulty_level'],
                            q_data['correct_answer'], q_data['answer_explanation'], q_data['language'],
                            q_data['quality_score'], q_data['extracted_by_model'], q_data['extraction_confidence'],
                            q_data['human_verified'], q_data['normalized_grade'], current_time, current_time,
                            psycopg2.extras.Json(q_data['scaffolding']),
                            psycopg2.extras.Json(q_data['options']),
                            psycopg2.extras.Json(q_data.get('di_formats_used')),
                            psycopg2.extras.Json(q_data.get('generation_params'))
                        ))

                    execute_values(cur, insert_query, values, template=template, page_size=100)
                    conn.commit()
                    uploaded_count = len(valid_questions)
                    logger.info(f"  ✅ Batch uploaded {uploaded_count} questions successfully")
                    
                except Exception as e:
                    conn.rollback()
                    error_msg = f"Batch insert failed: {type(e).__name__}: {e}"
                    errors.append(error_msg)
                    logger.error(f"  ❌ {error_msg}")
                    uploaded_count = 0
            cur.close()
            conn.close()
            
            result = {
                "uploaded": uploaded_count,
                "total": len(questions),
                "success_rate": f"{uploaded_count/len(questions)*100:.1f}%",
                "errors": errors[:5] if errors else None  # Show first 5 errors only
            }
            
            logger.info(f"🔧 DEV UPLOAD COMPLETE: {uploaded_count}/{len(questions)} uploaded ({result['success_rate']})")
            if errors:
                logger.warning(f"🔧 DEV UPLOAD ERRORS: {len(errors)} questions failed")
                
            return result
            
        except Exception as e:
            logger.error(f"🔧 DEV UPLOAD FAILED: {type(e).__name__}: {e}")
            return {"uploaded": 0, "error": str(e)}
    
    def _extract_question_data(self, question: Any, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract question data for database insertion"""
        try:
            question_text = question["question"]
            correct_answer = question["answer"]
            explanation = question["explanation"]
            difficulty = question["difficulty"]
            scaffolding = question["detailed_explanation"]["steps"]
            generator = params.get("generator", "orchestrator-pipeline") # or prompt-engineering-openai
            options = question["options"]
            di_formats_used = question.get("di_formats_used")  # Extract DI formats if present

            # Build question data for insertion
            question_data = {
                'grade_level': str(params.get('grade', '')),
                'subject_area': params.get('subject', 'Generated'),
                'broad_topic': params.get('skill_title', 'AI Generated'),
                'subtopic': params.get('skill_title', 'Generated Question'),
                'textbook_name': 'AI Generated - Development Upload',
                'question_text': question_text,
                'question_text_arabic': question_text if params.get('language') == 'arabic' else None,
                'question_type': 'mcq' if question['options'] else 'fill-in',
                'difficulty_level': difficulty,
                'correct_answer': correct_answer,
                'answer_explanation': explanation,
                'scaffolding': scaffolding,
                'options': options,
                'di_formats_used': di_formats_used,  # Include DI formats
                'language': 'ar' if params.get('language') == 'arabic' else 'en',
                'quality_score': 0.5,  # Conservative quality score for generated questions
                'extracted_by_model': generator,
                'extraction_confidence': 0.9,
                'human_verified': False,
                'normalized_grade': int(params.get('grade', 1)) if str(params.get('grade', '')).isdigit() else 1
            }

            return question_data

        except Exception as e:
            logger.error(f"Error extracting question data: {e}")
            return None

def retrieve_patterns_and_samples_psql(
    grade: int,
    subject: str,
    quantity: int,
    skill_title: Optional[str],
    language: str,
) -> Dict[str, Any]:
    """
    Simplified PostgreSQL retriever:
      • Partially matches skill_title (ILIKE)
      • 100% match on subject, grade, and language (ar or en)
      • Returns patterns and samples

    Returns:
        {
          "patterns": List[Dict[str, Any]],
          "samples":  List[Dict[str, Any]],
        }
    """
    from dataclasses import dataclass
    import os
    import re
    import logging
    from typing import List, Dict, Any, Optional
    import psycopg2

    logger = logging.getLogger(__name__)

    @dataclass
    class RetrievedSample:
        """Local RetrievedSample definition to avoid circular import."""
        question_text: str
        subject_area: str = ""
        grade: int = 1
        topic: str = ""
        difficulty: str = "medium"
        language: str = "english"
        answer: str = ""
        explanation: str = ""
        source: str = "PostgreSQL"

    def _generalize_question(q: str) -> str:
        """Replace numbers, names, units, and places with placeholders"""
        g = re.sub(r"\b\d+(?:[\.,]\d+)?\b", "[NUMBER]", q or "")
        names = [
            "ahmed","mohammed","mohammad","fatima","ali","sara","omar","layla","hassan",
            "أحمد","محمد","فاطمة","علي","سارة","عمر","ليلى","حسن","عائشة","زينب","خديجة"
        ]
        for n in names:
            g = re.sub(rf"\b{re.escape(n)}\b", "[NAME]", g, flags=re.IGNORECASE)
        units = [
            "meter","meters","kilogram","kilograms","liter","litre","liters","dirham","dollar",
            "year","day","hour","minute","second",
            "متر","كيلوغرام","لتر","درهم","دينار","ريال","سنة","يوم","ساعة","دقيقة","ثانية"
        ]
        for u in units:
            g = re.sub(rf"\b{re.escape(u)}\b", "[UNIT]", g, flags=re.IGNORECASE)
        places = ["dubai","abu dhabi","sharjah","دبي","أبوظبي","الشارقة"]
        for p in places:
            g = re.sub(rf"\b{re.escape(p)}\b", "[PLACE]", g, flags=re.IGNORECASE)
        return g

    max_each = min(20, max(1, int(quantity or 20)))
    samples = []
    patterns: List[Dict[str, Any]] = []

    try:
        postgres_uri = os.getenv("POSTGRES_URI")
        if not postgres_uri:
            raise ValueError("POSTGRES_URI environment variable not set")

        conn = psycopg2.connect(postgres_uri)
        cur = conn.cursor()

        # Map language to database format
        lang_code = 'ar' if (language or "").lower() in ['arabic', 'ar'] else 'en'

        # Choose question field based on language
        question_field = (
            "question_text_arabic" if lang_code == 'ar'
            else "question_text"
        )

        # Build skill pattern for partial matching
        skill_pattern = f"%{skill_title}%" if skill_title else "%"

        query = f"""
            WITH base AS (
                SELECT
                    {question_field}                                  AS question_text,
                    COALESCE(subject_area, %s)                        AS subject_area,
                    COALESCE(normalized_grade, %s)                    AS normalized_grade,
                    COALESCE(subtopic, broad_topic, 'general')        AS topic,
                    COALESCE(subtopic, '')                            AS subtopic_raw,
                    COALESCE(broad_topic, '')                         AS broad_topic_raw,
                    COALESCE(difficulty_level, 'medium')              AS difficulty,
                    COALESCE(language, %s)                            AS lang,
                    correct_answer,
                    answer_explanation,
                    -- Quality signals
                    (CASE WHEN correct_answer IS NOT NULL AND correct_answer <> '' THEN 3 ELSE 0 END +
                     CASE WHEN answer_explanation IS NOT NULL AND LENGTH(answer_explanation) > 20 THEN 2 ELSE 0 END +
                     CASE WHEN subtopic IS NOT NULL THEN 1 ELSE 0 END +
                     CASE WHEN difficulty_level IS NOT NULL THEN 1 ELSE 0 END +
                     CASE WHEN LENGTH({question_field}) > 20 THEN 1 ELSE 0 END) AS quality_score,
                    GREATEST(0, 3 - ABS(COALESCE(normalized_grade, %s) - %s))       AS grade_score,
                    CASE WHEN (subject_area ILIKE %s OR broad_topic ILIKE %s) THEN 2 ELSE 0 END AS subject_score,
                    LENGTH({question_field})                           AS qlen
                FROM uae_educational_questions_cleaned_duplicate
                WHERE {question_field} IS NOT NULL
                  AND (subject_area ILIKE %s OR broad_topic ILIKE %s)
                  AND COALESCE(normalized_grade, %s) BETWEEN %s AND %s
                  AND (%s = '' OR
                       COALESCE(subtopic,'')   ILIKE ANY(%s) OR
                       COALESCE(broad_topic,'') ILIKE ANY(%s) OR
                       {question_field}        ILIKE ANY(%s)
                  )
                  AND correct_answer IS NOT NULL AND correct_answer <> ''  -- ensure solvable
            ),
            ranked AS (
                SELECT *,
                       (quality_score*1.5 + grade_score + subject_score + (qlen/400.0)) AS pre_rank
                FROM base
            )
            SELECT question_text, subject_area, normalized_grade, topic, subtopic_raw, broad_topic_raw,
                   difficulty, lang, correct_answer, answer_explanation, pre_rank
            FROM ranked
            ORDER BY pre_rank DESC, RANDOM()
            LIMIT %s;
        """

        cur.execute(
            query,
            (
                subject,          # %s in COALESCE(subject_area, %s)
                grade,            # %s in COALESCE(normalized_grade, %s)
                lang_code,        # %s in COALESCE(language, %s)
                grade,            # %s in COALESCE(normalized_grade, %s)
                grade,            # %s in ABS(COALESCE(normalized_grade, %s) - %s)
                skill_pattern,    # %s in subject_area ILIKE %s
                skill_pattern,    # %s in broad_topic ILIKE %s
                skill_pattern,    # %s in subject_area ILIKE %s
                skill_pattern,    # %s in broad_topic ILIKE %s
                grade,            # %s in COALESCE(normalized_grade, %s) BETWEEN
                grade - 1,        # %s lower bound
                grade + 1,        # %s upper bound
                skill_title or '',  # %s = ''
                [f"%{skill_title}%"] if skill_title else ['%'],  # %s in ILIKE ANY(%s)
                [f"%{skill_title}%"] if skill_title else ['%'],  # %s in ILIKE ANY(%s)
                [f"%{skill_title}%"] if skill_title else ['%'],  # %s in ILIKE ANY(%s)
                max_each * 2,     # LIMIT %s
            ),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Build samples and patterns from results
        seen_q: set = set()
        pattern_seen: set = set()

        for (q_text, subj_area, norm_grade, topic, subtopic_raw, broad_topic_raw, diff, lang, answer, explanation, pre_rank) in rows:
            if not q_text:
                continue

            # Add to samples
            if len(samples) < max_each and q_text not in seen_q:
                samples.append(
                    RetrievedSample(
                        question_text=q_text,
                        subject_area=subj_area,
                        grade=int(norm_grade),
                        topic=topic,
                        difficulty=diff,
                        language=lang_code,
                        answer=answer or "",
                        explanation=explanation or "",
                        source="PostgreSQL",
                    )
                )
                seen_q.add(q_text)

            # Add to patterns
            if len(patterns) < max_each:
                tmpl = _generalize_question(q_text)
                if len(tmpl) >= 20 and tmpl not in pattern_seen:
                    patterns.append(
                        {
                            "pattern_id": f"psql_pattern_{len(patterns)+1}",
                            "template": tmpl,
                            "topic": topic,
                            "difficulty": diff,
                            "language": lang_code,
                            "subject_area": subj_area,
                            "example": q_text,
                            "source": "postgresql_examples",
                            "source_context": topic,
                        }
                    )
                    pattern_seen.add(tmpl)

        return {"patterns": patterns, "samples": samples}

    except Exception as e:
        logger.error(f"retrieve_patterns_and_samples_psql error: {type(e).__name__}: {e}")
        return {"patterns": patterns, "samples": samples}


def retrieve_existing_questions_for_mixing(
    grade: int,
    subject: str,
    quantity_needed: int,
    skill_title: Optional[str],
    language: str,
    provider: str = "falcon",
    partial_match_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Retrieve existing questions from database for mixing with generated questions.

    Strategy:
    1. Pull ~100 questions from DB (can be similar to each other)
    2. Deduplicate deterministically to ~50 unique questions
    3. Use Falcon LLM to evaluate and select best X questions
    4. Return selected questions

    Args:
        grade: Grade level (100% match)
        subject: Subject area (100% match)
        quantity_needed: How many questions we need from DB
        skill_title: Skill to partially match against
        language: Language for questions
        provider: LLM provider for filtering (default: falcon)
        partial_match_threshold: Not used anymore, kept for API compatibility

    Returns:
        List of question dicts ready for Module 4 (with answers already validated)
    """
    from difflib import SequenceMatcher
    import hashlib

    # Pull 100 questions for initial pool
    pull_quantity = 100

    if quantity_needed == 0:
        return []

    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        logger.warning("POSTGRES_URI not set, skipping DB retrieval")
        return []

    try:
        conn = psycopg2.connect(postgres_uri)
        cur = conn.cursor()

        # Map language
        lang_code = 'ar' if language.lower() in ['arabic', 'ar'] else 'en'
        question_field = "question_text_arabic" if lang_code == 'ar' else "question_text"

        # Step 1: Pull ~100 questions from DB
        query = f"""
            SELECT
                {question_field} AS question_text,
                subject_area,
                normalized_grade,
                broad_topic,
                subtopic,
                difficulty_level,
                correct_answer,
                answer_explanation,
                question_type,
                options
            FROM uae_educational_questions_cleaned_duplicate
            WHERE {question_field} IS NOT NULL
              AND subject_area = %s
              AND normalized_grade = %s
              AND correct_answer IS NOT NULL
              AND correct_answer <> ''
              AND language = %s
            ORDER BY RANDOM()
            LIMIT %s;
        """

        cur.execute(query, (subject, grade, lang_code, pull_quantity))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        if not rows:
            logger.info(f"No existing questions found for {subject} grade {grade}")
            return []

        logger.info(f"📥 Step 1: Retrieved {len(rows)} questions from DB")

        # Step 2: Deterministic deduplication to ~50 unique questions
        seen_hashes = set()
        unique_questions = []

        for row in rows:
            (q_text, subj, norm_grade, broad_topic, subtopic,
             difficulty, answer, explanation, q_type, options) = row

            # Create deterministic hash from question text (normalized)
            normalized_text = ' '.join(q_text.lower().split())  # Normalize whitespace
            question_hash = hashlib.md5(normalized_text.encode()).hexdigest()

            if question_hash not in seen_hashes:
                seen_hashes.add(question_hash)
                unique_questions.append({
                    'question_text': q_text,
                    'subject_area': subj,
                    'grade': int(norm_grade),
                    'broad_topic': broad_topic,
                    'subtopic': subtopic,
                    'difficulty': difficulty or 'medium',
                    'answer': answer,
                    'explanation': explanation or '',
                    'question_type': q_type,
                    'options': options,
                    'language': language
                })

                # Stop at 50 unique questions
                if len(unique_questions) >= 30:
                    break

        logger.info(f"🔍 Step 2: Deduplicated to {len(unique_questions)} unique questions")

        if not unique_questions:
            return []

        # Step 3: Use Falcon LLM to select best questions for the skill
        selected_questions = _llm_select_best_questions(
            unique_questions,
            skill_title,
            quantity_needed,
            provider
        )

        logger.info(f"✅ Step 3: LLM selected {len(selected_questions)} best questions for skill")

        return selected_questions

    except Exception as e:
        logger.error(f"retrieve_existing_questions_for_mixing error: {e}")
        return []


def _llm_select_best_questions(
    questions: List[Dict[str, Any]],
    skill_title: str,
    quantity_needed: int,
    provider: str
) -> List[Dict[str, Any]]:
    """
    Use Falcon LLM to evaluate and select the best questions for a skill.

    Args:
        questions: List of unique candidate questions
        skill_title: The skill to match against
        quantity_needed: Target number of questions to select
        provider: LLM provider to use (default: falcon)

    Returns:
        Selected list of best questions for the skill
    """
    from src.llms import solve_with_llm, format_messages_for_api
    from src.utils.json_repair import parse_json

    if not questions:
        return []

    # If we have fewer questions than needed, return all
    if len(questions) <= quantity_needed:
        return questions

    # Prepare question list for LLM evaluation
    question_summaries = []
    for idx, q in enumerate(questions):
        q_text = q['question_text']
        topic = q.get('broad_topic', '') or q.get('subtopic', '')
        question_summaries.append(f"{idx}: [{topic}] {q_text}")

    system_prompt = f"""You are an expert educational content evaluator for grade-level mathematics.
Your task: Select the {quantity_needed} BEST questions from the list that are most appropriate for practicing the skill: "{skill_title}".

Criteria for selection:
1. Direct relevance to the skill/topic
2. Variety in difficulty and approach
3. Clear, well-structured questions
4. Appropriate for the grade level

Return ONLY a JSON object with selected question indexes:
{{"selected_indexes": [0, 5, 12, ...]}}"""

    user_prompt = f"""Target Skill: {skill_title}
Number to Select: {quantity_needed}

Available Questions (index: [topic] question_preview):
{chr(10).join(question_summaries)}

Analyze these questions and select the {quantity_needed} best ones that match the skill.
Return format: {{"selected_indexes": [...]}}"""

    try:
        response = solve_with_llm(
            messages=format_messages_for_api(system_prompt, user_prompt),
            max_tokens=2000,
            provider=provider,
            temperature=0.2
        )

        # Parse response
        if isinstance(response, str):
            result = parse_json(response)
        else:
            result = response

        selected_indexes = result.get('selected_indexes', []) if result else []

        # Filter questions by selected indexes
        selected = [questions[idx] for idx in selected_indexes if 0 <= idx < len(questions)]

        # If we got fewer than needed, fill up to quantity_needed
        if len(selected) < quantity_needed:
            logger.warning(f"LLM selected only {len(selected)}/{quantity_needed} questions, filling with top candidates")
            # Add remaining questions that weren't selected
            remaining = [q for i, q in enumerate(questions) if i not in selected_indexes]
            selected.extend(remaining[:quantity_needed - len(selected)])

        return selected[:quantity_needed]

    except Exception as e:
        logger.warning(f"LLM selection failed: {e}, returning first {quantity_needed} questions")
        return questions[:quantity_needed]


# Global instance for easy importing
dev_uploader = DevQuestionUploader()