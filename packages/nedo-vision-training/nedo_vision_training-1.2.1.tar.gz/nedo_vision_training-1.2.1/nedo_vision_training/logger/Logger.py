import logging
import os
import sys

class Logger:
    def __init__(self, name: str = "APP", log_file: str = 'app.log', level: int = logging.DEBUG):
        """
        Initializes the Logger instance.

        :param name: Name of the logger.
        :param log_file: Path to the log file where logs will be written.
        :param level: Logging level (default: logging.DEBUG).
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Prevent duplicate handlers (Fixes the issue)
        if not self.logger.hasHandlers():
            # Define log format
            log_format = '%(asctime)s [%(levelname)s:%(name)s] %(message)s'
            datefmt="%Y-%m-%d %H:%M:%S"

            formatter = logging.Formatter(log_format, datefmt=datefmt)

            # File handler for logging to a file (UTF-8 encoding)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

            # Console handler for logging to stdout
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setFormatter(formatter)
            self.logger.addHandler(stream_handler)

            # Rotate the log file if it exceeds the size limit (10MB)
            log_size = 10 * 1024 * 1024  # 10MB
            if os.path.exists(log_file) and os.path.getsize(log_file) > log_size:
                self.rotate_log(log_file)

    def rotate_log(self, log_file: str):
        """
        Rotates the log file when it exceeds the predefined size limit.

        :param log_file: Path to the log file that needs to be rotated.
        """
        backup_log_file = f"{log_file}.{self._get_timestamp()}"
        if os.path.exists(log_file):
            os.rename(log_file, backup_log_file)
            self.logger.info(f"Previous log file has been renamed to {backup_log_file}")

    def _get_timestamp(self):
        """
        Generates a timestamp string for log file rotation.

        :return: Timestamp string in 'YYYYMMDDHHMMSS' format.
        """
        from datetime import datetime
        return datetime.now().strftime('%Y%m%d%H%M%S')

    def debug(self, msg: str):
        """Logs a message at DEBUG level."""
        self.logger.debug(msg)

    def info(self, msg: str):
        """Logs a message at INFO level."""
        self.logger.info(msg)

    def warning(self, msg: str):
        """Logs a message at WARNING level."""
        self.logger.warning(msg)

    def error(self, msg: str):
        """Logs a message at ERROR level."""
        self.logger.error(msg)

    def critical(self, msg: str):
        """Logs a message at CRITICAL level."""
        self.logger.critical(msg)
