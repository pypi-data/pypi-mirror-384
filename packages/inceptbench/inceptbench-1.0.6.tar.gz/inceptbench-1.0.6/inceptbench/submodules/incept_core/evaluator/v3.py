"""
Evaluator v3: Split evaluation into three sections (Question, Scaffolding, Image).

- Subject-agnostic (math-friendly but not math-specific).
- THREE separate evaluations per question:
  1. Question Section: question text, options, answer correctness, format
  2. Scaffolding Section: explanation quality, DI compliance, pedagogical value
  3. Image Section: image relevance and quality (placeholder score of 1.0 for now)
- Each section gets independent score, then combined into overall score
- Aggregates scores and writes to baseline_evaluation.json.
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
from incept_core.dto.question_generation import (
    GenerateQuestionsRequest,
    GenerateQuestionResponse,
    GeneratedQuestion
)
# Removed problematic import dependency

from incept_core.evaluator.llm_interface import simple_solve_with_llm
from incept_core.direct_instruction.principles_constants import (
    DI_INDIVIDUAL_QUESTION_PRINCIPLES,
    DI_SCAFFOLDING_PRINCIPLES,
    GRADE_VOCABULARY_EXAMPLES_AR,
    GRADE_VOCABULARY_EXAMPLES_EN,
)

# Import UniversalGeneratedQuestionInput at runtime to avoid circular dependency
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from incept_core.evaluator.unified_evaluator import UniversalGeneratedQuestionInput

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
    DI_COMPLIANCE = "di_compliance"
    QUERY_RELEVANCE = "query_relevance"


class EvaluationSection(Enum):
    """Three evaluation sections for split scoring"""
    QUESTION = "question"
    SCAFFOLDING = "scaffolding"
    IMAGE = "image"


# Mapping of dimensions to sections
QUESTION_DIMENSIONS = [
    EvaluationDimension.CORRECTNESS,
    EvaluationDimension.GRADE_ALIGNMENT,
    EvaluationDimension.DIFFICULTY_ALIGNMENT,
    EvaluationDimension.LANGUAGE_QUALITY,
    EvaluationDimension.INSTRUCTION_ADHERENCE,
    EvaluationDimension.FORMAT_COMPLIANCE,
    EvaluationDimension.QUERY_RELEVANCE,
]

SCAFFOLDING_DIMENSIONS = [
    EvaluationDimension.PEDAGOGICAL_VALUE,
    EvaluationDimension.EXPLANATION_QUALITY,
    EvaluationDimension.DI_COMPLIANCE,
]

# Image dimensions - placeholder for now
IMAGE_DIMENSIONS = []  # Will be evaluated separately with perfect score


@dataclass
class SectionEvaluation:
    """Evaluation for a single section (question, scaffolding, or image)"""
    section: EvaluationSection
    scores: Dict[EvaluationDimension, float]
    issues: List[str]
    strengths: List[str]
    section_score: float
    recommendation: str


@dataclass
class QuestionEvaluation:
    question_id: int
    scores: Dict[EvaluationDimension, float]
    issues: List[str]
    strengths: List[str]
    overall_score: float
    recommendation: str  # "accept", "revise", "reject"
    suggested_improvements: List[str]
    metadata: Optional[Dict[str, Any]] = None
    # V3 additions: section-specific evaluations
    question_section: Optional[SectionEvaluation] = None
    scaffolding_section: Optional[SectionEvaluation] = None
    image_section: Optional[SectionEvaluation] = None


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


# ----------------- V3: Split evaluation prompt & call -----------------
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
    "format_compliance": 0-10,
    "di_compliance": 0-10,
    "query_relevance": 0-10
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
  ],
  "di_scores": {
    "overall": 0-10,
    "general_principles": 0-10,
    "format_alignment": 0-10,
    "grade_language": 0-10
  },
  "section_evaluations": {
    "question": {
      "section_score": 0-10,
      "issues": [string],
      "strengths": [string],
      "recommendation": "accept" | "revise" | "reject"
    },
    "scaffolding": {
      "section_score": 0-10,
      "issues": [string],
      "strengths": [string],
      "recommendation": "accept" | "revise" | "reject"
    }
  }
}

REPORTING NOTES:
- For answer mapping: Use "Answer mapping is correct (B → 4)" instead of "should be 4 not B"
- For missing correct values: State "correct answer not present among options" clearly
- For impossible patterns: Note "impossible pattern detected" with specifics
- Prioritize structural issues over stylistic concerns
- SECTION SPLIT: Evaluate question and scaffolding as SEPARATE sections with independent scores
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
    },
    "di_compliance": {
        "name": "Direct Instruction Compliance",
        "description": "Evaluates adherence to DI principles, scaffolding formats, and grade-level language",
        "scoring": {
            "9-10": "Fully aligned with DI guidance across principles, format, and vocabulary",
            "7-8": "Minor DI lapses but overall aligned",
            "5-6": "Notable DI issues that need revision",
            "3-4": "Major DI violations (missing scaffolds, inconsistent tone)",
            "1-2": "Fundamentally breaks DI expectations"
        }
    },
    "query_relevance": {
        "name": "Query Relevance",
        "description": "Assesses how well the generated question matches the original user query/instructions/skill context",
        "scoring": {
            "9-10": "Perfectly aligned with query topic, skill, and educational intent",
            "7-8": "Relevant to query with minor topic drift",
            "5-6": "Partially relevant but some misalignment with query intent",
            "3-4": "Significant deviation from requested topic/skill",
            "1-2": "Completely off-topic or unrelated to original query"
        }
    }
}


def build_single_shot_messages(
    q: "UniversalGeneratedQuestionInput",
    total_questions: int
) -> List[Dict[str, str]]:
    """
    Build messages for a single LLM call that evaluates one question.
    Subject-agnostic with strong math tolerance.
    """
    # Prepare detailed_explanation and options representations
    det_exp = as_text(q.answer_explanation) if q.answer_explanation else ""

    options_payload: List[Dict[str, Any]] = []
    raw_options = q.answer_options  # This is Optional[Dict[str, str]]
    if isinstance(raw_options, dict):
        for label, text in raw_options.items():
            options_payload.append({
                "label": str(label),
                "text": as_text(text)
            })

    # Build request metadata from question's skill info (if available)
    req_meta = {
        "requested_grade": q.skill.grade if q.skill else None,
        "requested_language": q.skill.language if q.skill else "en",
        "requested_question_type": q.type,
        "requested_difficulty": q.skill.difficulty if q.skill else "medium",
        "requested_count": total_questions,
        "topic": q.skill.title if q.skill else None,
        "subject": q.skill.subject if q.skill else "mathematics",
        "raw_instructions": q.additional_details if q.additional_details else "",
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

    language = str(req_meta.get("requested_language") or "english").lower()
    grade = req_meta.get("requested_grade")
    grade_examples = None
    if grade is not None:
        try:
            grade_key = f"Grade{int(grade)}"
            store = GRADE_VOCABULARY_EXAMPLES_AR if language.startswith("ar") else GRADE_VOCABULARY_EXAMPLES_EN
            grade_examples = store.get(grade_key)
        except Exception:
            grade_examples = None

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
        "DIRECT INSTRUCTION (DI) SCORING:\n"
        "- Use the provided DI principles to score three sub-metrics (general_principles, format_alignment, grade_language) on a 0-10 scale.\n"
        "- Compute di_compliance overall (0-10) as a weighted summary (40% general, 35% format, 25% grade_language) or best holistic judgment.\n"
        "- If no DI formats are genuinely available, note it in issues but do not assume non-compliance automatically; judge format_alignment based on the scaffolding that is present.\n"
        "- Reflect DI findings in issues/strengths/improvements; call out specific violations.\n\n"
        "QUERY RELEVANCE SCORING (VETO DIMENSION):\n"
        "- Score query_relevance (0-10) by comparing the generated question to the original request context (instructions, skill title, subject, topic).\n"
        "- 9-10: Question directly addresses the requested topic/skill with perfect alignment\n"
        "- 7-8: Question is relevant with minor topic drift\n"
        "- 5-6: Partially relevant but noticeable misalignment\n"
        "- 3-4: Significant deviation from requested topic\n"
        "- 1-2: Completely off-topic or unrelated\n"
        "- This dimension has VETO POWER: query_relevance < 4.0 (0.4 normalized) triggers automatic REJECT\n\n"
        "V3 SECTION-BASED EVALUATION (NEW):\n"
        "You must evaluate TWO SECTIONS independently with separate scores:\n\n"
        "1. QUESTION SECTION (question text, options, answer correctness):\n"
        "   - Focus on: correctness, grade_alignment, difficulty_alignment, language_quality, instruction_adherence, format_compliance, query_relevance\n"
        "   - Check: Is the question text clear? Are options properly formatted? Is the correct answer present? Does it match the requested topic/grade?\n"
        "   - Calculate section_score (0-10) as average of these 7 dimensions\n"
        "   - List section-specific issues/strengths (e.g., 'Question text ambiguous', 'Options well-formatted')\n"
        "   - Provide section recommendation: accept/revise/reject\n\n"
        "2. SCAFFOLDING SECTION (explanation quality, DI compliance, pedagogical value):\n"
        "   - Focus on: pedagogical_value, explanation_quality, di_compliance\n"
        "   - Check: Does explanation guide learning? Does it follow DI principles? Are steps clear and educational?\n"
        "   - Calculate section_score (0-10) as average of these 3 dimensions\n"
        "   - List section-specific issues/strengths (e.g., 'Explanation too brief', 'Good DI scaffolding')\n"
        "   - Provide section recommendation: accept/revise/reject\n\n"
        "IMPORTANT: section_evaluations.question and section_evaluations.scaffolding are REQUIRED fields in your JSON response.\n\n"
        "RECOMMENDATION LOGIC (override rules):\n"
        "- REJECT if: answer letter doesn't map to an option, OR the correct answer is not present among options, OR the keyed option encodes an obviously impossible pattern (e.g., special-angle pair for cos x = −1/3), OR query_relevance < 4.0 (question is off-topic).\n"
        "- REVISE if: structure is OK and answer is correct, but there are issues (topic drift, weak explanation, minor format flaws).\n"
        "- ACCEPT only if: answer mapping is correct, correct value is present, query is relevant, and no major issues.\n\n"
        "REPORTING LANGUAGE:\n"
        "- When the letter maps correctly, avoid 'should be 4 not B.' Prefer: 'Answer mapping is correct (B → 4).'\n"
        "- Explicitly note when no correct option exists, and prioritize that issue over difficulty/style comments.\n\n"
        "OUTPUT REQUIREMENTS:\n"
        "- Return ONLY valid JSON as specified\n"
        "- Include detailed reasoning for each metric score\n"
        "- Provide actionable improvement suggestions\n"
        "- Base recommendation on overall educational quality, subject to override rules\n"
        "- Populate di_scores exactly as specified\n"
        "- **CRITICAL**: You MUST populate section_evaluations.question and section_evaluations.scaffolding with section_score, issues, strengths, and recommendation for each section"
    )

    # Add detailed scoring rubrics for each metric
    scoring_rubrics = {}
    for metric_key, metric_info in METRIC_DESCRIPTIONS.items():
        scoring_rubrics[metric_key] = metric_info["scoring"]

    user = {
        "question": {
            "type": q.type,
            "difficulty": q.skill.difficulty if q.skill else "medium",
            "question_text": q.question,
            "answer": q.answer,
            "answer_choice": None,  # Not in UniversalGeneratedQuestionInput
            "options": options_payload,
            "explanation": q.answer_explanation,
            "detailed_explanation": det_exp,
            "voiceover_script": None,
            "skill": q.skill.title if q.skill else None,
            "image_url": q.image_url if q.image_url else None,
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
            "explanation_leakage": "Check if explanation reveals exact option text instead of guiding reasoning",
            "query_relevance": "CRITICAL: Verify generated question matches original query (instructions, skill, subject, topic). Score < 4.0 = AUTO-REJECT"
        },
        "scoring_rubrics": scoring_rubrics,
        "di_guidance": {
            "individual_principles": DI_INDIVIDUAL_QUESTION_PRINCIPLES.strip(),
            "scaffolding_principles": DI_SCAFFOLDING_PRINCIPLES.strip(),
            "grade_language_examples": grade_examples,
            "weighting": {
                "general_principles": 0.4,
                "format_alignment": 0.35,
                "grade_language": 0.25
            }
        },
        "evaluation_instructions": (
            "MANDATORY PRE-CHECKS FIRST:\n"
            "1. QUERY RELEVANCE: Compare question to original request (instructions, skill, subject, topic). If off-topic or misaligned, query_relevance < 4.0 = AUTO-REJECT\n"
            "2. Verify answer letter maps to existing option (A-D must correspond to actual choices)\n"
            "3. For math problems, confirm correct answer value appears among options\n"
            "4. Check for impossible patterns (e.g., special angles for non-special problems)\n"
            "5. Flag explanation leakage (revealing exact option text)\n\n"
            "If any pre-check fails, mark as REJECT regardless of other qualities.\n"
            "Only then score each metric (0-10) based on rubrics with specific evidence.\n\n"
            "SECTION EVALUATIONS (REQUIRED):\n"
            "You MUST fill out section_evaluations.question AND section_evaluations.scaffolding.\n"
            "For QUESTION section: Calculate average of (correctness, grade_alignment, difficulty_alignment, language_quality, instruction_adherence, format_compliance, query_relevance), provide issues/strengths specific to question quality.\n"
            "For SCAFFOLDING section: Calculate average of (pedagogical_value, explanation_quality, di_compliance), provide issues/strengths specific to explanation/DI quality.\n"
            "DO NOT return empty arrays for issues/strengths - extract relevant ones from your analysis."
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
    q: "UniversalGeneratedQuestionInput",
    total_questions: int,
    provider: str = "openai"  # Can switch to "deepseek" for better human alignment
) -> Dict[str, Any]:
    """
    Perform one LLM call to evaluate a single question item and return normalized scores 0..1.
    Uses configurable provider - EduBench shows DeepSeek V3 has best human alignment.
    """
    import time
    messages = build_single_shot_messages(q, total_questions)

    # Time the LLM call
    llm_start = time.time()

    # Use simplified LLM interface to avoid dependency issues
    data = simple_solve_with_llm(
        messages=messages
    )

    llm_time = time.time() - llm_start
    logger.debug(f"⏱️ LLM evaluation call: {llm_time:.2f}s")

    # DEBUG: Log what we got back
    logger.debug(f"📥 LLM returned keys: {list(data.keys())}")
    if "section_evaluations" in data:
        logger.debug(f"✅ section_evaluations present: {data['section_evaluations'].keys() if data['section_evaluations'] else 'empty'}")
    else:
        logger.warning(f"⚠️ section_evaluations MISSING from LLM response")


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
        EvaluationDimension.QUERY_RELEVANCE: clip01(sr.get("query_relevance", 5) / 10.0),
    }

    issues = list(data.get("issues", []))[:10]
    strengths = list(data.get("strengths", []))[:10]
    suggestions = list(data.get("suggested_improvements", []))[:10]
    recommendation = data.get("recommendation", "revise")
    if recommendation not in {"accept", "revise", "reject"}:
        recommendation = "revise"

    # Academic overall (excludes DI-specific weighting)
    academic_overall = sum(scores.values()) / max(1, len(scores))

    di_scores_raw = data.get("di_scores", {}) or {}
    di_overall_raw = di_scores_raw.get("overall", sr.get("di_compliance", 5))
    di_scores = {
        "overall": clip01(float(di_overall_raw) / 10.0),
        "general_principles": clip01(float(di_scores_raw.get("general_principles", di_overall_raw)) / 10.0),
        "format_alignment": clip01(float(di_scores_raw.get("format_alignment", di_overall_raw)) / 10.0),
        "grade_language": clip01(float(di_scores_raw.get("grade_language", di_overall_raw)) / 10.0),
    }
    scores[EvaluationDimension.DI_COMPLIANCE] = di_scores["overall"]

    return {
        "scores": scores,
        "issues": issues,
        "strengths": strengths,
        "overall": academic_overall,
        "recommendation": recommendation,
        "suggested_improvements": suggestions,
        "di_scores": di_scores,
        "section_evaluations": data.get("section_evaluations", {})
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
        import time
        eval_start = time.time()
        logger.info(f"⏱️ EVALUATOR START: request_id={response.request_id}, questions={len(response.data)}")

        # Evaluate each question in parallel
        question_eval_start = time.time()
        question_evaluations = self._evaluate_questions_parallel(request, response.data)
        question_eval_time = time.time() - question_eval_start
        logger.info(f"⏱️ EVALUATOR: Question evaluation complete in {question_eval_time:.2f}s")

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

        eval_total_time = time.time() - eval_start
        logger.info(f"⏱️ EVALUATOR COMPLETE: Evaluation finished in {eval_total_time:.2f}s, overall_score={evaluation.overall_score:.2%}")

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
                suggested_improvements=["Retry evaluation; ensure JSON-only output; check question fields."],
                metadata={"di_scores": None}
            )

        scores: Dict[EvaluationDimension, float] = dict(res["scores"])
        di_scores = res.get("di_scores", {})

        issues = list(res["issues"])
        strengths = list(res["strengths"])
        suggestions = list(res["suggested_improvements"])

        academic_overall = float(res["overall"])
        di_score = scores.get(EvaluationDimension.DI_COMPLIANCE, 0.0)
        overall = clip01(academic_overall * 0.75 + di_score * 0.25)
        recommendation = res["recommendation"]

        # Enhanced guardrails on recommendation following override rules
        correctness_score = scores.get(EvaluationDimension.CORRECTNESS, 0.0)
        format_score = scores.get(EvaluationDimension.FORMAT_COMPLIANCE, 0.0)
        di_compliance_score = di_score
        query_relevance_score = scores.get(EvaluationDimension.QUERY_RELEVANCE, 0.0)

        # Override rules: REJECT if critical failures detected
        critical_issues = [
            "answer letter doesn't map to any option",
            "correct answer not present among options",
            "answer letter doesn't map",
            "no correct option exists",
            "impossible pattern",
            "special-angle pair for cos",
            "off-topic",
            "unrelated to query",
            "topic drift"
        ]

        has_critical_issue = any(
            any(critical in issue.lower() for critical in critical_issues)
            for issue in issues
        )

        # VETO POWER: Query relevance < 0.4 triggers automatic reject
        if has_critical_issue or correctness_score < 0.4 or format_score < 0.4 or di_compliance_score < 0.3 or query_relevance_score < 0.4:
            if query_relevance_score < 0.4:
                logger.info(f"Question {idx} REJECTED: Query relevance veto (score: {query_relevance_score:.2f} < 0.4)")
            recommendation = "reject"
        elif (
            correctness_score >= 0.6
            and format_score >= 0.6
            and di_compliance_score >= 0.7
            and query_relevance_score >= 0.7
            and overall >= 0.7
        ):
            # Only accept if answer mapping is correct, query is relevant, and no major issues
            recommendation = "accept"
        else:
            recommendation = "revise"

        # V3: Extract section evaluations from LLM response
        section_evals = res.get("section_evaluations", {})

        # DEBUG: Log what LLM actually returned
        if not section_evals or not section_evals.get("question") or not section_evals.get("scaffolding"):
            logger.error(f"❌ LLM did NOT return section_evaluations! Got: {section_evals}")
            logger.error(f"Full LLM response keys: {list(res.keys())}")
        else:
            logger.info(f"✅ LLM returned section_evaluations with question and scaffolding")

        question_section_eval = self._parse_question_section_eval(section_evals.get("question", {}), scores)
        scaffolding_section_eval = self._parse_scaffolding_section_eval(section_evals.get("scaffolding", {}), scores, di_scores)
        image_section_eval = self._create_image_section_eval()

        return QuestionEvaluation(
            question_id=idx,
            scores=scores,
            issues=issues,
            strengths=strengths,
            overall_score=overall,
            recommendation=recommendation,
            suggested_improvements=suggestions,
            metadata={
                "di_scores": di_scores,
            },
            question_section=question_section_eval,
            scaffolding_section=scaffolding_section_eval,
            image_section=image_section_eval
        )

    def _parse_question_section_eval(
        self,
        section_data: Dict[str, Any],
        scores: Dict[EvaluationDimension, float]
    ) -> SectionEvaluation:
        """Parse question section evaluation from LLM response"""
        # Extract only question-related scores
        question_scores = {dim: scores.get(dim, 0.0) for dim in QUESTION_DIMENSIONS}

        # Get section score from LLM (normalize from 0-10 to 0-1)
        # If LLM didn't provide section_score, calculate from dimension averages
        if "section_score" in section_data and section_data["section_score"] is not None:
            section_score = clip01(section_data.get("section_score", 5) / 10.0)
        else:
            # Fallback: calculate from question dimension scores
            section_score = sum(question_scores.values()) / max(1, len(question_scores))
            logger.warning(f"LLM didn't provide question section_score, calculated from dimensions: {section_score:.2f}")

        # Get section-specific issues/strengths from LLM
        section_issues = section_data.get("issues", [])
        section_strengths = section_data.get("strengths", [])
        section_recommendation = section_data.get("recommendation", "revise")

        return SectionEvaluation(
            section=EvaluationSection.QUESTION,
            scores=question_scores,
            issues=section_issues,
            strengths=section_strengths,
            section_score=section_score,
            recommendation=section_recommendation
        )

    def _parse_scaffolding_section_eval(
        self,
        section_data: Dict[str, Any],
        scores: Dict[EvaluationDimension, float],
        di_scores: Dict[str, float]
    ) -> SectionEvaluation:
        """Parse scaffolding section evaluation from LLM response"""
        # Extract only scaffolding-related scores
        scaffolding_scores = {dim: scores.get(dim, 0.0) for dim in SCAFFOLDING_DIMENSIONS}

        # Get section score from LLM (normalize from 0-10 to 0-1)
        # If LLM didn't provide section_score, calculate from dimension averages
        if "section_score" in section_data and section_data["section_score"] is not None:
            section_score = clip01(section_data.get("section_score", 5) / 10.0)
        else:
            # Fallback: calculate from scaffolding dimension scores
            section_score = sum(scaffolding_scores.values()) / max(1, len(scaffolding_scores))
            logger.warning(f"LLM didn't provide scaffolding section_score, calculated from dimensions: {section_score:.2f}")

        # Get section-specific issues/strengths from LLM
        section_issues = section_data.get("issues", [])
        section_strengths = section_data.get("strengths", [])
        section_recommendation = section_data.get("recommendation", "revise")

        return SectionEvaluation(
            section=EvaluationSection.SCAFFOLDING,
            scores=scaffolding_scores,
            issues=section_issues,
            strengths=section_strengths,
            section_score=section_score,
            recommendation=section_recommendation
        )

    def _create_image_section_eval(self) -> SectionEvaluation:
        """Create evaluation for image section (placeholder with perfect score for now)"""
        return SectionEvaluation(
            section=EvaluationSection.IMAGE,
            scores={},  # No specific dimensions yet
            issues=[],
            strengths=["Image evaluation not yet implemented - assigned perfect score"],
            section_score=1.0,  # Perfect score for now
            recommendation="accept"
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

        academic_dims = [d for d in EvaluationDimension if d != EvaluationDimension.DI_COMPLIANCE]
        academic_avg = sum(aggregate[d.value] for d in academic_dims) / max(1, len(academic_dims))
        di_avg = aggregate.get(EvaluationDimension.DI_COMPLIANCE.value, 0.0)

        aggregate["overall_academic"] = academic_avg
        aggregate["overall_di"] = di_avg
        aggregate["overall"] = clip01(academic_avg * 0.75 + di_avg * 0.25)
        return aggregate

    def _generate_compliance_report(
        self,
        request: GenerateQuestionsRequest,
        response: GenerateQuestionResponse,
        evaluations: List[QuestionEvaluation]
    ) -> Dict[str, Any]:
        # V3: Add section-specific scores
        section_scores = self._calculate_section_scores(evaluations)

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
            },
            "di_compliance": {
                "average_score": self._mean_di_score(evaluations),
                "hard_failures": [
                    idx + 1
                    for idx, e in enumerate(evaluations)
                    if e.scores.get(EvaluationDimension.DI_COMPLIANCE, 0.0) < 0.3
                ],
                "breakdown": [
                    {
                        "question": idx + 1,
                        "scores": (e.metadata or {}).get("di_scores")
                    }
                    for idx, e in enumerate(evaluations)
                    if (e.metadata or {}).get("di_scores") is not None
                ]
            },
            "section_scores": section_scores  # V3: Section breakdown
        }

    def _calculate_section_scores(self, evaluations: List[QuestionEvaluation]) -> Dict[str, Any]:
        """Calculate average scores for each section across all questions"""
        if not evaluations:
            return {}

        question_scores = []
        scaffolding_scores = []
        image_scores = []

        for eval_item in evaluations:
            if eval_item.question_section:
                question_scores.append(eval_item.question_section.section_score)
            if eval_item.scaffolding_section:
                scaffolding_scores.append(eval_item.scaffolding_section.section_score)
            if eval_item.image_section:
                image_scores.append(eval_item.image_section.section_score)

        return {
            "question": {
                "average_score": sum(question_scores) / max(1, len(question_scores)) if question_scores else 0.0,
                "count": len(question_scores)
            },
            "scaffolding": {
                "average_score": sum(scaffolding_scores) / max(1, len(scaffolding_scores)) if scaffolding_scores else 0.0,
                "count": len(scaffolding_scores)
            },
            "image": {
                "average_score": sum(image_scores) / max(1, len(image_scores)) if image_scores else 1.0,
                "count": len(image_scores)
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

    def _mean_di_score(self, evaluations: List[QuestionEvaluation]) -> float:
        if not evaluations:
            return 0.0
        scores = [e.scores.get(EvaluationDimension.DI_COMPLIANCE, 0.0) for e in evaluations]
        return sum(scores) / max(1, len(scores))

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
                elif dim == EvaluationDimension.DI_COMPLIANCE:
                    recs.append("🎯 Tighten DI compliance (concise wording, full scaffolding, grade-aligned tone)")

        rejected = [e for e in evaluations if e.recommendation == "reject"]
        if rejected:
            recs.append(f"🔄 Regenerate {len(rejected)} rejected question(s)")

        revised = [e for e in evaluations if e.recommendation == "revise"]
        if revised:
            recs.append(f"✏️ Revise {len(revised)} question(s) based on suggestions")

        return recs

    def generate_report(self, evaluation: ResponseEvaluation) -> str:
        """Generate a human-readable evaluation report with V3 section breakdowns."""
        report = []
        report.append(f"# Evaluation Report (V3) for Request {evaluation.request_id}\n")
        report.append(f"## Overall Score: {evaluation.overall_score:.2%}\n")

        # V3: Section scores
        section_scores = evaluation.compliance_report.get("section_scores", {})
        if section_scores:
            report.append("## Section Scores:")
            for section_name, section_data in section_scores.items():
                score = section_data.get("average_score", 0.0)
                report.append(f"- {section_name.title()}: {score:.2%}")

        report.append("\n## Dimension Scores:")
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

            # V3: Section breakdown for each question
            if qe.question_section:
                report.append(f"  - Question Section: {qe.question_section.section_score:.2%}")
            if qe.scaffolding_section:
                report.append(f"  - Scaffolding Section: {qe.scaffolding_section.section_score:.2%}")
            if qe.image_section:
                report.append(f"  - Image Section: {qe.image_section.section_score:.2%}")

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
