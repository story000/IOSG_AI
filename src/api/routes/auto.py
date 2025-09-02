"""Auto report specific routes"""

from flask import Blueprint

# Auto routes are handled in main.py for now
auto_bp = Blueprint('auto', __name__, url_prefix='/auto')