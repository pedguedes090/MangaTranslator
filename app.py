# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
MangaTranslator - Fixed version with cache system
No emoji characters to avoid encoding issues
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
import zipfile
import shutil
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv
import base64
from io import BytesIO
import json

# Load environment variables from .env file
load_dotenv()

# Configuration constants
MODEL = "model.pt"  
EXAMPLE_LIST = [["examples/0.png"], ["examples/ex0.png"]]
OUTPUT_DIR = "outputs"
CACHE_DIR = "cache"

# Create directories if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

class ImageCache:
    """Cache manager for processed images"""
    
    def __init__(self):
        self.cache = {}
        self.session_data = {}
    
    def store_session_images(self, session_id, images_data):
        """Store processed images in session cache"""
        self.session_data[session_id] = {
            'images': images_data,
            'timestamp': datetime.now(),
            'total_count': len(images_data),
            'successful_count': len([img for img in images_data if img['status'] == 'success'])
        }
        print(f"Cached {len(images_data)} images for session {session_id}")
    
    def get_session_data(self, session_id):
        """Get session data from cache"""
        return self.session_data.get(session_id, None)
    
    def create_zip_from_cache(self, session_id):
        """Create ZIP file from cached images"""
        session_data = self.get_session_data(session_id)
        if not session_data:
            return None
        
        successful_images = [img for img in session_data['images'] if img['status'] == 'success']
        if not successful_images:
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"manga_translated_{timestamp}_{session_id[:8]}.zip"
        zip_path = os.path.join(CACHE_DIR, zip_filename)
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for img_data in successful_images:
                    # Convert PIL image to bytes
                    img_bytes = BytesIO()
                    img_data['image'].save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    
                    # Add to ZIP
                    zipf.writestr(img_data['output_name'], img_bytes.getvalue())
            
            print(f"Created ZIP from cache: {zip_path}")
            return zip_path
        except Exception as e:
            print(f"Error creating ZIP from cache: {e}")
            return None
    
    def clear_old_sessions(self, max_age_hours=2):
        """Clear old session data to free memory"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        old_sessions = [
            session_id for session_id, data in self.session_data.items()
            if data['timestamp'] < cutoff_time
        ]
        
        for session_id in old_sessions:
            del self.session_data[session_id]
            print(f"Cleared old session: {session_id}")

# Global cache instance
image_cache = ImageCache()

def cleanup_debug_files():
    """Clean up temporary debug files on exit"""
    debug_dir = os.path.join(tempfile.gettempdir(), "manga_translator_debug")
    if os.path.exists(debug_dir):
        try:
            shutil.rmtree(debug_dir)
            print(f"Cleaned up debug directory: {debug_dir}")
        except Exception as e:
            print(f"Could not clean debug directory: {e}")
    
    # Also cleanup cache directory
    if os.path.exists(CACHE_DIR):
        try:
            shutil.rmtree(CACHE_DIR)
            print(f"Cleaned up cache directory: {CACHE_DIR}")
        except Exception as e:
            print(f"Could not clean cache directory: {e}")

# Register cleanup function to run on exit
atexit.register(cleanup_debug_files)

def process_single_image(img, translation_method, font_path, source_language="auto", gemini_api_key=None, custom_prompt=None):
    """Process a single image for translation"""
    
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
        print(f"Using custom prompt: {custom_prompt[:50]}")
    else:
        custom_prompt = None
        print("Using automatic prompt based on source language")
    
    # Debug logging
    print(f"Using translation method: {translation_method}")
    print(f"Source language: {source_language}")
    print(f"API key available: {'Yes' if gemini_api_key else 'No'}")

    # Step 1: Detect text bubbles using YOLO model
    results = detect_bubbles(MODEL, img)
    print(f"Detected {len(results)} bubbles")
    
    # Sort bubbles by Y coordinate (top to bottom)
    results = sorted(results, key=lambda x: x[1])

    # Step 2: Initialize translator with optional Gemini API key
    manga_translator = MangaTranslator(gemini_api_key=gemini_api_key)
    
    # Step 3: Initialize multi-language OCR system
    multi_ocr = MultiLanguageOCR()
    
    # Show OCR recommendation for selected language
    ocr_method, ocr_desc = multi_ocr.get_best_ocr_for_language(source_language)
    print(f"OCR Engine: {ocr_desc}")

    # Convert PIL image to numpy array for processing
    original_image = np.array(img)
    image = original_image.copy()

    # Step 4: Process each detected bubble
    for idx, result in enumerate(results):
        x1, y1, x2, y2, score, class_id = result
        print(f"Processing bubble {idx+1}/{len(results)}")

        # Extract the bubble region from ORIGINAL image
        detected_image = original_image[int(y1):int(y2), int(x1):int(x2)]

        # Convert to PIL Image for OCR processing
        im = Image.fromarray(np.uint8(detected_image))
        
        # Step 5: Extract text using appropriate OCR engine
        text = multi_ocr.extract_text(im, source_language, method="auto")
        
        # Clean OCR text before translation
        text = text.strip() if text else ""
        
        print(f"OCR Text: '{text}'")

        # Step 6: Process the bubble for text replacement
        working_bubble = image[int(y1):int(y2), int(x1):int(x2)]
        processed_bubble, cont = process_bubble(working_bubble)

        # Step 7: Translate the extracted text
        if text:
            text_translated = manga_translator.translate(text,
                                                         method=translation_method,
                                                         source_lang=source_language,
                                                         custom_prompt=custom_prompt)
            print(f"Translated: '{text_translated}'")
        else:
            text_translated = ""
            print("No text detected, skipping translation")

        # Step 8: Add translated text back to the image
        print(f"Adding text to bubble {idx+1}")
        image[int(y1):int(y2), int(x1):int(x2)] = add_text(processed_bubble, text_translated, font_path, cont)

    return Image.fromarray(image)

def process_batch_cached(images, translation_method, font_path, source_language="auto", gemini_api_key=None, custom_prompt=None):
    """Process multiple images in batch and store in cache"""
    
    if not images:
        return None, [], "No images uploaded"
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    total_images = len(images)
    
    print(f"Starting cached batch processing: {total_images} images")
    print(f"Session ID: {session_id}")
    
    # Clean old cache to free memory
    image_cache.clear_old_sessions()
    
    processed_images = []
    preview_images = []
    
    for idx, img_file in enumerate(images):
        try:
            print(f"Processing image {idx + 1}/{total_images}")
            
            # Open image
            if isinstance(img_file, str):
                img = Image.open(img_file)
                original_name = os.path.basename(img_file)
            else:
                img = Image.open(img_file.name)
                original_name = img_file.name if hasattr(img_file, 'name') else f"image_{idx+1}.png"
            
            # Process the image using existing function
            processed_img = process_single_image(
                img, translation_method, font_path, 
                source_language, gemini_api_key, custom_prompt
            )
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(original_name))[0]
            output_filename = f"{base_name}_translated.png"
            
            # Store in cache (in memory)
            image_data = {
                "original_name": original_name,
                "output_name": output_filename,
                "image": processed_img,
                "status": "success",
                "index": idx
            }
            processed_images.append(image_data)
            
            # Add to preview list (for Gradio Gallery)
            preview_images.append(processed_img)
            
            print(f"Successfully processed: {original_name}")
            
        except Exception as e:
            error_msg = f"Error processing image {idx+1}: {str(e)}"
            print(error_msg)
            
            # Store error info
            image_data = {
                "original_name": img_file.name if hasattr(img_file, 'name') else f'image_{idx+1}',
                "output_name": "N/A",
                "image": None,
                "status": "error",
                "error_message": str(e)[:100],
                "index": idx
            }
            processed_images.append(image_data)
    
    # Store session data in cache
    image_cache.store_session_images(session_id, processed_images)
    
    # Generate status message
    successful_count = len([img for img in processed_images if img['status'] == 'success'])
    failed_count = total_images - successful_count
    
    if failed_count == 0:
        status_msg = f"Complete! Successfully processed {successful_count}/{total_images} images"
    else:
        status_msg = f"Complete with errors! Success: {successful_count}, Failed: {failed_count}"
    
    return session_id, preview_images, status_msg

def create_file_list_display_cached(session_id):
    """Create HTML display for cached processed files list"""
    
    session_data = image_cache.get_session_data(session_id)
    if not session_data:
        return "<p>Session not found or expired</p>"
    
    images_data = session_data['images']
    total_count = session_data['total_count']
    successful_count = session_data['successful_count']
    
    html = f"""
    <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; margin: 10px 0;">
        <h3 style="color: #2c3e50; margin-bottom: 15px;">Processed Files List</h3>
        <div style="background: #e3f2fd; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
            <strong>Summary:</strong> {successful_count}/{total_count} images successful | Session: {session_id[:8]}
        </div>
    """
    
    for idx, img_data in enumerate(images_data, 1):
        if img_data['status'] == 'success':
            status_color = "#28a745"
            status_text = "Success"
        else:
            status_color = "#dc3545"
            status_text = f"Error: {img_data.get('error_message', 'Unknown error')}"
        
        html += f"""
        <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid {status_color};">
            <div>
                <strong>#{idx}:</strong> {img_data['original_name']} -> {img_data['output_name']}
                <br>
                <span style="color: {status_color}; font-weight: bold;">{status_text}</span>
            </div>
        </div>
        """
    
    if successful_count > 0:
        html += f"""
        <div style="background: #e8f5e8; padding: 15px; margin: 15px 0; border-radius: 8px; text-align: center;">
            <h4 style="color: #2e7d32; margin-bottom: 10px;">Ready to Download</h4>
            <p>Found <strong>{successful_count}</strong> successfully processed images</p>
            <p><em>Click "Create ZIP" button below to download all</em></p>
        </div>
        """
    
    html += "</div>"
    return html

def create_zip_download(session_id):
    """Create ZIP file from cached images when user requests download"""
    
    if not session_id:
        return None, "No session to create ZIP"
    
    zip_path = image_cache.create_zip_from_cache(session_id)
    if zip_path:
        return zip_path, "ZIP file created successfully! Ready to download."
    else:
        return None, "Cannot create ZIP file. Check session or no successful images."

def batch_predict(images, translation_method, font_path, source_language="auto", gemini_api_key=None, custom_prompt=None):
    """Batch prediction function for multiple images (cached version)"""
    
    session_id, preview_images, status_msg = process_batch_cached(
        images, translation_method, font_path, 
        source_language, gemini_api_key, custom_prompt
    )
    
    if session_id:
        file_list_html = create_file_list_display_cached(session_id)
    else:
        file_list_html = "<p>Cannot process batch</p>"
    
    return session_id, preview_images, file_list_html, status_msg

# Legacy single image function
def predict(img, translation_method, font_path, source_language="auto", gemini_api_key=None, custom_prompt=None):
    """Main prediction function for manga translation (single image)"""
    return process_single_image(img, translation_method, font_path, source_language, gemini_api_key, custom_prompt)

# UI Configuration
TITLE = "Multi-Language Comic Translator - Batch Processing with Cache"
DESCRIPTION = """
Dịch truyện tranh đa ngôn ngữ sang tiếng Việt! (Hỗ trợ nhiều ảnh)

