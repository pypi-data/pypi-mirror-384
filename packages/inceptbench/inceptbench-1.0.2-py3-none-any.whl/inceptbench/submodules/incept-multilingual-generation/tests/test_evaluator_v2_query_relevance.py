"""
Test case for evaluator v2 query relevance veto functionality.
Tests that questions unrelated to the original query are automatically rejected.
"""
import sys
import os

from dotenv import load_dotenv
load_dotenv()

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.evaluator.v2 import ResponseEvaluator, EvaluationDimension
from src.dto.question_generation import (
    GenerateQuestionsRequest,
    GenerateQuestionResponse,
    GeneratedQuestion,
    SkillContext,
    DetailedExplanation,
    ExplanationStep,
    PersonalizedInsight,
    VoiceoverScript,
    VoiceoverStepScript
)


def create_test_question(question_text: str, answer: str, options: dict, answer_choice: str) -> GeneratedQuestion:
    """Helper to create a test question with full scaffolding."""
    return GeneratedQuestion(
        type="mcq",
        question=question_text,
        answer=answer,
        difficulty="medium",
        explanation=f"The correct answer is {answer}.",
        options=options,
        answer_choice=answer_choice,
        detailed_explanation=DetailedExplanation(
            steps=[
                ExplanationStep(
                    title="Step 1: Understand the problem",
                    content=f"We need to find the correct answer.",
                    image=None,
                    image_alt_text=None
                ),
                ExplanationStep(
                    title="Step 2: Find the solution",
                    content=f"The answer is {answer}.",
                    image=None,
                    image_alt_text=None
                )
            ],
            personalized_academic_insights=[
                PersonalizedInsight(
                    answer=answer,
                    insight="This is correct!"
                )
            ]
        ),
        voiceover_script=VoiceoverScript(
            question_script=question_text,
            answer_choice_scripts=list(options.values()),
            explanation_step_scripts=[
                VoiceoverStepScript(step_number=1, script="Step 1"),
                VoiceoverStepScript(step_number=2, script="Step 2")
            ]
        )
    )


