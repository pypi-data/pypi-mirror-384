"""
LaTeX equation rendering tool for mathematical expressions using SymPy
"""

import io
import logging
from typing import Optional
import time
import os
import re
import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from matplotlib.patches import Arc

from src.utils.supabase_client import SupabaseStorage

logger = logging.getLogger(__name__)


def generate_latex_equation_image(
    equation: str,
    fontsize: int = 20,
    color: str = 'black',
    title: Optional[str] = None,
    background_color: str = 'transparent',
    use_usetex: bool = False,        # Default to mathtext for reliability
) -> Optional[str]:
    """
    Generate an image of a LaTeX equation using matplotlib mathtext for matrix support.
    """
    try:
        # --- Normalize delimiters ---
        eq = equation.strip()
        if eq.startswith('$$') and eq.endswith('$$'):
            eq = eq[2:-2].strip()
        elif eq.startswith('$') and eq.endswith('$'):
            eq = eq[1:-1].strip()

        # --- Handle matrices by creating a custom plot ---
        def render_matrix_manually(latex_str):
            """Check if this is a matrix and render it manually with text positioning"""
            
            # Handle determinant notation
            det_patterns = [
                r'\\det\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}',
                r'\\begin\{vmatrix\}(.*?)\\end\{vmatrix\}'
            ]
            
            for pattern in det_patterns:
                match = re.search(pattern, latex_str, re.DOTALL)
                if match:
                    matrix_content = match.group(1).strip()
                    rows = [row.strip() for row in matrix_content.split(r'\\') if row.strip()]
                    if len(rows) == 2:
                        row1 = [elem.strip() for elem in rows[0].split('&')]
                        row2 = [elem.strip() for elem in rows[1].split('&')]
                        if len(row1) == 2 and len(row2) == 2:
                            return ('matrix', 'det', [[row1[0], row1[1]], [row2[0], row2[1]]], '= ?' in latex_str)
            
            # Handle regular matrices
            matrix_patterns = [
                (r'\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}', 'bracket'),
                (r'\\begin\{pmatrix\}(.*?)\\end\{pmatrix\}', 'paren')
            ]
            
            for pattern, bracket_type in matrix_patterns:
                match = re.search(pattern, latex_str, re.DOTALL)
                if match:
                    matrix_content = match.group(1).strip()
                    rows = [row.strip() for row in matrix_content.split(r'\\') if row.strip()]
                    if len(rows) == 2:
                        row1 = [elem.strip() for elem in rows[0].split('&')]
                        row2 = [elem.strip() for elem in rows[1].split('&')]
                        if len(row1) == 2 and len(row2) == 2:
                            return ('matrix', bracket_type, [[row1[0], row1[1]], [row2[0], row2[1]]], False)
            
            return ('text', latex_str)
        
        result = render_matrix_manually(eq)
        
        if result[0] == 'matrix':
            # Render matrix manually
            _, bracket_type, elements, has_question = result
            
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.set_xlim(0, 10)
            ax.set_ylim(0, 4)
            ax.axis('off')
            
            # Draw matrix elements
            ax.text(5, 2.5, elements[0][0], fontsize=fontsize, ha='center', va='center')
            ax.text(6, 2.5, elements[0][1], fontsize=fontsize, ha='center', va='center')
            ax.text(5, 1.5, elements[1][0], fontsize=fontsize, ha='center', va='center')
            ax.text(6, 1.5, elements[1][1], fontsize=fontsize, ha='center', va='center')
            
            # Draw brackets/bars
            if bracket_type == 'det':
                # Vertical lines for determinant
                ax.plot([4.5, 4.5], [1, 3], 'k-', linewidth=2)
                ax.plot([6.5, 6.5], [1, 3], 'k-', linewidth=2)
            elif bracket_type == 'bracket':
                # Square brackets
                ax.plot([4.3, 4.5, 4.5, 4.3], [3, 3, 1, 1], 'k-', linewidth=2)
                ax.plot([6.5, 6.7, 6.7, 6.5], [1, 1, 3, 3], 'k-', linewidth=2)
            elif bracket_type == 'paren':
                # Parentheses using curved lines
                # Left parenthesis
                theta_left = np.linspace(np.pi/2, 3*np.pi/2, 50)
                x_left = 4.5 + 0.2 * np.cos(theta_left)
                y_left = 2 + np.sin(theta_left)
                ax.plot(x_left, y_left, 'k-', linewidth=2)
                
                # Right parenthesis  
                theta_right = np.linspace(-np.pi/2, np.pi/2, 50)
                x_right = 6.5 + 0.2 * np.cos(theta_right)
                y_right = 2 + np.sin(theta_right)
                ax.plot(x_right, y_right, 'k-', linewidth=2)
            
            if has_question:
                ax.text(7.5, 2, '= ?', fontsize=fontsize, ha='left', va='center')
            
            if title:
                ax.text(5, 3.5, title, fontsize=fontsize+4, ha='center', va='center', weight='bold')
            
            # Save the custom matrix plot
            timestamp = int(time.time() * 1000)
            filename = f"matrix_{timestamp}.png"
            os.makedirs("generated_images", exist_ok=True)
            local_path = os.path.join("generated_images", filename)
            
            plt.tight_layout()
            fig.savefig(
                local_path,
                dpi=150,
                bbox_inches='tight',
                facecolor='white' if background_color != 'transparent' else 'none',
                transparent=(background_color == 'transparent')
            )
            plt.close(fig)
            logger.info(f"Generated matrix image: {local_path}")
            
            # Upload
            try:
                storage = SupabaseStorage()
                public_url = storage.upload_image(local_path, f"educational/{filename}")
                if public_url:
                    logger.info(f"Uploaded matrix image to Supabase: {public_url}")
                    return public_url
            except Exception as e:
                logger.warning(f"Failed to upload to Supabase: {e}")
            
            return local_path
        
        # For non-matrix equations, use regular mathtext rendering
        eq = result[1]
        
        # --- Figure/axes ---
        matplotlib.rcParams['mathtext.fontset'] = 'cm'
        rendered = f'${eq}$'

        # --- Output path ---
        timestamp = int(time.time() * 1000)
        # Only allow ASCII alphanumeric characters, spaces, hyphens, underscores
        safe_name = "".join(c for c in eq[:20] if c.isascii() and (c.isalnum() or c in (' ', '-', '_'))).rstrip().replace(' ', '_')
        # Fallback if name becomes empty after filtering
        if not safe_name:
            safe_name = "equation"
        filename = f"equation_{safe_name}_{timestamp}.png"
        os.makedirs("generated_images", exist_ok=True)
        local_path = os.path.join("generated_images", filename)

        # --- Render ---
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.text(0.5, 0.5, rendered, fontsize=fontsize, ha='center', va='center',
                transform=ax.transAxes, color=color)
        ax.axis('off')
        if title:
            ax.set_title(title, fontsize=fontsize+4, pad=20)

        plt.tight_layout()
        fig.savefig(
            local_path,
            dpi=150,
            bbox_inches='tight',
            facecolor='white' if background_color != 'transparent' else 'none',
            transparent=(background_color == 'transparent')
        )
        plt.close(fig)
        logger.info(f"Generated equation image: {local_path}")

        # --- Upload ---
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"educational/{filename}")
            if public_url:
                logger.info(f"Uploaded equation image to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")

        return local_path

    except Exception as e:
        logger.error(f"Error generating equation image: {e}")
        return None
