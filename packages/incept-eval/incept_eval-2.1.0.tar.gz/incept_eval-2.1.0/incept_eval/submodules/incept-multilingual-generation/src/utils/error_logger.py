#!/usr/bin/env python3
"""
Centralized error logging for question generation pipeline.
Logs all failures with detailed context in JSONL format.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from threading import Lock

logger = logging.getLogger(__name__)

class ErrorLogger:
    """Thread-safe error logger for pipeline failures."""

    def __init__(self, log_dir: str = "data/error_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()

        # Use fixed log file (appends to same file)
        self.log_file = self.log_dir / "pipeline_errors.jsonl"

        logger.info(f"Error logger initialized: {self.log_file}")

    def log_error(
        self,
        module: str,
        error_type: str,
        error_message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Log an error with full context.

        Args:
            module: Module name (e.g., "module_1", "module_3", "module_4")
            error_type: Type of error (e.g., "validation_failed", "curation_rejected")
            error_message: Human-readable error message
            context: Additional context (question text, LLM response, etc.)
        """
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "module": module,
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {}
        }

        with self.lock:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(json.dumps(error_entry, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.error(f"Failed to write error log: {e}")

    def log_module_1_retrieval_failure(
        self,
        grade: int,
        subject: str,
        error: str,
        query_params: Optional[Dict[str, Any]] = None
    ):
        """Log Module 1 retrieval failures."""
        self.log_error(
            module="module_1",
            error_type="retrieval_failed",
            error_message=f"Failed to retrieve samples: {error}",
            context={
                "grade": grade,
                "subject": subject,
                "query_params": query_params
            }
        )

    def log_module_2_generation_failure(
        self,
        sample_text: str,
        error: str,
        attempt: int,
        generation_params: Optional[Dict[str, Any]] = None
    ):
        """Log Module 2 question generation failures."""
        self.log_error(
            module="module_2",
            error_type="generation_failed",
            error_message=f"Failed to generate question: {error}",
            context={
                "sample_text": sample_text[:500],  # Truncate for readability
                "attempt": attempt,
                "generation_params": generation_params
            }
        )

    def log_module_3_validation_failure(
        self,
        question_id: str,
        question_text: str,
        answer: str,
        validation_reason: str,
        validation_response: Optional[Dict[str, Any]] = None,
        question_metadata: Optional[Dict[str, Any]] = None,
        provider: Optional[str] = None,
        request_params: Optional[Dict[str, Any]] = None
    ):
        """Log Module 3 answer validation failures."""
        self.log_error(
            module="module_3",
            error_type="validation_failed",
            error_message=f"Answer validation failed: {validation_reason}",
            context={
                "question_id": question_id,
                "question_text": question_text,
                "answer": answer,
                "validation_reason": validation_reason,
                "llm_response": validation_response,
                "question_metadata": question_metadata,
                "provider": provider,
                "request_params": request_params
            }
        )

    def log_module_3_solving_failure(
        self,
        question_id: str,
        question_text: str,
        error: str,
        solver_type: str,
        question_metadata: Optional[Dict[str, Any]] = None
    ):
        """Log Module 3 solving failures."""
        self.log_error(
            module="module_3",
            error_type="solving_failed",
            error_message=f"Failed to solve question: {error}",
            context={
                "question_id": question_id,
                "question_text": question_text,
                "solver_type": solver_type,
                "error": error,
                "question_metadata": question_metadata
            }
        )

    def log_module_4_curation_failure(
        self,
        question_id: str,
        question_text: str,
        substandard_id: str,
        rejection_reason: str,
        llm_response: Optional[Dict[str, Any]] = None,
        curation_request: Optional[Dict[str, Any]] = None,
        request_params: Optional[Dict[str, Any]] = None
    ):
        """Log Module 4 curation failures."""
        self.log_error(
            module="module_4",
            error_type="curation_rejected",
            error_message=f"Question rejected during curation: {rejection_reason}",
            context={
                "question_id": question_id,
                "question_text": question_text,
                "substandard_id": substandard_id,
                "rejection_reason": rejection_reason,
                "llm_response": llm_response,
                "curation_request": curation_request,
                "request_params": request_params
            }
        )

    def log_module_5_translation_failure(
        self,
        question_id: str,
        source_text: str,
        target_language: str,
        error: str,
        translation_metadata: Optional[Dict[str, Any]] = None
    ):
        """Log Module 5 translation failures."""
        self.log_error(
            module="module_5",
            error_type="translation_failed",
            error_message=f"Translation failed: {error}",
            context={
                "question_id": question_id,
                "source_text": source_text[:500],
                "target_language": target_language,
                "error": error,
                "translation_metadata": translation_metadata
            }
        )

    def log_orchestrator_failure(
        self,
        pipeline: str,
        error: str,
        request_params: Optional[Dict[str, Any]] = None
    ):
        """Log orchestrator-level failures."""
        self.log_error(
            module="orchestrator",
            error_type="pipeline_failed",
            error_message=f"Pipeline failure: {error}",
            context={
                "pipeline": pipeline,
                "error": error,
                "request_params": request_params
            }
        )


# Global error logger instance
_error_logger: Optional[ErrorLogger] = None
_logger_lock = Lock()


def get_error_logger() -> ErrorLogger:
    """Get or create the global error logger instance."""
    global _error_logger
    with _logger_lock:
        if _error_logger is None:
            _error_logger = ErrorLogger()
        return _error_logger
