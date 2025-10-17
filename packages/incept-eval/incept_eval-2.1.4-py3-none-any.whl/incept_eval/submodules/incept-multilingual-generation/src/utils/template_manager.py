#!/usr/bin/env python3
"""
Template Manager: Dynamic template loading and variation generation from JSON configuration.
Replaces hardcoded templates with flexible, configurable system.
"""

import json
import logging
import random
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class TemplateManager:
    """
    Manages template variations dynamically from JSON configuration.
    Provides flexible template generation without hardcoded content.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize template manager with configuration."""
        if config_path is None:
            # Default to config directory
            current_dir = Path(__file__).parent.parent
            config_path = current_dir / "config" / "template_variations.json"
        
        self.config_path = config_path
        self.templates_config = {}
        self.load_configuration()
        
        logger.info(f"TemplateManager initialized with config: {config_path}")
    
    def load_configuration(self):
        """Load template configuration from JSON file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.templates_config = json.load(f)
            logger.info("Template configuration loaded successfully")
        except FileNotFoundError:
            logger.error(f"Template config file not found: {self.config_path}")
            self.templates_config = {"template_variations": {}, "fallback_templates": {"general": []}}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in template config: {e}")
            self.templates_config = {"template_variations": {}, "fallback_templates": {"general": []}}
    
    def detect_operation_type(self, text: str) -> Tuple[str, str]:
        """
        Detect operation type and subtype from text using configured keywords.
        
        Returns:
            Tuple of (main_type, sub_type) e.g., ("equation_solving", "quadratic")
        """
        text_lower = text.lower()
        
        for main_type, subtypes in self.templates_config.get("template_variations", {}).items():
            for sub_type, config in subtypes.items():
                keywords = config.get("detection_keywords", [])
                if any(keyword.lower() in text_lower for keyword in keywords):
                    logger.info(f"Detected operation: {main_type}.{sub_type}")
                    return main_type, sub_type
        
        logger.warning(f"No operation type detected for: {text[:50]}...")
        return "general", "unknown"
    
    def generate_template_variations(
        self, 
        operation_type: str, 
        sub_type: str,
        parameter_count: int = 2,
        max_variations: int = 5
    ) -> List[str]:
        """
        Generate template variations for given operation type.
        
        Args:
            operation_type: Main category (e.g., "equation_solving")
            sub_type: Subcategory (e.g., "quadratic") 
            parameter_count: Number of parameters available
            max_variations: Maximum variations to return
            
        Returns:
            List of template strings with parameter placeholders
        """
        templates = []
        
        # Get variations from config
        config_path = self.templates_config.get("template_variations", {}).get(operation_type, {}).get(sub_type, {})
        
        # Debug logging
        logger.info(f"DEBUG: Looking for {operation_type}.{sub_type}")
        logger.info(f"DEBUG: Available operation types: {list(self.templates_config.get('template_variations', {}).keys())}")
        if operation_type in self.templates_config.get("template_variations", {}):
            logger.info(f"DEBUG: Available subtypes for {operation_type}: {list(self.templates_config.get('template_variations', {}).get(operation_type, {}).keys())}")
        logger.info(f"DEBUG: Config path found: {bool(config_path)}")
        
        if config_path:
            # Get configured variations
            variations = config_path.get("variations", [])
            base_templates = config_path.get("base_templates", [])
            
            # Combine base templates and variations
            all_templates = base_templates + variations
            
            # Filter templates by parameter count compatibility
            compatible_templates = []
            for template in all_templates:
                template_param_count = len([p for p in template.split('{') if 'param_' in p])
                if template_param_count <= parameter_count:
                    compatible_templates.append(template)
            
            # Adjust parameter names to match available parameters
            adjusted_templates = []
            for template in compatible_templates[:max_variations]:
                adjusted = self._adjust_parameter_names(template, parameter_count)
                adjusted_templates.append(adjusted)
            
            templates = adjusted_templates
            
            logger.info(f"Generated {len(templates)} variations for {operation_type}.{sub_type}")
        
        # Fallback to general templates if no specific ones found
        if not templates:
            fallback_templates = self.templates_config.get("fallback_templates", {}).get("general", [])
            templates = fallback_templates[:max_variations]
            logger.warning(f"Using fallback templates for {operation_type}.{sub_type}")
        
        return templates
    
    def _adjust_parameter_names(self, template: str, available_param_count: int) -> str:
        """
        Adjust parameter names in template to match available parameters.
        Removes parameters beyond available count and replaces with placeholders.
        """
        import re
        adjusted_template = template
        
        # Find all parameter references in template
        param_matches = re.findall(r'\{param_(\d+)\}', template)
        
        # Replace parameters that are beyond available count
        for param_num_str in param_matches:
            param_index = int(param_num_str)
            if param_index >= available_param_count:
                # Remove parameters we don't have
                adjusted_template = adjusted_template.replace(f'{{param_{param_index}}}', '___')
        
        return adjusted_template
    
    def get_difficulty_adjustments(self, operation_type: str, sub_type: str, difficulty: str) -> Dict[str, Any]:
        """Get difficulty-specific adjustments from configuration."""
        config_path = self.templates_config.get("template_variations", {}).get(operation_type, {}).get(sub_type, {})
        difficulty_config = config_path.get("difficulty_adjustments", {}).get(difficulty, {})
        
        return difficulty_config
    
    def create_diverse_templates(
        self, 
        base_template: str, 
        operation_type: str,
        parameter_ranges: Dict[str, Any],
        max_variations: int = 3
    ) -> List[str]:
        """
        Create diverse templates based on detected operation type and base template.
        This is the main method called by Module 2.
        """
        # Detect specific sub-type
        main_type, sub_type = self.detect_operation_type(base_template)
        
        # If detection failed, use provided operation_type
        if main_type == "general":
            # Map common operation types
            type_mapping = {
                'arithmetic_addition': ('arithmetic', 'addition'),
                'arithmetic_subtraction': ('arithmetic', 'subtraction'),
                'arithmetic_multiplication': ('arithmetic', 'multiplication'),
                'arithmetic_division': ('arithmetic', 'division'),
                'ratios_percentages': ('ratios_percentages', 'basic_ratio'),
                'statistics': ('statistics', 'mean_average'),
                'equation_solving': ('equation_solving', 'quadratic' if ('x^2' in base_template or 'معادلة الدرجة الثانية' in base_template) else 'linear'),
                'geometry': ('geometry', 'area' if 'مساحة' in base_template else 'perimeter')
            }
            
            if operation_type in type_mapping:
                main_type, sub_type = type_mapping[operation_type]
        
        # Get parameter count
        parameter_count = len(parameter_ranges) if parameter_ranges else 2
        
        # Generate variations
        variations = self.generate_template_variations(main_type, sub_type, parameter_count, max_variations)
        
        # Include the original template if it's not already in variations
        all_templates = [base_template]
        for variation in variations:
            if variation not in all_templates and '___' not in variation:  # Exclude broken templates
                all_templates.append(variation)
        
        # Shuffle templates to add more randomness and avoid patterns
        import random
        if len(all_templates) > 1:
            shuffled = all_templates[1:]  # Keep original first
            random.shuffle(shuffled)
            all_templates = [all_templates[0]] + shuffled
        
        logger.info(f"Created {len(all_templates)} diverse templates for {operation_type}")
        return all_templates
    
    def get_mathematical_symbols(self, language: str = "arabic") -> Dict[str, str]:
        """Get mathematical symbols for specified language."""
        lang_config = self.templates_config.get("language_settings", {}).get(language, {})
        return lang_config.get("mathematical_symbols", {})
    
    def reload_configuration(self):
        """Reload configuration from file (useful for dynamic updates)."""
        logger.info("Reloading template configuration...")
        self.load_configuration()
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded templates."""
        stats = {
            "total_main_types": len(self.templates_config.get("template_variations", {})),
            "template_counts": {}
        }
        
        for main_type, subtypes in self.templates_config.get("template_variations", {}).items():
            total_templates = 0
            for sub_type, config in subtypes.items():
                base_count = len(config.get("base_templates", []))
                variations_count = len(config.get("variations", []))
                total_templates += base_count + variations_count
            
            stats["template_counts"][main_type] = total_templates
        
        return stats