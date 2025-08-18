# -*- coding: utf-8 -*-
#!/usr/bin/env python3
"""
MangaTranslator - Enhanced version with batch image processing
Supports processing up to 20 images simultaneously for optimal performance
"""

# Core modules
from add_text import add_text
from detect_bubbles import detect_bubbles  
from process_bubble import process_bubble
from translator import MangaTranslator
from multi_ocr import MultiLanguageOCR
from batch_image_processor import batch_processor, ImageTask
from manga_splitter import MangaSplitter

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
from typing import List, Tuple

# Load environment variables from .env file
load_dotenv()

# Configuration constants
MODEL = "model.pt"  
EXAMPLE_LIST = [["examples/0.png"], ["examples/ex0.png"]]
OUTPUT_DIR = "outputs"
CACHE_DIR = "cache"
FONTS_DIR = "fonts"

# Create directories if they don't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
os.makedirs(FONTS_DIR, exist_ok=True)

def load_fonts_from_directory(fonts_dir=FONTS_DIR):
    """
    Tự động load tất cả font từ thư mục fonts
    Returns: List of tuples (display_name, font_path)
    """
    font_list = []
    supported_extensions = ['.ttf', '.otf', '.woff', '.woff2']
    
    if not os.path.exists(fonts_dir):
        # Return default font if fonts directory doesn't exist
        return [("animeace_i (default)", "fonts/animeace_i.ttf")]
    
    try:
        for filename in os.listdir(fonts_dir):
            if any(filename.lower().endswith(ext) for ext in supported_extensions):
                font_path = os.path.join(fonts_dir, filename)
                # Create display name from filename (remove extension)
                display_name = os.path.splitext(filename)[0]
                font_list.append((display_name, font_path))
        
        # Sort by display name for better organization
        font_list.sort(key=lambda x: x[0])
        
        # If no fonts found, add default
        if not font_list:
            font_list = [("animeace_i (default)", "fonts/animeace_i.ttf")]
            
    except Exception as e:
        print(f"Error loading fonts: {e}")
        font_list = [("animeace_i (default)", "fonts/animeace_i.ttf")]
    
    return font_list

# Load available fonts
AVAILABLE_FONTS = load_fonts_from_directory()

def refresh_fonts():
    """Refresh font list and return updated choices"""
    global AVAILABLE_FONTS
    AVAILABLE_FONTS = load_fonts_from_directory()
    status_msg = f"✅ Đã làm mới danh sách font: {len(AVAILABLE_FONTS)} font được tìm thấy"
    print(status_msg)
    # Return both choices and value for dropdown update, and status message
    dropdown_update = gr.Dropdown(choices=AVAILABLE_FONTS, value=AVAILABLE_FONTS[0][1] if AVAILABLE_FONTS else "fonts/animeace_i.ttf")
    status_update = gr.Markdown(status_msg, visible=True)
    return dropdown_update, status_update

def refresh_fonts_simple():
    """Refresh font list for batch dropdown (no status)"""
    global AVAILABLE_FONTS
    AVAILABLE_FONTS = load_fonts_from_directory()
    print(f"📝 Đã làm mới danh sách font: {len(AVAILABLE_FONTS)} font được tìm thấy")
    return gr.Dropdown(choices=AVAILABLE_FONTS, value=AVAILABLE_FONTS[0][1] if AVAILABLE_FONTS else "fonts/animeace_i.ttf")

# Global API Key Manager instance
global_translator = None

def get_global_translator():
    """Get or create global translator instance"""
    global global_translator
    if global_translator is None:
        global_translator = MangaTranslator()
    return global_translator

def get_api_key_status():
    """Get status of all API keys"""
    translator = get_global_translator()
    status_list = translator.get_api_key_status()
    
    # Format for display
    html_content = """
    <div style=" padding: 20px; border-radius: 10px;">
        <h3>Trạng Thái API Keys</h3>
    """
    
    for status in status_list:
        color = "#28a745" if status['is_active'] and not status['is_failed'] else "#dc3545"
        usage_bar_width = min(status['usage_percentage'], 100)
        
        html_content += f"""
        <div style="border: 1px solid #dee2e6; padding: 15px; margin: 10px 0; border-radius: 5px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: {color};">{status['name']}</strong>
                <span style="font-family: monospace; color: #6c757d;">{status['key_preview']}</span>
            </div>
            <div style="margin-top: 10px;">
                <div>Usage: {status['usage_count']}/{status['daily_limit']} ({status['usage_percentage']:.1f}%)</div>
                <div style="background: #e9ecef; height: 8px; border-radius: 4px; margin-top: 5px;">
                    <div style="background: {color}; height: 100%; width: {usage_bar_width}%; border-radius: 4px;"></div>
                </div>
                <div style="margin-top: 5px; font-size: 12px; color: #6c757d;">
                    Status: {'Active' if status['is_active'] else 'Inactive'} | 
                    {'Failed' if status['is_failed'] else 'OK'} |
                    Last used: {status['last_used'] or 'Never'}
                </div>
            </div>
        </div>
        """
    
    html_content += "</div>"
    return html_content

