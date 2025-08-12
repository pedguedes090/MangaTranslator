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
- Multiple translation backends (Google, Gemini AI, HuggingFace, Sogou, Bing)
- Context-aware translation with relationship/formality/gender metadata
- Language-specific prompts (Japanese manga, Chinese manhua, Korean manhwa)
- Clean output guarantee (no AI explanations or multiple options)
- Automatic language detection
- Error handling and fallbacks

Author: MangaTranslator Team  
License: MIT
Version: 2.0 (Enhanced Prompt System)
"""

# Translation libraries
from deep_translator import GoogleTranslator
from transformers import pipeline
import translators as ts

# Standard library imports
import requests
import random
import time
import os
import json


class MangaTranslator:
    """
    Multi-service translator optimized for manga/comic text translation with context awareness.
    
    🆕 NEW: Context metadata support for intelligent translation:
    - Smart pronoun/honorific selection based on relationship and formality
    - Gender-aware translation for natural Vietnamese output  
    - Bubble fitting with character limits
    - SFX and internal thought specialized handling
    - Clean output guarantee (no AI explanations)
    """
    
    def __init__(self, gemini_api_key=None):
        """
        Initialize the translator with optional Gemini API key
        
        Args:
            gemini_api_key (str, optional): Gemini API key for AI translation
        """
        self.target = "vi"  # Target language: Vietnamese
        
        # Supported source languages mapping
        self.supported_languages = {
            "auto": "Tự động nhận diện",
            "ja": "Tiếng Nhật (Manga)",
            "zh": "Tiếng Trung (Manhua)", 
            "ko": "Tiếng Hàn (Manhwa)",
            "en": "Tiếng Anh"
        }
        
        # Initialize Gemini API key
        if not gemini_api_key:
            gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        if gemini_api_key and gemini_api_key.strip():
            self.gemini_api_key = gemini_api_key.strip()
            print(f"✅ Gemini 2.0 Flash API key configured: {self.gemini_api_key[:10]}...")
        else:
            self.gemini_api_key = None
            print("⚠️ No Gemini API key provided")
            
        # Translation methods mapping
        self.translators = {
            "google": self._translate_with_google,
            "hf": self._translate_with_hf,
            "sogou": self._translate_with_sogou,
            "bing": self._translate_with_bing,
            "gemini": self._translate_with_gemini
        }

        # Supported genres for specialized prompts
        self.supported_genres = {
            "auto": "Tự động",
            "action": "Hành động",
            "romance": "Tình cảm",
            "comedy": "Hài hước",
            "horror": "Kinh dị",
            "wuxia": "Kiếm hiệp",
            "xianxia": "Tiên hiệp",
            "fantasy_game": "Game giả tưởng"
        }

    def translate(self, text, method="google", source_lang="auto", context=None, genre="auto"):
        """
        Translate text to Vietnamese using the specified method with context support
        
        Args:
            text (str): Text to translate
            method (str): Translation method ("google", "gemini", "hf", "sogou", "bing")
            source_lang (str): Source language code - "auto", "ja", "zh", "ko", "en"
            context (dict, optional): Context metadata for better translation:
                - gender: 'male'/'female'/'neutral' (default: 'neutral')
                - relationship: 'friend'/'senior'/'junior'/'family'/'stranger' (default: 'neutral')
                - formality: 'casual'/'polite'/'formal' (default: 'casual')
                - bubble_limit: int (character limit for bubble fitting)
                - is_thought: bool (internal monologue/thought bubble)
                - is_sfx: bool (sound effect)
                - scene_context: str (brief scene description)
            genre (str): Story genre for specialized prompts (default: "auto")
            
        Returns:
            str: Translated text in Vietnamese
        """
        
        if method == "gemini" and not self.gemini_api_key:
            print("⚠️ Gemini 2.0 Flash API not available, falling back to Google Translate")
            method = "google"
        elif method == "gemini" and self.gemini_api_key:
            print("🤖 Using Gemini 2.0 Flash for context-aware translation")
            
        translator_func = self.translators.get(method)

        if translator_func:
            if method == "gemini":
                return translator_func(self._preprocess_text(text), source_lang, context, genre)
            else:
                return translator_func(self._preprocess_text(text), source_lang)
        else:
            raise ValueError("Invalid translation method.")
            
    def _translate_with_google(self, text, source_lang="auto"):
        self._delay()
        
        # Map our language codes to Google's codes
        google_lang = source_lang
        if source_lang == "zh":
            google_lang = "zh-cn"
        
        translator = GoogleTranslator(source=google_lang, target=self.target)
        translated_text = translator.translate(text)
        return translated_text if translated_text is not None else text

    def _translate_with_hf(self, text, source_lang="auto"):
        # HF pipeline chỉ hỗ trợ Japanese to English, fallback to Google
        print("⚠️ Helsinki-NLP chỉ hỗ trợ Nhật → Anh, chuyển sang Google Translate")
        return self._translate_with_google(text, source_lang)

    def _translate_with_sogou(self, text, source_lang="auto"):
        self._delay()
        
        # Map to sogou language codes
        sogou_lang = "auto" if source_lang == "auto" else source_lang
        
        translated_text = ts.translate_text(text, translator="sogou",
                                            from_language=sogou_lang,
                                            to_language=self.target)
        return translated_text if translated_text is not None else text

    def _translate_with_bing(self, text, source_lang="auto"):
        self._delay()
        
        # Map to bing language codes  
        bing_lang = "auto" if source_lang == "auto" else source_lang
        
        translated_text = ts.translate_text(text, translator="bing",
                                            from_language=bing_lang, 
                                            to_language=self.target)
        return translated_text if translated_text is not None else text

    def _translate_with_gemini(self, text, source_lang="auto", context=None, genre="auto"):
        """
        Translate using Google Gemini 2.0 Flash with context metadata support.
        
        Args:
            text (str): Text to translate
            source_lang (str): Source language
            context (dict, optional): Context metadata with keys:
                - gender: 'male'/'female'/'neutral'
                - relationship: 'friend'/'senior'/'junior'/'family'/'stranger'
                - formality: 'casual'/'polite'/'formal'
                - bubble_limit: int (character limit)
                - is_thought: bool (internal monologue)
                - is_sfx: bool (sound effect)
                - scene_context: str (brief scene description)
            genre (str): Story genre for specialized prompts
        """
        if not self.gemini_api_key:
            raise ValueError("Gemini API key not configured")
        
        # Clean input text
        text = text.strip() if text else ""
        if not text:
            print("⚠️ Empty text sent to Gemini, skipping")
            return ""
            
        # Debug logging
        print(f"🤖 Gemini input: '{text}' | Lang: {source_lang}")
        if context:
            print(f"📋 Context: {context}")
            
        try:
            # Use REST API directly for more reliable connection
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            
            headers = {
                'Content-Type': 'application/json',
                'X-goog-api-key': self.gemini_api_key
            }
            
            # Get specialized prompt based on source language, context and genre
            prompt = self._get_translation_prompt(text, source_lang, context, genre)
            
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
                    "temperature": 0.3,
                    "maxOutputTokens": 200,
                    "topP": 0.9,
                    "topK": 40
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    translated_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    
                    # Aggressive cleanup - remove any AI explanations
                    translated_text = self._clean_gemini_response(translated_text)
                    
                    return translated_text if translated_text else text
                else:
                    print("❌ No translation candidates in response")
                    return self._translate_with_google(text, source_lang)
            else:
                print(f"❌ Gemini API error: {response.status_code} - {response.text}")
                return self._translate_with_google(text, source_lang)
            
        except Exception as e:
            print(f"Gemini translation failed: {e}")
            # Fallback to Google Translate
            return self._translate_with_google(text, source_lang)

    def _get_translation_prompt(self, text, source_lang, context=None, genre="auto"):
        """
        Generate enhanced translation prompt with context metadata and genre support
        """
        # Parse context metadata
        gender = context.get('gender', 'neutral') if context else 'neutral'
        relationship = context.get('relationship', 'neutral') if context else 'neutral'  
        formality = context.get('formality', 'casual') if context else 'casual'
        bubble_limit = context.get('bubble_limit', None) if context else None
        is_thought = context.get('is_thought', False) if context else False
        is_sfx = context.get('is_sfx', False) if context else False
        scene_context = context.get('scene_context', '') if context else ''
        
        # Build context info
        context_info = []
        if gender != 'neutral':
            context_info.append(f"GENDER: {gender}")
        if relationship != 'neutral':
            context_info.append(f"RELATIONSHIP: {relationship}")
        if formality != 'casual':
            context_info.append(f"FORMALITY: {formality}")
        if bubble_limit:
            context_info.append(f"BUBBLE_LIMIT: {bubble_limit} chars")
        if is_thought:
            context_info.append("TYPE: internal_thought")
        if is_sfx:
            context_info.append("TYPE: sound_effect")
        if scene_context:
            context_info.append(f"SCENE: {scene_context}")
            
        context_str = " | ".join(context_info) if context_info else "No specific context"
        
        # Get language-specific rules
        lang_rules = self._get_language_rules(source_lang)
        genre_rules = self._get_genre_rules(genre)

        genre_section = f"\nGENRE RULES:\n{genre_rules}\n" if genre_rules else ""

        return f"""Dịch "{text}" sang tiếng Việt.

