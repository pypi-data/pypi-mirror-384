"""
Unified Evaluator: Combines v3.py and edubench.py evaluators.
Single clean function that takes request + questions and runs both evaluations.
"""

import sys
import uuid
import time
import logging
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from pydantic import BaseModel, ConfigDict
from typing import Any, List, Optional, Literal, Dict
import os
import json
import re
import requests
import asyncio
import anthropic
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add submodules to path
_reading_qc_path = Path(__file__).parent / "submodules" / "reading-question-qc"
_edubench_path = Path(__file__).parent / "submodules" / "EduBench" / "code" / "evaluation"

if str(_reading_qc_path) not in sys.path:
    sys.path.insert(0, str(_reading_qc_path))
if str(_edubench_path) not in sys.path:
    sys.path.insert(0, str(_edubench_path))

# Import from incept_core (extracted minimal files from incept-multilingual-generation)
from incept_core.evaluator.v3 import call_single_shot_evaluator
from incept_core.evaluator.edubench import verify_answer_with_gpt4, get_normal_answer
from evaluation import TASK_PROMPT_TEMPLATES
from qc_pipeline import QuestionQCAnalyzer


class UniverslSkillInfoInput(BaseModel):
    title: str
    grade: str
    subject: str = "mathematics"
    difficulty: Optional[Literal["easy", "medium", "hard"]] = "medium"
    description: Optional[str] = None
    language: Literal['en', 'ar'] = 'en'

class UniversalGeneratedQuestionInput(BaseModel):
    id: str
    type: Literal["mcq", "fill-in"]  # MCQ and fill-in questions supported
    question: str
    answer: str
    answer_explanation: str
    answer_options: Optional[Dict[str, str]] = None  # Dict format for MCQ: {"A": "4 cm", "B": "0.4 cm", ...}
    skill: Optional[UniverslSkillInfoInput] = None
    image_url: Optional[str] = None
    additional_details: Optional[str] = None


class UniversalEvaluationRequest(BaseModel):
    generated_questions: List[UniversalGeneratedQuestionInput]
    submodules_to_run: List[Literal["compliance_math_evaluator", "answer_verification", "directionai_edubench", "reading_question_qc"]] = ["compliance_math_evaluator", "answer_verification", "reading_question_qc"]
    verbose: bool = False  # If False, returns only overall scores per module

class EdubenchScores(BaseModel):
    qa_score: float
    ec_score: float
    ip_score: float
    ag_score: float
    qg_score: float
    tmg_score: float
    average_score: float


class InternalEvaluatorScores(BaseModel):
    correctness: float
    grade_alignment: float
    difficulty_alignment: float
    language_quality: float
    pedagogical_value: float
    explanation_quality: float
    instruction_adherence: float
    format_compliance: float
    query_relevance: float
    di_compliance: float


class DIScores(BaseModel):
    overall: float
    general_principles: float
    format_alignment: float
    grade_language: float


class SectionEvaluation(BaseModel):
    section_score: float
    issues: List[str]
    strengths: List[str]
    recommendation: str


class SectionEvaluations(BaseModel):
    question: SectionEvaluation
    scaffolding: SectionEvaluation


class InternalEvaluatorResult(BaseModel):
    scores: InternalEvaluatorScores
    issues: List[str]
    strengths: List[str]
    overall: float
    recommendation: str
    suggested_improvements: List[str]
    di_scores: DIScores
    section_evaluations: SectionEvaluations


class AnswerVerificationResult(BaseModel):
    is_correct: bool
    correct_answer: str
    confidence: int
    reasoning: str


class ReadingQuestionQCResult(BaseModel):
    overall_score: float
    distractor_checks: Dict[str, Any]
    question_checks: Dict[str, Any]
    passed: bool


# Simplified models for non-verbose mode
class SimplifiedInternalEvaluatorResult(BaseModel):
    overall: float


class SimplifiedAnswerVerificationResult(BaseModel):
    is_correct: bool


class SimplifiedEdubenchScores(BaseModel):
    average_score: float


