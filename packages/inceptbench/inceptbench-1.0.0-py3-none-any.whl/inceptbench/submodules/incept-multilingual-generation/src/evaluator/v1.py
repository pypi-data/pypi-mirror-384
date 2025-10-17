"""
Single-shot evaluator for v1/generate-questions API response-request pairs.

- Subject-agnostic (math-friendly but not math-specific).
- Exactly ONE LLM call per question via `solve_with_llm`.
- Aggregates scores and writes to baseline_evaluation.json.
- Focuses on: sense-making, correctness, answer-option consistency, explanation quality (guidance vs. just-the-answer),
  general grade appropriateness (if grade provided), and basic format sanity (type, options, answer key).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Project contracts ---
from src.dto.question_generation import (
    GenerateQuestionsRequest,
    GenerateQuestionResponse,
    GeneratedQuestion
)
# Removed problematic import dependency

from src.evaluator.llm_interface import simple_solve_with_llm

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def clip01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def safe_getattr(obj: Any, name: str, default: Any = None) -> Any:
    try:
        return getattr(obj, name, default)
    except Exception:
        return default


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    return str(value)


def get_git_commit_hash() -> str:
    """Get the current git commit hash for baseline snapshots."""
    try:
        # Try environment variable first (set by GitHub Actions)
        github_sha = os.getenv("GITHUB_SHA")
        if github_sha:
            return github_sha[:8]  # Short hash like git

        # Fallback to git command
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False  # Don't raise exception
        )
        if result.returncode == 0:
            return result.stdout.strip()[:8]
        else:
            logger.info(f"Git command failed with code {result.returncode}, using fallback")
            return "ci-build"
    except Exception as e:
        logger.info(f"Could not retrieve git commit hash: {e}, using fallback")
        return "ci-build"


def update_baseline_evaluation(evaluation: 'ResponseEvaluation', baseline_file: str = "baseline_evaluation.json") -> None:
    """Append an evaluation snapshot to baseline_evaluation.json (rolls the last 100)."""
    commit_hash = get_git_commit_hash()
    timestamp = datetime.now().isoformat()

    entry = {
        "timestamp": timestamp,
        "commit_hash": commit_hash,
        "request_id": evaluation.request_id,
        "overall_score": evaluation.overall_score,
        "aggregate_scores": evaluation.aggregate_scores,
        "total_issues": evaluation.total_issues,
        "total_strengths": evaluation.total_strengths,
        "compliance_report": evaluation.compliance_report,
        "recommendations": evaluation.recommendations,
        "question_count": len(evaluation.question_evaluations),
        "quality_distribution": {
            "accept": sum(1 for q in evaluation.question_evaluations if q.recommendation == "accept"),
            "revise": sum(1 for q in evaluation.question_evaluations if q.recommendation == "revise"),
            "reject": sum(1 for q in evaluation.question_evaluations if q.recommendation == "reject")
        }
    }

    data = {"evaluations": []}
    if os.path.exists(baseline_file):
        try:
            with open(baseline_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            logger.warning(f"Could not read existing {baseline_file}, creating new file")
            data = {"evaluations": []}

    data["evaluations"].append(entry)
    if len(data["evaluations"]) > 100:
        data["evaluations"] = data["evaluations"][-100:]

    try:
        with open(baseline_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Updated baseline evaluation file: {baseline_file}")
    except Exception as e:
        logger.error(f"Failed to update baseline evaluation file: {e}")


# ----------------- Evaluation dimensions & results -----------------
class EvaluationDimension(Enum):
    CORRECTNESS = "correctness"
    GRADE_ALIGNMENT = "grade_alignment"
    DIFFICULTY_ALIGNMENT = "difficulty_alignment"
    LANGUAGE_QUALITY = "language_quality"
    PEDAGOGICAL_VALUE = "pedagogical_value"
    EXPLANATION_QUALITY = "explanation_quality"
    INSTRUCTION_ADHERENCE = "instruction_adherence"
    FORMAT_COMPLIANCE = "format_compliance"


@dataclass
class QuestionEvaluation:
    question_id: int
    scores: Dict[EvaluationDimension, float]
    issues: List[str]
    strengths: List[str]
    overall_score: float
    recommendation: str  # "accept", "revise", "reject"
    suggested_improvements: List[str]


@dataclass
class ResponseEvaluation:
    request_id: str
    question_evaluations: List[QuestionEvaluation]
    aggregate_scores: Dict[str, float]
    overall_score: float
    total_issues: int
    total_strengths: int
    compliance_report: Dict[str, Any]
    recommendations: List[str]


# ----------------- Single-shot prompt & call -----------------
EVALUATION_JSON_SPEC = r"""
Return STRICT JSON with this schema (no extra keys, no text outside JSON):

