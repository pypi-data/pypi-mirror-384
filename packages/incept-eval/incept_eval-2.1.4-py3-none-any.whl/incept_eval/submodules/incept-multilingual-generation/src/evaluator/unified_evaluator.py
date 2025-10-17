"""
Unified Evaluator: Combines v3.py and edubench.py evaluators.
Single clean function that takes request + questions and runs both evaluations.
"""

import sys
import uuid
import time
import logging
from pathlib import Path
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Any, List, Optional, Literal, Dict
from src.dto.question_generation import GenerateQuestionsRequest, GeneratedQuestion, EvaluationModules, SkillInfo
from src.evaluator.v3 import QuestionEvaluation, ResponseEvaluation, call_single_shot_evaluator
from src.evaluator.edubench import verify_answer_with_gpt4, get_normal_answer
from src.evaluator.EduBench.code.evaluation.evaluation import TASK_PROMPT_TEMPLATES
import os
import json
import re
import requests
import asyncio
import anthropic
from openai import AsyncOpenAI

# Add reading-question-qc submodule to path
_submodule_path = Path(__file__).parent.parent / "external_submodules" / "reading-question-qc"
if str(_submodule_path) not in sys.path:
    sys.path.insert(0, str(_submodule_path))

from qc_pipeline import QuestionQCAnalyzer


class UniverslSkillInfoInput(BaseModel):
    title: str
    grade: str
    subject: str = "mathematics"
    difficulty: Optional[Literal["easy", "medium", "hard"]] = "medium"
    description: Optional[str] = None
    language: Literal['en', 'ar'] = 'en'

class UniversalGeneratedQuestionInput(BaseModel):
    id: str
    type: Literal["mcq", "fill-in"]  # MCQ and fill-in questions supported
    question: str
    answer: str
    answer_explanation: str
    answer_options: Optional[Dict[str, str]] = None  # Dict format for MCQ: {"A": "4 cm", "B": "0.4 cm", ...}
    skill: Optional[UniverslSkillInfoInput] = None
    image_url: Optional[str] = None
    additional_details: Optional[str] = None


class UniversalEvaluationRequest(BaseModel):
    generated_questions: List[UniversalGeneratedQuestionInput]
    submodules_to_run: List[Literal["internal_evaluator", "answer_verification", "directionai_edubench", "reading_question_qc"]] = ["internal_evaluator", "answer_verification", "directionai_edubench", "reading_question_qc"]

class EdubenchScores(BaseModel):
    qa_score: float
    ec_score: float
    ip_score: float
    ag_score: float
    qg_score: float
    tmg_score: float
    average_score: float


class InternalEvaluatorScores(BaseModel):
    correctness: float
    grade_alignment: float
    difficulty_alignment: float
    language_quality: float
    pedagogical_value: float
    explanation_quality: float
    instruction_adherence: float
    format_compliance: float
    query_relevance: float
    di_compliance: float


class DIScores(BaseModel):
    overall: float
    general_principles: float
    format_alignment: float
    grade_language: float


class SectionEvaluation(BaseModel):
    section_score: float
    issues: List[str]
    strengths: List[str]
    recommendation: str


class SectionEvaluations(BaseModel):
    question: SectionEvaluation
    scaffolding: SectionEvaluation


class InternalEvaluatorResult(BaseModel):
    scores: InternalEvaluatorScores
    issues: List[str]
    strengths: List[str]
    overall: float
    recommendation: str
    suggested_improvements: List[str]
    di_scores: DIScores
    section_evaluations: SectionEvaluations


class AnswerVerificationResult(BaseModel):
    is_correct: bool
    correct_answer: str
    confidence: int
    reasoning: str


class ReadingQuestionQCResult(BaseModel):
    overall_score: float
    distractor_checks: Dict[str, Any]
    question_checks: Dict[str, Any]
    passed: bool


class UniversalQuestionEvaluationScores(BaseModel):
    internal_evaluator: Optional[InternalEvaluatorResult] = None
    answer_verification: Optional[AnswerVerificationResult] = None
    directionai_edubench: Optional[EdubenchScores] = None
    reading_question_qc: Optional[ReadingQuestionQCResult] = None
    final_score: Optional[float] = None  # Combined score from all evaluations (0-1 scale)


class UniversalEvaluationResponse(BaseModel):
    request_id: str
    evaluations: Dict[str, UniversalQuestionEvaluationScores]
    evaluation_time_seconds: float

# Configure logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Add EduBench to path
edu_bench_path = Path(__file__).parent / "EduBench" / "code" / "evaluation"
sys.path.insert(0, str(edu_bench_path))


