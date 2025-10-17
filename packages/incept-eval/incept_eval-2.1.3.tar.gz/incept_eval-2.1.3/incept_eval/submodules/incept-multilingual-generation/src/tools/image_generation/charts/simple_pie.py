"""
Pie chart generation tool for educational visualizations
"""

import io
import matplotlib.pyplot as plt
import matplotlib
import logging
from typing import List, Optional
import time
import os

from src.utils.supabase_client import SupabaseStorage
from src.tools.image_generation.color_utils import validate_color_list

matplotlib.use('Agg')
logger = logging.getLogger(__name__)


def generate_simple_pie(
    labels: List[str],
    values: List[float],
    title: str,
    colors: Optional[List[str]] = None,
    explode: Optional[List[float]] = None,
    show_percentages: bool = True,
    show_legend: bool = True,
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate a pie chart for educational purposes.
    
    Parameters
    ----------
    labels : list of str
        Labels for each slice
    values : list of float
        Values for each slice
    title : str
        Chart title
    colors : list of str, optional
        Colors for each slice
    explode : list of float, optional
        Explosion values for each slice (0-1)
    show_percentages : bool
        Show percentage labels
    show_legend : bool
        Show legend for the slices
    background_color : str
        Background color
    
    Returns
    -------
    str or None
        URL of generated chart or None if failed
    """
    try:
        # Validate input
        if len(labels) != len(values):
            raise ValueError("Labels and values must have same length")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
        
        # Prepare colors
        if colors:
            colors = validate_color_list(colors)
        else:
            colors = plt.cm.Set3.colors[:len(labels)]
        
        # Create pie chart
        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            colors=colors,
            explode=explode,
            autopct='%1.1f%%' if show_percentages else '',
            shadow=True,
            startangle=90
        )
        
        # Style the text
        for text in texts:
            text.set_fontsize(12)
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(10)
            autotext.set_weight('bold')
        
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Add legend if requested
        if show_legend:
            ax.legend(labels, loc='center left', bbox_to_anchor=(1, 0.5))
        
        # Equal aspect ratio ensures circular pie
        ax.axis('equal')
        
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format='png',
            dpi=150,
            bbox_inches='tight',
            facecolor='white' if background_color != 'transparent' else background_color,
            transparent=(background_color == 'transparent')
        )
        buf.seek(0)
        
        # Generate filename
        timestamp = int(time.time() * 1000)
        filename = f"pie_chart_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved pie chart locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"charts/{filename}")
            if public_url:
                logger.info(f"Uploaded pie chart to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating pie chart: {e}")
        return None
    finally:
        plt.close('all')