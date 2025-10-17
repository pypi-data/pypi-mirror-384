#!/usr/bin/env python3
"""
Delete questions with low scores from the database.
This script identifies questions with unacceptable evaluation scores and removes them.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict
import psycopg2
from psycopg2.extras import RealDictCursor

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import scoring functions
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
from interpreter import (
    parse_results_response_to_json,
    score_from_QA,
    score_from_EC,
    score_from_IP,
)


def get_db_connection():
    """Get PostgreSQL database connection"""
    postgres_uri = os.getenv("POSTGRES_URI")
    if not postgres_uri:
        raise RuntimeError("POSTGRES_URI environment variable not set")
    return psycopg2.connect(postgres_uri)


def score_edubench_result(evaluation_json: Dict[str, Any], question_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score EduBench evaluation JSON using the same logic as interpreter.py

    Returns:
        Dictionary with scores for QA, EC, IP tasks
    """
    scores = {
        'qa_score': None,
        'ec_score': None,
        'ip_score': None,
        'has_qa': False,
        'has_ec': False,
        'has_ip': False,
    }

    gold_answer = question_data.get('correct_answer', '')

    # Score QA task
    if 'QA' in evaluation_json:
        scores['has_qa'] = True
        qa_data = evaluation_json['QA']
        if 'response' in qa_data:
            fake_result = {
                'results': [{'response': qa_data['response']}],
                'input': {'answer': gold_answer}
            }
            try:
                parsed = parse_results_response_to_json(fake_result)
                if parsed and parsed.get("_source") != "unparseable":
                    score = score_from_QA(parsed, gold_answer)
                    scores['qa_score'] = score
            except Exception as e:
                pass

    # Score EC task
    if 'EC' in evaluation_json:
        scores['has_ec'] = True
        ec_data = evaluation_json['EC']
        if 'response' in ec_data:
            fake_result = {
                'results': [{'response': ec_data['response']}],
                'input': {'original_answer': gold_answer}
            }
            try:
                parsed = parse_results_response_to_json(fake_result)
                if parsed and parsed.get("_source") != "unparseable":
                    score = score_from_EC(parsed, gold_answer)
                    scores['ec_score'] = score
            except Exception as e:
                pass

    # Score IP task
    if 'IP' in evaluation_json:
        scores['has_ip'] = True
        ip_data = evaluation_json['IP']
        if 'response' in ip_data:
            fake_result = {
                'results': [{'response': ip_data['response']}],
                'input': {'answer': gold_answer}
            }
            try:
                parsed = parse_results_response_to_json(fake_result)
                if parsed and parsed.get("_source") != "unparseable":
                    score = score_from_IP(parsed, gold_answer)
                    scores['ip_score'] = score
            except Exception as e:
                pass

    return scores


def calculate_weighted_score(scores: Dict[str, Any]) -> Optional[float]:
    """
    Calculate weighted score using the same formula as interpreter_v2.py
    Weight QA and EC higher as answer accuracy and curriculum alignment are critical
    """
    weights = {'qa': 0.35, 'ec': 0.45, 'ip': 0.20}

    qa = scores.get('qa_score')
    ec = scores.get('ec_score')
    ip = scores.get('ip_score')

    # Calculate weighted score (same as interpreter_v2.py)
    valid_scores = []
    weighted_sum = 0

    if qa is not None:
        weighted_sum += qa * weights['qa']
        valid_scores.append('qa')
    if ec is not None:
        weighted_sum += ec * weights['ec']
        valid_scores.append('ec')
    if ip is not None:
        weighted_sum += ip * weights['ip']
        valid_scores.append('ip')

    if valid_scores:
        return weighted_sum
    return None


def fetch_all_evaluated_questions(conn):
    """Fetch all questions that have been evaluated with EduBench"""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        query = """
            SELECT
                id,
                question_text,
                question_text_arabic,
                correct_answer,
                answer_explanation,
                difficulty_level,
                grade_level,
                normalized_grade,
                subject_area,
                broad_topic,
                subtopic,
                scaffolding,
                language,
                evaluation_edubench,
                evaluation_scaffolding,
                extracted_by_model,
                created_at
            FROM uae_educational_questions_cleaned_duplicate
            WHERE evaluation_edubench IS NOT NULL
            ORDER BY created_at DESC
        """
        cur.execute(query)
        return cur.fetchall()


