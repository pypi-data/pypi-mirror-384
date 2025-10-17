# Incept Eval

**Local** CLI tool for evaluating educational questions with comprehensive AI-powered assessment. Runs evaluation locally using compliance_math_evaluator, answer_verification, and reading_question_qc modules, plus EduBench tasks.

[![PyPI version](https://badge.fury.io/py/inceptbench.svg)](https://badge.fury.io/py/inceptbench)
[![Python Version](https://img.shields.io/pypi/pyversions/inceptbench.svg)](https://pypi.org/project/inceptbench/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

🎯 **Comprehensive Evaluation**
- **Internal Evaluator** - Scaffolding quality and DI compliance scoring
- **Answer Verification** - GPT-4o powered correctness checking
- **Reading Question QC** - MCQ distractor and question quality checks
- **EduBench Tasks** - Educational benchmarks (QA, EC, IP, AG, QG, TMG)

📊 **Flexible Output**
- Pretty mode for quick score viewing
- Full detailed results with all metrics
- Append mode for collecting multiple evaluations
- JSON output for easy integration

🚀 **Easy to Use**
- Simple CLI interface
- **Runs completely locally** - no API calls to external services
- Requires OpenAI and Anthropic API keys in `.env` file
- Batch processing support

## Installation

```bash
pip install inceptbench
```

## Quick Start

### 1. Install

```bash
pip install inceptbench
```

### 2. Set up API Keys

Create a `.env` file in your project directory with:

```bash
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
HUGGINGFACE_TOKEN=your_hf_token  # Optional for EduBench
```

### 3. Generate Sample File

```bash
inceptbench example
```

This creates `qs.json` with a complete example question.

### 4. Evaluate

```bash
inceptbench evaluate qs.json --verbose
```

## Usage

### Commands

#### `evaluate` - Evaluate questions from JSON file

```bash
# Basic evaluation (pretty mode by default)
inceptbench evaluate questions.json

# Verbose output with progress messages
inceptbench evaluate questions.json --verbose

# Save results to file (overwrite)
inceptbench evaluate questions.json -o results.json

# Append results to file (creates if not exists)
inceptbench evaluate questions.json -a all_evaluations.json --verbose

# Use local API server
inceptbench evaluate questions.json --api-url http://localhost:8000

# Full results without pretty formatting
inceptbench evaluate questions.json --no-pretty
```

#### `example` - Generate sample input file

```bash
# Generate qs.json (default)
inceptbench example

# Save to custom filename
inceptbench example -o sample.json
```

#### `configure` - Save API key

```bash
inceptbench configure YOUR_API_KEY
```

#### `help` - Show detailed help

```bash
inceptbench help
```

## Input Format

The input JSON file must contain:
- `request`: Question generation request metadata (grade, subject, instructions, etc.)
- `questions`: Array of 1-5 questions to evaluate

**Example:**

```json
{
  "request": {
    "grade": 3,
    "count": 2,
    "subject": "mathematics",
    "instructions": "Generate multiplication word problems that involve equal groups.",
    "language": "arabic"
  },
  "questions": [
    {
      "type": "mcq",
      "question": "إذا كان لديك 4 علب من القلم وكل علبة تحتوي على 7 أقلام، كم عدد الأقلام لديك إجمالاً؟",
      "answer": "28",
      "difficulty": "medium",
      "explanation": "استخدام ضرب لحساب مجموع الأقلام في جميع العلب.",
      "options": {
        "A": "21",
        "B": "32",
        "C": "35",
        "D": "28"
      },
      "answer_choice": "D",
      "detailed_explanation": { ... },
      "voiceover_script": { ... },
      "skill": null,
      "image_url": null,
      "di_formats_used": [ ... ]
    }
  ]
}
```

Use `inceptbench example` to see a complete example with all fields.

## Authentication

**Required API Keys:**

The tool requires API keys from OpenAI and Anthropic for running evaluations. Create a `.env` file in your working directory:

```bash
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
HUGGINGFACE_TOKEN=your_hf_token  # Optional, for EduBench tasks
```

The tool will automatically load these from the `.env` file when you run evaluations.

## Output Format

### Pretty Mode (default)

Shows only the scores:

```json
{
  "overall_scores": {
    "total_questions": 1.0,
    "v3_average": 0.9555555555555555,
    "answer_correctness_rate": 1.0,
    "total_edubench_tasks": 3.0
  },
  "v3_scores": [
    {
      "correctness": 1.0,
      "grade_alignment": 1.0,
      "difficulty_alignment": 1.0,
      "language_quality": 0.9,
      "pedagogical_value": 0.9,
      "explanation_quality": 0.8,
      "instruction_adherence": 1.0,
      "format_compliance": 1.0,
      "query_relevance": 1.0,
      "di_compliance": 0.9,
      "overall": 0.9555555555555555,
      "recommendation": "accept"
    }
  ],
  "answer_verification": [
    {
      "is_correct": true,
      "confidence": 10
    }
  ]
}
```

### Full Mode (`--no-pretty`)

Includes all evaluation details:
- `overall_scores`: Aggregate metrics
- `v3_scores`: Per-question scaffolding scores
- `answer_verification`: Answer correctness checks
- `edubench_results`: Full task evaluation responses
- `summary`: Evaluation metadata and timing

## Command Reference

| Command | Description |
|---------|-------------|
| `evaluate` | Evaluate questions from JSON file |
| `example` | Generate sample input file |
| `configure` | Save API key to config file |
| `help` | Show detailed help and usage examples |

### Evaluate Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output PATH` | `-o` | Save results to file (overwrites) |
| `--append PATH` | `-a` | Append results to file (creates if not exists) |
| `--api-key KEY` | `-k` | API key (or use INCEPT_API_KEY env var) |
| `--api-url URL` | | API endpoint (default: production) |
| `--pretty` | | Show only scores (default: true) |
| `--no-pretty` | | Show full results including EduBench details |
| `--verbose` | `-v` | Show progress messages |

## Examples

### Basic Evaluation

```bash
# Evaluate with default settings (pretty mode)
inceptbench evaluate questions.json --verbose
```

### Collecting Multiple Evaluations

```bash
# Append multiple evaluations to one file
inceptbench evaluate test1.json -a all_results.json
inceptbench evaluate test2.json -a all_results.json
inceptbench evaluate test3.json -a all_results.json

# Result: all_results.json contains an array of all 3 evaluations
```

### Batch Processing

```bash
# Evaluate all files and append to one results file
for file in questions/*.json; do
  inceptbench evaluate "$file" -a batch_results.json --verbose
done
```

### Local Development

```bash
# Test against local API server
inceptbench evaluate test.json --api-url http://localhost:8000 --verbose
```

### Full Results

```bash
# Get complete evaluation with EduBench details
inceptbench evaluate questions.json --no-pretty -o full_results.json
```

## Evaluation Modules

The API evaluates questions using three main modules:

### V3 Evaluation
- Scaffolding quality assessment (detailed_explanation steps)
- Direct Instruction (DI) compliance checking
- Pedagogical structure validation
- Language quality scoring
- Grade and difficulty alignment

### Answer Verification
- GPT-4o powered correctness checking
- Mathematical accuracy validation
- Confidence scoring (0-10)

### EduBench Tasks
- **QA**: Question Answering - Can the model answer the question?
- **EC**: Error Correction - Can the model identify and correct errors?
- **IP**: Instructional Planning - Can the model provide step-by-step solutions?

All modules run by default. Future versions will support configurable module selection.

## Requirements

- Python >= 3.11
- Incept API key

## Support

- **Issues**: [GitHub Issues](https://github.com/incept-ai/inceptbench/issues)
- **Help**: Run `inceptbench help` for detailed documentation

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Made by the Incept Team**
