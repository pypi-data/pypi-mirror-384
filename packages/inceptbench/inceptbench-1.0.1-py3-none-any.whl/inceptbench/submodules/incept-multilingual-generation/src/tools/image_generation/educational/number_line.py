"""
Number line visualization tool for mathematical concepts
"""

import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
import time
import os

from src.utils.supabase_client import SupabaseStorage

logger = logging.getLogger(__name__)


def generate_number_line(
    start: float,
    end: float,
    marks: Optional[List[float]] = None,
    highlight_points: Optional[List[Dict[str, any]]] = None,
    intervals: Optional[int] = None,
    show_arrows: bool = True,
    title: Optional[str] = None,
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate a number line visualization.
    
    Parameters
    ----------
    start : float
        Starting value of number line
    end : float
        Ending value of number line
    marks : list of float, optional
        Specific points to mark on the line
    highlight_points : list of dict, optional
        Points to highlight with special markers
        Each dict should have: 'value', 'label', 'color', 'style'
    intervals : int, optional
        Number of intervals to divide the line into
    show_arrows : bool
        Show arrows at the ends
    title : str, optional
        Title for the number line
    background_color : str
        Background color
    
    Returns
    -------
    str or None
        URL of generated image or None if failed
    """
    try:
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 4), facecolor='white')
        
        # Calculate line position
        y_pos = 0
        line_length = end - start
        padding = line_length * 0.1
        
        # Set up axes
        ax.set_xlim(start - padding, end + padding)
        ax.set_ylim(-0.5, 0.5)
        ax.axis('off')
        
        # Draw main line
        if show_arrows:
            # Line with arrows
            ax.annotate('', xy=(end + padding/2, y_pos), xytext=(start - padding/2, y_pos),
                       arrowprops=dict(arrowstyle='<->', color='black', lw=2))
        else:
            # Simple line
            ax.plot([start, end], [y_pos, y_pos], 'k-', linewidth=2)
        
        # Add tick marks
        if intervals:
            tick_values = np.linspace(start, end, intervals + 1)
        elif marks:
            tick_values = marks
        else:
            # Default to integer values
            tick_values = np.arange(np.ceil(start), np.floor(end) + 1)
        
        # Draw tick marks and labels
        for value in tick_values:
            if start <= value <= end:
                # Tick mark
                ax.plot([value, value], [-0.05, 0.05], 'k-', linewidth=1)
                
                # Label all tick marks to provide context
                label = int(value) if value == int(value) else f"{value:.1f}"
                ax.text(value, -0.15, str(label), ha='center', va='top', fontsize=12)
        
        # Add highlight points
        if highlight_points:
            for point in highlight_points:
                value = point['value']
                if start <= value <= end:
                    label = point.get('label', '')
                    color = point.get('color', 'red')
                    style = point.get('style', 'o')
                    
                    # Draw point
                    ax.plot(value, y_pos, style, color=color, markersize=10, 
                           markeredgecolor='black', markeredgewidth=1)
                    
                    # Add label if provided
                    if label:
                        ax.text(value, 0.15, label, ha='center', va='bottom', 
                               fontsize=10, color=color, fontweight='bold')
        
        # Add title
        if title:
            ax.text((start + end) / 2, 0.4, title, ha='center', va='center', 
                   fontsize=14, fontweight='bold')
        
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
        filename = f"number_line_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved number line locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"educational/{filename}")
            if public_url:
                logger.info(f"Uploaded number line to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating number line: {e}")
        return None
    finally:
        plt.close('all')