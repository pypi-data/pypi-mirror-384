#!/usr/bin/env python3
"""
Subject Factory: Creates subject-specific generators and validators.
Routes questions to appropriate subject handlers based on detected subject.
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

# Import moved to avoid circular dependency - will import locally when needed
from src.curriculum.subject_manager import SubjectManager, UAESubject

logger = logging.getLogger(__name__)

class BaseSubjectHandler(ABC):
    """Abstract base class for subject-specific handlers"""
    
    def __init__(self, subject: str):
        self.subject = subject
        self.subject_manager = SubjectManager()
    
    @abstractmethod
    def generate_subject_variables(self, variables: Dict[str, Any], grade: int) -> Dict[str, Any]:
        """Generate subject-appropriate variables"""
        pass
    
    @abstractmethod
    def get_solve_prompt(self, question_text: str, pattern: Dict[str, Any]) -> str:
        """Generate solving prompt for the subject"""
        pass
    
    @abstractmethod
    def validate_question(self, question_text: str, answer: str, operation_type: str, grade: int) -> bool:
        """Validate question for subject appropriateness"""
        pass

class MathematicsHandler(BaseSubjectHandler):
    """Mathematics subject handler"""
    
    def __init__(self):
        super().__init__("mathematics")
        # Local import to avoid circular dependency
        from src.subjects.mathematics import MathematicsPatternEngine, MathematicsQuestionValidator
        self.math_engine = MathematicsPatternEngine()
        self.math_validator = MathematicsQuestionValidator()
    
    def generate_subject_variables(self, variables: Dict[str, Any], grade: int) -> Dict[str, Any]:
        return self.math_engine.generate_math_variables(variables, grade)
    
    def get_solve_prompt(self, question_text: str, pattern: Dict[str, Any]) -> str:
        """Generate mathematical solving prompt"""
        operation_type = pattern.get('operation_type', 'general')
        return f"""Solve this mathematical problem step by step:

Question: {question_text}
Operation Type: {operation_type}

Provide only the numerical answer (no units or explanations)."""
    
    def validate_question(self, question_text: str, answer: str, operation_type: str, grade: int) -> bool:
        return self.math_validator.validate_math_question(question_text, answer, operation_type, grade)

class ScienceHandler(BaseSubjectHandler):
    """Science subject handler"""
    
    def __init__(self):
        super().__init__("science")
    
    def generate_subject_variables(self, variables: Dict[str, Any], grade: int) -> Dict[str, Any]:
        """Generate science-appropriate variables"""
        generated_values = {}
        
        for var_name, var_config in variables.items():
            if isinstance(var_config, list):
                generated_values[var_name] = self._random_choice(var_config)
            elif isinstance(var_config, str):
                if var_config.startswith("range("):
                    # Parse range for scientific measurements
                    import re, random
                    range_match = re.match(r"range\\((\\d+),\\s*(\\d+)(?:,\\s*(\\d+))?\\)", var_config)
                    if range_match:
                        start, end = int(range_match.group(1)), int(range_match.group(2))
                        step = int(range_match.group(3)) if range_match.group(3) else 1
                        generated_values[var_name] = random.choice(list(range(start, end, step)))
                elif "scientific_unit" in var_config:
                    # Generate appropriate scientific units
                    units = ["meters", "grams", "seconds", "joules", "newtons", "celsius"]
                    generated_values[var_name] = self._random_choice(units)
                else:
                    generated_values[var_name] = var_config
        
        return generated_values
    
    def get_solve_prompt(self, question_text: str, pattern: Dict[str, Any]) -> str:
        """Generate science solving prompt"""
        domain = pattern.get("domain", "science")
        return f"""Solve this science question step by step. Provide ONLY the final answer, no explanation.

Question: {question_text}

Subject: {domain}
Instructions: Use scientific principles and formulas to solve this question.

