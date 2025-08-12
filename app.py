#!/usr/bin/env python3
"""
Manga Translator App - Main Gradio Interface
============================================

A comprehensive manga/comic translation application that:
- Detects text bubbles using YOLO model
- Extracts text using multi-language OCR engines
- Translates text using various translation services
- Replaces original text with translated text

Author: MangaTranslator Team
License: MIT
"""

# Core modules
from add_text import add_text
from detect_bubbles import detect_bubbles
from process_bubble import process_bubble
from translator import MangaTranslator
from multi_ocr import MultiLanguageOCR

# External libraries
from ultralytics import YOLO
from PIL import Image
import gradio as gr
import numpy as np
import cv2
import os
import tempfile
import time
import atexit
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debug cleanup function
def cleanup_debug_files():
    """Clean up temporary debug files on exit"""
    debug_dir = os.path.join(tempfile.gettempdir(), "manga_translator_debug")
    if os.path.exists(debug_dir):
        try:
            import shutil
            shutil.rmtree(debug_dir)
            print(f"🧹 Cleaned up debug directory: {debug_dir}")
        except Exception as e:
            print(f"⚠️  Could not clean debug directory: {e}")

# Register cleanup function to run on exit
atexit.register(cleanup_debug_files)

# Configuration constants
MODEL = "model.pt"  # YOLO model for bubble detection
EXAMPLE_LIST = [["examples/0.png"], ["examples/ex0.png"]]  # Example images for testing

# UI Configuration
TITLE = "Multi-Language Comic Translator with AI"
DESCRIPTION = """
🌍 **Dịch truyện tranh đa ngôn ngữ sang tiếng Việt!**

**📚 OCR Engine tối ưu:**
- 🇯🇵 ** (Nhật):** manga-ocr (chuyên biệt)
- 🇨🇳 **Manhua (Trung):** PaddleOCR (tối ưu Chinese)  
- 🇰🇷 **Manhwa (Hàn):** EasyOCR (hỗ trợ Korean tốt)
- 🇺🇸 **Comics (Anh):** EasyOCR (đa ngôn ngữ)

**🤖 AI Translation:** Gemini 2.0 Flash với prompt tối ưu cho từng loại truyện

**🎨 NEW: Tùy chỉnh phong cách dịch:**
- Prompt tự động thông minh theo ngôn ngữ
- Tùy chỉnh phong cách: nhẹ nhàng, trang trọng, trẻ trung...
- Font size tự động điều chỉnh theo kích thước bubble
"""


