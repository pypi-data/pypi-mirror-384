"""
Mathematics Question Generation Rubric - UAE K-12 Curriculum
=============================================================

Comprehensive rubric for generating high-quality math questions following:
- Direct Instruction principles  
- Progressive reveal/scaffolding
- Grade-appropriate complexity
- UAE ADEK and MOE curriculum standards
- Lexile level alignment

Based on meeting insights: Focus on what makes a GOOD math question
Updated with expanded topics aligned to UAE MOE curriculum strands: Numbers, Patterns and Algebra, Measurement and Data, Space and Geometry.
Incorporated more detailed forbidden concepts and prerequisite extractions.
Aligned topics and forbidden concepts with official UAE curriculum from MOE and TIMSS reports, ensuring grade-appropriateness (e.g., decimals introduced in Grade 4, algebra in Grade 7).
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)

class MathGradeLevel(Enum):
    """UAE K-12 Math Grade Levels"""
    GRADE_1 = 1
    GRADE_2 = 2
    GRADE_3 = 3
    GRADE_4 = 4
    GRADE_5 = 5
    GRADE_6 = 6
    GRADE_7 = 7  
    GRADE_8 = 8
    GRADE_9 = 9
    GRADE_10 = 10
    GRADE_11 = 11
    GRADE_12 = 12

class MathTopicComplexity(Enum):
    """Mathematics Topic Complexity Levels"""
    BASIC = "basic"           # Fundamental concepts
    INTERMEDIATE = "intermediate"  # Applied concepts
    ADVANCED = "advanced"     # Higher-order thinking
    EXPERT = "expert"        # University-prep level

@dataclass
class MathQuestionRubric:
    """
    Comprehensive rubric for mathematics question quality assessment
    """
    # Grade Appropriateness (25% weight)
    grade_level: MathGradeLevel
    topic_complexity: MathTopicComplexity
    prerequisite_concepts: List[str]
    grade_alignment_score: float = 0.0
    
    # Cognitive Load Management (20% weight)
    working_memory_slots: int = 4  # 3-7 optimal range
    step_complexity: int = 3       # Number of solution steps
    concept_integration: int = 2   # How many concepts combined
    cognitive_load_score: float = 0.0
    
    # Progressive Reveal Structure (20% weight)
    has_scaffolding: bool = False
    reveal_stages: List[str] = None
    title_clarity: float = 0.0
    step_progression: float = 0.0
    scaffolding_score: float = 0.0
    
    # Language & Clarity (15% weight)
    lexile_level: int = 800        # Appropriate for grade
    vocabulary_complexity: str = "grade_appropriate"
    sentence_structure: str = "clear"
    language_score: float = 0.0
    
    # Mathematical Validity (10% weight)
    solution_correctness: bool = True
    multiple_solution_paths: bool = False
    real_world_context: bool = False
    validity_score: float = 0.0
    
    # Engagement & Relevance (10% weight)
    uae_cultural_context: bool = False
    practical_application: bool = False
    student_interest_level: float = 0.0
    engagement_score: float = 0.0
    
    def __post_init__(self):
        if self.reveal_stages is None:
            self.reveal_stages = ["title", "problem_statement", "guided_steps", "solution"]

# Grade-Specific Rubric Standards
MATH_GRADE_STANDARDS = {
    MathGradeLevel.GRADE_1: {
        "topics": ["counting", "addition_subtraction_10", "shapes", "measurement_basics", "patterns", "using_and_applying_number", "reasoning", "calculations", "time_days_of_week", "time_duration", "place_value_intro", "comparing_ordering_numbers", "financial_literacy_basics"],
        "max_steps": 2,
        "lexile_range": (200, 400),
        "forbidden_concepts": ["multiplication", "division", "fractions", "decimals", "algebra", "negative_numbers", "percentages", "variables"],
        "complexity": MathTopicComplexity.BASIC
    },
    MathGradeLevel.GRADE_2: {
        "topics": ["addition_subtraction_100", "skip_counting", "time", "money", "2d_shapes", "measurement", "calculation_grouping", "calculation_multiplication", "calculation_sharing_division", "length", "weight_mass", "time_months", "time_quarter_to_past", "time_analogue", "place_value", "number_patterns", "financial_literacy_money"],
        "max_steps": 3,
        "lexile_range": (300, 500),
        "forbidden_concepts": ["multiplication_facts", "division", "fractions", "decimals", "algebra", "negative_numbers", "percentages", "angles"],
        "complexity": MathTopicComplexity.BASIC
    },
    MathGradeLevel.GRADE_3: {
        "topics": ["multiplication_facts", "division_basics", "fractions_intro", "area_perimeter", "data_graphs", "calculation_multiples", "addition", "subtraction", "problems", "3d_shapes", "capacity", "2d_shapes", "lines_and_angles", "data", "time_minutes", "time_units", "place_value", "rounding_numbers", "financial_literacy_transactions"],
        "max_steps": 3,
        "lexile_range": (400, 600),
        "forbidden_concepts": ["decimals", "algebra", "advanced_fractions", "negative_numbers", "percentages", "variables", "trigonometry"],
        "complexity": MathTopicComplexity.BASIC
    },
    MathGradeLevel.GRADE_4: {
        "topics": ["multi_digit_multiplication", "division_with_remainders", "fractions_basic", "geometry_angles", "patterns", "place_value", "addition", "problems", "division", "length", "area", "weight_mass", "2d_shapes", "angles", "3d_shapes", "tessellating_2d_shapes", "capacity", "lines_and_angles", "decimals", "fractions", "percentages", "data_analysis_basics", "coordinate_planes_intro", "financial_literacy_change"],
        "max_steps": 4,
        "lexile_range": (500, 700),
        "forbidden_concepts": ["algebra", "negative_numbers", "advanced_fractions", "trigonometry", "calculus", "statistics"],
        "complexity": MathTopicComplexity.BASIC
    },
    MathGradeLevel.GRADE_5: {
        "topics": ["decimals_operations", "fractions_advanced", "volume", "coordinate_planes", "data_analysis", "place_value", "addition", "subtraction", "counting_and_numeration", "multiplication", "division", "time_am_pm", "time_24_hour", "time_zones", "time_distance_speed", "angles", "2d_shapes", "3d_shapes", "lines_and_angles", "data", "length", "area", "volume", "capacity", "weight_mass", "decimals", "fractions", "percentages", "sign_word_problems", "equations", "number_problems", "money", "probability_intro"],
        "max_steps": 4,
        "lexile_range": (550, 750),
        "forbidden_concepts": ["algebra", "negative_numbers", "trigonometry", "calculus", "complex_numbers"],
        "complexity": MathTopicComplexity.BASIC
    },
    MathGradeLevel.GRADE_6: {
        "topics": ["basic_arithmetic", "fractions", "decimals", "geometry_basics", "data_handling", "counting_and_numeration", "addition", "subtraction", "multiplication", "division", "3d_shapes", "area", "volume", "capacity", "weight_mass", "geometry_angles", "data", "time_24_hour", "time_zones", "time_distance_speed", "tessellating_2d_shapes", "lines_and_angles", "decimals", "percentages", "fractions", "sign_word_problems", "equations", "number_problems", "money", "length", "mass", "area", "volume_capacity", "ratios_intro", "financial_literacy_interest"],
        "max_steps": 4,
        "lexile_range": (600, 800),
        "forbidden_concepts": ["algebra", "calculus", "trigonometry", "statistics_advanced", "probability_advanced"],
        "complexity": MathTopicComplexity.BASIC
    },
    MathGradeLevel.GRADE_7: {
        "topics": ["integers", "rational_numbers", "basic_algebra", "geometry", "probability", "multiplication", "division", "decimals", "percentages", "fractions", "rules_properties", "area", "volume", "capacity", "weight_mass", "data", "algebraic_expressions", "algebraic_equations", "geometry_angles", "geometry_problems", "geometry_triangles", "special_triangles", "geometry_quadrilaterals", "geometry_constructions", "sign_word_problems", "equations", "number_problems", "money", "length", "mass", "area", "volume_capacity", "ratios_proportions"],
        "max_steps": 5,
        "lexile_range": (700, 900),
        "forbidden_concepts": ["calculus", "advanced_trigonometry", "complex_numbers", "matrices"],
        "complexity": MathTopicComplexity.BASIC
    },
    MathGradeLevel.GRADE_8: {
        "topics": ["linear_equations", "quadratic_expressions", "geometry", "statistics", "decimals", "fractions", "rules_properties", "percentages", "algebraic_expressions", "algebra_highest_common_factor", "algebraic_equations", "area", "volume", "geometry_angles", "frequency_distribution_table", "frequency_histograms_polygons", "relative_frequency", "range", "mode", "mean", "median", "probability_simple_events", "area_circle", "volume_prisms", "measuring_angles", "adjacent_angles", "complementary_supplementary_angles", "vertically_opposite_angles", "angles_point", "parallel_lines", "angle_sum_triangle", "exterior_angle_theorem", "special_triangles", "quadrilaterals", "geometric_constructions", "pythagorean_theorem", "transformations", "congruence_similarity"],
        "max_steps": 6,
        "lexile_range": (800, 1000),
        "forbidden_concepts": ["calculus", "complex_numbers", "advanced_statistics", "differential_equations"],
        "complexity": MathTopicComplexity.INTERMEDIATE
    },
    MathGradeLevel.GRADE_9: {
        "topics": ["quadratic_equations", "coordinate_geometry", "trigonometry_basics", "statistics", "expanding_simplifying_algebraic_expressions", "highest_common_factor", "solving_two_step_equations", "solving_equations_binomial_expressions", "equations_grouping_symbols", "simplifying_algebraic_fractions", "adding_indices_multiplying_terms", "subtracting_indices_dividing_terms", "multiplying_indices_raising_power", "terms_raised_power_zero", "negative_indices", "scientific_notation", "area_circle", "area_trapezium", "area_rhombus", "area_regular_polygons_composite_figures", "surface_area_cube_rectangular_prism", "surface_area_triangular_trapezoidal_prism", "surface_area_cylinder_sphere", "volume_cylinder_sphere", "congruent_triangles", "find_hypotenuse", "pythagorean_triples", "calculating_leg_right_angled_triangle", "trigonometric_ratios", "bearings_compass", "angles_elevation_depression", "frequency_distribution_table", "frequency_histograms_polygons", "relative_frequency", "range", "mode", "mean", "median", "probability_simple_events"],
        "max_steps": 7,
        "lexile_range": (900, 1100),
        "forbidden_concepts": ["calculus", "advanced_statistics", "integrals", "limits"],
        "complexity": MathTopicComplexity.INTERMEDIATE
    },
    MathGradeLevel.GRADE_10: {
        "topics": ["quadratic_functions", "trigonometry", "coordinate_geometry", "probability", "multiplying_dividing_equivalent_fractions", "reducing_fractions_lowest_form", "comparing_ordering_fractions", "subtracting_fractions_whole_numbers", "adding_subtracting_fractions_same_denominator", "adding_subtracting_fractions_different_denominators", "multiplying_fractions_whole_numbers", "multiplying_fractions", "multiplying_mixed_numbers", "finding_reciprocals_fractions_mixed_numbers", "dividing_fractions", "dividing_mixed_numbers", "order_operations_bidmas_fractions", "calculating_percentages_fractions_quantities", "solving_equations_binomial_expressions", "adding_decimals_two_places", "subtracting_decimals_two_places", "decimals_shopping_problems", "decimals_record_length", "decimals_three_places", "adding_decimals_different_places", "subtracting_decimals_different_places", "multiplication_decimals_two_places", "dividing_decimals_10_100_1000", "dividing_decimal_fractions_whole_numbers", "dividing_numbers_decimal_fraction", "introduction_percentages", "changing_fractions_decimals_percentages", "changing_percentages_fractions_decimals", "one_quantity_percentage_another", "equations_grouping_symbols", "equations_fractions", "solving_inequalities"],
        "max_steps": 8,
        "lexile_range": (1000, 1200),
        "forbidden_concepts": ["calculus", "advanced_calculus", "differential_equations"],
        "complexity": MathTopicComplexity.INTERMEDIATE
    },
    MathGradeLevel.GRADE_11: {
        "topics": ["advanced_functions", "trigonometry", "sequences_series", "calculus_intro", "exponential_logarithmic_functions", "conic_sections", "vectors", "matrices", "limits_derivatives", "statistics_probability_advanced"],
        "max_steps": 10,
        "lexile_range": (1100, 1300),
        "forbidden_concepts": ["advanced_calculus", "partial_differentials", "linear_algebra_advanced"],
        "complexity": MathTopicComplexity.ADVANCED
    },
    MathGradeLevel.GRADE_12: {
        "topics": ["calculus", "advanced_trigonometry", "complex_numbers", "statistics", "integrals", "differential_equations_intro", "linear_algebra", "probability_distributions", "vectors_matrices_advanced"],
        "max_steps": 12,
        "lexile_range": (1200, 1400),
        "forbidden_concepts": [],  # University prep - most concepts allowed
        "complexity": MathTopicComplexity.EXPERT
    }
}

# Progressive Reveal Templates
PROGRESSIVE_REVEAL_TEMPLATES = {
    "basic_problem": {
        "stages": [
            "title_only",
            "problem_statement", 
            "hint_1",
            "solution_approach",
            "detailed_solution"
        ],
        "scaffolding_points": [
            "What information are we given?",
            "What are we trying to find?",
            "What method should we use?",
            "Let's work through it step by step"
        ]
    },
    "multi_step_problem": {
        "stages": [
            "title_only",
            "problem_context",
            "part_a",
            "part_b", 
            "synthesis",
            "complete_solution"
        ],
        "scaffolding_points": [
            "Break down the problem into parts",
            "Solve each part systematically", 
            "Combine the results"
        ]
    },
    "word_problem": {
        "stages": [
            "title_only",
            "scenario_description",
            "key_questions",
            "step_by_step_guidance",
            "final_resolution"
        ],
        "scaffolding_points": [
            "Identify the real-world scenario",
            "Extract mathematical elements",
            "Apply concepts step by step",
            "Interpret the result in context"
        ]
    },
    "proof_problem": {
        "stages": [
            "title_only",
            "theorem_statement",
            "assumptions",
            "proof_steps",
            "conclusion"
        ],
        "scaffolding_points": [
            "State what needs to be proven",
            "List given assumptions",
            "Build logical arguments",
            "Conclude with verification"
        ]
    }
}

def evaluate_math_question(question: Dict[str, Any], grade: int) -> MathQuestionRubric:
    """
    Evaluate a math question against the comprehensive rubric
    
    Args:
        question: Question object with text, steps, solution, etc.
        grade: Target grade level (1-12)
        
    Returns:
        MathQuestionRubric with scoring
    """
    
    grade_level = MathGradeLevel(grade)
    standards = MATH_GRADE_STANDARDS[grade_level]
    
    rubric = MathQuestionRubric(
        grade_level=grade_level,
        topic_complexity=standards["complexity"],
        prerequisite_concepts=_extract_prerequisite_concepts(question, grade_level)
    )
    
    # Grade Appropriateness Assessment
    rubric.grade_alignment_score = _assess_grade_appropriateness(question, standards)
    
    # Cognitive Load Assessment  
    rubric.working_memory_slots = _calculate_working_memory_load(question)
    rubric.step_complexity = len(question.get('solution_steps', []))
    rubric.cognitive_load_score = _assess_cognitive_load(rubric)
    
    # Progressive Reveal Assessment
    rubric.has_scaffolding = _has_progressive_structure(question)
    rubric.scaffolding_score = _assess_scaffolding_quality(question)
    
    # Language Assessment
    rubric.lexile_level = _estimate_lexile_level(question.get('question_text', ''))
    rubric.language_score = _assess_language_appropriateness(rubric, standards)
    
    # Mathematical Validity
    rubric.solution_correctness = _validate_solution(question)
    rubric.validity_score = 1.0 if rubric.solution_correctness else 0.0
    
    # UAE Context & Engagement
    rubric.uae_cultural_context = _has_uae_context(question)
    rubric.engagement_score = _assess_engagement_level(question)
    
    return rubric

def _assess_grade_appropriateness(question: Dict[str, Any], standards: Dict) -> float:
    """Assess if question complexity matches grade level"""
    
    question_text = question.get('question_text', '').lower()
    topic = question.get('topic', '').lower()
    
    # Check for forbidden concepts
    for forbidden in standards.get('forbidden_concepts', []):
        if forbidden in question_text or forbidden in topic:
            return 0.0
    
    # Check step complexity
    steps = len(question.get('solution_steps', []))
    max_steps = standards.get('max_steps', 10)
    
    if steps > max_steps:
        return max(0.0, 1.0 - (steps - max_steps) * 0.1)
    
    # Check topic alignment
    allowed_topics = standards.get('topics', [])
    topic_match = any(allowed_topic in topic for allowed_topic in allowed_topics)
    
    base_score = 0.8 if topic_match else 0.4
    
    # Penalize trivial questions (like "x = 4" for grade 12)
    if _is_trivial_question(question_text, standards):
        base_score *= 0.3
        
    # Additional check for prerequisite alignment
    if len(question.get('prerequisite_concepts', [])) > 0:
        base_score += 0.1
        
    return min(1.0, base_score)

def _is_trivial_question(question_text: str, standards: Dict) -> bool:
    """Detect trivial questions inappropriate for grade level"""
    
    trivial_patterns = [
        r'x\s*=\s*\d+',           # x = 4
        r'\d+\s*\+\s*\d+',        # 2 + 3 for high grades
        r'what is \d+',           # "what is 5"
        r'count to \d+',          # count to 10 for high grades
        r'basic addition',        # basic operations in advanced grades
        r'simple shape identification'
    ]
    
    complexity = standards.get('complexity')
    
    if complexity in [MathTopicComplexity.ADVANCED, MathTopicComplexity.EXPERT, MathTopicComplexity.INTERMEDIATE]:
        for pattern in trivial_patterns:
            if re.search(pattern, question_text.lower()):
                return True
                
    return False

def _calculate_working_memory_load(question: Dict[str, Any]) -> int:
    """Calculate working memory slots required (3-7 optimal)"""
    
    # Base load from question complexity
    base_load = 2
    
    # Add load for each concept mentioned
    question_text = question.get('question_text', '')
    math_concepts = ['solve', 'find', 'calculate', 'determine', 'factor', 'simplify', 'integrate', 'differentiate', 'prove', 'graph', 'analyze']
    concept_load = sum(1 for concept in math_concepts if concept in question_text.lower())
    
    # Add load for solution steps
    step_load = min(3, len(question.get('solution_steps', [])) // 2)
    
    # Add load for variables or elements
    variable_load = question_text.lower().count('x') + question_text.lower().count('y') + question_text.lower().count('variable')
    
    total_load = base_load + concept_load + step_load + min(2, variable_load // 2)
    return min(7, max(3, total_load))  # Constrain to 3-7 range

def _assess_cognitive_load(rubric: MathQuestionRubric) -> float:
    """Assess if cognitive load is appropriate"""
    
    wm_slots = rubric.working_memory_slots
    
    # Optimal range is 3-7 working memory slots
    if 3 <= wm_slots <= 7:
        score = 1.0
    elif wm_slots < 3:
        score = 0.5  # Too simple
    else:
        score = max(0.0, 1.0 - (wm_slots - 7) * 0.2)  # Too complex
    
    # Adjust for concept integration
    if rubric.concept_integration > 4:
        score -= 0.1
        
    return score

def _has_progressive_structure(question: Dict[str, Any]) -> bool:
    """Check if question supports progressive reveal"""
    
    required_elements = ['title', 'question_text', 'solution_steps', 'scaffolding_hints']
    return all(element in question for element in required_elements)

def _assess_scaffolding_quality(question: Dict[str, Any]) -> float:
    """Assess quality of scaffolding/progressive reveal structure"""
    
    if not _has_progressive_structure(question):
        return 0.0
    
    score = 0.0
    
    # Title clarity (25%)
    title = question.get('title', '')
    if title and len(title.split()) >= 3 and 'uae' in title.lower():
        score += 0.25
    
    # Solution steps structure (50%) 
    steps = question.get('solution_steps', [])
    if len(steps) >= 3:
        score += 0.5
        
        # Check for logical progression
        if _has_logical_step_progression(steps):
            score += 0.1
    
    # UAE context integration (25%)
    if question.get('uae_context'):
        score += 0.25
    
    # Additional hints quality
    hints = question.get('scaffolding_hints', [])
    if len(hints) >= 2:
        score += 0.1
        
    return min(1.0, score)

def _has_logical_step_progression(steps: List[str]) -> bool:
    """Check if solution steps follow logical progression"""
    
    if len(steps) < 2:
        return False
        
    # Check for progression words
    progression_words = ['first', 'then', 'next', 'finally', 'now', 'substitute', 'therefore', 'subsequently', 'after that', 'following']
    progression_count = sum(1 for step in steps for word in progression_words if word.lower() in step.lower())
    
    return progression_count >= len(steps) // 2

def _estimate_lexile_level(text: str) -> int:
    """Estimate lexile level of question text"""
    
    # Improved heuristic: approximate Lexile formula
    # ASL = average sentence length (words/sentence)
    # ASW = average syllables per word (approximated by word length / 3)
    
    sentences = re.split(r'[.!?]+', text)
    sentence_count = max(1, len([s for s in sentences if s.strip()]))
    
    words = [word for sentence in sentences for word in sentence.split() if word.strip()]
    word_count = len(words)
    
    avg_sentence_length = word_count / sentence_count if sentence_count else 0
    avg_word_length = sum(len(word) for word in words) / word_count if word_count else 0
    approx_syllables = avg_word_length / 3  # Rough estimate
    
    # Approximate Lexile: 0.39 * ASL + 11.8 * ASW - 15.59 (simplified Flesch-Kincaid variant)
    lexile = 0.39 * avg_sentence_length + 11.8 * approx_syllables - 15.59
    lexile *= 10  # Scale to Lexile range
    
    return int(min(1400, max(200, lexile)))

def _assess_language_appropriateness(rubric: MathQuestionRubric, standards: Dict) -> float:
    """Assess if language is appropriate for grade level"""
    
    lexile_range = standards.get('lexile_range', (800, 1000))
    min_lexile, max_lexile = lexile_range
    
    if min_lexile <= rubric.lexile_level <= max_lexile:
        return 1.0
    elif rubric.lexile_level < min_lexile:
        return max(0.0, 1.0 - (min_lexile - rubric.lexile_level) / 200)
    else:
        return max(0.0, 1.0 - (rubric.lexile_level - max_lexile) / 200)

def _validate_solution(question: Dict[str, Any]) -> bool:
    """Basic validation of mathematical solution"""
    
    # Basic checks for solution validity
    solution_steps = question.get('solution_steps', [])
    final_answer = question.get('final_answer', '')
    
    # Must have both steps and final answer
    if not solution_steps or not final_answer:
        return False
        
    # Check for mathematical consistency (basic heuristic)
    # More sophisticated validation would involve symbolic math
    if str(final_answer).lower() not in ''.join(solution_steps).lower():
        return False
    
    return True

def _has_uae_context(question: Dict[str, Any]) -> bool:
    """Check if question includes UAE cultural context"""
    
    uae_indicators = [
        'uae', 'emirates', 'dubai', 'abu dhabi', 'dirham', 'sheikh', 
        'desert', 'camel', 'falcon', 'date palm', 'souq', 'majlis',
        'eid', 'ramadan', 'national day', 'burj khalifa', 'oil', 'palm jumeirah'
    ]
    
    question_text = question.get('question_text', '').lower()
    uae_context = question.get('uae_context', '').lower()
    
    full_text = f"{question_text} {uae_context}"
    
    return any(indicator in full_text for indicator in uae_indicators)

def _assess_engagement_level(question: Dict[str, Any]) -> float:
    """Assess student engagement potential"""
    
    score = 0.5  # Base score
    
    # Real-world application
    if question.get('real_world_context'):
        score += 0.3
        
    # UAE cultural context
    if _has_uae_context(question):
        score += 0.2
        
    # Interactive elements
    if question.get('interactive_elements'):
        score += 0.2
        
    # Age-appropriate scenarios
    grade = question.get('grade', 10)
    if _has_age_appropriate_scenario(question.get('question_text', ''), grade):
        score += 0.1
    
    # Multiple solution paths
    if question.get('multiple_solution_paths'):
        score += 0.1
        
    return min(1.0, score)

def _has_age_appropriate_scenario(text: str, grade: int) -> bool:
    """Check if scenario is age-appropriate"""
    
    text_lower = text.lower()
    
    age_appropriate_topics = {
        6: ['toys', 'games', 'family', 'animals', 'school trips'],
        7: ['school', 'friends', 'sports', 'food', 'hobbies'],
        8: ['hobbies', 'travel', 'technology', 'environment', 'gadgets'],
        9: ['social media', 'music', 'movies', 'fashion', 'sports teams'],
        10: ['career', 'driving', 'independence', 'relationships', 'technology trends'],
        11: ['university', 'future planning', 'global issues', 'economics'],
        12: ['career planning', 'adult responsibilities', 'society', 'innovation', 'entrepreneurship']
    }
    
    relevant_topics = []
    for g in range(max(6, grade-2), min(13, grade+2)):
        relevant_topics.extend(age_appropriate_topics.get(g, []))
    
    return any(topic in text_lower for topic in relevant_topics)

def generate_rubric_based_question_prompt(grade: int, topic: str, difficulty: str) -> str:
    """Generate DSPy prompt for rubric-based question generation"""
    
    grade_level = MathGradeLevel(grade)
    standards = MATH_GRADE_STANDARDS[grade_level]
    
    return f"""
