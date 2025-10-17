from concurrent.futures import ThreadPoolExecutor
import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from evaluator.llm_interface import simple_solve_with_llm
from utils.dev_upload_util import dev_uploader



SYSTEM_PROMPT = """You are an expert educational content generator. Convert the input into Arabic multiple-choice questions (MCQs) based on the specified grade, subject, and skill.

Generate questions in this exact format:
{
  "data": [
    {
      "type": "mcq",
      "question": "<Arabic question text>",
      "answer": "<correct answer>",
      "difficulty": "<easy/medium/hard>",
      "explanation": "<brief explanation in Arabic>",
      "options": {
        "A": "<option A>",
        "B": "<option B>",
        "C": "<option C>",
        "D": "<option D>"
      },
      "answer_choice": "<A/B/C/D>",
      "detailed_explanation": {
        "steps": [
          {
            "title": "<step title in Arabic>",
            "content": "<step content in Arabic>",
            "image": null,
            "image_alt_text": null
          }
        ],
        "personalized_academic_insights": [
          {
            "answer": "<incorrect option>",
            "insight": "<insight for why this is wrong, in Arabic>"
          }
        ]
      },
      "voiceover_script": {
        "question_script": "<question text>",
        "answer_choice_scripts": [
          "Option A: <text>",
          "Option B: <text>",
          "Option C: <text>",
          "Option D: <text>"
        ],
        "explanation_step_scripts": []
      },
      "skill": null,
      "image_url": null,
      "di_formats_used": null
    }
  ],
  "request_id": "<uuid>",
  "total_questions": <count>,
  "grade": <grade>,
  "evaluation": null
}

Requirements:
1. Generate all content in Arabic
2. Create exactly 'count' number of questions
3. Ensure questions align with the grade level and skill specified
4. Provide 3-4 plausible incorrect options
5. Include detailed step-by-step explanations with educational insights
6. Generate a unique UUID for request_id
7. Set appropriate difficulty levels"""


def generate_questions(input_data, upload=False):
    """Convert input specification to Arabic MCQ questions"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(input_data, ensure_ascii=False)}
    ]

    response = simple_solve_with_llm(messages)

    if upload and response and response.get("data"):
        upload_result = dev_uploader.upload_questions(
            questions=response["data"],
            generation_params=input_data
        )
        response["upload_result"] = upload_result
        print(upload_result)
    return response


if __name__ == "__main__":
    # Example input
    sample_input = {
      "grade": 5,
      "count": 10,
      "subject": "mathematics",
      "instructions": "Generate fraction questions",
      "language": "arabic",
      "model": "dspy",
      "skill": {
          "id": "fractions_5",
          "title": "Fractions",
          "unit_name": "Number Concepts",
          "lesson_title": "Adding and Subtracting Fractions"
      },
      "generator": "prompt-engineering-openai"
    }
    # handle 100 questions by breaking down the input data into 10 parts
    results = []
    # parallelize the generation
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(generate_questions, sample_input, upload=True) for i in range(30)]
        results = [future.result() for future in futures]