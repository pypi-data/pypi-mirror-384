#!/usr/bin/env python3
"""
Image Generation Module: Handles parallel image generation for questions using ImageGenerationAgent
Provides async interface to run in parallel with other modules
"""

import time
import logging
import asyncio
import concurrent.futures
from typing import List, Optional, Dict, Any
from src.config import Config

logger = logging.getLogger(__name__)

# Conditionally import image generation agent
try:
    if Config.ENABLE_IMAGE_GENERATION:
        from src.image_generation.image_generation_agent import ImageGenerationAgent
    else:
        ImageGenerationAgent = None
except ImportError:
    ImageGenerationAgent = None
    logger.warning("ImageGenerationAgent not available")

class ImageGenModule:
    """Module for generating images in parallel with other processing"""
    
    def __init__(self):
        if Config.ENABLE_IMAGE_GENERATION and ImageGenerationAgent:
            self.image_gen_agent = ImageGenerationAgent()
            logger.info("Image Generation Module initialized with agent")
        else:
            self.image_gen_agent = None
            logger.warning("Image Generation Module initialized without agent (disabled)")
    
    async def generate_images_async(self, questions, grade: int, subject: str) -> List[Optional[str]]:
        """Generate images for questions in parallel using ImageGenerationAgent"""
        
        if not self.image_gen_agent:
            logger.warning("🖼️ Image generation agent not available, returning empty list")
            return [None] * len(questions)
        
        logger.info(f"🖼️ IMAGE GEN: Starting parallel generation for {len(questions)} questions")
        start_time = time.time()
        
        # Create tasks for all questions
        tasks = []
        for i, question in enumerate(questions):
            question_text = getattr(question, 'question_text', str(question))
            logger.info(f"🖼️ IMAGE Q{i+1}: Queuing image generation")
            
            # Create task for each question
            task = self.image_gen_agent.generate_image_for_question(
                question=question_text,
                grade=grade,
                subject=subject
            )
            tasks.append(task)
        
        # Execute all tasks in parallel
        logger.info(f"🖼️ IMAGE GEN: Executing {len(tasks)} generation tasks in parallel")
        image_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        images = []
        successful_count = 0
        for i, result in enumerate(image_results):
            if isinstance(result, Exception):
                logger.error(f"🖼️ IMAGE Q{i+1}: Generation failed - {result}")
                images.append(None)
            elif result:
                logger.info(f"🖼️ IMAGE Q{i+1}: Successfully generated - {result}")
                images.append({'url': result})  # Wrap in dict for consistency
                successful_count += 1
            else:
                logger.warning(f"🖼️ IMAGE Q{i+1}: No image generated")
                images.append(None)
        
        total_time = time.time() - start_time
        logger.info(f"🖼️ IMAGE GEN COMPLETE: Generated {successful_count}/{len(questions)} images in {total_time:.2f}s")
        logger.info(f"🖼️ Average time per image: {total_time/len(questions):.2f}s")
        
        return images
    
    def generate_images_parallel(self, questions, grade: int, subject: str) -> List[Optional[Dict[str, str]]]:
        """Generate images for questions with proper event loop handling"""
        
        if not self.image_gen_agent:
            logger.warning("🖼️ Image generation disabled, returning empty list")
            return [None] * len(questions)
        
        # Handle existing event loop scenarios
        try:
            # Check if we're already in an event loop (like FastAPI)
            try:
                current_loop = asyncio.get_running_loop()
                logger.info("🖼️ IMAGE GEN: Running in existing event loop, using thread-based approach")
                
                def run_async_in_thread():
                    """Run async function in new thread with new event loop"""
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(
                            self.generate_images_async(questions, grade, subject)
                        )
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_async_in_thread)
                    return future.result()
                    
            except RuntimeError:
                # No event loop running, we can use asyncio.run
                logger.info("🖼️ IMAGE GEN: No existing event loop, using asyncio.run")
                return asyncio.run(self.generate_images_async(questions, grade, subject))
                
        except Exception as e:
            # If parallel execution fails, fall back to sequential
            logger.warning(f"🖼️ IMAGE GEN: Parallel execution failed ({e}), falling back to sequential")
            return self._generate_images_sequential(questions, grade, subject)
    
    def _generate_images_sequential(self, questions, grade: int, subject: str) -> List[Optional[Dict[str, str]]]:
        """Sequential fallback for image generation"""
        
        if not self.image_gen_agent:
            return [None] * len(questions)
        
        logger.info(f"🖼️ IMAGE GEN FALLBACK: Sequential generation of {len(questions)} images")
        start_time = time.time()
        images = []
        successful_count = 0
        
        for i, question in enumerate(questions):
            question_text = getattr(question, 'question_text', str(question))
            
            try:
                question_start = time.time()
                # Use synchronous wrapper if available, otherwise run in executor
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    image_url = loop.run_until_complete(
                        self.image_gen_agent.generate_image_for_question(
                            question=question_text,
                            grade=grade,
                            subject=subject
                        )
                    )
                finally:
                    loop.close()
                
                question_time = time.time() - question_start
                
                if image_url:
                    images.append({'url': image_url})
                    successful_count += 1
                    logger.info(f"🖼️ IMAGE Q{i+1}: Generated in {question_time:.2f}s - {image_url}")
                else:
                    images.append(None)
                    logger.warning(f"🖼️ IMAGE Q{i+1}: No image generated")
                    
            except Exception as e:
                logger.error(f"🖼️ IMAGE Q{i+1}: Generation failed - {e}")
                images.append(None)
        
        total_time = time.time() - start_time
        logger.info(f"🖼️ IMAGE GEN COMPLETE: Generated {successful_count}/{len(questions)} images in {total_time:.2f}s")
        
        return images