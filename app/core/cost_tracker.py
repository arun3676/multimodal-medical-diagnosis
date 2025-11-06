"""
API Cost & Performance Tracker
Tracks costs, execution time, and resource utilization per API provider
Simple, easy-to-understand metrics for W&B dashboard
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import psutil
import json

logger = logging.getLogger(__name__)

# API Pricing (as of 2024)
# OpenAI GPT-4o-mini
OPENAI_PRICING = {
    "gpt-4o-mini": {
        "input": 0.00015,  # per 1K tokens
        "output": 0.0006,  # per 1K tokens
    }
}

# Gemini pricing
GEMINI_PRICING = {
    "gemini-2.5-flash": {
        "input": 0.000075,  # per 1K tokens
        "output": 0.0003,   # per 1K tokens
    }
}

class CostTracker:
    """Track API costs and performance metrics"""
    
    def __init__(self):
        self.costs = {}  # {provider: {date: cost}}
        self.execution_times = {}  # {provider: [times]}
        self.api_calls = {}  # {provider: count}
        self.errors = {}  # {provider: count}
        
    def calculate_openai_cost(self, input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini") -> float:
        """Calculate OpenAI API cost"""
        try:
            pricing = OPENAI_PRICING.get(model, OPENAI_PRICING["gpt-4o-mini"])
            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            return round(input_cost + output_cost, 6)
        except Exception as e:
            logger.warning(f"Failed to calculate OpenAI cost: {e}")
            return 0.0
    
    def calculate_gemini_cost(self, input_tokens: int, output_tokens: int, model: str = "gemini-2.5-flash") -> float:
        """Calculate Gemini API cost"""
        try:
            pricing = GEMINI_PRICING.get(model, GEMINI_PRICING["gemini-2.5-flash"])
            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            return round(input_cost + output_cost, 6)
        except Exception as e:
            logger.warning(f"Failed to calculate Gemini cost: {e}")
            return 0.0
    
    def log_api_call(self, 
                    provider: str,
                    model: str,
                    input_tokens: int,
                    output_tokens: int,
                    execution_time: float,
                    success: bool = True):
        """Log an API call with cost and performance metrics"""
        
        # Calculate cost
        if provider.lower() == "openai":
            cost = self.calculate_openai_cost(input_tokens, output_tokens, model)
        elif provider.lower() == "gemini":
            cost = self.calculate_gemini_cost(input_tokens, output_tokens, model)
        else:
            cost = 0.0
        
        # Initialize provider tracking if needed
        if provider not in self.costs:
            self.costs[provider] = {}
            self.execution_times[provider] = []
            self.api_calls[provider] = 0
            self.errors[provider] = 0
        
        # Track metrics
        date_key = datetime.now().strftime("%Y-%m-%d")
        if date_key not in self.costs[provider]:
            self.costs[provider][date_key] = 0.0
        
        self.costs[provider][date_key] += cost
        self.execution_times[provider].append(execution_time)
        self.api_calls[provider] += 1
        
        if not success:
            self.errors[provider] += 1
        
        logger.info(f"📊 API Call: {provider}/{model} | Cost: ${cost:.6f} | Time: {execution_time:.2f}s")
        
        return {
            "provider": provider,
            "model": model,
            "cost": cost,
            "execution_time": execution_time,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "success": success
        }
    
    def get_provider_summary(self, provider: str) -> Dict[str, Any]:
        """Get summary statistics for a provider"""
        if provider not in self.api_calls:
            return {}
        
        times = self.execution_times.get(provider, [])
        total_cost = sum(self.costs.get(provider, {}).values())
        
        return {
            "provider": provider,
            "total_calls": self.api_calls[provider],
            "total_errors": self.errors[provider],
            "success_rate": ((self.api_calls[provider] - self.errors[provider]) / self.api_calls[provider] * 100) if self.api_calls[provider] > 0 else 0,
            "total_cost": round(total_cost, 6),
            "avg_execution_time": round(sum(times) / len(times), 2) if times else 0,
            "min_execution_time": round(min(times), 2) if times else 0,
            "max_execution_time": round(max(times), 2) if times else 0,
            "total_execution_time": round(sum(times), 2) if times else 0
        }
    
    def get_all_summary(self) -> Dict[str, Any]:
        """Get summary for all providers"""
        summary = {}
        total_cost = 0.0
        total_calls = 0
        
        for provider in self.api_calls.keys():
            provider_summary = self.get_provider_summary(provider)
            summary[provider] = provider_summary
            total_cost += provider_summary.get("total_cost", 0)
            total_calls += provider_summary.get("total_calls", 0)
        
        summary["total"] = {
            "total_calls": total_calls,
            "total_cost": round(total_cost, 6),
            "providers": list(self.api_calls.keys())
        }
        
        return summary
    
    def get_wandb_metrics(self) -> Dict[str, Any]:
        """Get metrics formatted for W&B logging"""
        summary = self.get_all_summary()
        metrics = {}
        
        # Overall metrics
        metrics["costs/total_cost_usd"] = summary.get("total", {}).get("total_cost", 0)
        metrics["costs/total_api_calls"] = summary.get("total", {}).get("total_calls", 0)
        
        # Per-provider metrics
        for provider, data in summary.items():
            if provider == "total":
                continue
            
            metrics[f"costs/{provider}/total_cost_usd"] = data.get("total_cost", 0)
            metrics[f"costs/{provider}/api_calls"] = data.get("total_calls", 0)
            metrics[f"costs/{provider}/success_rate_percent"] = data.get("success_rate", 0)
            metrics[f"performance/{provider}/avg_execution_time_seconds"] = data.get("avg_execution_time", 0)
            metrics[f"performance/{provider}/min_execution_time_seconds"] = data.get("min_execution_time", 0)
            metrics[f"performance/{provider}/max_execution_time_seconds"] = data.get("max_execution_time", 0)
        
        return metrics

class SystemMetricsTracker:
    """Track CPU, GPU, and memory utilization"""
    
    @staticmethod
    def get_cpu_usage() -> float:
        """Get current CPU usage percentage"""
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.warning(f"Failed to get CPU usage: {e}")
            return 0.0
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get memory usage statistics"""
        try:
            memory = psutil.virtual_memory()
            return {
                "total_gb": round(memory.total / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent
            }
        except Exception as e:
            logger.warning(f"Failed to get memory usage: {e}")
            return {}
    
    @staticmethod
    def get_gpu_usage() -> Dict[str, Any]:
        """Get GPU usage if available"""
        try:
            import torch
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                gpu_stats = {}
                
                for i in range(device_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                    gpu_allocated = torch.cuda.memory_allocated(i) / (1024**3)
                    gpu_reserved = torch.cuda.memory_reserved(i) / (1024**3)
                    
                    gpu_stats[f"gpu_{i}"] = {
                        "name": gpu_name,
                        "total_memory_gb": round(gpu_memory, 2),
                        "allocated_memory_gb": round(gpu_allocated, 2),
                        "reserved_memory_gb": round(gpu_reserved, 2),
                        "percent_used": round((gpu_allocated / gpu_memory * 100), 2) if gpu_memory > 0 else 0
                    }
                
                return gpu_stats
            else:
                return {"status": "No GPU available"}
        except Exception as e:
            logger.warning(f"Failed to get GPU usage: {e}")
            return {"status": "GPU tracking unavailable"}
    
    @staticmethod
    def get_system_summary() -> Dict[str, Any]:
        """Get complete system metrics summary"""
        return {
            "cpu_usage_percent": SystemMetricsTracker.get_cpu_usage(),
            "memory": SystemMetricsTracker.get_memory_usage(),
            "gpu": SystemMetricsTracker.get_gpu_usage(),
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def get_wandb_metrics() -> Dict[str, float]:
        """Get system metrics formatted for W&B logging"""
        summary = SystemMetricsTracker.get_system_summary()
        metrics = {}
        
        # CPU metrics
        metrics["system/cpu_usage_percent"] = summary.get("cpu_usage_percent", 0)
        
        # Memory metrics
        memory = summary.get("memory", {})
        if memory:
            metrics["system/memory_used_gb"] = memory.get("used_gb", 0)
            metrics["system/memory_available_gb"] = memory.get("available_gb", 0)
            metrics["system/memory_percent_used"] = memory.get("percent_used", 0)
        
        # GPU metrics
        gpu = summary.get("gpu", {})
        if gpu and "status" not in gpu:
            for gpu_id, gpu_data in gpu.items():
                metrics[f"system/{gpu_id}/memory_allocated_gb"] = gpu_data.get("allocated_memory_gb", 0)
                metrics[f"system/{gpu_id}/memory_percent_used"] = gpu_data.get("percent_used", 0)
        
        return metrics

# Global instances
_cost_tracker = None
_system_tracker = None

def get_cost_tracker() -> CostTracker:
    """Get or create global cost tracker"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker

def get_system_tracker() -> SystemMetricsTracker:
    """Get system metrics tracker"""
    return SystemMetricsTracker()
