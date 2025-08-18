#!/usr/bin/env python3
"""
Enhanced Manga Translator Module
===============================

A comprehensive translation system for manga/comic text with context-aware AI translation.

🆕 NEW FEATURES:
- Context metadata support for smart pronoun/honorific selection
- Locked output format (translation only - no explanations)  
- Language-specific rules for JA/ZH/KO comics
- SFX and thought bubble specialized handling
- Bubble fitting with character limits
- Line preservation for multi-bubble text

Features:
- AI translation backends (Gemini, DeepInfra Gemma)
- High-quality neural translation (NLLB)
- Context-aware translation with relationship/formality/gender metadata
- Language-specific prompts (Japanese manga, Chinese manhua, Korean manhwa)
- Clean output guarantee (no AI explanations or multiple options)
- Automatic language detection
- Error handling and fallbacks

Author: MangaTranslator Team  
License: MIT
Version: 2.0 (Enhanced Prompt System)
"""

# Translation libraries (kept minimal)
# Removed: GoogleTranslator, pipeline, translators
from api_key_manager import APIKeyManager
pass

# Standard library imports
import requests
import random
import time
import os
import json
import re

# Performance monitoring (optional)
try:
    from performance_monitor import performance_monitor
    PERFORMANCE_MONITORING = True
except ImportError:
    PERFORMANCE_MONITORING = False
    performance_monitor = None

# Performance monitoring
try:
    from performance_monitor import performance_monitor
    PERFORMANCE_MONITORING = True
except ImportError:
    PERFORMANCE_MONITORING = False
    performance_monitor = None


