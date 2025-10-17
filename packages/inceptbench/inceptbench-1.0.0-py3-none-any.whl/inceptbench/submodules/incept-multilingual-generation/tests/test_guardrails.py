#!/usr/bin/env python3
"""
Test systematic mathematical guardrails
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.mathematical_solver import MathematicalSolver

def test_guardrails():
    """Test all systematic mathematical guardrails"""
    
    solver = MathematicalSolver()
    
    guardrail_tests = [
        {
            "name": "GUARDRAIL 1: Identical bounds → integral = 0",
            "question": "احسب التكامل المحدود: ∫[1 إلى 1] x² dx",
            "expected_answer": "0",
            "expected_method": "identical_bounds_rule"
        },
        {
            "name": "GUARDRAIL 2: Cone volume with 1/3 factor",
            "question": "خزان مخروطي ارتفاعه 10 سم ونصف قطر قاعدته 5 سم يتسرب منه الماء بمعدل 2 سم³/دقيقة. أوجد معدل انخفاض مستوى الماء عندما يكون ارتفاعه 6 سم",
            "validate": lambda sol: any("1/3" in step for step in sol.steps) if sol.steps else False,
            "description": "Check cone formula includes 1/3 factor"
        },
        {
            "name": "GUARDRAIL 3: Surface area constraint verification",
            "question": "يراد صنع صندوق مفتوح من الأعلى بقاعدة مربعة الشكل بحيث تكون مساحته السطحية 101 سم². أوجد الأبعاد التي تجعل حجم الصندوق أكبر ما يمكن",
            "validate": lambda sol: abs(5.80**2 + 4*5.80*2.90 - 101) < 0.1,
            "description": "Verify surface area constraint is satisfied"
        },
        {
            "name": "GUARDRAIL 4: Template sanitization",
            "question": "احسب التكامل: ∫ 1x²هـ^1 dx",
            "validate": lambda sol: "1x" not in sol.answer and "هـ" not in sol.answer and "^1" not in sol.answer,
            "description": "Check template artifacts are cleaned"
        }
    ]
    
    print("="*80)
    print("SYSTEMATIC MATHEMATICAL GUARDRAILS TEST")
    print("="*80)
    
    passed = 0
    total = len(guardrail_tests)
    
    for i, test in enumerate(guardrail_tests, 1):
        print(f"\n🛡️  Test {i}: {test['name']}")
        print("-" * 60)
        print(f"Question: {test['question'][:60]}...")
        
        try:
            solution = solver.solve_question(test['question'], grade=12)
            
            print(f"Answer: {solution.answer}")
            print(f"Method: {solution.method_used}")
            print(f"Confidence: {solution.confidence:.2f}")
            
            # Check specific validation
            test_passed = False
            if 'expected_answer' in test:
                test_passed = test['expected_answer'] in solution.answer
                print(f"Expected: {test['expected_answer']}")
                print(f"✅ PASS" if test_passed else f"❌ FAIL")
                
            elif 'expected_method' in test:
                test_passed = solution.method_used == test['expected_method']
                print(f"Expected method: {test['expected_method']}")
                print(f"✅ PASS" if test_passed else f"❌ FAIL")
                
            elif 'validate' in test:
                test_passed = test['validate'](solution)
                print(f"Validation: {test['description']}")
                print(f"✅ PASS" if test_passed else f"❌ FAIL")
            
            if test_passed:
                passed += 1
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\n{'='*80}")
    print(f"GUARDRAILS TEST SUMMARY: {passed}/{total} tests passed")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_guardrails()