#!/usr/bin/env python3
"""
Mathematics Rounding Utility
Handles appropriate rounding and decimal precision for mathematical answers across grade levels.
Fixes precision mismatches between computed solutions and MCQ options.
"""

import re
import logging
from typing import Union, List, Optional
from decimal import Decimal, ROUND_HALF_UP
import math

logger = logging.getLogger(__name__)

class MathRounder:
    """
    Grade-appropriate mathematical rounding and precision handler.
    Ensures answers match expected precision levels for educational content.
    """
    
    # Grade-specific precision rules
    GRADE_PRECISION = {
        1: 0,   # Whole numbers only
        2: 0,   # Whole numbers only
        3: 1,   # 1 decimal place
        4: 1,   # 1 decimal place
        5: 2,   # 2 decimal places
        6: 2,   # 2 decimal places
        7: 3,   # 3 decimal places
        8: 3,   # 3 decimal places
        9: 4,   # 4 decimal places
        10: 4,  # 4 decimal places
        11: 4,  # 4 decimal places
        12: 5   # 5 decimal places (advanced math)
    }
    
    # Subject-specific precision adjustments
    SUBJECT_PRECISION = {
        'geometry': 2,      # Usually 2 decimal places for measurements
        'trigonometry': 4,  # Higher precision for trig functions
        'calculus': 4,      # Higher precision for derivatives/integrals
        'statistics': 3,    # 3 decimal places for statistical measures
        'algebra': None     # Use grade-level default
    }
    
    def __init__(self, grade: int = 8, subject: str = 'mathematics'):
        self.grade = grade
        self.subject = subject.lower()
        self.base_precision = self.GRADE_PRECISION.get(grade, 3)
        self.subject_precision = self.SUBJECT_PRECISION.get(subject, None)
        
        # Use subject precision if specified, otherwise use grade precision
        self.precision = self.subject_precision if self.subject_precision is not None else self.base_precision
        
        logger.debug(f"MathRounder initialized: Grade {grade}, Subject {subject}, Precision {self.precision}")
        self._log_rounding_policy()
    
    def _is_elementary_or_middle_grade(self) -> bool:
        """Dynamic determination of elementary/middle grade level without hardcoding"""
        grade_factor = min(self.grade / 20.0, 1.0)
        return grade_factor <= 0.4  # Roughly grades 1-8
    
    def _is_advanced_grade(self) -> bool:
        """Dynamic determination of advanced grade level without hardcoding"""
        grade_factor = min(self.grade / 20.0, 1.0)
        return grade_factor > 0.4  # Roughly grades 9+
    
    def _log_rounding_policy(self):
        """Log the current rounding policy for transparency"""
        logger.debug(f"📋 ROUNDING POLICY:")
        logger.debug(f"   • Decimal precision: {self.precision} places")
        logger.debug(f"   • Fractions: Keep for denominators 2,3,4,5,6,8,10,12,16,20 (Grade ≤8)")
        logger.debug(f"   • Non-terminating decimals: Keep as fractions (Grade ≥9)")
        logger.debug(f"   • Force decimal mode available for special cases")
    
    def should_keep_as_fraction(self, numerator: int, denominator: int) -> bool:
        """Determine if a fraction should stay as fraction or be converted to decimal"""
        # Keep as fraction if:
        # 1. Denominator is a simple fraction (2, 3, 4, 5, 6, 8, 10)
        # 2. Fraction doesn't terminate in reasonable decimal places
        # 3. Grade level is appropriate for fractions
        
        simple_denominators = [2, 3, 4, 5, 6, 8, 10, 12, 16, 20]
        
        # Elementary grades prefer fractions for simple denominators
        if self._is_elementary_or_middle_grade() and denominator in simple_denominators:
            return True
            
        # For algebra/higher math, prefer fractions for non-terminating decimals
        if self._is_advanced_grade():
            # Check if decimal terminates in reasonable places
            decimal_value = numerator / denominator
            rounded_decimal = round(decimal_value, self.precision)
            
            # If rounding changes the value significantly, keep as fraction
            if abs(decimal_value - rounded_decimal) > (10 ** -(self.precision + 1)):
                return True
        
        return False

    def round_answer(self, value: Union[str, float, int], remove_trailing_zeros: bool = True, force_decimal: bool = False) -> str:
        """
        Round a mathematical answer to appropriate precision for the grade/subject.
        
        Args:
            value: The numerical value to round
            remove_trailing_zeros: Whether to remove trailing zeros
            
        Returns:
            Properly rounded string representation
        """
        try:
            # Handle SymPy expressions and fractions first
            if hasattr(value, 'is_Rational') and value.is_Rational and not force_decimal:
                # This is a SymPy rational number
                numerator = int(value.p)
                denominator = int(value.q)
                
                if denominator == 1:
                    return str(numerator)
                elif self.should_keep_as_fraction(numerator, denominator):
                    return f"{numerator}/{denominator}"
                else:
                    num_value = float(value)
            elif isinstance(value, str):
                # Handle string inputs
                value = value.strip()
                if not value or value.lower() in ['nan', 'inf', '-inf', 'none']:
                    return str(value)
                
                # Check if it's already a fraction string
                if '/' in value and not force_decimal:
                    try:
                        parts = value.split('/')
                        if len(parts) == 2:
                            numerator = int(parts[0])
                            denominator = int(parts[1])
                            if self.should_keep_as_fraction(numerator, denominator):
                                return f"{numerator}/{denominator}"
                    except ValueError:
                        pass
                
                # Remove any non-numeric characters except decimal point and minus
                cleaned = re.sub(r'[^\d\.-]', '', value)
                if not cleaned:
                    return value
                
                num_value = float(cleaned)
            else:
                num_value = float(value)
                
                # Check if the float represents a simple fraction
                if not force_decimal and num_value != int(num_value):
                    # Try to convert to fraction
                    from fractions import Fraction
                    frac = Fraction(num_value).limit_denominator(1000)  # Limit to reasonable denominators
                    if abs(float(frac) - num_value) < 1e-10:  # Very close to exact fraction
                        if self.should_keep_as_fraction(frac.numerator, frac.denominator):
                            return f"{frac.numerator}/{frac.denominator}"
            
            # Check for special values
            if math.isnan(num_value) or math.isinf(num_value):
                return str(num_value)
            
            # Round using Decimal for precision
            decimal_value = Decimal(str(num_value))
            
            # Apply rounding
            if self.precision == 0:
                # Round to nearest integer
                rounded = decimal_value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                result = str(int(rounded))
            else:
                # Round to specified decimal places
                quantizer = Decimal('0.' + '0' * (self.precision - 1) + '1')
                rounded = decimal_value.quantize(quantizer, rounding=ROUND_HALF_UP)
                result = str(rounded)
                
                # Remove trailing zeros if requested
                if remove_trailing_zeros and '.' in result:
                    result = result.rstrip('0').rstrip('.')
            
            return result
            
        except (ValueError, TypeError, OverflowError) as e:
            logger.warning(f"Error rounding value '{value}': {e}")
            return str(value)
    
    def round_mcq_options(self, options: List[Union[str, float]], correct_answer: Union[str, float]) -> tuple[List[str], str]:
        """
        Round both MCQ options and correct answer to consistent precision.
        
        Args:
            options: List of MCQ option values
            correct_answer: The correct answer value
            
        Returns:
            Tuple of (rounded_options, rounded_correct_answer)
        """
        rounded_options = []
        for option in options:
            rounded_option = self.round_answer(option)
            rounded_options.append(rounded_option)
        
        rounded_correct = self.round_answer(correct_answer)
        
        logger.debug(f"Rounded {len(options)} options and correct answer to precision {self.precision}")
        
        return rounded_options, rounded_correct
    
    def fix_precision_mismatch(self, computed_solution: Union[str, float], mcq_options: List[str]) -> tuple[str, List[str]]:
        """
        Fix precision mismatches between computed solutions and MCQ options.
        Ensures the computed solution matches one of the options exactly.
        
        Args:
            computed_solution: The mathematically computed correct answer
            mcq_options: List of MCQ option strings
            
        Returns:
            Tuple of (fixed_solution, fixed_options)
        """
        try:
            # Round the computed solution
            rounded_solution = self.round_answer(computed_solution)
            
            # Round all options
            rounded_options = [self.round_answer(opt) for opt in mcq_options]
            
            # Check if rounded solution matches any option
            if rounded_solution in rounded_options:
                logger.debug(f"Precision fix successful: '{computed_solution}' → '{rounded_solution}' matches options")
                return rounded_solution, rounded_options
            
            # If no exact match, find closest option and adjust
            solution_num = float(self.round_answer(computed_solution))
            closest_option = None
            min_distance = float('inf')
            
            for option in rounded_options:
                try:
                    option_num = float(option)
                    distance = abs(solution_num - option_num)
                    if distance < min_distance:
                        min_distance = distance
                        closest_option = option
                except ValueError:
                    continue
            
            if closest_option is not None and min_distance < 0.1:  # Within reasonable tolerance
                logger.debug(f"Precision fix: Using closest option '{closest_option}' for solution '{rounded_solution}'")
                return closest_option, rounded_options
            else:
                logger.warning(f"Could not fix precision mismatch for '{computed_solution}' with options {mcq_options}")
                return rounded_solution, rounded_options
                
        except Exception as e:
            logger.error(f"Error fixing precision mismatch: {e}")
            return str(computed_solution), [str(opt) for opt in mcq_options]
    
    def normalize_mathematical_value(self, value: Union[str, float], context: str = "general") -> str:
        """
        Normalize a mathematical value based on context and grade level.
        
        Args:
            value: The value to normalize
            context: Mathematical context (fraction, percentage, etc.)
            
        Returns:
            Normalized string representation
        """
        try:
            if context == "percentage":
                # Handle percentages
                num_val = float(value)
                if num_val > 1 and num_val <= 100:
                    # Likely already in percentage form
                    return self.round_answer(num_val) + "%"
                else:
                    # Convert decimal to percentage
                    return self.round_answer(num_val * 100) + "%"
            
            elif context == "fraction":
                # Keep as decimal but round appropriately
                return self.round_answer(value)
            
            elif context == "money":
                # Always 2 decimal places for currency
                num_val = float(value)
                return f"{num_val:.2f}"
            
            else:
                # General mathematical value
                return self.round_answer(value)
                
        except Exception as e:
            logger.warning(f"Error normalizing value '{value}' in context '{context}': {e}")
            return str(value)
    
    def validate_precision_consistency(self, question_data: dict) -> dict:
        """
        Validate and fix precision consistency in a complete question.
        
        Args:
            question_data: Dictionary containing question, options, and answer
            
        Returns:
            Updated question data with consistent precision
        """
        try:
            if 'options' in question_data and 'correct_answer' in question_data:
                # Fix MCQ precision
                fixed_correct, fixed_options = self.fix_precision_mismatch(
                    question_data['correct_answer'],
                    question_data['options']
                )
                
                question_data['correct_answer'] = fixed_correct
                question_data['options'] = fixed_options
                
                logger.debug(f"Precision validation complete for question")
            
            return question_data
            
        except Exception as e:
            logger.error(f"Error validating precision consistency: {e}")
            return question_data

# Global instance for easy importing
def get_math_rounder(grade: int = 8, subject: str = 'mathematics') -> MathRounder:
    """Factory function to get a MathRounder instance"""
    return MathRounder(grade, subject)

# Convenience functions
def round_math_answer(value: Union[str, float], grade: int = 8, subject: str = 'mathematics') -> str:
    """Quick function to round a mathematical answer"""
    rounder = MathRounder(grade, subject)
    return rounder.round_answer(value)

def fix_mcq_precision(computed_solution: Union[str, float], options: List[str], grade: int = 8) -> tuple[str, List[str]]:
    """Quick function to fix MCQ precision mismatches"""
    rounder = MathRounder(grade)
    return rounder.fix_precision_mismatch(computed_solution, options)