Answer (final result only):"""
    
    def validate_question(self, question_text: str, answer: str, operation_type: str, grade: int) -> bool:
        """Validate science question"""
        # Science questions are generally valid if they have content
        return len(question_text.strip()) > 10 and len(answer.strip()) > 0
    
    def _extract_scientific_answer(self, gpt_response: str) -> str:
        """Extract scientific answer from GPT response"""
        response = gpt_response.replace("Answer:", "").replace("The answer is", "").strip()
        return response[:100]  # Limit length
    
    def _random_choice(self, choices: List[Any]) -> Any:
        """Safe random choice"""
        import random
        return random.choice(choices) if choices else ""

class EnglishHandler(BaseSubjectHandler):
    """English subject handler"""
    
    def __init__(self):
        super().__init__("english")
    
    def generate_subject_variables(self, variables: Dict[str, Any], grade: int) -> Dict[str, Any]:
        """Generate English-appropriate variables"""
        generated_values = {}
        
        for var_name, var_config in variables.items():
            if isinstance(var_config, list):
                generated_values[var_name] = self._random_choice(var_config)
            elif var_name in ["character", "protagonist", "author"]:
                # Generate literary variables
                characters = ["Ahmed", "Fatima", "Khalid", "Aisha", "Omar", "Layla"]
                generated_values[var_name] = self._random_choice(characters)
            elif var_name in ["setting", "location"]:
                uae_locations = ["Dubai", "Abu Dhabi", "Sharjah", "Al Ain", "Fujairah"]
                generated_values[var_name] = self._random_choice(uae_locations)
            else:
                generated_values[var_name] = var_config if isinstance(var_config, str) else str(var_config)
        
        return generated_values
    
    def get_solve_prompt(self, question_text: str, pattern: Dict[str, Any]) -> str:
        """Generate English solving prompt"""
        return f"""Answer this English language question clearly and concisely.

Question: {question_text}

Provide a clear, grade-appropriate answer:"""
    
    def validate_question(self, question_text: str, answer: str, operation_type: str, grade: int) -> bool:
        """Validate English question"""
        return len(question_text.strip()) > 10 and len(answer.strip()) > 0
    
    def _random_choice(self, choices: List[Any]) -> Any:
        import random
        return random.choice(choices) if choices else ""

class GeneralHandler(BaseSubjectHandler):
    """General handler for subjects without specific implementations"""
    
    def __init__(self, subject: str):
        super().__init__(subject)
    
    def generate_subject_variables(self, variables: Dict[str, Any], grade: int) -> Dict[str, Any]:
        """Generate general variables"""
        generated_values = {}
        
        for var_name, var_config in variables.items():
            if isinstance(var_config, list):
                import random
                generated_values[var_name] = random.choice(var_config)
            else:
                generated_values[var_name] = str(var_config)
        
        return generated_values
    
    def get_solve_prompt(self, question_text: str, pattern: Dict[str, Any]) -> str:
        """Generate general solving prompt"""
        subject = self.subject.replace("_", " ").title()
        return f"""Answer this {subject} question clearly and appropriately for a student.

Question: {question_text}

Provide a clear answer:"""
    
    def validate_question(self, question_text: str, answer: str, operation_type: str, grade: int) -> bool:
        """General validation"""
        return len(question_text.strip()) > 5 and len(answer.strip()) > 0

class SubjectHandlerFactory:
    """Factory for creating subject-specific handlers"""
    
    _handlers = {
        UAESubject.MATHEMATICS: MathematicsHandler,
        UAESubject.SCIENCE: ScienceHandler,
        UAESubject.ENGLISH: EnglishHandler,
    }
    
    @classmethod
    def create_handler(cls, subject: str) -> BaseSubjectHandler:
        """Create appropriate handler for subject"""
        try:
            subject_enum = UAESubject(subject.lower())
            if subject_enum in cls._handlers:
                return cls._handlers[subject_enum]()
            else:
                logger.info(f"Using general handler for subject: {subject}")
                return GeneralHandler(subject)
        except ValueError:
            logger.warning(f"Unknown subject: {subject}, using general handler")
            return GeneralHandler(subject)
    
    @classmethod
    def get_supported_subjects(cls) -> List[str]:
        """Get list of subjects with dedicated handlers"""
        return [subject.value for subject in cls._handlers.keys()]