class MangaTranslator:
    """
    Multi-service translator optimized for manga/comic text translation with context awareness.
    
    🆕 OPTIMIZED VERSION 2.1:
    - Translation caching system for performance
    - Batch translation support
    - Improved error handling and fallbacks
    - Smart text preprocessing and post-processing
    - Context metadata support for intelligent translation
    - Clean output guarantee (no AI explanations)
    """
    
    def __init__(self, gemini_api_key=None):
        """
        🚀 ENHANCED TRANSLATOR V3.0 - Initialize with intelligent optimization
        
        Args:
            gemini_api_key (str, optional): Gemini API key for AI translation (deprecated - sử dụng api_keys.json)
        """
        self.target = "vi"  # Target language: Vietnamese
        
        # 🔧 Initialize smart optimizer
        try:
            from config_optimizer import get_optimizer
            self.optimizer = get_optimizer()
            self.optimization_enabled = True
            print("🎯 Smart optimization system activated")
        except ImportError:
            print("⚠️ Optimizer not available - using default settings")
            self.optimizer = None
            self.optimization_enabled = False
        
        # Enhanced translation cache with intelligent sizing
        cache_size = 10000  # Default
        if self.optimizer:
            cache_size = self.optimizer.config["performance"]["cache_max_size"]
        
        self.translation_cache = {}
        self.cache_hits = 0
        self.total_requests = 0
        self.max_cache_size = cache_size
        
        # Supported source languages mapping
        self.supported_languages = {
            "auto": "Tự động nhận diện",
            "ja": "Tiếng Nhật (Manga)",
            "zh": "Tiếng Trung (Manhua)", 
            "ko": "Tiếng Hàn (Manhwa)",
            "en": "Tiếng Anh"
        }
        
        # Initialize API Key Manager
        self.api_key_manager = APIKeyManager("api_keys.json")
        
        # Backward compatibility: nếu có gemini_api_key được truyền vào
        if gemini_api_key and gemini_api_key.strip():
            print(f"⚠️ Đang sử dụng API key truyền vào trực tiếp: {gemini_api_key[:10]}...")
            print("💡 Khuyến nghị: Thêm API key vào file api_keys.json để sử dụng tính năng multi-key")
            self.fallback_api_key = gemini_api_key.strip()
        else:
            self.fallback_api_key = None
        
        # Test API key availability (không count usage)
        test_key = self.api_key_manager.get_active_key(count_usage=False)
        if test_key:
            print(f"✅ Multi-API key system đã sẵn sàng với {len(self.api_key_manager.config['gemini_api_keys'])} key(s)")
        elif self.fallback_api_key:
            print("✅ Sử dụng single API key mode")
        else:
            print("⚠️ Không có Gemini API key khả dụ - vui lòng cấu hình api_keys.json")
            
        # Enhanced translation methods mapping with intelligent ordering
        self.translators = {
            "gemini": self._translate_with_gemini,      # Best quality with context
            "deepinfra": self._translate_with_deepinfra, # AI alternative with Gemma model
            "nllb": self._translate_with_nllb,         # High quality, reliable fallback
        }
        
        # Language mapping for NLLB API (FLORES-200 codes)
        self.nllb_language_map = {
            "auto": "eng_Latn",  # Default to English for auto-detect
            "ja": "jpn_Jpan",    # Japanese
            "zh": "zho_Hans",    # Chinese Simplified
            "ko": "kor_Hang",    # Korean
            "en": "eng_Latn",    # English
            "vi": "vie_Latn"     # Vietnamese (target)
        }
        
        # Initialize enhanced common phrases cache
        self._init_common_phrases_cache()
        
        # Performance tracking
        self.performance_stats = {
            "total_translations": 0,
            "successful_translations": 0,
            "cache_hits": 0,
            "method_usage": {},
            "avg_translation_time": 0
        }

    def _init_common_phrases_cache(self):
        """
        🔥 CACHE THÔNG MINH V3.0 - Khởi tạo cache với common phrases được mở rộng
        Bao gồm cả các cụm từ phức tạp và context-aware translations
        """
        self.common_phrases = {
            # 🎌 Japanese common phrases (mở rộng)
            "はい": "Được", "いいえ": "Không", "すみません": "Xin lỗi",
            "ありがとう": "Cảm ơn", "ありがとうございます": "Cảm ơn",
            "こんにちは": "Xin chào", "おはよう": "Chào buổi sáng",
            "おやすみ": "Chúc ngủ ngon", "そうですね": "Đúng vậy",
            "わかりました": "Tôi hiểu rồi", "がんばって": "Cố lên!",
            "やった": "Làm được rồi!", "だめ": "Không được",
            "すごい": "Tuyệt vời!", "やばい": "Tệ rồi!",
            "本当": "Thật sự", "嘘": "Dối trá",
            "待って": "Đợi đã", "助けて": "Giúp tôi",
            
            # Japanese expressions (new)
            "そうか": "Ra vậy", "なるほど": "Hiểu rồi",
            "大丈夫": "Không sao đâu", "お疲れ様": "Cảm ơn bạn đã vất vả",
            "頑張れ": "Cố lên nào!", "無理": "Không thể được",
            "危ない": "Nguy hiểm!", "見つけた": "Tìm thấy rồi!",
            "行こう": "Đi thôi!", "やめて": "Dừng lại!",
            
            # 🏮 Chinese common phrases (mở rộng)  
            "你好": "Xin chào", "谢谢": "Cảm ơn", "对不起": "Xin lỗi",
            "不客气": "Không có gì", "再见": "Tạm biệt",
            "是的": "Đúng vậy", "不是": "Không phải",
            "好的": "Được rồi", "没问题": "Không vấn đề gì",
            "太好了": "Quá tuyệt!", "加油": "Cố lên!",
            "小心": "Cẩn thận", "等等": "Đợi chút", "救命": "Cứu tôi",
            
            # Chinese expressions (new)
            "走吧": "Đi thôi!", "没事": "Không sao",
            "真的吗": "Thật sự à?", "当然": "Dĩ nhiên",
            "不要": "Đừng", "快点": "Nhanh lên!",
            "慢着": "Khoan đã", "完了": "Xong rồi",
            "怎么了": "Sao vậy?", "明白了": "Hiểu rồi",
            
            # 🇰🇷 Korean common phrases (mở rộng)
            "안녕하세요": "Xin chào", "감사합니다": "Cảm ơn",
            "죄송합니다": "Xin lỗi", "네": "Vâng", "아니요": "Không",
            "괜찮아요": "Không sao đâu", "잠깐만요": "Chờ chút",
            "도와주세요": "Giúp tôi", "화이팅": "Cố lên!",
            "대박": "Tuyệt vời!", "헐": "Hả?!", "와": "Wow!",
            
            # Korean expressions (new)
            "가자": "Đi thôi!", "알겠어": "Hiểu rồi",
            "진짜": "Thật sự", "맞아": "Đúng rồi",
            "아니야": "Không phải", "빨리": "Nhanh lên",
            "잠깐": "Khoan", "끝났어": "Xong rồi",
            "뭐야": "Cái gì vậy?", "어떻게": "Làm sao?",
            
            # 🔊 Sound effects (SFX) - Enhanced
            # Japanese SFX
            "バン": "BÙNG!", "ドン": "RẦM!", "キラキラ": "lấp lánh",
            "ドキドキ": "thình thịch", "ブーン": "VỪN!", "ザー": "ào ào",
            "ピカピカ": "lóng lánh", "ガタガタ": "run bần bật",
            "ペコペコ": "đói cồn cào", "フワフワ": "mềm mịn",
            "ズズズ": "húp húp", "パチパチ": "tép tép",
            
            # Chinese SFX  
            "轰": "BOOM!", "砰": "ĐỤC!", "咔嚓": "KẮC!",
            "嘶": "xì", "呼": "phù", "啪": "tách",
            "哗": "ào", "嘭": "bụp", "咕咚": "cục tác",
            "滴答": "tích tắc", "哐当": "loảng xoảng",
            
            # Korean SFX
            "쾅": "CẠCH!", "쿵": "RẦM!", "휘익": "VỪN!",
            "따르르": "lách tách", "두근두근": "thình thịch",
            "펑": "bùng", "찰칵": "cắt", "쨍": "lanh",
            "부웅": "vù", "졸졸": "róc rách",
            
            # 😊 Emotional expressions
            "ハハハ": "Ha ha ha!", "ホホホ": "Ho ho ho!",
            "えへへ": "He he he", "うううう": "Ưưưư",
            "哈哈哈": "Ha ha ha!", "呵呵": "He he",
            "호호호": "Ho ho ho", "하하하": "Ha ha ha",
            
            # 💥 Action phrases
            "やれやれ": "Hài thật", "まずい": "Tệ rồi",
            "しまった": "Chết tiệt!", "よし": "Được rồi!",
            "糟糕": "Tệ rồi", "完蛋": "Tiêu rồi",
            "아차": "Ối", "어이구": "Ôi trời",
            
            # 🤔 Thinking expressions
            "うーん": "Ừm...", "そうねえ": "Để xem nào...",
            "嗯": "Ừm", "这样啊": "Ra vậy à",
            "음": "Ừm", "그렇구나": "Ra vậy"
        }
        
        # 🎯 Context-aware phrases (Thêm mới)
        self.context_phrases = {
            # Formal context
            ("です", "formal"): "ạ", ("ます", "formal"): "ạ",
            ("습니다", "formal"): "ạ", ("您好", "formal"): "Thưa",
            
            # Casual context  
            ("だよ", "casual"): "đấy", ("じゃん", "casual"): "mà",
            ("야", "casual"): "", ("哦", "casual"): "ồ",
            
            # Emotional context
            ("うれしい", "happy"): "vui quá", ("悲しい", "sad"): "buồn thật",
            ("기쁘다", "happy"): "vui quá", ("슬프다", "sad"): "buồn thật"
        }
        
        # Add all phrases to main cache
        for original, translated in self.common_phrases.items():
            cache_key = self._get_cache_key(original, "auto", None)
            self.translation_cache[cache_key] = translated
            
        # Add context phrases
        for (original, context_type), translated in self.context_phrases.items():
            cache_key = self._get_cache_key(original, "auto", {"context_type": context_type})
            self.translation_cache[cache_key] = translated

    def _get_cache_key(self, text, source_lang, context):
        """Generate cache key for translation"""
        context_str = ""
        if context:
            context_items = [
                context.get('gender', ''),
                context.get('relationship', ''),
                context.get('formality', ''),
                str(context.get('is_thought', False)),
                str(context.get('is_sfx', False))
            ]
            context_str = "|".join(context_items)
        
        return f"{text.strip().lower()}:{source_lang}:{context_str}"

    def _is_simple_text(self, text):
        """Check if text is simple enough for fast translation"""
        if not text or len(text.strip()) == 0:
            return True
        
        # Simple criteria for fast translation
        text = text.strip()
        return (
            len(text) <= 30 and  # Short text
            not any(char in text for char in ".,!?;:()[]{}") and  # No complex punctuation
            len(text.split()) <= 5  # Few words
        )

    def get_cache_stats(self):
        """Get cache performance statistics"""
        hit_rate = (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0
        return {
            "cache_size": len(self.translation_cache),
            "total_requests": self.total_requests,
            "cache_hits": self.cache_hits,
            "hit_rate": hit_rate
        }

    def clear_cache(self):
        """Clear translation cache"""
        self.translation_cache.clear()
        self.cache_hits = 0
        self.total_requests = 0
        # Re-initialize common phrases
        self._init_common_phrases_cache()

    def get_api_key_status(self):
        """
        Lấy trạng thái của tất cả API key
        
        Returns:
            List[Dict]: Danh sách trạng thái các key
        """
        return self.api_key_manager.get_key_status()
    
    def reset_failed_keys(self):
        """Reset danh sách API key bị lỗi"""
        self.api_key_manager.reset_failed_keys()
    
    def add_api_key(self, key: str, name: str, daily_limit: int = 1000):
        """
        Thêm API key mới
        
        Args:
            key (str): API key
            name (str): Tên mô tả  
            daily_limit (int): Giới hạn sử dụng hàng ngày
        """
        self.api_key_manager.add_api_key(key, name, daily_limit)

    def translate_batch(self, texts, method="gemini", source_lang="auto", context=None, custom_prompt=None):
        """
        Translate multiple texts in batch for better performance
        
        Args:
            texts (list): List of texts to translate
            method (str): Translation method
            source_lang (str): Source language code
            context (dict, optional): Context metadata
            custom_prompt (str, optional): Custom translation prompt
            
        Returns:
            list: List of translated texts
        """
        if not texts:
            return []
        
        print(f"🔄 Batch translating {len(texts)} texts using {method}")
        
        # Start batch performance monitoring
        batch_start_time = time.time()
        
        # For Gemini, use optimized batch translation (check availability without counting)
        if method == "gemini" and (self.api_key_manager.get_active_key(count_usage=False) or self.fallback_api_key):
            try:
                # Check cache first for each text ONLY if cache enabled
                cached_results = []
                uncached_texts = []
                uncached_indices = []
                
                if self.optimizer and self.optimizer.config.get("performance", {}).get("cache_enabled", False):
                    for i, text in enumerate(texts):
                        cache_key = self._get_cache_key(text, source_lang, context)
                        if cache_key in self.translation_cache:
                            cached_results.append((i, self.translation_cache[cache_key]))
                        else:
                            uncached_texts.append(text)
                            uncached_indices.append(i)
                else:
                    # Cache disabled - translate all texts fresh
                    uncached_texts = texts.copy()
                    uncached_indices = list(range(len(texts)))
                    print(f"🔄 Cache disabled - fresh translation for all {len(texts)} texts")
                
                print(f"📊 Cache hits: {len(cached_results)}/{len(texts)}")
                
                # Translate uncached texts in batch
                if uncached_texts:
                    batch_translations = self._translate_with_gemini(uncached_texts, source_lang, context, custom_prompt)
                    
                    # Store batch results in cache ONLY if cache enabled
                    if self.optimizer and self.optimizer.config.get("performance", {}).get("cache_enabled", False):
                        for text, translation in zip(uncached_texts, batch_translations):
                            cache_key = self._get_cache_key(text, source_lang, context)
                            self.translation_cache[cache_key] = translation
                else:
                    batch_translations = []
                
                # Combine cached and new results
                results = [""] * len(texts)
                for i, cached_result in cached_results:
                    results[i] = cached_result
                for i, (uncached_idx, translation) in enumerate(zip(uncached_indices, batch_translations)):
                    results[uncached_idx] = translation
                
                # Record performance
                batch_duration = time.time() - batch_start_time
                print(f"✅ Gemini batch completed in {batch_duration:.2f}s")
                
                return results
                
            except Exception as e:
                print(f"❌ Gemini batch failed: {e}, falling back to individual translations")
                # Fall through to individual translation mode
        
        # Fallback: individual translations (for other methods or if batch fails)
        results = []
        cache_hits = 0
        
        for i, text in enumerate(texts):
            try:
                # Try cache first ONLY if enabled
                translated = None
                if self.optimizer and self.optimizer.config.get("performance", {}).get("cache_enabled", False):
                    cache_key = self._get_cache_key(text, source_lang, context)
                    if cache_key in self.translation_cache:
                        translated = self.translation_cache[cache_key]
                        cache_hits += 1
                
                if translated is None:
                    # Translate new text
                    translated = self.translate(text, method, source_lang, context, custom_prompt)
                    # Store in cache ONLY if enabled
                    if self.optimizer and self.optimizer.config.get("performance", {}).get("cache_enabled", False):
                        cache_key = self._get_cache_key(text, source_lang, context)
                        self.translation_cache[cache_key] = translated
                
                results.append(translated)
                
                # Progress update for large batches
                if len(texts) > 10 and (i + 1) % 5 == 0:
                    print(f"📊 Progress: {i + 1}/{len(texts)} | Cache hits: {cache_hits}")
                    
            except Exception as e:
                print(f"❌ Error translating text {i + 1}: {e}")
                results.append(text)  # Fallback to original
        
        # Record batch performance
        batch_duration = time.time() - batch_start_time
        if PERFORMANCE_MONITORING:
            performance_monitor.record_batch_performance(len(texts), batch_duration, cache_hits)
            performance_monitor.record_cache_stats(len(self.translation_cache), self.total_requests, self.cache_hits)
        
        print(f"✅ Batch completed in {batch_duration:.2f}s. Cache hits: {cache_hits}/{len(texts)}")
        return results

    def smart_translate(self, texts_or_text, method="auto", source_lang="auto", context=None, custom_prompt=None, batch_threshold=3):
        """
        🧠 SMART TRANSLATION V3.0 - AI-powered intelligent translation system
        Automatically optimizes translation approach based on content and system state
        
        Args:
            texts_or_text (str|list): Single text string or list of texts
            method (str): Translation method ("auto" for intelligent selection)
            source_lang (str): Source language code  
            context (dict, optional): Context metadata
            custom_prompt (str, optional): Custom translation prompt
            batch_threshold (int): Minimum number of texts to use batch translation
            
        Returns:
            str|list: Single translated text or list of translated texts
        """
        start_time = time.time()
        
        # 📊 Prepare context for optimization
        optimization_context = {
            "is_batch": isinstance(texts_or_text, list),
            "text_count": len(texts_or_text) if isinstance(texts_or_text, list) else 1,
            "source_lang": source_lang,
            "quality_priority": method == "gemini" or method == "auto",
            "speed_priority": method == "deepinfra"
        }
        
        if isinstance(texts_or_text, list):
            optimization_context["avg_text_length"] = sum(len(str(t)) for t in texts_or_text) / len(texts_or_text)
        else:
            optimization_context["avg_text_length"] = len(str(texts_or_text))
        
        # 🎯 Get optimized settings if available
        if self.optimization_enabled:
            optimal_settings = self.optimizer.get_optimal_settings(optimization_context)
            
            # Use optimal method if auto-selection
            if method == "auto":
                method = optimal_settings["method"]
                print(f"🎯 Auto-selected method: {method}")
            
            # Use optimal batch size
            if optimization_context["is_batch"]:
                batch_threshold = optimal_settings["batch_size"]
                print(f"🎯 Optimal batch threshold: {batch_threshold}")
        
        # Single text input
        if isinstance(texts_or_text, str):
            result = self.translate(texts_or_text, method, source_lang, context, custom_prompt)
            
            # Record performance if optimization enabled
            if self.optimization_enabled:
                duration = time.time() - start_time
                self._record_translation_performance(method, 1, duration, result != texts_or_text)
            
            return result
        
        # List input - intelligent batch processing
        if isinstance(texts_or_text, list):
            text_count = len(texts_or_text)
            
            # 🚀 Enhanced batch decision logic
            should_use_batch = (
                text_count >= batch_threshold and 
                method in ["gemini", "deepinfra"] and
                optimization_context["avg_text_length"] < 200  # Don't batch very long texts
            )
            
            if should_use_batch:
                print(f"🚀 Smart batch mode: {text_count} texts with {method}")
                
                # Enhanced context for batch processing
                if context is None:
                    context = {}
                context["is_mega_batch"] = text_count > 20
                context["total_images"] = text_count // 10 + 1  # Estimate
                
                result = self.translate_batch(texts_or_text, method, source_lang, context, custom_prompt)
            else:
                print(f"🔄 Individual translation mode: {text_count} texts")
                result = []
                cache_hits = 0
                
                for text in texts_or_text:
                    # Check cache first for performance ONLY if enabled
                    translated = None
                    if self.optimizer and self.optimizer.config.get("performance", {}).get("cache_enabled", False):
                        cache_key = self._get_cache_key(text, source_lang, context)
                        if cache_key in self.translation_cache:
                            translated = self.translation_cache[cache_key]
                            cache_hits += 1
                    
                    if translated is None:
                        translated = self.translate(text, method, source_lang, context, custom_prompt)
                    
                    result.append(translated)
                
                print(f"💾 Individual mode cache hits: {cache_hits}/{text_count}")
            
            # Record batch performance if optimization enabled
            if self.optimization_enabled:
                duration = time.time() - start_time
                self._record_batch_performance(method, text_count, duration, context)
            
            return result
        
        # Invalid input
        raise ValueError("Input must be string or list of strings")
    
    def _record_translation_performance(self, method: str, text_count: int, duration: float, success: bool):
        """Record translation performance for optimizer"""
        if not self.optimization_enabled:
            return
        
        metrics = {
            "method": method,
            "text_count": text_count,
            "duration": duration,
            "texts_per_second": text_count / duration if duration > 0 else 0,
            "success": success,
            "cache_hit_rate": (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0,
            "efficiency_score": self._calculate_efficiency_score(text_count, duration, success)
        }
        
        self.optimizer.record_performance(metrics)
    
    def _record_batch_performance(self, method: str, batch_size: int, duration: float, context: dict):
        """Record batch performance metrics"""
        if not self.optimization_enabled:
            return
        
        cache_hits = context.get("cache_hits", 0) if context else 0
        
        metrics = {
            "method": method,
            "batch_size": batch_size,
            "duration": duration,
            "texts_per_second": batch_size / duration if duration > 0 else 0,
            "cache_hits": cache_hits,
            "cache_hit_rate": (cache_hits / batch_size * 100) if batch_size > 0 else 0,
            "efficiency_score": self._calculate_efficiency_score(batch_size, duration, True),
            "is_mega_batch": batch_size > 20
        }
        
        self.optimizer.record_performance(metrics)
    
    def _calculate_efficiency_score(self, text_count: int, duration: float, success: bool) -> float:
        """Calculate efficiency score (0-100)"""
        if not success:
            return 0
        
        # Base speed score
        speed = text_count / duration if duration > 0 else 0
        speed_score = min(100, speed * 20)  # 5 texts/sec = 100 points
        
        # Cache bonus
        cache_rate = (self.cache_hits / self.total_requests * 100) if self.total_requests > 0 else 0
        cache_bonus = cache_rate * 0.3
        
        return min(100, speed_score + cache_bonus)

    def translate_manga_page(self, text_bubbles, method="gemini", source_lang="auto", context=None, custom_prompt=None):
        """
        Specialized function for translating an entire manga page efficiently
        
        Args:
            text_bubbles (list): List of text bubble contents
            method (str): Translation method
            source_lang (str): Source language code
            context (dict, optional): Context metadata
            custom_prompt (str, optional): Custom translation prompt
            
        Returns:
            list: List of translated text bubbles
        """
        if not text_bubbles:
            return []
        
        print(f"📖 Translating manga page with {len(text_bubbles)} bubbles")
        
        # Filter out empty bubbles but preserve indices
        non_empty_bubbles = []
        bubble_indices = []
        for i, bubble in enumerate(text_bubbles):
            if bubble and bubble.strip():
                non_empty_bubbles.append(bubble.strip())
                bubble_indices.append(i)
        
        if not non_empty_bubbles:
            return [""] * len(text_bubbles)
        
        # Use batch translation for efficiency
        if method == "gemini" and len(non_empty_bubbles) >= 2:
            translations = self.translate_batch(non_empty_bubbles, method, source_lang, context, custom_prompt)
        else:
            # Fallback to individual translations
            translations = [self.translate(bubble, method, source_lang, context, custom_prompt) for bubble in non_empty_bubbles]
        
        # Map translations back to original bubble positions
        result = [""] * len(text_bubbles)
        for i, translation in enumerate(translations):
            if i < len(bubble_indices):
                result[bubble_indices[i]] = translation
        
        return result

    def translate(self, text, method="google", source_lang="auto", context=None, custom_prompt=None):
        """
        Translate text to Vietnamese using the specified method with context support and caching
        
        Args:
            text (str): Text to translate
            method (str): Translation method ("google", "gemini", "hf", "sogou", "bing")
            source_lang (str): Source language code - "auto", "ja", "zh", "ko", "en"
            context (dict, optional): Context metadata for better translation
            custom_prompt (str, optional): Custom translation style prompt to override defaults
            
        Returns:
            str: Translated text in Vietnamese
        """
        
        # Start performance monitoring
        start_time = time.time() if PERFORMANCE_MONITORING else None
        
        # Update statistics
        self.total_requests += 1
        
        # Early return for empty text
        if not text or not text.strip():
            return ""
        
        # Preprocess text
        processed_text = self._preprocess_text(text)
        text_length = len(processed_text)
        
        # Check cache first ONLY if cache is enabled
        if self.optimizer and self.optimizer.config.get("performance", {}).get("cache_enabled", False):
            cache_key = self._get_cache_key(processed_text, source_lang, context)
            if cache_key in self.translation_cache:
                self.cache_hits += 1
                cached_result = self.translation_cache[cache_key]
                print(f"💾 Cache hit: '{processed_text[:30]}...' -> '{cached_result[:30]}...'")
                
                # Record performance for cache hit
                if PERFORMANCE_MONITORING and start_time:
                    performance_monitor.end_translation_timer(start_time, method, text_length, cache_hit=True)
                
                return cached_result
        else:
            print(f"🔄 Cache disabled - fresh translation for: '{processed_text[:30]}...'")
        
        
        # Validate method and fallback if needed (check availability without counting)
        if method == "gemini" and not (self.api_key_manager.get_active_key(count_usage=False) or self.fallback_api_key):
            print("⚠️ Gemini API not available, falling back to DeepInfra Gemma")
            method = "deepinfra"
        elif method == "gemini" and (self.api_key_manager.get_active_key(count_usage=False) or self.fallback_api_key):
            print("🤖 Using Gemini for context-aware translation")
        
        # Get translator function
        translator_func = self.translators.get(method)
        if not translator_func:
            print(f"❌ Invalid translation method '{method}', using DeepInfra Gemma")
            translator_func = self._translate_with_deepinfra
            method = "deepinfra"

        try:
            # Perform translation
            if method in ["gemini", "deepinfra"]:
                translated = translator_func(processed_text, source_lang, context, custom_prompt)
            else:
                translated = translator_func(processed_text, source_lang)
            
            # Post-process and validate result
            if translated and translated.strip():
                translated = self._post_process_translation(translated, processed_text)
                
                # Store in cache ONLY if enabled
                if self.optimizer and self.optimizer.config.get("performance", {}).get("cache_enabled", False):
                    cache_key = self._get_cache_key(processed_text, source_lang, context)
                    self.translation_cache[cache_key] = translated
                
                # Record performance for successful translation
                if PERFORMANCE_MONITORING and start_time:
                    performance_monitor.end_translation_timer(start_time, method, text_length, cache_hit=False)
                
                return translated
            else:
                print(f"⚠️ Empty translation result for method '{method}', trying fallback")
                # Try NLLB first as it has good translation quality
                if method != "nllb":
                    try:
                        print("🔄 Trying NLLB API as primary fallback...")
                        fallback_result = self._translate_with_nllb(processed_text, source_lang)
                        
                        if fallback_result and fallback_result.strip() and fallback_result != text:
                            fallback_result = self._post_process_translation(fallback_result, processed_text)
                            self.translation_cache[cache_key] = fallback_result
                            
                            # Record performance for NLLB fallback
                            if PERFORMANCE_MONITORING and start_time:
                                performance_monitor.end_translation_timer(start_time, "nllb_fallback", text_length, cache_hit=False)
                            
                            print(f"✅ NLLB fallback successful: '{fallback_result}'")
                            return fallback_result
                            
                    except Exception as e:
                        print(f"❌ NLLB fallback failed: {e}")
                
                # If NLLB also fails, return original text
                print("⚠️ NLLB fallback failed, returning original text")
                return text
                
        except Exception as e:
            print(f"❌ Translation failed with {method}: {e}")
            # Try NLLB first as it has good translation quality
            if method != "nllb":
                try:
                    print("🔄 Trying NLLB API as primary fallback...")
                    fallback_result = self._translate_with_nllb(processed_text, source_lang)
                    
                    if fallback_result and fallback_result.strip() and fallback_result != text:
                        fallback_result = self._post_process_translation(fallback_result, processed_text)
                        self.translation_cache[cache_key] = fallback_result
                        
                        # Record performance for NLLB fallback
                        if PERFORMANCE_MONITORING and start_time:
                            performance_monitor.end_translation_timer(start_time, "nllb_fallback", text_length, cache_hit=False)
                        
                        print(f"✅ NLLB fallback successful: '{fallback_result}'")
                        return fallback_result
                        
                except Exception as e2:
                    print(f"❌ NLLB fallback failed: {e2}")
            
            # If NLLB also fails, return original text
            print("⚠️ NLLB exception fallback failed, returning original text")
            return text

    def _post_process_translation(self, translated, original):
        """Post-process translation for better quality"""
        if not translated:
            return original
        
        # Basic cleanup
        translated = translated.strip()
        
        # Remove duplicate punctuation
        translated = re.sub(r'([.!?])\1+', r'\1', translated)
        
        # Fix common spacing issues
        translated = re.sub(r'\s+', ' ', translated)
        
        # Ensure proper Vietnamese punctuation
        translated = translated.replace('...', '…')
        translated = translated.replace('--', '—')
        
        return translated
    
    def _translate_with_deepinfra(self, text, source_lang="auto", context=None, custom_prompt=None):
        """
        🚀 DEEPINFRA V3.0 - Enhanced AI Translation với Gemma 3-27B 
        Tối ưu hóa prompt và xử lý response cho chất lượng dịch tối đa
        """
        try:
            print("🤖 Using DeepInfra Gemma 3-27B for advanced AI translation...")
            
            # Clean input text
            text = text.strip() if text else ""
            if not text:
                print("⚠️ Empty text sent to DeepInfra, skipping")
                return ""
            
            # 🧠 Intelligent context analysis
            context_analysis = self._analyze_text_context(text, source_lang)
            
            # Build ultra-advanced translation prompt
            if custom_prompt and custom_prompt.strip():
                translation_instruction = custom_prompt.strip()
            else:
                # Parse context với smart defaults
                context_info = ""
                if context:
                    context_parts = []
                    if context.get('is_sfx', False):
                        context_parts.append("🔊 SFX_MODE")
                    if context.get('is_thought', False):
                        context_parts.append("💭 THOUGHT_MODE")
                    if context.get('formality') == 'polite':
                        context_parts.append("🎩 FORMAL_MODE")
                    elif context.get('formality') == 'casual':
                        context_parts.append("😊 CASUAL_MODE")
                    if context.get('emotion'):
                        context_parts.append(f"😃 EMOTION_{context.get('emotion').upper()}")
                    
                    if context_parts:
                        context_info = f" | MODES: {' + '.join(context_parts)}"
                
                # Enhanced language-specific instructions
                lang_instruction = ""
                if source_lang == "ja":
                    lang_instruction = """🎌 JAPANESE→VIETNAMESE EXPERT MODE:
- Keigo detection: です/ます→'ạ/dạ', casual→natural Vietnamese
- Cultural bridge: anime/manga terms to Vietnamese equivalent
- Honorifics: senpai→'tiền bối', sensei→'thầy/sensei'  
- Emotional particles: よ/ね→natural Vietnamese flow"""
                elif source_lang == "zh":
                    lang_instruction = """🏮 CHINESE→VIETNAMESE MASTER MODE:
- Classical terms: 武功→'võ công', 境界→'cảnh giới'
- Hierarchy: 您→'Ngài', 师父→'sư phụ', 前辈→'tiền bối'
- Cultural context: manhua style to Vietnamese comic style"""
                elif source_lang == "ko":
                    lang_instruction = """🇰🇷 KOREAN→VIETNAMESE PRO MODE:
- Honorific system: -요/-습니다→'ạ/dạ', banmal→casual Vietnamese
- Relationships: 형/누나→'anh/chị', 선배→'tiền bối'
- Modern expressions: manhwa/webtoon style adaptation"""
                else:
                    lang_instruction = "🌍 MULTILINGUAL→VIETNAMESE: Smart adaptation to Vietnamese culture and comic style"
                
                # 🎯 MEGA PROMPT V3.0 for DeepInfra
                translation_instruction = f"""🎌 MANGA TRANSLATION SPECIALIST V3.0
Bạn là chuyên gia dịch manga/comic hàng đầu với khả năng AI siêu việt.

🎯 MISSION: Dịch "{text}" sang tiếng Việt hoàn hảo

{lang_instruction}

📋 CONTEXT ANALYSIS: {context_info}
🧠 AI INSIGHTS: {context_analysis}

🔥 TRANSLATION PROTOCOL V3.0:

💎 CHẤT LƯỢNG TUYỆT ĐỐI:
- Chính xác 100% nghĩa gốc, không thêm bớt
- Tự nhiên như người Việt bản địa
- Giữ nguyên cảm xúc và phong cách gốc
- Bubble-friendly: dễ đọc trong speech bubble

🗣️ SMART ADDRESSING SYSTEM:
- Thân thiết: tao/mày, anh/em, mình/cậu  
- Formal: tôi/anh(chị), con/bố(mẹ), em/anh(chị)
- Respectful: đệ tử/sư phụ, nhân/ngài

⚡ SPECIAL HANDLING:
- SFX: Ngắn mạnh, âm thanh Việt ("RẦM!", "BỤP!")
- Thought: Mềm mại, tự nhiên ("...")
- Names: Giữ nguyên tên riêng
- Slang: Việt hóa phù hợp lứa tuổi

🚫 STRICTLY FORBIDDEN:
- Giải thích, ghi chú, phân tích
- Multiple versions/options
- "(tạm dịch)" hay labels
- Thay đổi nghĩa gốc

⚡ OUTPUT: CHỈ BẢN DỊCH HOÀN HẢO DUY NHẤT!"""
            
            # Prepare enhanced API request
            url = "https://eien-g4f.onrender.com/api/DeepInfra/chat/completions"
            
            payload = {
                "model": "google/gemma-3-27b-it",  # Latest Gemma model
                "messages": [
                    {
                        "role": "system", 
                        "content": "Bạn là siêu chuyên gia dịch thuật manga/comic với AI intelligence cực cao. Khả năng dịch của bạn ngang ngửa các dịch giả chuyên nghiệp hàng đầu. Luôn trả về bản dịch hoàn hảo nhất."
                    },
                    {
                        "role": "user", 
                        "content": translation_instruction
                    }
                ],
                "temperature": 0.1,  # Lower for more consistent results
                "max_tokens": min(300, len(text) * 4),  # Dynamic token calculation
                "top_p": 0.85,  # Optimized for quality
                "repetition_penalty": 1.1,  # Avoid repetition
                "do_sample": True
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "MangaTranslator/3.0"
            }
            
            # Send request với intelligent retry
            for attempt in range(3):  # Up to 3 attempts
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=25)
                    break
                except requests.Timeout:
                    if attempt < 2:
                        wait_time = (attempt + 1) * 2  # Progressive wait
                        print(f"⏰ DeepInfra timeout, retrying in {wait_time}s... (attempt {attempt + 1}/3)")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise
            
            # Enhanced response processing
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Extract assistant response với error handling
                    if "choices" in data and len(data["choices"]) > 0:
                        choice = data["choices"][0]
                        
                        # Handle different response formats
                        if "message" in choice and "content" in choice["message"]:
                            assistant_msg = choice["message"]["content"]
                        elif "text" in choice:
                            assistant_msg = choice["text"]
                        else:
                            print("❌ Unexpected DeepInfra response format")
                            return self._translate_with_nllb(text, source_lang)
                        
                        # Enhanced cleaning với AI intelligence
                        translated_text = self._clean_deepinfra_response_v3(assistant_msg, text)
                        
                        if translated_text and translated_text.strip():
                            print(f"✅ DeepInfra Gemma success: '{translated_text}'")
                            return translated_text
                        else:
                            print("⚠️ Empty DeepInfra result after advanced cleaning")
                            return self._translate_with_nllb(text, source_lang)
                    else:
                        print("❌ No choices in DeepInfra response")
                        return self._translate_with_nllb(text, source_lang)
                        
                except json.JSONDecodeError as e:
                    print(f"❌ DeepInfra JSON decode error: {e}")
                    return self._translate_with_nllb(text, source_lang)
            else:
                print(f"❌ DeepInfra API error: {response.status_code}")
                if response.text:
                    print(f"Error details: {response.text[:200]}...")
                return self._translate_with_nllb(text, source_lang)
                
        except Exception as e:
            print(f"❌ DeepInfra translation failed: {e}")
            # Intelligent fallback to NLLB
            return self._translate_with_nllb(text, source_lang)

    def _clean_deepinfra_response_v3(self, response, original_text):
        """
        🔧 ENHANCED RESPONSE CLEANING V3.0
        Advanced AI response cleaning với pattern recognition
        """
        if not response:
            return ""
        
        # Initial cleanup
        cleaned = response.strip()
        
        # Remove common AI prefixes (extended list)
        ai_prefixes = [
            "Bản dịch:", "Dịch:", "Translation:", "Vietnamese:", "Tiếng Việt:",
            "Câu dịch:", "Kết quả:", "Đáp án:", "Bản dịch tiếng Việt:",
            "Vietnamese translation:", "Trả lời:", "Câu trả lời:", "Nội dung:",
            "Output:", "Result:", "Answer:", "Response:", "Translated:",
            "Here's the translation:", "The translation is:", "Dịch thuật:",
            "🎌", "⚡", "💎", "CHỈ BẢN DỊCH:", "OUTPUT:"
        ]
        
        for prefix in ai_prefixes:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove surrounding quotes intelligently
        quote_pairs = [('"', '"'), ("'", "'"), ('`', '`'), ('"', '"'), (''', ''')]
        for start_quote, end_quote in quote_pairs:
            if cleaned.startswith(start_quote) and cleaned.endswith(end_quote):
                cleaned = cleaned[1:-1].strip()
        
        # Split by explanation markers and take best part
        explanation_markers = [
            "\n\n", "Giải thích:", "Lưu ý:", "Chú thích:", "Note:",
            "Hoặc có thể", "Tùy ngữ cảnh", "Alternatively", "Or:",
            "* ", "• ", "- ", "[", "(Lưu ý", "(Giải thích", "(Note",
            "Có thể dịch", "Another option", "Phiên bản khác"
        ]
        
        best_part = cleaned
        for marker in explanation_markers:
            if marker in cleaned:
                parts = cleaned.split(marker)
                if parts[0].strip() and len(parts[0].strip()) >= 3:
                    best_part = parts[0].strip()
                    break
        
        # Advanced pattern cleaning
        # Remove markdown formatting
        best_part = re.sub(r'\*\*(.*?)\*\*', r'\1', best_part)  # **text** -> text
        best_part = re.sub(r'\*(.*?)\*', r'\1', best_part)      # *text* -> text
        
        # Remove line numbers and bullets
        best_part = re.sub(r'^[\d\.\)\-\*\•]\s*', '', best_part)
        
        # Clean extra whitespace and normalize
        best_part = " ".join(best_part.split())
        
        # Quality check: ensure it's not just repeating original
        if best_part.lower() == original_text.lower():
            return ""
        
        # Length sanity check
        if len(best_part) > len(original_text) * 5:  # Too long, probably includes explanation
            sentences = best_part.split('.')
            if sentences and len(sentences[0]) <= len(original_text) * 3:
                best_part = sentences[0].strip()
        
        # Final cleanup
        best_part = best_part.rstrip('.,!?;:')
        
        return best_part

    def _clean_deepinfra_response(self, response):
        """Clean DeepInfra response to extract only translation"""
        if not response:
            return ""
        
        # Remove common prefixes and explanations
        cleaned = response.strip()
        
        # Remove translation labels
        prefixes_to_remove = [
            "Bản dịch:", "Dịch:", "Translation:", "Vietnamese:",
            "Tiếng Việt:", "Câu dịch:", "Kết quả:", "Đáp án:",
            "Bản dịch tiếng Việt:", "Vietnamese translation:",
            "Trả lời:", "Câu trả lời:", "Nội dung:",
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Remove quotes if the entire response is quoted
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1].strip()
        elif cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1].strip()
        
        # Split by explanations and take first part
        explanation_markers = [
            "\n\n", "Giải thích:", "Lưu ý:", "Chú thích:",
            "Hoặc có thể", "Tùy ngữ cảnh", "* ", "• ",
            "[", "(Lưu ý", "(Giải thích"
        ]
        
        for marker in explanation_markers:
            if marker in cleaned:
                parts = cleaned.split(marker)
                if parts[0].strip():
                    cleaned = parts[0].strip()
                    break
        
        # Clean extra whitespace
        cleaned = " ".join(cleaned.split())
        
        return cleaned.rstrip('.,!?;:')

    def _translate_with_nllb(self, text, source_lang="auto"):
        """NLLB API translator as high-quality fallback"""
        try:
            print("🔄 Using NLLB API as fallback...")
            
            # Map language codes to NLLB format
            source_code = self.nllb_language_map.get(source_lang, "eng_Latn")
            target_code = self.nllb_language_map.get("vi", "vie_Latn")
            
            # Prepare API request
            import urllib.parse
            encoded_text = urllib.parse.quote(text)
            
            url = f"https://winstxnhdw-nllb-api.hf.space/api/v4/translator"
            params = {
                "text": text,
                "source": source_code,
                "target": target_code
            }
            
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse NLLB API response format: {"result": "translated_text"}
                if isinstance(result, dict):
                    if "result" in result:
                        translated = result["result"]
                    elif "text" in result:
                        translated = result["text"]
                    else:
                        # Fallback: try to get first string value
                        translated = next((v for v in result.values() if isinstance(v, str)), None)
                elif isinstance(result, str):
                    translated = result
                else:
                    translated = str(result).strip('"')
                
                if translated and translated.strip() and translated != text:
                    print(f"✅ NLLB translation successful: '{translated}'")
                    return translated.strip()
                else:
                    print("⚠️ NLLB returned empty or same text")
                    return text
            else:
                print(f"❌ NLLB API error: {response.status_code}")
                return text
                
        except Exception as e:
            print(f"❌ NLLB API failed: {e}")
            return text

    def _translate_with_gemini(self, text, source_lang="auto", context=None, custom_prompt=None):
        """
        Optimized Gemini translation with improved error handling and smart prompting.
        
        Args:
            text (str): Text to translate or list of texts for batch processing
            source_lang (str): Source language
            context (dict, optional): Context metadata
            custom_prompt (str, optional): Custom prompt override
        """
        # Get API key from manager (COUNT USAGE - thực sự dùng API)
        current_api_key = self.api_key_manager.get_active_key(count_usage=True)
        if not current_api_key and not self.fallback_api_key:
            raise ValueError("Không có Gemini API key khả dụng - vui lòng cấu hình api_keys.json")
        
        # Use fallback if no key from manager
        if not current_api_key:
            current_api_key = self.fallback_api_key
        
        # Handle batch translation
        if isinstance(text, list):
            return self._translate_batch_with_gemini(text, source_lang, context, custom_prompt, current_api_key)
        
        # Clean input text
        text = text.strip() if text else ""
        if not text:
            print("⚠️ Empty text sent to Gemini, skipping")
            return ""
        
        # Smart prompt selection based on text complexity
        if self._is_simple_text(text):
            prompt = self._get_simple_translation_prompt(text, source_lang, context)
        else:
            prompt = self._get_translation_prompt(text, source_lang, context, custom_prompt)
            
        # Debug logging
        print(f"🤖 Gemini input: '{text}' | Lang: {source_lang}")
        if context:
            print(f"📋 Context: {context}")
            
        try:
            # Use REST API with optimized configuration
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': current_api_key
            }
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,  # Rất thấp để tăng tính nhất quán
                    "maxOutputTokens": min(100, max(20, len(text) * 2)),  # Giới hạn chặt output
                    "topP": 0.7,
                    "topK": 20,
                    "stopSequences": [
                        "\n\n", "Giải thích:", "Lưu ý:", "Translation:", "Note:"
                    ]
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
            }
            
            # Add timeout and retry logic
            for attempt in range(2):  # Maximum 2 attempts
                try:
                    response = requests.post(url, headers=headers, json=data, timeout=15)
                    break
                except requests.Timeout:
                    if attempt == 0:
                        print("⏰ Gemini request timeout, retrying...")
                        time.sleep(1)
                        continue
                    else:
                        raise
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    
                    # Check if response was blocked
                    if candidate.get('finishReason') == 'SAFETY':
                        print("⚠️ Gemini response blocked by safety filters, using fallback")
                        return self._translate_with_google(text, source_lang)
                    
                    translated_text = candidate['content']['parts'][0]['text'].strip()
                    
                    # Enhanced cleanup - remove any AI explanations
                    translated_text = self._clean_gemini_response(translated_text)
                    
                    if translated_text:
                        print(f"✅ Gemini translation: '{translated_text}'")
                        return translated_text
                    else:
                        print("⚠️ Empty Gemini result after cleaning")
                        return self._translate_with_google(text, source_lang)
                else:
                    print("❌ No translation candidates in Gemini response")
                    return self._translate_with_google(text, source_lang)
            else:
                error_msg = response.text if response.text else "Unknown error"
                print(f"❌ Gemini API error: {response.status_code} - {error_msg}")
                
                # Đánh dấu key bị lỗi nếu không phải fallback key
                if current_api_key != self.fallback_api_key:
                    self.api_key_manager.mark_key_failed(current_api_key)
                
                return self._translate_with_google(text, source_lang)
            
        except Exception as e:
            print(f"❌ Gemini translation failed: {e}")
            
            # Đánh dấu key bị lỗi nếu không phải fallback key
            if current_api_key != self.fallback_api_key:
                self.api_key_manager.mark_key_failed(current_api_key)
            
            # Fallback to Google Translate
            return self._translate_with_google(text, source_lang)
    
    def _translate_batch_with_gemini(self, texts, source_lang="auto", context=None, custom_prompt=None, api_key=None):
        """
        Batch translate multiple texts with Gemini in a single API call.
        Reduces API requests and improves performance.
        
        Args:
            texts (list): List of texts to translate
            source_lang (str): Source language
            context (dict, optional): Context metadata
            custom_prompt (str, optional): Custom prompt override
            api_key (str, optional): API key to use (from manager)
            
        Returns:
            list: List of translated texts
        """
        if not texts:
            return []
        
        # Use provided API key or get from manager (COUNT USAGE khi thực sự dùng)
        current_api_key = api_key if api_key else self.api_key_manager.get_active_key(count_usage=True)
        if not current_api_key and not self.fallback_api_key:
            print("❌ Không có API key khả dụng cho batch translation")
            return texts  # Return original texts as fallback
            
        if not current_api_key:
            current_api_key = self.fallback_api_key
        
        # Filter empty texts and track indices
        non_empty_texts = []
        text_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text.strip())
                text_indices.append(i)
        
        if not non_empty_texts:
            return [""] * len(texts)
        
        print(f"🚀 Gemini batch translation: {len(non_empty_texts)} texts")
        
        # Create batch prompt
        batch_prompt = self._get_batch_translation_prompt(non_empty_texts, source_lang, context, custom_prompt)
        
        try:
            # Use REST API with optimized configuration for batch
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': current_api_key
            }
            
            # Estimate output tokens needed for batch
            total_input_chars = sum(len(text) for text in non_empty_texts)
            max_output_tokens = min(2048, total_input_chars * 3 + 200)  # Buffer for batch overhead
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": batch_prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": max_output_tokens,
                    "topP": 0.8,
                    "topK": 30,
                    "stopSequences": [
                        "\n\n---", "Giải thích:", "TUYỆT VỜI!", "DƯỚI ĐÂY LÀ", "BẢN DỊCH"
                    ]
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_NONE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_NONE"
                    }
                ]
            }
            
            # Send request with timeout
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    
                    # Check if response was blocked
                    if candidate.get('finishReason') == 'SAFETY':
                        print("⚠️ Gemini batch response blocked by safety filters, using fallback")
                        return [self._translate_with_google(text, source_lang) for text in texts]
                    
                    batch_response = candidate['content']['parts'][0]['text'].strip()
                    
                    # Parse batch response
                    translated_texts = self._parse_batch_response(batch_response, len(non_empty_texts))
                    
                    if len(translated_texts) == len(non_empty_texts):
                        # Map back to original list with empties
                        result_list = [""] * len(texts)
                        for i, trans_text in enumerate(translated_texts):
                            result_list[text_indices[i]] = trans_text
                        
                        print(f"✅ Gemini batch completed: {len(translated_texts)} translations")
                        return result_list
                    else:
                        print(f"⚠️ Batch response count mismatch: expected {len(non_empty_texts)}, got {len(translated_texts)}")
                        # Fallback to individual translations
                        return [self._translate_with_google(text, source_lang) for text in texts]
                else:
                    print("❌ No translation candidates in Gemini batch response")
                    return [self._translate_with_google(text, source_lang) for text in texts]
            else:
                error_msg = response.text if response.text else "Unknown error"
                print(f"❌ Gemini batch API error: {response.status_code} - {error_msg}")
                
                # Đánh dấu key bị lỗi nếu không phải fallback key
                if current_api_key != self.fallback_api_key:
                    self.api_key_manager.mark_key_failed(current_api_key)
                
                return [self._translate_with_google(text, source_lang) for text in texts]
                
        except Exception as e:
            print(f"❌ Gemini batch translation failed: {e}")
            
            # Đánh dấu key bị lỗi nếu không phải fallback key
            if current_api_key != self.fallback_api_key:
                self.api_key_manager.mark_key_failed(current_api_key)
            
            # Fallback to individual Google translations
            return [self._translate_with_google(text, source_lang) for text in texts]

    def _get_simple_translation_prompt(self, text, source_lang, context=None):
        """Generate simplified prompt for simple/short texts"""
        
        # For very short text, use minimal prompt
        if len(text) <= 10:
            return f'Dịch "{text}" sang tiếng Việt. Chỉ trả về bản dịch:'
        
        # Build basic context
        context_info = []
        if context:
            if context.get('is_sfx', False):
                context_info.append("âm thanh")
            if context.get('is_thought', False):
                context_info.append("suy nghĩ")
            if context.get('formality') == 'polite':
                context_info.append("lịch sự")
        
        context_str = " (" + ", ".join(context_info) + ")" if context_info else ""
        
        return f'Dịch "{text}" sang tiếng Việt{context_str}. Trả về bản dịch ngắn gọn:'

    def _get_batch_translation_prompt(self, texts, source_lang, context=None, custom_prompt=None):
        """
        🚀 SIÊU BATCH PROMPT V3.0 - Xử lý hàng loạt thông minh
        Được tối ưu cho việc dịch nhiều text cùng lúc với chất lượng cao
        """
        text_count = len(texts)
        
        # Parse context metadata với intelligent defaults
        if context:
            gender = context.get('gender', 'neutral')
            relationship = context.get('relationship', 'neutral')  
            formality = context.get('formality', 'casual')
            is_thought = context.get('is_thought', False)
            is_sfx = context.get('is_sfx', False)
            is_mega_batch = context.get('is_mega_batch', False)
            total_images = context.get('total_images', 1)
            emotion = context.get('emotion', 'neutral')
            scene_context = context.get('scene_context', '')
        else:
            gender = relationship = emotion = 'neutral'
            formality = 'casual'
            is_thought = is_sfx = is_mega_batch = False
            total_images = 1
            scene_context = ''
        
        # 🧠 Phân tích batch context
        batch_analysis = self._analyze_batch_context(texts, source_lang)
        
        # Build enhanced context info
        context_info = []
        if gender != 'neutral':
            context_info.append(f"GIỚI TÍNH: {gender}")
        if relationship != 'neutral':
            context_info.append(f"MỐI QUAN HỆ: {relationship}")
        if formality != 'casual':
            context_info.append(f"THỂ LOẠI: {formality}")
        if emotion != 'neutral':
            context_info.append(f"CẢM XÚC: {emotion}")
        if is_thought:
            context_info.append("LOẠI: suy_nghĩ_nội_tâm")
        if is_sfx:
            context_info.append("LOẠI: hiệu_ứng_âm_thanh")
        if scene_context:
            context_info.append(f"BỐI CẢNH: {scene_context}")
        if is_mega_batch:
            context_info.append(f"MEGA_BATCH: {total_images} trang, {text_count} texts")
        if batch_analysis:
            context_info.append(f"AI_PHÂN_TÍCH: {batch_analysis}")
            
        context_str = " | ".join(context_info) if context_info else "Batch chuẩn"
        
        # Get enhanced language rules
        lang_rules = self._get_enhanced_language_rules(source_lang)
        
        # Create numbered list với smart formatting
        text_list = ""
        for i, text in enumerate(texts, 1):
            # Làm sạch text để hiển thị tốt hơn
            clean_text = text.strip().replace('\n', ' ')
            text_list += f"{i}. {clean_text}\n"
        
        # Intelligent mega batch handling
        if is_mega_batch and text_count > 20:
            mega_instructions = f"""MEGA BATCH ({text_count} texts từ {total_images} trang): Giữ nhất quán tên nhân vật, xưng hô và phong cách dịch."""
        else:
            mega_instructions = f"""BATCH ({text_count} texts): Dịch chất lượng cao, nhất quán."""
        
        # Custom prompt override với enhancements
        if custom_prompt and custom_prompt.strip():
            return f"""Dịch manga sang tiếng Việt. {mega_instructions}

Custom: {custom_prompt.strip()}
Context: {context_str}

{lang_rules}

Texts:
{text_list}

TRẢ VỀ: {text_count} dòng dịch tiếng Việt thuần."""

        # Standard tối ưu batch prompt
        return f"""Dịch manga sang tiếng Việt. Context: {context_str}

{lang_rules}

QUY TẮC:
- Dịch chính xác, tự nhiên như người Việt nói
- Xưng hô phù hợp với mối quan hệ
- SFX: ngắn gọn, mạnh mẽ (VD: "RẦM!", "BOOM!")
- Giữ nhất quán trong toàn bộ batch
- CHỈ trả về bản dịch, không giải thích

Texts cần dịch:
{text_list}

TRẢ VỀ: {text_count} dòng dịch tiếng Việt, mỗi dòng 1 bản dịch hoàn chỉnh."""

    def _parse_batch_response(self, response, expected_count):
        """
        Enhanced parsing for mega batch responses with better accuracy
        """
        if not response or not response.strip():
            return [""] * expected_count
        
        # Clean response from unwanted prefixes first
        cleaned_response = response.strip()
        
        # Remove problematic prefixes that AI sometimes adds
        unwanted_prefixes = [
            "TUYỆT VỜI! DƯỚI ĐÂY LÀ BẢN DỊCH",
            "ĐOẠN TEXT SANG TIẾNG VIỆT, GIỮ NHẤT QUÁN TÊN NHÂN VẬT, XLING HÔ VÀ PHONG CÁCH DICH:",
            "BẢN DỊCH", "ĐOẠN TEXT", "SANG TIẾNG VIỆT",
            "DƯỚI ĐÂY LÀ", "TUYỆT VỜI!", "NHẤT QUÁN",
            "TÊN NHÂN VẬT", "XLING HÔ", "PHONG CÁCH",
            "DICH:", "Bản dịch:", "Dịch:"
        ]
        
        for prefix in unwanted_prefixes:
            if cleaned_response.upper().startswith(prefix.upper()):
                cleaned_response = cleaned_response[len(prefix):].strip()
        
        # Remove any remaining header text before numbered items
        lines = cleaned_response.split('\n')
        start_idx = 0
        for i, line in enumerate(lines):
            if re.match(r'^\d+\.\s*', line.strip()):
                start_idx = i
                break
        
        if start_idx > 0:
            cleaned_response = '\n'.join(lines[start_idx:])
        
        # Split by lines and clean
        lines = []
        for line in cleaned_response.strip().split('\n'):
            line = line.strip()
            
            # Skip empty lines and separator lines
            if not line or line.startswith('---') or line.startswith('==='):
                continue
                
            # Remove numbering if present (1. 2. etc)
            line = re.sub(r'^\d+\.\s*', '', line)
            # Remove markdown formatting
            line = re.sub(r'^\*\*|\*\*$', '', line)
            # Remove quotes if present
            line = line.strip('"').strip("'").strip('`')
            
            # Skip meta content and unwanted phrases
            skip_words = [
                'giải thích', 'lưu ý', 'hoặc', 'phân tích', 'context',
                'tuyệt vời', 'dưới đây', 'bản dịch', 'đoạn text',
                'sang tiếng việt', 'nhất quán', 'tên nhân vật',
                'xling hô', 'phong cách', 'dich:'
            ]
            if any(skip_word in line.lower() for skip_word in skip_words):
                continue
                
            if line:  # Only add non-empty lines
                lines.append(line)
        
        # Enhanced logging for mega batch
        if expected_count > 20:  # Mega batch
            print(f"🔍 MEGA BATCH parsing: extracted {len(lines)} from {expected_count} expected")
        
        # If we have exactly the expected count, return as is
        if len(lines) == expected_count:
            return lines
        
        # If we have more lines, take the first expected_count
        if len(lines) > expected_count:
            print(f"⚠️ Got {len(lines)} lines, taking first {expected_count}")
            return lines[:expected_count]
        
        # If we have fewer lines, try alternative parsing
        if len(lines) < expected_count:
            print(f"⚠️ Got {len(lines)} lines, expected {expected_count}")
            
            # Try alternative splitting by common separators
            alternative_lines = []
            for separator in ['\n\n', '。\n', '！\n', '？\n']:
                parts = response.split(separator)
                if len(parts) >= expected_count:
                    alternative_lines = [p.strip() for p in parts if p.strip()][:expected_count]
                    break
            
            if len(alternative_lines) == expected_count:
                print(f"✅ Alternative parsing succeeded: {len(alternative_lines)} lines")
                return alternative_lines
            
            # Final fallback: pad with empty strings
            print(f"🔧 Padding {expected_count - len(lines)} missing lines")
            while len(lines) < expected_count:
                lines.append("")
            return lines
        
        return lines

    def _get_translation_prompt(self, text, source_lang, context=None, custom_prompt=None):
        """
        🔥 SIÊU TỐI ƯU PROMPT V3.0 - Intelligent Context-Aware Translation System
        """
        # If custom prompt provided, enhance it with our framework
        if custom_prompt and custom_prompt.strip():
            base_prompt = custom_prompt.strip()
        else:
            base_prompt = "Dịch manga/comic sang tiếng Việt tự nhiên, chuẩn xác và giữ nguyên tinh thần gốc."
        
        # Parse context metadata with smart defaults
        gender = context.get('gender', 'neutral') if context else 'neutral'
        relationship = context.get('relationship', 'neutral') if context else 'neutral'  
        formality = context.get('formality', 'casual') if context else 'casual'
        bubble_limit = context.get('bubble_limit', None) if context else None
        is_thought = context.get('is_thought', False) if context else False
        is_sfx = context.get('is_sfx', False) if context else False
        scene_context = context.get('scene_context', '') if context else ''
        character_emotion = context.get('emotion', 'neutral') if context else 'neutral'
        
        # 🧠 INTELLIGENT CONTEXT ANALYSIS
        context_analysis = self._analyze_text_context(text, source_lang)
        
        # Build enhanced context info with AI insights
        context_info = []
        if gender != 'neutral':
            context_info.append(f"GIỚI TÍNH: {gender}")
        if relationship != 'neutral':
            context_info.append(f"MỐI QUAN HỆ: {relationship}")
        if formality != 'casual':
            context_info.append(f"THỂ LOẠI: {formality}")
        if bubble_limit:
            context_info.append(f"GIỚI HẠN BUBBLE: {bubble_limit} ký tự")
        if is_thought:
            context_info.append("LOẠI: suy_nghĩ_nội_tâm")
        if is_sfx:
            context_info.append("LOẠI: hiệu_ứng_âm_thanh")
        if scene_context:
            context_info.append(f"BỐI CẢNH: {scene_context}")
        if character_emotion != 'neutral':
            context_info.append(f"CẢM XÚC: {character_emotion}")
        if context_analysis:
            context_info.append(f"AI_PHÂN_TÍCH: {context_analysis}")
            
        context_str = " | ".join(context_info) if context_info else "Ngữ cảnh chuẩn"
        
        # Get enhanced language-specific rules
        lang_rules = self._get_enhanced_language_rules(source_lang)
        
        # 🎯 PROMPT TỐI ƯU V4.0 - Đảm bảo output sạch 100%
        return f"""Bạn là chuyên gia dịch manga chuyên nghiệp. Dịch "{text}" sang tiếng Việt.

NGỮ CẢNH: {context_str}

{lang_rules}

QUY TẮC DỊCH:
- Dịch chính xác 100% nghĩa gốc
- Tự nhiên như người Việt nói
- Giữ nguyên cảm xúc và phong cách
- SFX: dịch ngắn gọn và mạnh mẽ (VD: "RẦM!", "BOOM!")
- Xưng hô phù hợp: tao/mày (thân), anh/em (lịch sự), tôi/bạn (trung tính)

TUYỆT ĐỐI CẤM:
- Giải thích, ghi chú, phân tích
- Trả về nhiều phiên bản
- Thêm nhãn như "(tạm dịch)"

CHỈ TRẢ VỀ: Bản dịch tiếng Việt duy nhất, không có gì khác."""
    def _analyze_text_context(self, text, source_lang):
        """
        🧠 PHÂN TÍCH NGỮ CẢNH THÔNG MINH - AI Context Analysis
        Tự động nhận diện đặc điểm của text để dịch chính xác hơn
        """
        if not text or len(text.strip()) < 2:
            return ""
        
        analysis_parts = []
        text_lower = text.lower()
        
        # 🎭 Phân tích cảm xúc
        emotions = {
            "vui_vẻ": ["笑", "happy", "기쁘", "うれし", "嬉しい", "楽しい", "ハハ", "호호", "haha"],
            "tức_giận": ["怒", "angry", "화나", "むかつく", "腹立", "クソ", "畜生", "젠장", "damn"],
            "buồn": ["悲", "sad", "슬프", "悲しい", "泣", "crying", "우는", "眠れ"],
            "ngạc_nhiên": ["驚", "surprise", "놀라", "びっくり", "えっ", "まさか", "헉", "어?"],
            "sợ": ["怖", "scared", "무서", "恐ろしい", "こわい", "怖い", "무서워", "scary"]
        }
        
        for emotion, keywords in emotions.items():
            if any(keyword in text for keyword in keywords):
                analysis_parts.append(f"cảm_xúc_{emotion}")
                break
        
        # 🗣️ Phân tích kiểu lời nói
        speech_patterns = {
            "thốt_ra": ["!", "！", "っ", "…", "어?", "えっ", "哎"],
            "nghiêm_túc": ["。", "だ", "である", "습니다", "입니다"],
            "thân_mật": ["よ", "ね", "じゃん", "야", "어", "呢", "哦"],
            "kêu_gọi": ["さあ", "よし", "가자", "来", "Come"]
        }
        
        for pattern, markers in speech_patterns.items():
            if any(marker in text for marker in markers):
                analysis_parts.append(f"phong_cách_{pattern}")
                break
        
        # 🎌 Phân tích đặc trưng ngôn ngữ
        if source_lang == "ja":
            if any(keigo in text for keigo in ["です", "ます", "である", "ございます"]):
                analysis_parts.append("keigo_formal")
            if any(casual in text for casual in ["だよ", "だね", "じゃん", "っす"]):
                analysis_parts.append("casual_japanese")
        
        elif source_lang == "ko":
            if any(formal in text for formal in ["습니다", "시다", "하십시오"]):
                analysis_parts.append("korean_formal")
            if any(casual in text for casual in ["야", "어", "지", "다고"]):
                analysis_parts.append("korean_casual")
        
        # 💭 Phân tích loại nội dung
        content_types = {
            "hành_động": ["戦", "戦う", "戦闘", "战斗", "싸우", "fight", "battle"],
            "lãng_mạn": ["愛", "love", "사랑", "恋", "좋아해", "好き"],
            "hài_hước": ["笑", "funny", "웃긴", "面白い", "おかしい"],
            "bí_ẩn": ["謎", "mystery", "신비", "不思議", "strange"]
        }
        
        for content_type, keywords in content_types.items():
            if any(keyword in text for keyword in keywords):
                analysis_parts.append(f"thể_loại_{content_type}")
                break
        
        # 🔊 Phân tích âm thanh/hiệu ứng
        sfx_patterns = [
            "ドン", "バン", "キラキラ", "ドキドキ",  # Japanese SFX
            "轰", "砰", "咔嚓", "嘭",              # Chinese SFX  
            "쾅", "쿵", "휘익", "따르르",           # Korean SFX
            "BANG", "BOOM", "CRASH", "POP"        # English SFX
        ]
        
        if any(sfx in text for sfx in sfx_patterns):
            analysis_parts.append("âm_thanh_hiệu_ứng")
        
        # 📏 Phân tích độ dài và phức tạp
        if len(text) > 50:
            analysis_parts.append("text_dài")
        elif len(text) < 10:
            analysis_parts.append("text_ngắn")
        
        return ", ".join(analysis_parts) if analysis_parts else "neutral"

    def _get_enhanced_language_rules(self, source_lang):
        """
        🔥 QUY TẮC NGÔN NGỮ SIÊU TỐI ƯU V3.0
        Rules được cải tiến dựa trên nghiên cứu ngôn ngữ học và kinh nghiệm thực tế
        """
        if source_lang == "ja":
            return """JAPANESE:
- です/ます → "ạ/dạ" (lịch sự), だ/である → bình thường
- SFX: バン→"BÙNG!", ドン→"RẦM!", キラキラ→"lấp lánh", ドキドキ→"thình thịch"
- やばい→"Chết tiệt!", すごい→"Tuyệt!", 大丈夫→"Không sao", 頑張って→"Cố lên!"
- Onii-chan→"anh trai", Sensei→"thầy/cô" """

        elif source_lang == "zh":
            return """CHINESE:
- 您→"Ngài", 师父→"sư phụ", 前辈→"tiền bối"
- Võlâm: 武功→"võ công", 内功→"nội công", 修炼→"tu luyện"
- SFX: 轰→"BÙMM!", 砰→"ĐỤC!", 咔嚓→"KẮC!"
- 走吧→"Đi thôi!", 没事→"Không sao", 加油→"Cố lên!" """

        elif source_lang == "ko":
            return """KOREAN:
- -요/-습니다 → "ạ/dạ" (lịch sự), Banmal → bình thường  
- 형/누나/오빠/언니 → "anh/chị", 선배/후배 → "tiền bối/hậu bối"
- SFX: 쾅→"CẠCH!", 쿵→"RẦM!", 휘익→"VỪN!", 두근두근→"thình thịch"
- 아이고→"Ôi giời!", 진짜→"Thật sự à?", 화이팅→"Cố lên!" """

        else:
            return """GENERAL:
- Xưng hô phù hợp với formality và relationship
- SFX: âm mạnh→"BOOM!/BANG!", âm nhẹ→"lách tách/xào xạc"
- Giữ tính cách nhân vật qua lời nói """

    def _clean_gemini_response(self, response):
        """Enhanced cleaning to remove any AI explanations and return only translation"""
        if not response:
            return ""
            
        # Remove quotes and common prefixes
        cleaned = response.strip().strip('"').strip("'")
        
        # Remove translation labels and prefixes
        prefixes_to_remove = [
            "Bản dịch:", "Dịch:", "Translation:", "Vietnamese:",
            "Tiếng Việt:", "Câu dịch:", "Kết quả:", "Đáp án:",
            "Bản dịch tiếng Việt:", "Vietnamese translation:",
            "Tôi sẽ dịch:", "Đây là bản dịch:", "Câu trả lời:",
            "Dịch thuật:", "Kết quả dịch:", "Phiên bản:",
            "CHỈ TRẢ VỀ:", "OUTPUT:", "Đáp án dịch:",
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Split by explanations and take first clean part
        explanation_splits = [
            "\n\n", "\n-", "\n*", "\n•", " (giải thích", " (lưu ý",
            " (", "[", "Hoặc", "Tùy", "Nếu", "* ", "• ",
            "- ", "Giải thích:", "Lưu ý:", "Chú thích:",
            "Có thể", "Tuỳ theo", "Tùy vào", "Ý nghĩa:",
            "Phiên bản khác:", "Cách khác:", "Hoặc có thể:",
            "\nGiải", "\nLưu", "\nChú", "\nHoặc"
        ]
        
        for split_pattern in explanation_splits:
            if split_pattern in cleaned:
                parts = cleaned.split(split_pattern, 1)
                if parts[0].strip():
                    cleaned = parts[0].strip()
                    break
        
        # Remove markdown formatting
        cleaned = cleaned.replace("**", "").replace("*", "")
        
        # Clean extra whitespace and newlines
        cleaned = " ".join(cleaned.split())
        
        # Extract core translation if contains AI patterns
        ai_patterns = [
            "có thể dịch", "tùy ngữ cảnh", "tuỳ theo", "hoặc là",
            "một cách khác", "phiên bản khác", "cách khác", "nghĩa là",
            "tức là", "hay là", "hoặc dịch", "có nghĩa"
        ]
        
        for pattern in ai_patterns:
            if pattern in cleaned.lower():
                # Extract the first sentence before the pattern
                sentences = cleaned.split('.')
                if sentences and len(sentences[0]) > 3:
                    cleaned = sentences[0].strip()
                    break
        
        # Remove trailing punctuation if excessive
        cleaned = cleaned.rstrip('.,!?;:')
        
        # Final check: if still contains problematic patterns, extract quoted text
        if any(bad in cleaned.lower() for bad in ["dịch là", "nghĩa gốc", "có thể hiểu"]):
            # Look for quoted content
            quotes = ['"', "'", """, """, "'", "'"]
            for quote in quotes:
                if quote in cleaned:
                    parts = cleaned.split(quote)
                    if len(parts) >= 3 and len(parts[1]) > 2:
                        cleaned = parts[1].strip()
                        break
        
        return cleaned

    def _analyze_batch_context(self, texts, source_lang):
        """
        🔍 PHÂN TÍCH BATCH CONTEXT - Intelligent Batch Analysis
        Phân tích tổng thể các text trong batch để dịch nhất quán
        """
        if not texts or len(texts) == 0:
            return ""
        
        analysis_parts = []
        
        # 📊 Thống kê batch
        total_chars = sum(len(text) for text in texts)
        avg_length = total_chars / len(texts)
        
        if avg_length > 30:
            analysis_parts.append("text_dài_trung_bình")
        elif avg_length < 10:
            analysis_parts.append("text_ngắn_trung_bình")
        
        # 🎭 Phân tích cảm xúc chung
        emotion_counts = {"positive": 0, "negative": 0, "neutral": 0}
        
        positive_indicators = ["笑", "楽しい", "기쁘", "happy", "좋", "好", "嬉しい", "开心"]
        negative_indicators = ["怒", "悲", "angry", "sad", "화나", "哭", "泣", "무서"]
        
        for text in texts:
            if any(pos in text for pos in positive_indicators):
                emotion_counts["positive"] += 1
            elif any(neg in text for neg in negative_indicators):
                emotion_counts["negative"] += 1
            else:
                emotion_counts["neutral"] += 1
        
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        if emotion_counts[dominant_emotion] > len(texts) * 0.3:  # 30% threshold
            analysis_parts.append(f"cảm_xúc_chủ_đạo_{dominant_emotion}")
        
        # 🗣️ Phân tích formality patterns
        formal_count = 0
        casual_count = 0
        
        formal_patterns = ["です", "ます", "습니다", "시다", "您", "です"]
        casual_patterns = ["だよ", "じゃん", "야", "어", "呢", "哦"]
        
        for text in texts:
            if any(formal in text for formal in formal_patterns):
                formal_count += 1
            elif any(casual in text for casual in casual_patterns):
                casual_count += 1
        
        if formal_count > casual_count and formal_count > len(texts) * 0.3:
            analysis_parts.append("formality_formal_dominant")
        elif casual_count > formal_count and casual_count > len(texts) * 0.3:
            analysis_parts.append("formality_casual_dominant")
        
        # 💥 Phân tích SFX density
        sfx_count = 0
        sfx_patterns = ["ドン", "バン", "轰", "砰", "쾅", "쿵", "BANG", "BOOM"]
        
        for text in texts:
            if any(sfx in text for sfx in sfx_patterns):
                sfx_count += 1
        
        if sfx_count > len(texts) * 0.2:  # 20% có SFX
            analysis_parts.append("batch_nhiều_sfx")
        
        # 📚 Phân tích thể loại content
        action_keywords = ["戦", "戰", "싸우", "fight", "battle", "attack"]
        romance_keywords = ["愛", "love", "사랑", "恋", "kiss", "heart"]
        comedy_keywords = ["笑", "funny", "웃긴", "面白い", "joke"]
        
        action_count = sum(1 for text in texts if any(keyword in text for keyword in action_keywords))
        romance_count = sum(1 for text in texts if any(keyword in text for keyword in romance_keywords))
        comedy_count = sum(1 for text in texts if any(keyword in text for keyword in comedy_keywords))
        
        if action_count > len(texts) * 0.25:
            analysis_parts.append("thể_loại_hành_động")
        if romance_count > len(texts) * 0.25:
            analysis_parts.append("thể_loại_lãng_mạn")
        if comedy_count > len(texts) * 0.25:
            analysis_parts.append("thể_loại_hài_hước")
        
        # 🧠 Character interaction patterns
        dialogue_indicators = ["!", "?", "…", "。", "！", "？"]
        dialogue_count = sum(1 for text in texts if any(indicator in text for indicator in dialogue_indicators))
        
        if dialogue_count > len(texts) * 0.7:  # 70% có dấu hiệu hội thoại
            analysis_parts.append("chủ_yếu_hội_thoại")
        elif dialogue_count < len(texts) * 0.3:  # <30% hội thoại
            analysis_parts.append("chủ_yếu_narration")
        
        return ", ".join(analysis_parts) if analysis_parts else "batch_neutral"

    def _preprocess_text(self, text):
        """Enhanced preprocessing for different comic types"""
        if not text:
            return ""
        
        # Basic cleaning
        preprocessed_text = text.replace("．", ".")
        
        # Remove excessive whitespace
        preprocessed_text = " ".join(preprocessed_text.split())
        
        # Clean up common OCR artifacts
        preprocessed_text = preprocessed_text.replace("（", "(").replace("）", ")")
        preprocessed_text = preprocessed_text.replace("！", "!").replace("？", "?")
        preprocessed_text = preprocessed_text.replace("。", ".")
        
        # Fix common OCR errors
        preprocessed_text = preprocessed_text.replace("0", "O")  # Common OCR mistake
        preprocessed_text = preprocessed_text.replace("|", "I")  # Vertical line to I
        
        # Remove extra symbols that might confuse translators
        preprocessed_text = re.sub(r'[•▪▫■□●○◆◇★☆]', '', preprocessed_text)
        
        return preprocessed_text.strip()

    def _delay(self):
        """Smart delay to avoid rate limiting"""
        # Shorter delay to improve performance
        delay_time = random.uniform(0.5, 1.5)  # Reduced from 3-5 seconds
        time.sleep(delay_time)