def add_new_api_key(key, name, daily_limit):
    """Add new API key"""
    if not key or not name:
        return "❌ Vui lòng nhập API key và tên!", get_api_key_status()
    
    try:
        translator = get_global_translator()
        translator.add_api_key(key, name, int(daily_limit or 1000))
        return f"✅ Đã thêm API key: {name}", get_api_key_status()
    except Exception as e:
        return f"❌ Lỗi thêm API key: {e}", get_api_key_status()

def reset_failed_api_keys():
    """Reset failed API keys"""
    try:
        translator = get_global_translator()
        translator.reset_failed_keys()
        return "✅ Đã reset tất cả API key bị lỗi!", get_api_key_status()
    except Exception as e:
        return f"❌ Lỗi reset: {e}", get_api_key_status()

def test_all_api_keys():
    """Test health of all API keys"""
    try:
        translator = get_global_translator()
        health_results = translator.api_key_manager.test_all_keys_health()
        
        healthy_count = sum(1 for status in health_results.values() if status)
        total_count = len(health_results)
        
        result_msg = f"✅ Kiểm tra hoàn thành! Hoạt động: {healthy_count}/{total_count} keys"
        
        return result_msg, get_api_key_status()
    except Exception as e:
        return f"❌ Lỗi test API keys: {e}", get_api_key_status()

def test_failed_api_keys():
    """Test and recover failed API keys"""
    try:
        translator = get_global_translator()
        translator.api_key_manager.auto_test_failed_keys()
        return "✅ Đã kiểm tra lại các key bị lỗi!", get_api_key_status()
    except Exception as e:
        return f"❌ Lỗi test failed keys: {e}", get_api_key_status()

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
    """Process a single image with optimized translation pipeline"""
    
    # Set default values if None
    if translation_method is None:
        translation_method = "google"
    if font_path is None:
        font_path = AVAILABLE_FONTS[0][1] if AVAILABLE_FONTS else "fonts/animeace_i.ttf"

    # Handle API key - DEPRECATED: Use multi-key system from api_keys.json
    if gemini_api_key and gemini_api_key.strip():
        print(f"⚠️ Deprecated: API key truyền từ UI. Khuyến nghị dùng api_keys.json")
        gemini_api_key = gemini_api_key.strip()
    else:
        # Don't use .env - let multi-key system handle it
        gemini_api_key = None
        print("✅ Using multi-API key system from api_keys.json")
    
    # Handle custom prompt
    if custom_prompt and custom_prompt.strip():
        custom_prompt = custom_prompt.strip()
        print(f"Using custom prompt: {custom_prompt[:50]}")
    else:
        custom_prompt = None
        print("Using automatic prompt based on source language")
    
    # Debug logging
    print(f"Using translation method: {translation_method}")
    print(f"Source language: {source_language}")

    # Step 1: Detect text bubbles using YOLO model
    results = detect_bubbles(MODEL, img)
    print(f"Detected {len(results)} bubbles")
    
    # Early return if no bubbles detected
    if not results:
        print("⚠️ No text bubbles detected in image")
        return img
    
    # Sort bubbles by Y coordinate (top to bottom) for better translation context
    results = sorted(results, key=lambda x: x[1])

    # Step 2: Initialize translator - use multi-key system
    manga_translator = MangaTranslator(gemini_api_key=gemini_api_key)
    
    # Step 3: Initialize multi-language OCR system
    multi_ocr = MultiLanguageOCR()
    
    # Show OCR recommendation for selected language
    ocr_method, ocr_desc = multi_ocr.get_best_ocr_for_language(source_language)
    print(f"OCR Engine: {ocr_desc}")

    # Convert PIL image to numpy array for processing
    original_image = np.array(img)
    image = original_image.copy()

    # Step 4: Extract all texts first for potential batch translation
    extracted_texts = []
    bubble_info = []
    
    print("🔍 Extracting text from all bubbles...")
    for idx, result in enumerate(results):
        x1, y1, x2, y2, score, class_id = result
        
        # Extract the bubble region from ORIGINAL image
        detected_image = original_image[int(y1):int(y2), int(x1):int(x2)]

        # Convert to PIL Image for OCR processing
        im = Image.fromarray(np.uint8(detected_image))
        
        # Extract text using appropriate OCR engine
        text = multi_ocr.extract_text(im, source_language, method="auto")
        text = text.strip() if text else ""
        
        extracted_texts.append(text)
        bubble_info.append({
            'coords': (x1, y1, x2, y2),
            'text': text,
            'index': idx
        })
        
        print(f"Bubble {idx+1}: '{text}'")

    # Step 5: Batch translate all texts for better performance
    if any(extracted_texts):  # Only if we have some text
        print(f"🔄 Starting batch translation of {len(extracted_texts)} texts...")
        
        # Filter out empty texts for batch translation
        non_empty_texts = [text for text in extracted_texts if text.strip()]
        
        if non_empty_texts:
            translated_texts = manga_translator.translate_batch(
                non_empty_texts, 
                method=translation_method, 
                source_lang=source_language, 
                custom_prompt=custom_prompt
            )
            
            # Map translations back to original list
            translated_map = dict(zip(non_empty_texts, translated_texts))
            final_translations = [translated_map.get(text, text) for text in extracted_texts]
        else:
            final_translations = extracted_texts
    else:
        final_translations = extracted_texts

    # Step 6: Process each bubble with translated text
    print("🎨 Adding translated text to bubbles...")
    for idx, bubble in enumerate(bubble_info):
        x1, y1, x2, y2 = bubble['coords']
        text_translated = final_translations[idx] if idx < len(final_translations) else ""
        
        if text_translated:
            print(f"Processing bubble {idx+1}: '{text_translated}'")
            
            # Process the bubble for text replacement
            working_bubble = image[int(y1):int(y2), int(x1):int(x2)]
            processed_bubble, cont = process_bubble(working_bubble)
            
            # Add translated text back to the image
            image[int(y1):int(y2), int(x1):int(x2)] = add_text(processed_bubble, text_translated, font_path, cont)
        else:
            print(f"Skipping bubble {idx+1}: no text to translate")

    # Display cache and performance statistics
    stats = manga_translator.get_cache_stats()
    print(f"📊 Translation cache: {stats['cache_size']} entries, {stats['hit_rate']:.1f}% hit rate")
    
    # Show performance monitor stats if available
    try:
        from performance_monitor import performance_monitor
        performance_monitor.record_memory_usage()
        performance_monitor.print_live_stats()
    except ImportError:
        pass

    return Image.fromarray(image)

