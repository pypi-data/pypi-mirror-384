#!/usr/bin/env python3
"""
Test image generation using Incept API for curriculum questions
"""

import asyncio
import aiohttp
import json
import os
import time
import logging
import re
from typing import Optional, Dict, Any
from tests.test_questions import TEST_QUESTIONS

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# API configuration
INCEPT_API_URL = "https://inceptapi.rp.devfactory.com/api/respond"
INCEPT_API_HEADERS = {
    "Content-Type": "application/json"
}

curriculum_mcqs = TEST_QUESTIONS


async def call_incept_api(question: str, session: aiohttp.ClientSession) -> Optional[str]:
    """
    Call Incept API to generate image for a question
    
    Parameters
    ----------
    question : str
        The educational question to generate an image for
    session : aiohttp.ClientSession
        The aiohttp session for making requests
        
    Returns
    -------
    Optional[str]
        URL of generated image or None if failed
    """
    try:
        # Prepare the API request
        prompt = f"Generate an image for the question: {question}"
        payload = {
            "prompt": prompt,
            "model": "incept"
        }
        
        logger.info(f"Calling Incept API with prompt: {prompt[:100]}...")
        timeout = 500
        
        # Make async request to API
        async with session.post(
            INCEPT_API_URL,
            json=payload,
            headers=INCEPT_API_HEADERS,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ) as response:
            if response.status == 200:
                # Parse streaming response (text/event-stream)
                image_url = None
                final_response = None
                
                async for line in response.content:
                    line_text = line.decode('utf-8').strip()
                    
                    # Skip empty lines
                    if not line_text:
                        continue
                    
                    try:
                        # Parse JSON event
                        event = json.loads(line_text)
                        event_type = event.get("type")
                        event_data = event.get("data")
                        
                        logger.debug(f"Received event: {event_type}")
                        
                        # Handle different event types
                        if event_type == "tool_final":
                            # Tool execution results might contain image URLs
                            if event_data:
                                try:
                                    tool_data = json.loads(event_data) if isinstance(event_data, str) else event_data
                                    # Look for image URL in tool results
                                    if isinstance(tool_data, dict):
                                        image_url = (
                                            tool_data.get("image_url") or 
                                            tool_data.get("imageUrl") or
                                            tool_data.get("url") or
                                            tool_data.get("image") or
                                            (tool_data.get("data", {}).get("image_url") if isinstance(tool_data.get("data"), dict) else None)
                                        )
                                        if image_url:
                                            logger.info(f"Found image URL in tool_final: {image_url}")
                                except json.JSONDecodeError:
                                    pass
                        
                        elif event_type == "response_final":
                            # Final response might contain the image URL
                            final_response = event_data
                            if event_data:
                                # Extract text from data object
                                response_text = ""
                                if isinstance(event_data, dict) and "text" in event_data:
                                    response_text = event_data["text"]
                                else:
                                    response_text = str(event_data)
                                
                                # Try to extract URL from final response text
                                url_pattern = r'https?://[^\s<>"]+\.(?:jpg|jpeg|png|gif|webp)'
                                urls = re.findall(url_pattern, response_text, re.IGNORECASE)
                                if urls:
                                    image_url = urls[0]
                                    logger.info(f"Found image URL in response_final: {image_url}")
                                    
                                # Also save the full response text for debugging
                                final_response = response_text
                        
                        elif event_type == "error":
                            logger.error(f"API returned error event: {event_data}")
                            return None
                    
                    except json.JSONDecodeError:
                        # Skip lines that aren't valid JSON
                        continue
                
                if image_url:
                    logger.info(f"✅ Successfully received image URL: {image_url}")
                    return image_url
                else:
                    logger.warning(f"No image URL found in streaming response. Final response: {final_response}")
                    return None
                    
            else:
                error_text = await response.text()
                logger.error(f"API request failed with status {response.status}: {error_text}")
                return None
                
    except asyncio.TimeoutError:
        logger.error(f"API request timed out after {timeout} seconds")
        return None
    except Exception as e:
        logger.error(f"Error calling Incept API: {e}")
        return None


