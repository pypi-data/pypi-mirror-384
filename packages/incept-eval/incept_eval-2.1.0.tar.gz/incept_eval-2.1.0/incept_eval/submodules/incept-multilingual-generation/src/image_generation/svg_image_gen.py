from __future__ import annotations

from typing import Callable
import logging
import json
import re
import textwrap
import xml.etree.ElementTree as ET
import asyncio
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from google import genai
from src.utils.supabase_client import SupabaseStorage
from src.config import Config

logger = logging.getLogger(__name__)


def clean_svg(raw: str) -> str:
    """Clean and validate SVG code from LLM response"""
    # 1. remove Markdown code fences and extract content
    if "```" in raw:
        # Find content between code fences
        import re
        code_blocks = re.findall(r"```(?:xml|svg)?\s*(.*?)```", raw, re.DOTALL)
        if code_blocks:
            raw = code_blocks[0]
    
    # 2. drop anything before the first <svg
    if "<svg" in raw:
        raw = raw[raw.find("<svg"):]
    elif "<?xml" in raw:
        raw = raw[raw.find("<?xml"):]
    
    # 3. dedent and strip BOM / whitespace
    raw = textwrap.dedent(raw).lstrip("\ufeff \n\r\t")
    
    try:
        ET.fromstring(raw)
    except ET.ParseError as e:
        raise RuntimeError(f"Bad SVG from LLM: {e}")
    return raw

def _get_system_prompt() -> str:
    return """Create SVG code for educational counting problems.

        Rules:
        - Show exact quantities specified - no more, no less
        - Include the appropriate mathematical operator symbol (+, -, ×, ÷) between groups if required
        - Use viewBox="0 0 800 600" and ensure all objects fit within
        
        - Create recognizable representations of the objects mentioned. 
        - Use appropriate shapes, colors, and simple details
        - Keep objects simple but identifiable 
        - NEVER include any descriptive text or labels in the images
        - Numbers are allowed ONLY when showing mathematical expressions or quantities
        - Ensure there is at least 20px of padding around the edges of the image
        - The objects should be centered in the image viewport
        
        CRITICAL:
        - NEVER use simple dots or shapes to depict other objects. Generate actual shapes to represent the object. For example for an apple - use a red apple shape with a small leaf on it.
        - Ensure there is enough space between the objects and the symbols
        - Add a margin of 10px around the operator symbols
        - Never include the question text in the SVG
        - Never show the final answer - only the problem setup
        - NO descriptive text, labels, or words (like "apples", "total", etc.) should appear in the SVG
        - Numbers are OK when showing mathematical operations or quantities
        - Return only valid SVG code starting with <?xml version="1.0" encoding="UTF-8"?> and nothing else
        - DON'T include any comments in the SVG
        """


def _get_user_prompt(description: str, feedback: str = None, original_svg: str = None) -> str:
    user_prompt = f"""Create an SVG image code with the following requirements: {description}"""

    if feedback and original_svg:
            # Editing prompt with feedback
            user_prompt = f"""Improve this SVG based on the feedback provided.
            Original problem: {description}

            Previous SVG code:
            {original_svg}

            Quality feedback to address:
            {feedback}

            Create an improved SVG that addresses all the feedback points while maintaining the counting visualization requirements."""
            
    return user_prompt


def _generate_svg_code_gpt(description: str, feedback: str = None, original_svg: str = None) -> str:
    """
    Generate SVG code based on a description using OpenAI.
    
    Parameters
    ----------
    description : str
        Description of the image to generate
        
    Returns
    -------
    str
        The generated SVG code
    """
    try:
        system_prompt = _get_system_prompt()
        user_prompt = _get_user_prompt(description, feedback, original_svg)
        
        client = OpenAI(api_key=Config.OPENAI_API_KEY)
        
        logger.info("Sending request to GPT for SVG generation")
        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=1.0
            )
            logger.info(f"GPT response received")
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise Exception(f"OpenAI API call failed: {str(e)}")
        
        logger.info("GPT response received successfully")

        if not response or not response.choices:
            raise Exception("No response from GPT")
        
        svg_code = response.choices[0].message.content
        if not svg_code:
            raise Exception("Empty response from GPT")
        
        svg_code = svg_code.strip()
        
        if not svg_code:
            raise Exception("Empty SVG code generated")
            
        logger.info("Successfully generated SVG code with GPT")
        logger.info(f"Generated SVG snippet: {svg_code[:200]}...")
        return svg_code

    except Exception as e:
        logger.error(f"Error generating SVG with GPT: {e}")
        raise


