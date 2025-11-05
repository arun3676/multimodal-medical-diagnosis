import logging
import json
import os
from logging import Formatter, LogRecord, getLogger, StreamHandler
from logging.handlers import RotatingFileHandler
from datetime import datetime
from app.config import settings

class JsonFormatter(Formatter):
    """Formats log records as a JSON string for structured logging."""
    
    def format(self, record: LogRecord) -> str:
        log_object = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger_name": record.name,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields passed to the logger
        # These will be our monitoring metrics
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info']:
                extra_fields[key] = value
        
        if extra_fields:
            log_object["metrics"] = extra_fields
            
        return json.dumps(log_object)

def setup_logging() -> None:
    """Initializes and configures the root logger for the application."""
    logger = getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Clear existing handlers to prevent duplicate logs
    if logger.hasHandlers():
        logger.handlers.clear()
        
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create file handler with JSON formatter
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "app.log"),
        maxBytes=1024 * 1024 * 5,  # 5 MB
        backupCount=5,
    )
    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)
    
    # Create console handler with a simpler formatter for readability
    console_handler = StreamHandler()
    console_formatter = Formatter("%(asctime)s %(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel("WARNING")
    logging.getLogger("urllib3").setLevel("WARNING")
    logging.getLogger("wandb").setLevel("WARNING")
    
    logger.info("Logging system initialized", extra={"component": "logging_setup"})