OCR Engine tối ưu:
- Manga (Nhật): manga-ocr (chuyên biệt)
- Manhua (Trung): PaddleOCR (tối ưu Chinese)  
- Manhwa (Hàn): EasyOCR (hỗ trợ Korean tốt)
- Comics (Anh): EasyOCR (đa ngôn ngữ)

AI Translation: Gemini 2.0 Flash với prompt tối ưu cho từng loại truyện

Tính năng mới:
- Batch Processing: Upload nhiều ảnh cùng lúc
- Preview Images: Xem trước kết quả ngay lập tức  
- Smart Cache: Lưu trong bộ nhớ, tạo ZIP chỉ khi cần
- Download Options: Tải từng file hoặc tất cả dưới dạng ZIP

Hướng dẫn sử dụng:
1. Upload một hoặc nhiều ảnh vào mục "Input Images"
2. Chọn cấu hình dịch thuật phù hợp
3. Nhấn "Dịch Truyện" để bắt đầu xử lý
4. Xem preview kết quả trong gallery
5. Nhấn "Tạo ZIP" nếu muốn tải về tất cả
"""

# Create Gradio interface with tabs for single and batch processing
with gr.Blocks(title=TITLE, theme=gr.themes.Soft()) as demo:
    gr.HTML(f"""
    <div style="text-align: center; padding: 20px;">
        <h1 style="color: #2c3e50; margin-bottom: 10px;">{TITLE}</h1>
    </div>
    """)
    
    gr.Markdown(DESCRIPTION)
    
    with gr.Tabs():
        # Tab 1: Single Image Processing
        with gr.TabItem("Ảnh Đơn"):
            with gr.Row():
                with gr.Column():
                    single_image_input = gr.Image(type="pil", label="Tải ảnh manga lên")
                    
                    # Configuration inputs
                    translation_method = gr.Dropdown(
                        [("Google Translate", "google"),
                         ("Gemini AI (Khuyến nghị)", "gemini"),
                         ("Helsinki-NLP (JP->EN)", "hf"),
                         ("Sogou", "sogou"),
                         ("Bing", "bing")],
                        label="Phương Pháp Dịch",
                        value="gemini"
                    )
                    
                    font_path = gr.Dropdown(
                        [("animeace_i", "fonts/animeace_i.ttf"),
                         ("animeace2_reg", "fonts/animeace2_reg.ttf"),
                         ("mangati", "fonts/mangati.ttf"),
                         ("ariali", "fonts/ariali.ttf")],
                        label="Phông Chữ",
                        value="fonts/animeace_i.ttf"
                    )
                    
                    source_language = gr.Dropdown(
                        [("Tự Động Nhận Dạng", "auto"),
                         ("Japanese (Manga)", "ja"),
                         ("Chinese (Manhua)", "zh"),
                         ("Korean (Manhwa)", "ko"),
                         ("English", "en")],
                        label="Ngôn Ngữ Gốc",
                        value="auto"
                    )
                    
                    gemini_api_key = gr.Textbox(
                        label="Gemini API Key (Tùy chọn)", 
                        type="password", 
                        placeholder="Nhập API key cho dịch thuật AI",
                        value=os.getenv("GEMINI_API_KEY", "")
                    )
                    
                    custom_prompt = gr.Textbox(
                        label="Prompt Tùy Chỉnh (Nâng cao)", 
                        lines=3,
                        placeholder="Để trống để sử dụng prompt tự động",
                        value=""
                    )
                    
                    single_submit_btn = gr.Button("Dịch Ảnh", variant="primary")
                
                with gr.Column():
                    single_output = gr.Image(label="Kết Quả Dịch")
            
            # Examples for single image
            gr.Examples(
                examples=[[ex[0]] for ex in EXAMPLE_LIST],
                inputs=[single_image_input],
                label="Ảnh Mẫu"
            )
        
        # Tab 2: Batch Processing with Cache & Preview
        with gr.TabItem("Xử Lý Batch"):
            with gr.Row():
                with gr.Column(scale=1):
                    batch_images_input = gr.Files(
                        label="Tải nhiều ảnh manga lên (PNG, JPG, JPEG)",
                        file_count="multiple",
                        file_types=["image"]
                    )
                    
                    # Shared configuration for batch
                    batch_translation_method = gr.Dropdown(
                        [("Google Translate", "google"),
                         ("Gemini AI (Khuyến nghị)", "gemini"),
                         ("Helsinki-NLP (JP->EN)", "hf"),
                         ("Sogou", "sogou"),
                         ("Bing", "bing")],
                        label="Phương Pháp Dịch",
                        value="gemini"
                    )
                    
                    batch_font_path = gr.Dropdown(
                        [("animeace_i", "fonts/animeace_i.ttf"),
                         ("animeace2_reg", "fonts/animeace2_reg.ttf"),
                         ("mangati", "fonts/mangati.ttf"),
                         ("ariali", "fonts/ariali.ttf")],
                        label="Font",
                        value="fonts/animeace_i.ttf"
                    )
                    
                    batch_source_language = gr.Dropdown(
                        [("Auto Detect", "auto"),
                         ("Japanese (Manga)", "ja"),
                         ("Chinese (Manhua)", "zh"),
                         ("Korean (Manhwa)", "ko"),
                         ("English", "en")],
                        label="Source Language",
                        value="auto"
                    )
                    
                    batch_gemini_api_key = gr.Textbox(
                        label="Gemini API Key (Optional)", 
                        type="password", 
                        placeholder="Enter API key for AI translation",
                        value=os.getenv("GEMINI_API_KEY", "")
                    )
                    
                    batch_custom_prompt = gr.Textbox(
                        label="Custom Prompt (Advanced)", 
                        lines=3,
                        placeholder="Custom translation style for entire batch",
                        value=""
                    )
                    
                    batch_submit_btn = gr.Button("Xử Lý Batch", variant="primary", size="lg")
                
                with gr.Column(scale=2):
                    batch_status = gr.Textbox(
                        label="Processing Status",
                        interactive=False,
                        value="Waiting for images..."
                    )
                    
                    # Preview gallery for processed images
                    batch_preview_gallery = gr.Gallery(
                        label="Preview Results",
                        show_label=True,
                        elem_id="preview_gallery",
                        columns=2,
                        rows=2,
                        height="400px",
                        show_share_button=False
                    )
            
            # File list and download section
            with gr.Row():
                with gr.Column():
                    batch_file_list = gr.HTML(
                        label="Processed files list",
                        value="<p>No files processed yet</p>"
                    )
                
                with gr.Column(scale=1):
                    # Hidden session ID storage
                    session_id_state = gr.Textbox(
                        value="",
                        visible=False,
                        interactive=False
                    )
                    
                    create_zip_btn = gr.Button(
                        "Create ZIP",
                        variant="secondary",
                        visible=False
                    )
                    
                    batch_download_zip = gr.File(
                        label="Download ZIP",
                        visible=False
                    )
                    
                    zip_status = gr.Textbox(
                        label="ZIP Status",
                        interactive=False,
                        visible=False
                    )
    
    # Event handlers
    single_submit_btn.click(
        fn=predict,
        inputs=[single_image_input, translation_method, font_path, source_language, gemini_api_key, custom_prompt],
        outputs=[single_output]
    )
    
    # Batch processing event handler
    batch_submit_btn.click(
        fn=batch_predict,
        inputs=[batch_images_input, batch_translation_method, batch_font_path, batch_source_language, batch_gemini_api_key, batch_custom_prompt],
        outputs=[session_id_state, batch_preview_gallery, batch_file_list, batch_status]
    ).then(
        # Show create ZIP button after processing
        lambda session_id: (
            gr.Button(visible=True if session_id else False),
            gr.Textbox(visible=True if session_id else False)
        ),
        inputs=[session_id_state],
        outputs=[create_zip_btn, zip_status]
    )
    
    # ZIP creation event handler  
    create_zip_btn.click(
        fn=create_zip_download,
        inputs=[session_id_state],
        outputs=[batch_download_zip, zip_status]
    ).then(
        # Show download file component
        lambda zip_path: gr.File(visible=True if zip_path else False),
        inputs=[batch_download_zip],
        outputs=[batch_download_zip]
    )

# Launch the application
if __name__ == "__main__":
    demo.launch(debug=False, share=False)