def _generate_svg_code_gemini(description: str, feedback: str = None, original_svg: str = None) -> str:
    """
    Generate SVG code based on a description using Gemini 2.5 Flash.
    
    Parameters
    ----------
    description : str
        Description of the image to generate
        
    Returns
    -------
    str
        The generated SVG code
    """
    try:
        system_prompt = _get_system_prompt()
        user_prompt = _get_user_prompt(description, feedback, original_svg)

        client = genai.Client()
        
        logger.info("Sending request to Gemini 2.5 Flash for SVG generation")
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    {"role": "user", "parts": [
                        {"text": f"{system_prompt}\n\n{user_prompt}"}
                    ]}
                ]
            )
            logger.info(f"Gemini response received: {type(response)}")
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise Exception(f"Gemini API call failed: {str(e)}")
        
        if not response or not response.candidates:
            raise Exception("No response from Gemini")
        
        svg_code = response.candidates[0].content.parts[0].text
        if not svg_code:
            raise Exception("Empty response from Gemini")
        
        svg_code = svg_code.strip()
        
        if not svg_code:
            raise Exception("Empty SVG code generated")
            
        logger.info("Successfully generated SVG code with Gemini 2.5 Flash")
        logger.info(f"Generated SVG snippet: {svg_code[:200]}...")
        return svg_code

    except Exception as e:
        logger.error(f"Error generating SVG with Gemini: {e}")
        raise


