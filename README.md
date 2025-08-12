# Multi-Language Comic Translator 🌏

**Hệ thống dịch truyện tranh đa ngôn ngữ thông minh với AI**

Công cụ dịch truyện tranh chuyên nghiệp hỗ trợ đa ngôn ngữ: Manga (Nhật), Manhua (Trung), và Manhwa (Hàn) sang tiếng Việt với độ chính xác cao.

## ✨ Tính năng nổi bật

### 🎯 OCR Engine Tối ưu
- **📚 manga-ocr**: Chuyên biệt cho text Nhật Bản (manga)
- **🇨🇳 PaddleOCR**: Tối ưu cho text Trung Quốc (manhua)  
- **🇰🇷 EasyOCR**: Hỗ trợ tốt Korean và đa ngôn ngữ (manhwa)
- **🔄 TrOCR**: Backup engine cho mọi ngôn ngữ

### 🤖 AI Translation
- **Gemini 2.0 Flash**: AI dịch thông minh với prompt tối ưu
- **Context-aware**: Hiểu ngữ cảnh manga/manhua/manhwa
- **Genre prompts**: Prompt chuyên dụng cho từng thể loại (Hành động, Tình cảm, Hài hước, Kinh dị, Kiếm hiệp, Tiên hiệp, Game giả tưởng)
- **Cultural adaptation**: Dịch phù hợp văn hóa Việt Nam
- **Onomatopoeia handling**: Xử lý hiệu ứng âm thanh chuyên nghiệp

### 🎨 Smart Text Processing
- **Bubble detection**: Tự động phát hiện khung thoại bằng YOLO
- **Text fitting**: Tự động điều chỉnh font và layout
- **Multi-font support**: 4 loại font tối ưu cho manga

## 🌐 Ngôn ngữ hỗ trợ

| Ngôn ngữ | Loại truyện | OCR Engine | Độ chính xác |
|----------|-------------|------------|--------------|
| 🇯🇵 Tiếng Nhật | Manga | manga-ocr | ⭐⭐⭐⭐⭐ |
| 🇨🇳 Tiếng Trung | Manhua | PaddleOCR | ⭐⭐⭐⭐⭐ |
| 🇰🇷 Tiếng Hàn | Manhwa | EasyOCR | ⭐⭐⭐⭐ |
| 🇺🇸 Tiếng Anh | Comics | EasyOCR | ⭐⭐⭐⭐ |

**Đầu ra**: 🇻🇳 Tiếng Việt tự nhiên, phù hợp văn hóa

## 🚀 Cách sử dụng

### Bước 1: Chuẩn bị
```bash
# Clone repository
git clone https://github.com/pedguedes090/MangaTranslator
cd MangaTranslator

# Cài đặt dependencies  
pip install -r requirements.txt

# Setup OCR engines (tùy chọn)
python setup_ocr.py
```

### Bước 2: Chạy ứng dụng
```bash
python app.py
```

### Bước 3: Sử dụng giao diện web
1. **Upload ảnh** manga/manhua/manhwa
2. **Chọn phương thức dịch:**
   - 🤖 **Gemini AI** (khuyến nghị) - Thông minh nhất
   - 🌐 **Google Translate** - Nhanh, đáng tin cậy  
   - 🔄 **Bing, Sogou, Helsinki-NLP** - Các lựa chọn khác
3. **Chọn font** phù hợp với style truyện
4. **Chọn ngôn ngữ nguồn** hoặc để "Tự động"
5. **Chọn thể loại truyện** (Hành động, Tình cảm, Hài hước, Kinh dị, Kiếm hiệp, Tiên hiệp, Game giả tưởng) hoặc để "Tự động"
6. **Nhập Gemini API key** (cho dịch AI - tùy chọn)
7. **Submit và thưởng thức kết quả!**

## 🔧 Cấu hình

### Environment Variables
Tạo file `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### Gemini API Key
Để có trải nghiệm dịch AI tốt nhất:
1. Truy cập [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Tạo API key miễn phí
3. Nhập vào ứng dụng hoặc file `.env`

## 📁 Cấu trúc Project

```
MangaTranslator/
├── 📄 app.py                 # Giao diện chính Gradio  
├── 🔍 detect_bubbles.py      # Phát hiện bubble bằng YOLO
├── 👁️ multi_ocr.py           # Hệ thống OCR đa ngôn ngữ
├── 🌐 translator.py          # Engine dịch thuật đa dịch vụ
├── 🖼️ process_bubble.py      # Xử lý và làm sạch bubble
├── ✍️ add_text.py            # Thêm text đã dịch vào ảnh
├── ⚙️ setup_ocr.py           # Script cài đặt OCR engines
├── 🤖 model.pt              # Mô hình YOLO cho bubble detection
├── 📋 requirements.txt      # Dependencies Python
├── 📖 README.md             # Hướng dẫn chi tiết
├── 🎨 fonts/                # Font chữ cho manga
│   ├── animeace_i.ttf       # Font manga style
│   ├── animeace2_reg.ttf    # Font manga regular
│   ├── mangati.ttf          # Font manga italic
│   └── ariali.ttf           # Font Arial Unicode
└── 📸 examples/             # Ảnh mẫu để test
    ├── 0.png               # Manga sample
    └── ex0.png             # Manhwa sample
```

## 🧠 Ưu điểm của Gemini AI

### Nhận diện thông minh:
- Tự động phát hiện Nhật/Trung/Hàn dựa trên ký tự
- Hiểu ngữ cảnh manga, manhua, manhwa khác nhau

### Dịch chuyên nghiệp:
- **Manga (Nhật)**: "やばい!" → "Tệ rồi!" (không phải "Nguy hiểm")
- **Manhua (Trung)**: "加油!" → "Cố lên!" (không phải "Thêm dầu")  
- **Manhwa (Hàn)**: "화이팅!" → "Cố lên!" (không phải "Fighting")

### Xử lý văn hóa:
- Kính ngữ → Xưng hô Việt phù hợp
- Sound effects → Onomatopoeia tiếng Việt
- Tên riêng → Giữ nguyên
- Cảm xúc → Biểu đạt tự nhiên

## 🎯 So sánh dịch thuật

| Ngôn ngữ | Text gốc | Gemini AI | Google Translate |
|----------|----------|-----------|------------------|
| 🇯🇵 Nhật | そうですね | "Đúng rồi" | "Như vậy thì" |
| 🇨🇳 Trung | 太好了！ | "Tuyệt quá!" | "Quá tốt!" |
| 🇰🇷 Hàn | 대박！ | "Tuyệt vời!" | "Daebak!" |
| 🇯🇵 Nhật | お疲れ様 | "Cảm ơn bạn đã vất vả" | "Bạn đã làm việc chăm chỉ" |

## 🤝 Đóng góp

1. Fork repository
2. Tạo branch mới: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Tạo Pull Request

## 📄 License

MIT License - Xem file [LICENSE](LICENSE) để biết chi tiết.

## 🙏 Credits

- **YOLO**: Object detection for bubble detection
- **manga-ocr**: Japanese text recognition
- **PaddleOCR**: Chinese text recognition  
- **EasyOCR**: Multi-language text recognition
- **Gemini AI**: Advanced translation
- **Gradio**: Web interface

---

**✨ Trải nghiệm dịch truyện tranh thông minh với AI! 🚀**