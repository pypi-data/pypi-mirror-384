import logging
from logging.handlers import RotatingFileHandler


def setup_logger(name: str, log_file: str = None, level: int = logging.DEBUG, max_bytes: int = 10485760,
                 backup_count: int = 5) -> logging.Logger:
    """
    Set up a logger with the specified name and level.
    Log to both console and file (with rotation if log_file is provided).

    :param name: Name of the logger.
    :param log_file: Path to the log file. If None, logs only to console.
    :param level: Logging level.
    :param max_bytes: Maximum size of log file before rotation (default 10MB).
    :param backup_count: Number of backup files to keep (default 5).
    :return: Configured logger.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.hasHandlers():
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        if log_file:
            file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def clean_up_logger(logger: logging.Logger):
    """
    Remove and close all handlers for the logger.

    :param logger: Logger instance.
    """
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()