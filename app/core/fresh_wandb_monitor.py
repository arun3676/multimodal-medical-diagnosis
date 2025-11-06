"""
Fresh W&B Monitor - Creates a new run for each server start
Clean, simple monitoring for multimodal medical diagnosis
"""

import os
import sys
import logging
import datetime
from typing import Dict, Any, Optional
from app.core.cost_tracker import get_cost_tracker, get_system_tracker
from app.config import settings

# 🛡️ PREEMPTIVE W&B ERROR SUPPRESSION - MUST BE FIRST
# This prevents ALL wandb socket/protocol errors before any imports
os.environ["WANDB_SILENT"] = "true"
os.environ["WANDB_CONSOLE"] = "off"
os.environ["WANDB_MODE"] = "offline"  # 🎯 CRITICAL: Prevents ALL socket errors
os.environ["WANDB_RUN_ID"] = "offline-run"
os.environ["WANDB_DIR"] = "/tmp/wandb"
os.environ["WANDB_SERVICE_WAIT"] = "300"
os.environ["WANDB_AGENT_DISABLE_FLAKING"] = "true"
os.environ["WANDB_DISABLE_CODE"] = "true"
os.environ["WANDB_DISABLE_STATS"] = "true"
os.environ["WANDB_DISABLE_GIT"] = "true"
os.environ["WANDB_ARTIFACTS_DISABLED"] = "true"
os.environ["WANDB_ENSURE_DIR"] = "true"
os.environ["WANDB_DISABLE_SERVICE"] = "true"  # 🛡️ EXTRA: Disable service completely
os.environ["WANDB_DISABLE_SYMLINKS"] = "true"  # Prevents symlink errors
os.environ["WANDB_RUN_GROUP"] = "offline"  # Prevents group conflicts

# 🛡️ GLOBAL STDERR REDIRECT FOR W&B ASSERTION ERRORS
import io
import contextlib
from threading import Lock

class AssertionErrorSuppressor:
    """Global stderr redirector to suppress wandb assertion errors"""
    
    def __init__(self):
        self.original_stderr = sys.stderr
        self.suppressed_stderr = io.StringIO()
        self.lock = Lock()
        self.active = False
    
    def start_suppression(self):
        """Start suppressing wandb assertion errors"""
        with self.lock:
            if not self.active:
                sys.stderr = self.suppressed_stderr
                self.active = True
    
    def stop_suppression(self):
        """Stop suppressing and restore original stderr"""
        with self.lock:
            if self.active:
                sys.stderr = self.original_stderr
                # Clear any captured assertion errors
                captured = self.suppressed_stderr.getvalue()
                if "AssertionError" in captured:
                    logging.getLogger(__name__).debug("🛡️ W&B assertion errors captured and destroyed")
                self.suppressed_stderr.seek(0)
                self.suppressed_stderr.truncate(0)
                self.active = False
    
    def get_suppressed_count(self):
        """Count suppressed assertion errors"""
        captured = self.suppressed_stderr.getvalue()
        return captured.count("AssertionError")

# Global suppressor instance
_assertion_suppressor = AssertionErrorSuppressor()

# Import wandb with error suppression
try:
    with contextlib.redirect_stderr(io.StringIO()):
        import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False
    wandb = None

logger = logging.getLogger(__name__)

