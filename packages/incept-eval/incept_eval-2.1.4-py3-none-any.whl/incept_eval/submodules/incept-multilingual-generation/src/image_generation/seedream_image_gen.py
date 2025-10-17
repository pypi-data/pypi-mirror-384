"""
Seedream 4.0 Image Generation Module
Uses BytePlus ARK API to generate educational images with Seedream 4.0 model
"""

import os
import json
import logging
import asyncio
import aiohttp
import time
from typing import Optional, Dict, Any
from src.config import Config
from src.utils.supabase_client import SupabaseStorage

logger = logging.getLogger(__name__)


class SeedreamImageGenerator:
    """Handles image generation using Seedream 4.0 model via BytePlus ARK API"""
    
    def __init__(self):
        self.api_key = os.getenv("ARK_API_KEY")
        self.base_url = "https://ark.ap-southeast.bytepluses.com/api/v3/images/generations"
        self.model = "seedream-4-0-250828"
        
        if not self.api_key:
            logger.warning("ARK_API_KEY not found in environment variables")
    
    async def generate_image_async(
        self,
        prompt: str,
        size: str = "2K",
        watermark: bool = False,
        sequential_image_generation: str = "disabled"
    ) -> Optional[str]:
        """
        Generate an image using Seedream 4.0 model asynchronously.
        
        Args:
            prompt: Text description of the image to generate
            size: Image size (1K, 2K, 4K, etc.)
            watermark: Whether to add watermark to the image
            sequential_image_generation: Enable/disable sequential generation
            
        Returns:
            URL of the generated image or None if failed
        """
        if not self.api_key:
            logger.error("ARK_API_KEY not configured")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "sequential_image_generation": sequential_image_generation,
            "response_format": "url",
            "size": size,
            "stream": False,
            "watermark": watermark
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract the first image URL from the response
                        if data.get("data") and len(data["data"]) > 0:
                            image_url = data["data"][0].get("url")
                            image_size = data["data"][0].get("size", "unknown")
                            
                            logger.info(f"✅ Seedream: Generated image ({image_size})")
                            
                            # Download and upload to Supabase like other generators
                            try:
                                # Download the image
                                async with session.get(image_url) as img_response:
                                    if img_response.status == 200:
                                        image_data = await img_response.read()
                                        
                                        # Save locally first
                                        images_dir = "generated_images"
                                        os.makedirs(images_dir, exist_ok=True)
                                        timestamp = int(time.time() * 1000)
                                        filename = f"{images_dir}/generated_image_{timestamp}.png"
                                        
                                        with open(filename, "wb") as f:
                                            f.write(image_data)
                                        
                                        # Upload to Supabase
                                        storage = SupabaseStorage()
                                        public_url = storage.upload_image(filename, f"generated/{os.path.basename(filename)}")
                                        
                                        if public_url:
                                            logger.info(f"Uploaded Seedream image to Supabase: {public_url}")
                                            return public_url
                                        else:
                                            logger.warning("Failed to upload to Supabase, returning original URL")
                                            return image_url
                                    else:
                                        logger.error(f"Failed to download Seedream image: {img_response.status}")
                                        return image_url
                                        
                            except Exception as e:
                                logger.warning(f"Failed to upload Seedream image to Supabase: {e}")
                                return image_url
                        else:
                            logger.warning("Seedream: No image data in response")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Seedream API error {response.status}: {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("Seedream: Request timed out after 60 seconds")
            return None
        except Exception as e:
            logger.error(f"Seedream: Generation failed - {str(e)}")
            return None
    
    def generate_image(
        self,
        prompt: str,
        size: str = "2K",
        watermark: bool = False
    ) -> Optional[str]:
        """
        Synchronous wrapper for image generation.
        
        Args:
            prompt: Text description of the image to generate
            size: Image size (1K, 2K, 4K, etc.)
            watermark: Whether to add watermark
            
        Returns:
            URL of the generated image or None if failed
        """
        try:
            # Handle existing event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an event loop, need to run in executor
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.generate_image_async(prompt, size, watermark)
                    )
                    return future.result()
            except RuntimeError:
                # No event loop, we can use asyncio.run
                return asyncio.run(self.generate_image_async(prompt, size, watermark))
        except Exception as e:
            logger.error(f"Seedream sync wrapper error: {e}")
            return None

    async def edit_image_async(
        self,
        original_image_url: str,
        edit_instruction: str,
        size: str = "2K",
        watermark: bool = False,
        sequential_image_generation: str = "disabled"
    ) -> Optional[str]:
        """
        Edit an existing image using Seedream 4.0 model asynchronously.
        
        Args:
            original_image_url: URL of the original image to edit
            edit_instruction: Text description of how to edit the image
            size: Image size (1K, 2K, 4K, etc.)
            watermark: Whether to add watermark to the image
            sequential_image_generation: Enable/disable sequential generation
            
        Returns:
            URL of the edited image or None if failed
        """
        if not self.api_key:
            logger.error("ARK_API_KEY not configured")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "prompt": edit_instruction,
            "image": original_image_url,
            "sequential_image_generation": sequential_image_generation,
            "response_format": "url",
            "size": size,
            "stream": False,
            "watermark": watermark
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract the first image URL from the response
                        if data.get("data") and len(data["data"]) > 0:
                            image_url = data["data"][0].get("url")
                            image_size = data["data"][0].get("size", "unknown")
                            
                            logger.info(f"✅ Seedream: Edited image ({image_size})")
                            
                            # Download and upload to Supabase like other generators
                            try:
                                # Download the edited image
                                async with session.get(image_url) as img_response:
                                    if img_response.status == 200:
                                        image_data = await img_response.read()
                                        
                                        # Save locally first
                                        images_dir = "generated_images"
                                        os.makedirs(images_dir, exist_ok=True)
                                        timestamp = int(time.time() * 1000)
                                        filename = f"{images_dir}/edited_image_{timestamp}.png"
                                        
                                        with open(filename, "wb") as f:
                                            f.write(image_data)
                                        
                                        # Upload to Supabase
                                        storage = SupabaseStorage()
                                        public_url = storage.upload_image(filename, f"generated/{os.path.basename(filename)}")
                                        
                                        if public_url:
                                            logger.info(f"Uploaded edited image to Supabase: {public_url}")
                                            return public_url
                                        else:
                                            logger.warning("Failed to upload edited image to Supabase, returning original URL")
                                            return image_url
                                    else:
                                        logger.error(f"Failed to download edited image: {img_response.status}")
                                        return image_url
                                        
                            except Exception as e:
                                logger.warning(f"Failed to upload edited image to Supabase: {e}")
                                return image_url
                        else:
                            logger.warning("Seedream: No image data in edit response")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"Seedream edit API error {response.status}: {error_text}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("Seedream: Edit request timed out after 60 seconds")
            return None
        except Exception as e:
            logger.error(f"Seedream: Edit failed - {str(e)}")
            return None




