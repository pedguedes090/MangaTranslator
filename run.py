#!/usr/bin/env python3
"""
MangaTranslator Startup Script
=============================

Smart startup script that checks dependencies and runs the application.

Usage:
    python run.py

Author: MangaTranslator Team
"""

import sys
import os
import subprocess

def check_dependency(module_name, package_name=None):
    """Check if a dependency is installed"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def check_critical_dependencies():
    """Check critical dependencies for the application"""
    critical_deps = [
        ("gradio", "gradio"),
        ("cv2", "opencv-python"),
        ("PIL", "pillow"),
        ("numpy", "numpy"),
        ("torch", "torch"),
        ("ultralytics", "ultralytics")
    ]
    
    missing_deps = []
    
    print("🔍 Checking critical dependencies...")
    for module, package in critical_deps:
        if check_dependency(module):
            print(f"✅ {package}")
        else:
            print(f"❌ {package} - MISSING")
            missing_deps.append(package)
    
    return missing_deps

def check_ocr_dependencies():
    """Check OCR dependencies (optional but recommended)"""
    ocr_deps = [
        ("paddleocr", "paddleocr"),
        ("easyocr", "easyocr"), 
        ("manga_ocr", "manga-ocr"),
        ("transformers", "transformers")
    ]
    
    missing_ocr = []
    
    print("\n👁️ Checking OCR dependencies...")
    for module, package in ocr_deps:
        if check_dependency(module):
            print(f"✅ {package}")
        else:
            print(f"⚠️ {package} - MISSING (OCR functionality will be limited)")
            missing_ocr.append(package)
    
    # Special check for PaddlePaddle
    if check_dependency("paddle"):
        print("✅ paddlepaddle")
    else:
        print("⚠️ paddlepaddle - MISSING (Chinese OCR will not work)")
        missing_ocr.append("paddlepaddle")
    
    return missing_ocr

def run_installation():
    """Run the installation script"""
    print("\n🔧 Running automatic installation...")
    try:
        subprocess.run([sys.executable, "install_dependencies.py"], check=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ Automatic installation failed")
        return False
    except FileNotFoundError:
        print("❌ install_dependencies.py not found")
        return False

def run_application():
    """Run the main application"""
    print("\n🚀 Starting MangaTranslator...")
    try:
        subprocess.run([sys.executable, "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Application failed to start: {e}")

def main():
    """Main startup process"""
    print("🎌 MangaTranslator Startup")
    print("=" * 30)
    
    # Check if we're in the right directory
    if not os.path.exists("app.py"):
        print("❌ app.py not found! Please run this script from the MangaTranslator directory")
        sys.exit(1)
    
    # Check critical dependencies
    missing_critical = check_critical_dependencies()
    missing_ocr = check_ocr_dependencies()
    
    # Handle missing critical dependencies
    if missing_critical:
        print(f"\n❌ Critical dependencies missing: {', '.join(missing_critical)}")
        print("\n💡 Options:")
        print("1. Run automatic installation: python install_dependencies.py")
        print("2. Install manually: pip install -r requirements.txt")
        print("3. Continue anyway (may fail)")
        
        choice = input("\nChoose option (1/2/3): ").strip()
        
        if choice == "1":
            if not run_installation():
                print("❌ Installation failed. Please install manually.")
                sys.exit(1)
        elif choice == "2":
            print("💡 Please run: pip install -r requirements.txt")
            print("💡 Then run: python run.py")
            sys.exit(0)
        elif choice == "3":
            print("⚠️ Continuing with missing dependencies...")
        else:
            print("❌ Invalid choice. Exiting.")
            sys.exit(1)
    
    # Warn about missing OCR dependencies
    if missing_ocr:
        print(f"\n⚠️ Some OCR engines are missing: {', '.join(missing_ocr)}")
        print("💡 The app will work but with limited OCR capabilities")
        print("💡 Run 'python install_dependencies.py' to install all OCR engines")
        
        choice = input("\nContinue anyway? (y/n): ").strip().lower()
        if choice not in ['y', 'yes']:
            sys.exit(0)
    
    # Check environment file
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            print("\n💡 .env file not found. Copy .env.example to .env and add your API keys")
            choice = input("Create .env from template? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                import shutil
                shutil.copy(".env.example", ".env")
                print("✅ .env file created. Please edit it to add your API keys.")
        else:
            print("\n⚠️ No .env file found. You may need to configure API keys manually.")
    
    # Run the application
    print("\n" + "=" * 50)
    run_application()

if __name__ == "__main__":
    main()
