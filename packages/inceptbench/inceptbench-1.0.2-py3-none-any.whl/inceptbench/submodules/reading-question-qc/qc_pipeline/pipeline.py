#!/usr/bin/env python3
"""
Unified Quality Control Pipeline

Main orchestration script that coordinates question QC, explanation QC,
distractor analysis, and difficulty assessment.

Usage:
  python pipeline.py --input questions.csv --output results/ --mode questions
  python pipeline.py --input questions_with_explanations.csv --output results/ --mode both
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
from dotenv import load_dotenv
import anthropic
from openai import AsyncOpenAI

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qc_pipeline.modules.question_qc import QuestionQCAnalyzer
from qc_pipeline.modules.explanation_qc import ExplanationQCAnalyzer
from qc_pipeline.utils import validate_env_vars, calculate_pass_rate

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class QCPipeline:
    """Main quality control pipeline orchestrator."""

    def __init__(self, args: argparse.Namespace):
        """
        Initialize the pipeline.

        Args:
            args: Command-line arguments
        """
        self.args = args
        self.output_dir = Path(args.output)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Validate env vars and initialize clients
        env_vars = validate_env_vars('ANTHROPIC_API_KEY', 'OPENAI_API_KEY')
        self.claude_client = anthropic.AsyncAnthropic(api_key=env_vars['ANTHROPIC_API_KEY'])
        self.openai_client = AsyncOpenAI(api_key=env_vars['OPENAI_API_KEY'])

        # Initialize analyzers based on mode
        if args.mode in ['questions', 'both']:
            examples_df = pd.read_csv(args.examples) if args.examples else None
            if examples_df is not None:
                logger.info(f"Loaded {len(examples_df)} benchmark questions for difficulty analysis")
            
            self.question_qc = QuestionQCAnalyzer(
                claude_client=self.claude_client,
                openai_client=self.openai_client,
                claude_model=args.claude_model,
                openai_model=args.openai_model,
                examples_df=examples_df
            )
        else:
            self.question_qc = None

        if args.mode in ['explanations', 'both']:
            self.explanation_qc = ExplanationQCAnalyzer(
                client=self.openai_client,
                model=args.openai_model
            )
        else:
            self.explanation_qc = None

    def load_input_data(self) -> pd.DataFrame:
        """Load and validate input data."""
        logger.info(f"Loading input data from {self.args.input}")
        df = pd.read_csv(self.args.input)

        if self.args.limit and self.args.limit > 0:
            df = df.head(self.args.limit)
            logger.info(f"Limited to first {len(df)} rows")

        logger.info(f"Loaded {len(df)} questions")
        return df

    async def run_question_qc(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Run question quality control concurrently."""
        if not self.question_qc:
            return []
            
        logger.info("\n" + "=" * 60)
        logger.info("RUNNING QUESTION QUALITY CONTROL")
        logger.info("=" * 60)

        questions = []
        for i, row in df.iterrows():
            choices = {
                'A': row.get('option_1') or row.get('choice_A', ''),
                'B': row.get('option_2') or row.get('choice_B', ''),
                'C': row.get('option_3') or row.get('choice_C', ''),
                'D': row.get('option_4') or row.get('choice_D', '')
            }

            structured_content = {
                'question': row.get('question', ''),
                'choices': choices,
                'correct_answer': row.get('correct_answer', ''),
                'CCSS': row.get('CCSS', ''),
                'CCSS_description': row.get('CCSS_description', ''),
                'DOK': row.get('DOK', '')
            }

            question_item = {
                'question_id': row.get('question_id') or row.get('item_id', f'Q{i+1}'),
                'question_type': row.get('question_type', 'MCQ'),
                'passage_text': row.get('passage', '') or row.get('stimulus', ''),
                'grade': row.get('grade'),
                'structured_content': structured_content
            }
            questions.append(question_item)

        results = await self.question_qc.analyze_batch(questions, self.args.concurrency)

        output_file = self.output_dir / f"question_qc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved question QC results to {output_file}")

        stats = calculate_pass_rate(results)
        logger.info(f"\nQuestion QC Summary:")
        logger.info(f"  Total: {stats['total']}")
        logger.info(f"  Passed: {stats['passed']} ({stats['pass_rate']:.1%})")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info(f"  Average Score: {stats['average_score']:.2f}")
        return results

    async def run_explanation_qc(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Run explanation quality control concurrently."""
        if not self.explanation_qc:
            return []

        logger.info("\n" + "=" * 60)
        logger.info("RUNNING EXPLANATION QUALITY CONTROL")
        logger.info("=" * 60)

        explanation_cols = [col for col in df.columns if 'explanation' in col.lower()]
        if not explanation_cols:
            logger.warning("No explanation columns found, skipping explanation QC")
            return []

        explanations = []
        for i, row in df.iterrows():
            question_id = row.get('question_id') or row.get('item_id', f'Q{i+1}')
            correct_answer_key = row.get('correct_answer', '')
            correct_option_text = row.get(f'option_{correct_answer_key}') or row.get(f'choice_{correct_answer_key}', '')

            for j in range(1, 5):
                option_key = f'option_{j}'
                explanation_key = f'{option_key}_explanation'
                if explanation_key in row and pd.notna(row[explanation_key]):
                    is_correct = (str(j) == str(correct_answer_key)) or (chr(64+j) == str(correct_answer_key))
                    explanation_item = {
                        'question_id': question_id,
                        'option_label': chr(64+j),
                        'explanation': row.get(explanation_key, ''),
                        'question': row.get('question', ''),
                        'passage': row.get('passage', '') or row.get('stimulus', ''),
                        'option_text': row.get(option_key, ''),
                        'correct_option_text': correct_option_text,
                        'is_correct': is_correct,
                        'grade': row.get('grade', 5)
                    }
                    explanations.append(explanation_item)

        if not explanations:
            logger.warning("No explanations found to evaluate")
            return []

        results = await self.explanation_qc.analyze_batch(explanations, self.args.concurrency)

        output_file = self.output_dir / f"explanation_qc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved explanation QC results to {output_file}")

        stats = calculate_pass_rate(results)
        logger.info(f"\nExplanation QC Summary:")
        logger.info(f"  Total: {stats['total']}")
        logger.info(f"  Passed: {stats['passed']} ({stats['pass_rate']:.1%})")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info(f"  Average Score: {stats['average_score']:.2f}")
        return results

    async def run(self):
        """Execute the complete pipeline."""
        logger.info("=" * 60)
        logger.info("STARTING QC PIPELINE")
        logger.info("=" * 60)
        logger.info(f"Mode: {self.args.mode}")
        logger.info(f"Input: {self.args.input}")
        logger.info(f"Output: {self.output_dir}")
        if self.args.examples:
            logger.info(f"Benchmarks: {self.args.examples}")

        df = self.load_input_data()

        tasks = []
        if self.args.mode in ['questions', 'both']:
            tasks.append(self.run_question_qc(df))
        if self.args.mode in ['explanations', 'both']:
            tasks.append(self.run_explanation_qc(df))

        results = await asyncio.gather(*tasks)
        
        question_results = results[0] if self.args.mode in ['questions', 'both'] else []
        explanation_results = results[1] if self.args.mode == 'both' else (results[0] if self.args.mode == 'explanations' else [])

        self._create_summary_report(question_results, explanation_results)

        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Results saved to {self.output_dir}")

    def _create_summary_report(self, question_results, explanation_results):
        """Create a consolidated summary report."""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'input_file': self.args.input,
            'mode': self.args.mode,
            'question_qc': calculate_pass_rate(question_results) if question_results else None,
            'explanation_qc': calculate_pass_rate(explanation_results) if explanation_results else None
        }

        summary_file = self.output_dir / "summary_report.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Saved summary report to {summary_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified Quality Control Pipeline for Reading Comprehension Assessment"
    )

    parser.add_argument("--input", required=True, help="Input CSV file")
    parser.add_argument("--output", required=True, help="Output directory for results")
    parser.add_argument("--mode", choices=['questions', 'explanations', 'both'], default='questions', help="Analysis mode")
    parser.add_argument("--examples", help="CSV file with benchmark questions for difficulty analysis")
    parser.add_argument("--concurrency", type=int, default=5, help="Max concurrent API calls")
    parser.add_argument("--limit", type=int, default=0, help="Process only first N questions (0 = all)")
    parser.add_argument("--claude-model", default="claude-sonnet-4-5", help="Claude model to use")
    parser.add_argument("--openai-model", default="gpt-5", help="OpenAI model to use")

    args = parser.parse_args()

    try:
        asyncio.run(QCPipeline(args).run())
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
