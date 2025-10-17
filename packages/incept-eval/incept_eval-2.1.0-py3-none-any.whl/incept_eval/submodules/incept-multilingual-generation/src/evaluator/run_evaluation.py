#!/usr/bin/env python3
"""
Standalone evaluation runner for CI/CD pipeline.
Generates questions using the actual API and evaluates them using the v2 evaluator.
Supports multiple test configurations for comprehensive evaluation.
"""

import argparse
import json
import logging
import os
import sys
import uuid
import asyncio
import httpx
from datetime import datetime
from pathlib import Path

import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.dto.question_generation import (
    GenerateQuestionsRequest,
    GenerateQuestionResponse,
    GeneratedQuestion,
    EvaluationInfo
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration templates
EVAL_CONFIGS = {
    "algebra_english": {
        "grade": 8,
        "count": 3,
        "subject": "mathematics",
        "language": "english",
        "translate": False,
        "model": "openai",
        "evaluate": True,
        "instructions": "Generate algebra questions",
        "skill": {
            "id": lambda: f"alg_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}",
            "title": "Solving algebra Equations",
            "unit_name": "algebra Unit 1",
            "lesson_title": "Introduction to algebra Equations"
        }
    },
    "geometry_arabic": {
        "grade": 8,
        "count": 3,
        "subject": "mathematics",
        "language": "arabic",
        "translate": False,
        "model": "openai",
        "evaluate": True,
        "instructions": "Generate geometry questions",
        "skill": {
            "id": lambda: f"geo_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}",
            "title": "Solving geometry problems",
            "unit_name": "Trigonometry Unit 1",
            "lesson_title": " Pythagorean theorem"
        }
    }
}

async def call_api_from_config(config_name, api_url="https://uae-poc.inceptapi.com"):
    """Call the actual API endpoint with configuration."""

    if config_name not in EVAL_CONFIGS:
        raise ValueError(f"Unknown configuration: {config_name}. Available: {list(EVAL_CONFIGS.keys())}")

    config = EVAL_CONFIGS[config_name].copy()

    # Generate random ID for skill
    if callable(config["skill"]["id"]):
        config["skill"]["id"] = config["skill"]["id"]()

    # Create request based on config
    request_data = {
        "grade": config["grade"],
        "count": config["count"],
        "subject": config["subject"],
        "language": config["language"],
        "translate": config["translate"],
        "model": config["model"],
        "evaluate": config["evaluate"],
        "instructions": config["instructions"],
        "skill": config["skill"],
        "question_type": "mcq",
        "difficulty": "medium"
    }

    # Create request object for evaluation
    request = GenerateQuestionsRequest(
        topic=config["instructions"].replace("Generate ", "").replace(" questions", ""),
        subject=config["subject"],
        grade=str(config["grade"]),
        language=config["language"],
        question_type="mcq",
        difficulty="medium",
        count=config["count"],
        instructions=config["instructions"]
    )

    try:
        logger.info(f"Calling API endpoint: {api_url}/v1/generate_questions")
        logger.info(f"Request payload: {json.dumps(request_data, indent=2)}")

        # Get API key from environment
        api_key = os.getenv("INCEPT_API_KEY")
        if not api_key:
            raise ValueError("INCEPT_API_KEY environment variable is required for API authentication")
        
        # Prepare headers with Bearer token
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 10 minute timeout for question generation
        response = requests.post(
            f"{api_url}/v1/generate_questions",
            json=request_data,
            headers=headers,
            timeout=600
        )
        response_data = response.json()
        response.raise_for_status()
        # Convert to GenerateQuestionResponse object
        questions = [
            GeneratedQuestion(**q) for q in response_data.get("data", [])
        ]

        # Extract evaluation if present
        evaluation = None
        if "evaluation" in response_data and response_data["evaluation"]:
            evaluation = EvaluationInfo(**response_data["evaluation"])

        api_response = GenerateQuestionResponse(
            request_id=response_data.get("request_id", f"eval_{config_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
            data=questions,
            total_questions=response_data.get("total_questions", len(questions)),
            grade=response_data.get("grade", config["grade"]),
            evaluation=evaluation
        )

        return request, api_response, config

    except Exception as e:
        logger.error(f"Error calling API: {e}")
        raise

def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in your GitHub repository secrets")
        return False

    return True

def main():
    """Main evaluation runner."""
    parser = argparse.ArgumentParser(description="Run question evaluator with specific configuration")
    parser.add_argument("--config-name", choices=list(EVAL_CONFIGS.keys()),
                       help="Configuration to use for evaluation")
    parser.add_argument("--api-url", default="https://uae-poc.inceptapi.com",
                       help="API URL to call (default: https://uae-poc.inceptapi.com)")
    args = parser.parse_args()

    config_name = args.config_name or "algebra_english"  # Default

    logger.info(f"Starting evaluation runner for CI/CD pipeline with config: {config_name}")
    logger.info(f"API URL: {args.api_url}")

    # Check environment
    if not check_environment():
        sys.exit(1)

    try:
        # Call actual API
        logger.info(f"Calling API for {config_name}")
        request, response, config = asyncio.run(call_api_from_config(config_name, args.api_url))

        # Extract evaluation from API response
        evaluation = response.evaluation
        if not evaluation:
            logger.warning("No evaluation data in API response")
            evaluation = EvaluationInfo(
                overall_score=0.0,
                report="No evaluation available"
            )

        # Create baseline structure for GitHub workflow compatibility
        baseline_file = f"baseline_evaluation_{config_name}.json"
        baseline_data = {
            "evaluations": [{
                "timestamp": datetime.now().isoformat(),
                "request_id": response.request_id,
                "overall_score": evaluation.overall_score or 0.0,
                "total_issues": 0,
                "quality_distribution": {
                    "accept": response.total_questions if evaluation.overall_score and evaluation.overall_score > 0.8 else 0,
                    "revise": response.total_questions if evaluation.overall_score and 0.3 < evaluation.overall_score <= 0.8 else 0,
                    "reject": response.total_questions if evaluation.overall_score and evaluation.overall_score <= 0.3 else 0
                }
            }]
        }

        # Save baseline for workflow
        with open(baseline_file, "w") as f:
            json.dump(baseline_data, f, indent=2)

        # Save evaluation report
        report_filename = f"evaluation_report_{config_name}_{response.request_id}.md"
        with open(report_filename, "w", encoding="utf-8") as f:
            f.write(evaluation.report or "No evaluation report available")

        logger.info(f"Evaluation complete. Report saved to {report_filename}")

        # Print summary
        print(f"\n{'='*60}")
        print(f"EVALUATION: {config_name}")
        print(f"Score: {evaluation.overall_score:.2%}" if evaluation.overall_score else "Score: N/A")
        print(f"Report saved to: {report_filename}")
        print(f"{'='*60}")

        # Exit with appropriate code
        sys.exit(0)

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()