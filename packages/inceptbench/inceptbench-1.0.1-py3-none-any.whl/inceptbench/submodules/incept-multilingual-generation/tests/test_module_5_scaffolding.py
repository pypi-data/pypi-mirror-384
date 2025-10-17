#!/usr/bin/env python3
"""
Test Module 5 scaffolding generation with DI insights integration
"""

import json
import sys
import os
import logging
import traceback
from typing import Dict, Any
from dataclasses import asdict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Set up logging to see DI insights messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable logging for DI modules
logging.getLogger('src.direct_instruction.di_formats').setLevel(logging.INFO)
logging.getLogger('src.direct_instruction.di_format_model').setLevel(logging.INFO)
logging.getLogger('src.module_5').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

from src.module_5 import Module5ScaffoldingGenerator
from src.dto.question_generation import DetailedExplanation, VoiceoverScript

def test_decimals_skill():
    """Test scaffolding generation for all Decimals skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    decimals_test_cases = [
        {
            "name": "Decimals Format 14.1 - Reading Decimals (Grade 4)",
            "question": "Read this decimal: 0.7",
            "answer": "seven tenths",
            "options": ["seven", "seventy", "seven tenths", "seven hundredths"],
            "subject": "Decimals",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Decimals"
        },
        {
            "name": "Decimals Format 14.2 - Writing Decimals (Grade 4)",
            "question": "Write 'four tenths' as a decimal",
            "answer": "0.4",
            "options": ["0.04", "0.4", "4.0", "40"],
            "subject": "Decimals",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Decimals"
        },
        {
            "name": "Decimals Format 14.3 - Reading and Writing Mixed Decimals (Grade 4)",
            "question": "Read this mixed decimal: 5.3",
            "answer": "five and three tenths",
            "options": ["five point three", "five and three tenths", "fifty-three", "five and thirty"],
            "subject": "Decimals",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Decimals"
        },
        {
            "name": "Decimals Format 14.4 - Converting Equivalent Decimals (Grade 4)",
            "question": "Convert 0.3 to hundredths",
            "answer": "0.30",
            "options": ["0.03", "0.30", "3.0", "30"],
            "subject": "Decimals",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Decimals"
        },
        {
            "name": "Decimals Format 14.5 - Addition/Subtraction Unlike Decimals (Grade 4)",
            "question": "Add: 2.3 + 1.25",
            "answer": "3.55",
            "options": ["3.28", "3.55", "4.3", "3.8"],
            "subject": "Decimals",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Decimals"
        },
        {
            "name": "Decimals Format 14.6 - Rounding Off Decimals (Grade 5)",
            "question": "Round 8.342 to the nearest whole number",
            "answer": "8",
            "options": ["7", "8", "9", "8.3"],
            "subject": "Decimals",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Decimals"
        },
        {
            "name": "Decimals Format 14.7 - Multiplying Decimals (Grade 5)",
            "question": "Multiply: 0.3 × 0.2",
            "answer": "0.06",
            "options": ["0.5", "0.6", "0.06", "0.006"],
            "subject": "Decimals",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Decimals"
        },
        {
            "name": "Decimals Format 14.8 - Division with Decimals Rounding (Grade 5)",
            "question": "Divide and round to the nearest hundredth: 3.1 ÷ 7",
            "answer": "0.44",
            "options": ["0.43", "0.44", "0.45", "0.4"],
            "subject": "Decimals",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Decimals"
        },
        {
            "name": "Decimals Format 14.9 - Multiplying by Multiples of 10 (Grade 5)",
            "question": "Multiply: 0.45 × 100",
            "answer": "45",
            "options": ["4.5", "45", "450", "0.45"],
            "subject": "Decimals",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Decimals"
        },
        {
            "name": "Decimals Format 14.10 - Dividing by Decimals (Grade 5)",
            "question": "Divide: 2.4 ÷ 0.6",
            "answer": "4",
            "options": ["2", "4", "6", "0.4"],
            "subject": "Decimals",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Decimals"
        }
    ]
    
    print("🧮 Testing Decimals Skill Formats...")
    print("=" * 50)
    
    for test_case in decimals_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Decimals skill testing complete")


def test_addition_skill():
    """Test scaffolding generation for all Addition skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    addition_test_cases = [
        {
            "name": "Addition Format 7.1 - Equality Introduction (Grade 0)",
            "question": "3 = ?",
            "answer": "3",
            "options": ["2", "3", "4", "5"],
            "subject": "addition",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Addition"
        },
        {
            "name": "Addition Format 7.2 - Teaching Addition Slow Way (Grade 0)",
            "question": "What is 2 + 1?",
            "answer": "3",
            "options": ["2", "3", "4", "5"],
            "subject": "addition",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Addition"
        },
        {
            "name": "Addition Format 7.3 - Solving Missing Addends (Grade 1)",
            "question": "5 + ? = 8",
            "answer": "3",
            "options": ["2", "3", "4", "5"],
            "subject": "addition",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Addition"
        },
        {
            "name": "Addition Format 7.4 - Teaching Addition Fast Way (Grade 0)",
            "question": "Add: 1 + 4 = ?",
            "answer": "5",
            "options": ["3", "4", "5", "6"],
            "subject": "addition",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Addition"
        },
        {
            "name": "Addition Format 7.5 - Adding Three Single-Digit Numbers (Grade 1)",
            "question": "What is 2 + 3 + 4?",
            "answer": "9",
            "options": ["8", "9", "10", "11"],
            "subject": "addition",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Addition"
        },
        {
            "name": "Addition Format 7.6 - Adding Two Numerals with Renaming (Grade 1)",
            "question": "What is 17 + 15?",
            "answer": "32",
            "options": ["30", "31", "32", "33"],
            "subject": "addition",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Addition"
        },
        {
            "name": "Addition Format 7.7 - Complex Addition Facts Total Less Than 20 (Grade 1)",
            "question": "What is 9 + 7?",
            "answer": "16",
            "options": ["15", "16", "17", "18"],
            "subject": "addition",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Addition"
        }
    ]
    
    print("➕ Testing Addition Skill Formats...")
    print("=" * 50)
    
    for test_case in addition_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Addition skill testing complete")


