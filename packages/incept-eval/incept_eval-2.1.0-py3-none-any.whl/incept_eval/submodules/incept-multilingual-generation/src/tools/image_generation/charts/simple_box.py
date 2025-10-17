"""
Box plot generation tool for educational visualizations
"""

import io
import matplotlib.pyplot as plt
import matplotlib
import logging
from typing import List, Dict, Optional
import time
import os

from src.utils.supabase_client import SupabaseStorage
from src.tools.image_generation.color_utils import validate_color_list

matplotlib.use('Agg')
logger = logging.getLogger(__name__)


def generate_simple_box(
    data_sets: List[Dict[str, any]],
    title: str,
    xlabel: str,
    ylabel: str,
    show_outliers: bool = True,
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate a box plot for educational purposes.
    
    Parameters
    ----------
    data_sets : list of dict
        Each dict must have:
        - 'data': list of numeric values
        - 'label': name for this data set
    title : str
        Chart title
    xlabel : str
        X-axis label
    ylabel : str
        Y-axis label
    show_outliers : bool
        Show outlier points
    background_color : str
        Background color
    
    Returns
    -------
    str or None
        URL of generated chart or None if failed
    """
    try:
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')
        
        # Prepare data and labels
        data = [d['data'] for d in data_sets]
        labels = [d['label'] for d in data_sets]
        
        # Create box plot
        box_plot = ax.boxplot(
            data,
            labels=labels,
            patch_artist=True,
            showfliers=show_outliers,
            notch=True,
            vert=True
        )
        
        # Color the boxes
        colors = plt.cm.Set3.colors[:len(data_sets)]
        for patch, color in zip(box_plot['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        # Style the plot elements
        for element in ['whiskers', 'fliers', 'means', 'medians', 'caps']:
            if element in box_plot:
                plt.setp(box_plot[element], color='black')
        
        # Configure axes
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        
        # Style the plot
        for spine in ax.spines.values():
            spine.set_color('black')
            spine.set_linewidth(1)
        
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
        filename = f"box_plot_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved box plot locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"charts/{filename}")
            if public_url:
                logger.info(f"Uploaded box plot to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating box plot: {e}")
        return None
    finally:
        plt.close('all')