#!/usr/bin/env python3
"""
Test script for Module 1 - RAG Sample Retrieval
Tests both mathematics and non-mathematics subjects
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.module_1 import Module1RAGRetriever
import logging

logging.basicConfig(level=logging.INFO)

def test_module_1():
    """Test Module 1 with different subjects"""
    module_1 = Module1RAGRetriever()
    
    test_cases = [
        # Mathematics subjects
        {"grade": 12, "subject": "Calculus", "limit": 3},
        {"grade": 8, "subject": "Algebra", "limit": 2},
        {"grade": 6, "subject": "Geometry", "limit": 2},
        
        # Non-mathematics subjects  
        {"grade": 10, "subject": "Physics", "limit": 2},
        {"grade": 9, "subject": "Chemistry", "limit": 2},
        {"grade": 11, "subject": "Biology", "limit": 2},
        {"grade": 8, "subject": "History", "limit": 2},
        {"grade": 7, "subject": "Geography", "limit": 2},
    ]
    
    print("=" * 60)
    print("MODULE 1 TEST RESULTS")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: Grade {test_case['grade']} {test_case['subject']}")
        print("-" * 40)
        
        try:
            samples = module_1.retrieve_samples(
                grade=test_case['grade'],
                subject=test_case['subject'], 
                limit=test_case['limit']
            )
            
            if samples:
                print(f"✅ SUCCESS: Retrieved {len(samples)} samples")
                for j, sample in enumerate(samples[:2], 1):
                    print(f"   Sample {j}: {sample.question_text[:80]}...")
                    print(f"   Subject: {sample.subject_area}, Grade: {sample.grade}")
            else:
                print("❌ FAILED: No samples retrieved")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("MODULE 1 TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_module_1()