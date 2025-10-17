# Evaluator

## Directory Structure

```
evaluator/
├── scripts/              # Utility scripts for analysis and reporting
│   ├── benchmark_report.py         # Generate comprehensive benchmark reports
│   ├── delete_low_scores.py        # Analyze and delete low-scoring questions
│   └── generate_jsonl_report.py    # Generate reports from JSONL evaluation runs
│
├── reports/              # Generated benchmark and evaluation reports
│   ├── incept_benchmark_report.md      # Main benchmark report (Markdown)
│   ├── incept_benchmark_report.json    # Main benchmark report (JSON)
│   └── evaluation_*_report.*           # Specific evaluation run reports
│
├── output/               # Evaluation run outputs
│   └── evaluation_runs/             # Raw evaluation JSONL files
│       └── MM_DD_YYYY/              # Organized by date
│
├── archive/              # Archived data and historical records
│   └── low_scores_deleted.json      # Record of deleted low-scoring questions
│
├── runs/                 # Evaluation interpreters and legacy scripts
│   ├── interpreter.py               # Original evaluation interpreter
│   └── interpreter_v2.py            # Database-based evaluation interpreter
│
└── EduBench/             # EduBench evaluation framework (submodule)
```

## EduBench Framework Integration

See `EDUBENCH_INTEGRATION.md` for detailed integration documentation.

### Architecture

**Clean separation of concerns:**
- **`edubench.py`** (192 lines): Minimal model interface
  - `query_hf_model()`: HuggingFace API calls with retry logic
  - `get_normal_answer()`: EDU-Qwen2.5-7B wrapper
  - `verify_answer_with_gpt4()`: Answer verification helper
  - **NO SCORING LOGIC** - just returns raw responses

- **`unified_evaluator.py`**: Complete evaluation orchestrator
  - Imports EduBench's official `TASK_PROMPT_TEMPLATES`
  - Calls `get_normal_answer()` for model responses
  - **ALL SCORING** via `score_edubench_response_with_llm()` using GPT-5 as judge
  - Evaluates across EduBench's 12 dimensions and 3 principles
  - Returns 0-10 scores matching EduBench paper methodology
  - **Calibrated for EDU-Qwen2.5-7B**: Judge ignores verbosity/repetition, focuses on content quality

### Why This Architecture?

**Problem:** EduBench paper uses LLM-as-judge but provides no scoring code.

**Solution:**
1. Use their official prompts and model (reproducible)
2. Implement LLM-as-judge ourselves following their methodology
3. Keep model interface clean and scoring logic separate

**Benefits:**
- No hardcoded scoring rules
- Judge calibrated for EDU-Qwen2.5-7B's verbose output style
- Scores focus on educational content quality, not formatting
- All scoring in one place (`unified_evaluator.py`)
- Model interface stays minimal and focused

**Scoring Calibration:**

The LLM judge is explicitly instructed to:
- **Ignore**: Verbosity, repetition, multiple JSON blocks, formatting issues
- **Focus on**: Factual accuracy, pedagogical soundness, task completion
- **Extract best interpretation**: Parse through verbose responses to find core content

This ensures fair scoring when using a 7B model against benchmarks from frontier models.

### Running Evaluations

Use `unified_evaluator.py` API (not `edubench.py` directly):

```python
from src.evaluator.unified_evaluator import evaluate_unified_with_response
from src.dto.question_generation import EvaluationModules

# Option 1: Evaluate AI model responses to your questions (6 EduBench tasks)
modules = EvaluationModules(
    v3_evaluation=True,
    answer_verification=True,
    edubench_tasks=["QA", "EC", "IP", "AG", "QG", "TMG"]
)

result = evaluate_unified_with_response(
    request=request,
    questions=questions,
    modules=modules
)

# Returns scores from AI model responses
print(result['overall_scores']['edubench_weighted_score'])  # 0-10 scale

# Option 2: Directly evaluate YOUR question content (12 EduBench dimensions)
modules = EvaluationModules(
    v3_evaluation=True,
    answer_verification=True,
    edubench_direct=True,  # Evaluate question directly
    edubench_tasks=[]  # Skip AI model response testing
)

result = evaluate_unified_with_response(
    request=request,
    questions=questions,
    modules=modules
)

# Returns direct evaluation of your question quality
print(result['overall_scores']['edubench_direct_average'])  # 0-10 scale
print(result['edubench_direct'][0])  # Full breakdown by dimension
```

**Two Evaluation Modes:**

1. **`edubench_tasks`** (AI Model Response Testing): Tests how well an AI model (EDU-Qwen2.5-7B) can respond to your question across 6 task types (QA, EC, IP, AG, QG, TMG). This validates that your question is clear enough for AI to understand.

2. **`edubench_direct`** (Direct Question Evaluation): Evaluates YOUR generated question content directly across EduBench's 12 dimensions (IFTC, RTC, CRSC, SEI, BFA, DKA, RPR, EICP, CSI, MGP, PAS, HOTS). This assesses the educational quality of your question itself.

**References:**
- EduBench paper: https://arxiv.org/pdf/2505.16160
- EduBench model: https://huggingface.co/DirectionAI/EDU-Qwen2.5-7B
- EduBench repo: https://github.com/StanHus/EduBench (submodule)
- Our implementation: `unified_evaluator.py` + `edubench.py`

## Key Scripts

### 1. benchmark_report.py

Generate comprehensive benchmark reports from the database.

**Usage:**
```bash
POSTGRES_URI="..." python scripts/benchmark_report.py \
  --start-date 2025-09-30 \
  --end-date 2025-10-02 \
  --output-md reports/benchmark.md \
  --output-json reports/benchmark.json
```

