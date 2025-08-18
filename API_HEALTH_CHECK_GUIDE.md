# API Key Health Check - Hướng Dẫn Sử Dụng

## 🎯 Tổng Quan

Hệ thống **API Key Health Check** đã được tích hợp vào MangaTranslator để tự động kiểm tra tình trạng hoạt động của các Gemini API keys. Điều này giúp:

- ✅ Phát hiện sớm các API key bị lỗi, hết hạn hoặc vượt quota
- 🔄 Tự động đánh dấu key không hoạt động để tránh sử dụng
- 🛡️ Cải thiện độ tin cậy của hệ thống dịch thuật
- 📊 Theo dõi trạng thái real-time của tất cả API keys

## 🆕 Chức Năng Mới

### 1. Test Single API Key
```python
# Kiểm tra một API key cụ thể
api_manager = APIKeyManager()
is_healthy = api_manager.test_api_key_health("YOUR_API_KEY")
print(f"API Key status: {'✅ Active' if is_healthy else '❌ Failed'}")
```

### 2. Test All API Keys
```python
# Kiểm tra tất cả API keys và cập nhật trạng thái
health_results = api_manager.test_all_keys_health()
```

### 3. Auto Recovery Test
```python
# Tự động kiểm tra lại các key đã bị đánh dấu lỗi
api_manager.auto_test_failed_keys()
```

## 🖥️ Giao Diện Người Dùng

Trong tab **"🔑 Quản Lý API Key"**, có 4 nút mới:

| Nút | Chức Năng | Mô Tả |
|-----|-----------|--------|
| 🔄 **Refresh** | Cập nhật hiển thị | Refresh trạng thái hiện tại |
| ♻️ **Reset Failed** | Reset đánh dấu lỗi | Xóa tất cả đánh dấu key lỗi |
| 🔍 **Test All Keys** | Kiểm tra tất cả | Test hoạt động của tất cả API keys |
| 🔁 **Test Failed Keys** | Test key lỗi | Kiểm tra lại các key đã bị đánh dấu lỗi |

## 🔧 Cách Hoạt Động

### Test Request
Hệ thống gửi một request nhỏ đến Gemini API:
```json
{
  "contents": [{"parts": [{"text": "Translate this word to Vietnamese: 'Hello'"}]}],
  "generationConfig": {
    "temperature": 0.1,
    "maxOutputTokens": 10,  // Tiết kiệm quota
    "topP": 0.7,
    "topK": 5
  }
}
```

### Response Codes
- **200** ✅ API key hoạt động bình thường
- **401** ❌ API key không hợp lệ hoặc hết hạn  
- **403** ❌ API key bị từ chối quyền truy cập
- **429** ❌ API key vượt quota hoặc rate limit

### Auto-Update Status
Sau khi test, hệ thống tự động:
1. Cập nhật `is_active: false` cho các key lỗi
2. Thêm vào `failed_keys` set để tạm thời không sử dụng
3. Lưu trạng thái vào `api_keys.json`

## 📊 Trạng Thái Hiển Thị

```
✅ Primary Key: AIzaSyDWFk... (105/1000)     // Key hoạt động
❌ Secondary Key: AIzaSyCJ1l... (14/1000) ⚠️  // Key lỗi + cảnh báo
```

**Ý nghĩa các biểu tượng:**
- ✅ Key hoạt động bình thường
- ❌ Key bị lỗi hoặc không hoạt động  
- ⚠️ Key đã bị đánh dấu failed (tạm thời không dùng)
- `(105/1000)` Usage count / Daily limit

## 🔄 Quy Trình Tự Động

### 1. Khi Khởi Động
- Hệ thống tự động kiểm tra API key đầu tiên
- Nếu có key khả dụng → hiển thị "Multi-API key system đã sẵn sàng"

### 2. Khi Translation Lỗi  
- Tự động đánh dấu key bị lỗi: `api_manager.mark_key_failed(api_key)`
- Chuyển sang key khác trong rotation
- Key lỗi sẽ không được sử dụng cho đến khi được test lại

### 3. Reset Hàng Ngày
- Usage count reset về 0 vào ngày mới
- Failed keys được clear tự động
- Tất cả key được phép sử dụng lại

## 💡 Tips Sử Dụng

### Test Định Kỳ
```bash
# Chạy script test độc lập
python test_api_health.py
```

### Monitoring
- Kiểm tra trạng thái trong UI thường xuyên
- Sử dụng "Test All Keys" sau khi thêm key mới
- "Test Failed Keys" để khôi phục key đã lỗi

### Troubleshooting
1. **Key bị 403**: Kiểm tra permissions trong Google Cloud Console
2. **Key bị 429**: Đợi reset quota hoặc upgrade billing
3. **Key bị timeout**: Kiểm tra kết nối internet

## 🛠️ Development Notes

### Code Structure
```
api_key_manager.py
├── test_api_key_health()      # Test single key
├── test_all_keys_health()     # Test all keys  
└── auto_test_failed_keys()    # Recovery test

app.py  
├── test_all_api_keys()        # UI handler for test all
└── test_failed_api_keys()     # UI handler for recovery
```

### Error Handling
- Timeout protection (10s)
- Connection error handling  
- Rate limiting between requests (0.5s delay)
- Graceful fallback to Google Translate when all keys fail

---

## 🎉 Kết Luận

Hệ thống API Key Health Check giúp:
- 🛡️ **Tăng độ tin cậy**: Tự động phát hiện và xử lý key lỗi
- ⚡ **Cải thiện hiệu suất**: Tránh request đến key đã chết  
- 📊 **Monitoring tốt hơn**: Theo dõi trạng thái real-time
- 🔄 **Tự động recovery**: Khôi phục key khi có thể

**Khuyến nghị**: Chạy "Test All Keys" định kỳ để đảm bảo hệ thống hoạt động ổn định!