CONTEXT: {context_str}

{lang_rules}{genre_section}
GLOBAL RULES:
- Chỉ trả về chuỗi bản dịch, không nhãn, không ngoặc kép, không giải thích
- Một dòng vào → một dòng ra (bảo toàn số dòng)
- Xưng hô tự động theo relationship/formality: bạn bè→"tôi/cậu"; lịch sự→"tôi/anh(chị)"; thân mật→"tao/mày"
- Không sáng tác thêm, dịch trung thực nhưng mượt
- Tên riêng/ký hiệu: giữ nguyên
- Dấu câu Việt: "…" cho thở dài, "—" cho ngắt mạnh
- SFX: dịch ngắn mạnh (vd: "RẦM!", "BỤP!")
- Thought: dùng "…" mềm, tránh đại từ nặng
- Bubble fit: ưu tiên câu ngắn tự nhiên

CHỈ TRẢ VỀ BẢN DỊCH:"""
    def _get_language_rules(self, source_lang):
        """Get language-specific translation rules"""
        if source_lang == "ja":
            return """JA RULES:
- Keigo→"ạ/dạ"; thường→bỏ kính ngữ
- Senpai/kouhai→"tiền bối/hậu bối" hoặc giữ nguyên
- やばい→"Chết tiệt!/Tệ rồi!"; すごい→"Đỉnh quá!"  
- 技→"kỹ thuật/chiêu"; 必殺技→"tuyệt kỹ"; 変身→"biến hình"
- SFX: バン→"BÙNG!"; ドン→"RẦM!"; キラキラ→"lấp lánh" """

        elif source_lang == "zh":
            return """ZH RULES:
