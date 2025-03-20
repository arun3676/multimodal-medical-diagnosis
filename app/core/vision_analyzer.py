"""
Enhanced vision analysis module for the Multimodal AI Medical Diagnosis System.

This module contains functions to analyze medical images using
Google Cloud Vision API along with medical image preprocessing.
"""
import os
import json
import logging
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import cv2
from google.cloud import vision
from google.oauth2 import service_account
from dotenv import load_dotenv
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def setup_credentials():
    """
    Set up Google Cloud credentials from environment variables or local file.
    """
    # Try to get credentials path from environment
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # If no environment variable, try to find credentials in standard locations
    if not credentials_path or not os.path.exists(credentials_path):
        # Check project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        possible_paths = [
            os.path.join(project_root, 'credentials', 'google_credentials.json'),
            os.path.join(project_root, 'google_credentials.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'credentials', 'google_credentials.json')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                credentials_path = path
                break
    
    if credentials_path and os.path.exists(credentials_path):
        logger.info(f"Using Google Cloud credentials from: {credentials_path}")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        return True
    else:
        logger.warning("Google Cloud credentials file not found.")
        return False

def get_vision_client():
    """
    Get an authenticated Vision API client.
    
    Returns:
        google.cloud.vision.ImageAnnotatorClient: Authenticated client
    """
    # First try to use credentials file
    if setup_credentials():
        return vision.ImageAnnotatorClient()
    
    # If that fails, try to load credentials directly
    try:
        # Check project root directory
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        possible_paths = [
            os.path.join(project_root, 'credentials', 'google_credentials.json'),
            os.path.join(project_root, 'google_credentials.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', 'credentials', 'google_credentials.json')
        ]
        
        for credentials_path in possible_paths:
            if os.path.exists(credentials_path):
                with open(credentials_path, 'r') as f:
                    credentials_info = json.load(f)
                    credentials = service_account.Credentials.from_service_account_info(credentials_info)
                    return vision.ImageAnnotatorClient(credentials=credentials)
        
        raise FileNotFoundError("Could not find Google credentials file")
    except Exception as e:
        logger.error(f"Error setting up Vision client: {str(e)}")
        raise

def preprocess_medical_image(image_path, enhanced_path=None):
    """
    Apply medical image preprocessing techniques to enhance features.
    
    Args:
        image_path: Path to the original image
        enhanced_path: Path to save the enhanced image (optional)
        
    Returns:
        str: Path to the enhanced image
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Convert to grayscale if not already
        if img.mode != 'L':
            img = img.convert('L')
        
        # Apply contrast enhancement
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)  # Increase contrast
        
        # Apply adaptive histogram equalization using OpenCV
        img_array = np.array(img)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        img_array = clahe.apply(img_array)
        
        # Apply mild sharpening
        img = Image.fromarray(img_array)
        img = img.filter(ImageFilter.SHARPEN)
        
        # Save enhanced image if path provided, otherwise create a temporary file
        if not enhanced_path:
            enhanced_path = f"{os.path.splitext(image_path)[0]}_enhanced.png"
        
        img.save(enhanced_path)
        logger.info(f"Enhanced medical image saved to: {enhanced_path}")
        
        return enhanced_path
    
    except Exception as e:
        logger.error(f"Error preprocessing medical image: {str(e)}")
        # Fall back to original image
        return image_path

def is_medical_xray(image_path):
    """
    Check if the image is likely to be a medical X-ray.
    
    Args:
        image_path: Path to the image
        
    Returns:
        bool: True if the image appears to be a medical X-ray
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Convert to grayscale if not already
        if img.mode != 'L':
            img = img.convert('L')
        
        # Get image as array
        img_array = np.array(img)
        
        # X-rays typically have these characteristics:
        # 1. Primarily grayscale
        # 2. High contrast
        # 3. Specific histogram patterns
        
        # Check grayscale distribution 
        histogram = cv2.calcHist([img_array], [0], None, [256], [0, 256])
        histogram = histogram.flatten() / histogram.sum()  # Normalize
        
        # Check for bimodal distribution (typical in X-rays)
        peaks = 0
        threshold = 0.01
        for i in range(1, 255):
            if histogram[i-1] < histogram[i] and histogram[i] > histogram[i+1] and histogram[i] > threshold:
                peaks += 1
        
        # Check contrast
        contrast = img_array.std()
        
        # Combine heuristics
        is_xray = (peaks >= 1 and peaks <= 4) and (contrast > 30)
        
        logger.info(f"Image assessment: peaks={peaks}, contrast={contrast}, is_xray={is_xray}")
        
        return is_xray
    
    except Exception as e:
        logger.error(f"Error checking if image is an X-ray: {str(e)}")
        # Be conservative, don't assume it's an X-ray
        return False

def analyze_image(image_path):
    """
    Analyze an image using Google Cloud Vision API with medical preprocessing.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        str: Detected text or features from the image
        
    Raises:
        Exception: If an error occurs during analysis
    """
    try:
        # Check if this looks like a medical X-ray
        if not is_medical_xray(image_path):
            logger.warning(f"The image at {image_path} does not appear to be a medical X-ray.")
            # Continue anyway but note this in results
            medical_warning = "⚠️ NOTE: This image does not appear to be a standard medical X-ray. Analysis may be inaccurate."
        else:
            medical_warning = ""
        
        # Preprocess the image to enhance medical features
        enhanced_path = preprocess_medical_image(image_path)
        
        # Initialize Google Cloud Vision client
        client = get_vision_client()
        
        logger.info(f"Analyzing image: {enhanced_path}")
        
        # Read the enhanced image file
        with open(enhanced_path, "rb") as image_file:
            content = image_file.read()
        
        # Create a Vision Image object
        image = vision.Image(content=content)
        
        # Perform comprehensive analysis
        text_response = client.text_detection(image=image)
        label_response = client.label_detection(image=image)
        object_response = client.object_localization(image=image)
        
        # Extract results
        text_annotations = text_response.text_annotations
        labels = label_response.label_annotations
        objects = object_response.localized_object_annotations
        
        # Combine results
        results = []
        
        if medical_warning:
            results.append(medical_warning)
        
        # Add text if found
        if text_annotations:
            results.append(f"DETECTED TEXT:\n{text_annotations[0].description}\n")
        
        # Add labels if found
        if labels:
            results.append("IMAGE FEATURES:")
            for label in labels:
                results.append(f"- {label.description} ({label.score:.2%})")
        
        # Add objects if found
        if objects:
            results.append("\nDETECTED STRUCTURES:")
            for obj in objects:
                results.append(f"- {obj.name} ({obj.score:.2%})")
        
        # Add medical imaging specific observations
        results.append("\nMEDICAL IMAGE PROPERTIES:")
        
        # Open image for additional analysis
        img = Image.open(image_path)
        img_array = np.array(img.convert('L'))  # Convert to grayscale
        
        # Analyze density and distribution
        mean_intensity = np.mean(img_array)
        std_intensity = np.std(img_array)
        
        results.append(f"- Average density: {mean_intensity:.2f}")
        results.append(f"- Density variation: {std_intensity:.2f}")
        
        # Use histogram to identify general density patterns
        hist = cv2.calcHist([img_array], [0], None, [5], [0, 256])
        hist = hist.flatten() / hist.sum()  # Normalize to percentage
        density_ranges = ["Very dark regions", "Dark regions", "Medium density", "Light regions", "Very light regions"]
        
        results.append("\nDENSITY DISTRIBUTION:")
        for i, (region, percentage) in enumerate(zip(density_ranges, hist)):
            results.append(f"- {region}: {percentage*100:.1f}%")
        
        # Return combined results
        return "\n".join(results)
            
    except Exception as e:
        logger.error(f"Error analyzing image: {str(e)}")
        raise Exception(f"Error analyzing image: {str(e)}")

def analyze_chest_xray(image_path):
    """
    Specialized analysis for chest X-ray images.
    
    Args:
        image_path: Path to the X-ray image
        
    Returns:
        dict: Dictionary containing analysis results
    """
    try:
        # Check if this looks like a medical X-ray
        is_xray = is_medical_xray(image_path)
        
        # Preprocess the image to enhance medical features
        enhanced_path = preprocess_medical_image(image_path)
        
        # Initialize Google Cloud Vision client
        client = get_vision_client()
        
        with open(enhanced_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        
        # Get both object detection and general image labels
        objects = client.object_localization(image=image).localized_object_annotations
        labels = client.label_detection(image=image).label_annotations
        
        # Extract image characteristics
        img = Image.open(image_path)
        img_array = np.array(img.convert('L'))  # Convert to grayscale
        
        # Basic image metrics
        mean_intensity = np.mean(img_array)
        std_intensity = np.std(img_array)
        
        # Analyze different regions (roughly corresponding to lungs)
        h, w = img_array.shape
        left_lung = img_array[int(h*0.25):int(h*0.75), :int(w*0.45)]
        right_lung = img_array[int(h*0.25):int(h*0.75), int(w*0.55):]
        heart_region = img_array[int(h*0.25):int(h*0.75), int(w*0.45):int(w*0.55)]
        
        left_density = np.mean(left_lung)
        right_density = np.mean(right_lung)
        heart_density = np.mean(heart_region)
        
        density_diff = abs(left_density - right_density)
        
        # Build the findings
        findings = {
            'is_likely_xray': is_xray,
            'objects': [f"{obj.name} ({obj.score:.2%})" for obj in objects],
            'features': [f"{label.description} ({label.score:.2%})" for label in labels],
            'metrics': {
                'overall_density': f"{mean_intensity:.2f}",
                'density_variation': f"{std_intensity:.2f}",
                'left_region_density': f"{left_density:.2f}",
                'right_region_density': f"{right_density:.2f}",
                'central_region_density': f"{heart_density:.2f}",
                'left_right_difference': f"{density_diff:.2f}",
            },
            'raw_scores': {
                'objects': {obj.name: obj.score for obj in objects},
                'labels': {label.description: label.score for label in labels}
            }
        }
        
        return findings
    
    except Exception as e:
        logger.error(f"Error analyzing chest X-ray: {str(e)}")
        raise Exception(f"Error analyzing chest X-ray: {str(e)}")