def test_subtraction_skill():
    """Test scaffolding generation for all Subtraction skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    subtraction_test_cases = [
        {
            "name": "Subtraction Format 8.1 - Subtraction with Lines (Grade 0)",
            "question": "You have 5 lines. Cross out 2. How many are left?",
            "answer": "3",
            "options": ["2", "3", "4", "5"],
            "subject": "subtraction",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Subtraction"
        },
        {
            "name": "Subtraction Format 8.2 - Teaching Regrouping (Grade 1)",
            "question": "What is 14 - 6?",
            "answer": "8",
            "options": ["6", "7", "8", "9"],
            "subject": "subtraction",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Subtraction"
        },
        {
            "name": "Subtraction Format 8.3 - Subtraction with Renaming (Grade 1)",
            "question": "What is 32 - 18?",
            "answer": "14",
            "options": ["12", "13", "14", "15"],
            "subject": "subtraction",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Subtraction"
        },
        {
            "name": "Subtraction Format 8.4 - Tens Numbers Minus One (Grade 2)",
            "question": "What is 30 - 1?",
            "answer": "29",
            "options": ["28", "29", "30", "31"],
            "subject": "subtraction",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Subtraction"
        },
        {
            "name": "Subtraction Format 8.5 - Renaming Numbers with Zeros (Grade 2)",
            "question": "What is 100 - 34?",
            "answer": "66",
            "options": ["64", "65", "66", "67"],
            "subject": "subtraction",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Subtraction"
        }
    ]
    
    print("➖ Testing Subtraction Skill Formats...")
    print("=" * 50)
    
    for test_case in subtraction_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Subtraction skill testing complete")


def test_basic_facts_skill():
    """Test scaffolding generation for all Basic Facts skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    basic_facts_test_cases = [
        {
            "name": "Basic Facts Format 6.1 - Plus-One Facts (Grade 1)",
            "question": "What is 6 + 1?",
            "answer": "7",
            "options": ["5", "6", "7", "8"],
            "subject": "basic facts",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Basic Facts"
        },
        {
            "name": "Basic Facts Format 6.2 - Series Saying (Grade 1)",
            "question": "Continue the pattern: 2, 4, 6, ?",
            "answer": "8",
            "options": ["7", "8", "9", "10"],
            "subject": "basic facts",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Basic Facts"
        },
        {
            "name": "Basic Facts Format 6.3 - Addition and Multiplication Fact Families (Grade 2)",
            "question": "If 3 + 4 = 7, what is 4 + 3?",
            "answer": "7",
            "options": ["6", "7", "8", "12"],
            "subject": "basic facts",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Basic Facts"
        },
        {
            "name": "Basic Facts Format 6.4 - Subtraction and Division Fact Families (Grade 2)",
            "question": "If 8 - 3 = 5, what is 8 - 5?",
            "answer": "3",
            "options": ["2", "3", "4", "5"],
            "subject": "basic facts",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Basic Facts"
        }
    ]
    
    print("🔢 Testing Basic Facts Skill Formats...")
    print("=" * 50)
    
    for test_case in basic_facts_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Basic Facts skill testing complete")


def test_multiplication_skill():
    """Test scaffolding generation for all Multiplication skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    multiplication_test_cases = [
        {
            "name": "Multiplication Format 9.1 - Single Digit Multiplication (Grade 3)",
            "question": "What is 3 × 4?",
            "answer": "12",
            "options": ["10", "11", "12", "13"],
            "subject": "multiplication",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Multiplication"
        },
        {
            "name": "Multiplication Format 9.2 - Missing-Factor Multiplication (Grade 3)",
            "question": "6 × ? = 24",
            "answer": "4",
            "options": ["3", "4", "5", "6"],
            "subject": "multiplication",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Multiplication"
        },
        {
            "name": "Multiplication Format 9.3 - One-Digit Factor Times Two-Digit Factor with Renaming (Grade 3)",
            "question": "What is 4 × 17?",
            "answer": "68",
            "options": ["64", "66", "68", "70"],
            "subject": "multiplication",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Multiplication"
        },
        {
            "name": "Multiplication Format 9.4 - Two-Digit Factor Times Two-Digit Factor (Grade 4)",
            "question": "What is 12 × 13?",
            "answer": "156",
            "options": ["144", "150", "156", "160"],
            "subject": "multiplication",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Multiplication"
        }
    ]
    
    print("✖️ Testing Multiplication Skill Formats...")
    print("=" * 50)
    
    for test_case in multiplication_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Multiplication skill testing complete")


def test_division_skill():
    """Test scaffolding generation for all Division skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    division_test_cases = [
        {
            "name": "Division Format 10.1 - Introducing Division (Grade 3)",
            "question": "What is 12 ÷ 3?",
            "answer": "4",
            "options": ["3", "4", "5", "6"],
            "subject": "division",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Division"
        },
        {
            "name": "Division Format 10.2 - Introducing Division with Remainders (Grade 3)",
            "question": "What is 13 ÷ 4?",
            "answer": "3 R1",
            "options": ["3", "3 R1", "4", "4 R1"],
            "subject": "division",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Division"
        },
        {
            "name": "Division Format 10.3 - Introducing Remainder Facts (Grade 3)",
            "question": "What is 17 ÷ 5?",
            "answer": "3 R2",
            "options": ["3 R1", "3 R2", "4 R1", "4 R2"],
            "subject": "division",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Division"
        },
        {
            "name": "Division Format 10.4 - Remediation Division with Remainders Quotient Too Small (Grade 3)",
            "question": "What is 23 ÷ 6?",
            "answer": "3 R5",
            "options": ["3 R4", "3 R5", "4 R1", "4 R2"],
            "subject": "division",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Division"
        },
        {
            "name": "Division Format 10.5 - Remediation Division with Remainders Quotient Too Large (Grade 3)",
            "question": "What is 19 ÷ 7?",
            "answer": "2 R5",
            "options": ["2 R4", "2 R5", "3 R1", "3 R2"],
            "subject": "division",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Division"
        },
        {
            "name": "Division Format 10.6 - Division with Two-Digit Quotients (Grade 4)",
            "question": "What is 84 ÷ 4?",
            "answer": "21",
            "options": ["20", "21", "22", "23"],
            "subject": "division",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Division"
        },
        {
            "name": "Division Format 10.7 - Rounding to Nearest Tens Unit (Grade 4)",
            "question": "Round 47 to the nearest tens unit for division estimation",
            "answer": "50",
            "options": ["40", "45", "50", "60"],
            "subject": "division",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Division"
        },
        {
            "name": "Division Format 10.8 - Correct Estimated Quotients with Two-Digit Divisors (Grade 5)",
            "question": "Estimate: 156 ÷ 23 (round 23 to 20)",
            "answer": "8",
            "options": ["6", "7", "8", "9"],
            "subject": "division",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Division"
        },
        {
            "name": "Division Format 10.9 - Incorrect Estimated Quotients (Grade 5)",
            "question": "What is 144 ÷ 18?",
            "answer": "8",
            "options": ["6", "7", "8", "9"],
            "subject": "division",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Division"
        }
    ]
    
    print("➗ Testing Division Skill Formats...")
    print("=" * 50)
    
    for test_case in division_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Division skill testing complete")


