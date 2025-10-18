from pydantic import BaseModel, Field
from typing import Any, List, Optional, Literal, Dict


class SkillInfo(BaseModel):
    id: str
    title: str
    unit: str
    grade: int


class SkillContext(BaseModel):
    """V1 Skill Context - maintains backward compatibility"""
    id: Optional[str] = None
    title: str
    unit_name: str
    lesson_title: str
    standard_description: Optional[str] = None
    substandard_description: Optional[str] = None


class SkillContextV1_1(BaseModel):
    """V1.1 Skill Context - cleaner naming that matches curriculum structure"""
    id: Optional[str] = None  # substandard_id (e.g., "CCSS.MATH.CONTENT.3.NBT.A.1+2")
    title: str  # lesson_title from curriculum (e.g., "Rounding")
    unit_name: str  # unit_name from curriculum (e.g., "Place Value and Rounding")
    description: Optional[str] = None  # substandard_description from curriculum (e.g., "Round to the nearest 10 or 100.")


class ExplanationStep(BaseModel):
    title: str
    content: str
    image: Optional[str] = None
    image_alt_text: Optional[str] = None


class PersonalizedInsight(BaseModel):
    answer: str
    insight: str


class DetailedExplanation(BaseModel):
    steps: List[ExplanationStep]
    personalized_academic_insights: List[PersonalizedInsight]


class VoiceoverStepScript(BaseModel):
    step_number: int
    script: str


class VoiceoverScript(BaseModel):
    question_script: str
    answer_choice_scripts: Optional[List[str]] = None  # Only for MCQ
    explanation_step_scripts: List[VoiceoverStepScript]


class GeneratedQuestion(BaseModel):
    type: Literal["mcq", "fill-in"]  # MCQ and fill-in questions supported
    question: str
    answer: str  # The actual answer text (e.g., "4 cm")
    # difficulty: Literal["easy", "medium", "hard", "expert"]
    difficulty: str
    explanation: str
    options: Optional[Dict[str, str]] = None  # Dict format for MCQ: {"A": "4 cm", "B": "0.4 cm", ...}
    answer_choice: Optional[str] = None  # Only for MCQ: "A", "B", "C", or "D"
    detailed_explanation: Optional[DetailedExplanation] = None
    voiceover_script: Optional[VoiceoverScript] = None
    skill: Optional[SkillInfo] = None
    image_url: Optional[str] = None
    di_formats_used: Optional[List[dict]] = Field(default=None, description="DI formats used for scaffolding generation")


class GenerateQuestionsRequest(BaseModel):
    grade: int = Field(..., ge=0, le=12, description="Grade level (0-12)")
    instructions: str = Field(...,
                              description="Instructions for question generation")
    count: int = Field(
        default=5, ge=1, le=200, description="Number of questions (default: 5)")
    question_type: Literal["mcq", "fill-in"] = Field(
        default="mcq", description="Question type: 'mcq' (multiple choice) or 'fill-in' (blank completion)")
    language: str = Field(
        default="english", description="Language for content (english/arabic)")
    difficulty: Optional[Literal["easy", "medium", "hard", "expert", "mixed"]] = Field(
        default="mixed", description="Difficulty level (default: mixed)")
    subject: Optional[str] = Field(
        default=None, description="Subject override (e.g., 'mathematics', 'science') - if not provided, will be auto-detected")
    model: Optional[str] = Field(
        default="openai", description="AI to use: 'openai' or 'falcon' (default: openai)")
    translate: bool = Field(
        default=False, description="Enable translation for scaffolding content (default: false)")
    evaluate: bool = Field(
        default=False, description="Enable quality evaluation of generated questions (default: false)")
    existing_ratio: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Ratio of questions to pull from existing database (0.0-1.0). E.g., 0.5 = 50% from DB, 50% newly generated. Default: 0.0 (all new)")
    partial_match_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Similarity threshold for partial matching of skill to broad_topic/subtopic in DB (0.0-1.0). E.g., 0.7 = 70% match required, 0.5 = 50% match. Default: 0.7")

    # Skill-related fields (optional but recommended for context)
    skill: Optional[SkillContext] = None

    # Alternative to skill object - direct topic specification
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    unit: Optional[str] = None

    # Additional context - maybe in future
    student_level: Optional[Literal["struggling",
                                    "average", "advanced"]] = None
    previous_mistakes: Optional[List[str]] = None


