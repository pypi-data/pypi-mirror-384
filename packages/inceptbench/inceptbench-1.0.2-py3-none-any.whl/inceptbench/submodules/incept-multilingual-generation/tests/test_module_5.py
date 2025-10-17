#!/usr/bin/env python3
"""
Test script for Module 5 - Scaffolded Solutions
Tests scaffolding generation with mock MCQ questions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.module_5 import Module5ScaffoldingGenerator
from src.module_4 import MultipleChoiceQuestion, MultipleChoiceOption
import logging

logging.basicConfig(level=logging.INFO)

def create_test_mcq_questions():
    """Create test MCQ questions for different subjects"""
    return [
        # Math MCQ
        MultipleChoiceQuestion(
            question_id="test_mcq_math_1",
            question_text="احسب قيمة x في المعادلة: 3x - 7 = 14",
            options=[
                MultipleChoiceOption("A", "x = 7", True, "correct"),
                MultipleChoiceOption("B", "x = 5", False, "arithmetic error"),
                MultipleChoiceOption("C", "x = 9", False, "sign error"),
                MultipleChoiceOption("D", "x = 3", False, "wrong operation")
            ],
            correct_answer="A",
            subject="mathematics",
            grade=8,
            difficulty="medium",
            distractor_quality="good",
            conversion_status="success"
        ),
        # Physics MCQ
        MultipleChoiceQuestion(
            question_id="test_mcq_physics_1",
            question_text="إذا كانت القوة 20 نيوتن والمساحة 4 متر مربع، فما هو الضغط؟",
            options=[
                MultipleChoiceOption("A", "5 باسكال", True, "correct"),
                MultipleChoiceOption("B", "80 باسكال", False, "multiplication error"),
                MultipleChoiceOption("C", "24 باسكال", False, "addition error"),
                MultipleChoiceOption("D", "16 باسكال", False, "wrong formula")
            ],
            correct_answer="A",
            subject="physics", 
            grade=9,
            difficulty="easy",
            distractor_quality="good",
            conversion_status="success"
        ),
        # Chemistry MCQ
        MultipleChoiceQuestion(
            question_id="test_mcq_chemistry_1",
            question_text="كم عدد البروتونات في ذرة الكربون؟",
            options=[
                MultipleChoiceOption("A", "6", True, "correct"),
                MultipleChoiceOption("B", "12", False, "mass number confusion"),
                MultipleChoiceOption("C", "8", False, "oxygen confusion"),
                MultipleChoiceOption("D", "4", False, "wrong element")
            ],
            correct_answer="A",
            subject="chemistry",
            grade=10,
            difficulty="easy", 
            distractor_quality="good",
            conversion_status="success"
        )
    ]

def test_module_5():
    """Test Module 5 scaffolding generation"""
    module_5 = Module5ScaffoldingGenerator()
    test_mcq_questions = create_test_mcq_questions()
    
    test_cases = [
        {"mcq": test_mcq_questions[0], "subject": "Mathematics"},
        {"mcq": test_mcq_questions[1], "subject": "Physics"}, 
        {"mcq": test_mcq_questions[2], "subject": "Chemistry"}
    ]
    
    print("=" * 60)
    print("MODULE 5 TEST RESULTS")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        mcq = test_case['mcq']
        print(f"\n🧪 Test {i}: {test_case['subject']} Scaffolding")
        print("-" * 40)
        
        try:
            # Get correct answer text
            correct_answer_text = next(
                (opt.text for opt in mcq.options if opt.option_id == mcq.correct_answer),
                "Unknown"
            )
            
            solution = module_5.generate_scaffolded_solution(
                question_text=mcq.question_text,
                correct_answer=correct_answer_text,
                subject=mcq.subject,
                grade=mcq.grade
            )
            
            if solution:
                print(f"✅ SUCCESS: Generated scaffolded solution")
                print(f"   Question: {mcq.question_text[:60]}...")
                print(f"   Answer: {correct_answer_text}")
                print(f"   Steps: {len(solution.detailed_steps)} detailed steps")
                print(f"   Insights: {len(solution.academic_insights)} academic insights")
            else:
                print("❌ FAILED: No scaffolded solution generated")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 60)
    print("MODULE 5 TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_module_5()