def test_fractions_skill():
    """Test scaffolding generation for all Fractions skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    fractions_test_cases = [
        {
            "name": "Fractions Format 13.1 - Introducing Fractions (Grade 1)",
            "question": "What fraction of this circle is shaded? (half shaded)",
            "answer": "1/2",
            "options": ["1/3", "1/2", "2/3", "3/4"],
            "subject": "fractions",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.2 - Part-Whole Discrimination (Grade 1)",
            "question": "How many parts make up the whole circle?",
            "answer": "4",
            "options": ["2", "3", "4", "5"],
            "subject": "fractions",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.3 - Writing Numerical Fractions (Grade 1)",
            "question": "Write the fraction for 2 out of 5 parts shaded",
            "answer": "2/5",
            "options": ["2/3", "2/5", "3/5", "5/2"],
            "subject": "fractions",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.4 - Reading Fractions (Grade 2)",
            "question": "How do you read 3/4?",
            "answer": "three fourths",
            "options": ["three fours", "three fourths", "four thirds", "four threes"],
            "subject": "fractions",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.5 - Fraction Comparison to One Whole (Grade 2)",
            "question": "Is 3/4 less than, equal to, or greater than 1?",
            "answer": "less than",
            "options": ["less than", "equal to", "greater than", "cannot tell"],
            "subject": "fractions",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.6 - Reading and Writing Mixed Numerals (Grade 3)",
            "question": "Write this mixed number: two and three fifths",
            "answer": "2 3/5",
            "options": ["2/3/5", "2 3/5", "3 2/5", "5/3"],
            "subject": "fractions",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.7 - Constructing Fractions Equal to 1 (Grade 3)",
            "question": "Which fraction equals 1 whole?",
            "answer": "5/5",
            "options": ["1/5", "5/1", "5/5", "0/5"],
            "subject": "fractions",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.8 - Computing Equivalent Fractions (Grade 4)",
            "question": "What is an equivalent fraction to 1/2?",
            "answer": "2/4",
            "options": ["1/4", "2/4", "1/3", "3/4"],
            "subject": "fractions",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.9 - Determining Factors (Grade 5)",
            "question": "What are the factors of 12?",
            "answer": "1, 2, 3, 4, 6, 12",
            "options": ["1, 2, 6", "1, 2, 3, 4, 6, 12", "2, 4, 6", "1, 3, 4"],
            "subject": "fractions",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.10 - Greatest Common Factor (Grade 5)",
            "question": "What is the GCF of 8 and 12?",
            "answer": "4",
            "options": ["2", "3", "4", "6"],
            "subject": "fractions",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.11 - Reducing Fractions (Grade 5)",
            "question": "Reduce 6/8 to lowest terms",
            "answer": "3/4",
            "options": ["6/8", "3/4", "2/3", "1/2"],
            "subject": "fractions",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.12 - Converting Improper Fractions to Mixed Numbers (Grade 4)",
            "question": "Convert 7/3 to a mixed number",
            "answer": "2 1/3",
            "options": ["1 4/3", "2 1/3", "3 1/7", "7/3"],
            "subject": "fractions",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.13 - Converting Mixed Numbers to Improper Fractions (Grade 4)",
            "question": "Convert 3 1/4 to an improper fraction",
            "answer": "13/4",
            "options": ["12/4", "13/4", "4/13", "3/4"],
            "subject": "fractions",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.14 - Adding Fractions with Like Denominators (Grade 2)",
            "question": "What is 2/5 + 1/5?",
            "answer": "3/5",
            "options": ["2/5", "3/5", "3/10", "4/5"],
            "subject": "fractions",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.15 - Finding Least Common Multiple (Grade 4)",
            "question": "What is the LCM of 4 and 6?",
            "answer": "12",
            "options": ["8", "10", "12", "24"],
            "subject": "fractions",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.16 - Adding Fractions with Unlike Denominators (Grade 4)",
            "question": "What is 1/3 + 1/6?",
            "answer": "1/2",
            "options": ["2/9", "1/2", "2/6", "1/3"],
            "subject": "fractions",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.17 - Multiplying Two Proper Fractions (Grade 4)",
            "question": "What is 1/2 × 1/3?",
            "answer": "1/6",
            "options": ["1/5", "1/6", "2/5", "2/6"],
            "subject": "fractions",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        },
        {
            "name": "Fractions Format 13.18 - Multiplying Fraction and Whole Number (Grade 4)",
            "question": "What is 1/4 × 8?",
            "answer": "2",
            "options": ["1", "2", "4", "8"],
            "subject": "fractions",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Fractions"
        }
    ]
    
    print("🔢 Testing Fractions Skill Formats...")
    print("=" * 50)
    
    for test_case in fractions_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Fractions skill testing complete")


def test_geometry_skill():
    """Test scaffolding generation for all Geometry skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    geometry_test_cases = [
        {
            "name": "Geometry Format 17.1 - Identification/Definition Triangle (Grade 0)",
            "question": "Which shape is a triangle?",
            "answer": "The three-sided shape",
            "options": ["The four-sided shape", "The three-sided shape", "The round shape", "The five-sided shape"],
            "subject": "geometry",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Geometry Format 17.2 - Finding Area of Rectangles (Grade 3)",
            "question": "Calculate the area of a rectangle with length 6 cm and width 4 cm.",
            "answer": "24 cm²",
            "options": ["10 cm²", "20 cm²", "24 cm²", "28 cm²"],
            "subject": "geometry",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Geometry Format 17.3 - Finding Area of Triangles (Grade 6)",
            "question": "Calculate the area of a triangle with base 8 cm and height 5 cm.",
            "answer": "20 cm²",
            "options": ["13 cm²", "20 cm²", "40 cm²", "80 cm²"],
            "subject": "geometry",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Geometry Format 17.4 - Calculating Area of Complex Figures (Grade 6)",
            "question": "Find the area of a shape made of a rectangle (4×3) attached to a triangle (base 4, height 2).",
            "answer": "16 cm²",
            "options": ["12 cm²", "14 cm²", "16 cm²", "18 cm²"],
            "subject": "geometry",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Geometry Format 17.5 - Calculating Area of Parallelograms (Grade 6)",
            "question": "Calculate the area of a parallelogram with base 7 cm and height 4 cm.",
            "answer": "28 cm²",
            "options": ["11 cm²", "22 cm²", "28 cm²", "35 cm²"],
            "subject": "geometry",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Geometry Format 17.6 - Calculating Volume of Boxes (Grade 5)",
            "question": "Calculate the volume of a box with length 4 cm, width 3 cm, and height 2 cm.",
            "answer": "24 cm³",
            "options": ["9 cm³", "14 cm³", "24 cm³", "32 cm³"],
            "subject": "geometry",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Geometry Format 17.7 - Finding Unknown Component Angles (Grade 7)",
            "question": "If two angles in a triangle are 60° and 70°, what is the third angle?",
            "answer": "50°",
            "options": ["40°", "50°", "60°", "70°"],
            "subject": "geometry",
            "grade": 7,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Geometry Format 17.8 - Finding Unknown Angles in Complex Diagrams (Grade 7)",
            "question": "In intersecting lines, if one angle is 130°, what is the opposite angle?",
            "answer": "130°",
            "options": ["50°", "90°", "130°", "180°"],
            "subject": "geometry",
            "grade": 7,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        }
    ]
    
    print("📐 Testing Geometry Skill Formats...")
    print("=" * 50)
    
    for test_case in geometry_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Geometry skill testing complete")


