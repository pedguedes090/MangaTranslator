#!/usr/bin/env python3
"""
Manga Splitter Module
====================

Advanced manga image splitting functionality with automatic separator detection.
Supports both white and black separator detection for various manga styles.

Features:
- Automatic white/black separator detection
- Intelligent height optimization
- Batch processing support
- Preview generation

Author: MangaTranslator Team
"""

import cv2
import numpy as np
import os
import tempfile
from typing import List, Tuple, Optional
from PIL import Image
import uuid


class MangaSplitter:
    """
    Advanced manga image splitter with intelligent separator detection
    """
    
    def __init__(self):
        self.temp_dir = None
        
    def detect_separators(self, image: np.ndarray, 
                         white_threshold: int = 240, 
                         black_threshold: int = 15,
                         min_separator_height: int = 15) -> List[int]:
        """
        Phát hiện các vùng separator (trắng hoặc đen) để cắt
        
        Args:
            image (np.ndarray): Input image array
            white_threshold (int): White pixel threshold (default: 240)
            black_threshold (int): Black pixel threshold (default: 15)
            min_separator_height (int): Minimum separator height (default: 15)
            
        Returns:
            List[int]: List of Y coordinates for splitting
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
            
        height, width = gray.shape
        split_points = []
        
        # Phân tích từng hàng pixel (kiểm tra mỗi 3 pixel để tăng tốc)
        for y in range(0, height, 3):
            row = gray[y, :]
            
            # Đếm pixel trắng và đen
            white_pixels = np.sum(row > white_threshold)
            black_pixels = np.sum(row < black_threshold)
            white_ratio = white_pixels / width
            black_ratio = black_pixels / width
            
            # Kiểm tra xem có phải là vùng separator không
            is_separator = white_ratio > 0.85 or black_ratio > 0.85
            
            if is_separator:
                # Kiểm tra chiều cao vùng separator
                separator_height = 0
                separator_type = "white" if white_ratio > black_ratio else "black"
                
                for check_y in range(y, min(y + 50, height)):
                    check_row = gray[check_y, :]
                    if separator_type == "white":
                        check_ratio = np.sum(check_row > white_threshold) / width
                    else:
                        check_ratio = np.sum(check_row < black_threshold) / width
                    
                    if check_ratio > 0.85:
                        separator_height += 1
                    else:
                        break
                
                # Nếu vùng separator đủ cao
                if separator_height >= min_separator_height:
                    split_points.append(y + separator_height // 2)
        
        # Loại bỏ các điểm quá gần nhau
        filtered_points = []
        for point in split_points:
            if not filtered_points or point - filtered_points[-1] > 100:
                filtered_points.append(point)
        
        return filtered_points
    
    def filter_split_points_by_min_height(self, split_points: List[int], 
                                         image_height: int, 
                                         min_height: int = 1300) -> List[int]:
        """
        Lọc các điểm cắt để đảm bảo mỗi phần có chiều cao tối thiểu
        
        Args:
            split_points (List[int]): Danh sách điểm cắt ban đầu
            image_height (int): Chiều cao ảnh gốc
            min_height (int): Chiều cao tối thiểu mỗi phần (default: 1300)
            
        Returns:
            List[int]: Danh sách điểm cắt đã được lọc
        """
        if not split_points:
            return split_points
        
        # Thêm điểm đầu và cuối để tính toán
        all_points = [0] + split_points + [image_height]
        filtered_points = [0]  # Luôn giữ điểm đầu
        
        for i in range(1, len(all_points)):
            current_point = all_points[i]
            last_accepted_point = filtered_points[-1]
            
            # Kiểm tra chiều cao từ điểm cuối đã chấp nhận
            segment_height = current_point - last_accepted_point
            
            if current_point == image_height:
                # Đây là điểm cuối, kiểm tra xem phần cuối có quá nhỏ không
                if segment_height < min_height and len(filtered_points) > 1:
                    # Phần cuối quá nhỏ, loại bỏ điểm cắt cuối để gộp vào phần trước
                    filtered_points.pop()
                # Không thêm điểm cuối vào filtered_points
                break
            elif segment_height >= min_height:
                # Chấp nhận điểm này nếu đạt chiều cao tối thiểu
                filtered_points.append(current_point)
            # Nếu không đạt chiều cao tối thiểu, bỏ qua điểm này
        
        # Loại bỏ điểm đầu (0) khỏi kết quả
        return filtered_points[1:] if len(filtered_points) > 1 else []
    
    def calculate_optimal_height(self, image_height: int, auto_height: bool = True,
                               manual_height: int = None) -> int:
        """
        Tính toán chiều cao tối ưu cho việc cắt ảnh
        
        Args:
            image_height (int): Chiều cao ảnh gốc
            auto_height (bool): Tự động tính chiều cao tối ưu
            manual_height (int): Chiều cao thủ công
            
        Returns:
            int: Chiều cao tối ưu
        """
        if not auto_height and manual_height:
            return max(manual_height, 1300)  # Đảm bảo tối thiểu 1300px
            
        # Tự động điều chỉnh chiều cao
        if image_height <= 2000:
            return max(image_height // 2, 1300)
        elif image_height <= 4000:
            return max(image_height // 3, 1300)
        elif image_height <= 6000:
            return max(2000, 1300)
        elif image_height <= 10000:
            return max(2500, 1300)
        else:
            return max(image_height // (image_height // 2000), 1300)
    
    def split_image(self, image: Image.Image, 
                   max_height: int = None,
                   white_threshold: int = 240,
                   black_threshold: int = 15,
                   min_separator_height: int = 15,
                   auto_height: bool = True) -> Tuple[List[Image.Image], dict]:
        """
        Cắt ảnh manga thành nhiều phần
        
        Args:
            image (Image.Image): Ảnh đầu vào
            max_height (int): Chiều cao tối đa mỗi phần
            white_threshold (int): Ngưỡng pixel trắng
            black_threshold (int): Ngưỡng pixel đen
            min_separator_height (int): Chiều cao tối thiểu vùng separator
            auto_height (bool): Tự động điều chỉnh chiều cao
            
        Returns:
            Tuple[List[Image.Image], dict]: Danh sách ảnh đã cắt và thông tin
        """
        try:
            # Convert PIL to OpenCV format
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_cv = img_array
            
            height, width = img_array.shape[:2]
            
            # Tính chiều cao tối ưu
            if auto_height or max_height is None or max_height == 0:
                calculated_height = self.calculate_optimal_height(height, auto_height)
                max_height = calculated_height
                auto_mode_text = " (Tự động tối ưu)"
            else:
                auto_mode_text = " (Thủ công)"
            
            # Tìm điểm cắt
            split_points = self.detect_separators(
                img_cv, white_threshold, black_threshold, min_separator_height
            )
            
            # Lọc điểm cắt để đảm bảo chiều cao tối thiểu 1300px
            original_split_count = len(split_points)
            split_points = self.filter_split_points_by_min_height(split_points, height, min_height=1300)
            
            # Nếu không tìm thấy điểm cắt hoặc sau khi lọc không còn điểm nào, dùng chiều cao đã tính
            if not split_points:
                # Đảm bảo max_height >= 1300
                if max_height < 1300:
                    max_height = 1300
                split_points = list(range(max_height, height, max_height))
                split_method = "fixed_height"
                if original_split_count > 0:
                    info_msg = f"Tìm thấy {original_split_count} separator nhưng không đạt chiều cao tối thiểu 1500px, cắt theo chiều cao {max_height}px{auto_mode_text}"
                else:
                    info_msg = f"Không tìm thấy vùng separator, cắt theo chiều cao {max_height}px{auto_mode_text}"
            else:
                split_method = "auto_separator"
                filtered_info = f" (đã lọc từ {original_split_count} điểm)" if original_split_count != len(split_points) else ""
                info_msg = f"Tìm thấy {len(split_points)} vùng separator tự động{filtered_info}, đảm bảo chiều cao tối thiểu 1500px{auto_mode_text}"
            
            # Thêm điểm đầu và cuối
            all_points = [0] + split_points + [height]
            all_points = sorted(list(set(all_points)))
            
            # Cắt ảnh
            split_images = []
            valid_parts = 0
            
            for i in range(len(all_points) - 1):
                start_y = all_points[i]
                end_y = all_points[i + 1]
                
                # Kiểm tra chiều cao tối thiểu (đã được đảm bảo trong filter, nhưng kiểm tra lại để chắc chắn)
                segment_height = end_y - start_y
                if segment_height < 1500:
                    print(f"⚠️ Phần {valid_parts + 1} có chiều cao {segment_height}px < 1500px, vẫn giữ lại")
                
                # Bỏ qua phần quá nhỏ (dưới 100px)
                if segment_height < 100:
                    continue
                
                valid_parts += 1
                
                # Cắt ảnh bằng PIL (giữ nguyên format)
                cropped_pil = image.crop((0, start_y, image.width, end_y))
                split_images.append(cropped_pil)
                
                print(f"✅ Phần {valid_parts}: {segment_height}px (từ {start_y} đến {end_y})")
            
            # Thông tin kết quả
            result_info = {
                'original_size': (width, height),
                'max_height': max_height,
                'auto_mode': auto_height,
                'split_method': split_method,
                'split_points': split_points,
                'total_parts': valid_parts,
                'info_message': info_msg
            }
            
            return split_images, result_info
            
        except Exception as e:
            raise Exception(f"Lỗi khi cắt ảnh: {str(e)}")
    
    def create_preview_image(self, image: Image.Image, split_points: List[int]) -> Image.Image:
        """
        Tạo ảnh preview với các đường cắt
        
        Args:
            image (Image.Image): Ảnh gốc
            split_points (List[int]): Danh sách điểm cắt
            
        Returns:
            Image.Image: Ảnh preview với đường cắt
        """
        try:
            # Convert to OpenCV format
            img_array = np.array(image)
            if len(img_array.shape) == 3:
                preview_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                preview_cv = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
            
            # Vẽ đường cắt
            width = preview_cv.shape[1]
            for point in split_points:
                cv2.line(preview_cv, (0, point), (width, point), (0, 0, 255), 3)
            
            # Convert back to PIL
            preview_rgb = cv2.cvtColor(preview_cv, cv2.COLOR_BGR2RGB)
            preview_pil = Image.fromarray(preview_rgb)
            
            return preview_pil
            
        except Exception as e:
            print(f"Lỗi tạo preview: {str(e)}")
            return image
    
    def split_image_batch(self, images: List[Tuple[Image.Image, str]], 
                         split_settings: dict) -> List[Tuple[List[Image.Image], str, dict]]:
        """
        Cắt nhiều ảnh trong batch
        
        Args:
            images (List[Tuple[Image.Image, str]]): Danh sách (ảnh, tên file)
            split_settings (dict): Cài đặt cắt ảnh
            
        Returns:
            List[Tuple[List[Image.Image], str, dict]]: Danh sách (ảnh đã cắt, tên file, thông tin)
        """
        results = []
        
        for image, filename in images:
            try:
                split_images, info = self.split_image(
                    image,
                    max_height=split_settings.get('max_height'),
                    white_threshold=split_settings.get('white_threshold', 240),
                    black_threshold=split_settings.get('black_threshold', 15),
                    min_separator_height=split_settings.get('min_separator_height', 15),
                    auto_height=split_settings.get('auto_height', True)
                )
                
                results.append((split_images, filename, info))
                print(f"✅ Cắt thành công {filename}: {len(split_images)} phần")
                
            except Exception as e:
                print(f"❌ Lỗi cắt {filename}: {str(e)}")
                # Trả về ảnh gốc nếu cắt thất bại
                results.append(([image], filename, {'error': str(e)}))
        
        return results


# Global instance for easy usage
manga_splitter = MangaSplitter()


def split_manga_image(image: Image.Image, **kwargs) -> Tuple[List[Image.Image], dict]:
    """
    Convenience function để cắt ảnh manga
    
    Args:
        image (Image.Image): Ảnh đầu vào
        **kwargs: Các tham số cắt ảnh
        
    Returns:
        Tuple[List[Image.Image], dict]: Ảnh đã cắt và thông tin
    """
    return manga_splitter.split_image(image, **kwargs)


def split_manga_batch(images: List[Tuple[Image.Image, str]], 
                     split_settings: dict) -> List[Tuple[List[Image.Image], str, dict]]:
    """
    Convenience function để cắt nhiều ảnh
    
    Args:
        images (List[Tuple[Image.Image, str]]): Danh sách ảnh và tên file
        split_settings (dict): Cài đặt cắt ảnh
        
    Returns:
        List[Tuple[List[Image.Image], str, dict]]: Kết quả cắt ảnh
    """
    return manga_splitter.split_image_batch(images, split_settings)