- 您→"Ngài/thưa"; 你→"anh/chị"; 朕→"Trẫm"; 本王→"Bản vương"
- 武功→"võ công"; 轻功→"khinh công"; 江湖→"giang hồ"
- 境界→"cảnh giới"; 丹药→"đan dược"; 法宝→"pháp bảo"  
- 哼→"Hừ!"; 哎呀→"Ôi trời!"; 天啊→"Trời ơi!"
- SFX: 轰→"BÙMM!"; 砰→"ĐỤC!"; 咔嚓→"KẮC!" """

        elif source_lang == "ko":
            return """KO RULES:
- Jondaetmal→"ạ/dạ"; banmal→bỏ kính ngữ
- 형/누나/오빠/언니→"anh/chị"; 선배→"tiền bối" 
- 아이고→"Ôi giời!"; 헐→"Hả?!"; 와→"Wow!"
- 능력→"năng lực"; 각성→"thức tỉnh"; 레벨업→"lên cấp"
- SFX: 쾅→"CẠCH!"; 쿵→"RẦM!"; 휘익→"VỪN!" """

        else:
            return """GENERAL RULES:
- Phân biệt formal/informal, nam/nữ, già/trẻ
- Cảm thán: "Ồ!", "Trời!", "Chết tiệt!"
- Hiệu ứng âm thanh: dịch phù hợp tiếng Việt"""

    def _get_genre_rules(self, genre):
        """Return genre-specific prompt rules"""
        genre_prompts = {
            "action": "- Tông giọng mạnh mẽ, nhịp độ nhanh, dùng động từ dứt khoát",
            "romance": "- Dùng lời lẽ nhẹ nhàng, tình cảm, giàu cảm xúc",
            "comedy": "- Giữ tính hài hước, sử dụng từ ngữ dí dỏm, đời thường",
            "horror": "- Giữ không khí căng thẳng, u ám, từ ngữ gợi sự rùng rợn",
            "wuxia": "- Phong cách giang hồ cổ trang, thuật ngữ võ hiệp, khí phách anh hùng",
            "xianxia": "- Ngôn ngữ tu tiên huyền ảo, dùng từ linh lực, phi thăng, tiên giới",
            "fantasy_game": "- Phong cách game giả tưởng, dùng từ level, kỹ năng, guild, boss",
        }
        return genre_prompts.get(genre, "")

    def _clean_gemini_response(self, response):
        """Enhanced cleaning to remove any AI explanations and return only translation"""
        if not response:
            return ""
            
        # Remove quotes and common prefixes
        cleaned = response.strip().strip('"').strip("'")
        
        # Remove translation labels
        prefixes_to_remove = [
            "Bản dịch:", "Dịch:", "Translation:", "Vietnamese:",
            "Tiếng Việt:", "Câu dịch:", "Kết quả:", "Đáp án:",
            "Bản dịch tiếng Việt:", "Vietnamese translation:",
            "Tôi sẽ dịch:", "Đây là bản dịch:", "Câu trả lời:",
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
        
        # Split by common explanation indicators and take first part
        explanation_splits = [
            " (", "[", "Hoặc", "Tùy", "Nếu", "* ", "• ",
            "- ", "Giải thích:", "Lưu ý:", "Chú thích:",
            "Có thể", "Tuỳ theo", "Tùy vào"
        ]
        
        for split_pattern in explanation_splits:
            if split_pattern in cleaned:
                parts = cleaned.split(split_pattern)
                if parts[0].strip():
                    cleaned = parts[0].strip()
                    break
        
        # Clean extra whitespace and newlines
        cleaned = " ".join(cleaned.split())
        
        # Final validation - if it contains typical AI response patterns, extract the core translation
        ai_patterns = [
            "có thể dịch", "tùy ngữ cảnh", "tuỳ theo", "hoặc là",
            "một cách khác", "phiên bản khác", "cách khác"
        ]
        
        for pattern in ai_patterns:
            if pattern in cleaned.lower():
                # Try to extract the first clean sentence before the pattern
                sentences = cleaned.split('.')
                if sentences and len(sentences[0]) > 3:
                    cleaned = sentences[0].strip()
                    break
                    
        return cleaned.rstrip('.,!?;:')

    def _preprocess_text(self, text):
        """Enhanced preprocessing for different comic types"""
        # Basic cleaning
        preprocessed_text = text.replace("．", ".")
        
        # Remove excessive whitespace
        preprocessed_text = " ".join(preprocessed_text.split())
        
        # Clean up common OCR artifacts
        preprocessed_text = preprocessed_text.replace("（", "(").replace("）", ")")
        preprocessed_text = preprocessed_text.replace("！", "!").replace("？", "?")
        
        return preprocessed_text

    def _delay(self):
        time.sleep(random.randint(3, 5))
