"""CLI for Incept Eval"""
import click
import json
import sys
import os
from pathlib import Path
import requests
from .client import InceptClient

def get_api_key(api_key=None):
    """Get API key - now optional since we run locally"""
    if api_key:
        return api_key
    if os.getenv('INCEPT_API_KEY'):
        return os.getenv('INCEPT_API_KEY')
    config_file = Path.home() / '.incept' / 'config'
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f).get('api_key')
        except:
            pass
    # API key is now optional - we run locally
    return None

@click.group()
@click.version_option(version='1.0.4')
def cli():
    """Incept Eval - Evaluate educational questions via Incept API

    \b
    CLI tool for evaluating educational questions with comprehensive
    assessment including V3 scaffolding, answer verification, and
    EduBench task evaluation.

    \b
    Commands:
      evaluate    Evaluate questions from a JSON file
      example     Generate sample input JSON file
      configure   Save API key to config file
      help        Show detailed help and usage examples

    \b
    Quick Start:
      1. Configure your API key:
         $ incept-eval configure YOUR_API_KEY

      2. Generate a sample file:
         $ incept-eval example

      3. Evaluate questions:
         $ incept-eval evaluate qs.json --verbose

    \b
    Examples:
      # Basic evaluation (simplified scores)
      $ incept-eval evaluate questions.json

      # Full detailed evaluation results
      $ incept-eval evaluate questions.json --full

      # Save full results to file
      $ incept-eval evaluate questions.json --full -o results.json

      # Append multiple evaluations to one file
      $ incept-eval evaluate test1.json -a all_results.json
      $ incept-eval evaluate test2.json -a all_results.json

      # Use local API server
      $ incept-eval evaluate test.json --api-url http://localhost:8000

    \b
    For detailed help, run: incept-eval help
    """
    pass

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Save results to file (overwrites)')
@click.option('--append', '-a', type=click.Path(), help='Append results to file (creates if not exists)')
@click.option('--api-key', '-k', envvar='INCEPT_API_KEY', help='API key for authentication')
@click.option('--api-url', default='https://uae-poc.inceptapi.com', help='API endpoint URL')
@click.option('--timeout', '-t', type=int, default=600, help='Request timeout in seconds (default: 600)')
@click.option('--pretty', is_flag=True, default=True, help='Show only scores (default: enabled)')
@click.option('--verbose', '-v', is_flag=True, help='Show progress messages')
@click.option('--full', '-f', is_flag=True, help='Return full detailed evaluation results (default: simplified scores only)')
def evaluate(input_file, output, append, api_key, api_url, timeout, pretty, verbose, full):
    """Evaluate questions from JSON file via Incept API

    Sends questions to the Incept API for comprehensive evaluation including:
    - V3 scaffolding and DI compliance scoring
    - Answer correctness verification
    - EduBench task evaluation (QA, EC, IP)

    By default, shows only scores in pretty format. Use --no-pretty for full results.
    """
    try:
        api_key = get_api_key(api_key)
        if verbose:
            click.echo(f"📂 Loading: {input_file}")

        with open(input_file) as f:
            data = json.load(f)

        # Add verbose flag to the data
        data['verbose'] = full

        client = InceptClient(api_key, api_url, timeout=timeout)
        result = client.evaluate_dict(data)

        # Always output full results - pretty only controls formatting
        json_output = json.dumps(result, indent=2 if pretty else None, ensure_ascii=False)

        # Handle output options
        if output:
            # Overwrite mode
            with open(output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            if verbose:
                click.echo(f"✅ Saved to: {output}")
        elif append:
            # Append mode - load existing evaluations or create new list
            existing_data = []
            if Path(append).exists():
                try:
                    with open(append, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            # If file exists but isn't a list, wrap it
                            existing_data = [existing_data]
                except json.JSONDecodeError:
                    if verbose:
                        click.echo(f"⚠️  File exists but is invalid JSON, creating new file")
                    existing_data = []

            # Append new result
            existing_data.append(result)

            # Write back to file
            with open(append, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

            if verbose:
                click.echo(f"✅ Appended to: {append} (total: {len(existing_data)} evaluations)")
        else:
            # Print to stdout
            click.echo(json_output)

    except requests.HTTPError as e:
        click.echo(f"❌ API Error: {e.response.status_code}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.argument('api_key')
def configure(api_key):
    """Save API key to config file"""
    try:
        config_dir = Path.home() / '.incept'
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / 'config'

        with open(config_file, 'w') as f:
            json.dump({'api_key': api_key}, f)

        config_file.chmod(0o600)
        click.echo(f"✅ API key saved to {config_file}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)

@cli.command()
def help():
    """Show detailed help and usage examples"""
    help_text = """
╔═══════════════════════════════════════════════════════════════════╗
║                    INCEPT-EVAL CLI HELP                           ║
╚═══════════════════════════════════════════════════════════════════╝

OVERVIEW:
  Incept Eval is a CLI tool for evaluating educational questions using
  the Incept API. It supports comprehensive evaluation including:
  - V3 scaffolding/DI compliance scoring
  - Answer correctness verification
  - EduBench task evaluation (QA, EC, IP, AG)

INSTALLATION:
  pip install incept-eval

COMMANDS:

  1. configure - Save your API key
     Usage: incept-eval configure YOUR_API_KEY

     This saves your API key to ~/.incept/config for future use.

  2. example - Generate sample input file
     Usage: incept-eval example [OPTIONS]

     Options:
       -o, --output PATH    Save to file (default: qs.json)

     Examples:
       incept-eval example                    # Creates qs.json
       incept-eval example -o sample.json     # Creates sample.json

  3. evaluate - Evaluate questions from JSON file
     Usage: incept-eval evaluate INPUT_FILE [OPTIONS]

     Options:
       -o, --output PATH      Save results to file (overwrites)
       -a, --append PATH      Append results to file (creates if not exists)
       -k, --api-key KEY      API key (or use INCEPT_API_KEY env var)
       --api-url URL          API endpoint (default: https://uae-poc.inceptapi.com)
       --pretty               Show only scores (default: enabled)
       --no-pretty            Show full results including EduBench details
       -v, --verbose          Show progress messages
       -f, --full             Return full detailed evaluation (default: simplified scores)

     Examples:
       # Basic evaluation (simplified scores only)
       incept-eval evaluate test.json

       # Full detailed evaluation results
       incept-eval evaluate test.json --full

       # Save to file (overwrite)
       incept-eval evaluate test.json -o results.json

       # Append to file (creates if not exists)
       incept-eval evaluate test.json -a evaluations.json --verbose

       # Full detailed results with progress messages
       incept-eval evaluate test.json --full --verbose

       # Local API testing
       incept-eval evaluate test.json --api-url http://localhost:8000

API KEY CONFIGURATION (3 methods):

  1. Config file (recommended):
     incept-eval configure YOUR_API_KEY

  2. Environment variable:
     export INCEPT_API_KEY=your_api_key
     incept-eval evaluate test.json

  3. Command line flag:
     incept-eval evaluate test.json --api-key your_api_key

INPUT FILE FORMAT:

  The input JSON file must contain:
  - submodules_to_run: List of evaluation modules to enable
    ["compliance_math_evaluator", "answer_verification", "directionai_edubench"]
  - generated_questions: Array of questions to evaluate with:
    - id: Unique question identifier
    - type: "mcq" or "fill-in"
    - question: Question text
    - answer: Correct answer
    - answer_explanation: Step-by-step explanation
    - answer_options: MCQ options (for MCQ type)
    - skill: Optional skill metadata

  Use 'incept-eval example' to see a complete example.

OUTPUT FORMAT:

  The response includes:
  - request_id: Unique evaluation identifier
  - evaluations: Per-question evaluation results:
    - compliance_math_evaluator: Comprehensive quality scores (0-1 scale)
    - answer_verification: Answer correctness verification
    - directionai_edubench: EduBench task scores (0-10 scale)
    - final_score: Combined score from all modules (0-1 scale)
  - evaluation_time_seconds: Total evaluation time

QUICK START:

  # 1. Configure API key
  incept-eval configure YOUR_API_KEY

  # 2. Generate sample file
  incept-eval example

  # 3. Evaluate questions
  incept-eval evaluate qs.json --verbose

  # 4. Save results (overwrite)
  incept-eval evaluate test.json -o results.json

  # 5. Append multiple evaluations to one file
  incept-eval evaluate test1.json -a all_results.json
  incept-eval evaluate test2.json -a all_results.json
  incept-eval evaluate test3.json -a all_results.json

LOCAL TESTING:

  To test against a local API server:
  incept-eval evaluate test.json --api-url http://localhost:8000

For more information, visit: https://github.com/incept-ai/incept-eval
"""
    click.echo(help_text)

@cli.command()
@click.option('--output', '-o', type=click.Path(), default='qs.json', help='Save to file (default: qs.json)')
def example(output):
    """Generate sample test_questions.json file

    Creates a complete example with Arabic math question for the new
    universal unified benchmark evaluation format.

    By default, saves to qs.json in the current directory.
    """
    example_data = {
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
                "image_url": None,
                "additional_details": "🔹 **Question generation logic:**\nThis question targets proportional reasoning for Grade 6 students, testing their ability to apply ratios and unit rates to real-world problems. It follows a classic proportionality structure — starting with a known ratio (2 items for 14 riyals) and scaling it up to 5 items. The stepwise reasoning develops algebraic thinking and promotes estimation checks to confirm logical correctness.\n\n🔹 **Personalized insight examples:**\n- Choosing 28 ريالًا shows a misunderstanding by doubling instead of proportionally scaling.\n- Choosing 7 ريالًا indicates the learner found the unit rate but didn't scale it up to 5.\n- Choosing 14 ريالًا confuses the given 2-item cost with the required 5-item cost.\n\n🔹 **Instructional design & DI integration:**\nThe question aligns with *Percent, Ratio, and Probability* learning targets. In DI format 15.7, it models how equivalent fractions and proportional relationships can predict outcomes across different scales. This builds foundational understanding for probability and proportional reasoning. By using a simple, relatable context (price of pens), it connects mathematical ratios to practical real-world applications, supporting concept transfer and cognitive engagement."
            }
        ]
    }

    json_output = json.dumps(example_data, indent=2, ensure_ascii=False)

    with open(output, 'w', encoding='utf-8') as f:
        f.write(json_output)
    click.echo(f"✅ Sample file saved to: {output}")

if __name__ == '__main__':
    cli()