Generate a high-quality mathematics question following UAE K-12 standards from MOE and ADEK:

**Grade Level**: {grade} (Complexity: {standards['complexity'].value})
**Topic**: {topic}
**Difficulty**: {difficulty}

**Rubric Requirements**:
1. **Grade Appropriateness**: Use concepts appropriate for Grade {grade}
   - Allowed topics: {', '.join(standards['topics'])}
   - Forbidden concepts: {', '.join(standards.get('forbidden_concepts', ['None']))}
   - Maximum solution steps: {standards['max_steps']}
   - Align to UAE curriculum strands: Numbers, Patterns and Algebra, Measurement and Data, Space and Geometry

2. **Progressive Reveal Structure**: 
   - Clear, descriptive title
   - Step-by-step solution that can be revealed progressively
   - Each step builds logically on the previous
   - Include scaffolding hints for guidance

3. **Language & Clarity**:
   - Lexile level: {standards['lexile_range'][0]}-{standards['lexile_range'][1]}
   - Grade-appropriate vocabulary
   - Clear, concise sentences
   - Avoid ambiguity in wording

4. **Mathematical Validity**:
   - Correct solution with verifiable steps
   - Show all working clearly
   - Include final answer
   - Consider multiple solution paths if applicable

5. **UAE Context & Engagement**:
   - Include UAE cultural context where appropriate (e.g., Dirhams, Dubai landmarks, Emirati traditions)
   - Real-world application relevant to {grade}th graders
   - Age-appropriate scenario
   - Promote student interest through relatable elements

