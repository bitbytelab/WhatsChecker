import sys
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "whatschecker.log"


class StreamToLogger:
    """
    Redirects print() calls to a logger as INFO while preserving console output.
    """
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.terminal = sys.__stdout__  # Keep original stdout for direct console prints

    def write(self, message):
        message = message.strip()
        if message:
            self.logger.info(message)
            self.terminal.write(message + "\n")

    def flush(self):
        self.terminal.flush()


def setup_logger(name: str = "whatschecker") -> logging.Logger:
    """
    Sets up and returns a logger instance with console and rotating file handlers.
    Also redirects `print()` to log as INFO level.
    :rtype: logging.Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(message)s')

        # Console stream handler
        stream_handler = logging.StreamHandler(sys.__stdout__)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # Rotating file handler (5MB, 3 backups)
        rotating_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
        rotating_handler.setFormatter(formatter)
        logger.addHandler(rotating_handler)

    # Redirect print() output
    sys.stdout = StreamToLogger(logger)

    return logger
