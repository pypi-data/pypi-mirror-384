#!/usr/bin/env python3
"""
Comprehensive curriculum evaluation script.
Generates and evaluates questions for every skill in the curriculum (grades 3-8).
"""

import argparse
import copy
import json
import logging
import os
import sys
import time
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np

from dotenv import load_dotenv
load_dotenv()

from src.llms import produce_structured_response
from src.dto.question_generation import (
    GenerateQuestionResponse,
    GeneratedQuestion,
    GenerateQuestionsRequest,
    GenerateQuestionResponseNoEval,
    GeneratedQuestionForDirectGen
)
from src.evaluator.v3 import evaluate_api_response

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CURRICULUM_DIR = project_root / "edu_configs"
OUTPUT_DIR = project_root / "data" / "evaluation_results"
OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

def call_generate_questions_api(
    lesson_title: str,
    substandard_description: str,
    unit_name: str,
    grade: int,
    tasks: str,
    substandard_id: str,
    api_url: str,
    api_key: str,
    count: int = 2,
    model: str = "openai"
) -> Dict[str, Any]:
    """Call the generate_questions API for a specific skill."""

    # Build request payload
    # When using "incept" mode, send "falcon" to the API to use Falcon provider
    api_model = "dspy"

    request_payload = {
        "grade": grade,
        "count": count,
        "subject": "mathematics",
        "language": "english",
        "translate": True,
        "model": api_model,
        "evaluate": False,  # Don't evaluate in API, do it separately
        "instructions": f"Generate questions for: {substandard_description}",
        "skill": {
            "id": substandard_id,
            "title": lesson_title,  # V1.1: title = lesson_title from curriculum
            "unit_name": unit_name,
            "description": substandard_description or lesson_title  # V1.1: description = substandard_description
        },
        "question_type": "mcq",
        "difficulty": "medium"
    }

    generation_start = time.time()

    try:
        # For GPT-5 and Falcon, use direct generation with produce_structured_response
        if model in ["gpt-5", "falcon"]:
            # Build prompt for direct generation - MUST match INCEPT output format
            prompt = f"""Generate {count} high-quality mathematics MCQ questions for Grade {grade}.

Skill: {lesson_title}
Unit: {unit_name}
Description: {substandard_description}
Learning Tasks: {tasks}

REQUIRED OUTPUT FOR EACH QUESTION:
1. Question text (real-world scenario, grade-appropriate)
2. Four answer options (A, B, C, D) with one correct answer
3. Basic explanation (1-2 sentences)
4. **detailed_explanation** with:
   - steps: Array of 3 explanation steps, each with:
     * title (e.g., "Step 1: Understand the Problem")
     * content (detailed explanation for that step, 3-5 sentences, grade-appropriate)
   - personalized_academic_insights: Array of 3 common wrong answers with:
     * answer: The incorrect answer value
     * insight: Why students might choose this and how to correct their thinking
5. **voiceover_script** with:
   - question_script: Natural language version of the question for text-to-speech
   - answer_choice_scripts: Array of 4 scripts for each answer option (for accessibility)
   - explanation_step_scripts: Array with step_number and script for each explanation step

CRITICAL:
- All questions must be mathematically correct
- Explanations must be clear and grade-appropriate
- Include all scaffolding (detailed_explanation and voiceover_script)
- Use grade-appropriate vocabulary and complexity"""

            messages = [
                {"role": "system", "content": "You are an expert educational content generator specialized in mathematics curriculum."},
                {"role": "user", "content": prompt}
            ]

            # Determine provider based on model
            provider = "openai" if model == "gpt-5" else "falcon"

            # Generate questions without evaluation (to avoid schema issues)
            response_no_eval = produce_structured_response(
                messages=messages,
                structure_model=GenerateQuestionResponseNoEval,
                provider=provider,
                max_output_tokens=4096
            )

            # Convert to dict to serialize all Pydantic models to plain dicts
            if hasattr(response_no_eval, 'model_dump_json'):
                response_dict = json.loads(response_no_eval.model_dump_json())
            elif hasattr(response_no_eval, 'model_dump'):
                response_dict = response_no_eval.model_dump()
            elif isinstance(response_no_eval, dict):
                response_dict = response_no_eval
            else:
                response_dict = dict(response_no_eval)

            # Convert each question dict to GeneratedQuestion object (with nested fields as dicts)
            question_objects = []
            for q_dict in response_dict['data']:
                q_dict['di_formats_used'] = None
                q_dict['skill'] = None  # Causes JSON serialization issues in evaluator
                # Use model_construct to create object without validation (keeps nested dicts as dicts)
                q_obj = GeneratedQuestion.model_construct(**q_dict)
                question_objects.append(q_obj)

            # Create response with actual GeneratedQuestion objects (not dicts)
            response_obj = GenerateQuestionResponse(
                data=question_objects,
                request_id=response_dict['request_id'],
                total_questions=response_dict['total_questions'],
                grade=response_dict['grade'],
                evaluation=None
            )

            generation_duration = time.time() - generation_start

            # Run evaluation on the generated response (separate timing)
            eval_start = time.time()

            # Fix request payload for evaluation - add lesson_title if missing
            eval_payload = copy.deepcopy(request_payload)
            if 'skill' in eval_payload and 'lesson_title' not in eval_payload['skill']:
                eval_payload['skill']['lesson_title'] = eval_payload['skill'].get('title', lesson_title)

            try:
                request_obj = GenerateQuestionsRequest(**eval_payload)
            except Exception as e:
                logger.error(f"      ❌ Failed to create GenerateQuestionsRequest: {e}")
                logger.error(f"      skill dict: {eval_payload.get('skill', {})}")
                raise

            evaluation, report = evaluate_api_response(
                request=request_obj,
                response=response_obj,
                generate_report=True,
                update_baseline=False
            )
            evaluation_duration = time.time() - eval_start

            # Add evaluation to response (convert QuestionEvaluation objects to dicts)
            section_scores = evaluation.compliance_report.get("section_scores", {}) if hasattr(evaluation, 'compliance_report') else {}

            # Convert question evaluations to simple dicts
            question_evals = []
            if evaluation.question_evaluations:
                for q in evaluation.question_evaluations:
                    question_evals.append({
                        "question_id": q.question_id,
                        "overall_score": q.overall_score,
                        "recommendation": q.recommendation,
                        "question_section": {
                            "section_score": q.question_section.section_score,
                            "recommendation": q.question_section.recommendation
                        } if q.question_section else None,
                        "scaffolding_section": {
                            "section_score": q.scaffolding_section.section_score,
                            "recommendation": q.scaffolding_section.recommendation
                        } if q.scaffolding_section else None,
                        "image_section": {
                            "section_score": q.image_section.section_score,
                            "recommendation": q.image_section.recommendation
                        } if q.image_section else None
                    })

            response_obj.evaluation = {
                "overall_score": evaluation.overall_score,
                "scores": evaluation.aggregate_scores,
                "section_scores": section_scores,
                "question_evaluations": question_evals
            }

            # Convert Pydantic model to dict if needed
            if hasattr(response_obj, 'model_dump'):
                response_data = response_obj.model_dump()
            elif not isinstance(response_obj, dict):
                response_data = dict(response_obj)
            else:
                response_data = response_obj

            return {
                "success": True,
                "duration": generation_duration,  # Only generation time
                "evaluation_duration": evaluation_duration,
                "total_duration": generation_duration + evaluation_duration,
                "request": request_payload,
                "response": response_data,
                "error": None
            }

        # For INCEPT (openai model), use the API
        else:
            logger.info(f"      🌐 Sending HTTP request with model={request_payload.get('model')}")
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(
                f"{api_url}/v1.1/generate_questions",
                json=request_payload,
                headers=headers,
                timeout=600  # 10 minutes
            )

            generation_duration = time.time() - generation_start

            response.raise_for_status()
            response_data = response.json()

            # Evaluate the response separately
            eval_start = time.time()

            # Convert response to proper format for evaluation
            question_objects = []
            for q_dict in response_data.get('data', []):
                q_dict['di_formats_used'] = q_dict.get('di_formats_used', None)
                q_dict['skill'] = None  # Causes JSON serialization issues in evaluator
                q_obj = GeneratedQuestion.model_construct(**q_dict)
                question_objects.append(q_obj)

            response_obj = GenerateQuestionResponse(
                data=question_objects,
                request_id=response_data['request_id'],
                total_questions=response_data['total_questions'],
                grade=response_data['grade'],
                evaluation=None
            )

            # Fix request payload for evaluation - add lesson_title if missing
            eval_payload = copy.deepcopy(request_payload)
            if 'skill' in eval_payload and 'lesson_title' not in eval_payload['skill']:
                eval_payload['skill']['lesson_title'] = eval_payload['skill'].get('title', lesson_title)

            try:
                request_obj = GenerateQuestionsRequest(**eval_payload)
            except Exception as e:
                logger.error(f"      ❌ Failed to create GenerateQuestionsRequest: {e}")
                logger.error(f"      skill dict: {eval_payload.get('skill', {})}")
                raise

            evaluation, report = evaluate_api_response(
                request=request_obj,
                response=response_obj,
                generate_report=True,
                update_baseline=False
            )

            evaluation_duration = time.time() - eval_start

            # Add evaluation to response_data
            section_scores = evaluation.compliance_report.get("section_scores", {}) if hasattr(evaluation, 'compliance_report') else {}

            question_evals = []
            if evaluation.question_evaluations:
                for q in evaluation.question_evaluations:
                    question_evals.append({
                        "question_id": q.question_id,
                        "overall_score": q.overall_score,
                        "recommendation": q.recommendation,
                        "question_section": {
                            "section_score": q.question_section.section_score,
                            "recommendation": q.question_section.recommendation
                        } if q.question_section else None,
                        "scaffolding_section": {
                            "section_score": q.scaffolding_section.section_score,
                            "recommendation": q.scaffolding_section.recommendation
                        } if q.scaffolding_section else None,
                        "image_section": {
                            "section_score": q.image_section.section_score,
                            "recommendation": q.image_section.recommendation
                        } if q.image_section else None
                    })

            response_data['evaluation'] = {
                "overall_score": evaluation.overall_score,
                "scores": evaluation.aggregate_scores,
                "section_scores": section_scores,
                "question_evaluations": question_evals
            }

            return {
                "success": True,
                "duration": generation_duration,  # Only generation time
                "evaluation_duration": evaluation_duration,
                "total_duration": generation_duration + evaluation_duration,
                "request": request_payload,
                "response": response_data,
                "error": None
            }

    except Exception as e:
        duration = time.time() - generation_start
        logger.error(f"API call failed for {lesson_title}: {e}")

        return {
            "success": False,
            "duration": duration,
            "evaluation_duration": 0,
            "total_duration": duration,
            "request": request_payload,
            "response": None,
            "error": str(e)
        }