async def test_curriculum_questions():
    """Test image generation for all curriculum questions using Incept API"""
    
    # JSON file path - use main imagen.json file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    json_path = os.path.join(project_root, "data", "imagen.json")
    
    logger.info(f"JSON output path: {json_path}")
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    # Load existing data
    existing_data = []
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                existing_data = json.load(f)
                logger.info(f"Loaded {len(existing_data)} existing entries from JSON")
        except json.JSONDecodeError:
            logger.warning("JSON file exists but is empty or invalid, starting fresh")
            existing_data = []
    else:
        # Create empty JSON file
        with open(json_path, 'w') as f:
            json.dump([], f)
    
    # Create a set of questions that already have incept_v1 data for quick lookup
    existing_incept_questions = {entry['question'] for entry in existing_data if 'question' in entry and 'incept_v1' in entry}
    
    # Statistics tracking
    total_questions = 0
    successful_generations = 0
    failed_generations = 0
    skipped_questions = 0
    
    # Create aiohttp session for API calls
    async with aiohttp.ClientSession() as session:
        # Process each grade level
        for grade_level, topics in curriculum_mcqs.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"Testing Grade: {grade_level}")
            logger.info(f"{'='*50}")
            
            # Process each topic in the grade
            for topic, question in topics.items():
                total_questions += 1
                
                # Check if this question already has incept_v1 data
                if question in existing_incept_questions:
                    logger.info(f"\n⏭️  Skipping (incept_v1 already exists): {question[:50]}...")
                    skipped_questions += 1
                    continue
                    
                logger.info(f"\nTopic: {topic}")
                logger.info(f"Question: {question}")
                
                try:
                    # Determine grade number
                    if grade_level.startswith("Grade"):
                        grade = int(grade_level.split()[1])
                    else:
                        # For non-numeric grades, default to 12
                        grade = 12
                    
                    # Call Incept API
                    logger.info("Calling Incept API...")
                    start_time = time.time()
                    
                    image_url = await call_incept_api(question, session)
                    
                    end_time = time.time()
                    time_taken = round(end_time - start_time, 2)
                    
                    if image_url:
                        successful_generations += 1
                        logger.info(f"✅ Success! Image URL: {image_url}")
                        
                        # Create incept_v1 data
                        incept_data = {
                            "image_url": image_url,
                            "time_taken": time_taken,
                            "quality_feedback": "No quality check performed",
                            "api_version": "v1",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Re-read JSON file to get latest data
                        if os.path.exists(json_path):
                            with open(json_path, 'r') as f:
                                try:
                                    existing_data = json.load(f)
                                except json.JSONDecodeError:
                                    existing_data = []
                        
                        # Find matching entry by question and add incept_v1 data
                        entry_found = False
                        for i, entry in enumerate(existing_data):
                            if entry.get('question') == question:
                                # Add incept_v1 to existing entry
                                existing_data[i]['incept_v1'] = incept_data
                                entry_found = True
                                logger.info(f"✅ Updated existing entry with incept_v1 data")
                                break
                        
                        # If no matching entry found, create new entry
                        if not entry_found:
                            new_entry = {
                                'question': question,
                                'grade': grade_level,
                                'topic': topic,
                                'incept_v1': incept_data
                            }
                            existing_data.append(new_entry)
                            logger.info(f"✅ Created new entry with incept_v1 data")
                        
                        # Write updated data back to JSON
                        with open(json_path, 'w') as f:
                            json.dump(existing_data, f, indent=2)
                        
                        logger.info(f"✅ Saved to JSON: {json_path}")
                        logger.info(f"Time taken: {time_taken}s")
                        
                    else:
                        failed_generations += 1
                        logger.error("❌ Failed to generate image")
                        
                        # Create failed incept_v1 data
                        incept_data = {
                            "image_url": None,
                            "time_taken": time_taken,
                            "quality_feedback": "Generation failed",
                            "api_version": "v1",
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "error": "Failed to generate image via API"
                        }
                        
                        # Re-read and update JSON
                        if os.path.exists(json_path):
                            with open(json_path, 'r') as f:
                                try:
                                    existing_data = json.load(f)
                                except json.JSONDecodeError:
                                    existing_data = []
                        
                        # Find matching entry by question and add incept_v1 data
                        entry_found = False
                        for i, entry in enumerate(existing_data):
                            if entry.get('question') == question:
                                # Add incept_v1 to existing entry
                                existing_data[i]['incept_v1'] = incept_data
                                entry_found = True
                                logger.info(f"✅ Updated existing entry with failed incept_v1 data")
                                break
                        
                        # If no matching entry found, create new entry
                        if not entry_found:
                            new_entry = {
                                'question': question,
                                'grade': grade_level,
                                'topic': topic,
                                'incept_v1': incept_data
                            }
                            existing_data.append(new_entry)
                            logger.info(f"✅ Created new entry with failed incept_v1 data")
                        
                        with open(json_path, 'w') as f:
                            json.dump(existing_data, f, indent=2)
                        
                except Exception as e:
                    failed_generations += 1
                    logger.error(f"❌ Error: {e}")
                
                # Add delay between requests to avoid rate limiting
                await asyncio.sleep(2)
    
    # Print summary statistics
    logger.info(f"\n{'='*50}")
    logger.info("TEST SUMMARY")
    logger.info(f"{'='*50}")
    logger.info(f"Total questions: {total_questions}")
    logger.info(f"Skipped (already exists): {skipped_questions}")
    logger.info(f"Attempted: {total_questions - skipped_questions}")
    logger.info(f"Successful: {successful_generations}")
    logger.info(f"Failed: {failed_generations}")
    if total_questions - skipped_questions > 0:
        success_rate = (successful_generations / (total_questions - skipped_questions)) * 100
        logger.info(f"Success rate: {success_rate:.1f}%")
    logger.info(f"Results saved to: {json_path}")


if __name__ == "__main__":
    asyncio.run(test_curriculum_questions())