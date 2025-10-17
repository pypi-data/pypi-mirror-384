"""
Test case for question evaluation tools - runs actual LLM evaluation.
"""
import json
import sys
import os
import time

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools.question_eval import evaluate_question, validate_amq_format

# Sample test question
SAMPLE_MCQ_QUESTION = {
    "type": "mcq",
    "question": "What is 8 + 5?",
    "options": ["11", "12", "13", "14"],
    "answer": "13",
    "difficulty": "easy",
    "explanation": "To find 8 + 5, we add the numbers together to get 13.",
    "detailed_explanation": {
        "steps": [
            {
                "title": "Step 1: Add the numbers",
                "content": "8 + 5 = 13",
                "image": None,
                "image_alt_text": None
            }
        ],
        "personalized_academic_insights": [
            {
                "answer": "13",
                "insight": "This is correct! 8 + 5 equals 13."
            },
            {
                "answer": "12", 
                "insight": "This would be correct if you were adding 7 + 5, but we're adding 8 + 5."
            }
        ]
    },
    "voiceover_script": {
        "question_script": "What is eight plus five?",
        "answer_choice_scripts": ["eleven", "twelve", "thirteen", "fourteen"],
        "explanation_step_scripts": [
            {
                "step_number": 1,
                "script": "To find eight plus five, we add the numbers together to get thirteen."
            }
        ]
    },
    "skill": {
        "id": "add_single_digit",
        "title": "Adding single-digit numbers",
        "unit": "Addition",
        "grade": 2
    }
}

def test_question_evaluation():
    """Test actual question evaluation with LLM."""
    print("🧪 Testing question evaluation...")
    
    # First validate the format
    print("\n1. Validating AMQ format...")
    validation_result = validate_amq_format.invoke({"question": SAMPLE_MCQ_QUESTION})
    print(f"✅ Format valid: {validation_result['valid']}")
    if validation_result.get('errors'):
        print(f"❌ Errors: {validation_result['errors']}")
    if validation_result.get('warnings'):
        print(f"⚠️  Warnings: {validation_result['warnings']}")
    
    # Now evaluate the question
    print("\n2. Evaluating question with LLM...")
    start_time = time.time()
    evaluation_result = evaluate_question.invoke({"question": SAMPLE_MCQ_QUESTION, "grade": 2})
    print(f"Evaluation result: {evaluation_result}")
    end_time = time.time()
    print(f"Time taken: {round(end_time - start_time)} seconds")
    
    if evaluation_result.get("success"):
        print(f"✅ Evaluation successful!")
        print(f"📊 Overall Score: {evaluation_result.get('overall_score', 'N/A')}/100")
        print(f"🏆 Quality Tier: {evaluation_result.get('quality_tier', 'N/A')}")
        
        if evaluation_result.get('strengths'):
            print(f"💪 Strengths: {', '.join(evaluation_result['strengths'])}")
        
        if evaluation_result.get('improvements'):
            print(f"📈 Improvements: {', '.join(evaluation_result['improvements'])}")
        
        if evaluation_result.get('recommendation'):
            print(f"💡 Recommendation: {evaluation_result['recommendation']}")
        
        # Show detailed criteria scores
        if evaluation_result.get('criteria_scores'):
            for criterion_id, scores in evaluation_result['criteria_scores'].items():
                score = scores.get('score', 'N/A')
                weight = scores.get('weight', 'N/A')
                feedback = scores.get('feedback', 'No feedback')
                print(f"  • {criterion_id}: {score}/4 (weight: {weight}%) - {feedback}")
    else:
        print(f"❌ Evaluation failed: {evaluation_result.get('error', 'Unknown error')}")
        if evaluation_result.get('raw_response'):
            print(f"🔍 Raw response: {evaluation_result['raw_response'][:200]}...")

if __name__ == "__main__":
    test_question_evaluation()