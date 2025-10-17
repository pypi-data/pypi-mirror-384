"""
Scatter plot generation tool for educational visualizations
"""

import io
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import logging
from typing import List, Dict, Any, Optional
import time
import os

from src.utils.supabase_client import SupabaseStorage
from src.tools.image_generation.color_utils import validate_color_list

matplotlib.use('Agg')
logger = logging.getLogger(__name__)


def generate_simple_scatter(
    series: List[Dict[str, Any]],
    title: str,
    xlabel: str,
    ylabel: str,
    xlim: Optional[Dict[str, float]] = None,
    ylim: Optional[Dict[str, float]] = None,
    legend: bool = True,
    grid: bool = True,
    point_size: float = 50,
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate a scatter plot for educational purposes.
    
    Parameters
    ----------
    series : list of dict
        Each dict must have:
        - 'x_values': list of x coordinates
        - 'y_values': list of y coordinates
        - 'label': series name
        - 'color': point color
        - 'marker': marker style ('o', 's', '^', 'D', etc.)
    title : str
        Chart title
    xlabel : str
        X-axis label
    ylabel : str
        Y-axis label
    xlim : dict, optional
        X-axis limits {'min': float, 'max': float}
    ylim : dict, optional
        Y-axis limits {'min': float, 'max': float}
    legend : bool
        Show legend
    grid : bool
        Show grid
    point_size : float
        Size of scatter points
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
        
        # Plot each series
        for i, s in enumerate(series):
            validated_color = validate_color_list(s.get('color', f'C{i}'))
            marker = s.get('marker', 'o')
            
            ax.scatter(
                s['x_values'],
                s['y_values'],
                color=validated_color,
                marker=marker,
                s=point_size,
                alpha=0.7,
                edgecolors='black',
                linewidth=1,
                label=s['label']
            )
        
        # Configure axes
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        
        # Set axis limits if provided
        if xlim:
            ax.set_xlim(xlim['min'], xlim['max'])
        if ylim:
            ax.set_ylim(ylim['min'], ylim['max'])
        
        # Add grid
        if grid:
            ax.grid(True, alpha=0.3, linestyle='--')
        
        # Add legend
        if legend and len(series) > 1:
            ax.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        
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
        filename = f"scatter_plot_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved scatter plot locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"charts/{filename}")
            if public_url:
                logger.info(f"Uploaded scatter plot to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating scatter plot: {e}")
        return None
    finally:
        plt.close('all')