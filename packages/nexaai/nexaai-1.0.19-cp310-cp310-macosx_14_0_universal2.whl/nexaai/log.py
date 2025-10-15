"""
Logging configuration for NexaAI bridge.

This module provides a minimal API to configure bridge-wide logging
to route into Python's logging system.
"""

import logging
import threading
from enum import IntEnum
from typing import Optional

from nexaai.binds import common_bind
from nexaai.runtime import is_initialized


class LogLevel(IntEnum):
    """Log levels matching ml_LogLevel from ml.h"""
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4


# Module-level state
_config_lock = threading.Lock()
_current_logger: Optional[logging.Logger] = None


def set_logger(logger: Optional[logging.Logger] = None, *, strict: bool = True) -> None:
    """
    Set the process-wide bridge logger.
    
    Args:
        logger: Python logger to receive bridge logs. If None, uses "nexaai.ml" logger.
        strict: If True, raises if called after runtime initialization.
                If False, attempts to set anyway (best-effort).
    
    Raises:
        RuntimeError: If strict=True and runtime is already initialized.
    """
    global _current_logger
    
    with _config_lock:
        # Check initialization state if strict mode
        if strict and is_initialized():
            raise RuntimeError(
                "Cannot configure logging after runtime initialization. "
                "Call set_logger() before creating any models, or use strict=False for best-effort."
            )
        
        # Use default logger if none provided
        if logger is None:
            logger = logging.getLogger("nexaai.ml")
        
        _current_logger = logger
        
        # Set the C callback
        common_bind.ml_set_log(_log_callback)


def _log_callback(level: int, message: str) -> None:
    """Internal callback that forwards bridge logs to Python logger."""
    if _current_logger is None:
        return
    
    # Map bridge log levels to Python logging levels
    if level == LogLevel.TRACE or level == LogLevel.DEBUG:
        _current_logger.debug(message)
    elif level == LogLevel.INFO:
        _current_logger.info(message)
    elif level == LogLevel.WARN:
        _current_logger.warning(message)
    elif level == LogLevel.ERROR:
        _current_logger.error(message)
    else:
        # Fallback for unknown levels
        _current_logger.info(f"[Level {level}] {message}")


def get_error_message(error_code: int) -> str:
    """
    Get error message string for error code.
    
    Args:
        error_code: ML error code (typically negative)
        
    Returns:
        Human-readable error message
    """
    return common_bind.ml_get_error_message(error_code)
