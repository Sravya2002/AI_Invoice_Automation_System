"""Logger utility for Invoice Portal Automation Agent"""
import logging
import os
import sys
from datetime import datetime


class FlowLogger:
    """Custom logger for the automation flow"""

    def __init__(self, log_dir: str, vendor_name: str):
        """
        Initialize logger

        Args:
            log_dir (str): Directory to save logs
            vendor_name (str): Name of vendor (for log filename)
        """
        self.log_dir = log_dir
        self.vendor_name = vendor_name
        self.logs = []
        self._handlers = []

        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        # Use a unique logger name per vendor + timestamp to avoid handler leakage
        # between test runs that share the same vendor name.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        logger_name = f"flow1_{vendor_name}_{timestamp}"
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        # Prevent propagation so root handlers don't double-print.
        self.logger.propagate = False

        # Create log file path
        log_file = os.path.join(log_dir, f"flow1_{vendor_name}_{timestamp}.log")

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File handler — UTF-8 so special chars are stored correctly
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)

        # Console handler — UTF-8 on Windows to avoid cp1252 UnicodeEncodeError
        stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8',
                      buffering=1, closefd=False)
        console_handler = logging.StreamHandler(stream)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self._handlers = [file_handler, console_handler]

        self.log_file = log_file

    # ------------------------------------------------------------------
    # Logging helpers
    # ------------------------------------------------------------------

    def log_info(self, message: str):
        """Log info message"""
        self.logger.info(message)
        self.logs.append(f"INFO: {message}")

    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)
        self.logs.append(f"WARNING: {message}")

    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)
        self.logs.append(f"ERROR: {message}")

    def log_debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)
        self.logs.append(f"DEBUG: {message}")

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_logs(self):
        """Get all collected logs"""
        return self.logs

    def get_log_file(self):
        """Get log file path"""
        return self.log_file

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self):
        """Flush and close all handlers so log files are released on Windows."""
        for handler in self._handlers:
            try:
                handler.flush()
                handler.close()
                self.logger.removeHandler(handler)
            except Exception:
                pass
        self._handlers = []
