#!/usr/bin/env python3
"""
Test QA guardrails against actual production questions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re

def test_production_questions():
    """Test production questions against QA guardrails"""
    
    questions = [
        {
            "type": "related_rates",
            "question": "سلم طوله 8 متر يستند على حائط عمودي. إذا انزلق طرفه السفلي بعيداً عن الحائط بمعدل 1 متر/ثانية، فما هو معدل تغير زاوية ميل السلم مع الأرض عندما يكون الطرف السفلي على بعد 2 متر من الحائط؟",
            "answer": "A: \\( \\frac{-\\sqrt{60}}{32} \\) راديان/ثانية",
            "expected": "Should be C: \\( \\frac{-\\sqrt{60}}{60} \\) راديان/ثانية"
        },
        {
            "type": "optimization",
            "question": "يراد صنع صندوق مفتوح من الأعلى بقاعدة مربعة الشكل بحيث تكون مساحته السطحية 101 سم². أوجد الأبعاد (طول ضلع القاعدة وارتفاع الصندوق) التي تجعل حجم الصندوق أكبر ما يمكن.",
            "answer": "طول ضلع القاعدة x ≈ 10.5 سم، والارتفاع h ≈ 5.5 سم",
            "expected": "Should be x ≈ 5.80 سم، h ≈ 2.90 سم"
        },
        {
            "type": "integration",
            "question": "احسب قيمة التكامل المحدود التالي باستخدام طريقة التكامل بالتجزئة: ∫[1 إلى 2] (1x²e^1) dx",
            "answer": "B: \\(\\frac{7e}{3}\\)",
            "expected": "Expression should be cleaned: 1x² → x², e^1 → e"
        }
    ]
    
    print("="*80)
    print("PRODUCTION QA ANALYSIS")
    print("="*80)
    
    for i, q in enumerate(questions, 1):
        print(f"\n🧪 Question {i}: {q['type'].upper()}")
        print("-" * 60)
        print(f"Question: {q['question'][:60]}...")
        print(f"Given Answer: {q['answer']}")
        print(f"Expected: {q['expected']}")
        
        # Apply our QA guardrails
        print("\n🔍 QA GUARDRAIL CHECKS:")
        
        if q['type'] == 'related_rates':
            # Extract ladder length and distance
            ladder_length = extract_number(q['question'], r'طوله (\d+(?:\.\d+)?)')
            distance = extract_number(q['question'], r'بعد (\d+(?:\.\d+)?)')
            rate = extract_number(q['question'], r'معدل (\d+(?:\.\d+)?)')
            
            if ladder_length and distance and rate:
                print(f"  ✅ Extracted: L={ladder_length}m, x={distance}m, dx/dt={rate}m/s")
                
                # Calculate correct answer
                import math
                cos_theta = distance / ladder_length
                sin_theta = math.sqrt(1 - cos_theta**2)
                dtheta_dt = -rate / (ladder_length * sin_theta)
                
                print(f"  📊 Calculated: dθ/dt = {dtheta_dt:.6f} rad/s")
                print(f"  📊 Simplified: dθ/dt = -√{60}/{60} = {-math.sqrt(60)/60:.6f} rad/s")
                
                # Check given answer
                given_val = -math.sqrt(60)/32  # Option A
                correct_val = -math.sqrt(60)/60  # Option C
                print(f"  ❌ Given answer A = {given_val:.6f} (WRONG)")
                print(f"  ✅ Correct answer C = {correct_val:.6f}")
            
        elif q['type'] == 'optimization':
            # Extract surface area constraint
            surface_area = extract_number(q['question'], r'(\d+(?:\.\d+)?)\s*سم²')
            given_x = extract_number(q['answer'], r'x.*?(\d+(?:\.\d+)?)')
            given_h = extract_number(q['answer'], r'h.*?(\d+(?:\.\d+)?)')
            
            if surface_area and given_x and given_h:
                print(f"  ✅ Extracted: Surface area = {surface_area} سم²")
                print(f"  ✅ Given dimensions: x = {given_x} سم, h = {given_h} سم")
                
                # Check constraint violation
                base_area = given_x**2
                side_area = 4 * given_x * given_h
                total_area = base_area + side_area
                
                print(f"  📊 Base area alone: {base_area:.1f} سم²")
                print(f"  📊 Total surface area: {total_area:.1f} سم²")
                print(f"  📊 Constraint: {surface_area} سم²")
                
                if base_area > surface_area:
                    print(f"  ❌ CONSTRAINT VIOLATED: Base area > total allowed area!")
                elif total_area > surface_area * 1.1:  # Allow small tolerance
                    print(f"  ❌ CONSTRAINT VIOLATED: Total area exceeds limit!")
                else:
                    print(f"  ✅ Constraint satisfied")
                    
                # Calculate correct answer
                import math
                x_correct = math.sqrt(surface_area / 3)
                h_correct = (surface_area - x_correct**2) / (4 * x_correct)
                print(f"  📊 Correct dimensions: x ≈ {x_correct:.2f} سم, h ≈ {h_correct:.2f} سم")
        
        elif q['type'] == 'integration':
            # Check for coefficient artifacts
            expression = q['question']
            artifacts = []
            
            if '1x²' in expression:
                artifacts.append("1x² should be x²")
            if 'e^1' in expression:
                artifacts.append("e^1 should be e")
                
            if artifacts:
                print(f"  ❌ EXPRESSION ARTIFACTS FOUND:")
                for artifact in artifacts:
                    print(f"    - {artifact}")
            else:
                print(f"  ✅ Expression clean")
                
            # Check integration by parts necessity
            if "بالتجزئة" in expression:
                if 'e^1' in expression:  # e^1 is constant
                    print(f"  ❌ METHOD MISMATCH: 'بالتجزئة' specified but e^1 is constant")
                else:
                    print(f"  ✅ Integration by parts appropriate")

def extract_number(text, pattern):
    """Extract number using regex pattern"""
    match = re.search(pattern, text)
    return float(match.group(1)) if match else None

if __name__ == "__main__":
    test_production_questions()