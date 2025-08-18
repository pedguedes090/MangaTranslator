#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example: Cách sử dụng API Key Health Check trong code

Ví dụ này cho thấy cách tích hợp health check vào workflow thực tế
"""

from api_key_manager import APIKeyManager
from translator import Translator
import time

def example_basic_health_check():
    """Ví dụ cơ bản: kiểm tra health của API keys"""
    print("=" * 50)
    print("📋 EXAMPLE 1: Basic Health Check")
    print("=" * 50)
    
    # Khởi tạo manager
    api_manager = APIKeyManager()
    
    # Kiểm tra key đầu tiên
    first_key = api_manager.config["gemini_api_keys"][0]["key"]
    print(f"🔍 Testing first key: {first_key[:10]}...")
    
    is_healthy = api_manager.test_api_key_health(first_key)
    print(f"Result: {'✅ Healthy' if is_healthy else '❌ Failed'}")

def example_comprehensive_check():
    """Ví dụ: kiểm tra toàn diện tất cả keys"""
    print("\n" + "=" * 50) 
    print("📋 EXAMPLE 2: Comprehensive Check")
    print("=" * 50)
    
    api_manager = APIKeyManager()
    
    print("🔍 Testing all API keys...")
    health_results = api_manager.test_all_keys_health()
    
    print(f"\n📊 Summary:")
    for key_name, is_healthy in health_results.items():
        status = "✅ Active" if is_healthy else "❌ Failed"
        print(f"   {key_name}: {status}")

def example_translation_with_health_check():
    """Ví dụ: sử dụng translator với health check"""
    print("\n" + "=" * 50)
    print("📋 EXAMPLE 3: Translation with Health Check") 
    print("=" * 50)
    
    # Khởi tạo translator (tự động có API manager)
    translator = Translator()
    
    # Kiểm tra có key khả dụng không
    if not translator.api_key_manager.has_available_key():
        print("❌ Không có API key nào khả dụng!")
        return
    
    print("✅ Có API key khả dụng, thử dịch...")
    
    # Test translation
    test_text = "Hello, world!"
    try:
        result = translator.translate(test_text, method="gemini")
        print(f"Input: {test_text}")
        print(f"Output: {result}")
    except Exception as e:
        print(f"❌ Translation failed: {e}")

def example_recovery_workflow():
    """Ví dụ: quy trình khôi phục key bị lỗi"""
    print("\n" + "=" * 50)
    print("📋 EXAMPLE 4: Recovery Workflow")
    print("=" * 50)
    
    api_manager = APIKeyManager()
    
    # Hiển thị failed keys hiện tại
    if api_manager.failed_keys:
        print(f"⚠️ Có {len(api_manager.failed_keys)} key(s) bị đánh dấu lỗi")
        print("🔄 Thử khôi phục...")
        api_manager.auto_test_failed_keys()
    else:
        print("✅ Không có key nào bị đánh dấu lỗi")

def example_monitoring_loop():
    """Ví dụ: monitoring loop với health check định kỳ"""
    print("\n" + "=" * 50)
    print("📋 EXAMPLE 5: Monitoring Loop")
    print("=" * 50)
    
    api_manager = APIKeyManager()
    
    print("🔄 Chạy monitoring loop (3 lần, mỗi 5 giây)...")
    
    for i in range(3):
        print(f"\n--- Round {i+1} ---")
        
        # Kiểm tra trạng thái
        status_list = api_manager.get_key_status()
        active_count = sum(1 for s in status_list if s["is_active"])
        total_count = len(status_list)
        
        print(f"📊 Status: {active_count}/{total_count} keys active")
        
        # Nếu có failed keys, thử recovery
        if api_manager.failed_keys:
            print("🔁 Trying to recover failed keys...")
            api_manager.auto_test_failed_keys()
        
        if i < 2:  # Không sleep ở lần cuối
            print("⏳ Waiting 5 seconds...")
            time.sleep(5)

def example_integration_pattern():
    """Ví dụ: pattern tích hợp health check vào ứng dụng"""
    print("\n" + "=" * 50)
    print("📋 EXAMPLE 6: Integration Pattern")
    print("=" * 50)
    
    # Pattern 1: Startup health check
    print("🚀 Startup Health Check Pattern:")
    api_manager = APIKeyManager()
    
    # Kiểm tra nhanh có key nào khả dụng không
    if api_manager.has_available_key():
        print("✅ Ready to translate")
    else:
        print("❌ No API keys available - running full health check...")
        api_manager.test_all_keys_health()
    
    # Pattern 2: Error handling với health check
    print("\n🛠️ Error Handling Pattern:")
    translator = Translator()
    
    def smart_translate(text):
        """Smart translation với health check khi lỗi"""
        try:
            return translator.translate(text, method="gemini")
        except Exception as e:
            print(f"⚠️ Translation failed: {e}")
            print("🔍 Running health check...")
            
            # Test failed keys để xem có key nào recover được không
            translator.api_key_manager.auto_test_failed_keys()
            
            # Thử lại một lần
            try:
                return translator.translate(text, method="gemini")
            except Exception as e2:
                print(f"❌ Still failed after health check: {e2}")
                return None
    
    # Test pattern
    result = smart_translate("Test translation")
    if result:
        print(f"✅ Smart translation succeeded: {result}")
    else:
        print("❌ Smart translation failed")

def main():
    """Chạy tất cả examples"""
    print("🎯 API KEY HEALTH CHECK EXAMPLES")
    print("=" * 60)
    
    try:
        example_basic_health_check()
        example_comprehensive_check()
        example_translation_with_health_check()
        example_recovery_workflow()
        example_monitoring_loop()
        example_integration_pattern()
        
        print("\n" + "=" * 60)
        print("✅ Tất cả examples đã chạy xong!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️ Dừng bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")

if __name__ == "__main__":
    main()
