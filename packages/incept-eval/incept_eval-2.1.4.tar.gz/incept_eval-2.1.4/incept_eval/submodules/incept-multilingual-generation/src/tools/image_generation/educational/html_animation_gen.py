"""
HTML animation generation tool for educational concepts
"""

import logging
import time
import os
from typing import Optional
import tempfile
import subprocess

from src.utils.supabase_client import SupabaseStorage

logger = logging.getLogger(__name__)


def generate_animation(
    description: str,
    duration: int = 5,
    width: int = 800,
    height: int = 600,
    background_color: str = 'white'
) -> Optional[str]:
    """
    Generate an HTML animation and convert to GIF.
    
    Parameters
    ----------
    description : str
        Description of the animation to create
    duration : int
        Animation duration in seconds
    width : int
        Animation width in pixels
    height : int
        Animation height in pixels
    background_color : str
        Background color
    
    Returns
    -------
    str or None
        URL of generated GIF or None if failed
    """
    try:
        logger.info(f"Generating animation: {description[:100]}...")
        
        # Generate HTML animation content using LLM
        html_content = _generate_html_animation(description, duration, width, height, background_color)
        
        if not html_content:
            logger.error("Failed to generate HTML content")
            return None
        
        # Save HTML to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as html_file:
            html_file.write(html_content)
            html_path = html_file.name
        
        try:
            # Generate output filename
            timestamp = int(time.time() * 1000)
            gif_filename = f"animation_{timestamp}.gif"
            
            # Save locally
            os.makedirs("generated_images", exist_ok=True)
            local_path = f"generated_images/{gif_filename}"
            
            # For now, just create a placeholder (would need additional tools for HTML->GIF conversion)
            # In production, you'd use tools like puppeteer, playwright, or similar
            logger.warning("HTML to GIF conversion not implemented - returning HTML file")
            
            # Copy HTML to generated_images for now
            html_local_path = f"generated_images/animation_{timestamp}.html"
            with open(html_local_path, 'w') as f:
                f.write(html_content)
            
            logger.info(f"Saved animation HTML locally: {html_local_path}")
            
            # Try to upload HTML
            try:
                storage = SupabaseStorage()
                public_url = storage.upload_image(html_local_path, f"animations/animation_{timestamp}.html")
                if public_url:
                    logger.info(f"Uploaded animation to Supabase: {public_url}")
                    return public_url
            except Exception as e:
                logger.warning(f"Failed to upload to Supabase: {e}")
            
            return html_local_path
            
        finally:
            # Clean up temp file
            if os.path.exists(html_path):
                os.remove(html_path)
        
    except Exception as e:
        logger.error(f"Error generating animation: {e}")
        return None


def _generate_html_animation(description: str, duration: int, width: int, height: int, background_color: str) -> Optional[str]:
    """Generate HTML animation content using LLM"""
    try:
        from src.llms import llm_gpt5
        
        prompt = f"""Create an HTML5 animation that illustrates: {description}

Requirements:
- Duration: {duration} seconds
- Canvas size: {width}x{height} pixels
- Background: {background_color}
- Use JavaScript for animation
- Make it educational and clear
- Include smooth transitions
- Loop the animation

Create a complete HTML document with embedded CSS and JavaScript.
Only return the HTML code, nothing else."""

        response = llm_gpt5.invoke(prompt)
        return response.content
        
    except Exception as e:
        logger.error(f"Failed to generate HTML content: {e}")
        return None