def score_edubench_response_with_llm(task_type: str, response: str, prompt: str, question_context: Dict[str, Any] = None) -> float:
    """
    Score EduBench response using GPT-4 following EduBench's official evaluation methodology.

    Based on EduBench paper: https://arxiv.org/pdf/2505.16160
    Uses their 3 evaluation principles:
    1. Scenario Adaptability
    2. Factual & Reasoning Accuracy
    3. Pedagogical Application

    Args:
        task_type: The EduBench task type (QA, EC, IP, AG, QG, TMG)
        response: The model's response to evaluate
        prompt: The original prompt sent to the model

    Returns:
        Score from 0-10
    """
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        logger.warning("No OpenAI API key found, skipping LLM scoring")
        return 0.0

    # Build context information
    context_info = ""
    if question_context:
        if "question" in question_context:
            context_info += f"\nQuestion: {question_context['question']}"
        if "answer" in question_context:
            context_info += f"\nCorrect Answer: {question_context['answer']}"
        if "explanation" in question_context:
            context_info += f"\nExpected Explanation: {question_context['explanation'][:300]}"
        if "difficulty" in question_context:
            context_info += f"\nDifficulty Level: {question_context['difficulty']}"
        if "grade" in question_context:
            context_info += f"\nGrade Level: {question_context['grade']}"

    # EduBench official evaluation dimensions
    evaluation_prompt = f"""You are an expert evaluator following the EduBench evaluation methodology.

IMPORTANT: You are evaluating responses from EDU-Qwen2.5-7B, a 7B parameter model that tends to be:
- Verbose and repetitive (may repeat answers multiple times)
- Sometimes provides multiple JSON blocks instead of one
- May include extra explanations beyond what was asked
- May echo parts of the prompt in the response

DO NOT penalize these stylistic issues. Focus ONLY on the core educational content quality.

Evaluate the BEST interpretation of the response across these dimensions:

**1. Scenario Adaptability:**
- Instruction Following & Task Completion (did it accomplish the core task?)
- Role & Tone Consistency (appropriate educational tone?)
- Content Relevance & Scope Control (relevant to the question?)
- Scenario Element Integration (addresses the educational context?)

**2. Factual & Reasoning Accuracy:**
- Basic Factual Accuracy (is the core answer correct?)
- Domain Knowledge Accuracy (demonstrates subject understanding?)
- Reasoning Process Rigor (logical steps present?)
- Error Identification & Correction Precision (for EC tasks: correctly identifies issues?)

**3. Pedagogical Application:**
- Clarity, Simplicity & Inspiration (understandable despite verbosity?)
- Motivation, Guidance & Positive Feedback (supportive tone?)
- Personalization, Adaptation & Learning Support (helpful for learning?)
- Higher-Order Thinking & Skill Development (promotes understanding?)

**Context:**{context_info}

**Task Type:** {task_type}

**Prompt Sent to Model:**
{prompt}

**Model Response (may be verbose/repetitive):**
{response}

**Scoring Guidelines:**
Extract the BEST answer from the response (ignore repetitions). Score based on:
- 0-3: Factually wrong or completely missing the task
- 4-6: Partially correct but missing key elements or has significant errors
- 7-8: Correct and educationally sound despite verbosity
- 9-10: Excellent content with comprehensive, accurate pedagogical value

DO NOT deduct points for:
- Verbosity or repetition
- Multiple JSON blocks
- Extra explanations
- Formatting issues

DO deduct points for:
- Factual errors
- Missing required task elements
- Poor pedagogical approach
- Incorrect reasoning

Return ONLY a JSON object:
{{"score": <number 0-10>, "reasoning": "<brief explanation focusing on content quality>"}}"""

    try:
        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }

        response_obj = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": evaluation_prompt}]
            }
        )

        if response_obj.status_code == 200:
            content = response_obj.json()['choices'][0]['message']['content']
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                score = result.get('score', 0)
                logger.debug(f"{task_type} LLM score: {score}/10 - {result.get('reasoning', '')[:100]}")
                return float(score)

        logger.warning(f"Failed to get LLM score for {task_type}: {response_obj.status_code}")
        return 0.0

    except Exception as e:
        logger.error(f"Error scoring {task_type} with LLM: {e}")
        return 0.0


def evaluate_unified(
    request: GenerateQuestionsRequest,
    questions: List[GeneratedQuestion],
    task_types: List[str] = None,
    modules: EvaluationModules = None
) -> Dict[str, Any]:
    """
    Run configurable evaluations on 1-5 questions.

    Args:
        request: Question generation request
        questions: 1-5 generated questions
        task_types: DEPRECATED - EduBench task types (default: ["QA", "EC", "IP"])
        modules: Configuration for which modules to run (default: all enabled)

    Returns:
        Dict with v3_results, edubench_results, and answer_verification (conditionally included)
    """
    # Handle backward compatibility
    if modules is None:
        modules = EvaluationModules()
        logger.info("No modules specified, using default EvaluationModules configuration")

    # Prefer modules.edubench_tasks over deprecated task_types parameter
    effective_edubench_tasks = modules.edubench_tasks if modules.edubench_tasks is not None else task_types
    if effective_edubench_tasks is None:
        effective_edubench_tasks = ["QA", "EC", "IP", "AG", "QG", "TMG"]
        logger.info("No edubench_tasks specified, using default: ['QA', 'EC', 'IP', 'AG', 'QG', 'TMG']")
    else:
        logger.info(f"Using specified edubench_tasks: {effective_edubench_tasks}")

    logger.info(f"Starting evaluation with {len(questions)} questions")
    logger.info(f"Modules enabled - v3: {modules.v3_evaluation}, answer_verification: {modules.answer_verification}, edubench_tasks: {effective_edubench_tasks}, edubench_direct: {modules.edubench_direct}")

    results = {
        "v3_results": None,
        "edubench_results": None,
        "answer_verification": None,
        "edubench_direct": None
    }

    # Prepare futures based on module configuration
    all_futures = []
    v3_futures = {}
    verify_futures = {}
    edubench_futures = []
    edubench_direct_futures = {}

    # Single phase: Run enabled evaluations in parallel
    with ThreadPoolExecutor(max_workers=20) as executor:
        # Submit V3 evaluations if enabled
        if modules.v3_evaluation:
            logger.info(f"Submitting {len(questions)} V3 evaluation tasks")
            results["v3_results"] = [None] * len(questions)
            v3_futures = {i: executor.submit(call_single_shot_evaluator, q, request, len(questions))
                          for i, q in enumerate(questions)}
            all_futures.extend(v3_futures.values())

        # Submit answer verifications if enabled
        if modules.answer_verification:
            logger.info(f"Submitting {len(questions)} answer verification tasks")
            results["answer_verification"] = [None] * len(questions)
            verify_futures = {i: executor.submit(verify_answer_with_gpt4, q.question, q.answer, q.explanation)
                              for i, q in enumerate(questions)}
            all_futures.extend(verify_futures.values())

        # Submit EduBench tasks if enabled
        if effective_edubench_tasks and len(effective_edubench_tasks) > 0:
            total_edubench_tasks = len(questions) * len(effective_edubench_tasks)
            logger.info(f"Submitting {total_edubench_tasks} EduBench tasks ({len(questions)} questions × {len(effective_edubench_tasks)} task types)")
            logger.info(f"Task types: {effective_edubench_tasks}")
            results["edubench_results"] = []
            for i, q in enumerate(questions):
                for task_type in effective_edubench_tasks:
                    logger.debug(f"Submitting {task_type} task for question {i}")
                    edubench_futures.append(executor.submit(_run_edubench_task, i, task_type, q))
            all_futures.extend(edubench_futures)

        # Wait for all futures to complete (only enabled ones)
        if all_futures:
            with tqdm(total=len(all_futures), desc="Unified Evaluation") as pbar:
                for future in as_completed(all_futures):
                    pbar.update(1)

        # Collect results in order
        if modules.v3_evaluation:
            logger.info("Collecting V3 evaluation results")
            for i in range(len(questions)):
                results["v3_results"][i] = v3_futures[i].result()
            logger.info(f"Collected {len(results['v3_results'])} V3 results")

        if modules.answer_verification:
            logger.info("Collecting answer verification results")
            for i in range(len(questions)):
                results["answer_verification"][i] = verify_futures[i].result()
            logger.info(f"Collected {len(results['answer_verification'])} verification results")

        if effective_edubench_tasks and len(effective_edubench_tasks) > 0:
            logger.info(f"Collecting {len(edubench_futures)} EduBench results")
            for future in edubench_futures:
                result = future.result()
                results["edubench_results"].append(result)
            logger.info(f"Collected {len(results['edubench_results'])} EduBench task results")

            # Log task type breakdown
            task_type_counts = {}
            for result in results["edubench_results"]:
                task_type = result.get("task_type")
                task_type_counts[task_type] = task_type_counts.get(task_type, 0) + 1
            logger.info(f"EduBench task breakdown: {task_type_counts}")

        if modules.edubench_direct:
            logger.info("Collecting EduBench direct criteria evaluation results")
            for i in range(len(questions)):
                results["edubench_direct"][i] = edubench_direct_futures[i].result()
            logger.info(f"Collected {len(results['edubench_direct'])} direct evaluation results")

    logger.info("Evaluation complete")
    return results