def process_batch_cached(images, translation_method, font_path, source_language="auto", gemini_api_key=None, custom_prompt=None, enable_splitting=False, split_settings=None):
    """
    Enhanced batch processing using the new BatchImageProcessor
    Supports processing up to 20 images simultaneously with optimal resource usage
    """
    
    if not images:
        return None, [], "No images uploaded"
    
    # Generate unique session ID
    session_id = str(uuid.uuid4())
    total_images = len(images)
    
    print(f"🚀 Starting enhanced batch processing: {total_images} images")
    print(f"📋 Session ID: {session_id}")
    print(f"🎯 Translation method: {translation_method}")
    print(f"🌐 Source language: {source_language}")
    
    # Clean old cache to free memory
    image_cache.clear_old_sessions()
    
    # Prepare image files for batch processor
    image_files = []
    for idx, img_file in enumerate(images):
        try:
            # Open image
            if isinstance(img_file, str):
                img = Image.open(img_file)
                original_name = os.path.basename(img_file)
            else:
                img = Image.open(img_file.name)
                original_name = img_file.name if hasattr(img_file, 'name') else f"image_{idx+1}.png"
            
            image_files.append((img, original_name))
            
        except Exception as e:
            print(f"❌ Error loading image {idx+1}: {e}")
            # Create a placeholder for failed image
            error_img = Image.new('RGB', (100, 100), color='red')
            image_files.append((error_img, f"error_{idx+1}.png"))
    
    print(f"📸 Loaded {len(image_files)} images for processing")
    
    # Process using the new batch processor
    try:
        batch_result = batch_processor.process_images(
            image_files=image_files,
            translation_method=translation_method,
            font_path=font_path,
            source_language=source_language,
            gemini_api_key=gemini_api_key,
            custom_prompt=custom_prompt,
            enable_splitting=enable_splitting,
            split_settings=split_settings
        )
        
        # Convert batch results to cache format
        processed_images = []
        preview_images = []
        
        for task in batch_result.tasks:
            if task.status == "completed" and task.result:
                # Successful processing
                base_name = os.path.splitext(task.filename)[0]
                output_filename = f"{base_name}_translated.png"
                
                image_data = {
                    "original_name": task.filename,
                    "output_name": output_filename,
                    "image": task.result,
                    "status": "success",
                    "index": task.id,
                    "processing_time": task.processing_time,
                    "bubble_count": task.bubble_count,
                    "text_count": task.text_count
                }
                processed_images.append(image_data)
                preview_images.append(task.result)
                
                print(f"✅ {task.filename}: {task.bubble_count} bubbles, {task.text_count} texts, {task.processing_time:.2f}s")
                
            else:
                # Failed processing
                image_data = {
                    "original_name": task.filename,
                    "output_name": "N/A",
                    "image": None,
                    "status": "error",
                    "error_message": task.error or "Unknown error",
                    "index": task.id
                }
                processed_images.append(image_data)
                
                print(f"❌ {task.filename}: {task.error}")
        
        # Store session data in cache
        image_cache.store_session_images(session_id, processed_images)
        
        # Generate enhanced status message
        successful_count = batch_result.successful_images
        failed_count = batch_result.failed_images
        total_time = batch_result.total_time
        total_bubbles = batch_result.summary['total_bubbles']
        total_texts = batch_result.summary['total_texts']
        batches_created = batch_result.summary['batches_created']
        
        # Get splitting statistics
        splitting_stats = ""
        if batch_processor.stats.get('images_with_splitting', 0) > 0:
            splitting_stats = f"""
✂️ Splitting: {batch_processor.stats['images_with_splitting']} images split into {batch_processor.stats['total_split_images']} parts"""
        
        if failed_count == 0:
            status_msg = f"""✅ BATCH PROCESSING COMPLETE!
📊 Successfully processed: {successful_count}/{total_images} images
⏱️ Total time: {total_time:.2f}s (avg {total_time/total_images:.2f}s per image)
🎯 Detected: {total_bubbles} bubbles, {total_texts} text blocks
📦 Processed in {batches_created} optimized batches{splitting_stats}
🚀 Batch efficiency: {batch_result.summary['api_efficiency']}"""
        else:
            status_msg = f"""⚠️ BATCH PROCESSING COMPLETE WITH ERRORS!
📊 Results: {successful_count} successful, {failed_count} failed
⏱️ Total time: {total_time:.2f}s
🎯 Detected: {total_bubbles} bubbles, {total_texts} text blocks
📦 Processed in {batches_created} optimized batches{splitting_stats}"""
        
        # Print batch processing statistics
        print("\n" + "="*50)
        print("📊 BATCH PROCESSING STATISTICS")
        print("="*50)
        print(f"Total images: {total_images}")
        print(f"Successful: {successful_count}")
        print(f"Failed: {failed_count}")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average per image: {total_time/total_images:.2f}s")
        print(f"Total bubbles detected: {total_bubbles}")
        print(f"Total texts extracted: {total_texts}")
        print(f"Batches created: {batches_created}")
        print(f"Batch efficiency: {batch_result.summary['api_efficiency']}")
        
        # Print global processor statistics
        global_stats = batch_processor.get_statistics()
        print(f"\n🌍 GLOBAL PROCESSOR STATS:")
        print(f"Total batches processed: {global_stats['total_batches']}")
        print(f"Total images processed: {global_stats['total_images']}")
        print(f"Success rate: {global_stats['successful_images']}/{global_stats['total_images']}")
        print(f"Average batch time: {global_stats['average_batch_time']:.2f}s")
        print(f"Average image time: {global_stats['average_image_time']:.2f}s")
        print("="*50)
        
        return session_id, preview_images, status_msg
        
    except Exception as e:
        error_msg = f"❌ Batch processing failed: {str(e)}"
        print(error_msg)
        
        # Fallback to original processing
        print("🔄 Falling back to original processing method...")
        return process_batch_cached_fallback(images, translation_method, font_path, source_language, gemini_api_key, custom_prompt, enable_splitting, split_settings)

