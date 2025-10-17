#!/usr/bin/env python3
"""
Stateless Quality Controller for Question Generation
Ensures quality without relying on persistent cache
Works independently for each generation batch
"""

import logging
import re
import random
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, Counter
import hashlib

logger = logging.getLogger(__name__)

class StatelessQualityController:
    """
    Stateless quality control that works independently for each batch.
    No dependency on persistent cache or previous generations.
    """
    
    def __init__(self):
        self.max_repetition_ratio = 0.1  # Max 10% of questions can use same template
        
    def ensure_diversity(self, patterns: List[Dict], requested_count: int) -> List[Dict]:
        """
        Ensure diversity in a single batch without cache dependency.
        Each call is independent and stateless.
        """
        if not patterns:
            return []
        
        # Step 1: Group patterns by normalized template
        template_groups = self._group_by_template(patterns)
        
        # Step 2: Calculate max allowed per template for this batch
        max_per_template = max(1, int(requested_count * self.max_repetition_ratio))
        
        # Step 3: Select diverse patterns
        diverse_patterns = self._select_diverse_patterns(
            template_groups, 
            requested_count, 
            max_per_template
        )
        
        # Step 4: Ensure parameter variation for duplicates
        varied_patterns = self._ensure_parameter_variation(diverse_patterns)
        
        logger.info(f"✅ Diversity ensured: {len(varied_patterns)} patterns from {len(patterns)} candidates")
        logger.info(f"📊 Unique templates: {len(set(self._get_template_hash(p) for p in varied_patterns))}")
        
        return varied_patterns
    
    def _group_by_template(self, patterns: List[Dict]) -> Dict[str, List[Dict]]:
        """Group patterns by their normalized template"""
        groups = defaultdict(list)
        
        for pattern in patterns:
            template_hash = self._get_template_hash(pattern)
            groups[template_hash].append(pattern)
        
        return groups
    
    def _get_template_hash(self, pattern: Dict) -> str:
        """Get a normalized hash for template comparison"""
        template = pattern.get('template', '')
        
        # Normalize by removing parameters and numbers
        normalized = re.sub(r'\{[^}]+\}', 'PARAM', template)
        normalized = re.sub(r'\d+', 'NUM', normalized)
        normalized = re.sub(r'\s+', ' ', normalized.strip().lower())
        
        # Also consider the mathematical operation type
        operation = pattern.get('mathematical_formula', '')
        
        # Create hash from normalized template + operation
        combined = f"{normalized}|{operation}"
        return hashlib.md5(combined.encode()).hexdigest()[:8]
    
    def _select_diverse_patterns(
        self, 
        template_groups: Dict[str, List[Dict]], 
        requested_count: int, 
        max_per_template: int
    ) -> List[Dict]:
        """Select patterns ensuring diversity"""
        selected = []
        
        # First pass: Take at least one from each unique template
        for template_hash, group_patterns in template_groups.items():
            if len(selected) < requested_count:
                # Take up to max_per_template from this group
                to_take = min(len(group_patterns), max_per_template, requested_count - len(selected))
                selected.extend(group_patterns[:to_take])
        
        # If we need more, cycle through templates again
        if len(selected) < requested_count:
            all_patterns = []
            for group_patterns in template_groups.values():
                all_patterns.extend(group_patterns[max_per_template:])  # Remaining patterns
            
            random.shuffle(all_patterns)
            remaining_needed = requested_count - len(selected)
            selected.extend(all_patterns[:remaining_needed])
        
        return selected[:requested_count]
    
    def _ensure_parameter_variation(self, patterns: List[Dict]) -> List[Dict]:
        """Ensure patterns with same template have different parameters"""
        # Group by template to find patterns that need variation
        template_groups = defaultdict(list)
        for i, pattern in enumerate(patterns):
            template_hash = self._get_template_hash(pattern)
            template_groups[template_hash].append((i, pattern))
        
        # Vary parameters for patterns with same template
        varied_patterns = patterns.copy()
        
        for template_hash, group in template_groups.items():
            if len(group) > 1:
                # These patterns share a template, vary their parameters
                for idx, (pattern_idx, pattern) in enumerate(group):
                    varied_pattern = self._vary_parameters(pattern, idx)
                    varied_patterns[pattern_idx] = varied_pattern
        
        return varied_patterns
    
    def _vary_parameters(self, pattern: Dict, variation_index: int) -> Dict:
        """Create parameter variations for a pattern"""
        pattern = pattern.copy()
        
        if 'parameter_ranges' not in pattern:
            return pattern
        
        # Create variations by shifting parameter ranges
        varied_ranges = {}
        for param_name, param_range in pattern['parameter_ranges'].items():
            if isinstance(param_range, tuple) and len(param_range) == 2:
                min_val, max_val = param_range
                
                # Create different variations based on index
                if variation_index == 0:
                    # Original range
                    varied_ranges[param_name] = param_range
                elif variation_index == 1:
                    # Shift up
                    shift = (max_val - min_val) // 2
                    varied_ranges[param_name] = (min_val + shift, max_val + shift)
                elif variation_index == 2:
                    # Shift down (if possible)
                    shift = (max_val - min_val) // 3
                    varied_ranges[param_name] = (max(1, min_val - shift), max_val - shift)
                else:
                    # Random variation
                    range_size = max_val - min_val
                    new_min = max(1, min_val + random.randint(-range_size//2, range_size//2))
                    new_max = new_min + range_size
                    varied_ranges[param_name] = (new_min, new_max)
            else:
                varied_ranges[param_name] = param_range
        
        pattern['parameter_ranges'] = varied_ranges
        
        # Also vary the template slightly if possible
        if variation_index > 0:
            pattern['template'] = self._vary_template_text(pattern['template'], variation_index)
        
        return pattern
    
    def _vary_template_text(self, template: str, variation_index: int) -> str:
        """Create slight variations in template text"""
        variations = {
            1: {
                'Find the derivative of': 'Differentiate',
                'Find the integral of': 'Integrate',
                'Calculate': 'Compute',
                'Evaluate': 'Find'
            },
            2: {
                'Find the derivative of': 'Find f\'(x) if f(x) =',
                'Find the integral of': 'Find ∫',
                'Calculate': 'Determine',
                'Evaluate': 'Calculate'
            }
        }
        
        if variation_index in variations:
            for original, replacement in variations[variation_index].items():
                if original in template:
                    return template.replace(original, replacement)
        
        return template
    
    def ensure_difficulty_consistency(self, patterns: List[Dict]) -> List[Dict]:
        """
        Ensure difficulty consistency within a single batch.
        Stateless - works independently for each batch.
        """
        # Group patterns by normalized template
        template_difficulty = {}
        
        for pattern in patterns:
            template_hash = self._get_template_hash(pattern)
            
            # First occurrence sets the difficulty for this template in this batch
            if template_hash not in template_difficulty:
                template_difficulty[template_hash] = pattern.get('difficulty', 'medium')
            else:
                # Ensure consistency with first occurrence
                pattern['difficulty'] = template_difficulty[template_hash]
        
        return patterns
    
    def validate_batch_quality(self, patterns: List[Dict]) -> Dict[str, Any]:
        """
        Validate quality metrics for a batch of patterns.
        Returns quality report without side effects.
        """
        total = len(patterns)
        
        # Count unique templates
        template_hashes = [self._get_template_hash(p) for p in patterns]
        unique_templates = len(set(template_hashes))
        
        # Check repetition constraint
        template_counts = Counter(template_hashes)
        max_allowed = max(1, int(total * self.max_repetition_ratio))
        violations = sum(1 for count in template_counts.values() if count > max_allowed)
        
        # Check difficulty consistency
        template_difficulties = defaultdict(set)
        for pattern in patterns:
            template_hash = self._get_template_hash(pattern)
            difficulty = pattern.get('difficulty', 'unknown')
            template_difficulties[template_hash].add(difficulty)
        
        inconsistent = sum(1 for difficulties in template_difficulties.values() if len(difficulties) > 1)
        
        return {
            'total_patterns': total,
            'unique_templates': unique_templates,
            'diversity_ratio': unique_templates / total if total > 0 else 0,
            'max_repetition_violations': violations,
            'difficulty_inconsistencies': inconsistent,
            'quality_pass': violations == 0 and inconsistent == 0 and unique_templates >= total * 0.7
        }


# Create a function-based interface for stateless usage
def ensure_question_diversity(patterns: List[Dict], requested_count: int) -> List[Dict]:
    """Stateless function to ensure diversity"""
    controller = StatelessQualityController()
    diverse = controller.ensure_diversity(patterns, requested_count)
    consistent = controller.ensure_difficulty_consistency(diverse)
    return consistent

def validate_quality(patterns: List[Dict]) -> Dict[str, Any]:
    """Stateless function to validate quality"""
    controller = StatelessQualityController()
    return controller.validate_batch_quality(patterns)