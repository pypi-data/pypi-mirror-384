"""
Venn diagram generation using Gemini API for educational visualizations
"""

import logging
import time
import os
from typing import Optional

from src.image_generation.gemini_image_gen import generate_image_gemini

logger = logging.getLogger(__name__)


async def generate_venn_diagram_image(
    question: str,
    background_color: str = 'white',
    feedback: str = ""
) -> Optional[str]:
    """
    Generate Venn diagram using Gemini API with educational prompt.
    
    Parameters
    ----------
    question : str
        The question containing Venn diagram data
    background_color : str
        Background color for the diagram
    feedback : str
        Quality feedback from previous generation attempt
    
    Returns
    -------
    str or None
        URL of generated image or None if failed
    """
    try:
        # Create educational prompt for Venn diagram
        venn_prompt = f"""Create a proper Venn diagram for this question: {question}

REQUIREMENTS:
- Draw the exact number of overlapping circles as there are different categories/subjects in the question
- Use true overlapping Venn diagram format (circles must overlap, not separate)
- For 4+ categories, limit to 3 circles maximum with NO additional text or notes
- Bright distinct colors for each circle
- Label each circle clearly with its category name
- Show ALL numbers/totals that are explicitly stated in the question
- Never show calculated values that would reveal the answer to what the question is asking
- No titles, headers, explanatory text, or "simplified view" notes
- Clean white background with no borders or frames
- Standard mathematical Venn diagram format"""
        
        # Add feedback if provided
        if feedback:
            logger.info(f"Venn diagram generation with feedback: {feedback}")
            venn_prompt += f"\n\nPREVIOUS ATTEMPT FEEDBACK: {feedback}\nAddress these issues in the new diagram."

        # Generate image using Gemini
        result_json = generate_image_gemini(venn_prompt, "1:1", 1)
        
        if result_json:
            import json
            result = json.loads(result_json)
            if result.get("status") == "success" and result.get("image_paths"):
                image_url = result["image_paths"][0]
                logger.info(f"Generated Venn diagram with Gemini: {image_url}")
                return image_url
        
        logger.error("Failed to generate Venn diagram with Gemini")
        return None
            
    except Exception as e:
        logger.error(f"Error generating Venn diagram: {e}")
        return None