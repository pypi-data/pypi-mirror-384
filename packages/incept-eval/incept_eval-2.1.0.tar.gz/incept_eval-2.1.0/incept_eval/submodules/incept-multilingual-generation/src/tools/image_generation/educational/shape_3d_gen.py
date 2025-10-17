"""
3D geometric shape generation tool for educational visualizations
"""

import io
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
import logging
from typing import List, Dict, Optional
import time
import os
import math

from src.utils.supabase_client import SupabaseStorage
from src.tools.image_generation.color_utils import validate_color_list

logger = logging.getLogger(__name__)


def generate_3d_shape_image(
    shape_type: str,
    dimensions: Dict[str, float],
    rotation: Optional[Dict[str, float]] = None,
    show_edges: bool = True,
    show_labels: bool = True,
    color: str = 'lightblue',
    title: Optional[str] = None,
    background_color: str = 'transparent',
    units: Optional[str] = None
) -> Optional[str]:
    """
    Generate 3D geometric shapes for educational purposes.
    
    Parameters
    ----------
    shape_type : str
        Type of shape: 'cube', 'cuboid', 'pyramid', 'cylinder', 'sphere', 'cone', 'triangular_prism'
    dimensions : dict
        Shape dimensions (e.g., {'side': 1} for cube, {'length': 2, 'width': 1, 'height': 1.5} for cuboid)
    rotation : dict, optional
        Rotation angles in degrees {'x': 0, 'y': 0, 'z': 0}
    show_edges : bool
        Show edge lines
    show_labels : bool
        Show dimension labels
    color : str
        Shape color
    title : str, optional
        Title for the image
    background_color : str
    units : str, optional
        Unit of measurement (e.g., 'cm', 'm', 'ft'). If None, no units shown
        Background color
    
    Returns
    -------
    str or None
        URL of generated image or None if failed
    """
    try:
        
        # Create figure
        fig = plt.figure(figsize=(10, 8), facecolor='white')
        ax = fig.add_subplot(111, projection='3d')
        ax.set_facecolor('white')
        
        # Validate color
        color = validate_color_list(color)
        
        # Set rotation
        if rotation:
            ax.view_init(elev=rotation.get('x', 30), azim=rotation.get('y', 45))
        
        if shape_type.lower() == 'cube':
            side = dimensions.get('side') or 1  # Default to 1 if None
            volume = dimensions.get('volume')
            show_side = dimensions.get('show_side', True)
            show_volume = dimensions.get('show_volume', False)
            logger.info(f"CUBE DEBUG: side={side}, volume={volume}, show_side={show_side}, show_volume={show_volume}")
            # Use unit cube for display to avoid axis scaling issues
            display_side = 1 if show_volume and not show_side else side
            vertices = _create_cube_vertices(display_side)
            logger.info(f"CUBE DEBUG: using display_side={display_side}, vertices shape={vertices.shape}, min={vertices.min()}, max={vertices.max()}")
            _draw_cube(ax, vertices, color, show_edges)
            
            if show_labels:
                if show_volume and volume:
                    volume_label = f'Volume = {volume}' if not units else f'Volume = {volume} {units}³'
                    # Use display_side for positioning to match the actual rendered cube
                    ax.text(0, 0, display_side + 0.5, volume_label, fontsize=12, ha='center')
                if show_side:
                    label = f'{side}' if not units else f'{side} {units}'
                    ax.text(side/2, -side*0.4, 0, label, fontsize=12, ha='center')
                
        elif shape_type.lower() == 'cuboid':
            length = dimensions.get('length') or 2
            width = dimensions.get('width') or 1
            height = dimensions.get('height') or 1.5
            show_length = dimensions.get('show_length', True)
            show_width = dimensions.get('show_width', True) 
            show_height = dimensions.get('show_height', True)
            vertices = _create_cuboid_vertices(length, width, height)
            _draw_cube(ax, vertices, color, show_edges)
            
            if show_labels:
                if show_length:
                    l_label = f'{length}' if not units else f'{length} {units}'
                    ax.text(length/2, -width*0.4, 0, l_label, fontsize=12, ha='center')
                if show_width:
                    w_label = f'{width}' if not units else f'{width} {units}'
                    ax.text(-length*0.3, width/2, 0, w_label, fontsize=12, ha='center')
                if show_height:
                    h_label = f'{height}' if not units else f'{height} {units}'
                    ax.text(-length*0.4, 0, height/2, h_label, fontsize=12, ha='center')
                
        elif shape_type.lower() == 'pyramid':
            base_side = dimensions.get('base_side') or 1
            base_area = dimensions.get('base_area')
            height = dimensions.get('height') or 1.5
            slant_height = dimensions.get('slant_height')
            
            _draw_pyramid(ax, base_side, height, color, show_edges, slant_height, show_labels, units)
            
            if show_labels:
                # Show base area if provided, otherwise show base side
                if base_area:
                    base_label = f'Base area = {base_area}' if not units else f'Base area = {base_area} {units}²'
                    ax.text(base_side*0.8, base_side*0.8, 0, base_label, fontsize=12, ha='center')
                else:
                    # Label a specific base edge directly
                    base_label = f'{base_side}' if not units else f'{base_side} {units}'
                    ax.text(base_side/2, -base_side*0.3, 0, base_label, fontsize=12, ha='center')
                
                # Show slant height if provided, otherwise show height
                if slant_height:
                    # Position slant height label parallel to the dotted slant line
                    slant_label = f'{slant_height}' if not units else f'{slant_height} {units}'
                    # Place label at midpoint of slant line (from apex to midpoint of front edge)
                    midpoint_front_edge = [base_side/2, 0, 0]
                    apex_pos = [base_side/2, base_side/2, height]
                    # Midpoint of the slant line
                    label_x = (apex_pos[0] + midpoint_front_edge[0]) / 2
                    label_y = (apex_pos[1] + midpoint_front_edge[1]) / 2  
                    label_z = (apex_pos[2] + midpoint_front_edge[2]) / 2
                    # Calculate rotation angle to make label parallel to slant line
                    
                    angle = math.degrees(math.atan2(height, base_side/2))
                    ax.text(label_x, label_y - 0.3, label_z, slant_label, fontsize=12, ha='center', rotation=angle)
                else:
                    h_label = f'h = {height}' if not units else f'h = {height} {units}'
                    ax.text(base_side*0.3, base_side*1.0, height*0.7, h_label, fontsize=12, ha='center')
                
        elif shape_type.lower() == 'cylinder':
            radius = dimensions.get('radius') or 0.5
            height = dimensions.get('height') or 1.5
            _draw_cylinder(ax, radius, height, color)
            
            if show_labels:
                r_label = f'r = {radius}' if not units else f'r = {radius} {units}'
                h_label = f'h = {height}' if not units else f'h = {height} {units}'
                ax.text(radius, 0, -height*0.1, r_label, fontsize=12, ha='center')
                ax.text(-radius*1.5, 0, height/2, h_label, fontsize=12, ha='center')
                
        elif shape_type.lower() == 'sphere':
            radius = dimensions.get('radius') or 1
            _draw_sphere(ax, radius, color)
            
            if show_labels:
                r_label = f'r = {radius}' if not units else f'r = {radius} {units}'
                ax.text(0, 0, -radius*1.3, r_label, fontsize=12, ha='center')
                
        elif shape_type.lower() == 'cone':
            radius = dimensions.get('radius') or 0.5
            height = dimensions.get('height') or 1.5
            slant_height = dimensions.get('slant_height')
            
            # If slant height is given, calculate actual height: h = sqrt(l² - r²)
            if slant_height:
                height = math.sqrt(slant_height**2 - radius**2)
            
            _draw_cone(ax, radius, height, color, slant_height, show_labels, units)
            
            if show_labels:
                r_label = f'r = {radius}' if not units else f'r = {radius} {units}'
                ax.text(radius, 0, -height*0.1, r_label, fontsize=12, ha='center')
                
                # Show slant height if provided, otherwise show height
                if slant_height:
                    l_label = f'l = {slant_height}' if not units else f'l = {slant_height} {units}'
                    # Position slant height label along the slant edge
                    ax.text(radius*0.7, 0, height*0.7, l_label, fontsize=12, ha='center', rotation=45)
                else:
                    h_label = f'h = {height}' if not units else f'h = {height} {units}'
                    ax.text(-radius*1.5, 0, height/2, h_label, fontsize=12, ha='center')
                
        elif shape_type.lower() == 'triangular_prism':
            base_side = dimensions.get('base_side') or 1
            height = dimensions.get('height') or 1.5
            base_area = dimensions.get('base_area')
            _draw_triangular_prism(ax, base_side, height, color, show_edges)
            
            if show_labels:
                # Show base area if provided, otherwise show base side
                if base_area:
                    base_label = f'Base area = {base_area}' if not units else f'Base area = {base_area} {units}²'
                else:
                    base_label = f'Base: {base_side}' if not units else f'Base: {base_side} {units}'
                h_label = f'h = {height}' if not units else f'h = {height} {units}'
                ax.text(base_side/2, -base_side*0.4, 0, base_label, fontsize=12, ha='center')
                ax.text(-base_side*0.4, 0, height/2, h_label, fontsize=12, ha='center')
        
        # Set aspect ratio based on actual dimensions
        if shape_type.lower() == 'cuboid':
            length = dimensions.get('length') or 1
            width = dimensions.get('width') or 1 
            height = dimensions.get('height') or 1
            # Check if it's actually a cube (all dimensions equal)
            if length == width == height:
                logger.info(f"ASPECT DEBUG: Cuboid with equal dims [{length},{width},{height}] - using [1,1,1]")
                ax.set_box_aspect([1, 1, 1])
            else:
                logger.info(f"ASPECT DEBUG: Cuboid with different dims - using [{length},{width},{height}]")
                ax.set_box_aspect([length, width, height])
        elif shape_type.lower() == 'cube':
            # Always use equal aspect ratio for cubes
            logger.info(f"ASPECT DEBUG: Cube shape - using [1,1,1]")
            ax.set_box_aspect([1, 1, 1])
        else:
            logger.info(f"ASPECT DEBUG: Other shape ({shape_type}) - using [1,1,1]")
            ax.set_box_aspect([1, 1, 1])
        
        # Completely hide all axes
        ax.axis('off')
        
        # Add title
        if title:
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
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
        filename = f"shape_3d_{shape_type}_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved 3D shape locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"educational/{filename}")
            if public_url:
                logger.info(f"Uploaded 3D shape to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating 3D shape: {e}")
        return None
    finally:
        plt.close('all')