def test_data_analysis_skill():
    """Test scaffolding generation for all Data Analysis skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    data_analysis_test_cases = [
        {
            "name": "Data Analysis Format 16.1 - Sorting (Grade 0)",
            "question": "Sort these shapes: circle, square, circle, triangle. How many circles?",
            "answer": "2",
            "options": ["1", "2", "3", "4"],
            "subject": "data analysis",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        },
        {
            "name": "Data Analysis Format 16.2 - Creating Picture Graphs (Grade 2)",
            "question": "In a picture graph, each symbol represents 2 students. If there are 3 symbols, how many students?",
            "answer": "6",
            "options": ["3", "5", "6", "9"],
            "subject": "data analysis",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        },
        {
            "name": "Data Analysis Format 16.3 - Reading Bar Graphs (Grade 1)",
            "question": "Look at this bar graph. Which color has the highest bar?",
            "answer": "Red",
            "options": ["Red", "Blue", "Green", "Yellow"],
            "subject": "data analysis",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        },
        {
            "name": "Data Analysis Format 16.4 - Creating Bar Graphs (Grade 2)",
            "question": "If you have 4 apples, 2 oranges, and 6 bananas, which fruit would have the tallest bar?",
            "answer": "Bananas",
            "options": ["Apples", "Oranges", "Bananas", "All equal"],
            "subject": "data analysis",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        },
        {
            "name": "Data Analysis Format 16.5 - Calculating the Mean (Grade 6)",
            "question": "Find the mean of these numbers: 4, 6, 8, 10",
            "answer": "7",
            "options": ["6", "7", "8", "9"],
            "subject": "data analysis",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        }
    ]
    
    print("📊 Testing Data Analysis Skill Formats...")
    print("=" * 50)
    
    for test_case in data_analysis_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Data Analysis skill testing complete")


def test_measurement_skill():
    """Test scaffolding generation for all Measurement skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    measurement_test_cases = [
        {
            "name": "Measurement Format 12.1 - Metric Prefixes (Grade 5)",
            "question": "What does the prefix 'centi' mean?",
            "answer": "one hundredth",
            "options": ["one tenth", "one hundredth", "one thousandth", "ten"],
            "subject": "measurement",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        },
        {
            "name": "Measurement Format 12.2 - Metric Conversions (Grade 4)",
            "question": "How many centimeters are in 3 meters?",
            "answer": "300",
            "options": ["30", "300", "3000", "30000"],
            "subject": "measurement",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        },
        {
            "name": "Measurement Format 12.3 - Converting from Mixed Numbers (Grade 4)",
            "question": "Convert 2 1/2 feet to inches",
            "answer": "30 inches",
            "options": ["24 inches", "28 inches", "30 inches", "36 inches"],
            "subject": "measurement",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        },
        {
            "name": "Measurement Format 12.4 - Renaming Customary Units (Grade 4)",
            "question": "How many feet are in 2 yards?",
            "answer": "6",
            "options": ["4", "6", "8", "12"],
            "subject": "measurement",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        },
        {
            "name": "Measurement Format 12.5 - Subtraction with Renaming (Grade 4)",
            "question": "What is 3 feet 2 inches - 1 foot 8 inches?",
            "answer": "1 foot 6 inches",
            "options": ["1 foot 4 inches", "1 foot 6 inches", "2 feet 6 inches", "1 foot 8 inches"],
            "subject": "measurement",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        },
        {
            "name": "Measurement Format 12.6 - Time Minutes After Hour (Grade 2)",
            "question": "If it's 3:15, how do you say the time?",
            "answer": "fifteen minutes after three",
            "options": ["quarter to three", "fifteen minutes after three", "three fifteen", "half past three"],
            "subject": "measurement",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        },
        {
            "name": "Measurement Format 12.7 - Time Minutes Before Hour (Grade 2)",
            "question": "If it's 2:45, how do you say the time?",
            "answer": "fifteen minutes before three",
            "options": ["quarter after two", "fifteen minutes before three", "two forty-five", "half past two"],
            "subject": "measurement",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        },
        {
            "name": "Measurement Format 12.8 - Coin Equivalencies (Grade 2)",
            "question": "How many nickels equal one quarter?",
            "answer": "5",
            "options": ["3", "4", "5", "6"],
            "subject": "measurement",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        },
        {
            "name": "Measurement Format 12.9 - Verifying Change (Grade 2)",
            "question": "You buy something for 75¢ with $1. How much change should you get?",
            "answer": "25¢",
            "options": ["20¢", "25¢", "30¢", "35¢"],
            "subject": "measurement",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        },
        {
            "name": "Measurement Format 12.10 - Counting Coins to Exact Amount (Grade 2)",
            "question": "What coins make exactly 35¢?",
            "answer": "1 quarter and 1 dime",
            "options": ["3 dimes and 1 nickel", "1 quarter and 1 dime", "7 nickels", "35 pennies"],
            "subject": "measurement",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        },
        {
            "name": "Measurement Format 12.11 - Decimal Notation for Money (Grade 4)",
            "question": "Write 3 dollars and 47 cents in decimal form",
            "answer": "$3.47",
            "options": ["$3.47", "$347", "$3.4.7", "$34.7"],
            "subject": "measurement",
            "grade": 4,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Measurement"
        }
    ]
    
    print("📏 Testing Measurement Skill Formats...")
    print("=" * 50)
    
    for test_case in measurement_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Measurement skill testing complete")


