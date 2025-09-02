"""Flask application factory"""

import os
from pathlib import Path
from flask import Flask
from flask_mail import Mail
from flask_socketio import SocketIO

from ..utils.config import get_settings
from ..utils.logger import setup_logger
from .routes import register_routes
from .websocket import setup_socketio


def create_app() -> Flask:
    """Create and configure Flask application"""
    
    # Load settings
    settings = get_settings()
    
    # Setup logging
    setup_logger(
        name="iosg",
        level="DEBUG" if settings.debug else "INFO",
        console=True
    )
    
    # Get project root directory (two levels up from src/api/)
    project_root = Path(__file__).parent.parent.parent
    template_dir = project_root / 'templates'
    static_dir = project_root / 'static'
    
    # Create Flask app with correct template and static directories
    app = Flask(__name__, 
                template_folder=str(template_dir),
                static_folder=str(static_dir))
    app.config['SECRET_KEY'] = settings.secret_key
    
    # Configure Flask-Mail
    mail_config = settings.get_mail_config()
    for key, value in mail_config.items():
        app.config[key] = value
    
    # Initialize extensions
    mail = Mail(app)
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Store instances for access in routes
    app.mail = mail
    app.socketio = socketio
    app.settings = settings
    
    # Setup WebSocket handlers
    setup_socketio(socketio)
    
    # Register routes
    register_routes(app)
    
    return app