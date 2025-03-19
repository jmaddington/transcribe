import os
import logging
from logging.handlers import RotatingFileHandler
import sys
from datetime import datetime

# Ensure logs directory exists
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create a custom formatter
class CustomFormatter(logging.Formatter):
    """Custom formatter with colored output for console"""
    
    grey = "\x1b[38;20m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + FORMAT + reset,
        logging.INFO: green + FORMAT + reset,
        logging.WARNING: yellow + FORMAT + reset,
        logging.ERROR: red + FORMAT + reset,
        logging.CRITICAL: bold_red + FORMAT + reset
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(name, log_file=None, level=logging.INFO):
    """Set up logger with file and console handlers"""
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logs
    
    # Clear existing handlers to avoid duplicates
    if logger.handlers:
        logger.handlers = []
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(CustomFormatter())
    logger.addHandler(console_handler)
    
    # Create file handler if a log file is specified
    if log_file:
        if not log_file.startswith('logs/'):
            log_file = f"logs/{log_file}"
        
        # Create rotating file handler (10MB max, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file, 
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    
    return logger

# Create main application logger
def get_app_logger():
    """Get the main application logger"""
    timestamp = datetime.now().strftime("%Y%m%d")
    return setup_logger('transcribe', f'logs/transcribe_{timestamp}.log', logging.INFO)

# Create API logger
def get_api_logger():
    """Get the OpenAI API logger"""
    timestamp = datetime.now().strftime("%Y%m%d")
    return setup_logger('transcribe.api', f'logs/api_{timestamp}.log', logging.INFO)

# Create database logger
def get_db_logger():
    """Get the database logger"""
    timestamp = datetime.now().strftime("%Y%m%d")
    return setup_logger('transcribe.db', f'logs/db_{timestamp}.log', logging.INFO)
