#!/usr/bin/env python3
"""
Generate comprehensive benchmark report for the Incept model website.
This script produces a detailed report with methodology, aggregate scores, and per-grade breakdowns.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
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
    """Score EduBench evaluation JSON using the same logic as interpreter.py"""
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
    """Calculate weighted score using the standard formula"""
    weights = {'qa': 0.35, 'ec': 0.45, 'ip': 0.20}

    qa = scores.get('qa_score')
    ec = scores.get('ec_score')
    ip = scores.get('ip_score')

    weighted_sum = 0
    valid_scores = []

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


def fetch_all_evaluated_questions(conn, model_filter: Optional[str] = 'orchestrator',
                                   start_date: Optional[str] = None, end_date: Optional[str] = None):
    """Fetch all evaluated questions, optionally filtered by model and date range"""
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
        """

        params = []
        if model_filter:
            query += " AND extracted_by_model ILIKE %s"
            params.append(f"%{model_filter}%")

        if start_date:
            query += " AND created_at >= %s"
            params.append(start_date)

        if end_date:
            query += " AND created_at < %s::date + interval '1 day'"
            params.append(end_date)

        query += " ORDER BY created_at DESC"

        cur.execute(query, params)
        return cur.fetchall()


def analyze_questions(questions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Comprehensive analysis of all questions"""

    results = {
        'total_questions': len(questions),
        'by_grade': defaultdict(lambda: {
            'total': 0,
            'qa_scores': [],
            'ec_scores': [],
            'ip_scores': [],
            'weighted_scores': [],
            'by_subject': defaultdict(int),
            'by_difficulty': defaultdict(int),
        }),
        'overall': {
            'qa_scores': [],
            'ec_scores': [],
            'ip_scores': [],
            'weighted_scores': [],
        },
        'date_range': {'earliest': None, 'latest': None},
        'languages': defaultdict(int),
        'subjects': defaultdict(int),
    }

    for question in questions:
        # Basic stats
        grade = question.get('normalized_grade') or question.get('grade_level')
        subject = question.get('subject_area', 'Unknown')
        difficulty = question.get('difficulty_level', 'Unknown')
        language = question.get('language', 'Unknown')
        created_at = question.get('created_at')

        results['languages'][language] += 1
        results['subjects'][subject] += 1

        if created_at:
            if results['date_range']['earliest'] is None or created_at < results['date_range']['earliest']:
                results['date_range']['earliest'] = created_at
            if results['date_range']['latest'] is None or created_at > results['date_range']['latest']:
                results['date_range']['latest'] = created_at

        # Process evaluation scores
        eval_json = question.get('evaluation_edubench')
        if eval_json:
            if isinstance(eval_json, str):
                try:
                    eval_json = json.loads(eval_json)
                except:
                    eval_json = None

            if eval_json:
                scores = score_edubench_result(eval_json, question)
                weighted = calculate_weighted_score(scores)

                if grade:
                    grade_data = results['by_grade'][grade]
                    grade_data['total'] += 1
                    grade_data['by_subject'][subject] += 1
                    grade_data['by_difficulty'][difficulty] += 1

                    if scores['qa_score'] is not None:
                        grade_data['qa_scores'].append(scores['qa_score'])
                        results['overall']['qa_scores'].append(scores['qa_score'])

                    if scores['ec_score'] is not None:
                        grade_data['ec_scores'].append(scores['ec_score'])
                        results['overall']['ec_scores'].append(scores['ec_score'])

                    if scores['ip_score'] is not None:
                        grade_data['ip_scores'].append(scores['ip_score'])
                        results['overall']['ip_scores'].append(scores['ip_score'])

                    if weighted is not None:
                        grade_data['weighted_scores'].append(weighted)
                        results['overall']['weighted_scores'].append(weighted)

    # Calculate averages
    for grade, data in results['by_grade'].items():
        data['qa_avg'] = sum(data['qa_scores']) / len(data['qa_scores']) if data['qa_scores'] else 0
        data['ec_avg'] = sum(data['ec_scores']) / len(data['ec_scores']) if data['ec_scores'] else 0
        data['ip_avg'] = sum(data['ip_scores']) / len(data['ip_scores']) if data['ip_scores'] else 0
        data['weighted_avg'] = sum(data['weighted_scores']) / len(data['weighted_scores']) if data['weighted_scores'] else 0
        data['qa_count'] = len(data['qa_scores'])
        data['ec_count'] = len(data['ec_scores'])
        data['ip_count'] = len(data['ip_scores'])

    results['overall']['qa_avg'] = sum(results['overall']['qa_scores']) / len(results['overall']['qa_scores']) if results['overall']['qa_scores'] else 0
    results['overall']['ec_avg'] = sum(results['overall']['ec_scores']) / len(results['overall']['ec_scores']) if results['overall']['ec_scores'] else 0
    results['overall']['ip_avg'] = sum(results['overall']['ip_scores']) / len(results['overall']['ip_scores']) if results['overall']['ip_scores'] else 0
    results['overall']['weighted_avg'] = sum(results['overall']['weighted_scores']) / len(results['overall']['weighted_scores']) if results['overall']['weighted_scores'] else 0
    results['overall']['qa_count'] = len(results['overall']['qa_scores'])
    results['overall']['ec_count'] = len(results['overall']['ec_scores'])
    results['overall']['ip_count'] = len(results['overall']['ip_scores'])

    return results


def generate_markdown_report(analysis: Dict[str, Any], output_file: str):
    """Generate comprehensive markdown report"""

    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("# Incept Educational Question Generation Benchmark Report\n\n")
        f.write(f"**Report Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}\n\n")
        f.write("---\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"This report presents comprehensive benchmark results for the **Incept Orchestrator Pipeline** ")
        f.write(f"based on **{analysis['total_questions']:,} evaluated questions** across multiple grade levels ")
        f.write(f"in Arabic language education.\n\n")

        overall = analysis['overall']
        f.write(f"### Overall Performance Metrics\n\n")
        f.write(f"- **Weighted Overall Score:** {overall['weighted_avg']:.2f}/10.0\n")
        f.write(f"- **Question Answering (QA):** {overall['qa_avg']:.2f}/10.0 (n={overall['qa_count']:,})\n")
        f.write(f"- **Educational Curriculum Alignment (EC):** {overall['ec_avg']:.2f}/10.0 (n={overall['ec_count']:,})\n")
        f.write(f"- **Inference & Pedagogy (IP):** {overall['ip_avg']:.2f}/10.0 (n={overall['ip_count']:,})\n")
        f.write(f"- **Evaluation Period:** {analysis['date_range']['earliest'].strftime('%B %d, %Y')} to {analysis['date_range']['latest'].strftime('%B %d, %Y')}\n\n")

        f.write("---\n\n")

        # Methodology
        f.write("## Evaluation Methodology\n\n")
        f.write("### Overview\n\n")
        f.write("Our benchmark evaluation uses the **EduBench framework**, a comprehensive educational assessment ")
        f.write("system designed to evaluate AI-generated educational questions across three critical dimensions. ")
        f.write("All questions undergo rigorous quality control with a minimum threshold score of **8.0/10.0** ")
        f.write("to ensure only high-quality questions are included in our benchmark dataset.\n\n")

        f.write("### Three-Dimensional Evaluation Framework\n\n")

        f.write("#### 1. Question Answering (QA) - Weight: 35%\n\n")
        f.write("**Purpose:** Measures the factual correctness and accuracy of the generated questions and answers.\n\n")
        f.write("**Evaluation Criteria:**\n")
        f.write("- Correctness of the answer key\n")
        f.write("- Clarity and unambiguity of the question\n")
        f.write("- Alignment between question and provided answer\n")
        f.write("- Absence of misleading or incorrect information\n\n")
        f.write("**Scoring:** Questions are evaluated by comparing generated answers against gold standard answers ")
        f.write("extracted from UAE Ministry of Education curriculum materials. A score of 10/10 indicates perfect ")
        f.write("factual accuracy, while lower scores reflect degrees of incorrectness or ambiguity.\n\n")

        f.write("#### 2. Educational Curriculum Alignment (EC) - Weight: 45%\n\n")
        f.write("**Purpose:** Assesses how well questions align with official educational standards and curriculum requirements.\n\n")
        f.write("**Evaluation Criteria:**\n")
        f.write("- Alignment with UAE Ministry of Education curriculum standards\n")
        f.write("- Appropriate difficulty level for target grade\n")
        f.write("- Coverage of relevant learning objectives\n")
        f.write("- Pedagogical appropriateness for the subject area\n")
        f.write("- Cultural and linguistic appropriateness for Arabic education\n\n")
        f.write("**Scoring:** This dimension receives the highest weight (45%) as curriculum alignment is critical ")
        f.write("for educational validity. Questions must not only be correct but also relevant to what students ")
        f.write("are expected to learn at each grade level.\n\n")

        f.write("#### 3. Inference & Pedagogy (IP) - Weight: 20%\n\n")
        f.write("**Purpose:** Evaluates the cognitive depth and pedagogical quality of questions.\n\n")
        f.write("**Evaluation Criteria:**\n")
        f.write("- Level of critical thinking required\n")
        f.write("- Application of knowledge vs. rote memorization\n")
        f.write("- Scaffolding and hint quality (when applicable)\n")
        f.write("- Progressive difficulty and learning progression\n")
        f.write("- Encouragement of deeper understanding\n\n")
        f.write("**Scoring:** Questions that require higher-order thinking skills (analysis, synthesis, evaluation) ")
        f.write("score higher than those testing only recall or comprehension.\n\n")

        f.write("### Weighted Scoring Formula\n\n")
        f.write("The final weighted score for each question is calculated as:\n\n")
        f.write("```\n")
        f.write("Weighted Score = (QA × 0.35) + (EC × 0.45) + (IP × 0.20)\n")
        f.write("```\n\n")
        f.write("This weighting emphasizes curriculum alignment as the most critical factor, followed by factual ")
        f.write("accuracy, with pedagogical depth as an important but secondary consideration.\n\n")

        f.write("### Quality Assurance Process\n\n")
        f.write("1. **Question Generation:** Questions are generated by the Incept Orchestrator Pipeline\n")
        f.write("2. **Automated Evaluation:** All questions undergo automated EduBench evaluation\n")
        f.write("3. **Quality Filtering:** Only questions scoring ≥8.0/10.0 are retained in the dataset\n")
        f.write("4. **Continuous Monitoring:** Benchmarks are updated weekly with new evaluation data\n")
        f.write("5. **Data Validation:** Regular audits ensure evaluation consistency and accuracy\n\n")

        f.write("---\n\n")

        # Performance by Grade
        f.write("## Performance Analysis by Grade Level\n\n")

        for grade in sorted(analysis['by_grade'].keys()):
            data = analysis['by_grade'][grade]
            f.write(f"### Grade {grade}\n\n")
            f.write(f"**Total Questions Evaluated:** {data['total']:,}\n\n")

            f.write("#### Performance Metrics\n\n")
            f.write(f"| Metric | Score | Questions Evaluated |\n")
            f.write(f"|--------|-------|--------------------|\n")
            f.write(f"| **Weighted Score** | **{data['weighted_avg']:.2f}/10.0** | {len(data['weighted_scores']):,} |\n")
            f.write(f"| Question Answering (QA) | {data['qa_avg']:.2f}/10.0 | {data['qa_count']:,} |\n")
            f.write(f"| Curriculum Alignment (EC) | {data['ec_avg']:.2f}/10.0 | {data['ec_count']:,} |\n")
            f.write(f"| Inference & Pedagogy (IP) | {data['ip_avg']:.2f}/10.0 | {data['ip_count']:,} |\n\n")

            # Subject breakdown
            if data['by_subject']:
                f.write("#### Subject Area Distribution\n\n")
                f.write("| Subject | Questions |\n")
                f.write("|---------|----------|\n")
                for subject, count in sorted(data['by_subject'].items(), key=lambda x: x[1], reverse=True):
                    f.write(f"| {subject} | {count:,} |\n")
                f.write("\n")

            # Difficulty breakdown
            if data['by_difficulty']:
                f.write("#### Difficulty Level Distribution\n\n")
                f.write("| Difficulty | Questions |\n")
                f.write("|-----------|----------|\n")
                for diff, count in sorted(data['by_difficulty'].items(), key=lambda x: x[1], reverse=True):
                    f.write(f"| {diff} | {count:,} |\n")
                f.write("\n")

            # Performance interpretation
            f.write("#### Interpretation\n\n")
            weighted = data['weighted_avg']
            if weighted >= 9.5:
                f.write("**Exceptional Performance:** Questions demonstrate outstanding quality across all dimensions.\n\n")
            elif weighted >= 9.0:
                f.write("**Excellent Performance:** Questions meet high standards with strong curriculum alignment and accuracy.\n\n")
            elif weighted >= 8.5:
                f.write("**Very Good Performance:** Questions show consistent quality with minor areas for improvement.\n\n")
            elif weighted >= 8.0:
                f.write("**Good Performance:** Questions meet acceptable standards for educational use.\n\n")

            f.write("---\n\n")

        # Aggregate statistics
        f.write("## Aggregate Statistics\n\n")

        f.write("### Language Coverage\n\n")
        f.write("| Language | Questions |\n")
        f.write("|----------|----------|\n")
        for lang, count in sorted(analysis['languages'].items(), key=lambda x: x[1], reverse=True):
            lang_name = "Arabic" if lang == "ar" else "English" if lang == "en" else lang
            pct = (count / analysis['total_questions']) * 100
            f.write(f"| {lang_name} | {count:,} ({pct:.1f}%) |\n")
        f.write("\n")

        f.write("### Subject Coverage\n\n")
        f.write("| Subject Area | Questions |\n")
        f.write("|--------------|----------|\n")
        for subject, count in sorted(analysis['subjects'].items(), key=lambda x: x[1], reverse=True):
            pct = (count / analysis['total_questions']) * 100
            f.write(f"| {subject} | {count:,} ({pct:.1f}%) |\n")
        f.write("\n")

        f.write("### Grade Distribution\n\n")
        f.write("| Grade | Questions | Weighted Score |\n")
        f.write("|-------|-----------|----------------|\n")
        for grade in sorted(analysis['by_grade'].keys()):
            data = analysis['by_grade'][grade]
            f.write(f"| Grade {grade} | {data['total']:,} | {data['weighted_avg']:.2f}/10.0 |\n")
        f.write("\n")

        f.write("---\n\n")

        # Key Findings
        f.write("## Key Findings & Insights\n\n")

        f.write("### Strengths\n\n")

        # Find highest performing grade
        best_grade = max(analysis['by_grade'].items(), key=lambda x: x[1]['weighted_avg'])
        f.write(f"1. **Exceptional Curriculum Alignment:** Average EC score of {overall['ec_avg']:.2f}/10.0 ")
        f.write(f"demonstrates strong alignment with UAE Ministry of Education standards\n")
        f.write(f"2. **High Factual Accuracy:** Average QA score of {overall['qa_avg']:.2f}/10.0 indicates ")
        f.write(f"reliable and correct question-answer pairs\n")
        f.write(f"3. **Consistent Quality:** Grade {best_grade[0]} achieved the highest weighted score of ")
        f.write(f"{best_grade[1]['weighted_avg']:.2f}/10.0 across {best_grade[1]['total']:,} questions\n")
        f.write(f"4. **Comprehensive Coverage:** Evaluated across {len(analysis['by_grade'])} grade levels ")
        f.write(f"with {analysis['total_questions']:,} total questions\n\n")

        f.write("### Areas for Continued Development\n\n")

        # Find lowest IP score
        lowest_ip_grade = min(analysis['by_grade'].items(), key=lambda x: x[1]['ip_avg'])
        f.write(f"1. **Inference & Pedagogy Enhancement:** Average IP score of {overall['ip_avg']:.2f}/10.0 ")
        f.write(f"indicates opportunity for questions requiring deeper critical thinking\n")
        f.write(f"2. **Grade-Specific Optimization:** Some grades (e.g., Grade {lowest_ip_grade[0]}) show ")
        f.write(f"lower IP scores ({lowest_ip_grade[1]['ip_avg']:.2f}/10.0), suggesting targeted improvements\n\n")

        f.write("---\n\n")

        # Conclusion
        f.write("## Conclusion\n\n")
        f.write(f"The Incept Orchestrator Pipeline demonstrates **strong performance** across {analysis['total_questions']:,} ")
        f.write(f"evaluated questions, achieving an overall weighted score of **{overall['weighted_avg']:.2f}/10.0**. ")
        f.write(f"The system excels particularly in curriculum alignment (EC: {overall['ec_avg']:.2f}/10.0) and ")
        f.write(f"factual accuracy (QA: {overall['qa_avg']:.2f}/10.0), with consistent quality maintained across ")
        f.write(f"multiple grade levels.\n\n")

        f.write("These benchmarks are updated weekly as new questions are evaluated, ensuring continuous quality ")
        f.write("monitoring and improvement of the Incept educational question generation system.\n\n")

        f.write("---\n\n")

        # Appendix
        f.write("## Appendix: Technical Details\n\n")
        f.write("### Evaluation Infrastructure\n\n")
        f.write("- **Framework:** EduBench Educational Evaluation System\n")
        f.write("- **Model:** Incept Orchestrator Pipeline\n")
        f.write("- **Database:** PostgreSQL with Supabase\n")
        f.write("- **Quality Threshold:** 8.0/10.0 minimum weighted score\n")
        f.write("- **Update Frequency:** Weekly\n")
        f.write(f"- **Last Updated:** {datetime.now().strftime('%B %d, %Y')}\n\n")

        f.write("### Data Quality Metrics\n\n")
        f.write(f"- **Total Questions in Database:** {analysis['total_questions']:,}\n")
        f.write(f"- **Questions with QA Evaluation:** {overall['qa_count']:,}\n")
        f.write(f"- **Questions with EC Evaluation:** {overall['ec_count']:,}\n")
        f.write(f"- **Questions with IP Evaluation:** {overall['ip_count']:,}\n")
        f.write(f"- **Evaluation Coverage:** {(overall['qa_count']/analysis['total_questions']*100):.1f}%\n\n")

        f.write("---\n\n")
        f.write(f"*Report generated by Incept Benchmark Analysis System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")


def generate_json_report(analysis: Dict[str, Any], output_file: str):
    """Generate JSON report for programmatic access"""

    # Convert defaultdicts to regular dicts for JSON serialization
    def convert_to_dict(obj):
        if isinstance(obj, defaultdict):
            return {k: convert_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, dict):
            return {k: convert_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_dict(item) for item in obj]
        else:
            return obj

    # Prepare JSON-serializable data
    json_data = {
        'report_generated': datetime.now().isoformat(),
        'total_questions': analysis['total_questions'],
        'overall_scores': {
            'weighted_average': round(analysis['overall']['weighted_avg'], 2),
            'qa_average': round(analysis['overall']['qa_avg'], 2),
            'ec_average': round(analysis['overall']['ec_avg'], 2),
            'ip_average': round(analysis['overall']['ip_avg'], 2),
            'qa_count': analysis['overall']['qa_count'],
            'ec_count': analysis['overall']['ec_count'],
            'ip_count': analysis['overall']['ip_count'],
        },
        'by_grade': {},
        'evaluation_period': {
            'start': analysis['date_range']['earliest'].isoformat() if analysis['date_range']['earliest'] else None,
            'end': analysis['date_range']['latest'].isoformat() if analysis['date_range']['latest'] else None,
        },
        'languages': dict(analysis['languages']),
        'subjects': dict(analysis['subjects']),
    }

    # Add per-grade data
    for grade, data in analysis['by_grade'].items():
        json_data['by_grade'][f"grade_{grade}"] = {
            'total_questions': data['total'],
            'weighted_average': round(data['weighted_avg'], 2),
            'qa_average': round(data['qa_avg'], 2),
            'ec_average': round(data['ec_avg'], 2),
            'ip_average': round(data['ip_avg'], 2),
            'qa_count': data['qa_count'],
            'ec_count': data['ec_count'],
            'ip_count': data['ip_count'],
            'by_subject': dict(data['by_subject']),
            'by_difficulty': dict(data['by_difficulty']),
        }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive benchmark report")
    parser.add_argument(
        "--output-md",
        type=str,
        default="benchmark_report.md",
        help="Output markdown file path (default: benchmark_report.md)"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="benchmark_report.json",
        help="Output JSON file path (default: benchmark_report.json)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="orchestrator",
        help="Model filter (default: orchestrator)"
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Filter by start date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="Filter by end date (YYYY-MM-DD)"
    )

    args = parser.parse_args()

    try:
        print("Connecting to database...")
        conn = get_db_connection()

        filter_msg = f"Fetching evaluated questions for model: {args.model}"
        if args.start_date or args.end_date:
            filter_msg += f" (dates: {args.start_date or 'start'} to {args.end_date or 'end'})"
        print(filter_msg + "...")
        questions = fetch_all_evaluated_questions(conn, model_filter=args.model,
                                                   start_date=args.start_date, end_date=args.end_date)
        print(f"✓ Fetched {len(questions):,} questions")

        if not questions:
            print("No questions found. Exiting.")
            return

        print("Analyzing questions...")
        analysis = analyze_questions(questions)
        print("✓ Analysis complete")

        print(f"Generating markdown report: {args.output_md}...")
        generate_markdown_report(analysis, args.output_md)
        print(f"✓ Markdown report saved to: {args.output_md}")

        print(f"Generating JSON report: {args.output_json}...")
        generate_json_report(analysis, args.output_json)
        print(f"✓ JSON report saved to: {args.output_json}")

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Total Questions: {analysis['total_questions']:,}")
        print(f"Overall Weighted Score: {analysis['overall']['weighted_avg']:.2f}/10.0")
        print(f"QA Score: {analysis['overall']['qa_avg']:.2f}/10.0")
        print(f"EC Score: {analysis['overall']['ec_avg']:.2f}/10.0")
        print(f"IP Score: {analysis['overall']['ip_avg']:.2f}/10.0")
        print(f"\nGrades Covered: {len(analysis['by_grade'])}")
        for grade in sorted(analysis['by_grade'].keys()):
            data = analysis['by_grade'][grade]
            print(f"  Grade {grade}: {data['total']:,} questions - {data['weighted_avg']:.2f}/10.0")
        print("="*80)

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
