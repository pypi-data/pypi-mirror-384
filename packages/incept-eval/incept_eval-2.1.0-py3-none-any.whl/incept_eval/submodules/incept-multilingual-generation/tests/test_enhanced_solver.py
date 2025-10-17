#!/usr/bin/env python3
"""
Test enhanced mathematical solver with production problems
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.mathematical_solver import MathematicalSolver

def test_enhanced_solver():
    """Test enhanced solver with problematic production questions"""
    
    solver = MathematicalSolver()
    
    problems = [
        {
            "type": "ladder",
            "question": "سلم طوله 8 متر يستند على حائط عمودي. إذا انزلق طرفه السفلي بعيداً عن الحائط بمعدل 1 متر/ثانية، فما هو معدل تغير زاوية ميل السلم مع الأرض عندما يكون الطرف السفلي على بعد 2 متر من الحائط؟",
            "expected": "\\( \\frac{-\\sqrt{60}}{60} \\) راديان/ثانية"
        },
        {
            "type": "box", 
            "question": "يراد صنع صندوق مفتوح من الأعلى بقاعدة مربعة الشكل بحيث تكون مساحته السطحية 101 سم². أوجد الأبعاد (طول ضلع القاعدة وارتفاع الصندوق) التي تجعل حجم الصندوق أكبر ما يمكن.",
            "expected": "x ≈ 5.80 سم، h ≈ 2.90 سم"
        },
        {
            "type": "integration",
            "question": "احسب قيمة التكامل المحدود التالي: ∫[1 إلى 2] x²e dx",
            "expected": "Cleaned expression without 1x² and e^1 artifacts"
        }
    ]
    
    print("="*80)
    print("ENHANCED MATHEMATICAL SOLVER TEST")
    print("="*80)
    
    for i, problem in enumerate(problems, 1):
        print(f"\n🧮 Problem {i}: {problem['type'].upper()}")
        print("-" * 60)
        print(f"Question: {problem['question'][:60]}...")
        print(f"Expected: {problem['expected']}")
        
        try:
            # First check question type detection
            question_type = solver._detect_question_type(problem['question'])
            print(f"\n🔍 Detected question type: {question_type}")
            
            # Test the enhanced mathematical solver
            solution = solver.solve_question(problem['question'], grade=12)
            
            print(f"\n✅ SOLVER RESULT:")
            print(f"  Answer: {solution.answer}")
            print(f"  Method: {solution.method_used}")
            print(f"  Confidence: {solution.confidence:.2f}")
            print(f"  Answer Type: {solution.answer_type}")
            
            if solution.steps:
                print(f"  Steps: {len(solution.steps)} detailed steps")
                for j, step in enumerate(solution.steps[:3], 1):
                    print(f"    {j}. {step}")
                if len(solution.steps) > 3:
                    print(f"    ... and {len(solution.steps) - 3} more steps")
            
            # Verify correctness for specific problems
            if problem['type'] == 'ladder':
                if '\\sqrt{60}' in solution.answer and '60}' in solution.answer:
                    print(f"  ✅ CORRECT: Found -√60/60 pattern")
                else:
                    print(f"  ❌ INCORRECT: Expected -√60/60 pattern")
            
            elif problem['type'] == 'box':
                if '5.80' in solution.answer and '2.90' in solution.answer:
                    print(f"  ✅ CORRECT: Found expected dimensions")
                elif '10.5' in solution.answer:
                    print(f"  ❌ INCORRECT: Still getting wrong dimensions")
                else:
                    print(f"  🤔 DIFFERENT: New calculation result")
                    
        except Exception as e:
            print(f"❌ SOLVER ERROR: {e}")
            print(f"  Falling back to DSPy/LLM generation")

if __name__ == "__main__":
    test_enhanced_solver()