def test_counting_skill():
    """Test scaffolding generation for all Counting skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    counting_test_cases = [
        {
            "name": "Counting Format 4.1 - Introducing New Numbers (Grade 0)",
            "question": "Count to 10. What comes after 7?",
            "answer": "8",
            "options": ["6", "7", "8", "9"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        {
            "name": "Counting Format 4.2 - Rational Counting (Grade 0)",
            "question": "How many dots are there? ● ● ● ●",
            "answer": "4",
            "options": ["3", "4", "5", "6"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        {
            "name": "Counting Format 4.3 - Counting Two Groups of Lines (Grade 0)",
            "question": "Count all the lines: ||| and ||. How many lines total?",
            "answer": "5",
            "options": ["4", "5", "6", "7"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        {
            "name": "Counting Format 4.4 - Counting from Numbers Other Than 1 (Grade 0)",
            "question": "Start counting from 5: 5, 6, 7, ?, ?",
            "answer": "8, 9",
            "options": ["7, 8", "8, 9", "9, 10", "10, 11"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        {
            "name": "Counting Format 4.5 - Count-By (Grade 0)",
            "question": "Count by 2s: 2, 4, 6, ?",
            "answer": "8",
            "options": ["7", "8", "9", "10"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        }
    ]
    
    print("🔢 Testing Counting Skill Formats...")
    print("=" * 50)
    
    for test_case in counting_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 50)
    print("✅ Counting skill testing complete")


def test_percent_ratio_probability_skill():
    """Test scaffolding generation for all Percent, Ratio, Probability skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    percent_ratio_probability_test_cases = [
        {
            "name": "Percent Format 15.1 - Converting Percent to Decimal (Grade 7)",
            "question": "Convert 25% to a decimal.",
            "answer": "0.25",
            "options": ["0.025", "0.25", "2.5", "25"],
            "subject": "percent",
            "grade": 7,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Percent, Ratio, Probability"
        },
        {
            "name": "Percent Format 15.2 - Determining Percent One Number is of Another (Grade 7)",
            "question": "What percent is 15 of 60?",
            "answer": "25%",
            "options": ["20%", "25%", "30%", "40%"],
            "subject": "percent",
            "grade": 7,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Percent, Ratio, Probability"
        },
        {
            "name": "Percent Format 15.3 - Finding a Percent of a Number (Grade 7)",
            "question": "What is 30% of 80?",
            "answer": "24",
            "options": ["20", "24", "26", "30"],
            "subject": "percent",
            "grade": 7,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Percent, Ratio, Probability"
        },
        {
            "name": "Percent Format 15.4 - Determining What Percent a Part is of the Whole (Grade 7)",
            "question": "If 12 out of 48 students are absent, what percent are absent?",
            "answer": "25%",
            "options": ["20%", "25%", "30%", "33%"],
            "subject": "percent",
            "grade": 7,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Percent, Ratio, Probability"
        },
        {
            "name": "Ratio Format 15.5 - Determining Ratio Problems (Grade 6)",
            "question": "If there are 3 red balls and 5 blue balls, what is the ratio of red to blue?",
            "answer": "3:5",
            "options": ["3:5", "5:3", "3:8", "5:8"],
            "subject": "ratio",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Percent, Ratio, Probability"
        },
        {
            "name": "Ratio Format 15.6 - Solving Ratio Problems Using Equivalent Fractions (Grade 6)",
            "question": "If the ratio is 2:3 and the first number is 8, what is the second number?",
            "answer": "12",
            "options": ["10", "12", "14", "16"],
            "subject": "ratio",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Percent, Ratio, Probability"
        },
        {
            "name": "Ratio Format 15.7 - Solving Ratio Problems Using Cross Multiplication (Grade 7)",
            "question": "Solve: 3/4 = x/12",
            "answer": "9",
            "options": ["6", "8", "9", "12"],
            "subject": "ratio",
            "grade": 7,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Percent, Ratio, Probability"
        },
        {
            "name": "Probability Format 15.8 - Introduction to Probability Fractions (Grade 5)",
            "question": "What is the probability of getting heads when flipping a coin?",
            "answer": "1/2",
            "options": ["1/4", "1/3", "1/2", "2/3"],
            "subject": "probability",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Percent, Ratio, Probability"
        },
        {
            "name": "Probability Format 15.9 - Writing Probability Fractions (Grade 5)",
            "question": "If you roll a die, what is the probability of getting a 3?",
            "answer": "1/6",
            "options": ["1/3", "1/4", "1/5", "1/6"],
            "subject": "probability",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Percent, Ratio, Probability"
        }
    ]
    
    print("📊 Testing Percent, Ratio, Probability Skill Formats...")
    print("=" * 60)
    
    for test_case in percent_ratio_probability_test_cases:
        try:
            logger.info(f"Testing: {test_case['name']}")
            
            # Generate scaffolding
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 60)
    print("✅ Percent, Ratio, Probability skill testing complete")


def test_pre_algebra_skill():
    """Test scaffolding generation for all Pre-Algebra skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    pre_algebra_test_cases = [
        {
            "name": "Pre-Algebra Format 18.1 - Using and Plotting a Function (Grade 6)",
            "question": "If y = x + 2 and x = 3, what is y?",
            "answer": "5",
            "options": ["1", "3", "5", "6"],
            "subject": "algebra",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Pre-Algebra"
        },
        {
            "name": "Pre-Algebra Format 18.2 - Combining Integers (Grade 7)",
            "question": "What is (-3) + 5?",
            "answer": "2",
            "options": ["-8", "-2", "2", "8"],
            "subject": "algebra",
            "grade": 7,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Pre-Algebra"
        },
        {
            "name": "Pre-Algebra Format 18.3 - Solving One-Step Problems with Variables—Addition and Subtraction (Grade 6)",
            "question": "Solve for x: x + 4 = 9",
            "answer": "5",
            "options": ["3", "4", "5", "13"],
            "subject": "algebra",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Pre-Algebra"
        },
        {
            "name": "Pre-Algebra Format 18.4 - Solving One-Step Problems with Variables—Multiplication and Division (Grade 6)",
            "question": "Solve for x: 3x = 12",
            "answer": "4",
            "options": ["3", "4", "9", "36"],
            "subject": "algebra",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Pre-Algebra"
        },
        {
            "name": "Pre-Algebra Format 18.5 - Ratio Tables Using Fractions for Classes (Grade 7)",
            "question": "If the ratio of boys to girls is 3:4 and there are 12 boys, how many girls are there?",
            "answer": "16",
            "options": ["9", "12", "15", "16"],
            "subject": "algebra",
            "grade": 7,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Pre-Algebra"
        }
    ]
    
    print("=" * 60)
    print("🔢 TESTING PRE-ALGEBRA SKILL (5 formats)")
    print("=" * 60)
    
    for i, test_case in enumerate(pre_algebra_test_cases, 1):
        print(f"\n🧮 Testing {i}/5: {test_case['name']}")
        
        try:
            # Generate scaffolded solution
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 60)
    print("✅ Pre-Algebra skill testing complete")


def test_symbol_identification_place_value_skill():
    """Test scaffolding generation for all Symbol Identification and Place Value skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    symbol_place_value_test_cases = [
        {
            "name": "Symbol ID Format 5.1 - Introducing New Numerals (Grade 0)",
            "question": "What number is this: 7",
            "answer": "seven",
            "options": ["six", "seven", "eight", "nine"],
            "subject": "place value",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.2 - Equation Writing (Grade 0)",
            "question": "Write the number equation for: three plus two equals five",
            "answer": "3 + 2 = 5",
            "options": ["3 + 2 = 5", "2 + 3 = 5", "3 × 2 = 5", "5 - 2 = 3"],
            "subject": "place value",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.3 - Identifying a Symbol and Drawing Lines (Grade 0)",
            "question": "Draw 4 lines to match the number 4",
            "answer": "||||",
            "options": ["|||", "||||", "|||||", "||||||"],
            "subject": "place value",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.4 - Writing a Numeral for a Set of Objects (Grade 0)",
            "question": "Count the objects and write the number: ● ● ● ● ●",
            "answer": "5",
            "options": ["4", "5", "6", "7"],
            "subject": "place value",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.5 - Reading Teen Numerals Using Place Value (Grade 0)",
            "question": "What number is 1 ten and 5 ones?",
            "answer": "15",
            "options": ["14", "15", "16", "51"],
            "subject": "place value",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.6 - Writing Teen Numerals Using Place Value (Grade 0)",
            "question": "Write the number that has 1 ten and 7 ones",
            "answer": "17",
            "options": ["16", "17", "18", "71"],
            "subject": "place value",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.7 - Reading Tens Numerals Using Place Value (Grade 0)",
            "question": "What number is 4 tens and 0 ones?",
            "answer": "40",
            "options": ["4", "14", "40", "400"],
            "subject": "place value",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.8 - Writing Tens Numerals Using Place Value (Grade 0)",
            "question": "Write the number that has 6 tens and 0 ones",
            "answer": "60",
            "options": ["6", "16", "60", "600"],
            "subject": "place value",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.9 - Reading Hundreds Numerals Using Place Value (Grade 2)",
            "question": "What number is 3 hundreds, 2 tens, and 5 ones?",
            "answer": "325",
            "options": ["235", "325", "523", "532"],
            "subject": "place value",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.10 - Writing Hundreds Numerals Using Place Value (Grade 2)",
            "question": "Write the number that has 4 hundreds, 7 tens, and 3 ones",
            "answer": "473",
            "options": ["374", "437", "473", "743"],
            "subject": "place value",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.11 - Reading Thousands Numerals Using Place Value (Grade 3)",
            "question": "What number is 2 thousands, 1 hundred, 4 tens, and 6 ones?",
            "answer": "2146",
            "options": ["1246", "2146", "2164", "6412"],
            "subject": "place value",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.12 - Expanded Notation (Grade 1)",
            "question": "Write 46 in expanded form",
            "answer": "40 + 6",
            "options": ["4 + 6", "40 + 6", "46 + 0", "400 + 60"],
            "subject": "place value",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        {
            "name": "Symbol ID Format 5.13 - Column Alignment (Grade 1)",
            "question": "Line up these numbers to add them: 234 + 56",
            "answer": "Align by place value: hundreds, tens, ones",
            "options": ["234 + 56", "234 + 056", "Align by place value: hundreds, tens, ones", "234 + 560"],
            "subject": "place value",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        }
    ]
    
    print("=" * 60)
    print("🔢 TESTING SYMBOL IDENTIFICATION AND PLACE VALUE SKILL (13 formats)")
    print("=" * 60)
    
    for i, test_case in enumerate(symbol_place_value_test_cases, 1):
        print(f"\n🧮 Testing {i}/13: {test_case['name']}")
        
        try:
            # Generate scaffolded solution
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 60)
    print("✅ Symbol Identification and Place Value skill testing complete")


