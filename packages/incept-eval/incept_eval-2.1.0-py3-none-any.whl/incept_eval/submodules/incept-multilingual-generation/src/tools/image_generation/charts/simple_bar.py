"""
Bar chart generation tool for educational visualizations
"""

import io
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import logging
from typing import Optional, Dict, Any, List
from PIL import Image
import time
import os

from src.utils.supabase_client import SupabaseStorage
from src.tools.image_generation.color_utils import validate_color_list

# Set matplotlib to use a non-interactive backend
matplotlib.use('Agg')

logger = logging.getLogger(__name__)


def generate_simple_bar(
    series: List[Dict[str, Any]],
    title: str,
    xlabel: str,
    ylabel: str,
    width: float = 0.8,
    xlim: Optional[Dict[str, float]] = None,
    ylim: Optional[Dict[str, float]] = None,
    legend: bool = True,
    xtick_rotation: float = 0,
    y_axis_interval: Optional[float] = None,
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate a bar chart for educational purposes.
    
    Parameters
    ----------
    series : list of dict
        Each dict must have:
        - 'categories': list of category names
        - 'values': list of values for each category
        - 'label': series name
        - 'color': color for bars
    title : str
        Chart title
    xlabel : str
        X-axis label
    ylabel : str
        Y-axis label
    width : float
        Bar width (0-1)
    xlim : dict, optional
        X-axis limits {'min': float, 'max': float}
    ylim : dict, optional
        Y-axis limits {'min': float, 'max': float}
    legend : bool
        Show legend
    xtick_rotation : float
        Rotation angle for x-axis labels
    y_axis_interval : float, optional
        Y-axis tick interval
    background_color : str
        Background color ('transparent' or matplotlib color)
    
    Returns
    -------
    str or None
        URL of generated chart or None if failed
    """
    try:
        # Create figure with white background for the chart area
        fig = plt.figure(figsize=(10, 8), facecolor='white')
        ax = fig.add_subplot(111, facecolor='white')
        
        # Validate series data
        if not series or not all(len(s['categories']) == len(s['values']) for s in series):
            raise ValueError("Invalid series data: categories and values must have same length")
        
        n_series = len(series)
        categories = series[0]['categories']
        n_cats = len(categories)
        indices = np.arange(n_cats)
        bar_width = width / n_series

        # Plot each series
        for i, s in enumerate(series):
            validated_color = validate_color_list(s['color'], default=f'C{i}')
            offset = (i - n_series/2 + 0.5) * bar_width
            
            ax.bar(
                indices + offset,
                s['values'],
                bar_width,
                label=s['label'],
                color=validated_color,
                edgecolor='black',
                linewidth=1
            )

        # Configure axes
        ax.set_xticks(indices)
        ax.set_xticklabels(categories, rotation=xtick_rotation, ha='right' if xtick_rotation > 0 else 'center')
        
        # Set labels and title
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel(xlabel, fontsize=14)
        ax.set_ylabel(ylabel, fontsize=14)
        
        # Set axis limits if provided
        if xlim:
            ax.set_xlim(xlim['min'], xlim['max'])
        if ylim:
            ax.set_ylim(ylim['min'], ylim['max'])
        
        # Set y-axis interval if specified
        if y_axis_interval:
            ymin, ymax = ax.get_ylim()
            yticks = np.arange(
                np.ceil(ymin / y_axis_interval) * y_axis_interval,
                np.floor(ymax / y_axis_interval) * y_axis_interval + y_axis_interval,
                y_axis_interval
            )
            ax.set_yticks(yticks)
        
        # Add legend if requested (show even for single series)
        if legend:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
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
        filename = f"bar_chart_{timestamp}.png"
        
        # Save locally first
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved bar chart locally: {local_path}")
        
        # Try to upload to Supabase
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"charts/{filename}")
            if public_url:
                logger.info(f"Uploaded bar chart to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        # Return local path as fallback
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating bar chart: {e}")
        return None
    finally:
        plt.close('all')