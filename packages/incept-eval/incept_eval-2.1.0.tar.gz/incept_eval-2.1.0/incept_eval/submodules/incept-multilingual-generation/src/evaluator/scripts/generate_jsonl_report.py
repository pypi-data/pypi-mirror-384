#!/usr/bin/env python3
"""
Generate comprehensive report from JSONL evaluation results.
This script analyzes a JSONL file from EduBench evaluations and produces detailed reports.
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))
from interpreter import (
    parse_results_response_to_json,
    score_from_QA,
    score_from_EC,
    score_from_IP,
)


def analyze_jsonl(file_path: str) -> Dict[str, Any]:
    """Analyze JSONL evaluation file and return comprehensive statistics"""

    results = {
        'total_questions': 0,
        'qa_scores': [],
        'ec_scores': [],
        'ip_scores': [],
        'unparsed': {'QA': 0, 'EC': 0, 'IP': 0},
        'by_grade': defaultdict(lambda: {
            'total': 0,
            'qa_scores': [],
            'ec_scores': [],
            'ip_scores': [],
        }),
        'by_subject': defaultdict(int),
        'questions': []
    }

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue

            try:
                data = json.loads(line)
                results['total_questions'] += 1

                # Extract metadata
                grade = data.get('input', {}).get('grade')
                subject = data.get('input', {}).get('subject', 'Unknown')
                question_text = data.get('input', {}).get('question', '')
                gold_answer = data.get('input', {}).get('answer', '')

                results['by_subject'][subject] += 1

                question_results = {
                    'line': line_num,
                    'grade': grade,
                    'subject': subject,
                    'question': question_text[:100],
                    'qa_score': None,
                    'ec_score': None,
                    'ip_score': None,
                }

                # Handle different JSONL structures - check if task_type field exists
                task_type = data.get('task_type', '')

                # Score based on task type
                if task_type == 'QA' and 'results' in data and len(data['results']) > 0:
                    qa_result = {'results': [data['results'][0]], 'input': {'answer': gold_answer}}
                    try:
                        parsed = parse_results_response_to_json(qa_result)
                        if parsed and parsed.get("_source") != "unparseable":
                            score = score_from_QA(parsed, gold_answer)
                            results['qa_scores'].append(score)
                            question_results['qa_score'] = score
                            if grade:
                                results['by_grade'][grade]['qa_scores'].append(score)
                        else:
                            results['unparsed']['QA'] += 1
                    except Exception as e:
                        results['unparsed']['QA'] += 1

                elif task_type == 'EC' and 'results' in data and len(data['results']) > 0:
                    ec_result = {'results': [data['results'][0]], 'input': {'original_answer': gold_answer}}
                    try:
                        parsed = parse_results_response_to_json(ec_result)
                        if parsed and parsed.get("_source") != "unparseable":
                            score = score_from_EC(parsed, gold_answer)
                            results['ec_scores'].append(score)
                            question_results['ec_score'] = score
                            if grade:
                                results['by_grade'][grade]['ec_scores'].append(score)
                        else:
                            results['unparsed']['EC'] += 1
                    except Exception as e:
                        results['unparsed']['EC'] += 1

                elif task_type == 'IP' and 'results' in data and len(data['results']) > 0:
                    ip_result = {'results': [data['results'][0]], 'input': {'answer': gold_answer}}
                    try:
                        parsed = parse_results_response_to_json(ip_result)
                        if parsed and parsed.get("_source") != "unparseable":
                            score = score_from_IP(parsed, gold_answer)
                            results['ip_scores'].append(score)
                            question_results['ip_score'] = score
                            if grade:
                                results['by_grade'][grade]['ip_scores'].append(score)
                        else:
                            results['unparsed']['IP'] += 1
                    except Exception as e:
                        results['unparsed']['IP'] += 1

                if grade:
                    results['by_grade'][grade]['total'] += 1

                results['questions'].append(question_results)

            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse line {line_num}: {e}")
                continue

    # Filter out None values and calculate averages
    results['qa_scores'] = [s for s in results['qa_scores'] if s is not None]
    results['ec_scores'] = [s for s in results['ec_scores'] if s is not None]
    results['ip_scores'] = [s for s in results['ip_scores'] if s is not None]

    results['qa_avg'] = sum(results['qa_scores']) / len(results['qa_scores']) if results['qa_scores'] else 0
    results['ec_avg'] = sum(results['ec_scores']) / len(results['ec_scores']) if results['ec_scores'] else 0
    results['ip_avg'] = sum(results['ip_scores']) / len(results['ip_scores']) if results['ip_scores'] else 0

    # Calculate weighted score using proper formula
    weights = {'qa': 0.35, 'ec': 0.45, 'ip': 0.20}
    results['weighted_avg'] = (
        results['qa_avg'] * weights['qa'] +
        results['ec_avg'] * weights['ec'] +
        results['ip_avg'] * weights['ip']
    )

    # Calculate per-grade averages
    for grade, data in results['by_grade'].items():
        # Filter out None values
        data['qa_scores'] = [s for s in data['qa_scores'] if s is not None]
        data['ec_scores'] = [s for s in data['ec_scores'] if s is not None]
        data['ip_scores'] = [s for s in data['ip_scores'] if s is not None]

        data['qa_avg'] = sum(data['qa_scores']) / len(data['qa_scores']) if data['qa_scores'] else 0
        data['ec_avg'] = sum(data['ec_scores']) / len(data['ec_scores']) if data['ec_scores'] else 0
        data['ip_avg'] = sum(data['ip_scores']) / len(data['ip_scores']) if data['ip_scores'] else 0
        data['weighted_avg'] = (
            data['qa_avg'] * weights['qa'] +
            data['ec_avg'] * weights['ec'] +
            data['ip_avg'] * weights['ip']
        )

    return results


def generate_markdown_report(analysis: Dict[str, Any], output_file: str, source_file: str):
    """Generate comprehensive markdown report"""

    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("# Incept Evaluation Run Report\n\n")
        f.write(f"**Report Generated:** {datetime.now().strftime('%B %d, %Y at %H:%M UTC')}\n\n")
        f.write(f"**Source File:** `{Path(source_file).name}`\n\n")
        f.write("---\n\n")

        # Executive Summary
        f.write("## Executive Summary\n\n")
        f.write(f"This evaluation run assessed **{analysis['total_questions']:,} questions** ")
        f.write(f"using the EduBench framework across three critical dimensions: ")
        f.write(f"Question Answering (QA), Educational Curriculum Alignment (EC), and Inference & Pedagogy (IP).\n\n")

        f.write("### Overall Performance Metrics\n\n")
        f.write(f"| Metric | Score | Questions Evaluated |\n")
        f.write(f"|--------|-------|--------------------|\n")
        f.write(f"| **Weighted Score** | **{analysis['weighted_avg']:.2f}/10.0** | {analysis['total_questions']:,} |\n")
        f.write(f"| Question Answering (QA) | {analysis['qa_avg']:.2f}/10.0 | {len(analysis['qa_scores']):,} |\n")
        f.write(f"| Curriculum Alignment (EC) | {analysis['ec_avg']:.2f}/10.0 | {len(analysis['ec_scores']):,} |\n")
        f.write(f"| Inference & Pedagogy (IP) | {analysis['ip_avg']:.2f}/10.0 | {len(analysis['ip_scores']):,} |\n\n")

        # Quality assessment
        weighted = analysis['weighted_avg']
        if weighted >= 8.0:
            f.write(f"✅ **Quality Status:** PASS - This evaluation run meets the quality threshold of 8.0/10.0\n\n")
        else:
            f.write(f"⚠️ **Quality Status:** BELOW THRESHOLD - Questions scoring below 8.0/10.0 are filtered from the dataset\n\n")

        f.write("---\n\n")

        # Detailed Breakdown
        f.write("## Detailed Score Breakdown\n\n")

        f.write("### Scoring Formula\n\n")
        f.write("The weighted score is calculated using the following formula:\n\n")
        f.write("```\n")
        f.write("Weighted Score = (QA × 0.35) + (EC × 0.45) + (IP × 0.20)\n")
        f.write("```\n\n")
        f.write("This weighting emphasizes curriculum alignment (45%) as the most critical factor, ")
        f.write("followed by factual accuracy (35%), with pedagogical depth (20%) as an important secondary consideration.\n\n")

        f.write("### Task Performance\n\n")

        f.write(f"#### Question Answering (QA) - {analysis['qa_avg']:.2f}/10.0\n\n")
        f.write(f"- **Questions Evaluated:** {len(analysis['qa_scores']):,}\n")
        f.write(f"- **Unparsed:** {analysis['unparsed']['QA']}\n")
        f.write(f"- **Contribution to Weighted Score:** {analysis['qa_avg'] * 0.35:.2f} points\n\n")
        if analysis['qa_avg'] >= 9.0:
            f.write("**Assessment:** Excellent factual accuracy. Questions demonstrate strong correctness.\n\n")
        elif analysis['qa_avg'] >= 8.0:
            f.write("**Assessment:** Good factual accuracy with minor areas for improvement.\n\n")
        else:
            f.write("**Assessment:** Factual accuracy needs improvement.\n\n")

        f.write(f"#### Educational Curriculum Alignment (EC) - {analysis['ec_avg']:.2f}/10.0\n\n")
        f.write(f"- **Questions Evaluated:** {len(analysis['ec_scores']):,}\n")
        f.write(f"- **Unparsed:** {analysis['unparsed']['EC']}\n")
        f.write(f"- **Contribution to Weighted Score:** {analysis['ec_avg'] * 0.45:.2f} points\n\n")
        if analysis['ec_avg'] >= 9.5:
            f.write("**Assessment:** Outstanding curriculum alignment. Questions perfectly match educational standards.\n\n")
        elif analysis['ec_avg'] >= 9.0:
            f.write("**Assessment:** Excellent curriculum alignment with educational standards.\n\n")
        elif analysis['ec_avg'] >= 8.0:
            f.write("**Assessment:** Good curriculum alignment with room for improvement.\n\n")
        else:
            f.write("**Assessment:** Curriculum alignment needs significant improvement.\n\n")

        f.write(f"#### Inference & Pedagogy (IP) - {analysis['ip_avg']:.2f}/10.0\n\n")
        f.write(f"- **Questions Evaluated:** {len(analysis['ip_scores']):,}\n")
        f.write(f"- **Unparsed:** {analysis['unparsed']['IP']}\n")
        f.write(f"- **Contribution to Weighted Score:** {analysis['ip_avg'] * 0.20:.2f} points\n\n")
        if analysis['ip_avg'] >= 7.0:
            f.write("**Assessment:** Strong pedagogical quality with good critical thinking depth.\n\n")
        elif analysis['ip_avg'] >= 5.0:
            f.write("**Assessment:** Moderate pedagogical quality. Questions could benefit from deeper critical thinking elements.\n\n")
        else:
            f.write("**Assessment:** Pedagogical quality needs improvement. Focus on higher-order thinking skills.\n\n")

        f.write("---\n\n")

        # Performance by Grade
        if analysis['by_grade']:
            f.write("## Performance by Grade Level\n\n")
            f.write("| Grade | Questions | QA Score | EC Score | IP Score | Weighted Score |\n")
            f.write("|-------|-----------|----------|----------|----------|----------------|\n")
            for grade in sorted(analysis['by_grade'].keys()):
                data = analysis['by_grade'][grade]
                f.write(f"| Grade {grade} | {data['total']:,} | {data['qa_avg']:.2f} | ")
                f.write(f"{data['ec_avg']:.2f} | {data['ip_avg']:.2f} | **{data['weighted_avg']:.2f}** |\n")
            f.write("\n")

        # Subject breakdown
        if analysis['by_subject']:
            f.write("## Subject Distribution\n\n")
            f.write("| Subject | Questions |\n")
            f.write("|---------|----------|\n")
            for subject, count in sorted(analysis['by_subject'].items(), key=lambda x: x[1], reverse=True):
                pct = (count / analysis['total_questions']) * 100
                f.write(f"| {subject} | {count:,} ({pct:.1f}%) |\n")
            f.write("\n")

        f.write("---\n\n")

        # Key Insights
        f.write("## Key Insights\n\n")

        f.write("### Strengths\n\n")
        if analysis['ec_avg'] >= 9.0:
            f.write(f"- ✅ **Exceptional Curriculum Alignment:** EC score of {analysis['ec_avg']:.2f}/10.0 demonstrates strong alignment with educational standards\n")
        if analysis['qa_avg'] >= 8.5:
            f.write(f"- ✅ **High Factual Accuracy:** QA score of {analysis['qa_avg']:.2f}/10.0 indicates reliable question-answer pairs\n")
        if analysis['weighted_avg'] >= 8.0:
            f.write(f"- ✅ **Quality Threshold Met:** Overall weighted score of {analysis['weighted_avg']:.2f}/10.0 exceeds the 8.0 minimum\n")
        f.write("\n")

        f.write("### Recommendations\n\n")
        if analysis['ip_avg'] < 6.0:
            f.write(f"- 📝 **Enhance Critical Thinking:** IP score of {analysis['ip_avg']:.2f}/10.0 suggests adding more questions requiring analysis, synthesis, or evaluation\n")
        if analysis['qa_avg'] < 8.5:
            f.write(f"- 📝 **Improve Factual Accuracy:** QA score of {analysis['qa_avg']:.2f}/10.0 indicates room for improvement in answer correctness\n")
        if analysis['ec_avg'] < 9.0:
            f.write(f"- 📝 **Strengthen Curriculum Alignment:** EC score of {analysis['ec_avg']:.2f}/10.0 could be improved with tighter alignment to standards\n")
        if analysis['weighted_avg'] < 8.0:
            f.write(f"- ⚠️ **Below Quality Threshold:** Overall score of {analysis['weighted_avg']:.2f}/10.0 requires improvement to meet 8.0 minimum\n")
        f.write("\n")

        f.write("---\n\n")

        # Footer
        f.write(f"*Report generated by Incept Evaluation Analysis System - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")


def generate_json_report(analysis: Dict[str, Any], output_file: str):
    """Generate JSON report"""

    json_data = {
        'report_generated': datetime.now().isoformat(),
        'total_questions': analysis['total_questions'],
        'overall_scores': {
            'weighted_average': round(analysis['weighted_avg'], 2),
            'qa_average': round(analysis['qa_avg'], 2),
            'ec_average': round(analysis['ec_avg'], 2),
            'ip_average': round(analysis['ip_avg'], 2),
            'qa_count': len(analysis['qa_scores']),
            'ec_count': len(analysis['ec_scores']),
            'ip_count': len(analysis['ip_scores']),
            'unparsed': analysis['unparsed'],
        },
        'weighted_score_calculation': {
            'qa_weight': 0.35,
            'ec_weight': 0.45,
            'ip_weight': 0.20,
            'qa_contribution': round(analysis['qa_avg'] * 0.35, 2),
            'ec_contribution': round(analysis['ec_avg'] * 0.45, 2),
            'ip_contribution': round(analysis['ip_avg'] * 0.20, 2),
        },
        'by_grade': {},
        'by_subject': dict(analysis['by_subject']),
    }

    # Add per-grade data
    for grade, data in analysis['by_grade'].items():
        json_data['by_grade'][f"grade_{grade}"] = {
            'total_questions': data['total'],
            'weighted_average': round(data['weighted_avg'], 2),
            'qa_average': round(data['qa_avg'], 2),
            'ec_average': round(data['ec_avg'], 2),
            'ip_average': round(data['ip_avg'], 2),
        }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Generate comprehensive report from JSONL evaluation results")
    parser.add_argument("jsonl_file", type=str, help="Path to JSONL evaluation file")
    parser.add_argument(
        "--output-md",
        type=str,
        default="evaluation_report.md",
        help="Output markdown file (default: evaluation_report.md)"
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default="evaluation_report.json",
        help="Output JSON file (default: evaluation_report.json)"
    )

    args = parser.parse_args()

    try:
        print(f"Analyzing {args.jsonl_file}...")
        analysis = analyze_jsonl(args.jsonl_file)
        print(f"✓ Analyzed {analysis['total_questions']:,} questions")

        print(f"\nGenerating markdown report: {args.output_md}...")
        generate_markdown_report(analysis, args.output_md, args.jsonl_file)
        print(f"✓ Markdown report saved")

        print(f"\nGenerating JSON report: {args.output_json}...")
        generate_json_report(analysis, args.output_json)
        print(f"✓ JSON report saved")

        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Weighted Score: {analysis['weighted_avg']:.2f}/10.0")
        print(f"  QA: {analysis['qa_avg']:.2f} (weight: 35%, contribution: {analysis['qa_avg']*0.35:.2f})")
        print(f"  EC: {analysis['ec_avg']:.2f} (weight: 45%, contribution: {analysis['ec_avg']*0.45:.2f})")
        print(f"  IP: {analysis['ip_avg']:.2f} (weight: 20%, contribution: {analysis['ip_avg']*0.20:.2f})")
        print(f"\nQuality Status: {'✅ PASS' if analysis['weighted_avg'] >= 8.0 else '⚠️ BELOW THRESHOLD'}")
        print("="*80)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
