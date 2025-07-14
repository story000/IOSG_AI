#!/usr/bin/env python3
"""
Web Application Runner
Quick start script for the Crypto News Analysis Web Interface
"""

import subprocess
import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'flask_socketio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:", ', '.join(missing_packages))
        print("📦 Installing dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully!")
    else:
        print("✅ All dependencies are already installed")

def main():
    print("=== Crypto News Analysis Web Interface ===")
    print("🚀 Starting web application...")
    
    # Check dependencies
    try:
        check_dependencies()
    except Exception as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Please run: pip install -r requirements.txt")
        return
    
    # Start the web application
    try:
        print("\n🌐 Web interface will be available at:")
        print("   Local: http://localhost:8080")
        print("   Network: http://0.0.0.0:8080")
        print("\n💡 Instructions:")
        print("   1. 点击 '开始获取' 按钮获取最新文章")
        print("   2. 点击 '开始分类' 按钮对文章进行分类")
        print("   3. 输入OpenAI API密钥并点击 '开始AI过滤' 生成最终报告")
        print("\n⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        from app import socketio, app
        socketio.run(app, debug=False, host='0.0.0.0', port=8080)
        
    except KeyboardInterrupt:
        print("\n\n👋 Web server stopped by user")
    except Exception as e:
        print(f"\n❌ Failed to start web server: {e}")

if __name__ == "__main__":
    main()