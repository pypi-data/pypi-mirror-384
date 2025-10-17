import json
import logging
from typing import Optional, Dict, Any
from src.llms import _llm_gpt5

logger = logging.getLogger(__name__)

def map_instructions_to_details(instructions: str, skill: Optional[object] = None) -> Dict[str, Any]:
    """
    Use AI to intelligently map instructions and skill info to educational details.
    
    Args:
        instructions: Natural language instructions for question generation
        skill: Optional skill context object with attributes like title, unit_name, etc.
    
    Returns:
        Dictionary with subject, topic, and focus fields
    """
    try:
        # Handle skill object safely
        skill_context = "Not provided"
        if skill:
            try:
                if hasattr(skill, 'dict'):
                    skill_context = skill.dict()
                elif hasattr(skill, '__dict__'):
                    skill_context = skill.__dict__
                else:
                    skill_context = str(skill)
            except Exception as e:
                logger.warning(f"Could not serialize skill context: {e}")
                skill_context = "Could not serialize skill context"

        prompt = f"""
You are an educational content mapper. Based on the provided instructions and skill context, extract the following educational details:

Instructions: "{instructions}"
Skill Context: {skill_context}

Please analyze and provide:
1. Subject (e.g., algebra, geometry, arithmetic, calculus, etc.)
2. Specific topic (e.g., linear equations, quadratic functions, trigonometry)
3. Educational focus (what should the questions emphasize)

Return your response in JSON format:
{{
    "subject": "specific_subject_name",
    "topic": "specific_topic", 
    "focus": "what_to_emphasize_in_questions"
}}

Be specific and educational. Extract the most relevant mathematics subject area.
"""

        response = _llm_gpt5.invoke(prompt)
        
        # Try to extract JSON from response
        response_text = response.content.strip()
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        elif response_text.startswith("```"):
            response_text = response_text.replace("```", "").strip()
        
        details = json.loads(response_text)
        return details
        
    except Exception as e:
        logger.error(f"AI mapping failed: {e}")
        # Fallback logic
        instructions_lower = instructions.lower()
        if skill and hasattr(skill, 'title') and skill.title:
            subject = skill.title.lower()
            topic = skill.title
        elif "algebra" in instructions_lower:
            subject = "algebra"
            topic = "Algebraic Operations"
        elif "geometry" in instructions_lower:
            subject = "geometry" 
            topic = "Geometric Concepts"
        else:
            subject = "mathematics"
            topic = "General Mathematics"
            
        return {
            "subject": subject,
            "topic": topic,
            "focus": "Grade-appropriate problem solving"
        }