def analyze_scores(questions: List[Dict[str, Any]], threshold: float = 5.0):
    """
    Analyze all questions and categorize by score

    Args:
        questions: List of question dictionaries
        threshold: Minimum acceptable weighted score (0-10 scale)

    Returns:
        Dictionary with analysis results
    """
    low_score_questions = []
    acceptable_questions = []
    no_score_questions = []

    score_distribution = defaultdict(int)

    for question in questions:
        eval_json = question.get('evaluation_edubench')
        if eval_json:
            if isinstance(eval_json, str):
                try:
                    eval_json = json.loads(eval_json)
                except:
                    eval_json = None

            if eval_json:
                scores = score_edubench_result(eval_json, question)
                weighted_score = calculate_weighted_score(scores)

                if weighted_score is not None:
                    # Round to nearest 0.5 for distribution
                    bucket = round(weighted_score * 2) / 2
                    score_distribution[bucket] += 1

                    question_with_score = {
                        'id': question['id'],
                        'weighted_score': weighted_score,
                        'qa_score': scores['qa_score'],
                        'ec_score': scores['ec_score'],
                        'ip_score': scores['ip_score'],
                        'grade': question.get('normalized_grade'),
                        'subject': question.get('subject_area'),
                        'language': question.get('language'),
                        'model': question.get('extracted_by_model'),
                    }

                    if weighted_score < threshold:
                        low_score_questions.append(question_with_score)
                    else:
                        acceptable_questions.append(question_with_score)
                else:
                    no_score_questions.append(question['id'])
            else:
                no_score_questions.append(question['id'])
        else:
            no_score_questions.append(question['id'])

    return {
        'low_score': low_score_questions,
        'acceptable': acceptable_questions,
        'no_score': no_score_questions,
        'distribution': dict(sorted(score_distribution.items())),
        'threshold': threshold
    }


def print_analysis_report(analysis: Dict[str, Any]):
    """Print detailed analysis report"""
    print("\n" + "="*100)
    print("SCORE ANALYSIS REPORT")
    print("="*100)

    threshold = analysis['threshold']
    low_score = analysis['low_score']
    acceptable = analysis['acceptable']
    no_score = analysis['no_score']

    total_scored = len(low_score) + len(acceptable)
    total_all = total_scored + len(no_score)

    print(f"\nTotal questions with evaluation: {total_all}")
    print(f"  - Questions with scores: {total_scored}")
    print(f"  - Questions without parseable scores: {len(no_score)}")

    print(f"\nScore Distribution (threshold: {threshold}):")
    print(f"  - Below threshold (< {threshold}): {len(low_score)} ({len(low_score)/total_scored*100:.1f}%)")
    print(f"  - Acceptable (>= {threshold}): {len(acceptable)} ({len(acceptable)/total_scored*100:.1f}%)")

    print(f"\nScore Distribution by Bucket:")
    for bucket, count in analysis['distribution'].items():
        bar = "█" * int(count / 10)
        print(f"  {bucket:4.1f}: {count:4d} {bar}")

    # Break down low-scoring questions by grade and model
    if low_score:
        print(f"\nLow-Scoring Questions by Grade and Model:")
        grade_model_counts = defaultdict(lambda: defaultdict(int))
        for q in low_score:
            grade = q['grade'] or 'Unknown'
            model = q['model'] or 'Unknown'
            # Simplify model name
            if 'orchestrator' in str(model).lower():
                model = 'INCEPT'
            elif 'gpt' in str(model).lower() or 'openai' in str(model).lower():
                model = 'GPT'
            elif 'falcon' in str(model).lower():
                model = 'FALCON'
            grade_model_counts[grade][model] += 1

        print(f"\n{'Grade':<12} {'Model':<12} {'Count':>8}")
        print("-"*35)
        for grade in sorted(grade_model_counts.keys()):
            for model in sorted(grade_model_counts[grade].keys()):
                count = grade_model_counts[grade][model]
                print(f"{f'Grade {grade}':<12} {model:<12} {count:>8}")

    # Show sample low-scoring questions
    if low_score:
        print(f"\nSample Low-Scoring Questions (showing first 10):")
        print(f"{'ID':<10} {'Grade':<8} {'Subject':<20} {'Weighted':<10} {'QA':<8} {'EC':<8} {'IP':<8}")
        print("-"*85)
        for q in sorted(low_score, key=lambda x: x['weighted_score'])[:10]:
            qa = f"{q['qa_score']:.2f}" if q['qa_score'] is not None else "N/A"
            ec = f"{q['ec_score']:.2f}" if q['ec_score'] is not None else "N/A"
            ip = f"{q['ip_score']:.2f}" if q['ip_score'] is not None else "N/A"
            grade = f"{q['grade']}" if q['grade'] is not None else "N/A"
            subject = (q['subject'] or 'N/A')[:18]
            print(f"{q['id']:<10} {grade:<8} {subject:<20} {q['weighted_score']:<10.2f} {qa:<8} {ec:<8} {ip:<8}")

    print("\n" + "="*100)


