"""
Simplified vision analysis module using Gemini API for medical image analysis.
"""
import os
import json
import logging
import base64
import requests
from PIL import Image
import numpy as np
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class GeminiImageAnalyzer:
    """Simplified medical image analyzer using Gemini API."""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    def analyze_medical_image(self, image_path: str, image_type: str = 'chest_xray') -> Dict:
        """
        Analyze medical image using Gemini Vision API.
        
        Args:
            image_path: Path to the medical image
            image_type: Type of medical image
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            logger.info(f"Starting analysis of image: {image_path}")
            
            # Convert image to base64
            image_data, mime_type = self._encode_image(image_path)
            logger.info(f"Image encoded successfully, size: {len(image_data)} chars")
            
            # Prepare the prompt
            prompt = self._get_medical_analysis_prompt()
            logger.info(f"Prompt prepared, length: {len(prompt)} chars")
            
            # Make API request to Gemini
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        }
                    ]
                }]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            logger.info(f"Making API request to Gemini...")
            
            # Add retry logic for API rate limiting
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    logger.info(f"API attempt {attempt + 1}/{max_retries}")
                    response = requests.post(
                        f"{self.api_url}?key={self.api_key}",
                        headers=headers,
                        json=payload,
                        timeout=60
                    )
                    
                    logger.info(f"API response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info("API call successful, parsing response...")
                        
                        # Parse Gemini response
                        if "candidates" in result and len(result["candidates"]) > 0:
                            candidate = result["candidates"][0]
                            if "content" in candidate and "parts" in candidate["content"]:
                                analysis_text = candidate["content"]["parts"][0]["text"]
                                logger.info(f"Analysis text received, length: {len(analysis_text)} chars")
                            else:
                                raise Exception("Unexpected response format from Gemini API")
                            
                            # Create structured response
                            return {
                                'is_medical_image': True,
                                'image_type': image_type,
                                'labels': self._extract_labels_from_text(analysis_text),
                                'objects': self._extract_objects_from_text(analysis_text),
                                'text': None,
                                'analysis_text': analysis_text,
                                'quality_metrics': self._assess_basic_quality(image_path),
                                'statistics': self._calculate_basic_stats(image_path)
                            }
                        else:
                            raise Exception("No analysis received from Gemini API")
                    
                    elif response.status_code == 503:
                        # Model overloaded - wait and retry
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 5
                            logger.warning(f"Gemini API overloaded, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            import time
                            time.sleep(wait_time)
                            continue
                        else:
                            raise Exception("Gemini API is currently overloaded. Please try again in a few minutes.")
                    
                    elif response.status_code == 429:
                        # Rate limited - wait and retry
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 10
                            logger.warning(f"Gemini API rate limited, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            import time
                            time.sleep(wait_time)
                            continue
                        else:
                            raise Exception("Gemini API rate limit exceeded. Please try again later.")
                    
                    else:
                        # Other errors
                        error_msg = f"Gemini API error: {response.status_code}"
                        try:
                            error_detail = response.json()
                            if 'error' in error_detail:
                                error_msg += f" - {error_detail['error'].get('message', response.text)}"
                        except:
                            error_msg += f" - {response.text}"
                        logger.error(f"API error: {error_msg}")
                        raise Exception(error_msg)
                        
                except requests.exceptions.Timeout:
                    logger.error(f"API timeout on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        logger.warning(f"Gemini API timeout, retrying (attempt {attempt + 1}/{max_retries})")
                        continue
                    else:
                        raise Exception("Gemini API request timed out. Please try again.")
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"API request failed: {e}")
                    if attempt < max_retries - 1:
                        logger.warning(f"Gemini API request failed, retrying (attempt {attempt + 1}/{max_retries}): {e}")
                        continue
                    else:
                        raise Exception(f"Failed to connect to Gemini API: {e}")
                
        except Exception as e:
            logger.error(f"Error analyzing image with Gemini: {str(e)}")
            raise
    
    def _encode_image(self, image_path: str) -> tuple:
        """Encode image to base64 for Gemini API."""
        # Determine the MIME type based on file extension
        import os
        ext = os.path.splitext(image_path)[1].lower()
        if ext in ['.jpg', '.jpeg']:
            mime_type = "image/jpeg"
        elif ext == '.png':
            mime_type = "image/png"
        elif ext == '.webp':
            mime_type = "image/webp"
        else:
            mime_type = "image/jpeg"  # Default
            
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
        return image_data, mime_type
    
    def _get_medical_analysis_prompt(self) -> str:
        """Get the prompt for medical image analysis."""
        return """You are an expert radiologist analyzing a medical image. Your task is to identify ANY abnormalities present, no matter how subtle.