def _create_cube_vertices(side):
    """Create vertices for a cube"""
    return np.array([
        [0, 0, 0],
        [side, 0, 0],
        [side, side, 0],
        [0, side, 0],
        [0, 0, side],
        [side, 0, side],
        [side, side, side],
        [0, side, side]
    ])


def _create_cuboid_vertices(length, width, height):
    """Create vertices for a cuboid"""
    return np.array([
        [0, 0, 0],
        [length, 0, 0],
        [length, width, 0],
        [0, width, 0],
        [0, 0, height],
        [length, 0, height],
        [length, width, height],
        [0, width, height]
    ])


def _draw_cube(ax, vertices, color, show_edges):
    """Draw a cube/cuboid with the given vertices"""
    # Define the faces
    faces = [
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # Front
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # Right
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # Back
        [vertices[3], vertices[0], vertices[4], vertices[7]],  # Left
        [vertices[0], vertices[1], vertices[2], vertices[3]],  # Bottom
        [vertices[4], vertices[5], vertices[6], vertices[7]]   # Top
    ]
    
    # Draw faces
    face_collection = Poly3DCollection(faces, alpha=0.6, facecolor=color, 
                                     edgecolor='black' if show_edges else 'none', 
                                     linewidth=2)
    ax.add_collection3d(face_collection)
    
    # Set limits with equal padding for all axes to maintain cube proportions
    ax.set_xlim(-max(vertices[:, 0]) * 0.5, max(vertices[:, 0]) * 1.5)
    ax.set_ylim(-max(vertices[:, 1]) * 0.5, max(vertices[:, 1]) * 1.5)
    ax.set_zlim(-max(vertices[:, 2]) * 0.5, max(vertices[:, 2]) * 1.5)


