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
    bubble_area = w * h
    
    print(f"📏 Bubble dimensions: {w}x{h} (area: {bubble_area}px²)")

    # Calculate optimal font size based on bubble dimensions
    # Base font size calculation using area and aspect ratio
    base_font_size = max(8, min(32, int(np.sqrt(bubble_area) * 0.08)))
    
    # Adjust based on aspect ratio (wide bubbles get smaller font)
    aspect_ratio = w / h if h > 0 else 1
    if aspect_ratio > 2:  # Very wide bubble
        base_font_size = int(base_font_size * 0.8)
    elif aspect_ratio < 0.5:  # Very tall bubble  
        base_font_size = int(base_font_size * 1.1)
    
    print(f"🎨 Calculated base font size: {base_font_size}px (aspect ratio: {aspect_ratio:.2f})")
    
    # Text formatting parameters
    line_spacing_ratio = 1.2    # Line height as ratio of font size
    max_width_ratio = 0.85      # Use 85% of bubble width for text
    min_font_size = 8           # Minimum readable font size

    # Smart text fitting algorithm
    font_size = base_font_size
    line_height = int(font_size * line_spacing_ratio)
    max_text_width = int(w * max_width_ratio)
    
    # Estimate characters per line based on font size
    chars_per_line = max(10, max_text_width // (font_size * 0.6))
    
    best_fit = None
    attempts = 0
    max_attempts = 10
    
    while font_size >= min_font_size and attempts < max_attempts:
        attempts += 1
        
        # Try current font size
        font = ImageFont.truetype(font_path, size=font_size)
        line_height = int(font_size * line_spacing_ratio)
        
        # Wrap text for current font size
        wrapped_text = textwrap.fill(text, width=chars_per_line, 
                                     break_long_words=True, break_on_hyphens=True)
        lines = wrapped_text.split('\n')
        
        # Calculate actual text dimensions
        max_line_width = 0
        for line in lines:
            line_width = draw.textlength(line, font=font)
            max_line_width = max(max_line_width, line_width)
        
        total_text_height = len(lines) * line_height
        
        print(f"   Attempt {attempts}: font={font_size}px, lines={len(lines)}, "
              f"text_size={max_line_width:.0f}x{total_text_height}, "
              f"bubble_size={w}x{h}")
        
        # Check if text fits within bubble
        fits_width = max_line_width <= max_text_width
        fits_height = total_text_height <= (h * 0.9)  # Use 90% of height
        
        if fits_width and fits_height:
            best_fit = {
                'font': font,
                'font_size': font_size,
                'line_height': line_height,
                'wrapped_text': wrapped_text,
                'lines': lines,
                'max_line_width': max_line_width,
                'total_height': total_text_height
            }
            print(f"   ✅ Found good fit: {font_size}px font")
            break
        
        # Reduce font size and try again
        font_size -= 2
        chars_per_line = max(10, max_text_width // (font_size * 0.6))
    
    # Use best fit or fallback to smallest size
    if best_fit is None:
        print(f"   ⚠️  Using minimum font size: {min_font_size}px")
        font_size = min_font_size
        font = ImageFont.truetype(font_path, size=font_size)
        line_height = int(font_size * line_spacing_ratio)
        chars_per_line = max(8, max_text_width // (font_size * 0.6))
        wrapped_text = textwrap.fill(text, width=chars_per_line, 
                                     break_long_words=True, break_on_hyphens=True)
        lines = wrapped_text.split('\n')
        total_text_height = len(lines) * line_height
    else:
        font = best_fit['font']
        line_height = best_fit['line_height']
        wrapped_text = best_fit['wrapped_text']
        lines = best_fit['lines']
        total_text_height = best_fit['total_height']                         

    # Calculate vertical centering position
    text_y = y + (h - total_text_height) // 2
    
    print(f"🎯 Final text placement: {len(lines)} lines, font={font.size}px, "
          f"position=({x + w//2}, {text_y})")

    # Draw each line of text with enhanced rendering
    for i, line in enumerate(lines):
        if not line.strip():  # Skip empty lines
            text_y += line_height
            continue
            
        # Calculate text width for horizontal centering
        text_bbox = draw.textbbox((0, 0), line, font=font)
        text_width = text_bbox[2] - text_bbox[0]

        # Calculate horizontal centering position
        text_x = x + (w - text_width) // 2

        # Draw text with slight outline for better readability
        outline_width = max(1, font.size // 16)  # Dynamic outline based on font size
        
        if outline_width > 0:
            # Draw outline
            for dx in [-outline_width, 0, outline_width]:
                for dy in [-outline_width, 0, outline_width]:
                    if dx != 0 or dy != 0:
                        draw.text((text_x + dx, text_y + dy), line, 
                                 font=font, fill=(255, 255, 255))  # White outline
        
        # Draw main text (black)
        draw.text((text_x, text_y), line, font=font, fill=(0, 0, 0))

        # Move to next line position
        text_y += line_height

    # Convert PIL Image back to OpenCV format (BGR)
    image[:, :, :] = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    return image