CRITICAL: If you see ANY of these findings, you MUST report them:
- Cardiomegaly (enlarged heart)
- Pleural effusion (fluid around lungs)
- Pneumothorax (air causing lung collapse)
- Lung opacities, consolidations, or infiltrates
- Pneumonia or infection
- Masses or nodules
- Atelectasis (lung collapse)
- Medical devices (tubes, lines, etc.)
- Elevated hemidiaphragm
- Blunted costophrenic angles

ANALYSIS INSTRUCTIONS:
1. **LUNG ASSESSMENT**: Look for ANY opacities, consolidations, or abnormal densities. Report location (right/left, upper/middle/lower).
2. **HEART ASSESSMENT**: Measure heart size. If heart appears enlarged, report cardiomegaly.
3. **PLEURAL ASSESSMENT**: Check for fluid (effusion) or air (pneumothorax) around lungs.
4. **MEDICAL DEVICES**: Note any tubes, lines, or devices visible.
5. **DIAPHRAGM**: Check if diaphragm is elevated or blunted.

REPORTING RULES:
- If you see ANY abnormality, report it with specific location
- Use "Possible" for 70-85% confidence, "Likely" for 85-95% confidence
- If uncertain, say "Cannot exclude [finding]" rather than calling it normal
- NEVER report "Normal chest X-ray" unless you are 100% certain no abnormalities exist
- If you see multiple findings, list ALL of them

