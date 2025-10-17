"""
Venn diagram generation tool using the venn library
"""

import io
import matplotlib.pyplot as plt
from venn import venn
import logging
import time
import os
from typing import Dict, List, Optional
from src.utils.supabase_client import SupabaseStorage
from src.llms import produce_structured_response_openai
from pydantic import BaseModel
        

logger = logging.getLogger(__name__)


def generate_venn_diagram_simple(
    sets_data: Dict[str, any],
    title: Optional[str] = None,
    colors: Optional[List[str]] = None,
    background_color: str = 'white'
) -> Optional[str]:
    """
    Generate Venn diagram using the venn library.
    
    Parameters
    ----------
    sets_data : dict
        Dictionary containing set information:
        - Should contain keys like 'A', 'B', 'C' with set data
        - Example: {'A': {1,2,3}, 'B': {2,3,4}, 'C': {3,4,5}}
    title : str, optional
        Title for the diagram
    colors : list of str, optional
        Colors for the sets
    background_color : str
        Background color
    
    Returns
    -------
    str or None
        URL of generated image or None if failed
    """
    try:
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8), facecolor=background_color)
        ax.set_facecolor(background_color)
        
        # Create the venn diagram
        if colors is None:
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFE66D', '#A8E6CF']  
        
        # Use the venn library - show only set labels, no numbers
        out = venn(sets_data, ax=ax, fmt='{size}')
        
        # Remove all number labels from the diagram
        for text in ax.texts:
            if text.get_text().isdigit():
                text.set_text('')
        
        # Add title
        if title:
            ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
        
        # Remove axis
        ax.axis('off')
        
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format='png',
            dpi=150,
            bbox_inches='tight',
            facecolor=background_color,
            transparent=(background_color == 'transparent')
        )
        buf.seek(0)
        
        # Generate filename
        timestamp = int(time.time() * 1000)
        filename = f"venn_simple_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved Venn diagram locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"charts/{filename}")
            if public_url:
                logger.info(f"Uploaded Venn diagram to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating Venn diagram with venn library: {e}")
        return None
    finally:
        plt.close('all')


def parse_venn_data_from_question(question: str) -> Optional[Dict[str, set]]:
    """
    Parse Venn diagram data from question text.
    This is a simplified parser - you may want to use LLM for complex parsing.
    """
    try:
        class VennSets(BaseModel):
            """Venn diagram set data"""
            sets: Dict[str, List[int]]  # Using List since Set isn't JSON serializable
            labels: Dict[str, str]
        
        messages = [{
            "role": "user", 
            "content": f"""Extract sets for Venn diagram from this question. 
For educational purposes, only include explicitly given information, not calculated values.

Question: {question}

Return sets as dictionaries with labels as keys and lists of elements as values.
Example: {{"sets": {{"A": [1,2,3], "B": [2,3,4]}}, "labels": {{"A": "Math", "B": "Science"}}}}"""
        }]
        
        result = produce_structured_response_openai(messages, VennSets)
        
        # Convert lists to sets
        sets_data = {}
        for key, values in result.sets.items():
            sets_data[result.labels.get(key, key)] = set(values)
        
        return sets_data
        
    except Exception as e:
        logger.error(f"Error parsing Venn data: {e}")
        return None