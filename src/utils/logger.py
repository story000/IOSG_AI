"""Structured logging configuration"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Colored console formatter for better readability"""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.RESET}"
            )
        return super().format(record)


def setup_logger(
    name: str = "iosg",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console: bool = True
) -> logging.Logger:
    """Setup structured logger with console and optional file output"""
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    console_formatter = ColoredFormatter(
        '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)-8s %(name)s.%(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


class LogCapture:
    """Capture logs and forward to web interface"""
    
    def __init__(self, process_name: str, socketio=None, max_entries: int = 1000):
        self.process_name = process_name
        self.socketio = socketio
        self.max_entries = max_entries
        self.logs = []
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
    def __enter__(self):
        sys.stdout = self
        sys.stderr = self
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def write(self, text: str):
        """Capture written text"""
        if text.strip():
            log_entry = {
                'timestamp': datetime.now().strftime('%H:%M:%S'),
                'message': text.strip()
            }
            
            # Maintain log size limit
            self.logs.append(log_entry)
            if len(self.logs) > self.max_entries:
                self.logs = self.logs[-self.max_entries:]
            
            # Emit to web interface if available
            if self.socketio:
                self.socketio.emit('log_update', {
                    'process': self.process_name,
                    'log': log_entry
                })
        
        # Also write to original stdout
        self.original_stdout.write(text)
        
    def flush(self):
        """Flush output"""
        self.original_stdout.flush()
    
    def get_logs(self):
        """Get captured logs"""
        return self.logs.copy()
    
    def clear_logs(self):
        """Clear captured logs"""
        self.logs.clear()