{
  "scores": {
    "correctness": 0-10,
    "grade_alignment": 0-10,
    "difficulty_alignment": 0-10,
    "language_quality": 0-10,
    "pedagogical_value": 0-10,
    "explanation_quality": 0-10,
    "instruction_adherence": 0-10,
    "format_compliance": 0-10
  },
  "issues": [string],
  "strengths": [string],
  "suggested_improvements": [string],
  "recommendation": "accept" | "revise" | "reject",
  "detailed_scores": [
    {
      "metric": "string",
      "score": 0-10,
      "reason": "string"
    }
  ]
}

REPORTING NOTES:
- For answer mapping: Use "Answer mapping is correct (B → 4)" instead of "should be 4 not B"
- For missing correct values: State "correct answer not present among options" clearly
- For impossible patterns: Note "impossible pattern detected" with specifics
- Prioritize structural issues over stylistic concerns
"""

# Score band definitions from EduBench
SCORE_BANDS = {
    "excellent": "9-10: Exceptional quality, meets all criteria perfectly",
    "good": "7-8: Good quality with minor issues that don't affect core functionality",
    "acceptable": "5-6: Acceptable but with notable issues requiring attention",
    "poor": "3-4: Significant problems, major revisions needed",
    "unacceptable": "1-2: Fundamentally flawed, complete rework required"
}

# Detailed metric descriptions adapted from EduBench
METRIC_DESCRIPTIONS = {
    "correctness": {
        "name": "Correctness & Factual Accuracy",
        "description": "Evaluates mathematical accuracy, factual correctness, and answer key validity",
        "scoring": {
            "9-10": "Perfect accuracy in all facts, calculations, and answer keys",
            "7-8": "Mostly correct with minor computational or factual errors",
            "5-6": "Generally correct but contains some notable errors",
            "3-4": "Multiple significant errors affecting reliability",
            "1-2": "Fundamentally incorrect or misleading"
        }
    },
    "grade_alignment": {
        "name": "Grade Level Appropriateness",
        "description": "Assesses if complexity and content match the target grade level",
        "scoring": {
            "9-10": "Perfectly calibrated to specified grade level",
            "7-8": "Well-aligned with minor deviations in complexity",
            "5-6": "Roughly appropriate but some misalignment",
            "3-4": "Significant mismatch with grade expectations",
            "1-2": "Completely inappropriate for target grade"
        }
    },
    "difficulty_alignment": {
        "name": "Difficulty Consistency",
        "description": "Checks if actual difficulty matches the declared level",
        "scoring": {
            "9-10": "Actual difficulty perfectly matches declaration",
            "7-8": "Good alignment with slight variance",
            "5-6": "Moderate mismatch between declared and actual",
            "3-4": "Significant discrepancy in difficulty",
            "1-2": "Complete mismatch or undefined difficulty"
        }
    },
    "language_quality": {
        "name": "Language & Clarity",
        "description": "Evaluates grammar, clarity, and appropriateness of language",
        "scoring": {
            "9-10": "Crystal clear, grammatically perfect, age-appropriate",
            "7-8": "Clear with minor language issues",
            "5-6": "Generally understandable but needs polish",
            "3-4": "Confusing or grammatically problematic",
            "1-2": "Incomprehensible or severely flawed language"
        }
    },
    "pedagogical_value": {
        "name": "Educational Impact",
        "description": "Assesses learning potential and educational value",
        "scoring": {
            "9-10": "Exceptional learning opportunity with clear objectives",
            "7-8": "Good educational value with solid learning outcomes",
            "5-6": "Moderate educational benefit",
            "3-4": "Limited learning value",
            "1-2": "No educational merit or potentially harmful"
        }
    },
    "explanation_quality": {
        "name": "Explanation & Guidance Quality",
        "description": "Evaluates if explanations guide learning vs just stating answers",
        "scoring": {
            "9-10": "Excellent step-by-step guidance promoting understanding",
            "7-8": "Good explanations with clear reasoning",
            "5-6": "Basic explanations present but could be clearer",
            "3-4": "Poor explanations or just answer statements",
            "1-2": "No useful explanation or misleading guidance"
        }
    },
    "instruction_adherence": {
        "name": "Request Compliance",
        "description": "Measures adherence to specified requirements and format",
        "scoring": {
            "9-10": "Perfectly follows all instructions and requirements",
            "7-8": "Good compliance with minor deviations",
            "5-6": "Partially compliant with some requirements missed",
            "3-4": "Major deviations from instructions",
            "1-2": "Completely ignores requirements"
        }
    },
    "format_compliance": {
        "name": "Format & Structure",
        "description": "Checks structural correctness (MCQ options, answer format, etc.)",
        "scoring": {
            "9-10": "Perfect format (e.g., 4 options A-D for MCQ)",
            "7-8": "Good structure with minor formatting issues",
            "5-6": "Acceptable format but needs improvement",
            "3-4": "Poor formatting affecting usability",
            "1-2": "Completely wrong or unusable format"
        }
    }
}


def build_single_shot_messages(
    q: GeneratedQuestion,
    request: GenerateQuestionsRequest,
    total_questions: int
) -> List[Dict[str, str]]:
    """
    Build messages for a single LLM call that evaluates one question.
    Subject-agnostic with strong math tolerance.
    """
    # Prepare detailed_explanation and options representations
    det_exp = ""
    if safe_getattr(q, "detailed_explanation"):
        try:
            det_exp = json.dumps(
                getattr(q.detailed_explanation, "steps", q.detailed_explanation),
                ensure_ascii=False
            )
        except Exception:
            det_exp = as_text(q.detailed_explanation)

    options = q.options or []
    if not isinstance(options, list):
        try:
            options = list(options)
        except Exception:
            options = [as_text(options)]

    # Instructions summary derived from request
    req_meta = {
        "requested_grade": safe_getattr(request, "grade", None),
        "requested_language": safe_getattr(request, "language", "English"),
        "requested_question_type": safe_getattr(request, "question_type", "mixed"),
        "requested_difficulty": safe_getattr(request, "difficulty", "mixed"),
        "requested_count": safe_getattr(request, "count", None),
        "topic": safe_getattr(request, "topic", None),
        "subject": safe_getattr(request, "subject", None),
        "raw_instructions": safe_getattr(request, "instructions", ""),
    }

    # Enhanced system prompt with EduBench-inspired metric descriptions
    metric_guidelines = "\n".join([
        f"- {desc['name']}: {desc['description']}"
        for desc in METRIC_DESCRIPTIONS.values()
    ])

    scoring_guidelines = "\n".join([
        f"{band}: {definition}"
        for band, definition in SCORE_BANDS.items()
    ])

    system = (
        "You are a strict, reliable evaluator of educational question items. "
        "Your evaluation must be thorough, evidence-based, and pedagogically sound.\n\n"
        "PRE-CHECK RULES (MANDATORY - check before judging pedagogy or style):\n"
        "1. Letter→Option Mapping: Verify the answer letter (A-D) maps to an existing option. If not, mark REJECT and add issue 'answer letter doesn't map to any option.'\n"
        "2. Correct Value Present: For MCQs with objectively computable answers, confirm the correct value actually appears in the options. If absent, mark REJECT with issue 'correct answer not present among options,' regardless of other qualities.\n"
        "3. Letter vs. Value Consistency: If the keyed letter maps to the correct option text, treat the key as CORRECT; do NOT complain that the answer should be a value instead of a letter.\n\n"
        "MATH SANITY CHECKS (when applicable; keep lightweight):\n"
        "- Basic Limits/Algebra: (x²−4)/(x−2) at x→2 → 4 present? (x³−1)/(x−1) at x→1 → 3 present?\n"
        "- Simple Integral Check: For clear polynomials with simple bounds, estimate the numeric result and see if an equivalent option exists (e.g., 33/2 ≡ 16.5).\n"
        "- Vertex Time: For h(t)=at²+bt+c with a<0, check t* = −b/(2a) appears when asked for 'time of max.'\n"
        "- Trig 'special angles' guard: If solving 2sin(x)=1 on [0,2π], accept only options containing π/6 and 5π/6. If cos(x)=−1/3, there are NO special-angle solutions; any clean special-angle pair is incorrect.\n"
        "- Simple Probability (no replacement): Two aces from a 52-card deck → 1/221 should appear.\n\n"
        "EVALUATION DIMENSIONS:\n"
        f"{metric_guidelines}\n\n"
        "SCORING SCALE:\n"
        f"{scoring_guidelines}\n\n"
        "EVALUATION PRINCIPLES:\n"
        "1. Be objective and consistent across all evaluations\n"
        "2. Provide specific evidence for each score\n"
        "3. Check mathematical computations meticulously\n"
        "4. Consider the target audience (grade level, prior knowledge)\n"
        "5. Prioritize educational value over technical perfection\n"
        "6. For MCQs: verify answer letter maps correctly to the option\n"
        "7. For explanations: assess if they guide learning, not just state answers\n"
        "8. Penalize if explanation reveals the exact correct option text ('leakage'). Note it as an issue but don't override correctness.\n\n"
        "RECOMMENDATION LOGIC (override rules):\n"
        "- REJECT if: answer letter doesn't map to an option, OR the correct answer is not present among options, OR the keyed option encodes an obviously impossible pattern (e.g., special-angle pair for cos x = −1/3).\n"
        "- REVISE if: structure is OK and answer is correct, but there are issues (topic drift, weak explanation, minor format flaws).\n"
        "- ACCEPT only if: answer mapping is correct, correct value is present, and no major issues.\n\n"
        "REPORTING LANGUAGE:\n"
        "- When the letter maps correctly, avoid 'should be 4 not B.' Prefer: 'Answer mapping is correct (B → 4).'\n"
        "- Explicitly note when no correct option exists, and prioritize that issue over difficulty/style comments.\n\n"
        "OUTPUT REQUIREMENTS:\n"
        "- Return ONLY valid JSON as specified\n"
        "- Include detailed reasoning for each metric score\n"
        "- Provide actionable improvement suggestions\n"
        "- Base recommendation on overall educational quality, subject to override rules"
    )

    # Add detailed scoring rubrics for each metric
    scoring_rubrics = {}
    for metric_key, metric_info in METRIC_DESCRIPTIONS.items():
        scoring_rubrics[metric_key] = metric_info["scoring"]

    # Serialize skill object if present
    skill_obj = safe_getattr(q, "skill", None)
    skill_data = None
    if skill_obj:
        try:
            # Convert Pydantic model to dict
            if hasattr(skill_obj, "model_dump"):
                skill_data = skill_obj.model_dump()
            elif hasattr(skill_obj, "dict"):
                skill_data = skill_obj.dict()
            else:
                skill_data = dict(skill_obj) if isinstance(skill_obj, dict) else None
        except Exception:
            skill_data = None

    user = {
        "question": {
            "type": q.type,
            "difficulty": q.difficulty,
            "question_text": q.question,
            "answer": q.answer,
            "options": options,
            "explanation": safe_getattr(q, "explanation", ""),
            "detailed_explanation": det_exp,
            "voiceover_script": None,
            "skill": skill_data,
            "image_url": None,
        },
        "request_context": req_meta,
        "format_requirements": {
            "mcq": "Expect 4 options (A-D) and the answer as a letter mapping to one of them. VALIDATE: 1) Answer letter exists in options, 2) For computable problems, correct value is present among options.",
            "fill-in": "No options; answer is numeric or short text.",
        },
        "validation_checklist": {
            "answer_mapping": "For MCQs, verify answer letter (A-D) corresponds to an actual option",
            "correct_value_present": "For math problems, ensure the mathematically correct answer appears among the options",
            "no_impossible_patterns": "Flag special-angle solutions for non-special-angle problems (e.g., cos(x)=-1/3)",
            "explanation_leakage": "Check if explanation reveals exact option text instead of guiding reasoning"
        },
        "scoring_rubrics": scoring_rubrics,
        "evaluation_instructions": (
            "MANDATORY PRE-CHECKS FIRST:\n"
            "1. Verify answer letter maps to existing option (A-D must correspond to actual choices)\n"
            "2. For math problems, confirm correct answer value appears among options\n"
            "3. Check for impossible patterns (e.g., special angles for non-special problems)\n"
            "4. Flag explanation leakage (revealing exact option text)\n\n"
            "If any pre-check fails, mark as REJECT regardless of other qualities.\n"
            "Only then score each metric (0-10) based on rubrics with specific evidence."
        ),
        "output_schema": EVALUATION_JSON_SPEC.strip()
    }

    # Single-turn messages
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user, ensure_ascii=False)}
    ]
    return messages


def call_single_shot_evaluator(
    q: GeneratedQuestion,
    request: GenerateQuestionsRequest,
    total_questions: int,
    provider: str = "openai"  # Can switch to "deepseek" for better human alignment
) -> Dict[str, Any]:
    """
    Perform one LLM call to evaluate a single question item and return normalized scores 0..1.
    Uses configurable provider - EduBench shows DeepSeek V3 has best human alignment.
    """
    messages = build_single_shot_messages(q, request, total_questions)

    # Use simplified LLM interface to avoid dependency issues
    data = simple_solve_with_llm(
        messages=messages
    )


    # Normalize scores to 0..1
    sr = data.get("scores", {})
    scores = {
        EvaluationDimension.CORRECTNESS: clip01(sr.get("correctness", 5) / 10.0),
        EvaluationDimension.GRADE_ALIGNMENT: clip01(sr.get("grade_alignment", 5) / 10.0),
        EvaluationDimension.DIFFICULTY_ALIGNMENT: clip01(sr.get("difficulty_alignment", 5) / 10.0),
        EvaluationDimension.LANGUAGE_QUALITY: clip01(sr.get("language_quality", 5) / 10.0),
        EvaluationDimension.PEDAGOGICAL_VALUE: clip01(sr.get("pedagogical_value", 5) / 10.0),
        EvaluationDimension.EXPLANATION_QUALITY: clip01(sr.get("explanation_quality", 5) / 10.0),
        EvaluationDimension.INSTRUCTION_ADHERENCE: clip01(sr.get("instruction_adherence", 5) / 10.0),
        EvaluationDimension.FORMAT_COMPLIANCE: clip01(sr.get("format_compliance", 5) / 10.0),
    }

    issues = list(data.get("issues", []))[:10]
    strengths = list(data.get("strengths", []))[:10]
    suggestions = list(data.get("suggested_improvements", []))[:10]
    recommendation = data.get("recommendation", "revise")
    if recommendation not in {"accept", "revise", "reject"}:
        recommendation = "revise"

    # Overall as simple mean of dims
    overall = sum(scores.values()) / max(1, len(scores))
    return {
        "scores": scores,
        "issues": issues,
        "strengths": strengths,
        "overall": overall,
        "recommendation": recommendation,
        "suggested_improvements": suggestions,
    }


# ----------------- Main Evaluator Class -----------------
class ResponseEvaluator:
    """
    Main evaluator for v1/generate-questions API responses.
    Evaluates request-response pairs across multiple dimensions with ONE LLM call per question.
    """

    def __init__(self, parallel_workers: int = None):
        # EduBench found 3-6 workers optimal, we'll auto-adjust based on workload
        self.default_workers = 6
        self.parallel_workers = parallel_workers if parallel_workers else self.default_workers
        logger.info(f"ResponseEvaluator initialized with {self.parallel_workers} workers")

    def evaluate_response(
        self,
        request: GenerateQuestionsRequest,
        response: GenerateQuestionResponse,
        update_baseline: bool = True,
        baseline_file: str = "baseline_evaluation.json"
    ) -> ResponseEvaluation:
        """
        Evaluate a complete API response against the request.
        """
        logger.info(f"Starting evaluation for request {response.request_id}")

        # Evaluate each question in parallel
        question_evaluations = self._evaluate_questions_parallel(request, response.data)

        # Calculate aggregate scores
        aggregate_scores = self._calculate_aggregate_scores(question_evaluations)

        # Generate compliance report
        compliance_report = self._generate_compliance_report(request, response, question_evaluations)

        # Overall statistics
        total_issues = sum(len(qe.issues) for qe in question_evaluations)
        total_strengths = sum(len(qe.strengths) for qe in question_evaluations)
        overall_score = aggregate_scores.get("overall", 0.0)

        # Recommendations
        recommendations = self._generate_recommendations(request, response, question_evaluations, aggregate_scores)

        evaluation = ResponseEvaluation(
            request_id=response.request_id,
            question_evaluations=question_evaluations,
            aggregate_scores=aggregate_scores,
            overall_score=overall_score,
            total_issues=total_issues,
            total_strengths=total_strengths,
            compliance_report=compliance_report,
            recommendations=recommendations
        )

        if update_baseline:
            update_baseline_evaluation(evaluation, baseline_file)

        return evaluation

    def _evaluate_questions_parallel(
        self,
        request: GenerateQuestionsRequest,
        questions: List[GeneratedQuestion]
    ) -> List[QuestionEvaluation]:

        evaluations: List[QuestionEvaluation] = []

        with ThreadPoolExecutor(max_workers=self.parallel_workers) as executor:
            futures = []
            for idx, question in enumerate(questions):
                futures.append(
                    executor.submit(self._evaluate_single_question, idx, question, request, len(questions))
                )

            for future in as_completed(futures):
                evaluations.append(future.result())

        evaluations.sort(key=lambda x: x.question_id)
        return evaluations

    def _evaluate_single_question(
        self,
        idx: int,
        question: GeneratedQuestion,
        request: GenerateQuestionsRequest,
        total_questions: int
    ) -> QuestionEvaluation:
        try:
            res = call_single_shot_evaluator(question, request, total_questions)
        except Exception as e:
            logger.error(f"Evaluator LLM call failed for question {idx}: {e}")
            # Fallback: neutral scores, request revision
            neutral = {dim: 0.5 for dim in EvaluationDimension}
            return QuestionEvaluation(
                question_id=idx,
                scores=neutral,
                issues=[f"Evaluation error: {e}"],
                strengths=[],
                overall_score=0.5,
                recommendation="revise",
                suggested_improvements=["Retry evaluation; ensure JSON-only output; check question fields."]
            )

        scores: Dict[EvaluationDimension, float] = res["scores"]
        overall = float(res["overall"])
        recommendation = res["recommendation"]

        # Enhanced guardrails on recommendation following override rules
        correctness_score = scores.get(EvaluationDimension.CORRECTNESS, 0.0)
        format_score = scores.get(EvaluationDimension.FORMAT_COMPLIANCE, 0.0)

        # Override rules: REJECT if critical failures detected
        critical_issues = [
            "answer letter doesn't map to any option",
            "correct answer not present among options",
            "answer letter doesn't map",
            "no correct option exists",
            "impossible pattern",
            "special-angle pair for cos"
        ]

        has_critical_issue = any(
            any(critical in issue.lower() for critical in critical_issues)
            for issue in res["issues"]
        )

        if has_critical_issue or correctness_score < 0.4 or format_score < 0.4:
            recommendation = "reject"
        elif correctness_score >= 0.6 and format_score >= 0.6 and overall >= 0.7:
            # Only accept if answer mapping is correct and no major issues
            recommendation = "accept"
        else:
            recommendation = "revise"

        return QuestionEvaluation(
            question_id=idx,
            scores=scores,
            issues=res["issues"],
            strengths=res["strengths"],
            overall_score=overall,
            recommendation=recommendation,
            suggested_improvements=res["suggested_improvements"]
        )

    def _calculate_aggregate_scores(
        self,
        question_evaluations: List[QuestionEvaluation]
    ) -> Dict[str, float]:
        if not question_evaluations:
            raise ValueError("No question evaluations to aggregate")

        aggregate: Dict[str, float] = {}
        for dim in EvaluationDimension:
            vals = [qe.scores.get(dim, 0.0) for qe in question_evaluations]
            aggregate[dim.value] = sum(vals) / max(1, len(vals))

        # Overall as mean of dimensions’ aggregates
        aggregate["overall"] = sum(aggregate.values()) / max(1, len(aggregate))
        return aggregate

    def _generate_compliance_report(
        self,
        request: GenerateQuestionsRequest,
        response: GenerateQuestionResponse,
        evaluations: List[QuestionEvaluation]
    ) -> Dict[str, Any]:
        return {
            "count_compliance": {
                "requested": safe_getattr(request, "count", None),
                "generated": safe_getattr(response, "total_questions", None),
                "compliant": safe_getattr(response, "total_questions", None) == safe_getattr(request, "count", None)
            },
            "grade_compliance": {
                "requested": safe_getattr(request, "grade", None),
                "response_grade": safe_getattr(response, "grade", None),
                "compliant": safe_getattr(response, "grade", None) == safe_getattr(request, "grade", None)
            },
            "type_distribution": self._get_type_distribution(response.data),
            "difficulty_distribution": self._get_difficulty_distribution(response.data),
            "quality_distribution": {
                "accept": sum(1 for e in evaluations if e.recommendation == "accept"),
                "revise": sum(1 for e in evaluations if e.recommendation == "revise"),
                "reject": sum(1 for e in evaluations if e.recommendation == "reject")
            }
        }

    def _get_type_distribution(self, questions: List[GeneratedQuestion]) -> Dict[str, int]:
        distribution: Dict[str, int] = {}
        for q in questions:
            t = getattr(q, "type", "unknown") or "unknown"
            distribution[t] = distribution.get(t, 0) + 1
        return distribution

    def _get_difficulty_distribution(self, questions: List[GeneratedQuestion]) -> Dict[str, int]:
        distribution: Dict[str, int] = {}
        for q in questions:
            d = getattr(q, "difficulty", "unknown") or "unknown"
            distribution[d] = distribution.get(d, 0) + 1
        return distribution

    def _generate_recommendations(
        self,
        request: GenerateQuestionsRequest,
        response: GenerateQuestionResponse,
        evaluations: List[QuestionEvaluation],
        aggregate_scores: Dict[str, float]
    ) -> List[str]:
        recs: List[str] = []

        # Check for critical issues first (following override rules)
        critical_issues_found = []
        for eval_item in evaluations:
            for issue in eval_item.issues:
                if any(critical in issue.lower() for critical in [
                    "answer letter doesn't map to any option",
                    "correct answer not present among options",
                    "no correct option exists",
                    "impossible pattern"
                ]):
                    critical_issues_found.append(f"Q{eval_item.question_id + 1}: {issue}")

        if critical_issues_found:
            recs.append(f"🚨 CRITICAL: Fix answer mapping/option availability issues for request {response.request_id}:")
            for critical_issue in critical_issues_found[:5]:  # Show first 5
                recs.append(f"  - {critical_issue}")

        overall = aggregate_scores.get("overall", 0.0)
        if overall >= 0.8:
            recs.append("✅ Overall quality is appropriate" + (" (after fixing critical issues)" if critical_issues_found else ""))
        elif overall >= 0.6:
            recs.append("⚠️ Consider revising questions with scores below 0.6")
        else:
            recs.append("❌ Significant improvements needed across multiple dimensions")

        # Specific dimension nudges
        for dim in EvaluationDimension:
            score = aggregate_scores.get(dim.value, 0.0)
            if score < 0.6:
                if dim == EvaluationDimension.CORRECTNESS:
                    recs.append("🔧 Review mathematical/factual accuracy")
                elif dim == EvaluationDimension.GRADE_ALIGNMENT:
                    recs.append(f"📚 Adjust complexity for grade {safe_getattr(request, 'grade', 'N/A')}")
                elif dim == EvaluationDimension.EXPLANATION_QUALITY:
                    recs.append("📝 Enhance explanations with clearer, guided steps")
                elif dim == EvaluationDimension.LANGUAGE_QUALITY:
                    recs.append(f"🌐 Improve {safe_getattr(request, 'language', 'English')} language quality")
                elif dim == EvaluationDimension.FORMAT_COMPLIANCE:
                    recs.append("📐 Fix formatting (MCQ options/answers; fill-in without options)")

        rejected = [e for e in evaluations if e.recommendation == "reject"]
        if rejected:
            recs.append(f"🔄 Regenerate {len(rejected)} rejected question(s)")

        revised = [e for e in evaluations if e.recommendation == "revise"]
        if revised:
            recs.append(f"✏️ Revise {len(revised)} question(s) based on suggestions")

        return recs

    def generate_report(self, evaluation: ResponseEvaluation) -> str:
        """Generate a human-readable evaluation report."""
        report = []
        report.append(f"# Evaluation Report for Request {evaluation.request_id}\n")
        report.append(f"## Overall Score: {evaluation.overall_score:.2%}\n")

        report.append("## Dimension Scores:")
        for dim, score in evaluation.aggregate_scores.items():
            if dim != "overall":
                report.append(f"- {dim.replace('_', ' ').title()}: {score:.2%}")

        report.append("\n## Compliance Report:")
        comp = evaluation.compliance_report
        report.append(f"- Questions: {comp['count_compliance']['generated']}/{comp['count_compliance']['requested']}")
        report.append(f"- Grade Level: {'✅' if comp['grade_compliance']['compliant'] else '❌'}")

        report.append("\n## Quality Distribution:")
        qual = comp["quality_distribution"]
        report.append(f"- Accepted: {qual['accept']}")
        report.append(f"- Needs Revision: {qual['revise']}")
        report.append(f"- Rejected: {qual['reject']}")

        report.append("\n## Individual Question Evaluations:")
        for qe in evaluation.question_evaluations:
            report.append(f"\n### Question {qe.question_id + 1}")
            report.append(f"- Overall: {qe.overall_score:.2%} ({qe.recommendation.upper()})")
            report.append(f"- Strengths: {', '.join(qe.strengths[:3]) if qe.strengths else 'None'}")
            report.append(f"- Issues: {', '.join(qe.issues[:3]) if qe.issues else 'None'}")
            if qe.suggested_improvements:
                report.append(f"- Suggestions: {', '.join(qe.suggested_improvements[:3])}")

        report.append("\n## Recommendations:")
        for rec in evaluation.recommendations:
            report.append(f"- {rec}")

        return "\n".join(report)


# ---------------- Convenience function (kept same name/signature) ----------------
def evaluate_api_response(
    request: GenerateQuestionsRequest,
    response: GenerateQuestionResponse,
    generate_report: bool = True,
    update_baseline: bool = True,
    baseline_file: str = "baseline_evaluation.json"
) -> Tuple[ResponseEvaluation, Optional[str]]:
    """
    Convenience function to evaluate an API response.

    Args:
        request: The original request
        response: The API response
        generate_report: Whether to generate a text report
        update_baseline: Whether to update the baseline evaluation file
        baseline_file: Path to the baseline evaluation file

    Returns:
        Tuple of (evaluation, report_text)
    """
    evaluator = ResponseEvaluator()
    evaluation = evaluator.evaluate_response(request, response, update_baseline=update_baseline, baseline_file=baseline_file)
    report = evaluator.generate_report(evaluation) if generate_report else None
    return evaluation, report
