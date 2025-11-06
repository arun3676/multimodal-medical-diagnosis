"""
Model caching utilities for Hugging Face models.

This module provides local caching to avoid downloading models repeatedly
during testing and development.
"""
import os
import shutil
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ModelCache:
    """Manages local caching of Hugging Face models."""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize model cache.
        
        Args:
            cache_dir: Directory to store cached models. Defaults to ./models_cache
        """
        # Use environment variable for cache dir, with a fallback for local dev
        default_cache_dir = Path(__file__).parent.parent.parent / "models_cache"
        cache_dir = os.getenv('MODEL_CACHE_DIR', str(default_cache_dir))

        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Set Hugging Face cache environment variable
        os.environ['HF_HOME'] = str(self.cache_dir)
        os.environ['HUGGINGFACE_HUB_CACHE'] = str(self.cache_dir / "hub")
        
        logger.info(f"📁 Model cache directory: {self.cache_dir}")
    
    def get_cache_info(self) -> dict:
        """Get information about cached models."""
        info = {
            'cache_dir': str(self.cache_dir),
            'cache_exists': self.cache_dir.exists(),
            'cache_size_mb': 0,
            'cached_models': []
        }
        
        if self.cache_dir.exists():
            # Calculate cache size
            total_size = 0
            for file_path in self.cache_dir.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            
            info['cache_size_mb'] = round(total_size / (1024 * 1024), 2)
            
            # Find cached models
            hub_dir = self.cache_dir / "hub"
            if hub_dir.exists():
                for model_dir in hub_dir.iterdir():
                    if model_dir.is_dir() and '--' in model_dir.name:
                        model_name = model_dir.name.split('--')[-1].replace('---', '/')
                        info['cached_models'].append(model_name)
        
        return info
    
    def clear_cache(self) -> bool:
        """Clear the model cache."""
        try:
            if self.cache_dir.exists():
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(exist_ok=True)
                logger.info("🗑️ Model cache cleared")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to clear cache: {e}")
            return False
    
    def is_model_cached(self, model_name: str) -> bool:
        """Check if a model is cached."""
        hub_dir = self.cache_dir / "hub"
        if not hub_dir.exists():
            return False
        
        # Convert model name to cache directory name
        cache_name = model_name.replace('/', '--')
        model_cache_dir = hub_dir / f"models--{cache_name}"
        
        return model_cache_dir.exists()

# Global cache instance
_model_cache = None

def get_model_cache() -> ModelCache:
    """Get the global model cache instance."""
    global _model_cache
    if _model_cache is None:
        _model_cache = ModelCache()
    return _model_cache

def setup_model_cache():
    """Set up model cache and print info."""
    cache = get_model_cache()
    info = cache.get_cache_info()
    
    print("📦 Model Cache Information")
    print("=" * 30)
    print(f"📁 Cache directory: {info['cache_dir']}")
    print(f"💾 Cache size: {info['cache_size_mb']} MB")
    
    if info['cached_models']:
        print(f"🤖 Cached models ({len(info['cached_models'])}):")
        for model in info['cached_models']:
            print(f"   ✅ {model}")
    else:
        print("🤖 No models cached yet")
    
    print("\n💡 Models will be downloaded once and cached locally")
    print("🔄 Subsequent runs will use cached models")
    
    return cache

if __name__ == "__main__":
    setup_model_cache()
