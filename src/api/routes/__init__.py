"""API routes package"""

from flask import Flask
from .main import main_bp
from .auto import auto_bp
from .labelhub import labelhub_bp
from .api import api_bp
from .process import process_bp
from .evaluation import evaluation_bp


def register_routes(app: Flask):
    """Register all route blueprints"""
    app.register_blueprint(main_bp)
    app.register_blueprint(auto_bp)
    app.register_blueprint(labelhub_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(process_bp)
    app.register_blueprint(evaluation_bp)