def _draw_pyramid(ax, base_side, height, color, show_edges, slant_height=None, show_labels=True, units=None):
    """Draw a square pyramid with optional slant height line"""
    # Base vertices
    base_vertices = np.array([
        [0, 0, 0],
        [base_side, 0, 0],
        [base_side, base_side, 0],
        [0, base_side, 0]
    ])
    
    # Apex
    apex = np.array([base_side/2, base_side/2, height])
    
    # Create faces
    faces = [
        base_vertices,  # Base
        [base_vertices[0], base_vertices[1], apex],  # Front
        [base_vertices[1], base_vertices[2], apex],  # Right
        [base_vertices[2], base_vertices[3], apex],  # Back
        [base_vertices[3], base_vertices[0], apex]   # Left
    ]
    
    # Draw faces
    face_collection = Poly3DCollection(faces, alpha=0.6, facecolor=color,
                                     edgecolor='black' if show_edges else 'none',
                                     linewidth=2)
    ax.add_collection3d(face_collection)
    
    # Draw slant height line if provided
    if slant_height and show_labels:
        # Draw a line from apex to midpoint of front base edge to show slant height
        midpoint_front_edge = np.array([base_side/2, 0, 0])
        ax.plot([apex[0], midpoint_front_edge[0]], 
               [apex[1], midpoint_front_edge[1]], 
               [apex[2], midpoint_front_edge[2]], 
               'k--', linewidth=3, alpha=1.0)
    
    # Set limits
    ax.set_xlim(-base_side*0.2, base_side*1.2)
    ax.set_ylim(-base_side*0.2, base_side*1.2)
    ax.set_zlim(0, height*1.2)


