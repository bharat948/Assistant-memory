"""
Logging configuration and setup for the memory module.
"""
import logging
import os
import sys
from .config import LOG_DIR

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - %(name)s - [DEBUG] - %(message)s" + reset,
        logging.INFO: blue + "%(asctime)s - %(name)s - [INFO] - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - %(name)s - [WARNING] - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - %(name)s - [ERROR] - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - %(name)s - [CRITICAL] - %(message)s" + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

# Setup loggers
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())
if os.name == 'nt':  # Windows
    # Try to set console to UTF-8
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7, use a different approach
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    console_handler.setStream(sys.stdout)

# Updated FileHandler to write to the 'logger' directory
log_file_path = os.path.join(LOG_DIR, 'enhanced_memory.log')
file_handler = logging.FileHandler(log_file_path, mode='a')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

logger = logging.getLogger("EnhancedMemory")
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Separate logger for storage operations
storage_logger = logging.getLogger("EnhancedMemory.Storage")
storage_logger.setLevel(logging.INFO)
storage_logger.addHandler(file_handler)

# Separate logger for LLM operations
llm_logger = logging.getLogger("EnhancedMemory.LLM")
llm_logger.setLevel(logging.INFO)
llm_logger.addHandler(file_handler)