def test_problem_solving_skill():
    """Test scaffolding generation for all Problem Solving skill formats."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    problem_solving_test_cases = [
        {
            "name": "Problem Solving Format 7.1 - Equality Introduction (Grade 1)",
            "question": "3 = ?",
            "answer": "3",
            "options": ["2", "3", "4", "5"],
            "subject": "problem solving",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Problem Solving"
        },
        {
            "name": "Problem Solving Format 7.2 - Story Problems (Grade 1)",
            "question": "Sarah has 3 apples. Her mom gives her 2 more apples. How many apples does Sarah have now?",
            "answer": "5",
            "options": ["4", "5", "6", "7"],
            "subject": "problem solving",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Problem Solving"
        },
        {
            "name": "Problem Solving Format 7.3 - More Story Problems (Grade 1)",
            "question": "There are 8 birds on a tree. 3 birds fly away. How many birds are left on the tree?",
            "answer": "5",
            "options": ["4", "5", "6", "11"],
            "subject": "problem solving",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Problem Solving"
        }
    ]
    
    print("=" * 60)
    print("🧩 TESTING PROBLEM SOLVING SKILL (3 formats)")
    print("=" * 60)
    
    for i, test_case in enumerate(problem_solving_test_cases, 1):
        print(f"\n🧮 Testing {i}/3: {test_case['name']}")
        
        try:
            # Generate scaffolded solution
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"]
            )
            
            # Log complete result
            logger.info(f"✓ {test_case['name']} - Result: {result}")
            print(f"RESULT FOR {test_case['name']}: {result}")
            
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Convert result to dict if it's not already
            if hasattr(result, '__dict__'):
                result_dict = asdict(result) if hasattr(result, '__dataclass_fields__') else result.__dict__
            else:
                result_dict = result
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_case["name"],
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")
            
        except Exception as e:
            logger.error(f"❌ {test_case['name']} failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    print("=" * 60)
    print("✅ Problem Solving skill testing complete")


def test_scaffolding_with_di_insights():
    """Test scaffolding generation with DI insights for different skills and grades."""
    
    # Initialize Module 5
    module5 = Module5ScaffoldingGenerator()
    
    test_cases = [
        # {
        #     "name": "Grade 1 Addition",
        #     "question": "What is 3 + 4?",
        #     "answer": "7",
        #     "options": ["5", "6", "7", "8"],
        #     "subject": "addition",
        #     "grade": 1,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Addition"
        # },
        # {
        #     "name": "Grade 1 Subtraction",
        #     "question": "If you have 15 apples and you give away 8, how many apples do you have left?",
        #     "answer": "7",
        #     "options": ["15", "0", "8", "7"],
        #     "subject": "subtraction",
        #     "grade": 1,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Subtraction"
        # },
        # {
        #     "name": "Grade 3 Geometry - Rectangle Area",
        #     "question": "Calculate the area of a rectangle with length 2 cm and width 7 cm.",
        #     "answer": "14 cm²",
        #     "options": ["10 cm²", "12 cm²", "16 cm²", "14 cm²"],
        #     "subject": "geometry",
        #     "grade": 3,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Geometry"
        # },
        # {
        #     "name": "Grade 3 Geometry - Square Area",
        #     "question": "What is the area of a square with side length 9 cm?",
        #     "answer": "81 cm²",
        #     "options": ["72 cm²", "81 cm²", "90 cm²", "99 cm²"],
        #     "subject": "geometry",
        #     "grade": 3,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Geometry"
        # },
        # {
        #     "name": "Grade 3 Geometry - Triangle Area",
        #     "question": "Find the area of a triangle with base 1 cm and height 1 cm.",
        #     "answer": "1/2 cm²",
        #     "options": ["1/2 cm²", "1 cm²", "2 cm²", "1/4 cm²"],
        #     "subject": "geometry",
        #     "grade": 3,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Geometry"
        # },
        {
            "name": "Grade 5 3D Geometry - Box Volume",
            "question": "Calculate the volume of a box with length 4 cm, width 3 cm, and height 2 cm.",
            "answer": "24 cm³",
            "options": ["9 cm³", "14 cm³", "24 cm³", "32 cm³"],
            "subject": "geometry",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Grade 5 3D Geometry - Cube Volume",
            "question": "What is the volume of a cube-shaped box with side length 3 cm?",
            "answer": "27 cm³",
            "options": ["9 cm³", "18 cm³", "27 cm³", "36 cm³"],
            "subject": "geometry",
            "grade": 5,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Grade 0 Geometry - Triangle Identification",
            "question": "Which shape is a triangle?",
            "answer": "The three-sided shape",
            "options": ["The four-sided shape", "The three-sided shape", "The round shape", "The five-sided shape"],
            "subject": "geometry",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Grade 3 Geometry - Rectangle Area",
            "question": "Calculate the area of a rectangle with length 6 cm and width 4 cm.",
            "answer": "24 cm²",
            "options": ["10 cm²", "20 cm²", "24 cm²", "28 cm²"],
            "subject": "geometry",
            "grade": 3,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Grade 6 Geometry - Triangle Area",
            "question": "Find the area of a triangle with base 8 cm and height 5 cm.",
            "answer": "20 cm²",
            "options": ["13 cm²", "20 cm²", "40 cm²", "80 cm²"],
            "subject": "geometry",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Grade 6 Geometry - Complex Figure Area",
            "question": "Calculate the total area of a shape made of two rectangles: one 4×3 cm and one 2×5 cm.",
            "answer": "22 cm²",
            "options": ["17 cm²", "22 cm²", "27 cm²", "32 cm²"],
            "subject": "geometry",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Grade 6 Geometry - Parallelogram Area",
            "question": "Find the area of a parallelogram with base 7 cm and height 3 cm.",
            "answer": "21 cm²",
            "options": ["10 cm²", "14 cm²", "21 cm²", "28 cm²"],
            "subject": "geometry",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        {
            "name": "Grade 7 Geometry - Unknown Angles",
            "question": "In a triangle, two angles are 45° and 60°. What is the third angle?",
            "answer": "75°",
            "options": ["65°", "70°", "75°", "80°"],
            "subject": "geometry",
            "grade": 7,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Geometry"
        },
        # ============= CHAPTER 2: BASIC FACTS =============
        {
            "name": "Grade 1 Basic Facts - Format 6.1 Plus-One Facts",
            "question": "What is 6 + 1?",
            "answer": "7",
            "options": ["5", "6", "7", "8"],
            "subject": "basic facts",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Basic Facts"
        },
        {
            "name": "Grade 1 Basic Facts - Format 6.2 Series Saying",
            "question": "Continue the pattern: 2, 4, 6, ?",
            "answer": "8",
            "options": ["7", "8", "9", "10"],
            "subject": "basic facts",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Basic Facts"
        },
        {
            "name": "Grade 2 Basic Facts - Format 6.3 Addition and Multiplication Fact Families",
            "question": "If 3 + 4 = 7, what is 4 + 3?",
            "answer": "7",
            "options": ["6", "7", "8", "12"],
            "subject": "basic facts",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Basic Facts"
        },
        {
            "name": "Grade 2 Basic Facts - Format 6.4 Subtraction and Division Fact Families",
            "question": "If 8 - 3 = 5, what is 8 - 5?",
            "answer": "3",
            "options": ["2", "3", "4", "5"],
            "subject": "basic facts",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Basic Facts"
        },
        
        # ============= CHAPTER 3: COUNTING =============
        {
            "name": "Grade 0 Counting - Format 4.1 Introducing New Numbers",
            "question": "Count to 10. What comes after 7?",
            "answer": "8",
            "options": ["6", "7", "8", "9"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        {
            "name": "Grade 0 Counting - Format 4.2 Rational Counting",
            "question": "How many dots are there? ● ● ● ●",
            "answer": "4",
            "options": ["3", "4", "5", "6"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        {
            "name": "Grade 0 Counting - Format 4.3 Counting Two Groups of Lines",
            "question": "Group 1 has 3 lines, Group 2 has 2 lines. How many lines altogether?",
            "answer": "5",
            "options": ["4", "5", "6", "7"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        {
            "name": "Grade 0 Counting - Format 4.4 Counting From Numbers Other Than 1",
            "question": "Start counting from 5: 5, 6, 7, ?",
            "answer": "8",
            "options": ["7", "8", "9", "10"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        {
            "name": "Grade 0 Counting - Format 4.5 Count-By",
            "question": "Count by 2s: 2, 4, 6, ?",
            "answer": "8",
            "options": ["7", "8", "9", "10"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        
        # ============= CHAPTER 4: DATA ANALYSIS =============
        {
            "name": "Grade 0 Data Analysis - Format 16.1 Sorting",
            "question": "Sort these shapes: circle, square, circle, triangle. How many circles?",
            "answer": "2",
            "options": ["1", "2", "3", "4"],
            "subject": "data analysis",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        },
        {
            "name": "Grade 2 Data Analysis - Format 16.2 Creating Picture Graphs",
            "question": "In a picture graph, each symbol represents 2 students. If there are 3 symbols, how many students?",
            "answer": "6",
            "options": ["3", "5", "6", "9"],
            "subject": "data analysis",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        },
        {
            "name": "Grade 1 Data Analysis - Format 16.3 Reading Bar Graphs",
            "question": "In a bar graph, the red bar reaches 4 and the blue bar reaches 7. How many more blue than red?",
            "answer": "3",
            "options": ["2", "3", "4", "11"],
            "subject": "data analysis",
            "grade": 1,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        },
        {
            "name": "Grade 2 Data Analysis - Format 16.4 Creating Bar Graphs",
            "question": "You survey 5 cats, 3 dogs, and 2 birds. How tall should the cat bar be?",
            "answer": "5",
            "options": ["3", "5", "8", "10"],
            "subject": "data analysis",
            "grade": 2,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        },
        {
            "name": "Grade 6 Data Analysis - Format 16.5 Calculating the Mean",
            "question": "Find the mean of these numbers: 4, 6, 8, 10",
            "answer": "7",
            "options": ["6", "7", "8", "28"],
            "subject": "data analysis",
            "grade": 6,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        },
        {
            "name": "Grade 0 Counting - Introducing New Numbers",
            "question": "Count to 10. What comes after 7?",
            "answer": "8",
            "options": ["6", "7", "8", "9"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        {
            "name": "Grade 0 Counting - Rational Counting",
            "question": "How many dots are there? ● ● ● ●",
            "answer": "4",
            "options": ["3", "4", "5", "6"],
            "subject": "counting",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Counting"
        },
        {
            "name": "Grade 0 Data Analysis - Sorting",
            "question": "Sort these shapes: circle, square, circle, triangle. How many circles?",
            "answer": "2",
            "options": ["1", "2", "3", "4"],
            "subject": "data analysis",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Data Analysis"
        },
        {
            "name": "Grade 0 Subtraction - Subtraction with Lines",
            "question": "You have 5 lines. Cross out 2. How many are left?",
            "answer": "3",
            "options": ["2", "3", "4", "5"],
            "subject": "subtraction",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Subtraction"
        },
        {
            "name": "Grade 0 Place Value - Introducing New Numerals",
            "question": "What number is this: 7",
            "answer": "seven",
            "options": ["six", "seven", "eight", "nine"],
            "subject": "place value",
            "grade": 0,
            "language": "en",
            "country": "UAE",
            "expected_di_skill": "Symbol Identification and Place Value"
        },
        # {
        #     "name": "Grade 1 Subtraction",
        #     "question": "If you have 5 apples and you give away 15, how many apples do you have left?",
        #     "answer": "-10",
        #     "options": ["10", "0", "5", "-10"],
        #     "subject": "subtraction",
        #     "grade": 1,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Subtraction"
        # },
        # {
        #     "name": "Grade 3 Multiplication",
        #     "question": "What is 6 × 7?",
        #     "answer": "42",
        #     "options": ["36", "40", "42", "48"],
        #     "subject": "multiplication",
        #     "grade": 3,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Multiplication"
        # },
        # {
        #     "name": "Grade 4 Division",
        #     "question": "What is 24 ÷ 6?",
        #     "answer": "4",
        #     "options": ["3", "4", "5", "6"],
        #     "subject": "division",
        #     "grade": 4,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Division"
        # },
        # {
        #     "name": "Grade 3 Fractions",
        #     "question": "What is 1/2 + 1/4?",
        #     "answer": "3/4",
        #     "options": ["2/6", "3/4", "1/6", "2/4"],
        #     "subject": "fractions",
        #     "grade": 3,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Fractions"
        # },
        # {
        #     "name": "Grade 5 Decimals",
        #     "question": "What is 2.5 + 1.3?",
        #     "answer": "3.8",
        #     "options": ["3.7", "3.8", "3.9", "4.0"],
        #     "subject": "decimals",
        #     "grade": 5,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Decimals"
        # },
        # {
        #     "name": "Grade 2 Geometry",
        #     "question": "How many sides does a triangle have?",
        #     "answer": "3",
        #     "options": ["2", "3", "4", "5"],
        #     "subject": "geometry",
        #     "grade": 2,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Geometry"
        # },
        # {
        #     "name": "Grade 1 Counting",
        #     "question": "Count the apples: 🍎🍎🍎🍎🍎",
        #     "answer": "5",
        #     "options": ["4", "5", "6", "7"],
        #     "subject": "counting",
        #     "grade": 1,
        #     "language": "en",
        #     "country": "UAE",
        #     "expected_di_skill": "Counting"
        # }
    ]
    
    logger.info("=" * 80)
    logger.info("Testing Module 5 Scaffolding with DI Insights")
    logger.info("=" * 80)
    
    for test_case in test_cases:
        logger.info(f"\n📚 Testing: {test_case['name']}")
        logger.info("-" * 40)
        logger.info(f"Question: {test_case['question']}")
        logger.info(f"Subject: {test_case['subject']}, Grade: {test_case['grade']}")
        
        try:
            # Generate scaffolded solution (not async)
            result = module5.generate_scaffolded_solution(
                question_text=test_case["question"],
                correct_answer=test_case["answer"],
                subject=test_case["subject"],
                grade=test_case["grade"],
                language=test_case["language"],
            )
            
            logger.info(f"Result:")
            # Convert dataclass to dict for JSON serialization
            result_dict = asdict(result)
            logger.info(json.dumps(result_dict, indent=2, default=str))
            
            logger.info("⚡ Starting file writing process...")
            # Append to JSONL file
            data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
            os.makedirs(data_dir, exist_ok=True)
            jsonl_file = os.path.join(data_dir, "test_results_dspy.jsonl")
            
            # Generate test name with format number for HTML viewer compatibility
            format_info = ""
            if hasattr(result, 'di_formats_used') and result.di_formats_used:
                first_format = result.di_formats_used[0]
                if isinstance(first_format, dict) and first_format.get('format_number'):
                    format_info = f" Format {first_format['format_number']}"
            
            test_name_with_format = test_case["name"] + format_info
            
            logger.info(f"Writing to file: {jsonl_file}")
            with open(jsonl_file, "a", encoding="utf-8") as f:
                output_data = {
                    "test_name": test_name_with_format,
                    "question": test_case["question"],
                    "answer": test_case["answer"],
                    "subject": test_case["subject"],
                    "grade": test_case["grade"],
                    "result": result_dict
                }
                
                # Explicitly extract di_formats_used if available
                if hasattr(result, 'di_formats_used'):
                    output_data["di_formats_used"] = result.di_formats_used
                    logger.info(f"DI Formats Used: {len(result.di_formats_used) if result.di_formats_used else 0} formats")
                elif isinstance(result_dict, dict) and 'di_formats_used' in result_dict:
                    output_data["di_formats_used"] = result_dict['di_formats_used']
                    logger.info(f"DI Formats Used: {len(result_dict['di_formats_used']) if result_dict['di_formats_used'] else 0} formats")
                
                json.dump(output_data, f, ensure_ascii=False)
                f.write("\n")
                f.flush()  # Force immediate write to disk
            logger.info(f"✅ Successfully wrote test result to {jsonl_file}")

            # Check if result contains expected fields (ScaffoldedSolution object)
            assert hasattr(result, "detailed_explanation"), "Missing detailed_explanation"
            assert hasattr(result, "voiceover_script"), "Missing voiceover_script"
            
            detailed_exp = result.detailed_explanation
            voiceover = result.voiceover_script
            
            
            
            
        except Exception as e:
            logger.info(f"❌ Test failed for {test_case['name']}: {e}")
            traceback.print_exc()
    
    logger.info("\n" + "=" * 80)
    logger.info("Test Suite Complete!")
    logger.info("=" * 80)


def main():
    """Run tests based on command line arguments."""
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1].lower()
        
        if test_name == "decimals":
            test_decimals_skill()
        elif test_name == "addition":
            test_addition_skill()
        elif test_name == "subtraction":
            test_subtraction_skill()
        elif test_name == "basicfacts":
            test_basic_facts_skill()
        elif test_name == "multiplication":
            test_multiplication_skill()
        elif test_name == "division":
            test_division_skill()
        elif test_name == "fractions":
            test_fractions_skill()
        elif test_name == "geometry":
            test_geometry_skill()
        elif test_name == "dataanalysis":
            test_data_analysis_skill()
        elif test_name == "measurement":
            test_measurement_skill()
        elif test_name == "counting":
            test_counting_skill()
        elif test_name == "percent":
            test_percent_ratio_probability_skill()
        elif test_name == "prealgebra":
            test_pre_algebra_skill()
        elif test_name == "symbolplacevalue":
            test_symbol_identification_place_value_skill()
        elif test_name == "problemsolving":
            test_problem_solving_skill()
        elif test_name == "all":
            print("Running all skill tests...")
            test_decimals_skill()
            test_addition_skill()
            test_subtraction_skill()
            test_basic_facts_skill()
            test_multiplication_skill()
            test_division_skill()
            test_fractions_skill()
            test_geometry_skill()
            test_data_analysis_skill()
            test_measurement_skill()
            test_counting_skill()
            test_percent_ratio_probability_skill()
            test_pre_algebra_skill()
            test_symbol_identification_place_value_skill()
            test_problem_solving_skill()
            test_scaffolding_with_di_insights()
        else:
            print("Available tests:")
            print("  python tests/test_module_5_scaffolding.py decimals")
            print("  python tests/test_module_5_scaffolding.py addition") 
            print("  python tests/test_module_5_scaffolding.py subtraction")
            print("  python tests/test_module_5_scaffolding.py basicfacts")
            print("  python tests/test_module_5_scaffolding.py multiplication")
            print("  python tests/test_module_5_scaffolding.py division")
            print("  python tests/test_module_5_scaffolding.py fractions")
            print("  python tests/test_module_5_scaffolding.py geometry")
            print("  python tests/test_module_5_scaffolding.py dataanalysis")
            print("  python tests/test_module_5_scaffolding.py measurement")
            print("  python tests/test_module_5_scaffolding.py counting")
            print("  python tests/test_module_5_scaffolding.py percent")
            print("  python tests/test_module_5_scaffolding.py prealgebra")
            print("  python tests/test_module_5_scaffolding.py symbolplacevalue")
            print("  python tests/test_module_5_scaffolding.py problemsolving")
            print("  python tests/test_module_5_scaffolding.py all")
            print("  python tests/test_module_5_scaffolding.py")
    else:
        # Default: run the original comprehensive test
        test_scaffolding_with_di_insights()

if __name__ == "__main__":
    main()