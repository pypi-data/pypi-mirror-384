"""
Structured logging utilities for Gnosari AI Teams.
"""

import logging
import logging.config
import sys
from typing import Any, Dict, Optional
from pathlib import Path
import json
from datetime import datetime


class GnosariFormatter(logging.Formatter):
    """
    Custom formatter for Gnosari logs with structured output.
    """
    
    def __init__(self, include_context: bool = True):
        """
        Initialize the formatter.
        
        Args:
            include_context: Whether to include context information
        """
        self.include_context = include_context
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted log string
        """
        # Create base log data
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        
        # Add context if enabled
        if self.include_context:
            log_data.update({
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'thread': record.thread,
                'process': record.process,
            })
        
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability.
    """
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green  
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record with colors.
        
        Args:
            record: Log record to format
            
        Returns:
            Formatted colored log string
        """
        color = self.COLORS.get(record.levelname, self.RESET)
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Format the message
        message = f"{color}[{timestamp}] {record.levelname:8s}{self.RESET} "
        message += f"{record.name:20s} | {record.getMessage()}"
        
        # Add exception info if present
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        
        return message


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    structured: bool = False,
    colored: bool = True
) -> None:
    """
    Set up logging configuration for Gnosari.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        structured: Whether to use structured JSON logging
        colored: Whether to use colored console output
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create formatters
    if structured:
        formatter = GnosariFormatter(include_context=True)
    elif colored and sys.stdout.isatty():
        formatter = ColoredFormatter()
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        
        # Always use structured format for file logging
        file_formatter = GnosariFormatter(include_context=True)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('anthropic').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for adding contextual information to logs.
    """
    
    def __init__(self, logger: logging.Logger, **context):
        """
        Initialize log context.
        
        Args:
            logger: Logger instance
            **context: Contextual key-value pairs
        """
        self.logger = logger
        self.context = context
        self.old_context = {}
    
    def __enter__(self):
        """Enter the context and add context fields."""
        # Store old values
        for key in self.context:
            if hasattr(self.logger, key):
                self.old_context[key] = getattr(self.logger, key)
        
        # Set new values
        for key, value in self.context.items():
            setattr(self.logger, key, value)
        
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context and restore original values."""
        for key in self.context:
            if key in self.old_context:
                setattr(self.logger, key, self.old_context[key])
            else:
                delattr(self.logger, key)


def log_execution_time(func_name: str = None):
    """
    Decorator to log function execution time.
    
    Args:
        func_name: Optional custom function name for logging
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            logger = get_logger(func.__module__)
            
            name = func_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"{name} completed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{name} failed after {execution_time:.3f}s: {e}")
                raise
        
        return wrapper
    return decorator


# Default logging configuration
DEFAULT_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s:%(lineno)d - %(message)s'
        },
        'json': {
            '()': GnosariFormatter,
            'include_context': True
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        'gnosari': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False
        }
    },
    'root': {
        'level': 'WARNING',
        'handlers': ['console']
    }
}