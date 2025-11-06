import time
import logging
from flask import request, g
from functools import wraps
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)

class APIMonitoringMiddleware:
    """Middleware to monitor API performance and health metrics."""
    
    def __init__(self, app=None):
        self.app = app
        # Smart health check tracking (in-memory, no disk I/O)
        self.health_check_count = 0
        self.health_check_failures = 0
        self.last_health_status = 'healthy'
        self.health_check_response_times = deque(maxlen=100)  # Keep last 100 only
        self.last_health_summary_time = time.time()
        self.health_summary_interval = 300  # Log summary every 5 minutes
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the middleware with Flask app."""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_request)
    
    def _before_request(self):
        """Store request start time in Flask's global context."""
        g.start_time = time.time()
        g.request_id = request.headers.get('X-Request-ID', 'unknown')
    
    def _after_request(self, response):
        """Log API performance metrics after request is processed."""
        if hasattr(g, 'start_time'):
            duration_ms = (time.time() - g.start_time) * 1000
            
            # Smart health check handling - skip logging but track metrics
            if request.path == '/health' or request.endpoint == 'main.health_check':
                self.health_check_count += 1
                self.health_check_response_times.append(duration_ms)
                
                # Only log health check failures or status changes
                current_status = 'healthy' if response.status_code == 200 else 'unhealthy'
                
                if response.status_code != 200:
                    self.health_check_failures += 1
                    logger.warning(
                        f"Health check FAILED: status={response.status_code}, time={duration_ms:.1f}ms",
                        extra={
                            "api_endpoint": "health_check",
                            "response_status": response.status_code,
                            "response_time_ms": round(duration_ms, 2),
                            "component": "health_monitoring"
                        }
                    )
                elif current_status != self.last_health_status:
                    # Status changed from unhealthy to healthy
                    logger.info(
                        f"Health check status changed: {self.last_health_status} → {current_status}",
                        extra={"component": "health_monitoring"}
                    )
                
                self.last_health_status = current_status
                
                # Periodic summary (every 5 minutes) instead of per-request logs
                current_time = time.time()
                if current_time - self.last_health_summary_time > self.health_summary_interval:
                    avg_response_time = sum(self.health_check_response_times) / len(self.health_check_response_times) if self.health_check_response_times else 0
                    logger.info(
                        f"📊 Health Check Summary: {self.health_check_count} checks, "
                        f"{self.health_check_failures} failures, "
                        f"avg response: {avg_response_time:.1f}ms, "
                        f"status: {self.last_health_status}",
                        extra={"component": "health_monitoring"}
                    )
                    self.last_health_summary_time = current_time
                    # Reset counters after summary
                    self.health_check_count = 0
                    self.health_check_failures = 0
                
                # Skip normal logging for health checks
                return response
            
            # Normal API request logging
            # Determine if this was an error response
            is_error = response.status_code >= 400
            error_type = None
            if response.status_code >= 500:
                error_type = "server_error"
            elif response.status_code >= 400:
                error_type = "client_error"
            
            log_data = {
                "api_endpoint": request.endpoint,
                "http_method": request.method,
                "response_status": response.status_code,
                "response_time_ms": round(duration_ms, 2),
                "request_id": g.request_id,
                "is_error": is_error,
                "error_type": error_type,
                "user_agent": request.headers.get('User-Agent', 'unknown'),
                "component": "api_monitoring"
            }
            
            if is_error:
                logger.error(f"API request failed: {request.method} {request.path}", 
                           extra=log_data)
            else:
                logger.info(f"API request completed: {request.method} {request.path}", 
                          extra=log_data)
        
        return response
    
    def _teardown_request(self, exception):
        """Handle any exceptions that occurred during the request."""
        if exception:
            logger.error(f"Unhandled exception in request: {request.method} {request.path}",
                        extra={
                            "api_endpoint": request.endpoint,
                            "http_method": request.method,
                            "exception_type": type(exception).__name__,
                            "request_id": getattr(g, 'request_id', 'unknown'),
                            "component": "api_monitoring"
                        }, exc_info=True)

def monitor_model_performance(func):
    """Decorator to monitor AI model performance metrics."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            success = True
            error_type = None
        except Exception as e:
            result = None
            success = False
            error_type = type(e).__name__
            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000
            
            # Extract model information if available
            model_info = getattr(result, 'model_info', {}) if result else {}
            
            log_data = {
                "function_name": func.__name__,
                "model_provider": model_info.get('provider', 'unknown'),
                "model_name": model_info.get('model', 'unknown'),
                "analysis_duration_ms": round(duration_ms, 2),
                "success": success,
                "error_type": error_type,
                "component": "model_monitoring"
            }
            
            if success and result:
                # Add quality metrics if available
                if hasattr(result, 'confidence'):
                    log_data["confidence_score"] = result.confidence
                if hasattr(result, 'findings'):
                    log_data["findings_count"] = len(result.findings) if result.findings else 0
                if hasattr(result, 'refusal_reason'):
                    log_data["model_refusal"] = True
                    log_data["refusal_reason"] = result.refusal_reason
                else:
                    log_data["model_refusal"] = False
            
            if success:
                logger.info(f"Model analysis completed: {func.__name__}", extra=log_data)
            else:
                logger.error(f"Model analysis failed: {func.__name__}", extra=log_data)
        
        return result
    
    return wrapper
