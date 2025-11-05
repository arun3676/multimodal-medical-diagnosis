"""
Fresh W&B Monitor - Creates a new run for each server start
Clean, simple monitoring for multimodal medical diagnosis
"""

import os
import wandb
from typing import Dict, Any, Optional
import logging
import datetime
from app.core.cost_tracker import get_cost_tracker, get_system_tracker
from app.config import settings

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
        """Initialize W&B with proper error handling"""
        try:
            # Check if API key is available
            if not settings.WANDB_API_KEY:
                logger.warning("W&B API key not found - monitoring disabled")
                self.enabled = False
                return
            
            # Login to W&B
            wandb.login(key=settings.WANDB_API_KEY)
            logger.info("✅ W&B authentication successful")
            
        except Exception as e:
            logger.warning(f"W&B initialization failed: {e}")
            self.enabled = False
    
    def start_fresh_run(self):
        """Start a completely new run for this server session"""
        if not self.enabled:
            logger.info("📊 W&B monitoring disabled")
            return False
        
        try:
            # Generate unique session ID
            self.session_id = f"session-{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Finish any existing run
            if self.run is not None:
                wandb.finish()
            
            # Start fresh run
            self.run = wandb.init(
                project=self.project_name,
                name=self.session_id,
                tags=["medical-diagnosis", "flask-app", settings.FLASK_ENV],
                config={
                    "environment": settings.FLASK_ENV,
                    "model_cache_enabled": settings.MODEL_CACHE_ENABLED,
                    "server_start_time": datetime.datetime.now().isoformat(),
                    "python_version": os.sys.version,
                    "working_directory": os.getcwd()
                },
                reinit=True  # Allow reinitialization
            )
            
            logger.info(f"🎯 Fresh W&B run started: {self.session_id}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to start fresh W&B run: {e}")
            self.enabled = False
            return False
    
    def log_prediction(self, 
                      model_name: str,
                      prediction: str,
                      confidence: float,
                      processing_time: float,
                      image_metadata: Dict[str, Any] = None):
        """Log a prediction to the current run"""
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
            
            wandb.log(log_data)
            logger.debug(f"📊 Logged prediction to {self.session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to log prediction to W&B: {e}")
    
    def log_model_performance(self, 
                             model_name: str,
                             metrics: Dict[str, float],
                             step: int = None):
        """Log model performance metrics"""
        if not self.enabled or not self.run:
            return
            
        try:
            log_data = {f"{model_name}/{k}": v for k, v in metrics.items()}
            log_data["session_id"] = self.session_id
            
            if step is not None:
                wandb.log(log_data, step=step)
            else:
                wandb.log(log_data)
                
            logger.debug(f"📊 Logged performance metrics to {self.session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to log model performance to W&B: {e}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log error occurrence"""
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
            
            wandb.log(log_data)
            logger.debug(f"📊 Logged error to {self.session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to log error to W&B: {e}")
    
    def log_system_metrics(self, metrics: Dict[str, Any]):
        """Log system performance metrics"""
        if not self.enabled or not self.run:
            return
            
        try:
            log_data = {"system/" + k: v for k, v in metrics.items()}
            log_data["session_id"] = self.session_id
            wandb.log(log_data)
            logger.debug(f"📊 Logged system metrics to {self.session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to log system metrics to W&B: {e}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log error occurrence"""
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
            
            wandb.log(log_data)
            logger.debug(f"📊 Logged error to {self.session_id}")
            
        except Exception as e:
            logger.warning(f"Failed to log error to W&B: {e}")
    
    def log_api_cost(self, provider: str, model: str, cost: float, execution_time: float, tokens: Dict[str, int]):
        """Log API cost and performance"""
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
            wandb.log(log_data)
            logger.debug(f"💰 Logged API cost: {provider} - ${cost:.6f}")
        except Exception as e:
            logger.warning(f"Failed to log API cost to W&B: {e}")
    
    def log_system_health(self):
        """Log system health metrics (CPU, GPU, Memory)"""
        if not self.enabled or not self.run:
            return
        
        try:
            system_tracker = get_system_tracker()
            metrics = system_tracker.get_wandb_metrics()
            metrics["session_id"] = self.session_id
            wandb.log(metrics)
            logger.debug(f"🖥️ Logged system health metrics")
        except Exception as e:
            logger.warning(f"Failed to log system health to W&B: {e}")
    
    def log_cost_summary(self):
        """Log cost and performance summary"""
        if not self.enabled or not self.run:
            return
        
        try:
            cost_tracker = get_cost_tracker()
            metrics = cost_tracker.get_wandb_metrics()
            metrics["session_id"] = self.session_id
            wandb.log(metrics)
            logger.info(f"💰 Cost Summary: {cost_tracker.get_all_summary()}")
        except Exception as e:
            logger.warning(f"Failed to log cost summary to W&B: {e}")
    
    def finish_run(self):
        """Finish the current W&B run"""
        if self.enabled and self.run:
            try:
                wandb.finish()
                logger.info(f"✅ W&B run finished: {self.session_id}")
                self.run = None
                self.session_id = None
            except Exception as e:
                logger.warning(f"Failed to finish W&B run: {e}")
    
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