class SimplifiedReadingQuestionQCResult(BaseModel):
    overall_score: float


class UniversalQuestionEvaluationScores(BaseModel):
    model_config = ConfigDict(
        # Exclude None values when serializing to JSON
        exclude_none=True
    )

    compliance_math_evaluator: Optional[InternalEvaluatorResult | SimplifiedInternalEvaluatorResult] = None
    answer_verification: Optional[AnswerVerificationResult | SimplifiedAnswerVerificationResult] = None
    directionai_edubench: Optional[EdubenchScores | SimplifiedEdubenchScores] = None
    reading_question_qc: Optional[ReadingQuestionQCResult | SimplifiedReadingQuestionQCResult] = None
    final_score: Optional[float] = None  # Combined score from all evaluations (0-1 scale)


class UniversalEvaluationResponse(BaseModel):
    request_id: str
    evaluations: Dict[str, UniversalQuestionEvaluationScores]
    evaluation_time_seconds: float

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def score_edubench_response_with_llm(task_type: str, response: str, prompt: str, question_context: Dict[str, Any] = None) -> float:
    """
    Score EduBench response using GPT-4 following EduBench's official evaluation methodology.

    Based on EduBench paper: https://arxiv.org/pdf/2505.16160
    Uses their 3 evaluation principles:
    1. Scenario Adaptability
    2. Factual & Reasoning Accuracy
    3. Pedagogical Application

    Args:
        task_type: The EduBench task type (QA, EC, IP, AG, QG, TMG)
        response: The model's response to evaluate
        prompt: The original prompt sent to the model

    Returns:
        Score from 0-10
    """
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        logger.warning("No OpenAI API key found, skipping LLM scoring")
        return 0.0

    # Build context information
    context_info = ""
    if question_context:
        if "question" in question_context:
            context_info += f"\nQuestion: {question_context['question']}"
        if "answer" in question_context:
            context_info += f"\nCorrect Answer: {question_context['answer']}"
        if "explanation" in question_context:
            context_info += f"\nExpected Explanation: {question_context['explanation'][:300]}"
        if "difficulty" in question_context:
            context_info += f"\nDifficulty Level: {question_context['difficulty']}"
        if "grade" in question_context:
            context_info += f"\nGrade Level: {question_context['grade']}"

    # EduBench official evaluation dimensions
    evaluation_prompt = f"""You are an expert evaluator following the EduBench evaluation methodology.

IMPORTANT: You are evaluating responses from EDU-Qwen2.5-7B, a 7B parameter model that tends to be:
- Verbose and repetitive (may repeat answers multiple times)
- Sometimes provides multiple JSON blocks instead of one
- May include extra explanations beyond what was asked
- May echo parts of the prompt in the response

DO NOT penalize these stylistic issues. Focus ONLY on the core educational content quality.

Evaluate the BEST interpretation of the response across these dimensions:

**1. Scenario Adaptability:**
- Instruction Following & Task Completion (did it accomplish the core task?)
- Role & Tone Consistency (appropriate educational tone?)
- Content Relevance & Scope Control (relevant to the question?)
- Scenario Element Integration (addresses the educational context?)

**2. Factual & Reasoning Accuracy:**
- Basic Factual Accuracy (is the core answer correct?)
- Domain Knowledge Accuracy (demonstrates subject understanding?)
- Reasoning Process Rigor (logical steps present?)
- Error Identification & Correction Precision (for EC tasks: correctly identifies issues?)

**3. Pedagogical Application:**
- Clarity, Simplicity & Inspiration (understandable despite verbosity?)
- Motivation, Guidance & Positive Feedback (supportive tone?)
- Personalization, Adaptation & Learning Support (helpful for learning?)
- Higher-Order Thinking & Skill Development (promotes understanding?)

**Context:**{context_info}

**Task Type:** {task_type}

**Prompt Sent to Model:**
{prompt}

**Model Response (may be verbose/repetitive):**
{response}

**Scoring Guidelines:**
Extract the BEST answer from the response (ignore repetitions). Score based on:
- 0-3: Factually wrong or completely missing the task
- 4-6: Partially correct but missing key elements or has significant errors
- 7-8: Correct and educationally sound despite verbosity
- 9-10: Excellent content with comprehensive, accurate pedagogical value

DO NOT deduct points for:
- Verbosity or repetition
- Multiple JSON blocks
- Extra explanations
- Formatting issues

DO deduct points for:
- Factual errors
- Missing required task elements
- Poor pedagogical approach
- Incorrect reasoning

Return ONLY a JSON object:
{{"score": <number 0-10>, "reasoning": "<brief explanation focusing on content quality>"}}"""

    try:
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }

        response_obj = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": evaluation_prompt}]
            }
        )

        if response_obj.status_code == 200:
            content = response_obj.json()['choices'][0]['message']['content']
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                score = result.get('score', 0)
                logger.debug(f"{task_type} LLM score: {score}/10 - {result.get('reasoning', '')[:100]}")
                return float(score)

        logger.warning(f"Failed to get LLM score for {task_type}: {response_obj.status_code}")
        return 0.0

    except Exception as e:
        logger.error(f"Error scoring {task_type} with LLM: {e}")
        return 0.0