def _run_reading_qc_task_sync(question_idx: int, question: UniversalGeneratedQuestionInput, claude_api_key: str, openai_api_key: str = None) -> Dict[str, Any]:
    """Synchronous wrapper for running reading question QC analysis."""

    async def _async_task():
        logger.debug(f"Running reading QC for question {question_idx}")

        # Initialize clients
        claude_client = anthropic.AsyncAnthropic(api_key=claude_api_key)
        openai_client = AsyncOpenAI(api_key=openai_api_key) if openai_api_key else None

        # Create analyzer
        analyzer = QuestionQCAnalyzer(
            claude_client=claude_client,
            openai_client=openai_client,
            claude_model="claude-sonnet-4-5-20250929",
            openai_model="gpt-4o"
        )

        # Convert question to the format expected by QuestionQCAnalyzer
        question_item = {
            'question_id': question.id,
            'question_type': 'MCQ' if question.type == 'mcq' else 'MP',
            'passage_text': question.additional_details or '',
            'grade': int(question.skill.grade) if question.skill and question.skill.grade.isdigit() else 5,
            'structured_content': {
                'question': question.question,
                'choices': question.answer_options or {},
                'correct_answer': question.answer,
                'CCSS': question.skill.title if question.skill else '',
                'CCSS_description': question.skill.description if question.skill else '',
                'DOK': question.skill.difficulty if question.skill else 'medium'
            }
        }

        try:
            result = await analyzer.analyze_question(question_item, semaphore=None)
            return {
                'question_idx': question_idx,
                'result': result
            }
        except Exception as e:
            logger.error(f"Error running reading QC for question {question_idx}: {e}")
            return {
                'question_idx': question_idx,
                'result': None,
                'error': str(e)
            }

    # Run the async function in a new event loop
    return asyncio.run(_async_task())


def _run_edubench_task(question_idx: int, task_type: str, question: UniversalGeneratedQuestionInput) -> Dict[str, Any]:
    """Run single EduBench task - just returns raw response like batch_edubench."""
    logger.debug(f"Running {task_type} task for question {question_idx}")

    # Extract explanation - always present as required field
    detailed_explanation = question.answer_explanation

    # Build prompt based on task type
    if task_type == "QA":
        prompt = TASK_PROMPT_TEMPLATES["QA"](question.question)
    elif task_type == "EC":
        prompt = TASK_PROMPT_TEMPLATES["EC"](question.question, question.answer)
    elif task_type == "IP":
        base_prompt = TASK_PROMPT_TEMPLATES["IP"](question.question)
        prompt = f"{base_prompt}\n\nReference scaffolding (detailed step-by-step guidance):\n{detailed_explanation}"
    elif task_type == "AG":
        base_prompt = TASK_PROMPT_TEMPLATES["AG"](question.question, question.answer)
        prompt = f"{base_prompt}\n\nReference explanation:\n{detailed_explanation}"
    elif task_type == "QG":
        # Extract knowledge point from skill (optional field)
        if question.skill:
            knowledge_point = question.skill.title
            subject = question.skill.subject
            level = question.skill.difficulty
        else:
            # Fallback if no skill provided
            knowledge_point = question.question.split('.')[0] if '.' in question.question else question.question[:50]
            subject = "mathematics"
            level = "medium"

        question_type = question.type  # "mcq" or "fill-in"
        prompt = TASK_PROMPT_TEMPLATES["QG"](knowledge_point, subject, question_type, level)
    elif task_type == "TMG":
        # Extract knowledge point from skill (optional field)
        if question.skill:
            knowledge_point = question.skill.title
        else:
            # Fallback if no skill provided
            knowledge_point = "General educational content"

        base_prompt = TASK_PROMPT_TEMPLATES["TMG"](knowledge_point)
        prompt = f"{base_prompt}\n\nReference scaffolding example:\n{detailed_explanation}"
    else:
        prompt = ""

    response = get_normal_answer(prompt, 'EDU-Qwen2.5-7B')

    # an llm call to score the response
    evaluation = score_edubench_response_with_llm(task_type, response, prompt, question_context={
        "question": question.question,
        "answer": question.answer,
        "explanation": detailed_explanation,
        "difficulty": question.skill.difficulty if question.skill else "medium",
        "grade": question.skill.grade if question.skill else "unknown"
    })

    result = {
        "question_idx": question_idx,
        "task_type": task_type,
        "response": response,
        "evaluation": evaluation,
    }

    return result


