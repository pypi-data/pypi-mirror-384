from __future__ import annotations

from google import genai
from google.genai import types
from typing import Callable, Optional, List
import logging
import concurrent.futures
from threading import Lock
import json
import os
import time
from PIL import Image
from io import BytesIO
from src.utils.supabase_client import SupabaseStorage

logger = logging.getLogger(__name__)

# Thread-safe counter for unique image naming
_image_counter = 0
_counter_lock = Lock()

def _get_next_image_number():
    """Get the next image number in a thread-safe way."""
    global _image_counter
    with _counter_lock:
        _image_counter += 1
        return _image_counter

def _generate_single_image_gemini(prompt: str, image_index: int) -> Optional[str]:
    """
    Generate a single image using Gemini 2.0 Flash.
    
    Parameters
    ----------
    prompt : str
        The prompt to generate the image from
    image_index : int
        Index of this image in the batch for logging
        
    Returns
    -------
    str
        The path of the saved image file
    """
    try:
        logger.info(f"Generating image {image_index + 1} with Gemini")
        logger.info(f"Full prompt sent to Gemini: {prompt}")
        
        # Initialize Gemini client
        client = genai.Client()
        
        # Generate content with both text and image modalities
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )
        
        # Extract image data from response parts
        image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                # The image data is already base64 decoded bytes
                image_data = part.inline_data.data
                break
        
        if image_data is None:
            logger.warning("No image data found in Gemini response")
            return None
        
        # Create generated_images directory if it doesn't exist
        images_dir = "generated_images"
        os.makedirs(images_dir, exist_ok=True)
        
        # Create filename using image index and timestamp
        timestamp = int(time.time() * 1000)  # milliseconds for uniqueness
        filename = f"{images_dir}/generated_image_{image_index + 1}_{timestamp}_gemini.png"
        
        # Save the image bytes to file
        with open(filename, "wb") as f:
            f.write(image_data)
        
        logger.info(f"Successfully generated image {image_index + 1} with Gemini: {filename}")
        
        # Try to upload to Supabase
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(filename, f"gemini/{os.path.basename(filename)}")
            if public_url:
                logger.info(f"Uploaded Gemini image to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return filename
        
    except Exception as e:
        logger.error(f"Error generating image {image_index + 1} with Gemini: {e}")
        return None

def generate_image_gemini(prompt: str, aspect_ratio: str = "1:1", num_images: int = 3) -> str:
    """
    Generate image(s) using Gemini 2.0 Flash.
    
    Parameters
    ----------
    prompt : str
        The prompt to generate the images from
    aspect_ratio : str, default "1:1"
        The aspect ratio preference (note: Gemini may not strictly follow this)
    num_images : int, default 3
        The number of images to generate in parallel
        
    Returns
    -------
    str
        JSON string containing the list of generated image paths
    """
    logger.debug(f"Generating {num_images} images with Gemini")
    
    # Enhance prompt with aspect ratio preference if not square
    enhanced_prompt = prompt
    if aspect_ratio == "16:9":
        enhanced_prompt = f"{prompt} (wide landscape format, 16:9 aspect ratio)"
    elif aspect_ratio == "9:16":
        enhanced_prompt = f"{prompt} (tall portrait format, 9:16 aspect ratio)"
    elif aspect_ratio == "4:3":
        enhanced_prompt = f"{prompt} (landscape format, 4:3 aspect ratio)"
    elif aspect_ratio == "3:4":
        enhanced_prompt = f"{prompt} (portrait format, 3:4 aspect ratio)"
    
    # Generate all images in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_images) as executor:
        # Submit all image generation tasks
        future_to_index = {
            executor.submit(_generate_single_image_gemini, enhanced_prompt, i): i 
            for i in range(num_images)
        }
        
        # Collect results as they complete
        image_paths = [None] * num_images
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                image_path = future.result()
                image_paths[index] = image_path
            except Exception as e:
                logger.error(f"Failed to generate image {index + 1} with Gemini: {e}")
    
    # Filter out any None values (failed generations)
    successful_paths = [path for path in image_paths if path is not None]
    
    if not successful_paths:
        logger.error("Failed to generate any images with Gemini")
        return json.dumps({"image_paths": [], "status": "failed"})
    
    logger.info(f"Successfully generated {len(successful_paths)} out of {num_images} images with Gemini")
    
    # Return the paths as a JSON string
    result = {
        "image_paths": successful_paths,
        "status": "success",
        "count": len(successful_paths)
    }
    
    return json.dumps(result)

def edit_image_with_gemini(original_image_path: str, edit_instruction: str) -> Optional[str]:
    """
    Edit an existing image using Gemini's image editing capabilities
    
    Parameters
    ----------
    original_image_path : str
        Local file path to the original image that needs editing
    edit_instruction : str
        Detailed instructions for what edits to make to the image
        
    Returns
    -------
    Optional[str]
        Path to the edited image, or None if failed
    """
    try:
        logger.info(f"Editing image with Gemini: {original_image_path}")
        logger.info(f"Full edit instruction sent to Gemini: {edit_instruction}")
        
        if not os.path.exists(original_image_path):
            logger.error(f"Original image not found: {original_image_path}")
            return None
        
        # Initialize Gemini client
        client = genai.Client()
        
        # Read and upload the original image
        with open(original_image_path, 'rb') as f:
            image_data = f.read()
        
        logger.info(f"Loaded image data: {len(image_data)} bytes from {original_image_path}")
        
        # Create the edit request with both image and instruction
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_data
                            }
                        },
                        {"text": edit_instruction}
                    ]
                }
            ],
            config=types.GenerateContentConfig(
                response_modalities=['TEXT', 'IMAGE']
            )
        )
        
        # Extract edited image data from response
        edited_image_data = None
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                edited_image_data = part.inline_data.data
                break
        
        if edited_image_data is None:
            logger.warning("No edited image data found in Gemini response")
            return None
        
        # Save the edited image
        images_dir = "generated_images"
        os.makedirs(images_dir, exist_ok=True)
        
        base_name = os.path.splitext(os.path.basename(original_image_path))[0]
        timestamp = int(time.time() * 1000)
        edited_filename = f"{images_dir}/{base_name}_gemini_edited_{timestamp}.png"
        
        with open(edited_filename, "wb") as f:
            f.write(edited_image_data)
        
        logger.info(f"Successfully edited image: {edited_filename}")
        
        # Try to upload to Supabase
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(edited_filename, f"gemini/{os.path.basename(edited_filename)}")
            if public_url:
                logger.info(f"Uploaded edited image to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload edited image to Supabase: {e}")
        
        return edited_filename
        
    except Exception as e:
        logger.error(f"Error editing image with Gemini: {e}")
        return None

def generate_image_gemini_tool() -> tuple[dict, Callable]:
    spec = {
        "type": "function",
        "name": "generate_image_gemini",
        "description": "Generate image(s) using Google's Gemini 2.0 Flash image generation model. Returns a JSON string containing the list of generated image paths. Use the quality checker to select the best image from the list.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Prompt for generating images. Gemini excels at creating contextually relevant images that leverage world knowledge and reasoning."
                },
                "aspect_ratio": {
                    "type": "string",
                    "description": "Preferred aspect ratio of the images. Options: '1:1', '16:9', '9:16', '4:3', '3:4'. Note: Gemini may not strictly follow aspect ratios but will attempt to match the preference.",
                    "default": "1:1"
                },
                "num_images": {
                    "type": "integer",
                    "description": "The number of images to generate in parallel. Default is 3. All images will be returned for quality checking.",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 5
                }
            },
            "required": ["prompt"]
        }
    }
    return spec, generate_image_gemini