def predict(img, translation_method, font_path, source_language="auto", gemini_api_key=None, custom_prompt=None):
    """
    Main prediction function for manga translation
    
    Args:
        img: Input image (PIL Image)
        translation_method: Translation service to use
        font_path: Path to font file for text rendering
        source_language: Source language code or 'auto' for auto-detection
        gemini_api_key: Optional Gemini API key
        custom_prompt: Custom translation style prompt or None for auto
    
    Returns:
        PIL Image: Translated image with text replaced
    """
    # Set default values if None
    if translation_method is None:
        translation_method = "google"
    if font_path is None:
        font_path = "fonts/animeace_i.ttf"

    # Handle API key - use from input or environment variable
    if not gemini_api_key or gemini_api_key.strip() == "":
        gemini_api_key = os.getenv("GEMINI_API_KEY", None)
    
    # Handle custom prompt
    if custom_prompt and custom_prompt.strip():
        print(f"🎨 Using custom prompt: {custom_prompt[:50]}{'...' if len(custom_prompt) > 50 else ''}")
    else:
        custom_prompt = None
        print("🤖 Using automatic prompt based on source language")
    
    # Debug logging
    print(f"Using translation method: {translation_method}")
    print(f"Source language: {source_language}")
    print(f"API key available: {'Yes' if gemini_api_key else 'No'}")
    if gemini_api_key:
        print(f"API key preview: {gemini_api_key[:10]}...")

    # Step 1: Detect text bubbles using YOLO model
    results = detect_bubbles(MODEL, img)
    print(f"🎯 Detected {len(results)} bubbles")
    
    # Debug: Print all bubble coordinates
    for idx, result in enumerate(results):
        x1, y1, x2, y2, score, class_id = result
        print(f"   Bubble {idx+1}: ({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f}) - Score: {score:.3f}")
    
    # Sort bubbles by Y coordinate (top to bottom) to ensure consistent processing order
    results = sorted(results, key=lambda x: x[1])  # Sort by y1 (top coordinate)
    print(f"📋 Processing order (sorted by Y):")
    for idx, result in enumerate(results):
        x1, y1, x2, y2, score, class_id = result
        print(f"   Order {idx+1}: ({x1:.1f}, {y1:.1f}, {x2:.1f}, {y2:.1f})")

    # Step 2: Initialize translator with optional Gemini API key
    manga_translator = MangaTranslator(gemini_api_key=gemini_api_key)
    
    # Step 3: Initialize multi-language OCR system
    multi_ocr = MultiLanguageOCR()
    
    # Show OCR recommendation for selected language
    ocr_method, ocr_desc = multi_ocr.get_best_ocr_for_language(source_language)
    print(f"🔍 OCR Engine: {ocr_desc}")

    # Convert PIL image to numpy array for processing
    original_image = np.array(img)  # Keep original unchanged
    image = original_image.copy()   # Working copy for modifications

    # Step 4: Process each detected bubble
    for idx, result in enumerate(results):
        x1, y1, x2, y2, score, class_id = result
        print(f"🔄 Processing bubble {idx+1}/{len(results)} at coordinates ({x1}, {y1}, {x2}, {y2})")

        # Extract the bubble region from ORIGINAL image (not modified one)
        detected_image = original_image[int(y1):int(y2), int(x1):int(x2)]
        print(f"📊 OCR source image shape: {detected_image.shape}, dtype: {detected_image.dtype}, range: [{detected_image.min()}, {detected_image.max()}]")

        # Convert to PIL Image for OCR processing (fix the scaling issue)
        im = Image.fromarray(np.uint8(detected_image))
        
        # Optional debug mode - only save if DEBUG environment variable is set
        if os.getenv("MANGA_DEBUG", "").lower() in ("1", "true", "yes"):
            import tempfile
            import time
            timestamp = int(time.time())
            debug_dir = os.path.join(tempfile.gettempdir(), "manga_translator_debug")
            os.makedirs(debug_dir, exist_ok=True)
            debug_filename = os.path.join(debug_dir, f"bubble_{timestamp}_{idx+1}.png")
            im.save(debug_filename)
            print(f"� DEBUG: Saved OCR input to {debug_filename}")
        
        # Step 5: Extract text using appropriate OCR engine
        text = multi_ocr.extract_text(im, source_language, method="auto")
        
        # Clean OCR text before translation
        text = text.strip() if text else ""
        
        # Debug logging for OCR results
        print(f"📝 OCR Text (raw): '{text}'")
        print(f"📝 OCR Text (length): {len(text)}")
        print(f"📝 OCR Text (repr): {repr(text)}")

        # Step 6: Process the bubble for text replacement (from working copy)
        working_bubble = image[int(y1):int(y2), int(x1):int(x2)]
        processed_bubble, cont = process_bubble(working_bubble)

        # Step 7: Translate the extracted text
        if text:  # Only translate if text exists
            text_translated = manga_translator.translate(text,
                                                         method=translation_method,
                                                         source_lang=source_language,
                                                         custom_prompt=custom_prompt)
            print(f"🌏 Translated: '{text_translated}'")
        else:
            text_translated = ""
            print("⚠️ No text detected, skipping translation")

        # Step 8: Add translated text back to the image
        print(f"📝 Adding text to bubble {idx+1}: '{text_translated[:50]}{'...' if len(text_translated) > 50 else ''}'")
        image[int(y1):int(y2), int(x1):int(x2)] = add_text(processed_bubble, text_translated, font_path, cont)

    return Image.fromarray(image)


# Create Gradio interface
demo = gr.Interface(
    fn=predict,
    inputs=[
        # Input image
        "image",
        
        # Translation method dropdown
        gr.Dropdown([("Google Translate", "google"),
                     ("Gemini AI (Khuyến nghị)", "gemini"),
                     ("Helsinki-NLP (Nhật→Anh)", "hf"),
                     ("Sogou", "sogou"),
                     ("Bing", "bing")],
                    label="Phương thức dịch",
                    value="gemini"),
        
        # Font selection dropdown
        gr.Dropdown([("animeace_i", "fonts/animeace_i.ttf"),
                     ("animeace2_reg", "fonts/animeace2_reg.ttf"),
                     ("mangati", "fonts/mangati.ttf"),
                     ("ariali", "fonts/ariali.ttf")],
                    label="Font chữ",
                    value="fonts/animeace_i.ttf"),
        
        # Source language dropdown
        gr.Dropdown([("Tự động nhận diện", "auto"),
                     ("Tiếng Nhật (Manga)", "ja"),
                     ("Tiếng Trung (Manhua)", "zh"),
                     ("Tiếng Hàn (Manhwa)", "ko"),
                     ("Tiếng Anh", "en")],
                    label="Ngôn ngữ gốc",
                    value="auto"),
        
        # API key input
        gr.Textbox(label="Gemini API Key (Tùy chọn)", 
                   type="password", 
                   placeholder="Nhập API key để dịch AI thông minh",
                   value=os.getenv("GEMINI_API_KEY", "")),
        
        # Custom prompt input
        gr.Textbox(label="🎨 Prompt Tùy Chỉnh (Advanced)", 
                   lines=4,
                   placeholder="""Ví dụ:
- Dịch theo phong cách nhẹ nhàng, thân thiện
- Giữ nguyên tính cách nhân vật, sử dụng ngôn ngữ trẻ trung
- Dịch theo phong cách cổ điển, trang trọng
- Dịch ngắn gọn để vừa bubble
- Để trống = sử dụng prompt tự động theo ngôn ngữ""",
                   value="")
    ],
    outputs=[gr.Image()],
    examples=EXAMPLE_LIST,
    title=TITLE,
    description=DESCRIPTION
)


# Launch the application
if __name__ == "__main__":
    demo.launch(debug=False, share=False)