def evaluate_unified_with_response(
    request: GenerateQuestionsRequest,
    questions: List[GeneratedQuestion],
    task_types: List[str] = None,
    modules: EvaluationModules = None
) -> Dict[str, Any]:
    """
    High-level function that runs evaluation and formats clean API response.

    Args:
        request: Question generation request
        questions: Generated questions to evaluate
        task_types: DEPRECATED - Use modules.edubench_tasks instead
        modules: Configuration for which evaluation modules to run

    Returns a dict ready for API response with:
    - request_id
    - overall_scores
    - v3_scores (clean, optional)
    - answer_verification (clean, optional)
    - edubench_results (optional)
    - summary
    """
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Handle backward compatibility
    if modules is None:
        modules = EvaluationModules()

    # Run core evaluation with module configuration
    results = evaluate_unified(request, questions, task_types, modules)

    # Calculate overall scores from v3 results (if enabled)
    v3_avg = 0.0
    if modules.v3_evaluation and results["v3_results"]:
        v3_overall_scores = []
        for v3_result in results["v3_results"]:
            if v3_result and "overall" in v3_result:
                v3_overall_scores.append(v3_result["overall"])
        v3_avg = sum(v3_overall_scores) / len(v3_overall_scores) if v3_overall_scores else 0.0

    # Calculate answer verification rate (if enabled)
    answer_correctness_rate = 0.0
    if modules.answer_verification and results["answer_verification"]:
        correct_answers = sum(1 for av in results["answer_verification"] if av and av.get("is_correct") == True)
        answer_correctness_rate = correct_answers / len(results["answer_verification"]) if results["answer_verification"] else 0.0

    # Extract only scores from v3_results (remove verbose details) if enabled
    clean_v3_scores = None
    if modules.v3_evaluation and results["v3_results"]:
        clean_v3_scores = []
        for v3_result in results["v3_results"]:
            if v3_result and "scores" in v3_result:
                # Convert EvaluationDimension enum keys to strings
                clean_scores = {
                    (k.value if hasattr(k, 'value') else str(k)): v
                    for k, v in v3_result["scores"].items()
                }
                clean_scores["overall"] = v3_result.get("overall", 0.0)
                clean_scores["recommendation"] = v3_result.get("recommendation", "revise")
                clean_v3_scores.append(clean_scores)

    # Simplify answer verification (keep only essential fields) if enabled
    clean_answer_verification = None
    if modules.answer_verification and results["answer_verification"]:
        clean_answer_verification = [
            {
                "is_correct": av.get("is_correct", False),
                "confidence": av.get("confidence", 0)
            }
            for av in results["answer_verification"]
        ]

    # EduBench direct criteria evaluation (already ran in parallel in evaluate_unified)
    edubench_direct_evaluations = results.get("edubench_direct")

    # EduBench results and scoring (if enabled)
    edubench_results = results.get("edubench_results") if results.get("edubench_results") else None
    edubench_scores = None

    # Create score lookup dictionary to avoid re-scoring
    edubench_score_lookup = {}  # {(question_idx, task_type): score}

    if edubench_results:
        logger.info(f"Starting to score {len(edubench_results)} EduBench results with LLM in parallel")

        # Score each result with LLM in parallel using ThreadPoolExecutor
        qa_scores = []
        ec_scores = []
        ip_scores = []
        ag_scores = []
        qg_scores = []
        tmg_scores = []

        # Prepare scoring tasks
        def score_single_result(result):
            task_type = result.get("task_type")
            response = result.get("response", "")
            prompt = result.get("prompt", "")
            question_idx = result.get("question_idx", 0)

            # Build question context for scorer
            question_context = None
            if question_idx < len(questions):
                q = questions[question_idx]
                question_context = {
                    "question": q.question,
                    "answer": q.answer,
                    "explanation": q.explanation,
                    "difficulty": getattr(q, 'difficulty', 'medium'),
                    "grade": getattr(request, 'grade', 'unknown')
                }

            # Score using LLM with full context
            score = score_edubench_response_with_llm(task_type, response, prompt, question_context)
            logger.debug(f"{task_type} scored {score}/10")
            return (question_idx, task_type, score)

        # Execute scoring in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            scoring_futures = [executor.submit(score_single_result, result) for result in edubench_results]

            with tqdm(total=len(scoring_futures), desc="Scoring EduBench results") as pbar:
                for future in as_completed(scoring_futures):
                    question_idx, task_type, score = future.result()
                    pbar.update(1)

                    # Store in lookup for per-question use
                    edubench_score_lookup[(question_idx, task_type)] = score

                    # Collect scores by task type for aggregates
                    if task_type == "QA" and score > 0:
                        qa_scores.append(score)
                    elif task_type == "EC" and score > 0:
                        ec_scores.append(score)
                    elif task_type == "IP" and score > 0:
                        ip_scores.append(score)
                    elif task_type == "AG" and score > 0:
                        ag_scores.append(score)
                    elif task_type == "QG" and score > 0:
                        qg_scores.append(score)
                    elif task_type == "TMG" and score > 0:
                        tmg_scores.append(score)

        # Calculate averages
        qa_avg = sum(qa_scores) / len(qa_scores) if qa_scores else 0.0
        ec_avg = sum(ec_scores) / len(ec_scores) if ec_scores else 0.0
        ip_avg = sum(ip_scores) / len(ip_scores) if ip_scores else 0.0
        ag_avg = sum(ag_scores) / len(ag_scores) if ag_scores else 0.0
        qg_avg = sum(qg_scores) / len(qg_scores) if qg_scores else 0.0
        tmg_avg = sum(tmg_scores) / len(tmg_scores) if tmg_scores else 0.0

        logger.info(f"Score counts - QA: {len(qa_scores)}, EC: {len(ec_scores)}, IP: {len(ip_scores)}, AG: {len(ag_scores)}, QG: {len(qg_scores)}, TMG: {len(tmg_scores)}")
        logger.info(f"Score averages - QA: {qa_avg:.2f}, EC: {ec_avg:.2f}, IP: {ip_avg:.2f}, AG: {ag_avg:.2f}, QG: {qg_avg:.2f}, TMG: {tmg_avg:.2f}")

        # Calculate weighted score with equal weight for all tasks
        all_task_scores = [qa_scores, ec_scores, ip_scores, ag_scores, qg_scores, tmg_scores]
        valid_tasks = sum([1 for scores in all_task_scores if len(scores) > 0])
        if valid_tasks > 0:
            # Simple average of all available task scores
            weighted_score = (qa_avg + ec_avg + ip_avg + ag_avg + qg_avg + tmg_avg) / 6
        else:
            weighted_score = 0.0

        logger.info(f"Calculated weighted score: {weighted_score:.2f} (based on {valid_tasks} task types)")

        edubench_scores = {
            'qa_average': qa_avg,
            'qa_count': len(qa_scores),
            'ec_average': ec_avg,
            'ec_count': len(ec_scores),
            'ip_average': ip_avg,
            'ip_count': len(ip_scores),
            'ag_average': ag_avg,
            'ag_count': len(ag_scores),
            'qg_average': qg_avg,
            'qg_count': len(qg_scores),
            'tmg_average': tmg_avg,
            'tmg_count': len(tmg_scores),
            'weighted_score': weighted_score,
            'total_scored': len(qa_scores) + len(ec_scores) + len(ip_scores) + len(ag_scores) + len(qg_scores) + len(tmg_scores)
        }

    # Build overall scores object
    overall_scores = {
        "total_questions": len(questions)
    }

    if modules.v3_evaluation:
        overall_scores["v3_average"] = v3_avg

    if modules.answer_verification:
        overall_scores["answer_correctness_rate"] = answer_correctness_rate

    if edubench_results:
        overall_scores["total_edubench_tasks"] = len(edubench_results)

    if edubench_scores:
        overall_scores["edubench_qa_average"] = edubench_scores["qa_average"]
        overall_scores["edubench_ec_average"] = edubench_scores["ec_average"]
        overall_scores["edubench_ip_average"] = edubench_scores["ip_average"]
        overall_scores["edubench_ag_average"] = edubench_scores["ag_average"]
        overall_scores["edubench_qg_average"] = edubench_scores["qg_average"]
        overall_scores["edubench_tmg_average"] = edubench_scores["tmg_average"]
        overall_scores["edubench_weighted_score"] = edubench_scores["weighted_score"]

    # Add direct EduBench criteria evaluation scores (if enabled)
    if edubench_direct_evaluations:
        direct_scores = [e.get('overall_score', 0) for e in edubench_direct_evaluations if e]
        overall_scores["edubench_direct_average"] = sum(direct_scores) / len(direct_scores) if direct_scores else 0.0

    # Determine recommendation based on enabled metrics
    recommendation = "accept"
    if modules.v3_evaluation and v3_avg < 0.85:
        recommendation = "revise"
    if modules.answer_verification and answer_correctness_rate < 0.8:
        recommendation = "revise"

    # Build summary
    summary = {
        "evaluation_time_seconds": time.time() - start_time,
        "questions_evaluated": len(questions),
        "recommendation": recommendation,
        "modules_enabled": {
            "v3_evaluation": modules.v3_evaluation,
            "answer_verification": modules.answer_verification,
            "edubench_tasks": modules.edubench_tasks if modules.edubench_tasks else [],
            "edubench_direct": modules.edubench_direct
        }
    }

    # Add EduBench scoring details to summary if available
    if edubench_scores:
        summary["edubench_scoring"] = {
            "qa_count": edubench_scores["qa_count"],
            "ec_count": edubench_scores["ec_count"],
            "ip_count": edubench_scores["ip_count"],
            "ag_count": edubench_scores["ag_count"],
            "qg_count": edubench_scores["qg_count"],
            "tmg_count": edubench_scores["tmg_count"],
            "total_scored": edubench_scores["total_scored"]
        }

    # Import DTOs once outside the loop
    from src.dto.question_generation import (
        PerQuestionV3Score,
        PerQuestionAnswerVerification,
        PerQuestionEdubenchScores,
        PerQuestionResult
    )

    # Build per-question detailed results with pass/fail status
    def process_single_question(i, question):
        """Process a single question to build its result object."""
        # Extract V3 scores for this question
        v3_score_obj = None
        if modules.v3_evaluation and clean_v3_scores and i < len(clean_v3_scores):
            v3_data = clean_v3_scores[i]
            v3_score_obj = PerQuestionV3Score(
                correctness=v3_data.get("correctness"),
                grade_alignment=v3_data.get("grade_alignment"),
                difficulty_alignment=v3_data.get("difficulty_alignment"),
                language_quality=v3_data.get("language_quality"),
                pedagogical_value=v3_data.get("pedagogical_value"),
                explanation_quality=v3_data.get("explanation_quality"),
                instruction_adherence=v3_data.get("instruction_adherence"),
                format_compliance=v3_data.get("format_compliance"),
                query_relevance=v3_data.get("query_relevance"),
                di_compliance=v3_data.get("di_compliance"),
                overall=v3_data.get("overall", 0.0),
                recommendation=v3_data.get("recommendation", "revise")
            )

        # Extract answer verification for this question
        answer_verif_obj = None
        if modules.answer_verification and clean_answer_verification and i < len(clean_answer_verification):
            av_data = clean_answer_verification[i]
            answer_verif_obj = PerQuestionAnswerVerification(
                is_correct=av_data.get("is_correct", False),
                confidence=av_data.get("confidence", 0)
            )

        # Extract EduBench scores for this question (using cached scores from lookup)
        edubench_score_obj = None
        if edubench_score_lookup:
            # Retrieve scores from lookup dictionary (already computed in parallel)
            qa_score = edubench_score_lookup.get((i, "QA"))
            ec_score = edubench_score_lookup.get((i, "EC"))
            ip_score = edubench_score_lookup.get((i, "IP"))
            ag_score = edubench_score_lookup.get((i, "AG"))
            qg_score = edubench_score_lookup.get((i, "QG"))
            tmg_score = edubench_score_lookup.get((i, "TMG"))

            # Calculate average for this question
            scores_list = [s for s in [qa_score, ec_score, ip_score, ag_score, qg_score, tmg_score] if s is not None]
            avg_score = sum(scores_list) / len(scores_list) if scores_list else None

            if any(s is not None for s in [qa_score, ec_score, ip_score, ag_score, qg_score, tmg_score]):
                edubench_score_obj = PerQuestionEdubenchScores(
                    qa_score=qa_score,
                    ec_score=ec_score,
                    ip_score=ip_score,
                    ag_score=ag_score,
                    qg_score=qg_score,
                    tmg_score=tmg_score,
                    average_score=avg_score
                )

        # Extract EduBench direct score
        edubench_direct_score = None
        if edubench_direct_evaluations and i < len(edubench_direct_evaluations):
            direct_eval = edubench_direct_evaluations[i]
            if direct_eval:
                edubench_direct_score = direct_eval.get("overall_score")

        # Determine pass/fail and calculate overall quality score
        failure_reasons = []
        quality_scores = []

        # V3 evaluation check (threshold: 0.85)
        if v3_score_obj:
            quality_scores.append(v3_score_obj.overall)
            if v3_score_obj.overall < 0.85:
                failure_reasons.append(f"V3 score {v3_score_obj.overall:.2%} below threshold (85%)")

        # Answer verification check
        if answer_verif_obj:
            # Convert to quality score (1.0 if correct, 0.0 if incorrect)
            answer_quality = 1.0 if answer_verif_obj.is_correct else 0.0
            quality_scores.append(answer_quality)
            if not answer_verif_obj.is_correct:
                failure_reasons.append(f"Answer verification failed (confidence: {answer_verif_obj.confidence})")

        # EduBench scores check (threshold: 7.0 out of 10)
        if edubench_score_obj and edubench_score_obj.average_score is not None:
            # Normalize to 0-1 scale
            edubench_normalized = edubench_score_obj.average_score / 10.0
            quality_scores.append(edubench_normalized)
            if edubench_score_obj.average_score < 7.0:
                failure_reasons.append(f"EduBench average {edubench_score_obj.average_score:.1f}/10 below threshold (7.0)")

        # EduBench direct check (threshold: 7.0 out of 10)
        if edubench_direct_score is not None:
            direct_normalized = edubench_direct_score / 10.0
            quality_scores.append(direct_normalized)
            if edubench_direct_score < 7.0:
                failure_reasons.append(f"EduBench direct {edubench_direct_score:.1f}/10 below threshold (7.0)")

        # Calculate overall quality score
        overall_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        # Determine pass/fail
        passed = len(failure_reasons) == 0

        return PerQuestionResult(
            question_index=i,
            question_text=question.question,
            answer=question.answer,
            v3_score=v3_score_obj,
            answer_verification=answer_verif_obj,
            edubench_scores=edubench_score_obj,
            edubench_direct_score=edubench_direct_score,
            passed=passed,
            failure_reasons=failure_reasons,
            overall_quality_score=overall_quality_score
        )

    # Process all questions in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        per_question_futures = {executor.submit(process_single_question, i, q): i
                               for i, q in enumerate(questions)}

        per_question_results = [None] * len(questions)
        for future in as_completed(per_question_futures):
            result = future.result()
            per_question_results[result.question_index] = result

    # Add pass/fail summary to overall scores
    total_passed = sum(1 for pqr in per_question_results if pqr.passed)
    total_failed = len(per_question_results) - total_passed
    overall_scores["questions_passed"] = total_passed
    overall_scores["questions_failed"] = total_failed
    overall_scores["pass_rate"] = total_passed / len(per_question_results) if per_question_results else 0.0

    # Build clean response
    return {
        "request_id": request_id,
        "overall_scores": overall_scores,
        "per_question_results": per_question_results,
        "v3_scores": clean_v3_scores,
        "answer_verification": clean_answer_verification,
        "edubench_results": edubench_results,
        "edubench_scores": edubench_scores,
        "edubench_direct": edubench_direct_evaluations,
        "summary": summary
    }