**Output Format**:
{{
    "title": "Clear descriptive title",
    "question_text": "Full question with UAE context",
    "solution_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
    "final_answer": "Complete final answer",
    "topic": "{topic}",
    "difficulty": "{difficulty}",
    "grade": {grade},
    "uae_context": "Brief description of UAE context used",
    "scaffolding_hints": ["Hint 1", "Hint 2", "Hint 3"]
}}
    """.strip()

def _extract_prerequisite_concepts(question: Dict[str, Any], grade_level: MathGradeLevel) -> List[str]:
    """
    Extract prerequisite mathematical concepts from a question
    
    Args:
        question: Question object with text and metadata
        grade_level: Target grade level
        
    Returns:
        List of prerequisite concept strings
    """
    
    question_text = question.get('question_text', '').lower()
    topic = question.get('topic', '').lower()
    
    # Expanded concept mapping based on common math patterns and UAE curriculum strands
    concept_patterns = {
        'arithmetic': ['addition', 'subtraction', 'multiplication', 'division'],
        'fractions': ['arithmetic', 'ratios', 'decimals'],
        'algebra': ['arithmetic', 'basic_equations', 'patterns'],
        'geometry': ['measurement', 'shapes', 'space_geometry'],
        'trigonometry': ['geometry', 'angles', 'algebra'],
        'calculus': ['algebra', 'functions', 'limits'],
        'statistics': ['arithmetic', 'data_analysis', 'measurement_data'],
        'probability': ['statistics', 'counting'],
        'coordinate_geometry': ['algebra', 'geometry'],
        'sequences_series': ['patterns', 'algebra']
    }
    
    prerequisites = []
    
    # Extract from topic if available
    if topic:
        for concept, prereqs in concept_patterns.items():
            if concept in topic:
                prerequisites.extend(prereqs)
    
    # Extract from question patterns
    if any(word in question_text for word in ['solve', 'equation', 'x', 'variable']):
        prerequisites.append('basic_equations')
    
    if any(word in question_text for word in ['graph', 'plot', 'coordinate']):
        prerequisites.append('coordinate_geometry')
    
    if any(word in question_text for word in ['area', 'perimeter', 'volume']):
        prerequisites.append('measurement')
    
    if any(word in question_text for word in ['sine', 'cosine', 'tan', 'angle']):
        prerequisites.append('trigonometry_basics')
    
    if any(word in question_text for word in ['mean', 'median', 'mode', 'data']):
        prerequisites.append('data_handling')
    
    if any(word in question_text for word in ['probability', 'chance', 'event']):
        prerequisites.append('probability_basics')
    
    # Grade-level defaults
    if not prerequisites:
        if grade_level.value <= 8:
            prerequisites = ['arithmetic', 'basic_concepts', 'measurement_basics']
        elif grade_level.value <= 10:
            prerequisites = ['algebra_basics', 'geometry_basics', 'statistics_basics']
        else:
            prerequisites = ['advanced_algebra', 'precalculus', 'trigonometry']
    
    return list(set(prerequisites))  # Remove duplicates

# Export key functions and classes
__all__ = [
    'MathQuestionRubric',
    'MathGradeLevel', 
    'MathTopicComplexity',
    'MATH_GRADE_STANDARDS',
    'evaluate_math_question',
    'generate_rubric_based_question_prompt'
]