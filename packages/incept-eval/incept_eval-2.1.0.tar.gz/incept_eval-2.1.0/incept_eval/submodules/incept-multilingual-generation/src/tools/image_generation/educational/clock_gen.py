"""
Clock visualization tool for educational time-related problems
"""

import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import logging
from typing import Optional, Tuple
import time
import os

from src.utils.supabase_client import SupabaseStorage

logger = logging.getLogger(__name__)


def generate_clock_image(
    hour: int,
    minute: int,
    show_digital: bool = False,
    clock_style: str = 'analog',
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate a clock image showing specific time.
    
    Parameters
    ----------
    hour : int
        Hour (0-23 for 24-hour format, will be converted to 12-hour for display)
    minute : int
        Minute (0-59)
    show_digital : bool
        Show digital time display below clock
    clock_style : str
        Style of clock ('analog', 'simple', 'educational')
    background_color : str
        Background color
    language : str
        Language for any text labels (e.g., 'English', 'Arabic', 'Spanish')
    
    Returns
    -------
    str or None
        URL of generated image or None if failed
    """
    try:
        # Validate inputs
        if not 0 <= hour <= 23:
            raise ValueError("Hour must be between 0 and 23")
        if not 0 <= minute <= 59:
            raise ValueError("Minute must be between 0 and 59")
        
        # Convert to 12-hour format
        display_hour = hour % 12
        if display_hour == 0:
            display_hour = 12
        
        # Create figure
        fig, ax = plt.subplots(figsize=(8, 8), facecolor='white')
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Draw clock circle
        circle = patches.Circle((0, 0), 1, fill=False, edgecolor='black', linewidth=3)
        ax.add_patch(circle)
        
        # Draw center dot
        center = patches.Circle((0, 0), 0.05, fill=True, color='black')
        ax.add_patch(center)
        
        # Draw hour marks and numbers
        for i in range(12):
            angle = np.pi/2 - i * np.pi/6  # Start from 12 o'clock
            
            # Hour marks
            x1 = 0.9 * np.cos(angle)
            y1 = 0.9 * np.sin(angle)
            x2 = 0.8 * np.cos(angle)
            y2 = 0.8 * np.sin(angle)
            
            ax.plot([x1, x2], [y1, y2], 'k-', linewidth=2)
            
            # Hour numbers
            number = 12 if i == 0 else i
            x_text = 0.7 * np.cos(angle)
            y_text = 0.7 * np.sin(angle)
            ax.text(x_text, y_text, str(number), fontsize=16, 
                   ha='center', va='center', fontweight='bold')
        
        # Draw minute marks
        for i in range(60):
            if i % 5 != 0:  # Skip hour positions
                angle = np.pi/2 - i * np.pi/30
                x1 = 0.95 * np.cos(angle)
                y1 = 0.95 * np.sin(angle)
                x2 = 0.9 * np.cos(angle)
                y2 = 0.9 * np.sin(angle)
                ax.plot([x1, x2], [y1, y2], 'k-', linewidth=1)
        
        # Calculate hand angles
        hour_angle = np.pi/2 - (display_hour % 12 + minute/60) * np.pi/6
        minute_angle = np.pi/2 - minute * np.pi/30
        
        # Draw hour hand
        hour_x = 0.5 * np.cos(hour_angle)
        hour_y = 0.5 * np.sin(hour_angle)
        ax.plot([0, hour_x], [0, hour_y], 'k-', linewidth=6, solid_capstyle='round')
        
        # Draw minute hand
        minute_x = 0.8 * np.cos(minute_angle)
        minute_y = 0.8 * np.sin(minute_angle)
        ax.plot([0, minute_x], [0, minute_y], 'k-', linewidth=4, solid_capstyle='round')
        
        # Add digital time if requested
        if show_digital:
            time_str = f"{display_hour:d}:{minute:02d}"
            if hour >= 12:
                time_str += " PM"
            else:
                time_str += " AM"
            ax.text(0, -1.4, time_str, fontsize=20, ha='center', va='center', 
                   fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray"))
        
        plt.tight_layout()
        
        # Save to buffer
        buf = io.BytesIO()
        fig.savefig(
            buf,
            format='png',
            dpi=150,
            bbox_inches='tight',
            facecolor='white',
            transparent=False
        )
        buf.seek(0)
        
        # Generate filename
        timestamp = int(time.time() * 1000)
        filename = f"clock_{hour}_{minute}_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved clock image locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"educational/{filename}")
            if public_url:
                logger.info(f"Uploaded clock image to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating clock image: {e}")
        return None
    finally:
        plt.close('all')