def universal_unified_benchmark(request: UniversalEvaluationRequest) -> UniversalEvaluationResponse:
    """
    Main entry point for universal evaluation.
    Processes each question and organizes results by question ID.
    """

    start_time = time.time()
    request_id = str(uuid.uuid4())

    logger.info(f"Universal evaluation request {request_id} with {len(request.generated_questions)} questions")

    modules_to_use = request.submodules_to_run
    evaluations = {}

    for question in request.generated_questions:
        evaluations[question.id] = UniversalQuestionEvaluationScores()

    # Run all enabled modules in parallel
    questions = request.generated_questions
    effective_edubench_tasks = ["QA", "EC", "IP", "AG", "QG", "TMG"]

    # Prepare storage for results
    edubench_task_results = []
    internal_eval_results = []
    verification_results = []
    reading_qc_results = []

    # Get API keys for reading QC
    claude_api_key = os.getenv('ANTHROPIC_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    with ThreadPoolExecutor(max_workers=50) as executor:
        all_futures = []

        # Submit EduBench tasks if enabled
        if "directionai_edubench" in modules_to_use:
            logger.info(f"Submitting EduBench evaluation with {len(effective_edubench_tasks)} tasks for {len(questions)} questions")
            for i, q in enumerate(questions):
                for task_type in effective_edubench_tasks:
                    future = executor.submit(_run_edubench_task, i, task_type, q)
                    all_futures.append(('directionai_edubench', future))

        # Submit internal evaluator tasks if enabled
        if "internal_evaluator" in modules_to_use:
            logger.info(f"Submitting {len(questions)} internal evaluator tasks")
            for i, q in enumerate(questions):
                future = executor.submit(call_single_shot_evaluator, q, len(questions))
                all_futures.append(('internal_evaluator', i, future))

        # Submit answer verification tasks if enabled
        if "answer_verification" in modules_to_use:
            logger.info(f"Submitting {len(questions)} answer verification tasks")
            for i, q in enumerate(questions):
                future = executor.submit(verify_answer_with_gpt4, q.question, q.answer, q.answer_explanation)
                all_futures.append(('answer_verification', i, future))

        # Submit reading QC tasks if enabled and dependencies available
        if "reading_question_qc" in modules_to_use:
            logger.info(f"Submitting {len(questions)} reading QC tasks")
            for i, q in enumerate(questions):
                future = executor.submit(_run_reading_qc_task_sync, i, q, claude_api_key, openai_api_key)
                all_futures.append(('reading_question_qc', i, future))

        # Collect all results with a single progress bar
        if all_futures:
            logger.info(f"Running {len(all_futures)} total tasks in parallel")
            with tqdm(total=len(all_futures), desc="Running All Evaluation Tasks") as pbar:
                for future_info in all_futures:
                    module_type = future_info[0]

                    if module_type == 'directionai_edubench':
                        _, future = future_info
                        result = future.result()
                        edubench_task_results.append(result)
                    elif module_type == 'internal_evaluator':
                        _, question_idx, future = future_info
                        result = future.result()
                        internal_eval_results.append((question_idx, result))
                    elif module_type == 'answer_verification':
                        _, question_idx, future = future_info
                        result = future.result()
                        verification_results.append((question_idx, result))
                    elif module_type == 'reading_question_qc':
                        _, question_idx, future = future_info
                        result = future.result()
                        reading_qc_results.append((question_idx, result))

                    pbar.update(1)

    # Process EduBench results
    if "directionai_edubench" in modules_to_use and edubench_task_results:
        logger.info(f"Processing {len(edubench_task_results)} EduBench task results")

        # Organize results by question
        question_scores = {}  # {question_idx: {task_type: score}}

        for result in edubench_task_results:
            question_idx = result['question_idx']
            task_type = result['task_type']
            evaluation_score = result['evaluation']

            if question_idx not in question_scores:
                question_scores[question_idx] = {}

            question_scores[question_idx][task_type] = evaluation_score

        # Build EdubenchScores for each question
        for i, question in enumerate(questions):
            scores = question_scores.get(i, {})

            edubench_scores = EdubenchScores(
                qa_score=scores.get('QA', 0.0),
                ec_score=scores.get('EC', 0.0),
                ip_score=scores.get('IP', 0.0),
                ag_score=scores.get('AG', 0.0),
                qg_score=scores.get('QG', 0.0),
                tmg_score=scores.get('TMG', 0.0),
                average_score=sum(scores.values()) / len(scores) if scores else 0.0
            )

            if question.id in evaluations:
                evaluations[question.id].directionai_edubench = edubench_scores

        logger.info(f"Built EduBench scores for {len(question_scores)} questions")

    # Process internal evaluator results
    if "internal_evaluator" in modules_to_use and internal_eval_results:
        logger.info(f"Processing {len(internal_eval_results)} internal evaluation results")

        # Sort by question index to maintain order
        internal_eval_results.sort(key=lambda x: x[0])

        for question_idx, result_dict in internal_eval_results:
            question = questions[question_idx]
            if question.id in evaluations:
                # Convert dict to Pydantic model
                try:
                    # Convert EvaluationDimension keys to strings and extract scores
                    scores_dict = {
                        k.value if hasattr(k, 'value') else str(k): v
                        for k, v in result_dict['scores'].items()
                    }

                    internal_result = InternalEvaluatorResult(
                        scores=InternalEvaluatorScores(**scores_dict),
                        issues=result_dict.get('issues', []),
                        strengths=result_dict.get('strengths', []),
                        overall=result_dict.get('overall', 0.0),
                        recommendation=result_dict.get('recommendation', 'revise'),
                        suggested_improvements=result_dict.get('suggested_improvements', []),
                        di_scores=DIScores(**result_dict.get('di_scores', {})),
                        section_evaluations=SectionEvaluations(
                            question=SectionEvaluation(**result_dict['section_evaluations']['question']),
                            scaffolding=SectionEvaluation(**result_dict['section_evaluations']['scaffolding'])
                        )
                    )
                    evaluations[question.id].internal_evaluator = internal_result
                except Exception as e:
                    logger.error(f"Error converting internal evaluator result for question {question_idx}: {e}")
                    # Keep the raw dict if conversion fails
                    evaluations[question.id].internal_evaluator = None

        logger.info(f"Assigned internal evaluator results to {len(internal_eval_results)} questions")

    # Process answer verification results
    if "answer_verification" in modules_to_use and verification_results:
        logger.info(f"Processing {len(verification_results)} answer verification results")

        # Sort by question index to maintain order
        verification_results.sort(key=lambda x: x[0])

        for question_idx, result_dict in verification_results:
            question = questions[question_idx]
            if question.id in evaluations:
                # Convert dict to Pydantic model
                try:
                    verification_result = AnswerVerificationResult(
                        is_correct=result_dict.get('is_correct', False),
                        correct_answer=result_dict.get('correct_answer', ''),
                        confidence=result_dict.get('confidence', 0),
                        reasoning=result_dict.get('reasoning', '')
                    )
                    evaluations[question.id].answer_verification = verification_result
                except Exception as e:
                    logger.error(f"Error converting answer verification result for question {question_idx}: {e}")
                    # Keep None if conversion fails
                    evaluations[question.id].answer_verification = None

        logger.info(f"Assigned answer verification results to {len(verification_results)} questions")

    # Process reading QC results
    if "reading_question_qc" in modules_to_use and reading_qc_results:
        logger.info(f"Processing {len(reading_qc_results)} reading QC results")

        # Sort by question index to maintain order
        reading_qc_results.sort(key=lambda x: x[0])

        for question_idx, result_dict in reading_qc_results:
            question = questions[question_idx]
            if question.id in evaluations:
                # Extract and convert the result
                try:
                    qc_result = result_dict.get('result')
                    if qc_result and 'error' not in result_dict:
                        # Extract scores
                        overall_score = qc_result.get('overall_score', 0.0)

                        # Extract checks - the 'checks' field contains all check results
                        all_checks = qc_result.get('checks', {})

                        # Separate distractor and question checks based on category
                        distractor_checks = {k: v for k, v in all_checks.items() if v.get('category') == 'distractor'}
                        question_checks = {k: v for k, v in all_checks.items() if v.get('category') == 'question'}

                        # Determine if passed (threshold: 0.8)
                        passed = overall_score >= 0.8

                        reading_qc_obj = ReadingQuestionQCResult(
                            overall_score=overall_score,
                            distractor_checks=distractor_checks,
                            question_checks=question_checks,
                            passed=passed
                        )
                        evaluations[question.id].reading_question_qc = reading_qc_obj
                    else:
                        logger.warning(f"Reading QC result for question {question_idx} is None or has error")
                        evaluations[question.id].reading_question_qc = None
                except Exception as e:
                    logger.error(f"Error converting reading QC result for question {question_idx}: {e}")
                    evaluations[question.id].reading_question_qc = None

        logger.info(f"Assigned reading QC results to {len(reading_qc_results)} questions")

    # Calculate final scores for each question
    logger.info("Calculating final combined scores for each question")
    for question_id, evaluation in evaluations.items():
        scores_to_combine = []

        # Debug: Log what we have for this question
        has_internal = evaluation.internal_evaluator is not None
        has_verification = evaluation.answer_verification is not None
        has_edubench = evaluation.directionai_edubench is not None
        has_reading_qc = evaluation.reading_question_qc is not None

        logger.info(f"Question {question_id}: internal_evaluator={has_internal}, answer_verification={has_verification}, directionai_edubench={has_edubench}, reading_question_qc={has_reading_qc}")

        # Internal evaluator: already on 0-1 scale
        if evaluation.internal_evaluator:
            internal_score = evaluation.internal_evaluator.overall
            scores_to_combine.append(internal_score)
            logger.info(f"  - Internal evaluator: {internal_score:.3f}")

        # Answer verification: convert boolean to 0-1 scale
        if evaluation.answer_verification:
            answer_score = 1.0 if evaluation.answer_verification.is_correct else 0.0
            scores_to_combine.append(answer_score)
            logger.info(f"  - Answer verification: {answer_score:.3f} (is_correct={evaluation.answer_verification.is_correct})")

        # EduBench: convert from 0-10 to 0-1 scale
        if evaluation.directionai_edubench:
            edubench_normalized = evaluation.directionai_edubench.average_score / 10.0
            scores_to_combine.append(edubench_normalized)
            logger.info(f"  - EduBench: {edubench_normalized:.3f} (avg={evaluation.directionai_edubench.average_score:.2f}/10)")

        # Reading QC: already on 0-1 scale
        if evaluation.reading_question_qc:
            reading_qc_score = evaluation.reading_question_qc.overall_score
            scores_to_combine.append(reading_qc_score)
            logger.info(f"  - Reading QC: {reading_qc_score:.3f}")

        # Calculate weighted average of all available scores
        if scores_to_combine:
            evaluation.final_score = sum(scores_to_combine) / len(scores_to_combine)
            logger.info(f"Question {question_id}: final_score = {evaluation.final_score:.3f} (from {len(scores_to_combine)} modules)")
        else:
            evaluation.final_score = None
            logger.warning(f"Question {question_id}: No scores available to calculate final_score - all evaluations are None!")

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f"Universal evaluation request {request_id} completed in {elapsed_time:.2f} seconds")

    return UniversalEvaluationResponse(
        request_id=request_id,
        evaluations=evaluations,
        evaluation_time_seconds=elapsed_time
    )


if __name__ == "__main__":    
    with open("src/evaluator/example.json", "r") as f:
        example_data = json.load(f)
    example_request = UniversalEvaluationRequest(**example_data)
    response = universal_unified_benchmark(example_request)
    print(response.model_dump_json(indent=2))