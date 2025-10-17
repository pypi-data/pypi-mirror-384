"""
EduBench Model Interface

This module provides functions to interact with the EDU-Qwen2.5-7B model
via HuggingFace API. It does NOT contain scoring logic - all scoring is
handled by unified_evaluator.py using LLM-as-judge methodology.

Functions:
- query_hf_model: Low-level HuggingFace API call with retry logic
- get_normal_answer: Call EDU-Qwen2.5-7B and return response
- verify_answer_with_gpt4: Verify answer correctness (used by unified_evaluator)
"""

import os
import re
import json
import requests


def query_hf_model(payload, max_retries=3, timeout=500):
    """Query the HuggingFace model endpoint with retry logic"""
    # Try multiple sources for the token
    HUGGINGFACE_TOKEN = (
        os.getenv('HUGGINGFACE_TOKEN') or
        os.getenv('HUGGINGFACE_TOKEN') or
        os.getenv('HF_API_TOKEN')
    )

    if not HUGGINGFACE_TOKEN:
        print("Warning: No HuggingFace token found. Checked: HUGGINGFACE_TOKEN, HUGGINGFACE_TOKEN, HF_API_TOKEN")
        print("Please set one of these environment variables with your HuggingFace API token.")
        raise ValueError("HuggingFace API token not found in environment variables")

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {HUGGINGFACE_TOKEN}",
        "Content-Type": "application/json"
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(
                "https://ifkx7sxcl1f3j6k6.us-east-1.aws.endpoints.huggingface.cloud",
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                print(f"Timeout on attempt {attempt + 1}/{max_retries}, retrying...")
                continue
            else:
                print(f"Failed after {max_retries} attempts due to timeout")
                raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                print(f"Request error on attempt {attempt + 1}/{max_retries}: {e}, retrying...")
                continue
            else:
                print(f"Failed after {max_retries} attempts")
                raise


def get_normal_answer(prompt, model_name):
    """
    Call EDU-Qwen2.5-7B model via HuggingFace and return raw response.

    This function does NOT score responses - scoring is done by
    unified_evaluator.py using LLM-as-judge methodology.

    Args:
        prompt: The prompt to send to the model
        model_name: Model identifier (currently only 'EDU-Qwen2.5-7B')

    Returns:
        Raw text response from the model
    """
    print(f"Calling model: {model_name}")
    try:
        output = query_hf_model({
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 512,
                "temperature": 0.7,
                "do_sample": True
            }
        })

        # Handle different response formats
        response_text = ""
        if isinstance(output, list) and len(output) > 0:
            # Standard text generation response
            if 'generated_text' in output[0]:
                response_text = output[0]['generated_text']
            elif 'text' in output[0]:
                response_text = output[0]['text']
            else:
                response_text = str(output[0])
        elif isinstance(output, dict):
            if 'generated_text' in output:
                response_text = output['generated_text']
            elif 'text' in output:
                response_text = output['text']
            elif 'choices' in output and len(output['choices']) > 0:
                response_text = output['choices'][0].get('text', str(output))
            else:
                response_text = str(output)
        else:
            response_text = str(output)

        # Remove prompt echo if present
        if response_text.startswith(prompt):
            response_text = response_text[len(prompt):].strip()

        return response_text

    except requests.exceptions.RequestException as e:
        print(f"Network error calling {model_name}: {e}")
        return f"Network error from {model_name}: {str(e)}"
    except ValueError as e:
        print(f"Configuration error: {e}")
        return f"Configuration error: {str(e)}"
    except Exception as e:
        print(f"Unexpected error calling {model_name}: {e}")
        return f"Error from {model_name}: {str(e)}"


def verify_answer_with_gpt4(question_text, expected_answer, explanation):
    """
    Use GPT-4 to verify if the expected answer is actually correct.

    This is used by unified_evaluator.py for answer verification.

    Args:
        question_text: The question text
        expected_answer: The answer to verify
        explanation: The explanation provided

    Returns:
        Dict with is_correct, correct_answer, confidence, reasoning
    """
    try:
        openai_key = os.getenv('OPENAI_API_KEY')
        if not openai_key:
            return {"is_correct": None, "gpt4_answer": None, "confidence": 0}

        prompt = f"""Given this educational question, determine if the provided answer is correct.

Question: {question_text}

Provided Answer: {expected_answer}
Provided Explanation: {explanation}

Please analyze:
1. Is the provided answer mathematically/logically correct?
2. What is the correct answer if different?
3. Your confidence level (0-10)

Return ONLY a JSON object:
{{"is_correct": true/false, "correct_answer": "your answer", "confidence": 0-10, "reasoning": "brief explanation"}}"""

        headers = {
            "Authorization": f"Bearer {openai_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-5",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30
        )

        if response.status_code == 200:
            content = response.json()['choices'][0]['message']['content']
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                return result

        return {"is_correct": None, "gpt4_answer": None, "confidence": 0}

    except Exception as e:
        print(f"Error verifying answer with GPT-4: {e}")
        return {"is_correct": None, "gpt4_answer": None, "confidence": 0}
