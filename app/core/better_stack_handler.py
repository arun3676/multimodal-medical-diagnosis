import logging
import json
import os
import httpx
from typing import Dict, Any
from datetime import datetime

class BetterStackHandler(logging.Handler):
    """Custom log handler to send logs directly to Better Stack."""
    
    def __init__(self, source_token: str):
        super().__init__()
        self.source_token = source_token
        # Better Stack Logtail API endpoint
        self.url = "https://in.logtail.com"
        self.http_client = httpx.Client(timeout=5.0)
        
    def emit(self, record: logging.LogRecord):
        """Send a log record to Better Stack."""
        try:
            # Format the log message
            log_entry = self.format(record)
            
            # Parse the JSON log entry
            if isinstance(log_entry, str):
                try:
                    log_data = json.loads(log_entry)
                except json.JSONDecodeError:
                    log_data = {
                        "message": log_entry,
                        "level": record.levelname,
                        "timestamp": datetime.utcnow().isoformat()
                    }
            else:
                log_data = log_entry
            
            # Better Stack Logtail expects array of logs
            payload = [log_data]
            
            # Send to Better Stack Logtail API
            response = self.http_client.post(
                self.url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.source_token}",
                    "Content-Type": "application/json"
                }
            )
            
            # Debug: print response status
            if response.status_code != 200:
                print(f"Better Stack Error: {response.status_code} - {response.text}")
            else:
                print(f"✅ Log sent to Better Stack")
                
        except Exception as e:
            print(f"Error sending log to Better Stack: {e}")
    
    def close(self):
        """Clean up resources."""
        self.http_client.close()
        super().close()

def setup_better_stack_logging(source_token: str, log_level: str = "INFO"):
    """Configure logging to send to Better Stack while keeping console logs."""
    
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Clear existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # 1. Keep console handler for local development
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 2. Add Better Stack handler for production
    if os.getenv("VERCEL") == "1" or os.getenv("BETTER_STACK_ENABLED") == "true":
        from app.core.logging_config import JsonFormatter
        
        better_stack_handler = BetterStackHandler(source_token)
        better_stack_handler.setFormatter(JsonFormatter())
        logger.addHandler(better_stack_handler)
        
        logger.info("Better Stack logging initialized", extra={"component": "logging_setup"})
    
    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel("WARNING")
    logging.getLogger("urllib3").setLevel("WARNING")
    logging.getLogger("httpx").setLevel("WARNING")
    
    return logger
