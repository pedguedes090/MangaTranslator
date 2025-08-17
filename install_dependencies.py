#!/usr/bin/env python3
"""
Auto Installation Script for MangaTranslator Dependencies
========================================================

This script automatically installs all required dependencies including
PaddlePaddle from the correct source.

Usage:
    python install_dependencies.py

Author: MangaTranslator Team
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔧 {description}...")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        if result.stdout:
            print("Output:", result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print("Error:", e.stderr.strip() if e.stderr else str(e))
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.8+ is required")
        return False

def install_basic_requirements():
    """Install basic requirements from requirements.txt (excluding PaddlePaddle)"""
    print("\n📦 Installing basic requirements...")
    
    # Read requirements.txt and filter out paddlepaddle
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    filtered_requirements = []
    for line in lines:
        line = line.strip()
        # Skip comments, empty lines, and paddlepaddle
        if (line and not line.startswith('#') and 
            not line.lower().startswith('paddlepaddle')):
            filtered_requirements.append(line)
    
    # Create temporary requirements file
    temp_req_file = 'temp_requirements.txt'
    with open(temp_req_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered_requirements))
    
    # Install filtered requirements
    success = run_command(
        f"python -m pip install -r {temp_req_file}",
        "Installing basic requirements"
    )
    
    # Clean up
    if os.path.exists(temp_req_file):
        os.remove(temp_req_file)
    
    return success

def install_paddlepaddle():
    """Install PaddlePaddle from the official source"""
    print("\n🐼 Installing PaddlePaddle...")
    
    # Try to install PaddlePaddle from official source
    success = run_command(
        "python -m pip install paddlepaddle==3.1.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/",
        "Installing PaddlePaddle from official source"
    )
    
    if not success:
        print("\n💡 Trying alternative installation method...")
        success = run_command(
            "python -m pip install paddlepaddle==3.1.1",
            "Installing PaddlePaddle from PyPI"
        )
    
    return success

def verify_installation():
    """Verify that key packages are installed correctly"""
    print("\n🧪 Verifying installation...")
    
    test_imports = [
        ("numpy", "NumPy"),
        ("cv2", "OpenCV"),
        ("PIL", "Pillow"),
        ("torch", "PyTorch"),
        ("ultralytics", "Ultralytics"),
        ("gradio", "Gradio"),
        ("paddleocr", "PaddleOCR"),
        ("easyocr", "EasyOCR"),
        ("manga_ocr", "Manga OCR"),
        ("transformers", "Transformers")
    ]
    
    failed_imports = []
    
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name} - OK")
        except ImportError as e:
            print(f"❌ {name} - FAILED: {e}")
            failed_imports.append(name)
    
    # Special test for PaddlePaddle
    try:
        import paddle
        print(f"✅ PaddlePaddle - OK (version: {paddle.__version__})")
    except ImportError as e:
        print(f"❌ PaddlePaddle - FAILED: {e}")
        failed_imports.append("PaddlePaddle")
    
    if failed_imports:
        print(f"\n⚠️ Failed imports: {', '.join(failed_imports)}")
        return False
    else:
        print("\n🎉 All packages verified successfully!")
        return True

def main():
    """Main installation process"""
    print("🚀 MangaTranslator Dependencies Installation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("\n❌ Installation aborted: Incompatible Python version")
        sys.exit(1)
    
    # Upgrade pip first
    print("\n📦 Upgrading pip...")
    run_command("python -m pip install --upgrade pip", "Upgrading pip")
    
    # Install basic requirements
    if not install_basic_requirements():
        print("\n❌ Failed to install basic requirements")
        sys.exit(1)
    
    # Install PaddlePaddle separately
    if not install_paddlepaddle():
        print("\n⚠️ PaddlePaddle installation failed, but continuing...")
        print("💡 You can try installing manually:")
        print("python -m pip install paddlepaddle==3.1.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/")
    
    # Verify installation
    print("\n" + "=" * 50)
    success = verify_installation()
    
    if success:
        print("\n🎉 Installation completed successfully!")
        print("\n🚀 You can now run the application:")
        print("python app.py")
    else:
        print("\n⚠️ Installation completed with some issues")
        print("Please check the failed imports above")
    
    print("\n📋 Next steps:")
    print("1. Set up your API keys in .env file (copy from .env.example)")
    print("2. Run: python app.py")
    print("3. Open your browser to the provided URL")

if __name__ == "__main__":
    main()
