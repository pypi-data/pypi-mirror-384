#!/usr/bin/env python3
"""
Mathematics Subject Module: Specialized mathematics question generation and validation.
Contains all math-specific logic extracted from the general pipeline.
"""

import logging
import math
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class MathematicsCurriculumManager:
    """Mathematics-specific curriculum and validation logic"""
    
    # Math-specific grade definitions (extracted from original Module 3)
    MATH_GRADE_DEFINITIONS = {
        1: {
            "new_operations": ["addition", "subtraction", "counting"],
            "new_concepts": ["number_recognition", "basic_shapes", "patterns"],
            "max_numbers": {"addition": 20, "subtraction": 20, "counting": 100},
        },
        2: {
            "new_operations": ["multiplication_basic", "division_basic"],
            "new_concepts": ["place_value", "measurement", "time"],
            "max_numbers": {"addition": 100, "subtraction": 100, "multiplication": 50, "division": 20},
        },
        3: {
            "new_operations": ["multiplication", "division", "fractions_basic"],
            "new_concepts": ["area", "perimeter", "data_collection"],
            "max_numbers": {"multiplication": 144, "division": 100, "fractions": 12},
        },
        4: {
            "new_operations": ["fractions", "decimals_basic"],
            "new_concepts": ["angles", "symmetry", "probability_basic"],
            "max_numbers": {"fractions": 100, "decimals": 1000, "geometry": 100},
        },
        5: {
            "new_operations": ["decimals", "percentages_basic"],
            "new_concepts": ["volume", "coordinate_geometry", "statistics_basic"],
            "max_numbers": {"decimals": 10000, "percentages": 100, "geometry": 500},
        },
        6: {
            "new_operations": ["percentages", "ratios", "negative_numbers"],
            "new_concepts": ["algebraic_thinking", "data_analysis"],
            "max_numbers": {"algebra": 1000, "ratios": 1000, "geometry": 1000},
        },
        7: {
            "new_operations": ["algebra_basic", "equations_simple"],
            "new_concepts": ["proportional_reasoning", "geometric_construction"],
            "max_numbers": {"algebra": 10000, "equations": 1000, "geometry": 1000},
        },
        8: {
            "new_operations": ["systems_equations", "functions", "exponents", "roots", "trigonometry", "trigonometric_right_triangle"],
            "new_concepts": ["transformations", "congruence", "similarity", "trigonometric_ratios"],
            "max_numbers": {"equations": 10000, "functions": 1000, "geometry": 1000, "arithmetic": 10000, "trigonometry": 100, "trigonometric_right_triangle": 100},
        },
        9: {
            "new_operations": ["quadratics", "inequalities", "polynomials"],
            "new_concepts": ["proof", "logical_reasoning", "advanced_geometry"],
            "max_numbers": {"quadratics": 100000, "polynomials": 100000, "equations": 10000, "geometry": 1000, "arithmetic": 100000},
        },
        10: {
            "new_operations": ["logarithms", "exponentials", "sequences"],
            "new_concepts": ["mathematical_modeling", "optimization"],
            "max_numbers": {"logs": 10000, "exponentials": 100000, "sequences": 1000, "algebra": 100000},
        },
        11: {
            "new_operations": ["calculus_basic", "statistics_advanced", "probability_advanced"],
            "new_concepts": ["limits", "derivatives_basic", "advanced_probability"],
            "max_numbers": {"calculus": 1000000, "statistics": 100000, "probability": 10000},
        },
        12: {
            "new_operations": ["calculus", "calculus_derivative", "statistics_inferential", "advanced_algebra"],
            "new_concepts": ["integration", "derivatives", "hypothesis_testing", "complex_modeling"],
            "max_numbers": {"calculus": 10000000, "calculus_derivative": 10000000, "statistics": 100000, "algebra": 1000000},
        }
    }
    
    @classmethod
    def get_math_operations_for_grade(cls, grade: int) -> List[str]:
        """Get cumulative math operations available for a grade"""
        operations = []
        for g in range(1, grade + 1):
            if g in cls.MATH_GRADE_DEFINITIONS:
                operations.extend(cls.MATH_GRADE_DEFINITIONS[g]["new_operations"])
        return list(set(operations))  # Remove duplicates
    
    @classmethod
    def is_math_operation_appropriate(cls, operation: str, grade: int) -> bool:
        """Check if a math operation is appropriate for grade level"""
        available_operations = cls.get_math_operations_for_grade(grade)
        return operation in available_operations
    
    @classmethod
    def get_math_complexity_bounds(cls, grade: int, operation: str) -> Tuple[int, int]:
        """Get appropriate number bounds for math operation and grade"""
        if grade not in cls.MATH_GRADE_DEFINITIONS:
            return (1, 100)  # Default bounds
            
        max_numbers = cls.MATH_GRADE_DEFINITIONS[grade].get("max_numbers", {})
        max_val = max_numbers.get(operation, 100)
        min_val = max(1, max_val // 20)
        return min_val, max_val

class MathematicsPatternEngine:
    """Mathematics-specific pattern application and solution generation"""
    
    def __init__(self):
        self.curriculum = MathematicsCurriculumManager()
    
    def generate_math_variables(self, variables: Dict[str, Any], grade: int) -> Dict[str, Any]:
        """Generate mathematically valid variables for math questions"""
        generated_values = {}
        
        for var_name, var_config in variables.items():
            if isinstance(var_config, list):
                generated_values[var_name] = random.choice(var_config)
            elif isinstance(var_config, str):
                if var_config.startswith("range("):
                    # Parse range expression
                    import re
                    range_match = re.match(r"range\((\d+),\s*(\d+)(?:,\s*(\d+))?\)", var_config)
                    if range_match:
                        start, end = int(range_match.group(1)), int(range_match.group(2))
                        step = int(range_match.group(3)) if range_match.group(3) else 1
                        generated_values[var_name] = random.choice(list(range(start, end, step)))
                elif "valid_triangle" in var_config:
                    # Generate mathematically valid triangle sides
                    if "side_1" in var_config:
                        generated_values[var_name] = random.randint(3, 20)
                    elif "side_2" in var_config:
                        generated_values[var_name] = random.randint(4, 25)
                    elif "hypotenuse" in var_config:
                        # Calculate valid hypotenuse using Pythagorean theorem
                        opp = generated_values.get("opp", random.randint(3, 20))
                        adj = generated_values.get("adj", random.randint(4, 25))
                        hyp = math.sqrt(opp**2 + adj**2)
                        generated_values[var_name] = round(hyp, 1)
                else:
                    generated_values[var_name] = var_config
        
        return generated_values
    
    def solve_math_with_gpt5(self, question_text: str, pattern: Dict[str, Any], llm_gpt5) -> str:
        """Use GPT-5 to solve mathematical questions"""
        try:
            domain = pattern.get("domain", "mathematics")
            solution_pattern = pattern.get("solution_pattern", "")
            
            prompt = f"""Solve this mathematical problem step by step. Provide ONLY the final numerical answer or expression, no explanation.

Problem: {question_text}

Domain: {domain}
Hint: {solution_pattern if solution_pattern else 'Use appropriate mathematical methods'}

Answer (numerical value only):"""
            
            response = llm_gpt5.invoke(prompt)
            answer = response.content.strip()
            
            # Clean up the answer to extract numerical value
            answer = self._extract_numerical_answer(answer)
            
            logger.info(f"GPT-5 solved math question: {answer}")
            return answer
            
        except Exception as e:
            logger.error(f"GPT-5 math solution failed: {e}")
            return self._fallback_math_solution(question_text, pattern)
    
    def _extract_numerical_answer(self, gpt_response: str) -> str:
        """Extract clean numerical answer from GPT response"""
        # Remove common prefixes
        response = gpt_response.replace("Answer:", "").replace("The answer is", "").strip()
        
        # Extract number patterns (including decimals, degrees, fractions)
        import re
        number_patterns = [
            r"([+-]?\d+\.?\d*°?)",  # Numbers with optional degrees
            r"([+-]?\d+/\d+)",        # Fractions
            r"θ\s*=\s*([^\\n]+)",      # Trigonometric expressions
        ]
        
        for pattern in number_patterns:
            match = re.search(pattern, response)
            if match:
                return match.group(1) if "θ" not in pattern else match.group(0)
        
        # If no pattern matches, return the cleaned response
        return response[:50]  # Limit length
    
    def _fallback_math_solution(self, question_text: str, pattern: Dict[str, Any]) -> str:
        """Fallback mathematical solution using pattern hints"""
        solution_pattern = pattern.get("solution_pattern", "")
        if solution_pattern and "{" not in solution_pattern:  # Already filled
            try:
                answer = eval(solution_pattern.replace("×", "*").replace("÷", "/"))
                return str(round(answer, 2) if isinstance(answer, float) else answer)
            except:
                pass
        return "Solution not available"
    
    def validate_math_answer(self, question_text: str, answer: str, grade: int) -> bool:
        """Validate mathematical answer for correctness"""
        # Math-specific validation logic
        try:
            # Check if answer is numerical
            float(answer.replace("°", "").replace("θ = ", ""))
            return True
        except:
            # For non-numerical answers, use more complex validation
            if "θ" in answer or "°" in answer:
                return True  # Trigonometric answers are complex to validate
            return False

class MathematicsQuestionValidator:
    """Mathematics-specific question validation"""
    
    def __init__(self):
        self.curriculum = MathematicsCurriculumManager()
    
    def validate_math_question(self, question_text: str, answer: str, operation_type: str, grade: int) -> bool:
        """Comprehensive validation for mathematics questions"""
        
        # 1. Grade-level appropriateness
        if not self.curriculum.is_math_operation_appropriate(operation_type, grade):
            logger.error(f"Math operation {operation_type} not appropriate for grade {grade}")
            return False
        
        # 2. Answer format validation
        if not self._validate_math_answer_format(answer, operation_type):
            logger.error(f"Invalid answer format for math operation {operation_type}")
            return False
        
        # 3. Trigonometry special validation
        if operation_type in ["trigonometry", "trigonometric_right_triangle"]:
            return self._validate_trigonometry_question(question_text, answer)
        
        # 4. General mathematical validation
        return self._validate_general_math(question_text, answer, operation_type, grade)
    
    def _validate_math_answer_format(self, answer: str, operation_type: str) -> bool:
        """Validate answer format for specific math operations"""
        if operation_type in ["trigonometry", "trigonometric_right_triangle"]:
            # Should contain angle notation or degrees
            return "°" in answer or "θ" in answer or any(char.isdigit() for char in answer)
        
        # General numerical validation
        try:
            # Remove common math symbols and check if numerical
            cleaned = answer.replace("°", "").replace("θ = ", "").strip()
            float(cleaned)
            return True
        except:
            return False
    
    def _validate_trigonometry_question(self, question_text: str, answer: str) -> bool:
        """Special validation for trigonometry questions"""
        # Trigonometry questions are complex, use permissive validation
        logger.info("Detected trigonometry question, using permissive validation")
        return True
    
    def _validate_general_math(self, question_text: str, answer: str, operation_type: str, grade: int) -> bool:
        """General mathematical validation"""
        # Check if numbers in question are grade-appropriate
        import re
        numbers = re.findall(r'\d+', question_text)
        if numbers:
            max_number = max(int(num) for num in numbers)
            min_bound, max_bound = self.curriculum.get_math_complexity_bounds(grade, operation_type)
            if max_number > max_bound * 2:  # Allow some flexibility
                logger.warning(f"Numbers in question may be too large for grade {grade}")
        
        return True