class FreshWandBMonitor:
    """Fresh W&B monitoring that creates a new run for each server session"""
    
    def __init__(self, project_name: str = "multimodal-medical-diagnosis"):
        self.project_name = project_name
        self.enabled = settings.WANDB_ENABLED
        self.run = None
        self.session_id = None
        
        if self.enabled:
            self._initialize_wandb()
    
    def _initialize_wandb(self):
        """Initialize W&B with robust error handling and socket protocol fixes"""
        try:
            # Check if wandb is available
            if not WANDB_AVAILABLE:
                logger.info("📊 W&B not installed - monitoring disabled")
                self.enabled = False
                return
            
            # Check if API key is available
            if not settings.WANDB_API_KEY:
                logger.info("📊 W&B API key not found - monitoring disabled")
                self.enabled = False
                return
            
            # 🛡️ START ASSERTION ERROR SUPPRESSION
            _assertion_suppressor.start_suppression()
            
            try:
                # Try to login with error suppression
                wandb.login(key=settings.WANDB_API_KEY, relogin=True, force=True)
                logger.info("✅ W&B authentication successful (offline mode)")
            except Exception as login_error:
                logger.info(f"📊 W&B login skipped: {login_error}")
                # Still continue - offline mode might work
            finally:
                # 🛡️ STOP ASSERTION ERROR SUPPRESSION
                _assertion_suppressor.stop_suppression()
            
        except Exception as e:
            logger.info(f"📊 W&B initialization skipped: {e}")
            self.enabled = False
    
    def start_fresh_run(self):
        """Start a completely new run for this server session with robust error handling"""
        if not self.enabled:
            logger.info("📊 W&B monitoring disabled")
            return False
        
        try:
            # Generate unique session ID
            self.session_id = f"session-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Finish any existing run quietly
            if self.run is not None:
                try:
                    wandb.finish(quiet=True)
                except:
                    pass
            
            # 🛡️ START ASSERTION ERROR SUPPRESSION
            _assertion_suppressor.start_suppression()
            
            try:
                # Start fresh run with comprehensive error suppression
                self.run = wandb.init(
                    project=self.project_name,
                    name=self.session_id,
                    tags=["medical-diagnosis", "flask-app", settings.FLASK_ENV],
                    config={
                        "environment": settings.FLASK_ENV,
                        "model_cache_enabled": settings.MODEL_CACHE_ENABLED,
                        "server_start_time": datetime.datetime.now().isoformat(),
                        "python_version": sys.version,
                        "working_directory": os.getcwd()
                    },
                    reinit=True,
                    mode="offline",  # 🎯 CRITICAL: Prevents socket protocol errors
                    settings=wandb.Settings(
                        silent=True,
                        console="off",
                        _disable_stats=True,
                        _disable_meta=True,
                        _disable_service=True,  # 🛡️ Prevents service socket errors
                        _disable_job=True,      # Prevents job tracking errors
                        _disable_code=True,     # Prevents code tracking errors
                        _disable_artifacts=True # Prevents artifact errors
                    )
                )
                
                logger.info(f"🎯 Fresh W&B run started: {self.session_id} (offline mode)")
                return True
                
            finally:
                # 🛡️ STOP ASSERTION ERROR SUPPRESSION
                _assertion_suppressor.stop_suppression()
            
        except Exception as e:
            logger.info(f"📊 W&B run skipped: {e}")
            self.enabled = False
            return False
    
    def log_prediction(self, 
                      model_name: str,
                      prediction: str,
                      confidence: float,
                      processing_time: float,
                      image_metadata: Dict[str, Any] = None):
        """Log a prediction to the current run with error suppression"""
        if not self.enabled or not self.run:
            return
            
        try:
            log_data = {
                f"{model_name}/prediction": prediction,
                f"{model_name}/confidence": confidence,
                f"{model_name}/processing_time": processing_time,
                "session_id": self.session_id
            }
            
            if image_metadata:
                log_data.update({
                    f"{model_name}/image_size": f"{image_metadata.get('width', 0)}x{image_metadata.get('height', 0)}",
                    f"{model_name}/image_format": image_metadata.get('format', 'unknown')
                })
            
            # 🛡️ USE GLOBAL ASSERTION ERROR SUPPRESSION
            _assertion_suppressor.start_suppression()
            
            try:
                wandb.log(log_data)
                logger.debug(f"📊 Logged prediction to {self.session_id}")
            finally:
                _assertion_suppressor.stop_suppression()
            
        except Exception as e:
            pass  # Silently skip W&B logging errors
    
    def log_model_performance(self, 
                             model_name: str,
                             metrics: Dict[str, float],
                             step: int = None):
        """Log model performance metrics with error suppression"""
        if not self.enabled or not self.run:
            return
            
        try:
            log_data = {f"{model_name}/{k}": v for k, v in metrics.items()}
            log_data["session_id"] = self.session_id
            
            # 🛡️ USE GLOBAL ASSERTION ERROR SUPPRESSION
            _assertion_suppressor.start_suppression()
            
            try:
                if step is not None:
                    wandb.log(log_data, step=step)
                else:
                    wandb.log(log_data)
                logger.debug(f"📊 Logged performance metrics to {self.session_id}")
            finally:
                _assertion_suppressor.stop_suppression()
                
        except Exception as e:
            pass  # Silently skip W&B logging errors
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log error occurrence with error suppression"""
        if not self.enabled or not self.run:
            return
            
        try:
            log_data = {
                "errors/type": error_type,
                "errors/count": 1,
                "session_id": self.session_id
            }
            
            if context:
                log_data.update({"errors/context_" + k: v for k, v in context.items()})
            
            # 🛡️ USE GLOBAL ASSERTION ERROR SUPPRESSION
            _assertion_suppressor.start_suppression()
            
            try:
                wandb.log(log_data)
                logger.debug(f"📊 Logged error to {self.session_id}")
            finally:
                _assertion_suppressor.stop_suppression()
            
        except Exception as e:
            pass  # Silently skip W&B logging errors
    
    def log_system_metrics(self, metrics: Dict[str, Any]):
        """Log system performance metrics with error suppression"""
        if not self.enabled or not self.run:
            return
            
        try:
            log_data = {"system/" + k: v for k, v in metrics.items()}
            log_data["session_id"] = self.session_id
            
            # 🛡️ USE GLOBAL ASSERTION ERROR SUPPRESSION
            _assertion_suppressor.start_suppression()
            
            try:
                wandb.log(log_data)
                logger.debug(f"📊 Logged system metrics to {self.session_id}")
            finally:
                _assertion_suppressor.stop_suppression()
            
        except Exception as e:
            pass  # Silently skip W&B logging errors
    
    def log_api_cost(self, provider: str, model: str, cost: float, execution_time: float, tokens: Dict[str, int]):
        """Log API cost and performance with error suppression"""
        if not self.enabled or not self.run:
            return
        
        try:
            log_data = {
                f"costs/{provider}/cost_usd": cost,
                f"costs/{provider}/execution_time_seconds": execution_time,
                f"costs/{provider}/input_tokens": tokens.get("input", 0),
                f"costs/{provider}/output_tokens": tokens.get("output", 0),
                "session_id": self.session_id
            }
            
            # 🛡️ USE GLOBAL ASSERTION ERROR SUPPRESSION
            _assertion_suppressor.start_suppression()
            
            try:
                wandb.log(log_data)
                logger.debug(f"💰 Logged API cost: {provider} - ${cost:.6f}")
            finally:
                _assertion_suppressor.stop_suppression()
                
        except Exception as e:
            pass  # Silently skip W&B logging errors
    
    def log_system_health(self):
        """Log system health metrics (CPU, GPU, Memory) with error suppression"""
        if not self.enabled or not self.run:
            return
        
        try:
            system_tracker = get_system_tracker()
            metrics = system_tracker.get_wandb_metrics()
            metrics["session_id"] = self.session_id
            
            # 🛡️ USE GLOBAL ASSERTION ERROR SUPPRESSION
            _assertion_suppressor.start_suppression()
            
            try:
                wandb.log(metrics)
                logger.debug(f"🖥️ Logged system health metrics")
            finally:
                _assertion_suppressor.stop_suppression()
                
        except Exception as e:
            pass  # Silently skip W&B logging errors
    
    def log_cost_summary(self):
        """Log cost and performance summary with error suppression"""
        if not self.enabled or not self.run:
            return
        
        try:
            cost_tracker = get_cost_tracker()
            metrics = cost_tracker.get_wandb_metrics()
            metrics["session_id"] = self.session_id
            
            # 🛡️ USE GLOBAL ASSERTION ERROR SUPPRESSION
            _assertion_suppressor.start_suppression()
            
            try:
                wandb.log(metrics)
                logger.info(f"💰 Cost Summary: {cost_tracker.get_all_summary()}")
            finally:
                _assertion_suppressor.stop_suppression()
                
        except Exception as e:
            pass  # Silently skip W&B logging errors
    
    def finish_run(self):
        """Finish the current W&B run with error suppression"""
        if self.enabled and self.run:
            try:
                # 🛡️ USE GLOBAL ASSERTION ERROR SUPPRESSION
                _assertion_suppressor.start_suppression()
                
                try:
                    wandb.finish()
                    logger.info(f"✅ W&B run finished: {self.session_id}")
                finally:
                    _assertion_suppressor.stop_suppression()
                
                self.run = None
                self.session_id = None
            except Exception as e:
                pass  # Silently skip W&B finish errors
    
    def get_session_info(self):
        """Get current session information"""
        return {
            "session_id": self.session_id,
            "enabled": self.enabled,
            "project": self.project_name,
            "run_active": self.run is not None
        }

# Global monitor instance
_fresh_monitor = None

def get_fresh_monitor() -> FreshWandBMonitor:
    """Get or create the global fresh monitor instance"""
    global _fresh_monitor
    if _fresh_monitor is None:
        _fresh_monitor = FreshWandBMonitor()
    return _fresh_monitor

def start_new_session():
    """Start a fresh monitoring session - call this when server starts"""
    monitor = get_fresh_monitor()
    return monitor.start_fresh_run()
