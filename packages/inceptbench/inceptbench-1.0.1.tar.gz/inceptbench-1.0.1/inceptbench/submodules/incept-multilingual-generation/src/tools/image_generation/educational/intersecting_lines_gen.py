"""
Intersecting lines visualization tool for geometry concepts
"""

import io
import matplotlib.pyplot as plt
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
import time
import os

from src.utils.supabase_client import SupabaseStorage

logger = logging.getLogger(__name__)


def generate_intersecting_lines_image(
    lines: List[Dict[str, any]],
    show_angles: bool = False,
    show_labels: bool = True,
    grid: bool = True,
    axis_range: float = 5,
    title: Optional[str] = None,
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate intersecting lines visualization for geometry.
    
    Parameters
    ----------
    lines : list of dict
        Each dict specifies a line with:
        - 'point1': [x, y] coordinates of first point
        - 'point2': [x, y] coordinates of second point
        - 'color': line color
        - 'label': line label
        - 'style': line style ('-', '--', '-.', ':')
    show_angles : bool
        Show angle measurements at intersections
    show_labels : bool
        Show line labels
    grid : bool
        Show coordinate grid
    axis_range : float
        Range for x and y axes (-range to +range)
    title : str, optional
        Title for the image
    background_color : str
        Background color
    
    Returns
    -------
    str or None
        URL of generated image or None if failed
    """
    try:
        # Create figure
        fig, ax = plt.subplots(figsize=(10, 10), facecolor='white')
        
        # Set up axes
        ax.set_xlim(-axis_range, axis_range)
        ax.set_ylim(-axis_range, axis_range)
        ax.set_aspect('equal')
        
        # Add grid if requested
        if grid:
            ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
            ax.axhline(y=0, color='k', linewidth=1)
            ax.axvline(x=0, color='k', linewidth=1)
        
        # Store line equations for intersection calculation
        line_equations = []
        
        # Draw each line
        for i, line in enumerate(lines):
            point1 = line['point1']
            point2 = line['point2']
            color = line.get('color', f'C{i}')
            label = line.get('label', f'Line {i+1}')
            style = line.get('style', '-')
            
            # Calculate slope and y-intercept
            if point2[0] != point1[0]:  # Not vertical
                slope = (point2[1] - point1[1]) / (point2[0] - point1[0])
                y_intercept = point1[1] - slope * point1[0]
                line_equations.append(('normal', slope, y_intercept))
            else:  # Vertical line
                line_equations.append(('vertical', point1[0], None))
            
            # Extend line across the visible area
            if point2[0] != point1[0]:  # Not vertical
                x_vals = np.linspace(-axis_range, axis_range, 100)
                y_vals = slope * x_vals + y_intercept
            else:  # Vertical line
                x_vals = [point1[0], point1[0]]
                y_vals = [-axis_range, axis_range]
            
            # Draw line
            ax.plot(x_vals, y_vals, linestyle=style, color=color, 
                   linewidth=2, label=label if show_labels else None)
            
            # Mark the defining points
            ax.plot([point1[0], point2[0]], [point1[1], point2[1]], 
                   'o', color=color, markersize=6, markeredgecolor='black')
        
        # Find and mark intersections
        intersections = []
        for i in range(len(line_equations)):
            for j in range(i+1, len(line_equations)):
                intersection = _find_intersection(line_equations[i], line_equations[j])
                if intersection and -axis_range <= intersection[0] <= axis_range and \
                   -axis_range <= intersection[1] <= axis_range:
                    intersections.append(intersection)
                    # Mark intersection point
                    ax.plot(intersection[0], intersection[1], 'ro', markersize=8,
                           markeredgecolor='black', markeredgewidth=2, zorder=10)
                    
                    # Label intersection
                    ax.text(intersection[0] + 0.3, intersection[1] + 0.3, 
                           f'({intersection[0]:.1f}, {intersection[1]:.1f})',
                           fontsize=10, ha='left', va='bottom',
                           bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))
        
        # Show angles at intersections if requested
        if show_angles and intersections:
            for intersection in intersections:
                # Calculate angles (simplified - just show that angles exist)
                ax.text(intersection[0] - 0.5, intersection[1] - 0.5, '∠',
                       fontsize=16, ha='center', va='center', color='red')
        
        # Add legend if labels are shown
        if show_labels and len(lines) > 1:
            ax.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
        
        # Add title
        if title:
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # Label axes
        ax.set_xlabel('x', fontsize=14)
        ax.set_ylabel('y', fontsize=14)
        
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
        filename = f"intersecting_lines_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved intersecting lines locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"educational/{filename}")
            if public_url:
                logger.info(f"Uploaded intersecting lines to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating intersecting lines: {e}")
        return None
    finally:
        plt.close('all')


def _find_intersection(line1, line2) -> Optional[Tuple[float, float]]:
    """Find intersection point of two lines"""
    try:
        type1, param1, param2 = line1
        type2, param3, param4 = line2
        
        if type1 == 'vertical' and type2 == 'vertical':
            return None  # Parallel vertical lines
        elif type1 == 'vertical':  # line1 vertical, line2 normal
            x = param1
            slope2, y_int2 = param3, param4
            y = slope2 * x + y_int2
            return (x, y)
        elif type2 == 'vertical':  # line2 vertical, line1 normal
            x = param3
            slope1, y_int1 = param1, param2
            y = slope1 * x + y_int1
            return (x, y)
        else:  # Both normal lines
            slope1, y_int1 = param1, param2
            slope2, y_int2 = param3, param4
            
            if abs(slope1 - slope2) < 1e-10:  # Parallel lines
                return None
            
            x = (y_int2 - y_int1) / (slope1 - slope2)
            y = slope1 * x + y_int1
            return (x, y)
    
    except:
        return None