#!/usr/bin/env python3
"""
Difficulty Cache for Consistent Labeling
Ensures identical questions always get the same difficulty rating
"""

import logging
from typing import Dict, Optional
import hashlib

logger = logging.getLogger(__name__)

class DifficultyCache:
    """
    Cache difficulty assessments to ensure consistency.
    Identical mathematical problems always get the same difficulty.
    """
    
    def __init__(self):
        self.cache = {}  # normalized_question -> difficulty
        self.hit_count = 0
        self.miss_count = 0
        
    def normalize_question(self, question_text: str) -> str:
        """Normalize question for consistent comparison"""
        # Remove extra whitespace
        normalized = ' '.join(question_text.split())
        
        # Remove language variations
        normalized = normalized.lower()
        
        # Normalize mathematical notation
        normalized = normalized.replace('**', '^')
        normalized = normalized.replace('*', '·')
        normalized = normalized.replace('sin', 'sin')
        normalized = normalized.replace('cos', 'cos')
        normalized = normalized.replace('tan', 'tan')
        
        # Remove "Find" variations
        for prefix in ['find', 'calculate', 'compute', 'determine', 'evaluate']:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):].strip()
        
        return normalized
    
    def get_hash(self, question_text: str) -> str:
        """Get consistent hash for a question"""
        normalized = self.normalize_question(question_text)
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get_difficulty(self, question_text: str) -> Optional[str]:
        """Get cached difficulty if available"""
        question_hash = self.get_hash(question_text)
        
        if question_hash in self.cache:
            self.hit_count += 1
            difficulty = self.cache[question_hash]
            logger.debug(f"📊 Difficulty cache HIT: '{question_text[:50]}...' → {difficulty}")
            return difficulty
        else:
            self.miss_count += 1
            return None
    
    def set_difficulty(self, question_text: str, difficulty: str):
        """Cache difficulty for a question"""
        question_hash = self.get_hash(question_text)
        
        if question_hash in self.cache and self.cache[question_hash] != difficulty:
            logger.warning(
                f"⚠️ Difficulty inconsistency detected! "
                f"Question: '{question_text[:50]}...' "
                f"Was: {self.cache[question_hash]}, Now: {difficulty}"
            )
        
        self.cache[question_hash] = difficulty
        logger.debug(f"📊 Difficulty cached: '{question_text[:50]}...' → {difficulty}")
    
    def ensure_consistency(self, questions: list) -> list:
        """Ensure all identical questions have the same difficulty"""
        consistency_fixed = 0
        
        for question in questions:
            question_text = question.get('question_text', question.get('question', ''))
            current_difficulty = question.get('difficulty', 'medium')
            
            # Check if we've seen this question before
            cached_difficulty = self.get_difficulty(question_text)
            
            if cached_difficulty:
                if cached_difficulty != current_difficulty:
                    logger.info(
                        f"🔧 Fixed difficulty inconsistency: "
                        f"'{question_text[:40]}...' from {current_difficulty} → {cached_difficulty}"
                    )
                    question['difficulty'] = cached_difficulty
                    consistency_fixed += 1
            else:
                # First time seeing this question, cache its difficulty
                self.set_difficulty(question_text, current_difficulty)
        
        if consistency_fixed > 0:
            logger.info(f"✅ Fixed {consistency_fixed} difficulty inconsistencies")
        
        return questions
    
    def get_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'unique_questions': len(self.cache),
            'cache_hits': self.hit_count,
            'cache_misses': self.miss_count,
            'hit_rate': self.hit_count / (self.hit_count + self.miss_count) if (self.hit_count + self.miss_count) > 0 else 0
        }

# Global difficulty cache instance
difficulty_cache = DifficultyCache()