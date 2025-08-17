# -*- coding: utf-8 -*-
"""
API Key Manager - Quản lý nhiều GEMINI_API_KEY để tối ưu sử dụng
Hỗ trợ rotation, load balancing và error handling
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import threading

class APIKeyManager:
    """
    Quản lý nhiều GEMINI_API_KEY với các tính năng:
    - Round robin rotation
    - Load balancing
    - Error handling và auto failover
    - Daily usage tracking
    - Key health monitoring
    """
    
    def __init__(self, config_file="api_keys.json"):
        """
        Khởi tạo APIKeyManager
        
        Args:
            config_file (str): Đường dẫn đến file config JSON
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.current_key_index = 0
        self.lock = threading.Lock()
        self.failed_keys = set()  # Track failed keys
        self.last_reset_date = datetime.now().date()
        
        # Auto-reset daily usage nếu enabled
        if self.config.get("reset_daily_usage", True):
            self._reset_daily_usage_if_needed()
    
    def _load_config(self) -> Dict:
        """Load config từ file JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"⚠️ Config file {self.config_file} không tồn tại, tạo file mặc định")
                return self._create_default_config()
        except Exception as e:
            print(f"❌ Lỗi load config: {e}")
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict:
        """Tạo config mặc định"""
        default_config = {
            "gemini_api_keys": [
                {
                    "key": os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"),
                    "name": "Default Key",
                    "usage_count": 0,
                    "last_used": None,
                    "daily_limit": 1000,
                    "is_active": True
                }
            ],
            "rotation_strategy": "round_robin",
            "auto_switch_on_error": True,
            "reset_daily_usage": True
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Lỗi tạo config file: {e}")
        
        return default_config
    
    def _save_config(self):
        """Lưu config vào file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Lỗi lưu config: {e}")
    
    def _reset_daily_usage_if_needed(self):
        """Reset daily usage nếu qua ngày mới"""
        current_date = datetime.now().date()
        if current_date > self.last_reset_date:
            print(f"🔄 Reset daily usage cho ngày mới: {current_date}")
            for key_info in self.config["gemini_api_keys"]:
                key_info["usage_count"] = 0
            self.last_reset_date = current_date
            self.failed_keys.clear()  # Reset failed keys
            self._save_config()
    
    def get_active_key(self, count_usage=True) -> Optional[str]:
        """
        Lấy API key hiện tại theo strategy
        
        Args:
            count_usage (bool): Có tính usage hay không (mặc định True)
        
        Returns:
            str: API key hoặc None nếu không có key khả dụng
        """
        with self.lock:
            self._reset_daily_usage_if_needed()
            
            available_keys = [
                (i, key_info) for i, key_info in enumerate(self.config["gemini_api_keys"])
                if (key_info.get("is_active", True) and 
                    key_info["usage_count"] < key_info.get("daily_limit", 1000) and
                    i not in self.failed_keys and
                    key_info["key"] not in ["YOUR_GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_1", 
                                          "YOUR_GEMINI_API_KEY_2", "YOUR_GEMINI_API_KEY_3"])
            ]
            
            if not available_keys:
                print("❌ Không có API key khả dụng!")
                return None
            
            strategy = self.config.get("rotation_strategy", "round_robin")
            
            if strategy == "round_robin":
                # Round robin: chuyển đổi tuần tự
                key_index = self.current_key_index % len(available_keys)
                selected_index, selected_key = available_keys[key_index]
                self.current_key_index = (self.current_key_index + 1) % len(available_keys)
                
            elif strategy == "least_used":
                # Chọn key ít sử dụng nhất
                selected_index, selected_key = min(available_keys, 
                                                 key=lambda x: x[1]["usage_count"])
            
            elif strategy == "random":
                # Random selection
                import random
                selected_index, selected_key = random.choice(available_keys)
            
            else:
                # Default: first available
                selected_index, selected_key = available_keys[0]
            
            # Only update usage if explicitly requested (when actually using API)
            if count_usage:
                selected_key["usage_count"] += 1
                selected_key["last_used"] = datetime.now().isoformat()
                
                print(f"🔑 Sử dụng API key: {selected_key['name']} "
                      f"(Usage: {selected_key['usage_count']}/{selected_key.get('daily_limit', 1000)})")
                
                self._save_config()
            else:
                print(f"🔍 Kiểm tra API key: {selected_key['name']} "
                      f"(Usage: {selected_key['usage_count']}/{selected_key.get('daily_limit', 1000)})")
            
            return selected_key["key"]
    
    def has_available_key(self) -> bool:
        """
        Kiểm tra xem có API key khả dụng hay không (không count usage)
        
        Returns:
            bool: True nếu có key khả dụng
        """
        return self.get_active_key(count_usage=False) is not None
    
    def mark_key_failed(self, api_key: str):
        """
        Đánh dấu API key bị lỗi để tạm thời không sử dụng
        
        Args:
            api_key (str): API key bị lỗi
        """
        with self.lock:
            for i, key_info in enumerate(self.config["gemini_api_keys"]):
                if key_info["key"] == api_key:
                    self.failed_keys.add(i)
                    print(f"⚠️ Đánh dấu API key {key_info['name']} bị lỗi, tạm thời không sử dụng")
                    break
    
    def reset_failed_keys(self):
        """Reset danh sách key bị lỗi"""
        with self.lock:
            self.failed_keys.clear()
            print("🔄 Reset danh sách API key bị lỗi")
    
    def get_key_status(self) -> List[Dict]:
        """
        Lấy trạng thái của tất cả API key
        
        Returns:
            List[Dict]: Danh sách trạng thái các key
        """
        status_list = []
        for i, key_info in enumerate(self.config["gemini_api_keys"]):
            status = {
                "name": key_info["name"],
                "key_preview": key_info["key"][:10] + "..." if len(key_info["key"]) > 10 else key_info["key"],
                "usage_count": key_info["usage_count"],
                "daily_limit": key_info.get("daily_limit", 1000),
                "is_active": key_info.get("is_active", True),
                "last_used": key_info.get("last_used"),
                "is_failed": i in self.failed_keys,
                "usage_percentage": (key_info["usage_count"] / key_info.get("daily_limit", 1000)) * 100
            }
            status_list.append(status)
        
        return status_list
    
    def add_api_key(self, key: str, name: str, daily_limit: int = 1000):
        """
        Thêm API key mới
        
        Args:
            key (str): API key
            name (str): Tên mô tả
            daily_limit (int): Giới hạn sử dụng hàng ngày
        """
        new_key = {
            "key": key,
            "name": name,
            "usage_count": 0,
            "last_used": None,
            "daily_limit": daily_limit,
            "is_active": True
        }
        
        self.config["gemini_api_keys"].append(new_key)
        self._save_config()
        print(f"✅ Đã thêm API key: {name}")
    
    def remove_api_key(self, key_name: str):
        """
        Xóa API key theo tên
        
        Args:
            key_name (str): Tên của key cần xóa
        """
        original_count = len(self.config["gemini_api_keys"])
        self.config["gemini_api_keys"] = [
            key_info for key_info in self.config["gemini_api_keys"]
            if key_info["name"] != key_name
        ]
        
        if len(self.config["gemini_api_keys"]) < original_count:
            self._save_config()
            print(f"✅ Đã xóa API key: {key_name}")
        else:
            print(f"⚠️ Không tìm thấy API key: {key_name}")
    
    def toggle_key_status(self, key_name: str):
        """
        Bật/tắt trạng thái của API key
        
        Args:
            key_name (str): Tên của key
        """
        for key_info in self.config["gemini_api_keys"]:
            if key_info["name"] == key_name:
                key_info["is_active"] = not key_info.get("is_active", True)
                self._save_config()
                status = "kích hoạt" if key_info["is_active"] else "tắt"
                print(f"✅ Đã {status} API key: {key_name}")
                return
        
        print(f"⚠️ Không tìm thấy API key: {key_name}")
