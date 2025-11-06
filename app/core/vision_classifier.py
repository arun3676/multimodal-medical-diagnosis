"""
Fine-tuned Vision Classifier for Pneumonia Detection

This module provides a self-contained classifier for pneumonia detection
using a fine-tuned deep learning model. It handles model loading, image
preprocessing, and inference with proper error handling and logging.

Based on the fine-tuning logic from the Colab notebook (Cells 14-15).
"""
import os
import logging
import numpy as np
from typing import Dict, Tuple, Optional, Any
from pathlib import Path
import time

try:
    import torch
    import torch.nn.functional as F
    from torchvision import transforms
    from PIL import Image
    from transformers import AutoModelForImageClassification, AutoImageProcessor
    from peft import PeftModel
    from .model_cache import get_model_cache
    from .fresh_wandb_monitor import get_fresh_monitor
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    IMPORT_ERROR = str(e)

logger = logging.getLogger(__name__)


class PneumoniaClassifier:
    """
    Fine-tuned pneumonia detection classifier.
    
    This class loads a fine-tuned model and performs inference on chest X-ray images
    to detect pneumonia with confidence scores.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        """
        Initialize the pneumonia classifier.
        
        Args:
            model_path: Hugging Face model ID or path to local model files
                       Defaults to: arunn7/vit-base-patch16-224-in21k-medical-xray-lora
            device: Device to run inference on ('cuda', 'cpu', or None for auto-detect)
        """
        self.model = None
        self.processor = None
        self.device = None
        self.model_loaded = False
        self.model_path = model_path or "arunn7/vit-base-patch16-224-in21k-medical-xray-lora"
        self.class_names = ['NORMAL', 'PNEUMONIA']
        self.monitor = get_fresh_monitor()
        
        # Check dependencies
        if not DEPENDENCIES_AVAILABLE:
            logger.error(f"Missing dependencies: {IMPORT_ERROR}")
            raise ImportError(f"Required dependencies not available: {IMPORT_ERROR}")
        
        # Initialize device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
            
        logger.info(f"Initializing PneumoniaClassifier on device: {self.device}")
        logger.info(f"Using model: {self.model_path}")
        
        # Set up model cache
        try:
            self.model_cache = get_model_cache()
            cache_info = self.model_cache.get_cache_info()
            logger.info(f"📁 Model cache: {cache_info['cache_dir']}")
            
            # Check if model is already cached
            if self.model_cache.is_model_cached(self.model_path):
                logger.info("✅ Model found in cache - will load locally")
            else:
                logger.info("📥 Model not cached - will download from Hugging Face")
                
        except Exception as e:
            logger.warning(f"⚠️ Model cache setup failed: {e}")
            self.model_cache = None
        
        # Try to load model
        self.load_model(self.model_path)
    
    def load_model(self, model_path: str) -> bool:
        """
        Load the fine-tuned model from Hugging Face or local path.
        
        Args:
            model_path: Hugging Face model ID or local path
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            logger.info(f"📦 Loading model from: {model_path}")
            logger.info(f"🖥️ Device: {self.device}")
            
            # Load the base ViT model
            base_model_name = "google/vit-base-patch16-224-in21k"
            logger.info(f"📥 Loading base model: {base_model_name}")
            
            try:
                # Load the image processor
                self.processor = AutoImageProcessor.from_pretrained(base_model_name)
                logger.info("✅ Image processor loaded")
            except Exception as proc_error:
                logger.error(f"❌ Failed to load image processor: {str(proc_error)}", exc_info=True)
                raise
            
            try:
                # Load the base model
                base_model = AutoModelForImageClassification.from_pretrained(
                    base_model_name,
                    num_labels=2,  # NORMAL, PNEUMONIA
                    ignore_mismatched_sizes=True
                )
                logger.info("✅ Base model loaded")
            except Exception as base_error:
                logger.error(f"❌ Failed to load base model: {str(base_error)}", exc_info=True)
                raise
            
            # Load LoRA weights if it's a Hugging Face model
            if "/" in model_path and not os.path.exists(model_path):
                logger.info(f"📥 Loading LoRA adapter from: {model_path}")
                try:
                    self.model = PeftModel.from_pretrained(base_model, model_path)
                    logger.info("✅ LoRA adapter loaded")
                except Exception as lora_error:
                    logger.error(f"❌ Failed to load LoRA adapter: {str(lora_error)}", exc_info=True)
                    raise
            else:
                # For local models, try to load as a regular model
                logger.info(f"📥 Loading local model from: {model_path}")
                try:
                    self.model = AutoModelForImageClassification.from_pretrained(model_path)
                    logger.info("✅ Local model loaded")
                except Exception as local_error:
                    logger.error(f"❌ Failed to load local model: {str(local_error)}", exc_info=True)
                    raise
            
            logger.info(f"🔄 Moving model to device: {self.device}")
            try:
                self.model.to(self.device)
                logger.info("✅ Model moved to device")
            except Exception as device_error:
                logger.error(f"❌ Failed to move model to device: {str(device_error)}", exc_info=True)
                raise
            
            self.model.eval()  # Set to evaluation mode
            logger.info("✅ Model set to evaluation mode")
            
            self.model_loaded = True
            self.model_path = model_path
            
            logger.info("✅ Model loaded successfully and ready for inference")
            return True
            
        except Exception as e:
            logger.error(f"❌ CRITICAL: Failed to load model: {str(e)}", exc_info=True)
            logger.error(f"❌ Exception type: {type(e).__name__}")
            logger.error(f"❌ Model path attempted: {model_path}")
            logger.error(f"❌ Device: {self.device}")
            self.model_loaded = False
            return False
    
    def preprocess_image(self, image_path: str) -> Optional[torch.Tensor]:
        """
        Preprocess the input image for inference using Hugging Face processor.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed tensor or None if preprocessing failed
        """
        try:
            # Load and validate image
            image = Image.open(image_path).convert('RGB')
            
            # Use Hugging Face image processor
            if self.processor is None:
                raise Exception("Image processor not loaded")
            
            # Process image
            inputs = self.processor(image, return_tensors="pt")
            image_tensor = inputs['pixel_values'].to(self.device)
            
            return image_tensor
            
        except Exception as e:
            logger.error(f"Failed to preprocess image {image_path}: {str(e)}")
            return None
    
    def predict(self, image_path: str) -> Dict[str, Any]:
        """
        Perform pneumonia prediction on the input image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing prediction results:
            {
                'prediction': 'NORMAL' or 'PNEUMONIA',
                'confidence': float (0.0 to 1.0),
                'probabilities': {'NORMAL': float, 'PNEUMONIA': float},
                'success': bool,
                'error': str (if failed)
            }
        """
        start_time = time.time()
        
        if not self.model_loaded:
            logger.error("❌ Prediction failed: Model not loaded")
            logger.error(f"❌ Model status: loaded={self.model_loaded}, model_exists={self.model is not None}")
            return {
                'success': False,
                'error': 'Model not loaded',
                'prediction': None,
                'confidence': 0.0
            }
        
        try:
            # Preprocess image
            image_tensor = self.preprocess_image(image_path)
            if image_tensor is None:
                return {
                    'success': False,
                    'error': 'Failed to preprocess image',
                    'prediction': None,
                    'confidence': 0.0
                }
            
            # Perform inference
            with torch.no_grad():
                outputs = self.model(image_tensor)
                
                # Handle different model output formats
                if hasattr(outputs, 'logits'):
                    logits = outputs.logits
                else:
                    logits = outputs
                
                # Apply softmax to get probabilities
                probabilities = F.softmax(logits, dim=1)
                
                # Get prediction and confidence
                confidence, predicted_class = torch.max(probabilities, 1)
                predicted_class = predicted_class.item()
                confidence = confidence.item()
                
                # Convert to class name
                prediction = self.class_names[predicted_class]
                
                # Get probabilities for both classes
                probs_dict = {
                    self.class_names[0]: probabilities[0][0].item(),
                    self.class_names[1]: probabilities[0][1].item()
                }
            
            logger.info(f"Prediction: {prediction} (confidence: {confidence:.3f})")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Get image metadata for monitoring
            try:
                with Image.open(image_path) as img:
                    image_metadata = {
                        'width': img.width,
                        'height': img.height,
                        'format': img.format or 'unknown'
                    }
            except:
                image_metadata = {'width': 0, 'height': 0, 'format': 'unknown'}
            
            # Log to W&B
            self.monitor.log_prediction(
                model_name="vision_classifier",
                prediction=prediction,
                confidence=confidence,
                processing_time=processing_time,
                image_metadata=image_metadata
            )
            
            return {
                'success': True,
                'prediction': prediction,
                'confidence': confidence,
                'probabilities': probs_dict,
                'error': None,
                'processing_time': processing_time
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"❌ CRITICAL: Prediction failed: {str(e)}", exc_info=True)
            logger.error(f"❌ Exception type: {type(e).__name__}")
            logger.error(f"❌ Image path: {image_path}")
            logger.error(f"❌ Processing time before error: {processing_time:.3f}s")
            
            # Log error to W&B
            self.monitor.log_error(
                error_type="prediction_error",
                error_message=str(e),
                context={
                    "model": "vision_classifier",
                    "processing_time": processing_time,
                    "image_path": image_path
                }
            )
            
            return {
                'success': False,
                'error': f'Prediction failed: {str(e)}',
                'prediction': None,
                'confidence': 0.0,
                'processing_time': processing_time
            }
    
    def is_ready(self) -> bool:
        """Check if the classifier is ready for inference."""
        return self.model_loaded and self.model is not None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        return {
            'model_loaded': self.model_loaded,
            'model_path': self.model_path,
            'device': self.device,
            'class_names': self.class_names,
            'dependencies_available': DEPENDENCIES_AVAILABLE
        }