def _run_reading_qc_task_sync(question_idx: int, question: UniversalGeneratedQuestionInput, claude_api_key: str, openai_api_key: str = None) -> Dict[str, Any]:
    """Synchronous wrapper for running reading question QC analysis."""

    async def _async_task():
        logger.debug(f"Running reading QC for question {question_idx}")

        # Initialize clients
        claude_client = anthropic.AsyncAnthropic(api_key=claude_api_key)
        openai_client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None

        # Create analyzer
        analyzer = QuestionQCAnalyzer(
            claude_client=claude_client,
            openai_client=openai_client,
            claude_model="claude-sonnet-4-5-20250929",
            openai_model="gpt-4o"
        )

        # Convert question to the format expected by QuestionQCAnalyzer
        question_item = {
            'question_id': question.id,
            'question_type': 'MCQ' if question.type == 'mcq' else 'MP',
            'passage_text': question.additional_details or '',
            'grade': int(question.skill.grade) if question.skill and question.skill.grade.isdigit() else 5,
            'structured_content': {
                'question': question.question,
                'choices': question.answer_options or {},
                'correct_answer': question.answer,
                'CCSS': question.skill.title if question.skill else '',
                'CCSS_description': question.skill.description if question.skill else '',
                'DOK': question.skill.difficulty if question.skill else 'medium'
            }
        }

        try:
            result = await analyzer.analyze_question(question_item, semaphore=None)
            return {
                'question_idx': question_idx,
                'result': result
            }
        except Exception as e:
            logger.error(f"Error running reading QC for question {question_idx}: {e}")
            return {
                'question_idx': question_idx,
                'result': None,
                'error': str(e)
            }

    # Run the async function in a new event loop
    return asyncio.run(_async_task())

