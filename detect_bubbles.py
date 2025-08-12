#!/usr/bin/env python3
"""
Bubble Detection Module
======================

Uses YOLO (You Only Look Once) model to detect text bubbles in manga/comic images.
This module provides functionality to locate speech bubbles, text boxes, and other
text-containing regions in comic images.

Author: MangaTranslator Team
License: MIT
"""

import torch.serialization
from ultralytics import YOLO


def detect_bubbles(model_path, image_path):
    """
    Detect text bubbles in manga/comic images using YOLOv8 model
    
    This function loads a pre-trained YOLO model and uses it to identify
    text bubble regions in the provided image.
    
    Args:
        model_path (str): Path to the YOLO model file (.pt format)
        image_path (str): Path to the input image or PIL Image object
        
    Returns:
        list: List of detected bubbles with format:
              [x1, y1, x2, y2, confidence_score, class_id]
              where (x1,y1) is top-left corner and (x2,y2) is bottom-right corner
    """
    # Load YOLO model with safe globals for security
    with torch.serialization.safe_globals([YOLO]):
        model = YOLO(model_path)

    # Run detection on the image
    results = model(image_path)[0]

    # Extract bounding box data and return as list
    return results.boxes.data.tolist()
