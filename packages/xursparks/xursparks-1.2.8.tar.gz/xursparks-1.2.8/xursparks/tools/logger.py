import logging
from datetime import datetime
import os

class Logger:
    """
    A class to handle logging functionality.
    """
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize logger with log directory.
        
        Args:
            log_dir (str): Directory to store log files
        """
        self.log_dir = log_dir
        
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Configure logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create handlers
        # File handler - logs to file with date
        log_file = os.path.join(
            log_dir, 
            f"log_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        # Stream handler - logs to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def log(self, message: str, level: str = "info"):
        """
        Log a message with specified level.
        
        Args:
            message (str): Message to log
            level (str): Logging level (debug, info, warning, error, critical)
        """
        level = level.lower()
        if level == "debug":
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "critical":
            self.logger.critical(message)
        else:
            self.logger.info(f"Unknown log level '{level}', using INFO: {message}")

    def __del__(self):
        """Cleanup handlers on object destruction"""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)