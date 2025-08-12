#!/usr/bin/env python3
"""
OCR Setup Script
================

Automated setup script for installing and configuring all OCR dependencies
required by the MangaTranslator system.

This script installs:
- PaddleOCR (Chinese text recognition)
- EasyOCR (Korean + multilingual text)
- manga-ocr (Japanese manga text)
- TrOCR (Transformers OCR)
- Supporting libraries

Author: MangaTranslator Team
License: MIT
"""

import subprocess
import sys


def install_package(package):
    """
    Install a Python package using pip
    
    Args:
        package (str): Package name with optional version specifier
        
    Returns:
        bool: True if installation successful, False otherwise
    """
    print(f"📦 Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False


def install_paddlepaddle():
    """
    Install PaddlePaddle with specific index URL for better compatibility
    
    Returns:
        bool: True if installation successful, False otherwise
    """
    package = "paddlepaddle==3.1.0"
    index_url = "https://www.paddlepaddle.org.cn/packages/stable/cpu/"
    
    print(f"📦 Installing {package} from PaddlePaddle official repository...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            package, "-i", index_url
        ])
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False


def main():
    """Main setup function to install all OCR dependencies"""
    print("🔧 Setting up Multi-Language OCR Dependencies")
    print("=" * 60)
    
    # Step 1: Install PaddlePaddle first (special installation)
    print("\n🇨🇳 Installing PaddlePaddle for Chinese OCR...")
    paddlepaddle_success = install_paddlepaddle()
    
    # Step 2: Install other OCR packages
    print("\n📦 Installing other OCR dependencies...")
    packages = [
        # Chinese OCR (PaddleOCR) - depends on PaddlePaddle
        "paddleocr>=2.7.0",
        
        # Multi-language OCR  
        "easyocr>=1.7.0",
        
        # Transformer-based OCR
        "transformers>=4.21.0",
        
        # Additional dependencies
        "shapely>=1.8.0",
        "pyclipper>=1.3.0",
        "opencv-python>=4.5.0",
        
        # For image processing
        "Pillow>=8.0.0",
    ]
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    # Include PaddlePaddle in success count
    total_packages = len(packages) + 1
    if paddlepaddle_success:
        success_count += 1
    
    print(f"\n📊 Installation Summary:")
    print(f"✅ Success: {success_count}/{total_packages} packages")
    
    if success_count == total_packages:
        print("🎉 All OCR dependencies installed successfully!")
        print("\n🚀 Available OCR engines:")
        print("   • manga-ocr: Japanese manga (already installed)")
        print("   • PaddleOCR + PaddlePaddle: Chinese manhua") 
        print("   • EasyOCR: Korean manhwa + multi-language")
        print("   • TrOCR: General transformer-based OCR")
        
        print("\n💡 PaddlePaddle 3.1.0 installed from official repository for optimal compatibility")
        print("\n📝 Test the installation:")
        print("   python -c \"from multi_ocr import MultiLanguageOCR; print('OCR setup OK!')\"")
        
    else:
        print("⚠️  Some packages failed to install.")
        print("You may need to install them manually or check your Python environment.")
        if not paddlepaddle_success:
            print("\n🔧 Manual PaddlePaddle installation:")
            print("   python -m pip install paddlepaddle==3.1.0 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/")

if __name__ == "__main__":
    main()