def _run_edubench_task(question_idx: int, task_type: str, question: UniversalGeneratedQuestionInput) -> Dict[str, Any]:
    """Run single EduBench task - just returns raw response like batch_edubench."""
    logger.debug(f"Running {task_type} task for question {question_idx}")

    # Extract explanation - always present as required field
    detailed_explanation = question.answer_explanation

    # Build prompt based on task type
    if task_type == "QA":
        prompt = TASK_PROMPT_TEMPLATES["QA"](question.question)
    elif task_type == "EC":
        prompt = TASK_PROMPT_TEMPLATES["EC"](question.question, question.answer)
    elif task_type == "IP":
        base_prompt = TASK_PROMPT_TEMPLATES["IP"](question.question)
        prompt = f"{base_prompt}\n\nReference scaffolding (detailed step-by-step guidance):\n{detailed_explanation}"
    elif task_type == "AG":
        base_prompt = TASK_PROMPT_TEMPLATES["AG"](question.question, question.answer)
        prompt = f"{base_prompt}\n\nReference explanation:\n{detailed_explanation}"
    elif task_type == "QG":
        # Extract knowledge point from skill (optional field)
        if question.skill:
            knowledge_point = question.skill.title
            subject = question.skill.subject
            level = question.skill.difficulty
        else:
            # Fallback if no skill provided
            knowledge_point = question.question.split('.')[0] if '.' in question.question else question.question[:50]
            subject = "mathematics"
            level = "medium"

        question_type = question.type  # "mcq" or "fill-in"
        prompt = TASK_PROMPT_TEMPLATES["QG"](knowledge_point, subject, question_type, level)
    elif task_type == "TMG":
        # Extract knowledge point from skill (optional field)
        if question.skill:
            knowledge_point = question.skill.title
        else:
            # Fallback if no skill provided
            knowledge_point = "General educational content"

        base_prompt = TASK_PROMPT_TEMPLATES["TMG"](knowledge_point)
        prompt = f"{base_prompt}\n\nReference scaffolding example:\n{detailed_explanation}"
    else:
        prompt = ""

    response = get_normal_answer(prompt, 'EDU-Qwen2.5-7B')

    # an llm call to score the response
    evaluation = score_edubench_response_with_llm(task_type, response, prompt, question_context={
        "question": question.question,
        "answer": question.answer,
        "explanation": detailed_explanation,
        "difficulty": question.skill.difficulty if question.skill else "medium",
        "grade": question.skill.grade if question.skill else "unknown"
    })

    result = {
        "question_idx": question_idx,
        "task_type": task_type,
        "response": response,
        "evaluation": evaluation,
    }

    return result

