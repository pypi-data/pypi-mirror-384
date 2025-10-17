#!/usr/bin/env python3
"""
Test pipeline image generation for curriculum questions
"""

import asyncio
import os
import logging
import json
import time
from src.image_gen_module import ImageGenModule
from src.config import Config
from tests.test_questions import TEST_QUESTIONS

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

# Force enable image generation for testing
Config.ENABLE_IMAGE_GENERATION = True

curriculum_mcqs = TEST_QUESTIONS

class MockQuestion:
    def __init__(self, question_text):
        self.question_text = question_text

async def test_pipeline_questions():
    """Test pipeline image generation for all curriculum questions"""
    
    # Initialize the pipeline image generation module
    image_gen_module = ImageGenModule()
    
    # JSON file path - use absolute path to ensure consistency
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    json_path = os.path.join(project_root, "data", "imagen.json")
    
    logger.info(f"JSON path: {json_path}")
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    
    # Load existing questions to skip
    existing_questions = set()
    existing_data = []
    
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r') as f:
                existing_data = json.load(f)
                for item in existing_data:
                    # Check if this question already has pipeline_v1 generator
                    if 'pipeline_v1' in item:
                        existing_questions.add((item.get('question', ''), 'pipeline_v1'))
            logger.info(f"Found {len(existing_questions)} existing pipeline questions in JSON")
        except json.JSONDecodeError:
            logger.warning("JSON file exists but is empty or invalid, starting fresh")
            existing_data = []
    else:
        # Create empty JSON file
        with open(json_path, 'w') as f:
            json.dump([], f)
    
    # Process each grade level
    for grade_level, topics in curriculum_mcqs.items():
        logger.info(f"\\n{'='*50}")
        logger.info(f"Testing Grade: {grade_level}")
        logger.info(f"{'='*50}")
        
        # Process each topic in the grade
        for topic, question in topics.items():
            # Check if this question already exists with pipeline_v1 generator
            if (question, 'pipeline_v1') in existing_questions:
                logger.info(f"\\n⏭️  Skipping (already exists): {question}")
                continue
                
            logger.info(f"\\nTopic: {topic}")
            logger.info(f"Question: {question}")
            
            try:
                # Create mock question object
                mock_question = MockQuestion(question)
                
                # Generate image using pipeline
                logger.info("Generating image using pipeline...")
                start_time = time.time()
                results = image_gen_module.generate_images_parallel([mock_question])
                end_time = time.time()
                time_taken = end_time - start_time
                
                # Extract Gemini URL from results (pipeline uses Gemini)
                image_url = None
                if results and len(results) > 0 and results[0]:
                    image_url = results[0].get('gemini')
                
                if image_url:
                    logger.info(f"✅ Success! Image URL: {image_url}")
                    
                    # Append to JSON
                    try:
                        # Re-read latest file before updating
                        if os.path.exists(json_path):
                            with open(json_path, 'r') as f:
                                existing_data = json.load(f)
                        else:
                            existing_data = []
                        
                        # Find existing entry or create new one
                        existing_entry = None
                        for entry in existing_data:
                            if entry['question'] == question:
                                existing_entry = entry
                                break
                        
                        if existing_entry:
                            # Only update pipeline_v1, preserve all other fields
                            existing_entry['pipeline_v1'] = {
                                "image_url": image_url,
                                "time_taken": round(time_taken, 2),
                                "quality_feedback": "No quality check performed"
                            }
                        else:
                            # Create new entry with only required fields
                            new_entry = {
                                'question': question,
                                'grade': grade_level,
                                'topic': topic,
                                'pipeline_v1': {
                                    "image_url": image_url,
                                    "time_taken": round(time_taken, 2),
                                    "quality_feedback": "No quality check performed"
                                }
                            }
                            existing_data.append(new_entry)
                        
                        # Write entire JSON file
                        with open(json_path, 'w') as f:
                            json.dump(existing_data, f, indent=2)
                        
                        logger.info(f"✅ Saved to JSON: {json_path}")
                        logger.info(f"JSON now has {len(existing_data)} entries")
                    except Exception as e:
                        logger.error(f"Failed to write to JSON: {e}")
                else:
                    logger.error("❌ Failed to generate image")
                    
            except Exception as e:
                logger.error(f"❌ Error: {e}")
            
            # Delay between requests to avoid rate limiting
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(test_pipeline_questions())