def process_batch_cached_fallback(images, translation_method, font_path, source_language="auto", gemini_api_key=None, custom_prompt=None, enable_splitting=False, split_settings=None):
    """Fallback batch processing using original method"""
    
    session_id = str(uuid.uuid4())
    total_images = len(images)
    
    print(f"🔄 Fallback batch processing: {total_images} images")
    if enable_splitting:
        print("✂️ Image splitting is ENABLED in fallback mode")
    
    processed_images = []
    preview_images = []
    manga_splitter = MangaSplitter() if enable_splitting else None
    
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
            
            # Handle image splitting if enabled
            images_to_process = [(img, original_name)]
            
            if enable_splitting and split_settings and manga_splitter:
                try:
                    split_images, split_info = manga_splitter.split_image(
                        img,
                        max_height=split_settings.get('max_height', 1500),
                        white_threshold=split_settings.get('white_threshold', 240),
                        black_threshold=split_settings.get('black_threshold', 15),
                        min_separator_height=split_settings.get('min_separator_height', 15),
                        auto_height=split_settings.get('auto_height', True)
                    )
                    
                    if len(split_images) > 1:
                        print(f"✂️ Split {original_name} into {len(split_images)} parts")
                        images_to_process = []
                        base_name = os.path.splitext(original_name)[0]
                        extension = os.path.splitext(original_name)[1]
                        
                        for i, split_img in enumerate(split_images):
                            part_name = f"{base_name}_part_{i+1:03d}{extension}"
                            images_to_process.append((split_img, part_name))
                    
                except Exception as e:
                    print(f"❌ Error splitting {original_name}: {str(e)}")
                    # Continue with original image if splitting fails
            
            # Process each image (original or split parts)
            for img_to_process, name_to_process in images_to_process:
                processed_img = process_single_image(
                    img_to_process, translation_method, font_path, 
                    source_language, gemini_api_key, custom_prompt
                )
                
                # Generate output filename
                base_name = os.path.splitext(os.path.basename(name_to_process))[0]
                output_filename = f"{base_name}_translated.png"
                
                # Store in cache (in memory)
                image_data = {
                    "original_name": name_to_process,
                    "output_name": output_filename,
                    "image": processed_img,
                    "status": "success",
                    "index": len(processed_images)
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
    <div style=" padding: 20px; border-radius: 10px; margin: 10px 0;">
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

def batch_predict(images, translation_method, font_path, source_language="auto", gemini_api_key=None, custom_prompt=None, 
                 enable_splitting=False, auto_height=True, max_height=1500, white_threshold=240, black_threshold=15, min_separator_height=15):
    """Batch prediction function for multiple images (cached version)"""
    
    # Prepare split settings if splitting is enabled
    split_settings = None
    if enable_splitting:
        split_settings = {
            'auto_height': auto_height,
            'max_height': max_height,
            'white_threshold': white_threshold,
            'black_threshold': black_threshold,
            'min_separator_height': min_separator_height
        }
    
    session_id, preview_images, status_msg = process_batch_cached(
        images, translation_method, font_path, 
        source_language, gemini_api_key, custom_prompt,
        enable_splitting, split_settings
    )
    
    if session_id:
        file_list_html = create_file_list_display_cached(session_id)
    else:
        file_list_html = "<p>Cannot process batch</p>"
    
    return preview_images, status_msg

# Legacy single image function
def predict(img, translation_method, font_path, source_language="auto", gemini_api_key=None, custom_prompt=None):
    """Main prediction function for manga translation (single image)"""
    return process_single_image(img, translation_method, font_path, source_language, gemini_api_key, custom_prompt)

# UI Configuration
TITLE = "Multi-Language Comic Translator - Batch Processing with Cache"
DESCRIPTION = """
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
                        [("Gemini AI (Khuyến nghị)", "gemini"),
                         ("DeepInfra Gemma (AI - Miễn phí)", "deepinfra"),
                         ("NLLB API (Chất lượng cao)", "nllb")],
                        label="Phương Pháp Dịch",
                        value="gemini"
                    )
                    
                    font_path = gr.Dropdown(
                        AVAILABLE_FONTS,
                        label="Phông Chữ",
                        value=AVAILABLE_FONTS[0][1] if AVAILABLE_FONTS else "fonts/animeace_i.ttf"
                    )
                    
                    refresh_fonts_btn = gr.Button("🔄 Làm mới danh sách font", size="sm")
                    font_status = gr.Markdown("", visible=False)
                    
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
        
        # Tab 2: Batch Processing
        with gr.TabItem("Xử Lý Hàng Loạt"):
            with gr.Row():
                with gr.Column():
                    folder_input = gr.File(
                        file_count="multiple",
                        file_types=[".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".gif"],
                        label="Chọn ảnh để xử lý hàng loạt"
                    )
                    
                    # Configuration for batch
                    batch_translation_method = gr.Dropdown(
                        [("Gemini AI (Khuyến nghị)", "gemini"),
                         ("DeepInfra Gemma (AI - Miễn phí)", "deepinfra"),
                         ("NLLB API (Chất lượng cao)", "nllb")],
                        label="Phương Pháp Dịch",
                        value="gemini"
                    )
                    
                    batch_font_path = gr.Dropdown(
                        AVAILABLE_FONTS,
                        label="Phông Chữ",
                        value=AVAILABLE_FONTS[0][1] if AVAILABLE_FONTS else "fonts/animeace_i.ttf"
                    )
                    
                    batch_source_language = gr.Dropdown(
                        [("Tự Động Nhận Dạng", "auto"),
                         ("Japanese (Manga)", "ja"),
                         ("Chinese (Manhua)", "zh"),
                         ("Korean (Manhwa)", "ko"),
                         ("English", "en")],
                        label="Ngôn Ngữ Gốc",
                        value="auto"
                    )
                    
                    batch_gemini_api_key = gr.Textbox(
                        label="Gemini API Key (Tùy chọn)", 
                        type="password", 
                        placeholder="Nhập API key cho dịch thuật AI",
                        value=os.getenv("GEMINI_API_KEY", "")
                    )
                    
                    batch_custom_prompt = gr.Textbox(
                        label="Prompt Tùy Chỉnh (Nâng cao)", 
                        lines=3,
                        placeholder="Để trống để sử dụng prompt tự động",
                        value=""
                    )
                    
                    # ✂️ Splitting Settings Section
                    with gr.Accordion("✂️ Cài Đặt Cắt Ảnh (Tuỳ Chọn)", open=False):
                        batch_enable_splitting = gr.Checkbox(
                            label="🔧 Bật chức năng cắt ảnh trước khi dịch",
                            value=False,
                            info="Tự động cắt ảnh dài thành nhiều phần nhỏ để dịch hiệu quả hơn"
                        )
                        
                        batch_auto_height = gr.Checkbox(
                            label="🤖 Tự động điều chỉnh chiều cao tối ưu",
                            value=True,
                            info="Tự động tính chiều cao phù hợp dựa trên kích thước ảnh"
                        )
                        
                        batch_max_height = gr.Slider(
                            minimum=1500, maximum=5000, value=1500, step=100,
                            label="📏 Chiều cao tối đa mỗi phần (px)",
                            info="Chỉ áp dụng khi tắt chế độ tự động (tối thiểu 1500px)",
                            visible=False
                        )
                        
                        batch_white_threshold = gr.Slider(
                            minimum=200, maximum=255, value=240, step=5,
                            label="⚪ Ngưỡng pixel trắng",
                            info="Độ trắng để nhận diện vùng separator (240 = rất trắng)"
                        )
                        
                        batch_black_threshold = gr.Slider(
                            minimum=0, maximum=50, value=15, step=5,
                            label="⚫ Ngưỡng pixel đen",
                            info="Độ đen để nhận diện vùng dramatic (15 = rất đen)"
                        )
                        
                        batch_min_separator_height = gr.Slider(
                            minimum=5, maximum=50, value=15, step=5,
                            label="📐 Chiều cao tối thiểu vùng separator",
                            info="Vùng separator phải cao ít nhất bao nhiêu pixel"
                        )
                        
                        # Toggle manual height visibility
                        def toggle_manual_height(auto_mode):
                            return gr.update(visible=not auto_mode)
                        
                        batch_auto_height.change(
                            toggle_manual_height,
                            inputs=[batch_auto_height],
                            outputs=[batch_max_height]
                        )
                    
                    batch_submit_btn = gr.Button("Xử Lý Hàng Loạt", variant="primary")
                
                with gr.Column():
                    batch_output = gr.Gallery(
                        label="Kết Quả Hàng Loạt",
                        show_label=True,
                        elem_id="gallery",
                        columns=2,
                        rows=2,
                        height="auto"
                    )
            
            batch_status = gr.HTML("Sẵn sàng xử lý hàng loạt")
        
        # Tab 3: API Management - Cleaner interface
        with gr.TabItem("🔑 Quản Lý API", elem_id="api-tab"):
            gr.HTML("""
            <div class="config-panel">
                <h2 style="color: #007bff; margin-top: 0;">� Multi-API Key Management</h2>
                <p style="color: #6c757d;">
                    Quản lý nhiều GEMINI API Key để tối ưu hóa sử dụng và tránh giới hạn rate limit
                </p>
                <div style=" padding: 15px; border-radius: 8px; margin: 15px 0;">
                    <strong>✨ Tính năng:</strong>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>🔄 Round-robin rotation giữa các key</li>
                        <li>🛡️ Auto failover khi key bị lỗi</li>
                        <li>📊 Daily usage tracking</li>
                        <li>⚖️ Load balancing thông minh</li>
                    </ul>
                </div>
            </div>
            """)
            
            with gr.Row():
                with gr.Column(scale=2):
                    # API Key status display with better formatting
                    gr.HTML("<h3 style='color: #28a745; margin: 20px 0 15px 0;'>📊 Trạng Thái API Keys</h3>")
                    api_status_display = gr.HTML(
                        value=get_api_key_status(),
                        elem_id="api_status"
                    )
                    
                    # Action buttons in a clean row
                    with gr.Row():
                        refresh_status_btn = gr.Button(
                            "🔄 Refresh",
                            variant="secondary",
                            elem_classes="action-button secondary-button"
                        )
                        reset_failed_btn = gr.Button(
                            "♻️ Reset Failed",
                            variant="secondary", 
                            elem_classes="action-button secondary-button"
                        )
                    
                    # Health check buttons in a second row
                    with gr.Row():
                        test_all_btn = gr.Button(
                            "🔍 Test All Keys",
                            variant="secondary",
                            elem_classes="action-button secondary-button"
                        )
                        test_failed_btn = gr.Button(
                            "🔁 Test Failed Keys",
                            variant="secondary",
                            elem_classes="action-button secondary-button"
                        )
                
                with gr.Column(scale=1):
                    with gr.Group():
                        gr.HTML("<h3 style='color: #007bff; margin: 20px 0 15px 0;'>➕ Thêm API Key</h3>")
                        
                        new_api_key = gr.Textbox(
                            label="🔑 API Key",
                            type="password",
                            placeholder="Nhập GEMINI API KEY mới",
                            interactive=True
                        )
                        
                        new_key_name = gr.Textbox(
                            label="🏷️ Tên Mô Tả",
                            placeholder="VD: Primary Key, Backup Key...",
                            interactive=True
                        )
                        
                        new_daily_limit = gr.Number(
                            label="📈 Daily Limit",
                            value=1000,
                            minimum=1,
                            maximum=10000,
                            interactive=True
                        )
                        
                        add_key_btn = gr.Button(
                            "➕ Thêm Key",
                            variant="primary",
                            elem_classes="action-button primary-button"
                        )
                        
                        # Status message with better styling
                        key_management_status = gr.HTML(
                            """<div class="status-panel">
                                <p style="margin: 0; text-align: center; color: #6c757d;">
                                    ℹ️ Kết quả thao tác sẽ hiển thị ở đây
                                </p>
                            </div>""",
                            visible=True
                        )
    
    # Event handlers with improved error handling and user feedback
    def handle_single_image_process(img, method, font, lang, api_key, prompt):
        """Enhanced single image processing with better error handling"""
        if img is None:
            return None, """<div class="error-panel">
                <p style="margin: 0; text-align: center;">
                    ❌ Vui lòng upload ảnh trước khi xử lý
                </p>
            </div>"""
        
        try:
            result = predict(img, method, font, lang, api_key, prompt)
            success_html = """<div class="status-panel">
                <p style="margin: 0; text-align: center; color: #28a745;">
                    ✅ Xử lý thành công! Ảnh đã được dịch.
                </p>
            </div>"""
            return result, success_html
        except Exception as e:
            error_html = f"""<div class="error-panel">
                <p style="margin: 0; text-align: center;">
                    ❌ Lỗi xử lý: {str(e)[:100]}...
                </p>
            </div>"""
            return None, error_html
    
    def handle_batch_process(images, method, font, lang, api_key, prompt):
        """Enhanced batch processing with progress feedback"""
        if not images:
            error_status = """<div class="error-panel">
                <h4 style="margin-top: 0; color: #dc3545;">❌ Lỗi</h4>
                <p style="margin: 0;">Vui lòng upload ít nhất một ảnh</p>
            </div>"""
            return "", [], "<p>Chưa có file nào</p>", error_status
        
        processing_status = f"""<div class="status-panel">
            <h4 style="margin-top: 0; color: #007bff;">🔄 Đang Xử Lý</h4>
            <p style="margin: 0;">Đang xử lý {len(images)} ảnh. Vui lòng đợi...</p>
            <div style="background: #e9ecef; height: 6px; border-radius: 3px; margin-top: 10px;">
                <div style="background: #007bff; height: 100%; width: 0%; border-radius: 3px; animation: progress 2s infinite;"></div>
            </div>
        </div>"""
        
        try:
            session_id, preview_images, file_list_html, status_msg = batch_predict(
                images, method, font, lang, api_key, prompt
            )
            
            if "Complete!" in status_msg or "COMPLETE!" in status_msg:
                final_status = f"""<div class="status-panel">
                    <h4 style="margin-top: 0; color: #28a745;">✅ Hoàn Thành</h4>
                    <p style="margin: 0;">{status_msg}</p>
                </div>"""
            else:
                final_status = f"""<div class="error-panel">
                    <h4 style="margin-top: 0; color: #dc3545;">⚠️ Có Lỗi</h4>
                    <p style="margin: 0;">{status_msg}</p>
                </div>"""
            
            return session_id, preview_images, file_list_html, final_status
            
        except Exception as e:
            error_status = f"""<div class="error-panel">
                <h4 style="margin-top: 0; color: #dc3545;">❌ Lỗi Hệ Thống</h4>
                <p style="margin: 0;">Lỗi xử lý batch: {str(e)[:100]}...</p>
            </div>"""
            return "", [], "<p>Lỗi xử lý</p>", error_status
    
    def handle_font_refresh():
        """Enhanced font refresh with user feedback"""
        try:
            dropdown, status = refresh_fonts()
            return dropdown, """<div class="status-panel" style="margin: 10px 0;">
                <p style="margin: 0; color: #28a745; text-align: center;">
                    ✅ Đã làm mới danh sách font thành công
                </p>
            </div>"""
        except Exception as e:
            return None, f"""<div class="error-panel" style="margin: 10px 0;">
                <p style="margin: 0; color: #dc3545; text-align: center;">
                    ❌ Lỗi làm mới font: {str(e)}
                </p>
            </div>"""
    
    def handle_zip_creation(session_id):
        """Enhanced ZIP creation with better feedback"""
        if not session_id:
            return None, """<div class="error-panel">
                <p style="margin: 0; text-align: center;">
                    ❌ Không có session để tạo ZIP
                </p>
            </div>"""
        
        try:
            zip_path, status_msg = create_zip_download(session_id)
            if zip_path:
                return zip_path, f"""<div class="status-panel">
                    <p style="margin: 0; text-align: center; color: #28a745;">
                        ✅ {status_msg}
                    </p>
                </div>"""
            else:
                return None, f"""<div class="error-panel">
                    <p style="margin: 0; text-align: center;">
                        ❌ {status_msg}
                    </p>
                </div>"""
        except Exception as e:
            return None, f"""<div class="error-panel">
                <p style="margin: 0; text-align: center;">
                    ❌ Lỗi tạo ZIP: {str(e)}
                </p>
            </div>"""
    
    def handle_api_management(action, *args):
        """Enhanced API management with better feedback"""
        try:
            if action == "add":
                key, name, limit = args
                status_msg, api_status = add_new_api_key(key, name, limit)
                if "✅" in status_msg:
                    status_html = f"""<div class="status-panel">
                        <p style="margin: 0; text-align: center; color: #28a745;">{status_msg}</p>
                    </div>"""
                else:
                    status_html = f"""<div class="error-panel">
                        <p style="margin: 0; text-align: center;">{status_msg}</p>
                    </div>"""
                return status_html, api_status
            elif action == "reset":
                status_msg, api_status = reset_failed_api_keys()
                status_html = f"""<div class="status-panel">
                    <p style="margin: 0; text-align: center; color: #28a745;">{status_msg}</p>
                </div>"""
                return status_html, api_status
            elif action == "refresh":
                api_status = get_api_key_status()
                return None, api_status
        except Exception as e:
            error_html = f"""<div class="error-panel">
                <p style="margin: 0; text-align: center;">❌ Lỗi: {str(e)}</p>
            </div>"""
            return error_html, get_api_key_status()
    
    # Event handlers  
    single_submit_btn.click(
        fn=predict,
        inputs=[single_image_input, translation_method, font_path, source_language, gemini_api_key, custom_prompt],
        outputs=single_output
    )
    
    batch_submit_btn.click(
        fn=batch_predict,
        inputs=[folder_input, batch_translation_method, batch_font_path, batch_source_language, batch_gemini_api_key, batch_custom_prompt,
                batch_enable_splitting, batch_auto_height, batch_max_height, batch_white_threshold, batch_black_threshold, batch_min_separator_height],
        outputs=[batch_output, batch_status]
    )
    
    refresh_fonts_btn.click(
        fn=refresh_fonts,
        outputs=[font_path, font_status]
    )
    
    refresh_status_btn.click(
        fn=get_api_key_status,
        outputs=api_status_display
    )
    
    add_key_btn.click(
        fn=add_new_api_key,
        inputs=[new_api_key, new_key_name, new_daily_limit],
        outputs=[key_management_status, api_status_display]
    )
    
    reset_failed_btn.click(
        fn=reset_failed_api_keys,
        outputs=[key_management_status, api_status_display]
    )
    
    # New health check button handlers
    test_all_btn.click(
        fn=test_all_api_keys,
        outputs=[key_management_status, api_status_display]
    )
    
    test_failed_btn.click(
        fn=test_failed_api_keys,
        outputs=[key_management_status, api_status_display]
    )

# Launch the application
if __name__ == "__main__":
    demo.launch(debug=False, share=True)