# Global classifier instance (singleton pattern)
_classifier_instance = None


def get_classifier(model_path: Optional[str] = None) -> PneumoniaClassifier:
    """
    Get or create a singleton instance of the pneumonia classifier.
    
    Args:
        model_path: Hugging Face model ID or local path (only used on first creation)
                   Defaults to: arunn7/vit-base-patch16-224-in21k-medical-xray-lora
        
    Returns:
        PneumoniaClassifier instance
    """
    global _classifier_instance
    
    if _classifier_instance is None:
        # Try to get model path from environment if not provided
        if model_path is None:
            model_path = os.getenv('FINETUNED_MODEL_PATH', 'arunn7/vit-base-patch16-224-in21k-medical-xray-lora')
        
        _classifier_instance = PneumoniaClassifier(model_path=model_path)
        
        # If model path provided and not loaded, try to load
        if model_path and not _classifier_instance.is_ready():
            _classifier_instance.load_model(model_path)
    
    return _classifier_instance


def analyze_xray_for_pneumonia(image_path: str, model_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to analyze an X-ray image for pneumonia.
    
    This function provides a simple interface that can be easily integrated
    into the existing application routes.
    
    Args:
        image_path: Path to the X-ray image
        model_path: Optional path to the fine-tuned model
        
    Returns:
        Dictionary with analysis results compatible with existing app structure
    """
    try:
        # Get classifier instance
        classifier = get_classifier(model_path)
        
        # Check if classifier is ready
        if not classifier.is_ready():
            return {
                'success': False,
                'error': 'Fine-tuned model not available or not loaded',
                'provider': 'fine_tuned_model',
                'is_medical_image': False,
                'diagnosis': 'Model not available',
                'confidence_score': 0.0
            }
        
        # Perform prediction
        result = classifier.predict(image_path)
        
        if not result['success']:
            return {
                'success': False,
                'error': result['error'],
                'provider': 'fine_tuned_model',
                'is_medical_image': False,
                'diagnosis': 'Analysis failed',
                'confidence_score': 0.0
            }
        
        # Format result to match existing app structure
        prediction = result['prediction']
        confidence = result['confidence']
        
                # Create structured findings based on prediction
        if prediction == 'PNEUMONIA':
            diagnosis_summary = f"PNEUMONIA DETECTED with {confidence:.1%} confidence"
            overall_assessment = f"PNEUMONIA DETECTED ({confidence:.1%} confidence)"
            urgency = "urgent" if confidence > 0.8 else "routine"
            
            findings = [
                {
                    'term': 'Pneumonia',
                    'status': 'present',
                    'category': 'LUNGS',
                    'title': 'Pneumonia Detection',
                    'severity': 'urgent' if confidence > 0.8 else 'moderate',
                    'description': f'Evidence of pneumonia detected in chest X-ray with {confidence:.1%} confidence.',
                    'confidence': int(confidence * 100),
                    'details': [
                        f'Pneumonia probability: {result["probabilities"]["PNEUMONIA"]:.1%}',
                        f'Normal probability: {result["probabilities"]["NORMAL"]:.1%}',
                        'Clinical correlation recommended',
                        'Consider follow-up imaging if symptoms persist'
                    ]
                }
            ]
            recommendations = [
                "Clinical correlation recommended",
                "Consider follow-up imaging if symptoms persist"
            ]
        else:
            diagnosis_summary = f"NO EVIDENCE OF PNEUMONIA (confidence: {confidence:.1%})"
            overall_assessment = f"NORMAL STUDY ({confidence:.1%} confidence)"
            urgency = "routine"

            findings = [
                {
                    'term': 'Pneumonia',
                    'status': 'absent',
                    'category': 'LUNGS',
                    'title': 'Normal Study',
                    'severity': 'normal',
                    'description': f'No evidence of pneumonia detected. {confidence:.1%} confidence in normal assessment.',
                    'confidence': int(confidence * 100),
                    'details': [
                        f'Normal probability: {result["probabilities"]["NORMAL"]:.1%}',
                        f'Pneumonia probability: {result["probabilities"]["PNEUMONIA"]:.1%}',
                        'No immediate follow-up required',
                        'Continue routine monitoring as advised'
                    ]
                }
            ]
            recommendations = [
                "No immediate follow-up required",
                "Continue routine monitoring"
            ]
        
        return {
            'success': True,
            'provider': 'fine_tuned_model',
            'is_medical_image': True,
            'diagnosis': diagnosis_summary,
            'overall_impression': diagnosis_summary,
            'overall_assessment': overall_assessment,
            'confidence_score': confidence,
            'findings': findings,
            'recommendations': recommendations,
            'priority_recommendations': [recommendations[0]],
            'urgency': urgency,
            'image_type': 'chest_xray',
            'model_prediction': prediction,
            'model_probabilities': result['probabilities'],
            'analysis_method': 'fine_tuned_cnn'
        }
        
    except Exception as e:
        logger.error(f"❌ CRITICAL: Fine-tuned model analysis failed: {str(e)}", exc_info=True)
        logger.error(f"❌ Exception type: {type(e).__name__}")
        logger.error(f"❌ Image path: {image_path}")
        return {
            'success': False,
            'error': f'Fine-tuned model analysis failed: {str(e)}',
            'provider': 'fine_tuned_model',
            'is_medical_image': False,
            'diagnosis': 'Analysis failed',
            'confidence_score': 0.0
        }
