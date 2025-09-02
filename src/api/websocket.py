"""WebSocket event handlers"""

from flask_socketio import SocketIO, emit
from ..utils.logger import get_logger

logger = get_logger(__name__)


def setup_socketio(socketio: SocketIO):
    """Setup WebSocket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info("Client connected")
        emit('connected', {'data': 'Connected to server'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info("Client disconnected")
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping from client"""
        emit('pong', {'timestamp': time.time()})
    
    return socketio