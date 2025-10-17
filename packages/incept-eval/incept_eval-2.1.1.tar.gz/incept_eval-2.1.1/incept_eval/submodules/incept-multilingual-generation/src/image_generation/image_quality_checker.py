from __future__ import annotations

from typing import Callable, List, Dict, Any, Optional
import logging
import json
from openai import OpenAI
import base64
import requests
from pydantic import BaseModel
from src.llms import produce_structured_response_openai

logger = logging.getLogger(__name__)


class ImageRanking(BaseModel):
    """Single image evaluation"""
    rank: int
    image_index: int
    score: int
    strengths: List[str]
    weaknesses: List[str]
    changes_required: List[str]  # Concrete changes needed for regeneration
    recommendation: str  # "ACCEPT" or "REJECT"


class QualityCheckResult(BaseModel):
    """Quality check result for multiple images"""
    rankings: List[ImageRanking]
    best_image_index: int
    overall_feedback: str


class ImageQualityChecker:
    """Checks image quality and accuracy against expected descriptions using GPT-4 Vision."""
    
    def __init__(self):
        self.client = OpenAI()
    
    def check_image_quality_batch(
        self, 
        image_urls: List[str], 
        expected_description: str,
        educational_context: str = "",
        age_group: str = ""
    ) -> QualityCheckResult:
        """
        Check quality and accuracy of multiple images against expected description.
        Returns a ranking and feedback for each image.
        
        Parameters
        ----------
        image_urls : List[str]
            List of image URLs or local paths to check
        expected_description : str
            What the images should depict
        educational_context : str
            The educational context (e.g., "Grade 5 Mathematics - Fractions")
        age_group : str
            Target age group (e.g., "10-11 years old")
            
        Returns
        -------
        QualityCheckResult
            Structured result with rankings and detailed feedback
        """
        try:
            if not image_urls:
                return QualityCheckResult(
                    rankings=[],
                    best_image_index=0,
                    overall_feedback="Error: No images provided"
                )
            
            logger.info(f"Checking quality of {len(image_urls)} images")
            for i, url in enumerate(image_urls):
                logger.info(f"  Image {i+1}: {url}")
            
            system_prompt = """You are an expert image quality assessor for educational content. You are evaluating multiple images to select the best one that accurately depicts the expected content and meets quality standards.

CRITICAL RULE FOR EDUCATIONAL IMAGES:
If the image shows the answer or calculated values that the student is supposed to figure out, you MUST REJECT it. Educational diagrams should only show given information, not reveal solutions.

SPECIAL RULE FOR SVG COUNTING/ARITHMETIC IMAGES:
SVG images should contain NO descriptive text or labels (like "apples", "total", "sum", etc.). Numbers are acceptable ONLY when showing mathematical operations or quantities. Any descriptive text or labeling should result in REJECTION.

SPECIAL RULE FOR VENN DIAGRAMS:
Venn diagrams should show ONLY set labels (e.g., "Math", "Science") and proper overlapping structure. They should NOT show any numbers - neither given values nor calculated answers. This provides a clean visual framework for students to organize their thinking without revealing solutions.

## Evaluation Criteria

1. **Accuracy to Description** (40% weight)
   - Does the image accurately represent what was requested?
   - Are all required elements present?
   - Is the content mathematically/scientifically correct?
   - Do the objects in the image match the description?
   - CRITICAL: Does it reveal the answer that students should calculate? If yes, REJECT

2. **Educational Value** (30% weight)
   - Is the image clear and easy to understand for the target age group?
   - Does it effectively communicate the concept?
   - Would it help students learn?
   - Does it preserve the learning challenge by not revealing answers?

3. **Visual Clarity** (20% weight)
   - Is the image well-organized and uncluttered?
   - For SVG counting/arithmetic images: NO descriptive text or labels should be present (numbers for math operations are OK)
   - Is the color scheme appropriate?
   - For counting/arithmetic problems: Are all objects fully visible with no unwanted overlap? Can students easily count individual items?
   - For Venn diagrams: Are overlapping regions clearly defined and appropriate for the concept?

4. **Technical Quality** (10% weight)
   - Is the image sharp and well-rendered?
   - Are there any visual artifacts or errors?

## Response Format

Provide your evaluation as a JSON object with:
{
  "rankings": [
    {
      "rank": 1,
      "image_index": <0-based index>,
      "score": <0-100>,
      "strengths": ["list", "of", "strengths"],
      "weaknesses": ["list", "of", "weaknesses"],
      "changes_required": ["concrete", "specific", "changes", "needed", "for", "regeneration"],
      "recommendation": "ACCEPT" or "REJECT"
    }
  ],
  "best_image_index": <index of best image>,
  "overall_feedback": "Summary of the evaluation"
}

**IMPORTANT for changes_required field:**
- For REJECTED images, provide specific, actionable changes that can be used directly in regeneration prompts
- Focus on concrete modifications like "Change the count from 4 to 5 apples", "Make all apples fully visible with no overlap", "Remove the total number 12 from the image"
- Be precise about positioning, counts, colors, arrangements, or content changes needed
- For ACCEPTED images, this field can be empty or contain minor suggested improvements

Only recommend ACCEPT for images that score 70 or above."""

            # Prepare images for vision API
            image_contents = []
            for i, image_url in enumerate(image_urls):
                if image_url.startswith('http'):
                    image_contents.append({
                        "type": "image_url",
                        "image_url": {"url": image_url}
                    })
                else:
                    # Local file - encode as base64
                    try:
                        with open(image_url, "rb") as image_file:
                            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                            image_contents.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                            })
                    except Exception as e:
                        logger.error(f"Failed to read local image {image_url}: {e}")
                        continue
            
            if not image_contents:
                return QualityCheckResult(
                    rankings=[],
                    best_image_index=0,
                    overall_feedback="Error: Failed to process any images"
                )
            
            # Build user message
            url_list = "\n".join([f"Image {i+1}: {url}" for i, url in enumerate(image_urls)])
            
            user_prompt = f"""Please evaluate these {len(image_urls)} images against the expected description within the specified educational context:

Educational Context: {educational_context}
Target Age Group: {age_group}

Expected Description:
{expected_description}

Images to evaluate:
{url_list}

Analyze each image carefully and provide your rankings and feedback in the JSON format specified."""

            # Prepare message content
            message_content = [{"type": "text", "text": user_prompt}]
            message_content.extend(image_contents)
            
            # Use structured output
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_content}
            ]
            
            # GPT-5 only supports temperature=1, so pass it explicitly
            return produce_structured_response_openai(
                messages=messages, 
                structure_model=QualityCheckResult, 
                model="gpt-5", 
                instructions=None,
                temperature=1.0,
                max_output_tokens=None
            )
                
        except Exception as e:
            logger.error(f"Error checking image quality: {e}")
            # Return a failed result
            return QualityCheckResult(
                rankings=[],
                best_image_index=0,
                overall_feedback=f"Error checking images: {str(e)}"
            )
    
    def check_single_image(
        self,
        image_url: str,
        expected_description: str,
        educational_context: str = "",
        age_group: str = ""
    ) -> ImageRanking:
        """Evaluate a single image."""
        
        system_prompt = """You are an expert image quality assessor for educational content. Your task is to evaluate whether an image accurately depicts what it's supposed to show and meets quality standards for educational use.

## Evaluation Criteria

1. **Accuracy** (Critical)
   - Does the image show what was requested?
   - Are all elements correct and properly positioned?
   - Is it mathematically/scientifically accurate?

2. **Educational Appropriateness**
   - Is it suitable for the target age group?
   - Does it clearly communicate the concept?
   - Is it free from distracting elements?

3. **Visual Quality**
   - Is the image clear and well-organized?
   - Are any labels or text readable?
   - Is the style appropriate for educational content?
   - Are the objects visually appealing

**Important Guidelines:**
- PASS: Score ≥ 70, image accurately represents the concept with minor issues at most
- FAIL: Score < 70, significant inaccuracies or quality issues

**Provide Complete Feedback: If you rate an image as a FAIL, you must provide complete, specific, detailed feedback about ALL issues with the image. Do not leave out any feedback about shortcomings for any reason. The image will be improved based only on what you provide feedback on, so you MUST describe every error and how to fix it in your response.**"""

        user_prompt = f"""Please evaluate this image against the expected description within the specified educational context:

Educational Context: {educational_context}
Target Age Group: {age_group}

Expected Description:
{expected_description}

Evaluate the image carefully and provide your assessment."""

        try:
            # Prepare image for vision API
            if image_url.startswith('http'):
                image_content = {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            else:
                # Local file
                import base64
                with open(image_url, "rb") as image_file:
                    base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    image_content = {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                    }
            
            # Use structured output with response_format
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Use gpt-4o for structured output support
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": user_prompt},
                        image_content
                    ]}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "image_quality_assessment",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "evaluation": {
                                    "type": "string",
                                    "enum": ["PASS", "FAIL"]
                                },
                                "score": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 100
                                },
                                "feedback": {
                                    "type": "string"
                                },
                                "issues": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                },
                                "strengths": {
                                    "type": "array",
                                    "items": {
                                        "type": "string"
                                    }
                                }
                            },
                            "required": ["evaluation", "score", "feedback", "issues", "strengths"],
                            "additionalProperties": False
                        }
                    }
                },
                max_completion_tokens=800
            )
            
            result_json = json.loads(response.choices[0].message.content)
            
            # Convert to ImageRanking object
            return ImageRanking(
                rank=1,  # Single image always ranks 1st
                image_index=0,  # Single image has index 0
                score=result_json["score"],
                recommendation="ACCEPT" if result_json["evaluation"] == "PASS" else "REJECT",
                strengths=result_json.get("strengths", []),
                weaknesses=result_json.get("issues", []),
                changes_required=result_json.get("issues", [])
            )
                
        except Exception as e:
            logger.error(f"Error checking single image: {e}")
            return ImageRanking(
                rank=1,
                image_index=0,
                score=0,
                recommendation="REJECT",
                strengths=[],
                weaknesses=[f"Error during evaluation: {str(e)}"],
                changes_required=[f"Technical error occurred: {str(e)}"]
            )

