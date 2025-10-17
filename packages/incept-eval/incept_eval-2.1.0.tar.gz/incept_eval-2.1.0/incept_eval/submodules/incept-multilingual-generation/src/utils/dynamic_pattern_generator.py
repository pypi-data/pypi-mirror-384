#!/usr/bin/env python3
"""
Dynamic Pattern Generator using LLM
Generates grade-appropriate mathematical patterns when database samples are insufficient
"""

import logging
import time
import asyncio
import concurrent.futures
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from src.llms import _llm_gpt5
from src.utils.pattern_types import ExtractedPattern
import json
import re
import math

logger = logging.getLogger(__name__)


@dataclass
class GeneratedPatternSet:
    """Set of dynamically generated patterns for a specific topic"""
    patterns: List[ExtractedPattern]
    source: str
    generation_method: str
    confidence: float


class DynamicPatternGenerator:
    """
    Generate mathematical patterns using LLM when samples are not available
    Ensures grade-appropriate content for all education levels
    """
    
    def __init__(self):
        self.llm = _llm_gpt5
        self.generation_cache = {}
        
        # Parallel processing configuration
        self.max_batch_size = 25  # Max patterns per API call
        self.max_concurrent_requests = 6  # Max parallel requests to HF API
        self.enable_parallel_processing = True  # Feature flag
        
    
    def _get_mathematical_diversity_requirements(self, subject: str, skill_title: str, grade: int, count: int) -> str:
        """Generate specific mathematical diversity requirements to fix duplication issues"""
        
        # Based on scorecard feedback: Fix the specific duplication patterns
        base_requirements = f"""
MANDATORY VARIETY - Generate exactly {count} questions using DIFFERENT mathematical structures:

**LINEAR EQUATIONS - MUST VARY FORMS:**
1. Simple one-step: ax = b (e.g., 3x = 15)
2. Two-step: ax + b = c (e.g., 2x + 5 = 17)  
3. Multi-step: ax + b = cx + d (e.g., 3x + 7 = x + 15)
4. With fractions: ax/b = c (e.g., x/4 = 7)
5. With negatives: -ax + b = c (e.g., -2x + 10 = 4)
6. Word problems with different contexts (age, money, geometry)

**LOGARITHMIC EQUATIONS - MUST VARY STRUCTURES:**
1. Simple log: ln(x) = a
2. Log with addition: ln(x + a) = b  
3. Log with coefficient: ln(ax) = b
4. Multiple logs: ln(x) + ln(y) = c
5. Log equations: ln(x - a) = ln(b)

**GEOMETRY - MUST VARY SHAPES/CONCEPTS:**
1. Rectangle area: A = length × width
2. Triangle area: A = ½ × base × height  
3. Circle circumference: C = 2πr
4. Circle area: A = πr²
5. Composite shapes: Combined areas
6. Perimeter vs area problems (clearly different)"""

        # Add grade-specific mathematical diversity
        if grade <= 8:
            grade_specific = """
**GRADE 8 SPECIFIC DIVERSITY:**
- Vary coefficient ranges (1-5, 6-15, 16-50)
- Mix whole numbers, decimals, and simple fractions  
- Alternate between solving for x and solving for other variables
- Include both abstract equations and real-world word problems"""
        else:
            grade_specific = """
**ADVANCED GRADE DIVERSITY:**  
- Include polynomial, exponential, trigonometric varieties
- Vary complexity levels within the same concept
- Mix symbolic and numerical problems"""

        # Subject-specific requirements
        if 'math' in subject.lower():
            subject_specific = """
**MATHEMATICAL DOMAIN MIXING:**
- Combine algebra, geometry, and basic statistics
- Ensure no more than 2 questions from the same mathematical operation
- Vary problem contexts: abstract, real-world applications, word problems"""
        else:
            subject_specific = f"""
**{subject.upper()} DIVERSITY:**
- Apply mathematical concepts to {subject} contexts
- Vary complexity and application scenarios"""

        return f"{base_requirements}\n{grade_specific}\n{subject_specific}"
    def generate_patterns_for_missing_content(
        self,
        grade: int,
        subject: str = "mathematics",
        skill_title: str = None,
        topic: str = None,
        requested_count: int = 5,
        language: str = 'arabic'
    ) -> List[ExtractedPattern]:
        """
        Generate appropriate patterns when database content is missing
        
        Args:
            grade: Grade level (1-12)
            subject: Subject area
            skill_title: Specific skill (e.g., "Calculus", "Linear Equations")
            topic: Specific topic within skill
            requested_count: Number of pattern variations needed
            
        Returns:
            List of ExtractedPattern objects appropriate for grade level
        """
        
        cache_key = f"g{grade}_{subject}_{skill_title}_{topic}_{requested_count}"
        if cache_key in self.generation_cache:
            cached_patterns = self.generation_cache[cache_key]
            if len(cached_patterns) >= requested_count:
                logger.info(f"⚡ CACHE HIT: Using cached patterns for {cache_key}")
                return cached_patterns[:requested_count]
        
        logger.info(f"Generating patterns for Grade {grade} {skill_title or subject}")
        
        try:
            # Generate patterns with moderate variety (1.5x instead of 3x for performance)
            generation_count = max(requested_count, int(requested_count * 1.5))
            raw_patterns = self._generate_raw_patterns(grade, subject, skill_title, topic, generation_count, language)
            
            if raw_patterns:
                # Apply stateless quality control
                from src.utils.stateless_quality_controller import ensure_question_diversity
                
                # Convert to dict format for quality control
                pattern_dicts = [self._pattern_to_dict(p) for p in raw_patterns]
                
                # Ensure diversity without cache dependency
                quality_patterns = ensure_question_diversity(pattern_dicts, requested_count)
                
                # Convert back to ExtractedPattern objects
                final_patterns = [self._dict_to_pattern(p, grade, subject) for p in quality_patterns]
                
                # Only cache if we got good results
                if len(final_patterns) >= requested_count:
                    self.generation_cache[cache_key] = final_patterns
                
                logger.info(f"🔍 STATELESS QUALITY: Generated {len(final_patterns)} diverse patterns for Grade {grade}")
                return final_patterns
            else:
                logger.warning("Failed to generate patterns, using fallback")
                return self._create_fallback_patterns(grade, subject, skill_title)
                
        except Exception as e:
            logger.error(f"Pattern generation failed: {e}")
            return self._create_fallback_patterns(grade, subject, skill_title)
    
    def _create_pattern_generation_prompt(
        self,
        grade: int,
        subject: str,
        skill_title: str,
        topic: str,
        count: int,
        language: str = 'arabic'
    ) -> str:
        """Create comprehensive prompt for LLM pattern generation with hardcoded examples"""
        
        # Get examples from hardcoded patterns
        examples_context = self._get_hardcoded_examples(grade, skill_title, topic)
        
        # Define grade-appropriate expectations
        grade_context = self._get_grade_context(grade)
        
        # Mathematical structural diversity requirements
        diversity_instructions = self._get_mathematical_diversity_requirements(subject, skill_title, grade, count)
        
        prompt = f"""Generate {count} MAXIMALLY DIVERSE mathematical question patterns for Grade {grade} in {language}.

**CRITICAL MATHEMATICAL DIVERSITY REQUIREMENTS:**
{diversity_instructions}
Each pattern MUST use COMPLETELY DIFFERENT mathematical structures and operations. NO REPETITION of forms.

**Requirements:**
- Grade {grade} ({grade_context['difficulty']} difficulty)
- Topic: {skill_title or topic or 'Mathematics'}  
- Language: {language} with proper math notation (use ^{{}} for exponents, · for multiplication)
- NO programming notation (no **, no *, no exp())

**Topics:** {grade_context['topics'][:200]}...

**Example:** {examples_context[:300]}...

**FORMAT REQUIREMENTS:**
Return a JSON object with this exact structure:
{{
    "patterns": [
        {{
            "template": "{language} question with parameter placeholders like {{a}}, {{b}}, {{c}}",
            "parameter_ranges": {{
                "a": [min_value, max_value],
                "b": [min_value, max_value]
            }},
            "mathematical_formula": "description of mathematical operation",
            "constraints": ["mathematical constraints"],
            "difficulty": "easy/medium/hard/expert",
            "operation_type": "specific operation type"
        }}
    ]
}}

**CRITICAL REQUIREMENTS:**
1. **Grade Appropriateness**: Content must match Grade {grade} curriculum standards
2. **Mathematical Accuracy**: All formulas and operations must be correct
3. **Language**: Questions in proper {language} mathematical terminology
4. **Parameter Placeholders**: Use {{param_name}} format in templates
5. **Diverse Content**: Each pattern should test different aspects of the topic
6. **Realistic Parameters**: Value ranges appropriate for grade level
7. **Follow Examples**: Use the reference examples as quality and style guidelines

**SPECIFIC FOCUS FOR GRADE {grade}:**
{self._get_grade_specific_focus(grade, skill_title)}

Generate appropriate mathematical patterns now, following the style and quality of the reference examples:"""

        return prompt
    
    def _get_hardcoded_examples(self, grade: int, skill_title: str, topic: str) -> str:
        """Get relevant hardcoded examples to guide LLM generation - optimized for performance"""
        
        # PERFORMANCE OPTIMIZATION: Use simple cached examples instead of complex catalog iteration
        if hasattr(self, '_examples_cache'):
            cache_key = f"examples_g{grade}"
            if cache_key in self._examples_cache:
                return self._examples_cache[cache_key]
        else:
            self._examples_cache = {}
        
        try:
            from src.utils.skill_patterns import CATALOG, _grade_key
            
            examples = []
            grade_key = _grade_key(grade)
            
            # Get ONLY 1 pattern from the requested grade for performance
            catalog = CATALOG.get(grade_key)
            if catalog and catalog.patterns:
                # Take just the first pattern to save time
                pattern_name, pattern = next(iter(catalog.patterns.items()))
                examples.append(f"""
Example from Grade {grade}:
Template: {pattern.templates.get('ar', ['N/A'])[0] if pattern.templates.get('ar') else 'N/A'}
Topic: {pattern.topic}
Difficulty: {pattern.difficulty}""")
            
            # Skip nearby grades examples for performance - they add complexity without much benefit
            
            result = "\n".join(examples) if examples else "Generate grade-appropriate mathematical content."
            
            # Cache the result
            cache_key = f"examples_g{grade}"
            self._examples_cache[cache_key] = result
            
            return result
                
        except Exception as e:
            logger.warning(f"Could not load hardcoded examples: {e}")
            return "Generate grade-appropriate mathematical content based on curriculum standards."
    
    def _get_grade_context(self, grade: int) -> Dict[str, str]:
        """Get grade-specific educational context"""
        
        if grade <= 3:
            return {
                "age_range": "Ages 6-9",
                "difficulty": "Elementary",
                "topics": "Basic counting, simple addition/subtraction, basic multiplication, shapes",
                "complexity": "Single-step problems, numbers 1-100, concrete concepts"
            }
        elif grade <= 6:
            return {
                "age_range": "Ages 9-12", 
                "difficulty": "Intermediate",
                "topics": "Multi-digit arithmetic, fractions, decimals, basic geometry, simple word problems",
                "complexity": "Multi-step problems, numbers up to 1000s, introduction to abstract concepts"
            }
        elif grade <= 9:
            return {
                "age_range": "Ages 12-15",
                "difficulty": "Advanced",
                "topics": "Algebra, geometry, statistics, probability, advanced fractions",
                "complexity": "Abstract reasoning, variables, equations, proofs"
            }
        else:
            return {
                "age_range": "Ages 15-18",
                "difficulty": "Expert", 
                "topics": "Advanced algebra, calculus, trigonometry, advanced statistics",
                "complexity": "Complex multi-step problems, advanced mathematical reasoning, calculus concepts"
            }
    
    def _get_grade_specific_focus(self, grade: int, skill_title: str) -> str:
        """Get specific focus based on grade and skill"""
        
        if skill_title and "calculus" in skill_title.lower() and grade >= 11:
            return """
            - Derivatives of polynomials, trigonometric, exponential functions
            - Integration techniques: substitution, by parts
            - Limits and continuity
            - Applications: optimization, related rates
            - Differential equations (basic)
            """
        elif skill_title and "algebra" in skill_title.lower() and grade >= 7:
            return """
            - Linear equations and systems
            - Quadratic equations and functions
            - Polynomials and factoring
            - Exponential and logarithmic functions
            - Rational expressions
            """
        elif grade <= 3:
            return """
            - Numbers 1-100
            - Basic addition, subtraction within 20
            - Simple multiplication (tables 1-10)
            - Basic shapes and counting
            """
        elif grade <= 6:
            return """
            - Multi-digit operations
            - Fractions and decimals
            - Basic geometry (area, perimeter)
            - Word problems with multiple steps
            """
        else:
            return f"Standard Grade {grade} mathematics curriculum"
    
    def _get_diversity_instructions_for_subject(self, subject: str, skill_title: str, grade: int, count: int) -> str:
        """Get enhanced diversity instructions with specific template variety requirements"""
        # Determine mathematical focus
        is_mathematics = (
            subject and 'math' in subject.lower() or 
            skill_title and any(term in skill_title.lower() for term in ['calculus', 'derivative', 'integral', 'algebra', 'geometry', 'equation'])
        )
        
        if is_mathematics and grade >= 11:
            return f"""
CALCULUS DIVERSITY - Generate {count} COMPLETELY DIFFERENT question types:

MANDATORY VARIETY - Include these different templates:
• Derivative problems: polynomial, trig, exponential, logarithmic, chain rule, product rule, quotient rule
• Integration problems: basic antiderivatives, substitution, by parts, definite integrals
• Limit problems: polynomial, rational, trigonometric, indeterminate forms
• Application problems: optimization, related rates, motion, area under curves

VARY MATHEMATICAL EXPRESSIONS:
- Different function types (polynomial degrees: linear, quadratic, cubic)
- Different trig functions (sin, cos, tan with various arguments)
- Different exponential forms (e^x, e^(ax+b), exponential bases)
- Different rational expressions (simple fractions, complex ratios)

NO REPETITION: Each question must have a unique mathematical structure!
"""
        elif is_mathematics and grade >= 7:
            return f"""
ALGEBRA/GEOMETRY DIVERSITY - Generate {count} DISTINCT problem types:

MANDATORY VARIETY - Include these different templates:
• Linear equations: one-step, two-step, multi-step, with fractions, with decimals
• Systems of equations: substitution method, elimination method, graphing
• Quadratic equations: factoring, quadratic formula, completing the square
• Geometric problems: area, perimeter, volume, Pythagorean theorem, similar figures
• Exponential/logarithmic: basic exponential equations, simple logarithms
• Word problems: age problems, distance/rate/time, mixture problems, percentage problems

CONTEXT VARIETY:
- Real-world applications (sports, shopping, construction, science)  
- Abstract mathematical problems
- Geometric visualization problems
- Financial/percentage problems

PARAMETER VARIETY:
- Mix positive/negative coefficients
- Include fractions, decimals, and integers
- Vary complexity within grade-appropriate bounds

NO TEMPLATE REPETITION: Each question must have completely different structure!

CRITICAL DIVERSITY ENFORCEMENT:
- Generate AT LEAST 8 different question templates for every batch of 25+ patterns
- Vary question formats: solve for X, find the area, calculate the volume, determine the slope, etc.
- Vary mathematical operations: addition/subtraction, multiplication/division, exponents/roots, derivatives/integrals
- Vary contexts: word problems vs abstract problems vs geometric problems vs real-world applications
- If you generate similar templates, the batch will be REJECTED
"""
        elif grade <= 6:
            return f"""
ELEMENTARY DIVERSITY - Generate {count} DIFFERENT problem types:

MANDATORY VARIETY - Include these different templates:
• Arithmetic operations: addition, subtraction, multiplication, division with various number types
• Word problems: money, measurement, time, shopping, sports, animals
• Geometry basics: shapes, area, perimeter, basic volume
• Fractions and decimals: comparing, adding, subtracting, converting
• Data and probability: reading graphs, simple statistics, basic probability

CONTEXT VARIETY:
- School scenarios, home scenarios, outdoor activities
- Different measurement units (length, weight, time, money)
- Various number ranges appropriate for grade level

NO REPETITION: Each problem must have unique context and mathematical focus!
"""
        else:
            return f"""
CONTENT DIVERSITY - Generate {count} DIFFERENT problems:
VARY: Contexts, numbers, formats, approaches
Make each problem unique!
"""
    
    def _parse_llm_patterns_response(
        self,
        response_text: str,
        grade: int,
        subject: str,
        skill_title: str,
        topic: str
    ) -> List[ExtractedPattern]:
        """Parse LLM response into structured patterns"""
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(0)
            else:
                json_text = response_text.strip()
            
            # Parse JSON
            parsed = json.loads(json_text)
            
            if "patterns" not in parsed:
                logger.warning("No patterns key in LLM response")
                return []
            
            extracted_patterns = []
            
            for i, pattern_data in enumerate(parsed["patterns"]):
                # Convert parameter ranges format
                parameter_ranges = {}
                for param, range_list in pattern_data.get("parameter_ranges", {}).items():
                    if isinstance(range_list, list) and len(range_list) == 2:
                        parameter_ranges[param] = (int(range_list[0]), int(range_list[1]))
                    else:
                        parameter_ranges[param] = (1, 10)  # Default fallback
                
                # Create ExtractedPattern
                pattern = ExtractedPattern(
                    template=pattern_data.get("template", ""),
                    parameter_ranges=parameter_ranges,
                    mathematical_formula=pattern_data.get("mathematical_formula", ""),
                    constraints=pattern_data.get("constraints", []),
                    subject=subject,
                    grade=grade,
                    difficulty=pattern_data.get("difficulty", "medium"),
                    pattern_id=f"llm_generated_{grade}_{skill_title}_{i}",
                    source_samples=0
                )
                
                extracted_patterns.append(pattern)
            
            logger.info(f"Successfully parsed {len(extracted_patterns)} patterns from LLM")
            return extracted_patterns
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM response: {e}")
            logger.debug(f"Raw response: {response_text[:500]}...")
            return []
        except Exception as e:
            logger.error(f"Error parsing LLM patterns: {e}")
            return []
    
    def _create_fallback_patterns(
        self,
        grade: int,
        subject: str,
        skill_title: str
    ) -> List[ExtractedPattern]:
        """Create basic fallback patterns when LLM generation fails"""
        
        logger.info(f"Creating fallback patterns for Grade {grade}")
        
        if grade <= 3:
            # Elementary fallback
            return [
                ExtractedPattern(
                    template="{a} + {b} = ؟",
                    parameter_ranges={"a": (1, 10), "b": (1, 10)},
                    mathematical_formula="addition",
                    constraints=["a + b <= 20"],
                    subject=subject,
                    grade=grade,
                    difficulty="easy",
                    pattern_id=f"fallback_elementary_{grade}",
                    source_samples=0
                )
            ]
        elif grade >= 11:
            # Advanced fallback 
            return [
                ExtractedPattern(
                    template="أوجد المشتقة: f(x) = {a}x² + {b}x + {c}",
                    parameter_ranges={"a": (1, 10), "b": (-10, 10), "c": (-10, 10)},
                    mathematical_formula="derivative",
                    constraints=["a != 0"],
                    subject=subject,
                    grade=grade,
                    difficulty="expert",
                    pattern_id=f"fallback_advanced_{grade}",
                    source_samples=0
                )
            ]
        else:
            # Middle school fallback
            return [
                ExtractedPattern(
                    template="حل المعادلة: {a}x + {b} = {c}",
                    parameter_ranges={"a": (1, 10), "b": (-20, 20), "c": (-20, 20)},
                    mathematical_formula="linear_equation",
                    constraints=["a != 0"],
                    subject=subject,
                    grade=grade,
                    difficulty="medium",
                    pattern_id=f"fallback_middle_{grade}",
                    source_samples=0
                )
            ]
    
    def generate_comprehensive_grade_patterns(self, grade: int) -> Dict[str, List[ExtractedPattern]]:
        """Generate comprehensive patterns for all major topics at a grade level"""
        
        # Define key topics by grade
        grade_topics = {
            1: ["counting", "basic_addition", "shapes"],
            3: ["multiplication_facts", "division_basic", "fractions_intro"],
            5: ["decimals", "fractions_advanced", "geometry_basic"],
            8: ["linear_equations", "geometry_advanced", "statistics"],
            10: ["quadratics", "trigonometry", "functions"],
            12: ["calculus", "derivatives", "integrals", "limits"]
        }
        
        topics = grade_topics.get(grade, ["general_mathematics"])
        all_patterns = {}
        
        for topic in topics:
            patterns = self.generate_patterns_for_missing_content(
                grade=grade,
                skill_title=topic,
                requested_count=3
            )
            all_patterns[topic] = patterns
        
        return all_patterns
    
    def _generate_raw_patterns(
        self,
        grade: int,
        subject: str,
        skill_title: str,
        topic: str,
        count: int,
        language: str
    ) -> List[ExtractedPattern]:
        """Generate patterns with parallel batch processing for speed"""
        if not self.enable_parallel_processing or count <= self.max_batch_size:
            # Use single request for small batches
            return self._generate_patterns_single_batch(grade, subject, skill_title, topic, count, language)
        
        # Use parallel batch processing for large requests
        return self._generate_patterns_parallel_batches(grade, subject, skill_title, topic, count, language)
    
    def _generate_patterns_single_batch(
        self,
        grade: int,
        subject: str,
        skill_title: str,
        topic: str,
        count: int,
        language: str
    ) -> List[ExtractedPattern]:
        """Generate patterns in a single batch (original method)"""
        try:
            prompt = self._create_pattern_generation_prompt(
                grade, subject, skill_title, topic, count, language
            )
            
            logger.info(f"🔄 Calling LLM for {count} patterns (single batch)...")
            start_time = time.time()
            
            response = self.llm.invoke(prompt)
            
            generation_time = time.time() - start_time
            logger.info(f"✅ LLM response received in {generation_time:.2f}s")
            
            patterns = self._parse_llm_patterns_response(
                response.content, grade, subject, skill_title, topic
            )
            
            if patterns:
                logger.info(f"🎯 Successfully parsed {len(patterns)} patterns from LLM")
                return patterns
            else:
                logger.warning("LLM returned no valid patterns, using fallback")
                return self._create_fallback_patterns(grade, subject, skill_title)
                
        except Exception as e:
            logger.error(f"LLM pattern generation failed: {e}")
            return self._create_fallback_patterns(grade, subject, skill_title)
    
    def _generate_patterns_parallel_batches(
        self,
        grade: int,
        subject: str,
        skill_title: str,
        topic: str,
        count: int,
        language: str
    ) -> List[ExtractedPattern]:
        """Generate patterns using parallel batch processing for speed"""
        try:
            # Calculate batch configuration
            num_batches = math.ceil(count / self.max_batch_size)
            actual_concurrent = min(num_batches, self.max_concurrent_requests)
            
            logger.info(f"🔄 PARALLEL: Generating {count} patterns across {num_batches} batches ({actual_concurrent} concurrent)")
            
            # Create batch specifications
            batches = []
            remaining = count
            for i in range(num_batches):
                batch_size = min(self.max_batch_size, remaining)
                batches.append({
                    'batch_id': i + 1,
                    'size': batch_size,
                    'grade': grade,
                    'subject': subject,
                    'skill_title': skill_title,
                    'topic': topic,
                    'language': language
                })
                remaining -= batch_size
            
            # Execute parallel batches
            start_time = time.time()
            all_patterns = []
            
            # Use ThreadPoolExecutor to avoid event loop issues
            with concurrent.futures.ThreadPoolExecutor(max_workers=actual_concurrent) as executor:
                # Submit all batch tasks
                future_to_batch = {
                    executor.submit(self._process_single_batch, batch): batch 
                    for batch in batches
                }
                
                # Collect results as they complete
                completed_batches = 0
                for future in concurrent.futures.as_completed(future_to_batch):
                    batch = future_to_batch[future]
                    try:
                        patterns = future.result()
                        all_patterns.extend(patterns)
                        completed_batches += 1
                        logger.info(f"✅ BATCH {batch['batch_id']}/{num_batches} completed: {len(patterns)} patterns")
                    except Exception as e:
                        logger.error(f"❌ BATCH {batch['batch_id']} failed: {e}")
            
            total_time = time.time() - start_time
            logger.info(f"🏁 PARALLEL COMPLETE: {len(all_patterns)} patterns in {total_time:.2f}s ({completed_batches}/{num_batches} batches)")
            
            if not all_patterns:
                logger.warning("All parallel batches failed, using fallback")
                return self._create_fallback_patterns(grade, subject, skill_title)
            
            return all_patterns
            
        except Exception as e:
            logger.error(f"❌ Parallel pattern generation failed: {e}")
            return self._create_fallback_patterns(grade, subject, skill_title)
    
    def _process_single_batch(self, batch_spec: Dict) -> List[ExtractedPattern]:
        """Process a single batch in the parallel workflow"""
        try:
            prompt = self._create_pattern_generation_prompt(
                batch_spec['grade'],
                batch_spec['subject'], 
                batch_spec['skill_title'],
                batch_spec['topic'],
                batch_spec['size'],
                batch_spec['language']
            )
            
            batch_start = time.time()
            response = self.llm.invoke(prompt)
            batch_time = time.time() - batch_start
            
            logger.debug(f"🔄 BATCH {batch_spec['batch_id']}: LLM responded in {batch_time:.2f}s")
            
            patterns = self._parse_llm_patterns_response(
                response.content,
                batch_spec['grade'],
                batch_spec['subject'], 
                batch_spec['skill_title'],
                batch_spec['topic']
            )
            
            return patterns or []
            
        except Exception as e:
            logger.error(f"❌ Batch {batch_spec['batch_id']} processing failed: {e}")
            return []
    
    def _pattern_to_dict(self, pattern: ExtractedPattern) -> Dict[str, Any]:
        """Convert ExtractedPattern to dict for quality control"""
        return {
            'template': pattern.template,
            'parameter_ranges': pattern.parameter_ranges,
            'mathematical_formula': pattern.mathematical_formula,
            'constraints': pattern.constraints,
            'difficulty': pattern.difficulty,
            'subject': pattern.subject,
            'grade': pattern.grade,
            'pattern_id': pattern.pattern_id
        }
    
    def _dict_to_pattern(self, pattern_dict: Dict[str, Any], grade: int, subject: str) -> ExtractedPattern:
        """Convert dict back to ExtractedPattern after quality control"""
        return ExtractedPattern(
            template=pattern_dict.get('template', ''),
            parameter_ranges=pattern_dict.get('parameter_ranges', {}),
            mathematical_formula=pattern_dict.get('mathematical_formula', ''),
            constraints=pattern_dict.get('constraints', []),
            subject=pattern_dict.get('subject', subject),
            grade=pattern_dict.get('grade', grade),
            difficulty=pattern_dict.get('difficulty', 'medium'),
            pattern_id=pattern_dict.get('pattern_id', f'quality_controlled_{grade}'),
            source_samples=0
        )

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get statistics about pattern generation"""
        return {
            "cached_pattern_sets": len(self.generation_cache),
            "generation_method": "llm_openai_gpt5_with_quality_control",
            "fallback_support": True,
            "grade_coverage": "1-12",
            "languages": ["Arabic", "English_mathematical_symbols"],
            "quality_control": "topic_diversity_deduplication_notation_validation"
        }