"""
Histogram generation tool for educational visualizations
"""

import io
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import logging
from typing import List, Optional, Union
import time
import os

from src.utils.supabase_client import SupabaseStorage
from src.tools.image_generation.color_utils import normalize_color

matplotlib.use('Agg')
logger = logging.getLogger(__name__)


def generate_simple_histogram(
    data: List[float],
    title: str,
    xlabel: str,
    ylabel: str = "Frequency",
    bins: Union[int, List[float]] = 10,
    color: str = 'blue',
    show_normal_curve: bool = False,
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate a histogram for educational purposes.
    
    Parameters
    ----------
    data : list of float
        Data values to plot
    title : str
        Chart title
    xlabel : str
        X-axis label
    ylabel : str
        Y-axis label
    bins : int or list of float
        Number of bins or bin edges
    color : str
        Bar color
    show_normal_curve : bool
        Overlay normal distribution curve
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
        
        # Validate color
        validated_color = normalize_color(color)
        
        # Create histogram
        n, bins_arr, patches = ax.hist(
            data,
            bins=bins,
            color=validated_color,
            alpha=0.7,
            edgecolor='black',
            linewidth=1
        )
        
        # Add normal curve if requested
        if show_normal_curve:
            mu = np.mean(data)
            sigma = np.std(data)
            x = np.linspace(min(data), max(data), 100)
            y = ((1 / (np.sqrt(2 * np.pi) * sigma)) *
                 np.exp(-0.5 * ((x - mu) / sigma)**2))
            # Scale to match histogram
            y = y * len(data) * (bins_arr[1] - bins_arr[0])
            ax.plot(x, y, 'r-', linewidth=2, label='Normal curve')
            ax.legend()
        
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
        filename = f"histogram_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved histogram locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"charts/{filename}")
            if public_url:
                logger.info(f"Uploaded histogram to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating histogram: {e}")
        return None
    finally:
        plt.close('all')