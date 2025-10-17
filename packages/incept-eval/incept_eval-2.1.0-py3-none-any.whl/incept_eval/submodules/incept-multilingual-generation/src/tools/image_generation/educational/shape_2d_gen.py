"""
2D geometric shape generation tool for educational visualizations
"""

import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple, Union
import time
import os

from src.utils.supabase_client import SupabaseStorage
from src.tools.image_generation.color_utils import validate_color_list
from src.image_generation.types import Shape2D, Shapes2DData, CircleSize, RectangleSize, SquareSize, TriangleSize, EllipseSize, PolygonSize

logger = logging.getLogger(__name__)


def generate_2d_shape_image(
    shapes: Union[List[Dict[str, any]], List[Shape2D], Shapes2DData],
    title: Optional[str] = None,
    grid_size: Tuple[int, int] = (1, 1),
    show_labels: bool = True,
    show_measurements: bool = True,
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate 2D geometric shapes for educational purposes.
    
    Parameters
    ----------
    shapes : list of dict, list of Shape2D, or Shapes2DData
        Shape data in various formats
    title : str, optional
        Title for the image
    grid_size : tuple of int
        (rows, cols) for arranging multiple shapes
    show_labels : bool
        Show shape labels
    show_measurements : bool
        Show measurements (radius, side lengths, etc.)
    background_color : str
        Background color
    
    Returns
    -------
    str or None
        URL of generated image or None if failed
    """
    try:
        # Handle different input formats
        if isinstance(shapes, Shapes2DData):
            shape_list = shapes.shapes
            if not title:
                title = shapes.title
            show_measurements = shapes.show_measurements
            show_labels = shapes.show_labels
        elif isinstance(shapes, list) and len(shapes) > 0 and isinstance(shapes[0], Shape2D):
            shape_list = shapes
        else:
            shape_list = shapes
        
        logger.info(f"Generating 2D shapes with data: {len(shape_list)} shapes")
        
        # Create figure
        rows, cols = grid_size
        fig, axes = plt.subplots(rows, cols, figsize=(6*cols, 6*rows), facecolor='white')
        
        # Handle single subplot case
        if rows == 1 and cols == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        # Calculate appropriate axis limits based on all shapes
        max_extent = 3
        for shape in shape_list:
            # Handle both dict and Shape2D objects
            if isinstance(shape, Shape2D):
                shape_type = shape.type.lower()
                size_data = shape.size
            else:
                shape_type = shape.get('type', '').lower()
                size_data = shape.get('size', {})
            
            if shape_type == 'circle':
                if isinstance(size_data, CircleSize):
                    if size_data.radius:
                        radius = size_data.radius
                    elif size_data.diameter:
                        radius = size_data.diameter / 2
                    else:
                        radius = 1
                elif isinstance(size_data, dict):
                    radius = size_data.get('radius') or (size_data.get('diameter', 2) / 2)
                else:
                    radius = float(size_data) if size_data else 1
                max_extent = max(max_extent, radius + 1)
                
            elif shape_type == 'rectangle':
                if isinstance(size_data, RectangleSize):
                    width, height = size_data.width, size_data.height
                elif isinstance(size_data, dict):
                    width = size_data.get('width', 1.5)
                    height = size_data.get('height', 1)
                elif isinstance(size_data, list):
                    width, height = size_data if len(size_data) >= 2 else [1.5, 1]
                else:
                    width, height = 1.5, 1
                max_extent = max(max_extent, max(width, height) + 1)
                
            elif shape_type == 'square':
                if isinstance(size_data, SquareSize):
                    side = size_data.side
                    diagonal = size_data.diagonal
                elif isinstance(size_data, dict):
                    side = size_data.get('side')
                    diagonal = size_data.get('diagonal')
                else:
                    side = float(size_data) if size_data else None
                    diagonal = None
                
                max_dim = max(side or 1, diagonal or 1)
                max_extent = max(max_extent, max_dim * 0.6)
                
            elif shape_type == 'triangle':
                if isinstance(size_data, TriangleSize):
                    base_side = size_data.base_side or 1
                    left_side = size_data.left_side or 1
                    right_side = size_data.right_side or 1
                    height = size_data.height or 1
                    max_dim = max(base_side, left_side, right_side, height)
                elif isinstance(size_data, dict):
                    base_side = size_data.get('base_side', 1)
                    left_side = size_data.get('left_side', 1) 
                    right_side = size_data.get('right_side', 1)
                    height = size_data.get('height', 1)
                    max_dim = max(base_side or 1, left_side or 1, right_side or 1, height or 1)
                else:
                    max_dim = float(size_data) if size_data else 1
                max_extent = max(max_extent, max_dim * 0.6)
        
        # Draw each shape
        for idx, (ax, shape) in enumerate(zip(axes, shape_list)):
            ax.set_xlim(-max_extent, max_extent)
            ax.set_ylim(-max_extent, max_extent)
            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_facecolor('white')  # Ensure white background for each subplot
            
            # Handle both dict and Shape2D objects
            if isinstance(shape, Shape2D):
                shape_type = shape.type.lower()
                center = shape.center
                color = validate_color_list(shape.color)
                label = shape.label or ''
                size_data = shape.size
                units = shape.units or 'cm'
            else:
                shape_type = shape['type'].lower()
                center = shape.get('center', [0, 0])
                color = validate_color_list(shape.get('color', 'blue'))
                label = shape.get('label', '')
                size_data = shape.get('size', {})
                units = shape.get('units', 'cm')
            
            logger.info(f"Drawing shape: type={shape_type}, center={center}, color={color}, size={size_data}")
            
            if shape_type == 'circle':
                if isinstance(size_data, CircleSize):
                    if size_data.radius:
                        radius = size_data.radius
                    elif size_data.diameter:
                        radius = size_data.diameter / 2
                    else:
                        radius = 1
                elif isinstance(size_data, dict):
                    radius = size_data.get('radius') or (size_data.get('diameter', 2) / 2)
                else:
                    radius = float(size_data) if size_data else 1
                    
                circle = patches.Circle(center, radius, facecolor=color, 
                                      edgecolor='black', linewidth=2)
                ax.add_patch(circle)
                
                if show_measurements:
                    # Determine if we should show radius or diameter
                    show_diameter = False
                    if isinstance(size_data, CircleSize) and size_data.diameter and not size_data.radius:
                        show_diameter = True
                    elif isinstance(size_data, dict) and size_data.get('diameter') and not size_data.get('radius'):
                        show_diameter = True
                    
                    if show_diameter:
                        # Show diameter line across the circle
                        diameter = radius * 2
                        ax.plot([center[0] - radius, center[0] + radius], [center[1], center[1]], 
                               'k--', linewidth=1)
                        ax.text(center[0], center[1] + 0.1, f'{diameter} {units}', 
                               ha='center', fontsize=10)
                    else:
                        # Show radius line
                        ax.plot([center[0], center[0] + radius], [center[1], center[1]], 
                               'k--', linewidth=1)
                        ax.text(center[0] + radius/2, center[1] + 0.1, f'r = {radius} {units}', 
                               ha='center', fontsize=10)
                
            elif shape_type == 'square':
                # Handle new SquareSize format with diagonal support
                if isinstance(size_data, SquareSize):
                    side = size_data.side
                    diagonal = size_data.diagonal
                    show_side_label = getattr(size_data, 'show_side_label', True)
                    show_diagonal_label = getattr(size_data, 'show_diagonal_label', False)
                elif isinstance(size_data, dict):
                    side = size_data.get('side')
                    diagonal = size_data.get('diagonal')
                    show_side_label = size_data.get('show_side_label', True)
                    show_diagonal_label = size_data.get('show_diagonal_label', False)
                else:
                    side = float(size_data) if size_data else 1
                    diagonal = None
                    show_side_label = True
                    show_diagonal_label = False
                
                # Calculate dimensions - if only diagonal given, calculate side for rendering
                if side is None and diagonal:
                    side = diagonal / np.sqrt(2)  # For rendering only, don't show this calculated value
                elif side is None:
                    side = 1  # Default fallback
                
                # Draw the square
                square = patches.Rectangle((center[0] - side/2, center[1] - side/2), 
                                         side, side, facecolor=color, 
                                         edgecolor='black', linewidth=2)
                ax.add_patch(square)
                
                # Add measurements based on flags
                display_units = units if units else ""
                if show_measurements:
                    # Show side label only if requested and side value is known
                    if show_side_label and size_data.get('side') if isinstance(size_data, dict) else (isinstance(size_data, SquareSize) and size_data.side):
                        ax.text(center[0], center[1] - side/2 - 0.8, 
                               f'{size_data.get("side") if isinstance(size_data, dict) else size_data.side} {display_units}'.strip(), 
                               ha='center', fontsize=10)
                    
                    # Show diagonal line and label if requested
                    if show_diagonal_label and diagonal:
                        # Draw diagonal line from bottom-left to top-right
                        ax.plot([center[0] - side/2, center[0] + side/2], 
                               [center[1] - side/2, center[1] + side/2], 
                               'k--', linewidth=2)
                        # Label the diagonal
                        ax.text(center[0] + side/4, center[1] + side/4, 
                               f'{diagonal} {display_units}'.strip(), 
                               ha='center', va='bottom', fontsize=10, rotation=45)
                
            elif shape_type == 'rectangle':
                if isinstance(size_data, RectangleSize):
                    width = size_data.width
                    height = size_data.height
                elif isinstance(size_data, dict):
                    width = size_data.get('width', 1.5)
                    height = size_data.get('height', 1)
                elif isinstance(size_data, list) and len(size_data) >= 2:
                    width, height = size_data[0], size_data[1]
                else:
                    width, height = 1.5, 1
                
                rect = patches.Rectangle((center[0] - width/2, center[1] - height/2), 
                                       width, height, facecolor=color, 
                                       edgecolor='black', linewidth=2)
                ax.add_patch(rect)
                
                if show_measurements:
                    display_units = units if units else ""
                    ax.text(center[0], center[1] - height/2 - 0.8, f'{width} {display_units}'.strip() if display_units else str(width), 
                           ha='center', fontsize=10)
                    ax.text(center[0] - width/2 - 0.3, center[1], f'{height} {display_units}'.strip() if display_units else str(height), 
                           ha='right', va='center', fontsize=10, rotation=90)
                
            elif shape_type == 'triangle':
                # COMPREHENSIVE TRIANGLE HANDLING FOR ALL CASES
                
                # Initialize defaults
                base_side, left_side, right_side = None, None, None
                triangle_type = None
                height = None
                show_base, show_left, show_right, show_height = False, False, False, False
                angle_base_left, angle_left_right, angle_right_base = None, None, None
                
                logger.info(f"TRIANGLE INPUT: size_data type = {type(size_data)}, is TriangleSize = {isinstance(size_data, TriangleSize)}, is dict = {isinstance(size_data, dict)}")
                
                # Extract data based on input type
                if isinstance(size_data, TriangleSize):
                    base_side = size_data.base_side
                    left_side = size_data.left_side
                    right_side = size_data.right_side
                    triangle_type = size_data.triangle_type
                    height = size_data.height
                    
                    show_base = size_data.show_base_label if hasattr(size_data, 'show_base_label') else False
                    show_left = size_data.show_left_label if hasattr(size_data, 'show_left_label') else False
                    show_right = size_data.show_right_label if hasattr(size_data, 'show_right_label') else False
                    show_height = size_data.show_height_label if hasattr(size_data, 'show_height_label') else False
                    
                    logger.info(f"TRIANGLE SHOW FLAGS: show_base={show_base}, show_left={show_left}, show_right={show_right}, show_height={show_height}")
                    
                    # Extract angle data
                    angle_base_left = getattr(size_data, 'angle_base_left', None)
                    angle_left_right = getattr(size_data, 'angle_left_right', None)  # Top vertex angle
                    angle_right_base = getattr(size_data, 'angle_right_base', None)
                            
                elif isinstance(size_data, dict):
                    base_side = size_data.get('base_side')
                    left_side = size_data.get('left_side')
                    right_side = size_data.get('right_side')
                    triangle_type = size_data.get('triangle_type')
                    height = size_data.get('height')
                    
                    angle_base_left = size_data.get('angle_base_left')
                    angle_left_right = size_data.get('angle_left_right')
                    angle_right_base = size_data.get('angle_right_base')
                    
                    # Get show flags from dict
                    show_base = size_data.get('show_base_label', False)
                    show_left = size_data.get('show_left_label', False)
                    show_right = size_data.get('show_right_label', False)
                    show_height = size_data.get('show_height_label', False)
                    
                    logger.info(f"DICT TRIANGLE SHOW FLAGS: show_base={show_base}, show_left={show_left}, show_right={show_right}, show_height={show_height}")
                            
                else:
                    # Simple float input - assume equilateral
                    side_length = float(size_data) if size_data else 2
                    base_side = left_side = right_side = side_length
                    triangle_type = 'equilateral'
                
                # Apply defaults if no sides specified
                if not any([base_side, left_side, right_side]):
                    base_side = left_side = right_side = 2
                    # Don't override triangle_type if it was already set (e.g., for angle problems)
                    if not triangle_type:
                        triangle_type = 'equilateral'
                
                logger.info(f"TRIANGLE DEBUG: After defaults - base_side={base_side}, left_side={left_side}, right_side={right_side}")
                    
                # Base length is always base_side since it's explicitly the base
                base_length = base_side or 2
                
                # Calculate triangle height for visualization
                if height:
                    triangle_height = height
                elif triangle_type == 'equilateral':
                    triangle_height = base_length * np.sqrt(3) / 2
                elif triangle_type == 'right':
                    # For right triangles, calculate height using Pythagorean theorem
                    # right_side is hypotenuse, base_side is base, left_side is height
                    if right_side and base_side:
                        # height = sqrt(hypotenuse^2 - base^2)
                        triangle_height = np.sqrt(right_side**2 - base_side**2)
                    elif left_side and base_side:
                        # left_side is the height, base_side is the base
                        triangle_height = left_side
                    elif left_side and right_side:
                        # Need to determine which is hypotenuse (longest side)
                        if right_side > left_side:
                            triangle_height = left_side
                            base_length = np.sqrt(right_side**2 - left_side**2)
                        else:
                            triangle_height = right_side
                            base_length = np.sqrt(left_side**2 - right_side**2)
                    else:
                        triangle_height = base_length * 0.8  # Default fallback
                elif triangle_type == 'isosceles':
                    # For isosceles, calculate height from base and equal sides
                    # In an isosceles triangle, left_side == right_side
                    if left_side and right_side and left_side == right_side:
                        # Calculate height using Pythagorean theorem
                        triangle_height = np.sqrt(left_side**2 - (base_length/2)**2) if left_side > base_length/2 else base_length * 0.8
                    else:
                        triangle_height = base_length * 0.8  # Default ratio
                else:
                    triangle_height = base_length * 0.8  # Default ratio
                
                # Create vertices based on triangle type
                if triangle_type == 'right':
                    # Right triangle - right angle at bottom left
                    vertices = [
                        [center[0] - base_length/2, center[1] - triangle_height/2],  # Bottom left (right angle)
                        [center[0] + base_length/2, center[1] - triangle_height/2],  # Bottom right
                        [center[0] - base_length/2, center[1] + triangle_height/2]   # Top left
                    ]
                else:
                    # Isosceles or equilateral - symmetric about vertical axis
                    vertices = [
                        [center[0], center[1] + triangle_height/2],              # Top apex
                        [center[0] - base_length/2, center[1] - triangle_height/2],  # Bottom left
                        [center[0] + base_length/2, center[1] - triangle_height/2]   # Bottom right
                    ]
                
                # Draw the triangle
                triangle = patches.Polygon(vertices, facecolor=color, edgecolor='black', linewidth=2)
                ax.add_patch(triangle)
                
                # Add right angle indicator for right triangles
                if triangle_type == 'right':
                    corner_size = min(base_length, triangle_height) * 0.15
                    right_angle_square = patches.Rectangle(
                        (center[0] - base_length/2, center[1] - triangle_height/2),
                        corner_size, corner_size,
                        facecolor='none', edgecolor='black', linewidth=1.5
                    )
                    ax.add_patch(right_angle_square)
                
                # Add measurements based on show flags  
                logger.info(f"MEASUREMENT DEBUG: show_measurements={show_measurements}, units={units}, show_base={show_base}, show_left={show_left}, show_right={show_right}")
                # Allow measurements without units for pure geometry problems (base/height)
                display_units = units if units else ""
                logger.info(f"MEASUREMENT DEBUG: condition result = {show_measurements and (show_base or show_left or show_right or show_height)}")
                if show_measurements and (show_base or show_left or show_right or show_height):  # Show measurements if requested, with or without units
                    # Show measurements for the triangle sides
                    # Base is ALWAYS at the bottom
                    if show_base and base_side:
                        ax.text(center[0], center[1] - triangle_height/2 - 0.6, 
                               f'{base_side} {display_units}'.strip() if display_units else str(base_side),
                               ha='center', va='top', fontsize=10)
                    
                    # Left side
                    if show_left and left_side:
                        if triangle_type == 'right':
                            # For right triangle, left side is the vertical leg - position on left edge
                            ax.text(center[0] - base_length/2 - 0.3, center[1], 
                                   f'{left_side} {display_units}'.strip() if display_units else str(left_side),
                                   ha='right', va='center', fontsize=10, rotation=90)
                        else:
                            # For other triangles, position on left diagonal
                            ax.text(center[0] - base_length/4, center[1] + triangle_height/6, 
                                   f'{left_side} {display_units}'.strip() if display_units else str(left_side),
                                   ha='center', va='center', fontsize=10, rotation=60)
                    
                    # Right side
                    if show_right and right_side:
                        if triangle_type == 'right':
                            # For right triangle, right side is the hypotenuse - position horizontally above diagonal
                            ax.text(center[0] + base_length/4, center[1] + triangle_height/4,
                                   f'{right_side} {display_units}'.strip() if display_units else str(right_side),
                                   ha='center', va='center', fontsize=10)
                        else:
                            # For other triangles, position on right diagonal
                            ax.text(center[0] + base_length/4, center[1] + triangle_height/6,
                                   f'{right_side} {display_units}'.strip() if display_units else str(right_side),
                                   ha='center', va='center', fontsize=10, rotation=-60)
                    
                    # Add height line and label if requested
                    if show_height and height:
                        if triangle_type == 'right':
                            # Height line on left side for right triangles
                            ax.plot([center[0] - base_length/2, center[0] - base_length/2],
                                   [center[1] - triangle_height/2, center[1] + triangle_height/2],
                                   'k--', linewidth=1)
                            ax.text(center[0] - base_length/2 - 0.6, center[1], f'{height} {display_units}'.strip() if display_units else str(height),
                                   ha='right', va='center', fontsize=10, rotation=90)
                        else:
                            # Height line from apex to base for isosceles/equilateral
                            ax.plot([center[0], center[0]],
                                   [center[1] - triangle_height/2, center[1] + triangle_height/2],
                                   'k--', linewidth=1)
                            ax.text(center[0] + 0.4, center[1], f'{height} {display_units}'.strip() if display_units else str(height),
                                   ha='left', va='center', fontsize=10, rotation=90)
                
                # Add angle labels if any angles are specified
                logger.info(f"ANGLE CHECK: angle_base_left={angle_base_left}, angle_left_right={angle_left_right}, angle_right_base={angle_right_base}")
                if any([angle_base_left, angle_left_right, angle_right_base]):
                    logger.info(f"ANGLE DEBUG: Angles detected, proceeding with angle display")
                    # DON'T calculate missing angles - that reveals the answer!
                    # Only show given angles, not calculated ones
                    
                    # Position angle labels AT the actual angle vertices
                    # Base-left angle (bottom left vertex)
                    if angle_base_left:
                        ax.text(center[0] - base_length/2 + 0.3, center[1] - triangle_height/2 + 0.2, f'{angle_base_left}°',
                               ha='left', va='bottom', fontsize=10)
                    
                    # Left-right angle (top vertex)  
                    if angle_left_right:
                        ax.text(center[0], center[1] + triangle_height/2 - 0.8, f'{angle_left_right}°',
                               ha='center', va='center', fontsize=10)
                    
                    # Right-base angle (bottom right vertex)
                    if angle_right_base:
                        ax.text(center[0] + base_length/2 - 0.9, center[1] - triangle_height/2 + 0.2, f'{angle_right_base}°',
                               ha='center', va='center', fontsize=9)
                
            elif shape_type == 'polygon':
                # Handle both dict and Shape2D objects properly
                if isinstance(shape, Shape2D):
                    # Don't get sides from shape - it doesn't have this attribute
                    # Extract all data from size_data
                    if isinstance(size_data, PolygonSize):
                        radius = size_data.radius or 2
                        n_sides = size_data.sides or 4
                        angle_offset = size_data.rotation or 0
                    else:
                        radius = 2  # Default radius
                        n_sides = 4  # Default sides
                        angle_offset = 0
                else:
                    n_sides = shape.get('sides', 4)
                    size_info = shape.get('size', {})
                    if isinstance(size_info, dict):
                        radius = size_info.get('radius', 2)
                        angle_offset = size_info.get('rotation', 0)
                        n_sides = size_info.get('sides', n_sides)
                    else:
                        radius = float(size_info) if isinstance(size_info, (int, float)) else 2
                        angle_offset = shape.get('rotation', 0)
                
                angles = np.linspace(0, 2*np.pi, n_sides+1) + angle_offset
                vertices = [[center[0] + radius*np.cos(a), 
                           center[1] + radius*np.sin(a)] for a in angles[:-1]]
                
                polygon = patches.Polygon(vertices, facecolor=color, 
                                        edgecolor='black', linewidth=2)
                ax.add_patch(polygon)
                
            elif shape_type == 'ellipse':
                # Handle both dict and Shape2D objects properly
                if isinstance(shape, Shape2D):
                    if isinstance(size_data, EllipseSize):
                        width = size_data.width or 1.5
                        height = size_data.height or 1
                        angle = size_data.angle or 0
                    else:
                        width, height = 1.5, 1
                        angle = 0
                else:
                    size_info = shape.get('size', [1.5, 1])
                    if isinstance(size_info, dict):
                        width = size_info.get('width', 1.5)
                        height = size_info.get('height', 1)
                        angle = size_info.get('angle', 0)
                    elif isinstance(size_info, list) and len(size_info) >= 2:
                        width, height = size_info[0], size_info[1]
                        angle = shape.get('angle', 0)
                    else:
                        width, height = 1.5, 1
                        angle = shape.get('angle', 0)
                
                ellipse = patches.Ellipse(center, width, height, angle=angle,
                                        facecolor=color, edgecolor='black', linewidth=2)
                ax.add_patch(ellipse)
            
            # Add label only if non-empty and not answer-revealing
            if show_labels and label and label.strip():
                ax.text(center[0], center[1] - 1.5, label, ha='center', 
                       fontsize=14, fontweight='bold')
        
        # Hide unused subplots
        for idx in range(len(shape_list), len(axes)):
            axes[idx].axis('off')
        
        # Add title only if not default/stupid titles
        if title and not any(stupid in title.lower() for stupid in ['extracted', 'information', '2d shape']):
            fig.suptitle(title, fontsize=16, fontweight='bold')
        
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
        filename = f"shapes_2d_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved 2D shapes locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"educational/{filename}")
            if public_url:
                logger.info(f"Uploaded 2D shapes to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating 2D shapes: {e}")
        return None
    finally:
        plt.close('all')