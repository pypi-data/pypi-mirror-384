"""
Ruler visualization tool for measurement concepts
"""

import io
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import logging
from typing import Optional, List
import time
import os

from src.utils.supabase_client import SupabaseStorage

logger = logging.getLogger(__name__)


def generate_ruler_image(
    length: float,
    unit: str = 'cm',
    show_minor_marks: bool = True,
    highlight_measurements: Optional[List[float]] = None,
    orientation: str = 'horizontal',
    background_color: str = 'transparent'
) -> Optional[str]:
    """
    Generate a ruler image for measurement visualization.
    
    Parameters
    ----------
    length : float
        Length of the ruler in specified units
    unit : str
        Unit of measurement ('cm', 'inch', 'mm')
    show_minor_marks : bool
        Show small division marks
    highlight_measurements : list of float, optional
        Specific measurements to highlight
    orientation : str
        'horizontal' or 'vertical'
    background_color : str
        Background color
    
    Returns
    -------
    str or None
        URL of generated image or None if failed
    """
    try:
        # Set up figure dimensions based on orientation
        if orientation == 'horizontal':
            fig_width = max(12, length)
            fig_height = 3
        else:
            fig_width = 3
            fig_height = max(12, length)
        
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), facecolor='white')
        
        # Define ruler dimensions
        if orientation == 'horizontal':
            ruler_length = length
            ruler_width = 1.5
            ax.set_xlim(-0.5, ruler_length + 0.5)
            ax.set_ylim(-1, 2)
        else:
            ruler_length = length
            ruler_width = 1.5
            ax.set_xlim(-1, 2)
            ax.set_ylim(-0.5, ruler_length + 0.5)
        
        ax.axis('off')
        
        # Draw ruler body
        if orientation == 'horizontal':
            ruler_rect = patches.Rectangle((0, 0), ruler_length, ruler_width,
                                         facecolor='lightyellow', 
                                         edgecolor='black', linewidth=2)
        else:
            ruler_rect = patches.Rectangle((0, 0), ruler_width, ruler_length,
                                         facecolor='lightyellow', 
                                         edgecolor='black', linewidth=2)
        ax.add_patch(ruler_rect)
        
        # Determine divisions based on unit
        if unit == 'cm':
            major_div = 1  # 1 cm
            minor_div = 0.1  # 1 mm
            label_interval = 1
        elif unit == 'inch':
            major_div = 1  # 1 inch
            minor_div = 0.125  # 1/8 inch
            label_interval = 1
        else:  # mm
            major_div = 10  # 10 mm
            minor_div = 1  # 1 mm
            label_interval = 10
        
        # Draw markings
        position = 0
        while position <= ruler_length:
            if orientation == 'horizontal':
                # Major mark
                if position % major_div < 0.001:  # floating point comparison
                    ax.plot([position, position], [0, 0.6], 'k-', linewidth=2)
                    # Add label
                    if position % label_interval < 0.001:
                        label_val = int(position) if position == int(position) else position
                        ax.text(position, -0.3, str(label_val), 
                               ha='center', va='top', fontsize=12, fontweight='bold')
                
                # Minor mark
                elif show_minor_marks and position % minor_div < 0.001:
                    ax.plot([position, position], [0, 0.3], 'k-', linewidth=1)
                
            else:  # vertical
                # Major mark
                if position % major_div < 0.001:
                    ax.plot([0, 0.6], [position, position], 'k-', linewidth=2)
                    # Add label
                    if position % label_interval < 0.001:
                        label_val = int(position) if position == int(position) else position
                        ax.text(-0.3, position, str(label_val), 
                               ha='right', va='center', fontsize=12, fontweight='bold')
                
                # Minor mark
                elif show_minor_marks and position % minor_div < 0.001:
                    ax.plot([0, 0.3], [position, position], 'k-', linewidth=1)
            
            position += minor_div
        
        # Highlight specific measurements
        if highlight_measurements:
            for measurement in highlight_measurements:
                if 0 <= measurement <= ruler_length:
                    if orientation == 'horizontal':
                        # Draw arrow pointing to measurement
                        ax.annotate('', xy=(measurement, 0), xytext=(measurement, 1.8),
                                   arrowprops=dict(arrowstyle='->', color='red', lw=2))
                        ax.text(measurement, 1.9, f'{measurement} {unit}', 
                               ha='center', va='bottom', fontsize=10, color='red',
                               bbox=dict(boxstyle="round,pad=0.3", facecolor="white"))
                    else:
                        # Draw arrow for vertical ruler
                        ax.annotate('', xy=(0, measurement), xytext=(1.8, measurement),
                                   arrowprops=dict(arrowstyle='->', color='red', lw=2))
                        ax.text(1.9, measurement, f'{measurement} {unit}', 
                               ha='left', va='center', fontsize=10, color='red',
                               bbox=dict(boxstyle="round,pad=0.3", facecolor="white"))
        
        # Add unit label
        if orientation == 'horizontal':
            ax.text(ruler_length + 0.3, ruler_width/2, unit, 
                   ha='left', va='center', fontsize=14, fontweight='bold')
        else:
            ax.text(ruler_width/2, ruler_length + 0.3, unit, 
                   ha='center', va='bottom', fontsize=14, fontweight='bold')
        
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
        filename = f"ruler_{length}{unit}_{timestamp}.png"
        
        # Save locally
        os.makedirs("generated_images", exist_ok=True)
        local_path = f"generated_images/{filename}"
        
        with open(local_path, 'wb') as f:
            f.write(buf.getvalue())
        
        logger.info(f"Saved ruler image locally: {local_path}")
        
        # Try to upload
        try:
            storage = SupabaseStorage()
            public_url = storage.upload_image(local_path, f"educational/{filename}")
            if public_url:
                logger.info(f"Uploaded ruler image to Supabase: {public_url}")
                return public_url
        except Exception as e:
            logger.warning(f"Failed to upload to Supabase: {e}")
        
        return local_path
        
    except Exception as e:
        logger.error(f"Error generating ruler image: {e}")
        return None
    finally:
        plt.close('all')