def classify_error_type(issue: str) -> str:
    """Classify error type from issue text for EduBench-aligned taxonomy."""
    issue_lower = issue.lower()

    # Mathematical errors
    if any(keyword in issue_lower for keyword in [
        'calculation', 'answer', 'correct', 'incorrect', 'wrong', 'value',
        'math', 'solution', 'equation', 'formula', 'option'
    ]):
        return 'mathematical'

    # Query mismatch errors
    if any(keyword in issue_lower for keyword in [
        'topic', 'off-topic', 'query', 'relevance', 'unrelated', 'mismatch', 'skill'
    ]):
        return 'query_mismatch'

    # Format errors
    if any(keyword in issue_lower for keyword in [
        'format', 'structure', 'option', 'mcq', 'letter', 'map'
    ]):
        return 'format'

    # Linguistic errors
    if any(keyword in issue_lower for keyword in [
        'language', 'grammar', 'clarity', 'wording', 'vocabulary', 'translation'
    ]):
        return 'linguistic'

    # Pedagogical errors (default for explanation, DI, etc.)
    if any(keyword in issue_lower for keyword in [
        'explanation', 'pedagog', 'learning', 'di', 'scaffolding', 'grade'
    ]):
        return 'pedagogical'

    return 'pedagogical'  # Default