IMPORTANT: This patient may have serious conditions. Missing abnormalities could be life-threatening. When in doubt, report the finding."""
    
    def _extract_labels_from_text(self, analysis_text: str) -> List[Dict]:
        """Extract labels from Gemini analysis text."""
        # Simple keyword extraction
        medical_keywords = [
            'lung', 'heart', 'chest', 'ribs', 'diaphragm', 'spine',
            'pneumonia', 'pneumothorax', 'effusion', 'consolidation',
            'atelectasis', 'cardiomegaly', 'normal', 'abnormal'
        ]
        
        labels = []
        text_lower = analysis_text.lower()
        
        for keyword in medical_keywords:
            if keyword in text_lower:
                # Simple confidence based on keyword frequency
                count = text_lower.count(keyword)
                confidence = min(0.9, 0.5 + (count * 0.1))
                labels.append({
                    'description': keyword.title(),
                    'score': confidence
                })
        
        return labels[:10]  # Return top 10
    
    def _extract_objects_from_text(self, analysis_text: str) -> List[Dict]:
        """Extract anatomical objects from analysis text."""
        anatomical_objects = [
            'heart', 'lung', 'rib', 'spine', 'diaphragm', 'clavicle'
        ]
        
        objects = []
        text_lower = analysis_text.lower()
        
        for obj in anatomical_objects:
            if obj in text_lower:
                objects.append({
                    'name': obj.title(),
                    'score': 0.8,  # Default confidence
                    'bounds': []  # Gemini doesn't provide coordinates
                })
        
        return objects[:10]
    
    def _assess_basic_quality(self, image_path: str) -> Dict:
        """Basic image quality assessment."""
        try:
            img = Image.open(image_path)
            img_array = np.array(img.convert('L'))
            
            # Basic quality metrics
            contrast = float(np.std(img_array))
            brightness = float(np.mean(img_array))
            
            # Simple quality score
            quality_score = min(1.0, contrast / 100.0)
            
            if quality_score >= 0.8:
                quality_rating = "Excellent"
            elif quality_score >= 0.6:
                quality_rating = "Good"
            elif quality_score >= 0.4:
                quality_rating = "Fair"
            else:
                quality_rating = "Poor"
            
            return {
                'quality_score': quality_score,
                'quality_rating': quality_rating,
                'contrast': contrast,
                'brightness': brightness,
                'sharpness': contrast,  # Simplified
                'noise_level': 10.0  # Placeholder
            }
        except Exception as e:
            logger.error(f"Error assessing image quality: {e}")
            return {
                'quality_score': 0.5,
                'quality_rating': "Unknown",
                'contrast': 0.0,
                'brightness': 0.0,
                'sharpness': 0.0,
                'noise_level': 0.0
            }
    
    def _calculate_basic_stats(self, image_path: str) -> Dict:
        """Calculate basic image statistics."""
        try:
            img = Image.open(image_path)
            img_array = np.array(img.convert('L'))
            
            return {
                'mean_intensity': float(np.mean(img_array)),
                'std_intensity': float(np.std(img_array)),
                'min_intensity': float(np.min(img_array)),
                'max_intensity': float(np.max(img_array)),
                'median_intensity': float(np.median(img_array)),
                'contrast': float(np.std(img_array)),
                'entropy': 7.5,  # Placeholder
                'energy': float(np.sum(img_array ** 2))
            }
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def is_medical_image(self, image_path: str) -> bool:
        """Check if image is likely a medical X-ray."""
        try:
            img = Image.open(image_path)
            
            # Convert to grayscale for analysis
            if img.mode != 'L':
                img = img.convert('L')
            
            img_array = np.array(img)
            
            # Basic criteria for X-ray detection
            criteria = {
                'size_adequate': img.size[0] >= 256 and img.size[1] >= 256,
                'aspect_ratio': 0.6 < img.size[0] / img.size[1] < 1.6,
                'grayscale_nature': self._is_grayscale_image(img_array),
                'intensity_range': self._has_medical_intensity_range(img_array),
                'contrast_appropriate': 20 < np.std(img_array) < 120,
                'brightness_range': 50 < np.mean(img_array) < 200,
            }
            
            # Calculate confidence score
            score = sum(criteria.values())
            total_criteria = len(criteria)
            confidence = score / total_criteria
            
            logger.info(f"X-ray detection criteria: {criteria}")
            logger.info(f"X-ray confidence: {confidence:.2f} ({score}/{total_criteria})")
            
            return confidence >= 0.6  # Need at least 60% of criteria met
            
        except Exception as e:
            logger.error(f"Error checking if image is X-ray: {str(e)}")
            return False
    
    def _is_grayscale_image(self, img_array: np.ndarray) -> bool:
        """Check if image is effectively grayscale."""
        # If already 2D, it's grayscale
        if len(img_array.shape) == 2:
            return True
        
        # If 3D, check if R,G,B channels are similar
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
            # Calculate average difference between channels
            diff = np.mean([np.abs(r - g), np.abs(g - b), np.abs(r - b)])
            return diff < 15  # Very similar channels indicate grayscale
        
        return True
    
    def _has_medical_intensity_range(self, img_array: np.ndarray) -> bool:
        """Check if image has typical medical X-ray intensity distribution."""
        min_val, max_val = np.min(img_array), np.max(img_array)
        
        # Good dynamic range (not too narrow, not full range)
        dynamic_range = max_val - min_val
        
        # X-rays typically have good contrast but not extreme values
        return (
            dynamic_range > 80 and  # Sufficient contrast
            min_val < 50 and       # Some dark areas (air/background)
            max_val > 150          # Some bright areas (bones/dense tissue)
        )

# Create singleton instance
analyzer = GeminiImageAnalyzer()

# Backward compatibility functions
def analyze_image(image_path: str) -> str:
    """Backward compatible function."""
    results = analyzer.analyze_medical_image(image_path)
    return results.get('analysis_text', 'Analysis completed')

def analyze_chest_xray(image_path: str) -> Dict:
    """Backward compatible function."""
    return analyzer.analyze_medical_image(image_path, 'chest_xray') 