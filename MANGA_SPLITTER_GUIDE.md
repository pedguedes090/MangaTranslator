# MangaTranslator - Chức Năng Cắt Ảnh Mới

## 🎉 Cập Nhật Mới: Tích Hợp Chức Năng Cắt Ảnh

Phiên bản mới của MangaTranslator đã tích hợp chức năng **cắt ảnh tự động** cho xử lý hàng loạt, giúp xử lý hiệu quả các ảnh manga dài.

### ✨ Tính Năng Mới

#### 🔧 Cắt Ảnh Thông Minh
- **Tự động phát hiện separator**: Nhận diện vùng trắng/đen để cắt ảnh
- **Điều chỉnh chiều cao tự động**: Tối ưu chiều cao dựa trên kích thước ảnh
- **Hỗ trợ nhiều loại manga**: Manga truyền thống, action manga, webtoon

#### 🎯 Ưu Điểm
- **Tránh cắt trúng bóng thoại**: Phát hiện vùng separator an toàn
- **Tối ưu cho OCR**: Ảnh nhỏ hơn = OCR chính xác hơn
- **Xử lý ảnh dài**: Webtoon, manga scan dài có thể xử lý hiệu quả
- **Tùy chọn linh hoạt**: Bật/tắt theo nhu cầu

### 🚀 Cách Sử Dụng

#### 1. Xử Lý Hàng Loạt với Cắt Ảnh

1. **Mở tab "Xử Lý Hàng Loạt"**
2. **Upload ảnh** như bình thường
3. **Mở "Cài Đặt Cắt Ảnh"** (accordion)
4. **Bật chức năng cắt ảnh**: ✅ "Bật chức năng cắt ảnh trước khi dịch"
5. **Điều chỉnh cài đặt** (hoặc để mặc định)
6. **Nhấn "Xử Lý Hàng Loạt"**

#### 2. Cài Đặt Cắt Ảnh

| Tham Số | Mô Tả | Giá Trị Mặc Định |
|----------|-------|------------------|
| **Tự động điều chỉnh chiều cao** | Tự động tính chiều cao tối ưu | ✅ Bật |
| **Chiều cao tối đa** | Chiều cao mỗi phần (px) | 2000px |
| **Ngưỡng pixel trắng** | Độ trắng nhận diện separator | 240 |
| **Ngưỡng pixel đen** | Độ đen nhận diện vùng dramatic | 15 |
| **Chiều cao separator** | Chiều cao tối thiểu vùng cắt | 15px |

### 🎨 Hoạt Động Với Các Loại Ảnh

#### ✅ Tương Thích Tốt
- **Manga truyền thống**: Nền trắng, separator rõ ràng
- **Action manga**: Vùng đen dramatic làm separator
- **Webtoon dài**: Tự động cắt theo chiều cao
- **Raw scan**: Chất lượng cao, separator rõ nét

#### ⚠️ Hạn Chế
- **Ảnh không có separator**: Sẽ cắt theo chiều cao cố định
- **Nền phức tạp**: Có thể không phát hiện separator chính xác
- **Ảnh quá nhỏ**: Không cần thiết phải cắt

### 🔧 API và Code

#### Sử Dụng Trực Tiếp MangaSplitter

```python
from manga_splitter import MangaSplitter
from PIL import Image

# Khởi tạo
splitter = MangaSplitter()

# Cắt ảnh
image = Image.open("manga_long.png")
split_images, split_info = splitter.split_image(
    image,
    auto_height=True,
    white_threshold=240,
    black_threshold=15,
    min_separator_height=15
)

print(f"Đã cắt thành {len(split_images)} phần")
print(f"Thông tin: {split_info}")
```

#### Sử Dụng BatchImageProcessor

```python
from batch_image_processor import BatchImageProcessor

# Khởi tạo
processor = BatchImageProcessor()

# Cài đặt cắt ảnh
split_settings = {
    'auto_height': True,
    'max_height': 2000,
    'white_threshold': 240,
    'black_threshold': 15,
    'min_separator_height': 15
}

# Xử lý với cắt ảnh
result = processor.process_images(
    image_files=image_list,
    enable_splitting=True,
    split_settings=split_settings
)
```

### 📊 Thống Kê Cắt Ảnh

Sau khi xử lý, hệ thống sẽ hiển thị:
- Số ảnh được cắt
- Tổng số phần được tạo
- Phương pháp cắt (tự động/cố định)
- Thời gian xử lý

### 🛠️ Troubleshooting

#### Vấn Đề Thường Gặp

**1. Không cắt được ảnh**
- Kiểm tra ảnh có separator rõ ràng không
- Điều chỉnh ngưỡng trắng/đen
- Thử tắt chế độ tự động

**2. Cắt sai vị trí**
- Tăng chiều cao tối thiểu separator
- Điều chỉnh ngưỡng pixel
- Kiểm tra chất lượng ảnh

**3. Quá nhiều phần nhỏ**
- Tăng chiều cao tối thiểu separator
- Điều chỉnh chiều cao tối đa
- Sử dụng chế độ cố định

### 🎯 Tips Sử Dụng

1. **Ảnh chất lượng cao**: Kết quả cắt tốt hơn
2. **Thử nghiệm cài đặt**: Mỗi loại manga cần cài đặt khác nhau
3. **Backup ảnh gốc**: Luôn giữ ảnh gốc để tham khảo
4. **Kiểm tra preview**: Sử dụng chức năng preview để kiểm tra
5. **Batch processing**: Cắt ảnh hoạt động tốt nhất với xử lý hàng loạt

### 📈 Performance

#### Trước Khi Có Cắt Ảnh
- Ảnh lớn → OCR chậm → Dịch kém chính xác
- Memory usage cao
- Thời gian xử lý lâu

#### Sau Khi Có Cắt Ảnh
- Ảnh nhỏ → OCR nhanh → Dịch chính xác hơn
- Memory usage thấp hơn
- Xử lý song song hiệu quả

### 🔄 Workflow Mới

```
[Upload Ảnh] → [Cắt Ảnh] → [Detect Bubbles] → [OCR] → [Translate] → [Add Text] → [Kết Quả]
     ↓              ↓            ↓           ↓         ↓          ↓          ↓
  1 ảnh dài    → N ảnh nhỏ  → Bubble/ảnh → Text/ảnh → Trans/ảnh → Final/ảnh → N ảnh hoàn chỉnh
```

### 🎉 Lợi Ích

- **Chất lượng dịch tốt hơn**: Ảnh nhỏ, OCR chính xác
- **Tốc độ nhanh hơn**: Xử lý song song nhiều phần
- **Tiết kiệm bộ nhớ**: Không load ảnh quá lớn
- **Linh hoạt**: Bật/tắt theo nhu cầu
- **Tự động**: Không cần can thiệp thủ công

---

## 📝 Changelog

### v2.1.0 - Manga Splitter Integration
- ✅ Thêm module `manga_splitter.py`
- ✅ Tích hợp vào `batch_image_processor.py`
- ✅ Cập nhật UI trong `app.py`
- ✅ Thêm cài đặt cắt ảnh trong batch processing
- ✅ Hỗ trợ fallback cho processing cũ
- ✅ Thống kê và logging chi tiết

### Tương Lai
- 🔄 Thêm preview cắt ảnh trực tiếp
- 🔄 Hỗ trợ cắt ảnh cho single image
- 🔄 Machine learning để phát hiện separator tốt hơn
- 🔄 Preset cho các loại manga khác nhau

---

*Developed by MangaTranslator Team - 2025*
