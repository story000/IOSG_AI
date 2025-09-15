#!/usr/bin/env python3
"""
IOSG Crypto News Analysis System - Main Entry Point

A professional cryptocurrency news analysis platform with AI-powered 
classification, filtering, and automated report generation.
"""

import sys
import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.api.app import create_app
from src.utils.config import get_settings
from src.utils.logger import get_logger
from src.services.token_refresh_service import start_token_refresh_service, stop_token_refresh_service

logger = get_logger(__name__)


def main():
    """Main application entry point"""
    
    # Load settings
    settings = get_settings()
    
    # Create Flask app
    app = create_app()
    
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Host: {settings.host}, Port: {settings.port}")

    # 启动Token自动刷新服务（每12小时检查一次）
    try:
        start_token_refresh_service(refresh_interval_hours=12)
        logger.info("Token自动刷新服务已启动")
    except Exception as e:
        logger.warning(f"Token自动刷新服务启动失败: {e}")

    # Force line buffering for better real-time output
    sys.stdout.reconfigure(line_buffering=True)
    
    # Run the application
    app.socketio.run(
        app,
        debug=settings.debug,
        host=settings.host,
        port=settings.port,
        use_reloader=False  # Avoid issues with threading
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)
    finally:
        # 确保停止Token刷新服务
        try:
            stop_token_refresh_service()
            logger.info("Token自动刷新服务已停止")
        except Exception as e:
            logger.warning(f"停止Token刷新服务时出错: {e}")