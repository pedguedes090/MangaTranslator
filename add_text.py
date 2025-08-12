#!/usr/bin/env python3
"""
Text Addition Module
===================

Handles the insertion of translated text into processed speech bubbles.
This module provides intelligent text fitting, centering, and formatting
to ensure the translated text fits properly within bubble boundaries.

Features:
- Automatic text wrapping and sizing
- Smart font size adjustment
- Text centering (horizontal and vertical)
- Multi-line text support

Author: MangaTranslator Team
License: MIT
"""

from PIL import Image, ImageDraw, ImageFont
import numpy as np
import textwrap
import cv2


def add_text(image, text, font_path, bubble_contour):
    """
    Add translated text inside a speech bubble with automatic sizing and centering
    
    This function intelligently places translated text within the bubble boundaries,
    automatically adjusting font size and text wrapping to ensure optimal fit.
    
    Args:
        image (numpy.ndarray): Processed bubble image in BGR format (OpenCV)
        text (str): Translated text to place inside the speech bubble
        font_path (str): Path to the font file (.ttf format)
        bubble_contour (numpy.ndarray): Contour defining the speech bubble boundary
        
    Returns:
        numpy.ndarray: Image with translated text properly placed inside the bubble
    """
    # Convert OpenCV image (BGR) to PIL Image (RGB)
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)

    # Get bounding rectangle of the bubble contour
    x, y, w, h = cv2.boundingRect(bubble_contour)

    # Initial text formatting parameters
    line_height = 16        # Space between lines
    font_size = 14         # Initial font size
    wrapping_ratio = 0.075 # Text wrapping width ratio

    # Wrap text based on bubble width
    wrapped_text = textwrap.fill(text, width=int(w * wrapping_ratio), 
                                 break_long_words=True)
    
    # Load font with initial size
    font = ImageFont.truetype(font_path, size=font_size)

    # Split into individual lines
    lines = wrapped_text.split('\n')
    total_text_height = len(lines) * line_height

    # Dynamically adjust text size if it doesn't fit
    while total_text_height > h:
        line_height -= 2        # Reduce line spacing
        font_size -= 2          # Reduce font size
        wrapping_ratio += 0.025 # Increase text wrapping (narrower text)

        # Re-wrap text with new parameters
        wrapped_text = textwrap.fill(text, width=int(w * wrapping_ratio), 
                                     break_long_words=True)
                                 
        # Reload font with new size
        font = ImageFont.truetype(font_path, size=font_size)

        # Recalculate text dimensions
        lines = wrapped_text.split('\n')
        total_text_height = len(lines) * line_height                         

    # Calculate vertical centering position
    text_y = y + (h - total_text_height) // 2

    # Draw each line of text
    for line in lines:
        # Calculate text width for horizontal centering
        text_length = draw.textlength(line, font=font)

        # Calculate horizontal centering position
        text_x = x + (w - text_length) // 2

        # Draw the text line with black color
        draw.text((text_x, text_y), line, font=font, fill=(0, 0, 0))

        # Move to next line position
        text_y += line_height

    # Convert PIL Image back to OpenCV format (BGR)
    image[:, :, :] = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    return image
