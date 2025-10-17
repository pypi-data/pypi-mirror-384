#!/usr/bin/env python3
"""
Utility functions for voiceover script processing
"""

def convert_mcq_voiceover_to_fillin(voiceover_script: str, question_text: str) -> str:
    """
    Convert MCQ-style voiceover script to fill-in format
    
    Args:
        voiceover_script: Original voiceover script (possibly with MCQ language)
        question_text: The actual question text
        
    Returns:
        Converted voiceover script appropriate for fill-in questions
    """
    if not voiceover_script or not question_text:
        return voiceover_script
    
    # Check if script contains MCQ language that needs conversion
    script_lower = voiceover_script.lower()
    if "choose from" not in script_lower and "select" not in script_lower:
        return voiceover_script  # No conversion needed
    
    # Convert based on question type
    question_lower = question_text.lower()
    
    if "add the fractions" in question_lower:
        return f"{question_text}. What is the sum?"
    elif "%" in question_text:
        return f"{question_text}. What is the result?"
    elif "perimeter" in question_lower:
        return f"{question_text}. Give your answer in centimeters."
    elif "area" in question_lower:
        return f"{question_text}. Give your answer in square centimeters."
    else:
        # Generic fix - remove choice language
        cleaned = voiceover_script.replace("Choose from:", "").replace("Select:", "").strip()
        return cleaned if cleaned else question_text


def clean_voiceover_for_fillin(voiceover_data, question_text: str = ""):
    """
    Clean voiceover data when converting MCQ to fill-in
    
    Args:
        voiceover_data: Dictionary or object containing voiceover scripts
        question_text: The question text for context
    """
    if isinstance(voiceover_data, dict):
        # Remove answer choice scripts
        if "answer_choice_scripts" in voiceover_data:
            voiceover_data["answer_choice_scripts"] = None
        
        # Fix question script if needed
        if "question_script" in voiceover_data and question_text:
            voiceover_data["question_script"] = convert_mcq_voiceover_to_fillin(
                voiceover_data["question_script"], question_text
            )
    
    elif hasattr(voiceover_data, 'answer_choice_scripts'):
        # Handle Pydantic objects
        voiceover_data.answer_choice_scripts = None
        
        if hasattr(voiceover_data, 'question_script') and question_text:
            voiceover_data.question_script = convert_mcq_voiceover_to_fillin(
                voiceover_data.question_script, question_text
            )