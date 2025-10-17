#!/usr/bin/env python3
"""
Module 0: Database Question Retrieval

Fetches existing questions from the database based on specified criteria.
This module runs independently and feeds both Pipeline A and Pipeline B.
"""

import logging
import uuid
from typing import List
from src.question_gen_v1.module_2 import GeneratedQuestion

logger = logging.getLogger(__name__)


class Module0DatabaseRetriever:
    """Module 0: Retrieve existing questions from database."""

    def __init__(self):
        """Initialize Module 0."""
        pass

    def retrieve_db_questions(
        self,
        grade: int,
        subject: str,
        quantity: int,
        skill_title: str = None,
        language: str = 'arabic',
        provider: str = 'openai',
        partial_match_threshold: float = 0.7
    ) -> List[GeneratedQuestion]:
        """
        Retrieve existing questions from database.

        Args:
            grade: Educational grade level
            subject: Subject area
            quantity: Number of questions to retrieve
            skill_title: Optional specific skill
            language: Language for questions
            provider: LLM provider
            partial_match_threshold: Similarity threshold for matching

        Returns:
            List of GeneratedQuestion objects from database
        """
        from src.utils.dev_upload_util import retrieve_existing_questions_for_mixing

        if quantity == 0:
            return []

        db_questions_raw = retrieve_existing_questions_for_mixing(
            grade=grade,
            subject=subject,
            quantity_needed=quantity,
            skill_title=skill_title,
            language=language,
            provider=provider,
            partial_match_threshold=partial_match_threshold
        )

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
                metadata={
                    'source': 'database',
                    'db_question_type': db_q.get('question_type'),
                    'db_options': db_q.get('options'),
                    'skip_module_4': True
                }
            ))

        return db_questions