def process_grade(
    grade: int,
    api_url: str,
    api_key: str,
    max_skills: int = None,
    resume: bool = False,
    model: str = "dspy",
    concurrent_requests: int = 1
) -> Dict[str, Any]:
    """Process all skills for a grade."""

    curriculum_file = CURRICULUM_DIR / f"curriculum_grade_{grade}.jsonl"

    # Create model-specific directory
    model_dir = OUTPUT_DIR / model
    model_dir.mkdir(exist_ok=True, parents=True)

    output_file = model_dir / f"evaluation_grade_{grade}.jsonl"

    logger.info(f"📚 Processing Grade {grade} with model {model}")
    logger.info(f"   Input: {curriculum_file}")
    logger.info(f"   Output: {output_file}")

    # Load curriculum
    skills = []
    with open(curriculum_file, 'r') as f:
        for line in f:
            skills.append(json.loads(line))

    if max_skills:
        skills = skills[:max_skills]
        logger.info(f"   Limited to first {max_skills} skills")

    # Check for resume
    completed_indices = set()
    if resume and output_file.exists():
        # Find ALL processed skill indices (including gaps)
        with open(output_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    record = json.loads(line)
                    completed_indices.add(record.get('skill_index'))
                except json.JSONDecodeError:
                    logger.warning(f"   ⚠️  Skipping invalid JSON line in existing results")
                    continue

        if completed_indices:
            missing_count = len(skills) - len(completed_indices)
            logger.info(f"   📌 Resume mode: Found {len(completed_indices)} completed, {missing_count} missing")

            # Show first few missing indices
            all_indices = set(range(1, len(skills) + 1))
            missing_indices = sorted(all_indices - completed_indices)
            if missing_indices:
                preview = missing_indices[:10]
                preview_str = ", ".join(map(str, preview))
                if len(missing_indices) > 10:
                    preview_str += f"... ({len(missing_indices)} total missing)"
                logger.info(f"   Missing indices: {preview_str}")
            else:
                logger.info(f"   ✅ All skills already completed")
                # Return existing stats
                summary_file = model_dir / f"summary_grade_{grade}.json"
                if summary_file.exists():
                    with open(summary_file, 'r') as f:
                        return json.load(f)
                else:
                    return {"grade": grade, "message": "Already completed, no summary found"}

    logger.info(f"   Total skills: {len(skills)}")

    # Process skills in parallel (max 5 concurrent)
    results = []
    durations = []
    overall_scores = []

    # EduBench-aligned statistics
    dimension_scores = {
        'correctness': [],
        'grade_alignment': [],
        'difficulty_alignment': [],
        'language_quality': [],
        'pedagogical_value': [],
        'explanation_quality': [],
        'instruction_adherence': [],
        'format_compliance': [],
        'di_compliance': [],
        'query_relevance': []
    }
    section_scores = {'question': [], 'scaffolding': [], 'image': []}
    recommendation_counts = {'accept': 0, 'revise': 0, 'reject': 0}
    error_types = {'mathematical': 0, 'pedagogical': 0, 'linguistic': 0, 'format': 0, 'query_mismatch': 0}

    def process_skill(idx, skill):
        """Process a single skill (called in parallel)."""
        lesson_title = skill.get('lesson_title', 'Unknown')
        substandard_id = skill.get('substandard_id', 'Unknown')

        logger.info(f"   [{idx}/{len(skills)}] {lesson_title}")

        # Call API
        result = call_generate_questions_api(
            lesson_title=lesson_title,
            substandard_description=skill.get('substandard_description', ''),
            unit_name=skill.get('unit_name', ''),
            grade=grade,
            tasks=skill.get('tasks', ''),
            substandard_id=substandard_id,
            api_url=api_url,
            api_key=api_key,
            count=1,  # Changed from 50 to 1 for debugging
            model=model
        )

        return (idx, skill, result)

    # Open file in append mode if resuming, write mode otherwise
    file_mode = 'a' if resume else 'w'

    with open(output_file, file_mode) as out:
        # Process skills in parallel batches
        logger.info(f"   Processing skills with {concurrent_requests} concurrent requests")

        # Filter skills to process: exclude already completed indices
        skills_to_process = [(idx, skill) for idx, skill in enumerate(skills, 1) if idx not in completed_indices]

        if not skills_to_process:
            logger.info(f"   ✅ No skills to process (all completed)")
            return {"grade": grade, "message": "All skills already completed"}

        logger.info(f"   Processing {len(skills_to_process)} skills (skipping {len(completed_indices)} already completed)")

        with ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
            # Process in batches
            for batch_start in range(0, len(skills_to_process), concurrent_requests):
                batch_end = min(batch_start + concurrent_requests, len(skills_to_process))
                batch = skills_to_process[batch_start:batch_end]

                logger.info(f"   📦 Processing batch: skills {batch[0][0]}-{batch[-1][0]} ({len(batch)} concurrent)")

                # Submit all skills in this batch
                futures = {
                    executor.submit(process_skill, idx, skill): (idx, skill)
                    for idx, skill in batch
                }

                # Wait for all in this batch to complete
                for future in as_completed(futures):
                    idx, skill = futures[future]
                    lesson_title = skill.get('lesson_title', 'Unknown')
                    substandard_id = skill.get('substandard_id', 'Unknown')

                    try:
                        idx, skill, result = future.result()

                        durations.append(result['duration'])

                        if result['success']:
                            # Extract questions and evaluations
                            response_data = result['response']
                            questions = response_data.get('data', [])
                            evaluation = response_data.get('evaluation', {})

                            # Get overall score
                            overall_score = evaluation.get('overall_score')
                            if overall_score is not None:
                                overall_scores.append(overall_score)

                            # EduBench-aligned: Collect dimension scores
                            eval_scores = evaluation.get('scores', {})
                            for dim_name, dim_score in eval_scores.items():
                                if dim_name in dimension_scores:
                                    dimension_scores[dim_name].append(dim_score)

                            # EduBench-aligned: Collect section scores
                            eval_section_scores = evaluation.get('section_scores', {})
                            for section_name, section_data in eval_section_scores.items():
                                if section_name in section_scores and isinstance(section_data, dict):
                                    avg_score = section_data.get('average_score')
                                    if avg_score is not None:
                                        section_scores[section_name].append(avg_score)

                            # EduBench-aligned: Collect recommendation counts and error types
                            question_evaluations = evaluation.get('question_evaluations', [])
                            for q_eval in question_evaluations:
                                # Count recommendations
                                recommendation = q_eval.get('recommendation', 'revise')
                                if recommendation in recommendation_counts:
                                    recommendation_counts[recommendation] += 1

                                # Classify error types from issues
                                issues = q_eval.get('issues', [])
                                for issue in issues:
                                    error_type = classify_error_type(issue)
                                    if error_type in error_types:
                                        error_types[error_type] += 1

                            # Write each question as a separate line
                            for q_idx, question in enumerate(questions):
                                # Get question-specific evaluation if available
                                question_evaluations = evaluation.get('question_evaluations', [])
                                question_eval = question_evaluations[q_idx] if q_idx < len(question_evaluations) else {}

                                output_record = {
                                    "timestamp": datetime.now().isoformat(),
                                    "grade": grade,
                                    "skill_index": idx,
                                    "substandard_id": substandard_id,
                                    "lesson_title": lesson_title,
                                    "unit_name": skill.get('unit_name', ''),
                                    "question_index": q_idx,
                                    "request": result['request'],
                                    "question": question,
                                    "question_evaluation": question_eval,
                                    "overall_evaluation": {
                                        "overall_score": overall_score,
                                        "scores": evaluation.get('scores', {}),
                                        "section_scores": evaluation.get('section_scores', {})
                                    },
                                    "generation_duration": result['duration'],  # Only generation time
                                    "evaluation_duration": result.get('evaluation_duration', 0),
                                    "total_duration": result.get('total_duration', result['duration']),
                                    "success": True
                                }

                                out.write(json.dumps(output_record, ensure_ascii=False) + '\n')
                                out.flush()

                            gen_time = result['duration']
                            eval_time = result.get('evaluation_duration', 0)
                            total_time = result.get('total_duration', gen_time)
                            logger.info(f"      ✅ [{idx}/{len(skills)}] {lesson_title}: {len(questions)} questions in {gen_time:.1f}s gen + {eval_time:.1f}s eval = {total_time:.1f}s (score: {overall_score:.2%})" if overall_score else f"      ✅ [{idx}/{len(skills)}] {lesson_title}: {len(questions)} questions in {gen_time:.1f}s gen + {eval_time:.1f}s eval = {total_time:.1f}s")
                        else:
                            # Log error but don't write to JSONL
                            logger.error(f"      ❌ [{idx}/{len(skills)}] {lesson_title}: Failed - {result['error']}")

                    except Exception as e:
                        logger.error(f"      ❌ Exception processing skill {idx} ({lesson_title}): {str(e)}")

    # Calculate dimension statistics (EduBench-aligned)
    dimension_stats = {}
    for dim_name, dim_values in dimension_scores.items():
        if dim_values:
            dimension_stats[dim_name] = {
                "mean": float(np.mean(dim_values)),
                "median": float(np.median(dim_values)),
                "std": float(np.std(dim_values)),
                "min": float(np.min(dim_values)),
                "max": float(np.max(dim_values))
            }

    # Calculate section statistics (EduBench-aligned)
    section_stats = {}
    for section_name, section_values in section_scores.items():
        if section_values:
            section_stats[section_name] = {
                "mean": float(np.mean(section_values)),
                "median": float(np.median(section_values)),
                "std": float(np.std(section_values)),
                "count": len(section_values)
            }

    # Calculate statistics
    stats = {
        "grade": grade,
        "timestamp": datetime.now().isoformat(),
        "total_skills": len(skills),
        "total_questions": len(overall_scores) * 50,  # 50 questions per skill
        "successful_skills": sum(1 for d in durations if d > 0),
        "durations": {
            "mean": float(np.mean(durations)) if durations else 0.0,
            "median": float(np.median(durations)) if durations else 0.0,
            "p90": float(np.percentile(durations, 90)) if durations else 0.0,
            "p95": float(np.percentile(durations, 95)) if durations else 0.0,
            "p99": float(np.percentile(durations, 99)) if durations else 0.0,
            "min": float(np.min(durations)) if durations else 0.0,
            "max": float(np.max(durations)) if durations else 0.0
        },
        "scores": {
            "mean": float(np.mean(overall_scores)) if overall_scores else 0.0,
            "median": float(np.median(overall_scores)) if overall_scores else 0.0,
            "min": float(np.min(overall_scores)) if overall_scores else 0.0,
            "max": float(np.max(overall_scores)) if overall_scores else 0.0,
            "p25": float(np.percentile(overall_scores, 25)) if overall_scores else 0.0,
            "p75": float(np.percentile(overall_scores, 75)) if overall_scores else 0.0,
            "std": float(np.std(overall_scores)) if overall_scores else 0.0
        },
        # EduBench-aligned metrics
        "dimension_scores": dimension_stats,
        "section_scores": section_stats,
        "quality_distribution": {
            "accept": recommendation_counts['accept'],
            "revise": recommendation_counts['revise'],
            "reject": recommendation_counts['reject'],
            "total": sum(recommendation_counts.values()),
            "accept_rate": recommendation_counts['accept'] / sum(recommendation_counts.values()) if sum(recommendation_counts.values()) > 0 else 0.0,
            "reject_rate": recommendation_counts['reject'] / sum(recommendation_counts.values()) if sum(recommendation_counts.values()) > 0 else 0.0
        },
        "error_taxonomy": {
            "mathematical": error_types['mathematical'],
            "pedagogical": error_types['pedagogical'],
            "linguistic": error_types['linguistic'],
            "format": error_types['format'],
            "query_mismatch": error_types['query_mismatch'],
            "total_errors": sum(error_types.values())
        }
    }

    # Save summary
    summary_file = model_dir / f"summary_grade_{grade}.json"
    with open(summary_file, 'w') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    logger.info(f"   📊 Summary:")
    logger.info(f"      Duration: mean={stats['durations']['mean']:.1f}s, p95={stats['durations']['p95']:.1f}s, p99={stats['durations']['p99']:.1f}s")
    logger.info(f"      Quality: mean={stats['scores']['mean']:.2%}, median={stats['scores']['median']:.2%}")
    logger.info(f"      Quality Distribution: Accept={stats['quality_distribution']['accept']}, Revise={stats['quality_distribution']['revise']}, Reject={stats['quality_distribution']['reject']}")
    logger.info(f"      Error Taxonomy: Math={stats['error_taxonomy']['mathematical']}, Pedagogical={stats['error_taxonomy']['pedagogical']}, Linguistic={stats['error_taxonomy']['linguistic']}, Format={stats['error_taxonomy']['format']}, Query={stats['error_taxonomy']['query_mismatch']}")
    logger.info(f"      Saved to: {summary_file}")

    return stats

def main():
    """Main evaluation runner."""
    parser = argparse.ArgumentParser(description="Run comprehensive curriculum evaluation")
    parser.add_argument("--grades", nargs="+", type=int, default=[3, 4, 5, 6, 7, 8],
                       help="Grades to evaluate (default: 3 4 5 6 7 8)")
    parser.add_argument("--api-url", default=None,
                       help="API URL (default: from EVALUATION_API_URL env or https://uae-poc.inceptapi.com)")
    parser.add_argument("--model", default="dspy",
                       help="Model to use: dspy, openai, gpt-5, falcon (default: dspy)")
    parser.add_argument("--max-skills", type=int, default=None,
                       help="Maximum skills per grade (for testing)")
    parser.add_argument("--no-resume", dest="resume", action="store_false", default=True,
                       help="Disable resume mode (overwrite existing results)")
    parser.add_argument("--concurrent", type=int, default=1,
                       help="Number of concurrent requests (default: 1)")
    args = parser.parse_args()

    # Determine API URL: CLI arg > env var > default
    api_url = args.api_url or os.getenv("EVALUATION_API_URL", "https://uae-poc.inceptapi.com")

    logger.info("🚀 Starting comprehensive curriculum evaluation")
    logger.info(f"   Grades: {args.grades}")
    logger.info(f"   Model: {args.model}")
    logger.info(f"   API: {api_url}")
    logger.info(f"   Concurrent requests: {args.concurrent}")
    logger.info(f"   Output: {OUTPUT_DIR}")

    # Check API key
    api_key = os.getenv("INCEPT_API_KEY")
    if not api_key:
        logger.error("❌ INCEPT_API_KEY environment variable required")
        sys.exit(1)

    # Process each grade
    all_stats = []
    for grade in args.grades:
        try:
            stats = process_grade(grade, api_url, api_key, args.max_skills, args.resume, args.model, args.concurrent)
            all_stats.append(stats)
        except Exception as e:
            logger.error(f"❌ Failed to process grade {grade}: {e}")
            import traceback
            traceback.print_exc()

    # Calculate aggregated dimension scores across all grades
    aggregated_dimensions = {}
    all_dimension_names = set()
    for stat in all_stats:
        if 'dimension_scores' in stat:
            all_dimension_names.update(stat['dimension_scores'].keys())

    for dim_name in all_dimension_names:
        dim_means = []
        for stat in all_stats:
            if 'dimension_scores' in stat and dim_name in stat['dimension_scores']:
                dim_means.append(stat['dimension_scores'][dim_name]['mean'])
        if dim_means:
            aggregated_dimensions[dim_name] = {
                "mean": float(np.mean(dim_means)),
                "std": float(np.std(dim_means)),
                "min": float(np.min(dim_means)),
                "max": float(np.max(dim_means))
            }

    # Calculate aggregated error taxonomy
    aggregated_errors = {
        'mathematical': sum(s['error_taxonomy']['mathematical'] for s in all_stats if 'error_taxonomy' in s),
        'pedagogical': sum(s['error_taxonomy']['pedagogical'] for s in all_stats if 'error_taxonomy' in s),
        'linguistic': sum(s['error_taxonomy']['linguistic'] for s in all_stats if 'error_taxonomy' in s),
        'format': sum(s['error_taxonomy']['format'] for s in all_stats if 'error_taxonomy' in s),
        'query_mismatch': sum(s['error_taxonomy']['query_mismatch'] for s in all_stats if 'error_taxonomy' in s)
    }
    aggregated_errors['total'] = sum(aggregated_errors.values())

    # Calculate aggregated quality distribution
    aggregated_quality = {
        'accept': sum(s['quality_distribution']['accept'] for s in all_stats if 'quality_distribution' in s),
        'revise': sum(s['quality_distribution']['revise'] for s in all_stats if 'quality_distribution' in s),
        'reject': sum(s['quality_distribution']['reject'] for s in all_stats if 'quality_distribution' in s)
    }
    total_questions_with_quality = sum(aggregated_quality.values())
    if total_questions_with_quality > 0:
        aggregated_quality['accept_rate'] = aggregated_quality['accept'] / total_questions_with_quality
        aggregated_quality['reject_rate'] = aggregated_quality['reject'] / total_questions_with_quality
    else:
        aggregated_quality['accept_rate'] = 0.0
        aggregated_quality['reject_rate'] = 0.0

    # Save combined summary
    combined_summary = {
        "timestamp": datetime.now().isoformat(),
        "model": args.model,
        "grades_evaluated": args.grades,
        "grade_summaries": all_stats,
        "overall": {
            "total_skills": sum(s['total_skills'] for s in all_stats),
            "total_questions": sum(s['total_questions'] for s in all_stats),
            "mean_duration": float(np.mean([s['durations']['mean'] for s in all_stats])),
            "mean_score": float(np.mean([s['scores']['mean'] for s in all_stats if s['scores']['mean'] > 0]))
        },
        # EduBench-aligned aggregated metrics
        "aggregated_dimension_scores": aggregated_dimensions,
        "aggregated_quality_distribution": aggregated_quality,
        "aggregated_error_taxonomy": aggregated_errors
    }

    model_dir = OUTPUT_DIR / args.model
    model_dir.mkdir(exist_ok=True, parents=True)
    combined_file = model_dir / "summary_all_grades.json"
    with open(combined_file, 'w') as f:
        json.dump(combined_summary, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'='*60}")
    logger.info(f"✨ Evaluation complete!")
    logger.info(f"   Total skills: {combined_summary['overall']['total_skills']}")
    logger.info(f"   Total questions: {combined_summary['overall']['total_questions']}")
    logger.info(f"   Mean duration: {combined_summary['overall']['mean_duration']:.1f}s")
    logger.info(f"   Mean quality: {combined_summary['overall']['mean_score']:.2%}")
    logger.info(f"\n   📊 Quality Distribution:")
    logger.info(f"      Accept: {combined_summary['aggregated_quality_distribution']['accept']} ({combined_summary['aggregated_quality_distribution']['accept_rate']:.1%})")
    logger.info(f"      Revise: {combined_summary['aggregated_quality_distribution']['revise']}")
    logger.info(f"      Reject: {combined_summary['aggregated_quality_distribution']['reject']} ({combined_summary['aggregated_quality_distribution']['reject_rate']:.1%})")
    logger.info(f"\n   🔍 Error Taxonomy (Total: {combined_summary['aggregated_error_taxonomy']['total']}):")
    logger.info(f"      Mathematical: {combined_summary['aggregated_error_taxonomy']['mathematical']}")
    logger.info(f"      Pedagogical: {combined_summary['aggregated_error_taxonomy']['pedagogical']}")
    logger.info(f"      Linguistic: {combined_summary['aggregated_error_taxonomy']['linguistic']}")
    logger.info(f"      Format: {combined_summary['aggregated_error_taxonomy']['format']}")
    logger.info(f"      Query Mismatch: {combined_summary['aggregated_error_taxonomy']['query_mismatch']}")
    logger.info(f"\n   Results saved to: {model_dir}")
    logger.info(f"{'='*60}")

if __name__ == "__main__":
    main()