def check_image_quality_batch_tool() -> tuple[dict, Callable]:
    """Tool specification for batch image quality checking."""
    spec = {
        "type": "function",
        "name": "check_image_quality_batch",
        "description": "Check the quality and accuracy of multiple images against an expected description. Returns rankings and detailed feedback for each image to help select the best one.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of image URLs or local file paths to evaluate"
                },
                "expected_description": {
                    "type": "string",
                    "description": "What the images should depict"
                },
                "educational_context": {
                    "type": "string",
                    "description": "The educational context (e.g., 'Grade 5 Mathematics - Fractions')"
                },
                "age_group": {
                    "type": "string",
                    "description": "Target age group (e.g., '10-11 years old')"
                }
            },
            "required": ["image_urls", "expected_description"]
        }
    }
    
    checker = ImageQualityChecker()
    return spec, checker.check_image_quality_batch

def check_single_image_tool() -> tuple[dict, Callable]:
    """Tool specification for single image quality checking."""
    spec = {
        "type": "function",
        "name": "check_single_image",
        "description": "Evaluate a single image for quality and accuracy against an expected description.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_url": {
                    "type": "string",
                    "description": "Image URL or local file path to evaluate"
                },
                "expected_description": {
                    "type": "string",
                    "description": "What the image should depict"
                },
                "educational_context": {
                    "type": "string",
                    "description": "The educational context"
                },
                "age_group": {
                    "type": "string",
                    "description": "Target age group"
                }
            },
            "required": ["image_url", "expected_description"]
        }
    }
    
    checker = ImageQualityChecker()
    return spec, checker.check_single_image