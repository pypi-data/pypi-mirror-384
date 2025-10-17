"""
Color validation utilities for matplotlib chart tools.

This module provides functions to validate and normalize color values
to prevent matplotlib color errors.
"""

import matplotlib.colors as mcolors
from typing import Union, List


def is_valid_matplotlib_color(color: str) -> bool:
    """
    Check if a color is valid for matplotlib.
    
    Parameters
    ----------
    color : str
        Color name or hex code to validate
        
    Returns
    -------
    bool
        True if color is valid, False otherwise
    """
    if not isinstance(color, str):
        return False
        
    # Check for transparent
    if color.lower() == 'transparent':
        return True
        
    try:
        # Try to convert color - this will raise ValueError if invalid
        mcolors.to_rgba(color)
        return True
    except (ValueError, TypeError):
        return False


def normalize_color(color: str, default: str = 'blue') -> str:
    """
    Normalize a color value to a valid matplotlib color.
    
    Parameters
    ----------
    color : str
        Color name or hex code to normalize
    default : str
        Default color to use if input is invalid
        
    Returns
    -------
    str
        Valid matplotlib color
    """
    if not isinstance(color, str) or not color.strip():
        return default
        
    # Handle transparent
    if color.lower() == 'transparent':
        return 'transparent'
    
    # Fix common invalid colors
    color_fixes = {
        'lightred': 'lightcoral',
        'darkred': 'darkred',  # Already valid
        'lightblue': 'lightblue',  # Already valid
    }
    
    fixed_color = color_fixes.get(color.lower(), color)
    
    if is_valid_matplotlib_color(fixed_color):
        return fixed_color
    else:
        return default


def validate_color_list(colors: Union[str, List[str]], default: str = 'blue') -> Union[str, List[str]]:
    """
    Validate and normalize a color or list of colors.
    
    Parameters
    ----------
    colors : str or List[str]
        Single color or list of colors to validate
    default : str
        Default color to use for invalid colors
        
    Returns
    -------
    str or List[str]
        Validated color(s)
    """
    if isinstance(colors, str):
        return normalize_color(colors, default)
    elif isinstance(colors, list):
        return [normalize_color(c, default) for c in colors]
    else:
        return default