class GenerateQuestionsRequestV1_1(BaseModel):
    """V1.1 Request Model - uses cleaner SkillContextV1_1"""
    grade: int = Field(..., ge=0, le=12, description="Grade level (0-12)")
    instructions: str = Field(...,
                              description="Instructions for question generation")
    count: int = Field(
        default=5, ge=1, le=200, description="Number of questions (default: 5)")
    question_type: Literal["mcq", "fill-in"] = Field(
        default="mcq", description="Question type: 'mcq' (multiple choice) or 'fill-in' (blank completion)")
    language: str = Field(
        default="english", description="Language for content (english/arabic)")
    difficulty: Optional[Literal["easy", "medium", "hard", "expert", "mixed"]] = Field(
        default="mixed", description="Difficulty level (default: mixed)")
    subject: Optional[str] = Field(
        default=None, description="Subject override (e.g., 'mathematics', 'science') - if not provided, will be auto-detected")
    model: Optional[str] = Field(
        default="openai", description="AI to use: 'openai' or 'falcon' (default: openai)")
    translate: bool = Field(
        default=False, description="Enable translation for scaffolding content (default: false)")
    evaluate: bool = Field(
        default=False, description="Enable quality evaluation of generated questions (default: false)")
    existing_ratio: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Ratio of questions to pull from existing database (0.0-1.0). E.g., 0.5 = 50% from DB, 50% newly generated. Default: 0.5")
    partial_match_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Similarity threshold for partial matching of skill to broad_topic/subtopic in DB (0.0-1.0). E.g., 0.7 = 70% match required, 0.5 = 50% match. Default: 0.7")

    # Skill-related fields (optional but recommended for context)
    skill: Optional[SkillContextV1_1] = None

    # Alternative to skill object - direct topic specification
    topic: Optional[str] = None
    subtopic: Optional[str] = None
    unit: Optional[str] = None

    # Additional context - maybe in future
    student_level: Optional[Literal["struggling",
                                    "average", "advanced"]] = None
    previous_mistakes: Optional[List[str]] = None


class SectionScore(BaseModel):
    """Section-specific evaluation score (V3)"""
    section_score: float
    issues: List[str] = []
    strengths: List[str] = []
    recommendation: str  # "accept", "revise", "reject"


class QuestionEvaluationDetail(BaseModel):
    """Per-question evaluation with section breakdown (V3)"""
    question_id: int
    overall_score: float
    recommendation: str
    question_section: Optional[SectionScore] = None
    scaffolding_section: Optional[SectionScore] = None
    image_section: Optional[SectionScore] = None


class EvaluationInfo(BaseModel):
    model_config = {"extra": "allow"}  # Allow extra fields for flexible evaluation data

    overall_score: Optional[float] = None
    scores: Optional[Dict[str, float]] = None
    recommendations: Optional[List[str]] = None
    report: Optional[str] = None
    error: Optional[str] = None
    # V3 additions
    section_scores: Optional[Dict[str, Dict[str, float]]] = None  # {"question": {"average_score": 0.85, ...}, "scaffolding": {...}, "image": {...}}
    question_evaluations: Optional[List[QuestionEvaluationDetail]] = None


class GenerateQuestionResponse(BaseModel):
    data: List[GeneratedQuestion]
    request_id: str
    total_questions: int
    grade: int
    evaluation: Optional[EvaluationInfo] = None


class GeneratedQuestionForDirectGen(BaseModel):
    """Full question model for direct LLM generation (without di_formats_used which has schema issues)"""
    model_config = {"extra": "forbid"}

    type: Literal["mcq", "fill-in"]
    question: str
    answer: str
    difficulty: str
    explanation: str
    options: Optional[Dict[str, str]] = None
    answer_choice: Optional[str] = None
    detailed_explanation: Optional[DetailedExplanation] = None
    voiceover_script: Optional[VoiceoverScript] = None
    skill: Optional[SkillInfo] = None
    image_url: Optional[str] = None


class GenerateQuestionResponseNoEval(BaseModel):
    """Response model without evaluation - used for direct LLM generation"""
    model_config = {"extra": "forbid"}

    data: List[GeneratedQuestionForDirectGen]
    request_id: str = "direct-generation"
    total_questions: int
    grade: int