def _convert_and_upload_svg(svg_code: str, prefix: str = "svg_generated") -> str:
    """Convert SVG to PNG and upload to storage. Returns the public URL."""
    try:
        from cairosvg import svg2png
        import io
        import time
        import os
        
        # Convert SVG to PNG
        png_bytes = svg2png(bytestring=svg_code.encode('utf-8'))
        
        # Upload to Supabase
        storage = SupabaseStorage()
        timestamp = int(time.time() * 1000)
        filename = f"{prefix}_{timestamp}.png"
        
        # Save locally first
        local_path = f"generated_images/{filename}"
        os.makedirs("generated_images", exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(png_bytes)
        
        # Try to upload to Supabase
        public_url = storage.upload_image(local_path, f"svg/{filename}")
        if public_url:
            logger.info(f"Successfully uploaded SVG image to Supabase: {public_url}")
            return public_url
        else:
            logger.info(f"Supabase upload failed, returning local path: {local_path}")
            return local_path
            
    except ImportError:
        logger.error("cairosvg not available - cannot convert SVG to PNG")
        raise Exception("SVG to PNG conversion not available - cairosvg dependency missing")
    except Exception as e:
        logger.error(f"Failed to convert and upload SVG: {e}")
        raise


def generate_svg_image(description: str, feedback: str = None, original_svg: str = None) -> str:
    """
    Generate an SVG image from a description and convert it to PNG.
    
    Parameters
    ----------
    description : str
        Description of the counting/arithmetic problem to visualize
        
    Returns
    -------
    str
        A JSON string containing the URL of the generated image
    """
    logger.info(f"Generating SVG image from description: {description}")
    logger.info(f"Feedback: {feedback}")
    logger.info(f"Original SVG provided: {len(original_svg) if original_svg else 0} characters")
    try:
        # If feedback is provided, use it for regeneration with the best performing model
        if feedback and original_svg:
            logger.info("Regenerating with feedback - using both models in parallel")
            
            # Run both models in parallel for regeneration
            with ThreadPoolExecutor(max_workers=2) as executor:
                gpt_future = executor.submit(
                    lambda: clean_svg(_generate_svg_code_gpt(description, feedback, original_svg))
                )
                gemini_future = executor.submit(
                    lambda: clean_svg(_generate_svg_code_gemini(description, feedback, original_svg))
                )
                
                # Get results
                gpt_svg = None
                gemini_svg = None
                
                try:
                    gpt_svg = gpt_future.result(timeout=180)  # 3 minute timeout
                    logger.info("GPT regeneration successful")
                except Exception as e:
                    logger.warning(f"GPT regeneration failed: {e}")
                
                try:
                    gemini_svg = gemini_future.result(timeout=180)  # 3 minute timeout
                    logger.info("Gemini regeneration successful")
                except Exception as e:
                    logger.error(f"Gemini regeneration failed with error: {e}")
                    import traceback
                    logger.error(f"Gemini traceback: {traceback.format_exc()}")
            
            # Return both regenerated versions for QA comparison (if both succeeded)
            if gpt_svg and gemini_svg:
                logger.info("Both models regenerated successfully - returning both for agent QA")
                try:
                    # Convert both regenerated SVGs to PNG and upload in parallel
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        gpt_url_future = executor.submit(_convert_and_upload_svg, gpt_svg, "svg_regen_v1")
                        gemini_url_future = executor.submit(_convert_and_upload_svg, gemini_svg, "svg_regen_v2")
                        
                        # Get both URLs
                        gpt_url = gpt_url_future.result(timeout=60)
                        gemini_url = gemini_url_future.result(timeout=60)
                    
                    # Return both regenerated images for agent to handle QA
                    logger.info(f"Returning both regenerated images: GPT={gpt_url}, Gemini={gemini_url}")
                    return json.dumps({
                        "images": [
                            {
                                "local_path": None,
                                "remote_url": gpt_url,
                                "status": "success",
                                "method": "GPT",
                                "svg_code": gpt_svg,
                                "qa_results": None  # Agent will handle QA
                            },
                            {
                                "local_path": None,
                                "remote_url": gemini_url,
                                "status": "success", 
                                "method": "Gemini",
                                "svg_code": gemini_svg,
                                "qa_results": None  # Agent will handle QA
                            }
                        ],
                        "status": "success", 
                        "count": 2
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to convert both regenerated images: {e}, falling back to single model")
                    # Fall through to single model logic
            
            # Use whichever succeeded, or fallback if conversion failed
            if gpt_svg:
                svg_code = gpt_svg
                logger.info("Using GPT regenerated SVG")
            elif gemini_svg:
                svg_code = gemini_svg
                logger.info("Using Gemini regenerated SVG")
            else:
                raise Exception("Both GPT and Gemini regeneration failed")
                
        else:
            # Initial generation - create both versions in parallel and select best
            logger.info("Initial generation - creating both GPT and Gemini versions in parallel")
            
            # Run both models in parallel
            with ThreadPoolExecutor(max_workers=2) as executor:
                gpt_future = executor.submit(
                    lambda: clean_svg(_generate_svg_code_gpt(description))
                )
                gemini_future = executor.submit(
                    lambda: clean_svg(_generate_svg_code_gemini(description))
                )
                
                # Get results
                gpt_svg = None
                gemini_svg = None
                
                try:
                    gpt_svg = gpt_future.result(timeout=180)  # 3 minute timeout
                    logger.info("GPT generation successful")
                except Exception as e:
                    logger.error(f"GPT generation failed with error: {e}")
                    import traceback
                    logger.error(f"GPT traceback: {traceback.format_exc()}")
                
                try:
                    gemini_svg = gemini_future.result(timeout=180)  # 3 minute timeout
                    logger.info("Gemini generation successful")
                except Exception as e:
                    logger.error(f"Gemini generation failed with error: {e}")
                    import traceback
                    logger.error(f"Gemini traceback: {traceback.format_exc()}")
            
            # Return both images if both succeeded - let agent handle QA
            if gpt_svg and gemini_svg:
                logger.info("Both models successful - returning both for agent QA")
                try:
                    # Convert both SVGs to PNG and upload in parallel
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        gpt_url_future = executor.submit(_convert_and_upload_svg, gpt_svg, "svg_v1")
                        gemini_url_future = executor.submit(_convert_and_upload_svg, gemini_svg, "svg_v2")
                        
                        # Get both URLs
                        gpt_url = gpt_url_future.result(timeout=60)  # 1 minute for conversion/upload
                        gemini_url = gemini_url_future.result(timeout=60)  # 1 minute for conversion/upload
                    
                    # Return both images for agent to handle QA
                    logger.info(f"Returning both images: GPT={gpt_url}, Gemini={gemini_url}")
                    return json.dumps({
                        "images": [
                            {
                                "local_path": None,
                                "remote_url": gpt_url,
                                "status": "success",
                                "method": "GPT",
                                "svg_code": gpt_svg,  # Store the actual SVG code!
                                "qa_results": None  # Agent will handle QA
                            },
                            {
                                "local_path": None,
                                "remote_url": gemini_url,
                                "status": "success", 
                                "method": "Gemini",
                                "svg_code": gemini_svg,  # Store the actual SVG code!
                                "qa_results": None  # Agent will handle QA
                            }
                        ],
                        "status": "success", 
                        "count": 2
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to convert both images: {e}, falling back to single model")
                    # Fall through to single model logic
            elif gpt_svg:
                svg_code = gpt_svg
                logger.info("Using GPT generated SVG (only successful model)")
            elif gemini_svg:
                svg_code = gemini_svg
                logger.info("Using Gemini generated SVG (only successful model)")
            else:
                raise Exception("Both GPT and Gemini generation failed")
        
        # Convert final selected SVG to PNG and upload (only for single-model cases)
        logger.info(f"Selected SVG code: {svg_code[:300]}...")
        try:
            final_url = _convert_and_upload_svg(svg_code, "svg_generated")
            logger.info(f"Final SVG image uploaded: {final_url}")
            
            # Determine which model was used for single-model cases
            model_used = "GPT" if gpt_svg and not gemini_svg else "Gemini" if gemini_svg and not gpt_svg else "GPT"
            
            return json.dumps({
                "images": [{
                    "local_path": None,  # TODO: track local path if needed
                    "remote_url": final_url,
                    "status": "success",
                    "method": model_used,
                    "svg_code": svg_code,  # Store the actual SVG code!
                    "qa_results": None  # No QA performed for single-model cases
                }],
                "status": "success", 
                "count": 1
            })
        except Exception as e:
            logger.error(f"Failed to convert and upload final SVG: {e}")
            return json.dumps({
                "images": [],
                "status": "failed", 
                "error": f"Failed to convert SVG: {str(e)}",
                "count": 0
            })
        
    except Exception as e:
        error_message = f"Error generating SVG image: {str(e)}"
        logger.error(error_message)
        return json.dumps({"image_paths": [], "status": "failed", "error": error_message})


def generate_svg_image_tool() -> tuple[dict, Callable]:
    """Tool specification for SVG image generation"""
    spec = {
        "type": "function",
        "name": "generate_svg_image",
        "description": "Generate SVG images for counting and arithmetic problems. Creates precise visual representations of mathematical operations like addition, subtraction, multiplication, and division using exact quantities of simple objects. Perfect for educational content where students need to visualize counting concepts.",
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of the counting/arithmetic problem to visualize. Should specify exact quantities, operation type, and desired object representation (e.g., 'Show 9 apples plus 6 more apples for addition', 'Show 24 circles arranged in 6 equal groups for division')."
                },
            },
            "required": ["description"]
        }
    }
    return spec, generate_svg_image