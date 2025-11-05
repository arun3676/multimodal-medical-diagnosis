"""Demo monitoring that shows the metrics without external dependencies."""

import logging
import json
from datetime import datetime
from typing import Dict, Any

class DemoMonitoringHandler(logging.Handler):
    """Demo handler that shows what would be sent to a monitoring platform."""
    
    def __init__(self):
        super().__init__()
        self.logs_sent = []
        
    def emit(self, record: logging.LogRecord):
        """Store the log record to demonstrate monitoring."""
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
            
            # Store the log for demo purposes
            self.logs_sent.append(log_data)
            
            # Print a summary of what would be sent to monitoring
            if log_data.get("component") == "model_monitoring":
                print(f"\n📊 MODEL METRICS WOULD BE SENT:")
                print(f"   Provider: {log_data.get('metrics', {}).get('model_provider', 'unknown')}")
                print(f"   Model: {log_data.get('metrics', {}).get('model_name', 'unknown')}")
                print(f"   Duration: {log_data.get('metrics', {}).get('analysis_duration_ms', 0)}ms")
                print(f"   Success: {log_data.get('metrics', {}).get('success', False)}")
                print(f"   Findings: {log_data.get('metrics', {}).get('findings_count', 0)}")
                
            elif log_data.get("component") == "api_monitoring":
                print(f"\n🌐 API METRICS WOULD BE SENT:")
                print(f"   Endpoint: {log_data.get('metrics', {}).get('api_endpoint', 'unknown')}")
                print(f"   Status: {log_data.get('metrics', {}).get('response_status', 0)}")
                print(f"   Response Time: {log_data.get('metrics', {}).get('response_time_ms', 0)}ms")
                print(f"   Error: {log_data.get('metrics', {}).get('is_error', False)}")
                
        except Exception as e:
            print(f"Error in demo monitoring: {e}")
    
    def get_summary(self):
        """Return a summary of all metrics collected."""
        model_logs = [log for log in self.logs_sent if log.get("component") == "model_monitoring"]
        api_logs = [log for log in self.logs_sent if log.get("component") == "api_monitoring"]
        
        return {
            "total_logs": len(self.logs_sent),
            "model_calls": len(model_logs),
            "api_calls": len(api_logs),
            "model_logs": model_logs,
            "api_logs": api_logs
        }

def setup_demo_logging(log_level: str = "INFO"):
    """Configure demo logging that shows metrics without external services."""
    
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Demo monitoring handler
    demo_handler = DemoMonitoringHandler()
    from app.core.logging_config import JsonFormatter
    demo_handler.setFormatter(JsonFormatter())
    logger.addHandler(demo_handler)
    
    # Suppress noisy loggers
    logging.getLogger("werkzeug").setLevel("WARNING")
    logging.getLogger("urllib3").setLevel("WARNING")
    logging.getLogger("httpx").setLevel("WARNING")
    
    return logger, demo_handler
