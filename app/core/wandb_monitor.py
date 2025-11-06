"""
Weights & Biases monitoring configuration for multimodal medical diagnosis
Simple, free-tier friendly monitoring for model performance and metrics
"""

import os
import wandb
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class WandBMonitor:
    """Simple W&B monitoring wrapper for medical diagnosis system"""
    
    def __init__(self, project_name: str = "multimodal-medical-diagnosis"):
        self.project_name = project_name
        self.enabled = os.getenv("WANDB_ENABLED", "false").lower() == "true"
        self.run = None
        
        if self.enabled:
            try:
                wandb.login(key=os.getenv("WANDB_API_KEY"))
                logger.info("W&B initialized successfully")
            except Exception as e:
                logger.warning(f"W&B initialization failed: {e}")
                self.enabled = False
    
    def start_run(self, run_name: str = None, tags: list = None):
        """Start a new W&B run"""
        if not self.enabled:
            return
            
        try:
            self.run = wandb.init(
                project=self.project_name,
                name=run_name,
                tags=tags or ["medical-diagnosis"],
                config={
                    "environment": os.getenv("FLASK_ENV", "development"),
                    "model_cache_enabled": os.getenv("MODEL_CACHE_ENABLED", "true").lower() == "true"
                }
            )
            logger.info(f"W&B run started: {self.run.name}")
        except Exception as e:
            logger.warning(f"Failed to start W&B run: {e}")
    
    def log_prediction(self, 
                      model_name: str,
                      prediction: str,
                      confidence: float,
                      processing_time: float,
                      image_metadata: Dict[str, Any] = None):
        """Log a single prediction to W&B"""
        if not self.enabled or not self.run:
            return
            
        try:
            log_data = {
                f"{model_name}/prediction": prediction,
                f"{model_name}/confidence": confidence,
                f"{model_name}/processing_time": processing_time
            }
            
            if image_metadata:
                log_data.update({
                    f"{model_name}/image_size": f"{image_metadata.get('width', 0)}x{image_metadata.get('height', 0)}",
                    f"{model_name}/image_format": image_metadata.get('format', 'unknown')
                })
            
            wandb.log(log_data)
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
            if step is not None:
                wandb.log(log_data, step=step)
            else:
                wandb.log(log_data)
        except Exception as e:
            logger.warning(f"Failed to log model performance to W&B: {e}")
    
    def log_system_metrics(self, metrics: Dict[str, Any]):
        """Log system performance metrics"""
        if not self.enabled or not self.run:
            return
            
        try:
            wandb.log({"system/" + k: v for k, v in metrics.items()})
        except Exception as e:
            logger.warning(f"Failed to log system metrics to W&B: {e}")
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log error occurrence"""
        if not self.enabled or not self.run:
            return
            
        try:
            log_data = {
                "errors/type": error_type,
                "errors/count": 1
            }
            
            if context:
                log_data.update({"errors/context_" + k: v for k, v in context.items()})
            
            wandb.log(log_data)
        except Exception as e:
            logger.warning(f"Failed to log error to W&B: {e}")
    
    def finish_run(self):
        """Finish the current W&B run"""
        if self.enabled and self.run:
            try:
                wandb.finish()
                logger.info("W&B run finished")
                self.run = None
            except Exception as e:
                logger.warning(f"Failed to finish W&B run: {e}")

# Global monitor instance
monitor = WandBMonitor()

def init_monitoring():
    """Initialize monitoring for the application"""
    return monitor

def get_monitor():
    """Get the global monitor instance"""
    return monitor
