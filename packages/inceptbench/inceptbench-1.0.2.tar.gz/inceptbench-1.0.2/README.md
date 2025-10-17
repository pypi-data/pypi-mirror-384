# InceptBench

Educational question evaluation CLI tool with comprehensive AI-powered assessment. Evaluates questions locally using multiple evaluation modules including compliance_math_evaluator, answer_verification, reading_question_qc, and EduBench tasks.

[![PyPI version](https://badge.fury.io/py/inceptbench.svg)](https://badge.fury.io/py/inceptbench)
[![Python Version](https://img.shields.io/pypi/pyversions/inceptbench.svg)](https://pypi.org/project/inceptbench/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Repository**: [https://github.com/trilogy-group/inceptbench](https://github.com/trilogy-group/inceptbench)

## Features

🎯 **Comprehensive Evaluation**
- **Internal Evaluator** - Scaffolding quality and DI compliance scoring (0-1 scale)
- **Answer Verification** - GPT-4o powered correctness checking
- **Reading Question QC** - MCQ distractor and question quality checks
- **EduBench Tasks** - Educational benchmarks (QA, EC, IP, AG, QG, TMG) (0-10 scale)

📊 **Flexible Output**
- Simplified mode (default) for quick score viewing - ~95% smaller output
- Full mode (`--full`) with all detailed metrics, issues, strengths, and reasoning
- Append mode (`-a`) for collecting multiple evaluations
- JSON output for easy integration

🚀 **Easy to Use**
- Simple CLI interface
- Runs locally with OpenAI and Anthropic API integrations
- Batch processing support
- Only evaluates requested modules (configurable via `submodules_to_run`)

## Installation

```bash
pip install inceptbench

# Or upgrade to latest version
pip install inceptbench --upgrade --no-cache-dir
```

## Quick Start

### 1. Set up API Keys

Create a `.env` file in your working directory:

```bash
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
HUGGINGFACE_TOKEN=your_hf_token  # Optional for EduBench tasks
```

### 2. Generate Sample File

```bash
inceptbench example
```

This creates `qs.json` with a complete example question including the `submodules_to_run` configuration.

### 3. Evaluate

```bash
# Simplified output (default)
inceptbench evaluate qs.json

# With progress messages
inceptbench evaluate qs.json --verbose

# Full detailed output
inceptbench evaluate qs.json --full --verbose
```

## Usage

### Commands

#### `evaluate` - Evaluate questions from JSON file

```bash
# Basic evaluation (simplified scores - default)
inceptbench evaluate questions.json

# Verbose output with progress messages
inceptbench evaluate questions.json --verbose

# Full detailed evaluation results
inceptbench evaluate questions.json --full

# Save results to file (overwrite)
inceptbench evaluate questions.json -o results.json

# Append results to file (creates if not exists)
inceptbench evaluate questions.json -a all_evaluations.json --verbose

# Full detailed results to file
inceptbench evaluate questions.json --full -o detailed_results.json --verbose
```

#### `example` - Generate sample input file

```bash
# Generate qs.json (default)
inceptbench example

# Save to custom filename
inceptbench example -o sample.json
```

#### `help` - Show detailed help

```bash
inceptbench help
```

## Input Format

The input JSON file must contain:
- `submodules_to_run`: List of evaluation modules to run
- `generated_questions`: Array of questions to evaluate

**Available Modules:**
- `compliance_math_evaluator` - Internal evaluator (scaffolding + DI compliance)
- `answer_verification` - GPT-4o answer correctness checking
- `reading_question_qc` - MCQ distractor quality checks
- `directionai_edubench` - EduBench educational tasks (QA, EC, IP, etc.)

**Example:**

```json
{
  "submodules_to_run": [
    "compliance_math_evaluator",
    "answer_verification",
    "reading_question_qc"
  ],
  "generated_questions": [
    {
      "id": "q1",
      "type": "mcq",
      "question": "إذا كان ثمن 2 قلم هو 14 ريالًا، فما ثمن 5 أقلام بنفس المعدل؟",
      "answer": "35 ريالًا",
      "answer_explanation": "الخطوة 1: تحليل المسألة — لدينا ثمن 2 قلم وهو 14 ريالًا. نحتاج إلى معرفة ثمن 5 أقلام بنفس المعدل. يجب التفكير في العلاقة بين عدد الأقلام والسعر وكيفية تحويل عدد الأقلام بمعدل ثابت.\nالخطوة 2: تطوير الاستراتيجية — يمكننا أولًا إيجاد ثمن قلم واحد بقسمة 14 ÷ 2 = 7 ريال، ثم ضربه في 5 لإيجاد ثمن 5 أقلام: 7 × 5 = 35 ريالًا.\nالخطوة 3: التطبيق والتحقق — نتحقق من منطقية الإجابة بمقارنة السعر بعدد الأقلام. السعر يتناسب طرديًا مع العدد، وبالتالي 35 ريالًا هي الإجابة الصحيحة والمنطقية.",
      "answer_options": {
        "A": "28 ريالًا",
        "B": "70 ريالًا",
        "C": "30 ريالًا",
        "D": "35 ريالًا"
      },
      "skill": {
        "title": "Grade 6 Mid-Year Comprehensive Assessment",
        "grade": "6",
        "subject": "mathematics",
        "difficulty": "medium",
        "description": "Apply proportional reasoning, rational number operations, algebraic thinking, geometric measurement, and statistical analysis to solve multi-step real-world problems",
        "language": "ar"
      },
      "image_url": null,
      "additional_details": "🔹 **Question generation logic:**\nThis question targets proportional reasoning for Grade 6 students, testing their ability to apply ratios and unit rates to real-world problems. It follows a classic proportionality structure — starting with a known ratio (2 items for 14 riyals) and scaling it up to 5 items. The stepwise reasoning develops algebraic thinking and promotes estimation checks to confirm logical correctness.\n\n🔹 **Personalized insight examples:**\n- Choosing 28 ريالًا shows a misunderstanding by doubling instead of proportionally scaling.\n- Choosing 7 ريالًا indicates the learner found the unit rate but didn't scale it up to 5.\n- Choosing 14 ريالًا confuses the given 2-item cost with the required 5-item cost.\n\n🔹 **Instructional design & DI integration:**\nThe question aligns with *Percent, Ratio, and Probability* learning targets. In DI format 15.7, it models how equivalent fractions and proportional relationships can predict outcomes across different scales. This builds foundational understanding for probability and proportional reasoning. By using a simple, relatable context (price of pens), it connects mathematical ratios to practical real-world applications, supporting concept transfer and cognitive engagement."
    }
  ]
}
```

Use `inceptbench example` to generate this file automatically.

## Authentication

**Required API Keys:**

The tool integrates with OpenAI and Anthropic APIs for running evaluations. Create a `.env` file in your working directory:

```bash
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
HUGGINGFACE_TOKEN=your_hf_token  # Optional, for EduBench tasks
```

The tool will automatically load these from the `.env` file when you run evaluations.

## Output Format

### Simplified Mode (default)

Returns only essential scores - **~95% smaller output**:

```json
{
  "request_id": "c7bce978-66e9-4f8f-ac52-5468340fde8f",
  "evaluations": {
    "q1": {
      "compliance_math_evaluator": {
        "overall": 0.9333333333333333
      },
      "answer_verification": {
        "is_correct": true
      },
      "reading_question_qc": {
        "overall_score": 0.8
      },
      "final_score": 0.9111111111111111
    }
  },
  "evaluation_time_seconds": 12.151433229446411
}
```

**Note:** Only requested modules (specified in `submodules_to_run`) will be included in the output. Unrequested modules will not appear.

### Full Mode (`--full` flag)

Returns complete evaluation details including all scores, issues, strengths, reasoning, and recommendations:

```json
{
  "request_id": "uuid",
  "evaluations": {
    "q1": {
      "compliance_math_evaluator": {
        "overall": 0.95,
        "scores": {
          "correctness": 1.0,
          "grade_alignment": 0.9,
          "difficulty_alignment": 0.9,
          "language_quality": 0.8,
          "pedagogical_value": 0.9,
          "explanation_quality": 0.9,
          "instruction_adherence": 0.9,
          "format_compliance": 1.0,
          "query_relevance": 1.0,
          "di_compliance": 0.9
        },
        "issues": [],
        "strengths": ["Clear explanation", "Good grade alignment"],
        "recommendation": "accept",
        "suggested_improvements": [...],
        "di_scores": {...},
        "section_evaluations": {...}
      },
      "answer_verification": {
        "is_correct": true,
        "correct_answer": "35 ريالًا",
        "confidence": 10,
        "reasoning": "The answer is correct because..."
      },
      "reading_question_qc": {
        "overall_score": 0.85,
        "distractor_checks": {...},
        "question_checks": {...},
        "passed": true
      },
      "final_score": 0.91
    }
  },
  "evaluation_time_seconds": 45.2
}
```

## Command Reference

| Command | Description |
|---------|-------------|
| `evaluate` | Evaluate questions from JSON file |
| `example` | Generate sample input file |
| `help` | Show detailed help and usage examples |

### Evaluate Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output PATH` | `-o` | Save results to file (overwrites) |
| `--append PATH` | `-a` | Append results to file (creates if not exists) |
| `--full` | `-f` | Return full detailed evaluation results (default: simplified scores only) |
| `--verbose` | `-v` | Show progress messages |
| `--timeout SECS` | `-t` | Request timeout in seconds (default: 600) |

## Examples

### Basic Evaluation

```bash
# Evaluate with default settings (simplified scores)
inceptbench evaluate questions.json

# With progress messages
inceptbench evaluate questions.json --verbose
```

### Full Detailed Evaluation

```bash
# Get complete evaluation with all details
inceptbench evaluate questions.json --full --verbose

# Save full results to file
inceptbench evaluate questions.json --full -o detailed_results.json
```

### Collecting Multiple Evaluations

```bash
# Append multiple evaluations to one file
inceptbench evaluate test1.json -a all_results.json --verbose
inceptbench evaluate test2.json -a all_results.json --verbose
inceptbench evaluate test3.json -a all_results.json --verbose

# Result: all_results.json contains an array of all 3 evaluations
```

### Batch Processing

```bash
# Evaluate all files and append to one results file
for file in questions/*.json; do
  inceptbench evaluate "$file" -a batch_results.json --verbose
done
```

## Evaluation Modules

### compliance_math_evaluator (Internal Evaluator)
- Scaffolding quality assessment (answer_explanation structure)
- Direct Instruction (DI) compliance checking
- Pedagogical structure validation
- Language quality scoring
- Grade and difficulty alignment
- Returns scores on 0-1 scale

### answer_verification
- GPT-4o powered correctness checking
- Mathematical accuracy validation
- Confidence scoring (0-10)
- Reasoning explanation

### reading_question_qc
- MCQ distractor quality checks
- Question clarity validation
- Overall quality scoring

### directionai_edubench
- **QA**: Question Answering - Can the model answer the question?
- **EC**: Error Correction - Can the model identify and correct errors?
- **IP**: Instructional Planning - Can the model provide step-by-step solutions?
- **AG**: Answer Generation - Can the model generate correct answers?
- **QG**: Question Generation - Question quality assessment
- **TMG**: Test Making Generation - Test design quality
- Returns scores on 0-10 scale

All modules are optional and configurable via `submodules_to_run` in the input JSON.

## Requirements

- Python >= 3.11
- OpenAI API key
- Anthropic API key
- Hugging Face token (optional, for EduBench tasks)

## Support

- **Repository**: [https://github.com/trilogy-group/inceptbench](https://github.com/trilogy-group/inceptbench)
- **Issues**: [GitHub Issues](https://github.com/trilogy-group/inceptbench/issues)
- **Help**: Run `inceptbench help` for detailed documentation

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Made by the Incept Team**