class EvaluationModules(BaseModel):
    """Configuration for which evaluation modules to run"""
    v3_evaluation: bool = Field(default=True, description="Run V3 scaffolding/DI compliance evaluation")
    answer_verification: bool = Field(default=True, description="Run GPT-4 answer correctness verification")
    edubench_tasks: Optional[List[str]] = Field(default=["QA", "EC", "IP", "AG", "QG", "TMG"], description="EduBench tasks to run (tests AI model responses). Options: QA, EC, IP, AG, QG, TMG. Set to [] or None to skip.")
    edubench_direct: bool = Field(default=False, description="Evaluate YOUR question directly using EduBench's 12 dimensions (IFTC, RTC, CRSC, SEI, BFA, DKA, RPR, EICP, CSI, MGP, PAS, HOTS)")

    # Future: individual V3 section control
    v3_question_section: bool = Field(default=True, description="Include question section in V3 evaluation")
    v3_scaffolding_section: bool = Field(default=True, description="Include scaffolding section in V3 evaluation")
    v3_image_section: bool = Field(default=True, description="Include image section in V3 evaluation")


class UnifiedEvaluationRequest(BaseModel):
    """Request model for unified evaluation endpoint"""
    request: GenerateQuestionsRequest
    questions: List[GeneratedQuestion]
    task_types: Optional[List[str]] = Field(default=["QA", "EC", "IP"], description="DEPRECATED: Use modules.edubench_tasks instead")
    modules: EvaluationModules = Field(default_factory=EvaluationModules, description="Configuration for which evaluation modules to run")


class PerQuestionV3Score(BaseModel):
    """Per-question V3 evaluation score"""
    correctness: Optional[float] = None
    grade_alignment: Optional[float] = None
    difficulty_alignment: Optional[float] = None
    language_quality: Optional[float] = None
    pedagogical_value: Optional[float] = None
    explanation_quality: Optional[float] = None
    instruction_adherence: Optional[float] = None
    format_compliance: Optional[float] = None
    query_relevance: Optional[float] = None
    di_compliance: Optional[float] = None
    overall: float
    recommendation: str


class PerQuestionAnswerVerification(BaseModel):
    """Per-question answer verification result"""
    is_correct: bool
    confidence: int


class PerQuestionEdubenchScores(BaseModel):
    """Per-question EduBench scores across task types"""
    qa_score: Optional[float] = None
    ec_score: Optional[float] = None
    ip_score: Optional[float] = None
    ag_score: Optional[float] = None
    qg_score: Optional[float] = None
    tmg_score: Optional[float] = None
    average_score: Optional[float] = None


class PerQuestionResult(BaseModel):
    """
    Detailed evaluation results for a single question with pass/fail status.
    This provides actionable per-question information for evaluation.
    """
    question_index: int
    question_text: str
    answer: str

    # V3 Evaluation
    v3_score: Optional[PerQuestionV3Score] = None

    # Answer Verification
    answer_verification: Optional[PerQuestionAnswerVerification] = None

    # EduBench Scores (if enabled)
    edubench_scores: Optional[PerQuestionEdubenchScores] = None

    # EduBench Direct (if enabled)
    edubench_direct_score: Optional[float] = None

    # Binary Pass/Fail Status
    passed: bool = Field(description="Binary pass/fail based on configured thresholds")
    failure_reasons: List[str] = Field(default_factory=list, description="Specific reasons why the question failed (if it failed)")

    # Overall quality score (0-1)
    overall_quality_score: float = Field(description="Composite quality score combining all enabled metrics")


class UnifiedEvaluationResponse(BaseModel):
    """Clean response model for unified evaluation"""
    request_id: str
    overall_scores: Dict[str, float]

    per_question_results: List[PerQuestionResult] = Field(description="Detailed evaluation results for each question with pass/fail status")

    # Aggregated results (kept for backward compatibility)
    v3_scores: Optional[List[Dict[str, Any]]] = None  # Scores (floats) + recommendation (string), None if v3_evaluation=False
    answer_verification: Optional[List[Dict[str, Any]]] = None  # None if answer_verification=False
    edubench_results: Optional[List[Dict[str, Any]]] = None  # Raw responses, None if edubench_tasks=[] or None
    edubench_scores: Optional[Dict[str, Any]] = None  # Interpreted scores (0-10 scale) with QA/EC/IP averages, None if no EduBench tasks
    edubench_direct: Optional[List[Dict[str, Any]]] = None  # Direct evaluation of questions using EduBench's 12 dimensions (IFTC, RTC, CRSC, SEI, BFA, DKA, RPR, EICP, CSI, MGP, PAS, HOTS), None if edubench_direct=False
    summary: Dict[str, Any]