def test_query_relevance_rejection():
    """
    Test that questions unrelated to the original query are rejected due to query relevance veto.
    """
    print("🧪 Testing Query Relevance Veto Functionality\n")

    # Create a request asking for GEOMETRY questions about quadrilaterals
    request = GenerateQuestionsRequest(
        grade=5,
        instructions="Generate questions about quadrilaterals and their properties",
        count=1,
        question_type="mcq",
        language="english",
        difficulty="medium",
        subject="mathematics",
        skill=SkillContext(
            title="Quadrilaterals",
            unit_name="Geometry",
            lesson_title="Properties of Quadrilaterals",
            standard_description="Identify and classify quadrilaterals based on their properties"
        )
    )

    # Create an OFF-TOPIC question about ALGEBRA (not geometry/quadrilaterals)
    # This should be rejected due to poor query relevance
    off_topic_question = create_test_question(
        question_text="What is the value of x in the equation 2x + 5 = 13?",
        answer="4",
        options={"A": "3", "B": "4", "C": "5", "D": "6"},
        answer_choice="B"
    )

    # Create a RELEVANT question about quadrilaterals
    # This should pass query relevance check
    relevant_question = create_test_question(
        question_text="Which of the following is a quadrilateral with four equal sides?",
        answer="Square",
        options={"A": "Triangle", "B": "Circle", "C": "Square", "D": "Pentagon"},
        answer_choice="C"
    )

    # Test 1: Off-topic question should be REJECTED
    print("=" * 70)
    print("TEST 1: Off-topic Question (Algebra instead of Quadrilaterals)")
    print("=" * 70)

    response_off_topic = GenerateQuestionResponse(
        data=[off_topic_question],
        request_id="test_off_topic_001",
        total_questions=1,
        grade=5
    )

    evaluator = ResponseEvaluator(parallel_workers=1)
    evaluation_off_topic = evaluator.evaluate_response(
        request=request,
        response=response_off_topic,
        update_baseline=False
    )

    print(f"\n📊 Evaluation Results for Off-topic Question:")
    print(f"Overall Score: {evaluation_off_topic.overall_score:.2%}")

    question_eval = evaluation_off_topic.question_evaluations[0]
    query_relevance_score = question_eval.scores.get(EvaluationDimension.QUERY_RELEVANCE, 0.0)

    print(f"Query Relevance Score: {query_relevance_score:.2%}")
    print(f"Recommendation: {question_eval.recommendation.upper()}")

    if question_eval.issues:
        print(f"\n❌ Issues Found:")
        for issue in question_eval.issues:
            print(f"  • {issue}")

    # Verify veto was triggered
    if question_eval.recommendation == "reject" and query_relevance_score < 0.4:
        print(f"\n✅ TEST 1 PASSED: Off-topic question correctly REJECTED")
        print(f"   Veto triggered: query_relevance ({query_relevance_score:.2%}) < 0.4")
    else:
        print(f"\n❌ TEST 1 FAILED: Off-topic question should be rejected")
        print(f"   Expected: recommendation='reject' and query_relevance < 0.4")
        print(f"   Got: recommendation='{question_eval.recommendation}', query_relevance={query_relevance_score:.2%}")

    # Test 2: Relevant question should NOT be rejected on query relevance
    print("\n" + "=" * 70)
    print("TEST 2: Relevant Question (Quadrilaterals as requested)")
    print("=" * 70)

    response_relevant = GenerateQuestionResponse(
        data=[relevant_question],
        request_id="test_relevant_001",
        total_questions=1,
        grade=5
    )

    evaluation_relevant = evaluator.evaluate_response(
        request=request,
        response=response_relevant,
        update_baseline=False
    )

    print(f"\n📊 Evaluation Results for Relevant Question:")
    print(f"Overall Score: {evaluation_relevant.overall_score:.2%}")

    question_eval_relevant = evaluation_relevant.question_evaluations[0]
    query_relevance_score_relevant = question_eval_relevant.scores.get(EvaluationDimension.QUERY_RELEVANCE, 0.0)

    print(f"Query Relevance Score: {query_relevance_score_relevant:.2%}")
    print(f"Recommendation: {question_eval_relevant.recommendation.upper()}")

    if question_eval_relevant.strengths:
        print(f"\n✅ Strengths Found:")
        for strength in question_eval_relevant.strengths:
            print(f"  • {strength}")

    if question_eval_relevant.issues:
        print(f"\n⚠️  Issues Found:")
        for issue in question_eval_relevant.issues:
            print(f"  • {issue}")

    # Verify query relevance is acceptable
    if query_relevance_score_relevant >= 0.4:
        print(f"\n✅ TEST 2 PASSED: Relevant question has acceptable query relevance")
        print(f"   Query relevance ({query_relevance_score_relevant:.2%}) >= 0.4")
    else:
        print(f"\n❌ TEST 2 FAILED: Relevant question should have high query relevance")
        print(f"   Expected: query_relevance >= 0.4")
        print(f"   Got: query_relevance={query_relevance_score_relevant:.2%}")

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    test1_passed = question_eval.recommendation == "reject" and query_relevance_score < 0.4
    test2_passed = query_relevance_score_relevant >= 0.4

    print(f"Test 1 (Off-topic rejection): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (Relevant acceptance): {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print(f"\n🎉 ALL TESTS PASSED: Query relevance veto is working correctly!")
        return True
    else:
        print(f"\n⚠️  SOME TESTS FAILED: Review evaluator behavior")
        return False


def test_query_relevance_with_different_subjects():
    """
    Test query relevance across different subject mismatches.
    """
    print("\n\n" + "=" * 70)
    print("ADDITIONAL TEST: Cross-subject Query Relevance")
    print("=" * 70)

    # Request: SCIENCE question about photosynthesis
    request = GenerateQuestionsRequest(
        grade=7,
        instructions="Generate questions about photosynthesis in plants",
        count=1,
        question_type="mcq",
        language="english",
        difficulty="medium",
        subject="science",
        topic="Photosynthesis"
    )

    # Generated: HISTORY question (completely wrong subject)
    history_question = create_test_question(
        question_text="Who was the first president of the United States?",
        answer="George Washington",
        options={"A": "George Washington", "B": "Thomas Jefferson", "C": "John Adams", "D": "Abraham Lincoln"},
        answer_choice="A"
    )

    response = GenerateQuestionResponse(
        data=[history_question],
        request_id="test_cross_subject_001",
        total_questions=1,
        grade=7
    )

    evaluator = ResponseEvaluator(parallel_workers=1)
    evaluation = evaluator.evaluate_response(
        request=request,
        response=response,
        update_baseline=False
    )

    question_eval = evaluation.question_evaluations[0]
    query_relevance_score = question_eval.scores.get(EvaluationDimension.QUERY_RELEVANCE, 0.0)

    print(f"\nRequest: Science (Photosynthesis)")
    print(f"Generated: History (US Presidents)")
    print(f"Query Relevance Score: {query_relevance_score:.2%}")
    print(f"Recommendation: {question_eval.recommendation.upper()}")

    if question_eval.recommendation == "reject":
        print(f"\n✅ Cross-subject mismatch correctly REJECTED")
        return True
    else:
        print(f"\n⚠️  Cross-subject mismatch should be rejected")
        return False


def test_wrong_math_topic():
    """
    Test: Request multiplication, get division instead (same subject, wrong topic).
    """
    print("\n\n" + "=" * 70)
    print("TEST 3: Wrong Math Topic (Multiplication → Division)")
    print("=" * 70)

    request = GenerateQuestionsRequest(
        grade=3,
        instructions="Generate multiplication problems with single-digit numbers",
        count=1,
        question_type="mcq",
        language="english",
        difficulty="easy",
        subject="mathematics",
        topic="Multiplication"
    )

    # Generated: Division question instead of multiplication
    division_question = create_test_question(
        question_text="What is 24 ÷ 6?",
        answer="4",
        options={"A": "3", "B": "4", "C": "5", "D": "6"},
        answer_choice="B"
    )

    response = GenerateQuestionResponse(
        data=[division_question],
        request_id="test_wrong_topic_001",
        total_questions=1,
        grade=3
    )

    evaluator = ResponseEvaluator(parallel_workers=1)
    evaluation = evaluator.evaluate_response(
        request=request,
        response=response,
        update_baseline=False
    )

    question_eval = evaluation.question_evaluations[0]
    query_relevance_score = question_eval.scores.get(EvaluationDimension.QUERY_RELEVANCE, 0.0)

    print(f"\nRequest: Multiplication")
    print(f"Generated: Division")
    print(f"Query Relevance Score: {query_relevance_score:.2%}")
    print(f"Recommendation: {question_eval.recommendation.upper()}")

    if question_eval.issues:
        print(f"\n❌ Issues Found:")
        for issue in question_eval.issues:
            print(f"  • {issue}")

    # Division is a different operation, should have low relevance
    if query_relevance_score < 0.4:
        print(f"\n✅ TEST 3 PASSED: Wrong topic correctly identified (score < 0.4)")
        return True
    else:
        print(f"\n⚠️  TEST 3 UNCLEAR: Query relevance = {query_relevance_score:.2%}")
        return False


def test_partial_relevance():
    """
    Test: Request fractions, get decimals (related but not exact match).
    Should have moderate relevance, not auto-reject.
    """
    print("\n\n" + "=" * 70)
    print("TEST 4: Partial Relevance (Fractions → Decimals)")
    print("=" * 70)

    request = GenerateQuestionsRequest(
        grade=4,
        instructions="Generate questions about adding fractions with like denominators",
        count=1,
        question_type="mcq",
        language="english",
        difficulty="medium",
        subject="mathematics",
        topic="Fractions"
    )

    # Generated: Decimal question (related to fractions but different)
    decimal_question = create_test_question(
        question_text="What is 0.5 + 0.25?",
        answer="0.75",
        options={"A": "0.5", "B": "0.75", "C": "1.0", "D": "0.25"},
        answer_choice="B"
    )

    response = GenerateQuestionResponse(
        data=[decimal_question],
        request_id="test_partial_001",
        total_questions=1,
        grade=4
    )

    evaluator = ResponseEvaluator(parallel_workers=1)
    evaluation = evaluator.evaluate_response(
        request=request,
        response=response,
        update_baseline=False
    )

    question_eval = evaluation.question_evaluations[0]
    query_relevance_score = question_eval.scores.get(EvaluationDimension.QUERY_RELEVANCE, 0.0)

    print(f"\nRequest: Fractions")
    print(f"Generated: Decimals")
    print(f"Query Relevance Score: {query_relevance_score:.2%}")
    print(f"Recommendation: {question_eval.recommendation.upper()}")

    # Decimals are related to fractions, might get moderate score
    # Should be in the 0.4-0.7 range (not rejected, but marked for revision)
    if 0.3 <= query_relevance_score <= 0.8:
        print(f"\n✅ TEST 4 PASSED: Partial relevance correctly scored in moderate range")
        return True
    else:
        print(f"\n⚠️  TEST 4 NOTE: Score {query_relevance_score:.2%} outside expected range 0.3-0.8")
        return False


def test_correct_skill_alignment():
    """
    Test: Request specific skill, get exactly that skill.
    Should have very high query relevance (>= 0.7).
    """
    print("\n\n" + "=" * 70)
    print("TEST 5: Perfect Skill Alignment")
    print("=" * 70)

    request = GenerateQuestionsRequest(
        grade=6,
        instructions="Generate questions about calculating the area of rectangles",
        count=1,
        question_type="mcq",
        language="english",
        difficulty="medium",
        subject="mathematics",
        skill=SkillContext(
            title="Area of Rectangles",
            unit_name="Geometry",
            lesson_title="Area and Perimeter",
            standard_description="Calculate the area of rectangles using length × width"
        )
    )

    # Generated: Perfect match - area of rectangle question
    area_question = create_test_question(
        question_text="A rectangle has length 8 cm and width 5 cm. What is its area?",
        answer="40 cm²",
        options={"A": "13 cm²", "B": "26 cm²", "C": "40 cm²", "D": "80 cm²"},
        answer_choice="C"
    )

    response = GenerateQuestionResponse(
        data=[area_question],
        request_id="test_perfect_001",
        total_questions=1,
        grade=6
    )

    evaluator = ResponseEvaluator(parallel_workers=1)
    evaluation = evaluator.evaluate_response(
        request=request,
        response=response,
        update_baseline=False
    )

    question_eval = evaluation.question_evaluations[0]
    query_relevance_score = question_eval.scores.get(EvaluationDimension.QUERY_RELEVANCE, 0.0)

    print(f"\nRequest: Area of Rectangles")
    print(f"Generated: Area of Rectangle Question")
    print(f"Query Relevance Score: {query_relevance_score:.2%}")
    print(f"Recommendation: {question_eval.recommendation.upper()}")

    if question_eval.strengths:
        print(f"\n✅ Strengths Found:")
        for strength in question_eval.strengths:
            print(f"  • {strength}")

    # Perfect match should score high (>= 0.7)
    if query_relevance_score >= 0.7:
        print(f"\n✅ TEST 5 PASSED: Perfect alignment scored >= 0.7")
        return True
    else:
        print(f"\n❌ TEST 5 FAILED: Perfect alignment should score >= 0.7, got {query_relevance_score:.2%}")
        return False


def test_wrong_grade_level_content():
    """
    Test: Request grade 2 content, get calculus (completely inappropriate grade level).
    """
    print("\n\n" + "=" * 70)
    print("TEST 6: Wrong Grade Level (Grade 2 → Calculus)")
    print("=" * 70)

    request = GenerateQuestionsRequest(
        grade=2,
        instructions="Generate simple addition problems for second graders",
        count=1,
        question_type="mcq",
        language="english",
        difficulty="easy",
        subject="mathematics",
        topic="Addition"
    )

    # Generated: Calculus question (way too advanced)
    calculus_question = create_test_question(
        question_text="What is the derivative of f(x) = x² + 3x?",
        answer="2x + 3",
        options={"A": "x + 3", "B": "2x + 3", "C": "x²", "D": "3x"},
        answer_choice="B"
    )

    response = GenerateQuestionResponse(
        data=[calculus_question],
        request_id="test_wrong_grade_001",
        total_questions=1,
        grade=2
    )

    evaluator = ResponseEvaluator(parallel_workers=1)
    evaluation = evaluator.evaluate_response(
        request=request,
        response=response,
        update_baseline=False
    )

    question_eval = evaluation.question_evaluations[0]
    query_relevance_score = question_eval.scores.get(EvaluationDimension.QUERY_RELEVANCE, 0.0)
    grade_alignment_score = question_eval.scores.get(EvaluationDimension.GRADE_ALIGNMENT, 0.0)

    print(f"\nRequest: Grade 2 Addition")
    print(f"Generated: Calculus Derivative")
    print(f"Query Relevance Score: {query_relevance_score:.2%}")
    print(f"Grade Alignment Score: {grade_alignment_score:.2%}")
    print(f"Recommendation: {question_eval.recommendation.upper()}")

    # Should be rejected (either on query relevance or grade alignment)
    if question_eval.recommendation == "reject":
        print(f"\n✅ TEST 6 PASSED: Wrong grade level content correctly REJECTED")
        return True
    else:
        print(f"\n⚠️  TEST 6 FAILED: Should reject inappropriate grade level content")
        return False


def test_language_mismatch():
    """
    Test: Request Arabic questions, generate English questions.
    """
    print("\n\n" + "=" * 70)
    print("TEST 7: Language Mismatch (Arabic → English)")
    print("=" * 70)

    request = GenerateQuestionsRequest(
        grade=5,
        instructions="توليد أسئلة حول الكسور",  # "Generate questions about fractions" in Arabic
        count=1,
        question_type="mcq",
        language="arabic",
        difficulty="medium",
        subject="mathematics",
        topic="Fractions"
    )

    # Generated: English question instead of Arabic
    english_question = create_test_question(
        question_text="What is 1/2 + 1/4?",
        answer="3/4",
        options={"A": "1/4", "B": "1/2", "C": "3/4", "D": "1"},
        answer_choice="C"
    )

    response = GenerateQuestionResponse(
        data=[english_question],
        request_id="test_language_001",
        total_questions=1,
        grade=5
    )

    evaluator = ResponseEvaluator(parallel_workers=1)
    evaluation = evaluator.evaluate_response(
        request=request,
        response=response,
        update_baseline=False
    )

    question_eval = evaluation.question_evaluations[0]
    query_relevance_score = question_eval.scores.get(EvaluationDimension.QUERY_RELEVANCE, 0.0)
    language_quality_score = question_eval.scores.get(EvaluationDimension.LANGUAGE_QUALITY, 0.0)

    print(f"\nRequest: Arabic language")
    print(f"Generated: English question")
    print(f"Query Relevance Score: {query_relevance_score:.2%}")
    print(f"Language Quality Score: {language_quality_score:.2%}")
    print(f"Recommendation: {question_eval.recommendation.upper()}")

    # Topic is correct (fractions) but language is wrong
    # Query relevance might be moderate, but language quality should be low
    if question_eval.recommendation in ["reject", "revise"]:
        print(f"\n✅ TEST 7 PASSED: Language mismatch flagged for {question_eval.recommendation}")
        return True
    else:
        print(f"\n⚠️  TEST 7 NOTE: Language mismatch got '{question_eval.recommendation}'")
        return False


if __name__ == "__main__":
    print("🚀 Starting Evaluator v2 Query Relevance Tests\n")
    print("Running comprehensive test suite to validate query relevance veto functionality\n")

    # Track all test results
    results = {}

    # Test 1 & 2: Original tests (algebra vs geometry, correct quadrilateral question)
    print("=" * 70)
    print("CORE TESTS: Basic Query Relevance Veto")
    print("=" * 70)
    results['core_tests'] = test_query_relevance_rejection()

    # Test 3: Cross-subject mismatch
    results['cross_subject'] = test_query_relevance_with_different_subjects()

    # Test 4: Wrong math topic (multiplication → division)
    results['wrong_topic'] = test_wrong_math_topic()

    # Test 5: Partial relevance (fractions → decimals)
    results['partial_relevance'] = test_partial_relevance()

    # Test 6: Perfect skill alignment
    results['perfect_alignment'] = test_correct_skill_alignment()

    # Test 7: Wrong grade level
    results['wrong_grade'] = test_wrong_grade_level_content()

    # Test 8: Language mismatch
    results['language_mismatch'] = test_language_mismatch()

    # Final summary
    print("\n\n" + "=" * 70)
    print("FINAL TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title():.<50} {status}")

    total_tests = len(results)
    passed_tests = sum(1 for p in results.values() if p)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    print("\n" + "=" * 70)
    print(f"OVERALL: {passed_tests}/{total_tests} tests passed ({success_rate:.1f}%)")
    print("=" * 70)

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED! Query relevance veto is working correctly.")
    elif passed_tests >= total_tests * 0.75:
        print(f"\n✅ MOSTLY PASSED ({success_rate:.1f}%) - Review failed tests for edge cases.")
    else:
        print(f"\n⚠️  MULTIPLE FAILURES ({success_rate:.1f}%) - Query relevance may need adjustment.")