def _draw_cylinder(ax, radius, height, color):
    """Draw a cylinder"""
    z = np.linspace(0, height, 50)
    theta = np.linspace(0, 2*np.pi, 50)
    theta_grid, z_grid = np.meshgrid(theta, z)
    
    x_grid = radius * np.cos(theta_grid)
    y_grid = radius * np.sin(theta_grid)
    
    ax.plot_surface(x_grid, y_grid, z_grid, alpha=0.6, color=color)
    
    # Draw top and bottom circles
    circle_theta = np.linspace(0, 2*np.pi, 50)
    circle_x = radius * np.cos(circle_theta)
    circle_y = radius * np.sin(circle_theta)
    
    ax.plot(circle_x, circle_y, 0, 'k-', linewidth=2)
    ax.plot(circle_x, circle_y, height, 'k-', linewidth=2)
    
    # Set limits
    ax.set_xlim(-radius*1.5, radius*1.5)
    ax.set_ylim(-radius*1.5, radius*1.5)
    ax.set_zlim(0, height*1.2)


def _draw_sphere(ax, radius, color):
    """Draw a sphere"""
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 50)
    
    x = radius * np.outer(np.cos(u), np.sin(v))
    y = radius * np.outer(np.sin(u), np.sin(v))
    z = radius * np.outer(np.ones(np.size(u)), np.cos(v))
    
    ax.plot_surface(x, y, z, alpha=0.6, color=color)
    
    # Set limits
    ax.set_xlim(-radius*1.2, radius*1.2)
    ax.set_ylim(-radius*1.2, radius*1.2)
    ax.set_zlim(-radius*1.2, radius*1.2)


def _draw_cone(ax, radius, height, color, slant_height=None, show_labels=True, units=None):
    """Draw a cone with optional slant height line"""
    z = np.linspace(0, height, 50)
    theta = np.linspace(0, 2*np.pi, 50)
    
    Z, Theta = np.meshgrid(z, theta)
    R = radius * (1 - Z/height)  # Radius decreases linearly with height
    
    X = R * np.cos(Theta)
    Y = R * np.sin(Theta)
    
    ax.plot_surface(X, Y, Z, alpha=0.6, color=color)
    
    # Draw base circle
    circle_theta = np.linspace(0, 2*np.pi, 50)
    circle_x = radius * np.cos(circle_theta)
    circle_y = radius * np.sin(circle_theta)
    ax.plot(circle_x, circle_y, 0, 'k-', linewidth=2)
    
    # Draw slant height line if provided
    if slant_height:
        # Draw a dashed line from base edge to apex to show slant height
        ax.plot([radius, 0], [0, 0], [0, height], 'k--', linewidth=2, alpha=0.8)
    
    # Set limits
    ax.set_xlim(-radius*1.5, radius*1.5)
    ax.set_ylim(-radius*1.5, radius*1.5)
    ax.set_zlim(0, height*1.2)


def _draw_triangular_prism(ax, base_side, height, color, show_edges):
    """Draw a triangular prism"""
    # Create triangular base vertices (equilateral triangle)
    h_tri = base_side * np.sqrt(3) / 2  # Height of equilateral triangle
    
    # Bottom triangle vertices
    bottom_vertices = np.array([
        [0, 0, 0],
        [base_side, 0, 0],
        [base_side/2, h_tri, 0]
    ])
    
    # Top triangle vertices
    top_vertices = np.array([
        [0, 0, height],
        [base_side, 0, height],
        [base_side/2, h_tri, height]
    ])
    
    # Create faces
    faces = [
        # Bottom triangle
        bottom_vertices,
        # Top triangle  
        top_vertices,
        # Rectangular faces
        [bottom_vertices[0], bottom_vertices[1], top_vertices[1], top_vertices[0]],
        [bottom_vertices[1], bottom_vertices[2], top_vertices[2], top_vertices[1]],
        [bottom_vertices[2], bottom_vertices[0], top_vertices[0], top_vertices[2]]
    ]
    
    # Draw faces
    face_collection = Poly3DCollection(faces, alpha=0.6, facecolor=color,
                                     edgecolor='black' if show_edges else 'none',
                                     linewidth=2)
    ax.add_collection3d(face_collection)
    
    # Set limits
    ax.set_xlim(-base_side*0.2, base_side*1.2)
    ax.set_ylim(-h_tri*0.2, h_tri*1.2)
    ax.set_zlim(0, height*1.2)