def universal_unified_benchmark(request: UniversalEvaluationRequest) -> UniversalEvaluationResponse:
    """
    Main entry point for universal evaluation.
    Processes each question and organizes results by question ID.
    """

    start_time = time.time()
    request_id = str(uuid.uuid4())

    logger.info(f"Universal evaluation request {request_id} with {len(request.generated_questions)} questions")

    modules_to_use = request.submodules_to_run
    evaluations = {}

    for question in request.generated_questions:
        evaluations[question.id] = UniversalQuestionEvaluationScores()

    # Run all enabled modules in parallel
    questions = request.generated_questions
    effective_edubench_tasks = ["QA", "EC", "IP", "AG", "QG", "TMG"]

    # Prepare storage for results
    edubench_task_results = []
    internal_eval_results = []
    verification_results = []
    reading_qc_results = []

    # Get API keys for reading QC
    claude_api_key = os.getenv('ANTHROPIC_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    with ThreadPoolExecutor(max_workers=50) as executor:
        all_futures = []

        # Submit EduBench tasks if enabled
        if "directionai_edubench" in modules_to_use:
            logger.info(f"Submitting EduBench evaluation with {len(effective_edubench_tasks)} tasks for {len(questions)} questions")
            for i, q in enumerate(questions):
                for task_type in effective_edubench_tasks:
                    future = executor.submit(_run_edubench_task, i, task_type, q)
                    all_futures.append(('directionai_edubench', future))

        # Submit internal evaluator tasks if enabled
        if "compliance_math_evaluator" in modules_to_use:
            logger.info(f"Submitting {len(questions)} internal evaluator tasks")
            for i, q in enumerate(questions):
                future = executor.submit(call_single_shot_evaluator, q, len(questions))
                all_futures.append(('compliance_math_evaluator', i, future))

        # Submit answer verification tasks if enabled
        if "answer_verification" in modules_to_use:
            logger.info(f"Submitting {len(questions)} answer verification tasks")
            for i, q in enumerate(questions):
                future = executor.submit(verify_answer_with_gpt4, q.question, q.answer, q.answer_explanation)
                all_futures.append(('answer_verification', i, future))

        # Submit reading QC tasks if enabled and dependencies available
        if "reading_question_qc" in modules_to_use:
            logger.info(f"Submitting {len(questions)} reading QC tasks")
            for i, q in enumerate(questions):
                future = executor.submit(_run_reading_qc_task_sync, i, q, claude_api_key, openai_api_key)
                all_futures.append(('reading_question_qc', i, future))

        # Collect all results with a single progress bar
        if all_futures:
            logger.info(f"Running {len(all_futures)} total tasks in parallel")
            with tqdm(total=len(all_futures), desc="Running All Evaluation Tasks") as pbar:
                for future_info in all_futures:
                    module_type = future_info[0]

                    if module_type == 'directionai_edubench':
                        _, future = future_info
                        result = future.result()
                        edubench_task_results.append(result)
                    elif module_type == 'compliance_math_evaluator':
                        _, question_idx, future = future_info
                        result = future.result()
                        internal_eval_results.append((question_idx, result))
                    elif module_type == 'answer_verification':
                        _, question_idx, future = future_info
                        result = future.result()
                        verification_results.append((question_idx, result))
                    elif module_type == 'reading_question_qc':
                        _, question_idx, future = future_info
                        result = future.result()
                        reading_qc_results.append((question_idx, result))

                    pbar.update(1)

    # Process EduBench results
    if "directionai_edubench" in modules_to_use and edubench_task_results:
        logger.info(f"Processing {len(edubench_task_results)} EduBench task results")

        # Organize results by question
        question_scores = {}  # {question_idx: {task_type: score}}

        for result in edubench_task_results:
            question_idx = result['question_idx']
            task_type = result['task_type']
            evaluation_score = result['evaluation']

            if question_idx not in question_scores:
                question_scores[question_idx] = {}

            question_scores[question_idx][task_type] = evaluation_score

        # Build EdubenchScores for each question
        for i, question in enumerate(questions):
            scores = question_scores.get(i, {})
            average_score = sum(scores.values()) / len(scores) if scores else 0.0

            if request.verbose:
                # Full detailed result
                edubench_scores = EdubenchScores(
                    qa_score=scores.get('QA', 0.0),
                    ec_score=scores.get('EC', 0.0),
                    ip_score=scores.get('IP', 0.0),
                    ag_score=scores.get('AG', 0.0),
                    qg_score=scores.get('QG', 0.0),
                    tmg_score=scores.get('TMG', 0.0),
                    average_score=average_score
                )
            else:
                # Simplified result - just average score
                edubench_scores = SimplifiedEdubenchScores(
                    average_score=average_score
                )

            if question.id in evaluations:
                evaluations[question.id].directionai_edubench = edubench_scores

        logger.info(f"Built EduBench scores for {len(question_scores)} questions")

    # Process internal evaluator results
    if "compliance_math_evaluator" in modules_to_use and internal_eval_results:
        logger.info(f"Processing {len(internal_eval_results)} internal evaluation results")

        # Sort by question index to maintain order
        internal_eval_results.sort(key=lambda x: x[0])

        for question_idx, result_dict in internal_eval_results:
            question = questions[question_idx]
            if question.id in evaluations:
                # Convert dict to Pydantic model
                try:
                    if request.verbose:
                        # Full detailed result
                        # Convert EvaluationDimension keys to strings and extract scores
                        scores_dict = {
                            k.value if hasattr(k, 'value') else str(k): v
                            for k, v in result_dict['scores'].items()
                        }

                        internal_result = InternalEvaluatorResult(
                            scores=InternalEvaluatorScores(**scores_dict),
                            issues=result_dict.get('issues', []),
                            strengths=result_dict.get('strengths', []),
                            overall=result_dict.get('overall', 0.0),
                            recommendation=result_dict.get('recommendation', 'revise'),
                            suggested_improvements=result_dict.get('suggested_improvements', []),
                            di_scores=DIScores(**result_dict.get('di_scores', {})),
                            section_evaluations=SectionEvaluations(
                                question=SectionEvaluation(**result_dict['section_evaluations']['question']),
                                scaffolding=SectionEvaluation(**result_dict['section_evaluations']['scaffolding'])
                            )
                        )
                        evaluations[question.id].compliance_math_evaluator = internal_result
                    else:
                        # Simplified result - just overall score
                        internal_result = SimplifiedInternalEvaluatorResult(
                            overall=result_dict.get('overall', 0.0)
                        )
                        evaluations[question.id].compliance_math_evaluator = internal_result
                except Exception as e:
                    logger.error(f"Error converting internal evaluator result for question {question_idx}: {e}")
                    # Keep the raw dict if conversion fails
                    evaluations[question.id].compliance_math_evaluator = None

        logger.info(f"Assigned internal evaluator results to {len(internal_eval_results)} questions")

    # Process answer verification results
    if "answer_verification" in modules_to_use and verification_results:
        logger.info(f"Processing {len(verification_results)} answer verification results")

        # Sort by question index to maintain order
        verification_results.sort(key=lambda x: x[0])

        for question_idx, result_dict in verification_results:
            question = questions[question_idx]
            if question.id in evaluations:
                # Convert dict to Pydantic model
                try:
                    if request.verbose:
                        # Full detailed result
                        verification_result = AnswerVerificationResult(
                            is_correct=result_dict.get('is_correct', False),
                            correct_answer=result_dict.get('correct_answer', ''),
                            confidence=result_dict.get('confidence', 0),
                            reasoning=result_dict.get('reasoning', '')
                        )
                        evaluations[question.id].answer_verification = verification_result
                    else:
                        # Simplified result - just is_correct
                        verification_result = SimplifiedAnswerVerificationResult(
                            is_correct=result_dict.get('is_correct', False)
                        )
                        evaluations[question.id].answer_verification = verification_result
                except Exception as e:
                    logger.error(f"Error converting answer verification result for question {question_idx}: {e}")
                    # Keep None if conversion fails
                    evaluations[question.id].answer_verification = None

        logger.info(f"Assigned answer verification results to {len(verification_results)} questions")

    # Process reading QC results
    if "reading_question_qc" in modules_to_use and reading_qc_results:
        logger.info(f"Processing {len(reading_qc_results)} reading QC results")

        # Sort by question index to maintain order
        reading_qc_results.sort(key=lambda x: x[0])

        for question_idx, result_dict in reading_qc_results:
            question = questions[question_idx]
            if question.id in evaluations:
                # Extract and convert the result
                try:
                    qc_result = result_dict.get('result')
                    if qc_result and 'error' not in result_dict:
                        # Extract scores
                        overall_score = qc_result.get('overall_score', 0.0)

                        if request.verbose:
                            # Full detailed result
                            # Extract checks - the 'checks' field contains all check results
                            all_checks = qc_result.get('checks', {})

                            # Separate distractor and question checks based on category
                            distractor_checks = {k: v for k, v in all_checks.items() if v.get('category') == 'distractor'}
                            question_checks = {k: v for k, v in all_checks.items() if v.get('category') == 'question'}

                            # Determine if passed (threshold: 0.8)
                            passed = overall_score >= 0.8

                            reading_qc_obj = ReadingQuestionQCResult(
                                overall_score=overall_score,
                                distractor_checks=distractor_checks,
                                question_checks=question_checks,
                                passed=passed
                            )
                            evaluations[question.id].reading_question_qc = reading_qc_obj
                        else:
                            # Simplified result - just overall score
                            reading_qc_obj = SimplifiedReadingQuestionQCResult(
                                overall_score=overall_score
                            )
                            evaluations[question.id].reading_question_qc = reading_qc_obj
                    else:
                        logger.warning(f"Reading QC result for question {question_idx} is None or has error")
                        evaluations[question.id].reading_question_qc = None
                except Exception as e:
                    logger.error(f"Error converting reading QC result for question {question_idx}: {e}")
                    evaluations[question.id].reading_question_qc = None

        logger.info(f"Assigned reading QC results to {len(reading_qc_results)} questions")

    # Calculate final scores for each question
    logger.info("Calculating final combined scores for each question")
    for question_id, evaluation in evaluations.items():
        scores_to_combine = []

        # Debug: Log what we have for this question
        has_internal = evaluation.compliance_math_evaluator is not None
        has_verification = evaluation.answer_verification is not None
        has_edubench = evaluation.directionai_edubench is not None
        has_reading_qc = evaluation.reading_question_qc is not None

        logger.info(f"Question {question_id}: compliance_math_evaluator={has_internal}, answer_verification={has_verification}, directionai_edubench={has_edubench}, reading_question_qc={has_reading_qc}")

        # Internal evaluator: already on 0-1 scale
        if evaluation.compliance_math_evaluator:
            # Works for both InternalEvaluatorResult and SimplifiedInternalEvaluatorResult
            internal_score = evaluation.compliance_math_evaluator.overall
            scores_to_combine.append(internal_score)
            logger.info(f"  - Internal evaluator: {internal_score:.3f}")

        # Answer verification: convert boolean to 0-1 scale
        if evaluation.answer_verification:
            # Works for both AnswerVerificationResult and SimplifiedAnswerVerificationResult
            answer_score = 1.0 if evaluation.answer_verification.is_correct else 0.0
            scores_to_combine.append(answer_score)
            logger.info(f"  - Answer verification: {answer_score:.3f} (is_correct={evaluation.answer_verification.is_correct})")

        # EduBench: convert from 0-10 to 0-1 scale
        if evaluation.directionai_edubench:
            # Works for both EdubenchScores and SimplifiedEdubenchScores
            edubench_normalized = evaluation.directionai_edubench.average_score / 10.0
            scores_to_combine.append(edubench_normalized)
            logger.info(f"  - EduBench: {edubench_normalized:.3f} (avg={evaluation.directionai_edubench.average_score:.2f}/10)")

        # Reading QC: already on 0-1 scale
        if evaluation.reading_question_qc:
            # Works for both ReadingQuestionQCResult and SimplifiedReadingQuestionQCResult
            reading_qc_score = evaluation.reading_question_qc.overall_score
            scores_to_combine.append(reading_qc_score)
            logger.info(f"  - Reading QC: {reading_qc_score:.3f}")

        # Calculate weighted average of all available scores
        if scores_to_combine:
            evaluation.final_score = sum(scores_to_combine) / len(scores_to_combine)
            logger.info(f"Question {question_id}: final_score = {evaluation.final_score:.3f} (from {len(scores_to_combine)} modules)")
        else:
            evaluation.final_score = None
            logger.warning(f"Question {question_id}: No scores available to calculate final_score - all evaluations are None!")

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Universal evaluation request {request_id} completed in {elapsed_time:.2f} seconds")

    # Filter out evaluators that weren't requested
    filtered_evaluations = {}
    for question_id, evaluation in evaluations.items():
        # Build dict with only requested evaluators (and only non-None values)
        eval_dict = {}

        if "compliance_math_evaluator" in modules_to_use and evaluation.compliance_math_evaluator is not None:
            eval_dict["compliance_math_evaluator"] = evaluation.compliance_math_evaluator
        if "answer_verification" in modules_to_use and evaluation.answer_verification is not None:
            eval_dict["answer_verification"] = evaluation.answer_verification
        if "directionai_edubench" in modules_to_use and evaluation.directionai_edubench is not None:
            eval_dict["directionai_edubench"] = evaluation.directionai_edubench
        if "reading_question_qc" in modules_to_use and evaluation.reading_question_qc is not None:
            eval_dict["reading_question_qc"] = evaluation.reading_question_qc

        # Always include final_score if not None
        if evaluation.final_score is not None:
            eval_dict["final_score"] = evaluation.final_score

        # Create object from dict (Pydantic will only include provided keys)
        filtered_eval = UniversalQuestionEvaluationScores(**eval_dict)
        filtered_evaluations[question_id] = filtered_eval

    return UniversalEvaluationResponse(
        request_id=request_id,
        evaluations=filtered_evaluations,
        evaluation_time_seconds=elapsed_time
    )


if __name__ == "__main__":
    with open("qs.json", "r") as f:
        example_data = json.load(f)
    example_request = UniversalEvaluationRequest(**example_data)
    response = universal_unified_benchmark(example_request)
    print(response.model_dump_json(indent=2, exclude_none=True))