def delete_low_score_questions(conn, question_ids: List[int], dry_run: bool = True):
    """
    Delete questions with low scores from the database

    Args:
        conn: Database connection
        question_ids: List of question IDs to delete
        dry_run: If True, only show what would be deleted
    """
    if not question_ids:
        print("No questions to delete.")
        return

    print(f"\n{'DRY RUN: ' if dry_run else ''}Deleting {len(question_ids)} questions...")

    if dry_run:
        print(f"IDs to delete: {question_ids[:20]}{'...' if len(question_ids) > 20 else ''}")
        return

    with conn.cursor() as cur:
        query = """
            DELETE FROM uae_educational_questions_cleaned_duplicate
            WHERE id = ANY(%s)
        """
        cur.execute(query, (question_ids,))
        deleted_count = cur.rowcount
        conn.commit()

        print(f"✓ Successfully deleted {deleted_count} questions")


def main():
    parser = argparse.ArgumentParser(description="Analyze and delete low-scoring questions")
    parser.add_argument(
        "--threshold",
        type=float,
        default=5.0,
        help="Minimum acceptable weighted score (0-10 scale). Questions below this will be deleted. Default: 5.0"
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Actually delete the questions (default is dry-run)"
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt (use with --delete)"
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export low-scoring questions to JSON file before deletion"
    )

    args = parser.parse_args()

    try:
        # Connect to database
        print("Connecting to database...")
        conn = get_db_connection()

        # Fetch all evaluated questions
        print("Fetching evaluated questions...")
        questions = fetch_all_evaluated_questions(conn)
        print(f"✓ Fetched {len(questions)} evaluated questions")

        # Analyze scores
        print(f"Analyzing scores with threshold: {args.threshold}...")
        analysis = analyze_scores(questions, threshold=args.threshold)

        # Print report
        print_analysis_report(analysis)

        # Export if requested
        if args.export:
            export_data = {
                'threshold': args.threshold,
                'total_low_score': len(analysis['low_score']),
                'total_acceptable': len(analysis['acceptable']),
                'low_score_questions': analysis['low_score'],
                'distribution': analysis['distribution']
            }
            with open(args.export, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"✓ Exported analysis to: {args.export}")

        # Delete low-scoring questions
        if analysis['low_score']:
            question_ids = [q['id'] for q in analysis['low_score']]

            if args.delete:
                if args.confirm:
                    delete_low_score_questions(conn, question_ids, dry_run=False)
                else:
                    response = input(f"\n⚠️  Are you sure you want to delete {len(question_ids)} questions? (yes/no): ")
                    if response.lower() == 'yes':
                        delete_low_score_questions(conn, question_ids, dry_run=False)
                    else:
                        print("Deletion cancelled.")
            else:
                print(f"\n💡 This is a DRY RUN. Use --delete to actually delete questions.")
                delete_low_score_questions(conn, question_ids, dry_run=True)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if 'conn' in locals():
            conn.close()
            print("✓ Database connection closed")


if __name__ == "__main__":
    main()
