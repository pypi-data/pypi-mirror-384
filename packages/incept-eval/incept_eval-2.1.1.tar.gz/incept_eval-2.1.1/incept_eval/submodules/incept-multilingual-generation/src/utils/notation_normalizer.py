#!/usr/bin/env python3
"""
Notation Normalizer for Mathematics
Ensures mathematical expressions are properly formatted according to TQG spec
Module 3 mathematics-specific formatting rules
"""

import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class MathNotationNormalizer:
    """
    Mathematics notation normalizer implementing TQG spec requirements:
    - Never show 1x or x^1; collapse to x
    - Write fractional coefficients with parentheses: (a/b)x^n
    - Use adjacency or · for multiplication; avoid *
    - For indefinite integrals, always append + C with a preceding space
    - Prefer sin(x), e^x, ln(x); be consistent with function names
    """
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self._patterns = {
            # Remove coefficient of 1
            'one_coefficient': re.compile(r'\b1([a-zA-Z])\b'),
            'one_x': re.compile(r'\b1x\b'),
            
            # Remove exponent of 1
            'one_exponent': re.compile(r'\^1\b'),
            
            # Fix fractional coefficients
            'fraction_coefficient': re.compile(r'(\d+)/(\d+)([a-zA-Z])'),
            
            # Replace * with proper multiplication
            'star_multiplication': re.compile(r'\*'),
            
            # Normalize function names
            'sin_function': re.compile(r'\bsin\s+([a-zA-Z0-9()]+)'),
            'cos_function': re.compile(r'\bcos\s+([a-zA-Z0-9()]+)'),
            'tan_function': re.compile(r'\btan\s+([a-zA-Z0-9()]+)'),
            'ln_function': re.compile(r'\bln\s+([a-zA-Z0-9()]+)'),
            'log_function': re.compile(r'\blog\s+([a-zA-Z0-9()]+)'),
            
            # Indefinite integral constant
            'indefinite_integral': re.compile(r'(\+\s*C)(?!\w)'),
            'missing_constant': re.compile(r'([\+\-]?\s*[^C\+\-]+)$'),
        }
    
    def normalize_expression(self, expression: str) -> str:
        """
        Normalize a mathematical expression according to TQG rules
        
        Args:
            expression: Raw mathematical expression
            
        Returns:
            Normalized expression following TQG notation rules
        """
        if not expression or not isinstance(expression, str):
            return expression
            
        normalized = expression.strip()
        
        # Apply normalization rules in order
        normalized = self._remove_one_coefficients(normalized)
        normalized = self._remove_one_exponents(normalized)
        normalized = self._fix_fractional_coefficients(normalized)
        normalized = self._fix_multiplication_symbols(normalized)
        normalized = self._normalize_function_names(normalized)
        normalized = self._fix_integral_constants(normalized)
        
        logger.debug(f"Normalized '{expression}' -> '{normalized}'")
        return normalized
    
    def _remove_one_coefficients(self, expr: str) -> str:
        """Remove coefficient of 1: 1x -> x, 1y -> y"""
        # Handle 1x specifically
        expr = self._patterns['one_x'].sub('x', expr)
        
        # Handle 1<variable> generally
        expr = self._patterns['one_coefficient'].sub(r'\1', expr)
        
        return expr
    
    def _remove_one_exponents(self, expr: str) -> str:
        """Remove exponent of 1: x^1 -> x"""
        return self._patterns['one_exponent'].sub('', expr)
    
    def _fix_fractional_coefficients(self, expr: str) -> str:
        """Fix fractional coefficients: a/bx -> (a/b)x"""
        def replace_fraction(match):
            num, denom, var = match.groups()
            return f"({num}/{denom}){var}"
        
        return self._patterns['fraction_coefficient'].sub(replace_fraction, expr)
    
    def _fix_multiplication_symbols(self, expr: str) -> str:
        """Replace * with · or adjacency"""
        # Replace * with ·
        return self._patterns['star_multiplication'].sub('·', expr)
    
    def _normalize_function_names(self, expr: str) -> str:
        """Ensure consistent function notation: sin x -> sin(x)"""
        # Fix sin, cos, tan without parentheses
        expr = self._patterns['sin_function'].sub(r'sin(\1)', expr)
        expr = self._patterns['cos_function'].sub(r'cos(\1)', expr)
        expr = self._patterns['tan_function'].sub(r'tan(\1)', expr)
        expr = self._patterns['ln_function'].sub(r'ln(\1)', expr)
        expr = self._patterns['log_function'].sub(r'log(\1)', expr)
        
        return expr
    
    def _fix_integral_constants(self, expr: str) -> str:
        """Ensure indefinite integrals have + C with preceding space"""
        # Check if this looks like an indefinite integral result
        if any(indicator in expr.lower() for indicator in ['∫', 'integral', 'antiderivative']):
            # If it doesn't already have + C, add it
            if not re.search(r'\+\s*C\b', expr):
                # Add + C to the end
                expr = expr.rstrip() + " + C"
            else:
                # Ensure proper spacing
                expr = re.sub(r'\+\s*C\b', ' + C', expr)
        
        return expr
    
    def normalize_question_data(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize all mathematical expressions in a question data structure
        
        Args:
            question_data: Complete question data
            
        Returns:
            Question data with normalized mathematical expressions
        """
        normalized_data = question_data.copy()
        
        # Fields that may contain mathematical expressions
        math_fields = [
            'question_text', 'answer', 'explanation', 'detailed_explanation'
        ]
        
        for field in math_fields:
            if field in normalized_data and normalized_data[field]:
                normalized_data[field] = self.normalize_expression(normalized_data[field])
        
        # Normalize options if present
        if 'options' in normalized_data and normalized_data['options']:
            normalized_data['options'] = [
                self.normalize_expression(str(opt)) for opt in normalized_data['options']
            ]
        
        # Normalize working steps if present
        if 'working_steps' in normalized_data and normalized_data['working_steps']:
            normalized_data['working_steps'] = [
                self.normalize_expression(str(step)) for step in normalized_data['working_steps']
            ]
        
        return normalized_data
    
    def batch_normalize(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize a batch of questions"""
        return [self.normalize_question_data(q) for q in questions]


# Global instance for easy importing
notation_normalizer = MathNotationNormalizer()


def normalize_math_expression(expression: str) -> str:
    """Convenience function for normalizing a mathematical expression"""
    return notation_normalizer.normalize_expression(expression)


def normalize_math_question(question_data: Dict) -> Dict:
    """Convenience function for normalizing a question"""
    return notation_normalizer.normalize_question_data(question_data)