async def generate_image_seedream(
    prompt: str,
    size: str = "2K",
    watermark: bool = False
) -> Optional[str]:
    """
    Main entry point for Seedream image generation.
    
    Args:
        prompt: Description of the image to generate
        size: Image size (1K, 2K, 4K)
        watermark: Whether to add watermark
        
    Returns:
        URL of generated image or None if failed
    """
    generator = SeedreamImageGenerator()
    
    return await generator.generate_image_async(
        prompt=prompt,
        size=size,
        watermark=watermark
    )


async def edit_image_seedream(
    original_image_url: str,
    edit_instruction: str,
    size: str = "2K",
    watermark: bool = False
) -> Optional[str]:
    """
    Main entry point for Seedream image editing.
    
    Args:
        original_image_url: URL of the original image to edit
        edit_instruction: Description of how to edit the image
        size: Image size (1K, 2K, 4K)
        watermark: Whether to add watermark
        
    Returns:
        URL of edited image or None if failed
    """
    generator = SeedreamImageGenerator()
    
    return await generator.edit_image_async(
        original_image_url=original_image_url,
        edit_instruction=edit_instruction,
        size=size,
        watermark=watermark
    )


# Convenience function for quick testing
def test_seedream_generation():
    """Test function to verify Seedream integration"""
    import asyncio
    
    test_prompt = "A simple mathematics classroom with geometric shapes on the blackboard, educational illustration, clear and simple"
    
    async def test():
        url = await generate_image_seedream(
            prompt=test_prompt,
            size="1K"
        )
        if url:
            print(f"✅ Test successful! Image URL: {url}")
        else:
            print("❌ Test failed - no image generated")
    
    asyncio.run(test())


if __name__ == "__main__":
    test_seedream_generation()