**Features:**
- Query orchestrator-pipeline questions from database
- Calculate weighted scores using proper formula
- Generate per-grade performance breakdowns
- Export comprehensive markdown and JSON reports
- Filter by date range and model

### 2. delete_low_scores.py

Analyze question scores and remove low-performing questions from the database.

**Usage:**
```bash
POSTGRES_URI="..." python scripts/delete_low_scores.py \
  --threshold 8.0 \
  --delete \
  --confirm \
  --export deleted_questions.json
```

**Features:**
- Analyze score distribution across all questions
- Filter by quality threshold (default: 8.0/10.0)
- Preview deletion candidates (dry-run mode)
- Export deleted questions for record-keeping
- Breakdown by grade and model

### 3. generate_jsonl_report.py

Generate detailed reports from JSONL evaluation run files.

**Usage:**
```bash
python scripts/generate_jsonl_report.py \
  output/evaluation_runs/07_10_2025/13-01-37.jsonl \
  --output-md reports/eval_report.md \
  --output-json reports/eval_report.json
```

**Features:**
- Parse JSONL evaluation outputs
- Calculate weighted scores using proper formula
- Generate per-grade and per-subject breakdowns
- Provide quality assessment (PASS/BELOW THRESHOLD)
- Export detailed markdown and JSON reports

### 4. interpreter_v2.py

Database-based evaluation interpreter for orchestrator-pipeline questions.

**Usage:**
```bash
# View all evaluated questions
POSTGRES_URI="..." python runs/interpreter_v2.py

# Filter by grade with date range
POSTGRES_URI="..." python runs/interpreter_v2.py \
  --grade 5 \
  --start-date 2025-09-30 \
  --end-date 2025-10-02 \
  --detailed
```

Available parameters:
- `--grade`: Filter by grade level
- `--subject`: Filter by subject
- `--language`: Filter by language (ar, en)
- `--start-date`: Filter by start date (YYYY-MM-DD)
- `--end-date`: Filter by end date (YYYY-MM-DD)
- `--limit`: Maximum questions to analyze
- `--detailed`: Show detailed statistics
- `--output`: Export to JSON file

## Workflow

### 1. Run Evaluations

```bash
# Run EduBench evaluation on recent questions
python edubench.py --db_limit 300 --db_grade 3 --db_hours 720
```

### 2. Analyze Results

```bash
# Interpret JSONL results
python scripts/generate_jsonl_report.py \
  output/evaluation_runs/MM_DD_YYYY/HH-MM-SS.jsonl
```

### 3. Clean Low-Quality Questions

```bash
# Remove questions below threshold (dry-run first)
POSTGRES_URI="..." python scripts/delete_low_scores.py --threshold 8.0

# Actually delete after review
POSTGRES_URI="..." python scripts/delete_low_scores.py \
  --threshold 8.0 --delete --confirm --export archive/deleted.json
```

### 4. Generate Benchmark Reports

```bash
# Create comprehensive benchmark report
POSTGRES_URI="..." python scripts/benchmark_report.py \
  --start-date 2025-09-30 \
  --end-date 2025-10-02 \
  --output-md reports/incept_benchmark_report.md \
  --output-json reports/incept_benchmark_report.json
```

## Prompt Engineering Benchmarks

Located in `src/prompt_engineering/`, these provide baseline comparisons for our orchestrator pipeline.

### Falcon Benchmark (`falcon/main.py`)

Uses Falcon-180B with direct prompt engineering. Requests 5 questions per call with parallel generation (5 workers). This small batch size ensures maximum quality per request while maintaining throughput.

```bash
python src/prompt_engineering/falcon/main.py
```

### OpenAI Benchmark (`openai/main.py`)

Uses GPT-4 with direct prompt engineering. Requests 10 questions per call with parallel generation (10 workers). Similar batch strategy prioritizes quality over bulk generation.

```bash
python src/prompt_engineering/openai/main.py
```

### Why These Are Strong Benchmarks

These implementations represent the upper bound of what pure prompt engineering can achieve:
- **Small batch requests** (5-10 questions): Prevents quality degradation from large batch processing
- **Parallel execution**: Multiple concurrent requests maximize throughput without compromising quality
- **Frontier models**: GPT-4 and Falcon-180B are among the most capable models for Arabic educational content
- **Direct prompting**: No intermediate steps or complexity—just optimal prompts to the best models

This configuration ensures our orchestrator pipeline is compared against the best possible prompt-engineering baseline, not a suboptimal implementation.

## Database Schema

Questions are stored in the `uae_educational_questions_cleaned_duplicate` table:

**Key Fields:**
- `id`: Unique question identifier
- `normalized_grade`: Grade level (3, 5, 8, 9, 12)
- `subject_area`: Subject (Mathematics, Science, etc.)
- `language`: Language code (ar, en)
- `evaluation_edubench`: JSON evaluation results
- `extracted_by_model`: Model used for generation
- `created_at`: Timestamp

## Environment Variables

```bash
# Required for database operations
export POSTGRES_URI="postgresql://user:password@host:port/database"

# Optional: HuggingFace API token for model inference
export HF_TOKEN="your_token_here"
```

## Contributing

When adding new scripts or reports:
1. Place utility scripts in `scripts/`
2. Save generated reports in `reports/`
3. Store evaluation runs in `output/evaluation_runs/MM_DD_YYYY/`
4. Archive historical data in `archive/`
5. Update this README with usage instructions

---

*Last Updated: October 13, 2025*
