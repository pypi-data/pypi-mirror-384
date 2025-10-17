"""
Heatmap generation tool for educational visualizations
"""

import io
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import logging
from typing import List, Optional
import time
import os

from src.utils.supabase_client import SupabaseStorage

matplotlib.use('Agg')
logger = logging.getLogger(__name__)


def generate_simple_heatmap(
    data: List[List[float]],
    title: str,
    xlabel: str,
    ylabel: str,
    x_labels: Optional[List[str]] = None,
    y_labels: Optional[List[str]] = None,
    colormap: str = 'viridis',
    show_values: bool = True,
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate a heatmap for educational purposes.
    
    Parameters
    ----------
    data : list of list of float
        2D array of values
    title : str
        Chart title
    xlabel : str
        X-axis label
    ylabel : str
        Y-axis label
    x_labels : list of str, optional
        Labels for x-axis ticks
    y_labels : list of str, optional
        Labels for y-axis ticks
    colormap : str
        Matplotlib colormap name
    show_values : bool
        Show numeric values in cells
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
        
        # Convert to numpy array
        data_array = np.array(data)
        
        # Create heatmap
        im = ax.imshow(data_array, cmap=colormap, aspect='auto')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.ax.set_ylabel('Value', rotation=270, labelpad=15)
        
        # Set ticks and labels
        if x_labels:
            ax.set_xticks(np.arange(len(x_labels)))
            ax.set_xticklabels(x_labels)
        if y_labels:
            ax.set_yticks(np.arange(len(y_labels)))
            ax.set_yticklabels(y_labels)
        
        # Rotate the tick labels for better readability
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # Add values to cells if requested
        if show_values:
            for i in range(len(data)):
                for j in range(len(data[i])):
                    text = ax.text(j, i, f'{data[i][j]:.1f}',
                                 ha="center", va="center", color="white")
        
        # Configure axes
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        
        # Style the plot
        for spine in ax.spines.values():
            spine.set_visible(False)
        
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
        filename = f"heatmap_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved heatmap locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"charts/{filename}")
            if public_url:
                logger.info(f"Uploaded heatmap to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating heatmap: {e}")
        return None
    finally:
        plt.close('all')