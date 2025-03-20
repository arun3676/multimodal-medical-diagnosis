"""
Enhanced route definitions for the Multimodal AI Medical Diagnosis System.
"""
import os
import uuid
import time
import numpy as np
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
)
from werkzeug.utils import secure_filename

from app.core.vision_analyzer import analyze_image, analyze_chest_xray, is_medical_xray
from app.core.diagnosis_generator import generate_diagnosis, generate_enhanced_interpretation

# Create blueprint
main_bp = Blueprint("main", __name__)

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    Args:
        filename: Name of the uploaded file
        
    Returns:
        Boolean indicating if the file is allowed
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )

# Helper function to convert NumPy types to native Python types
def convert_numpy_types(obj):
    """
    Convert NumPy types to native Python types that are JSON serializable.
    
    Args:
        obj: The object to convert
        
    Returns:
        The converted object
    """
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: convert_numpy_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(i) for i in obj]
    else:
        return obj

@main_bp.route("/", methods=["GET"])
def index():
    """Render the main page."""
    return render_template("index.html")

@main_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    Handle the form submission for image analysis and diagnosis generation.
    """
    # Check if image file was uploaded
    if "xray_image" not in request.files:
        flash("No file part", "danger")
        return redirect(request.url)
    
    file = request.files["xray_image"]
    
    # Check if file was selected
    if file.filename == "":
        flash("No file selected", "danger")
        return redirect(request.url)
    
    # Get patient symptoms
    symptoms = request.form.get("symptoms", "")
    
    if file and allowed_file(file.filename):
        # Generate a unique filename to avoid collisions
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        
        # Save the file
        file.save(filepath)
        
        try:
            # Record start time for processing time calculation
            start_time = time.time()
            
            # Check if it appears to be a medical X-ray
            is_xray = is_medical_xray(filepath)
            
            # Convert NumPy bool_ to Python bool
            is_xray = bool(is_xray)
            
            if not is_xray:
                flash("Warning: The uploaded image may not be a standard medical X-ray. Analysis may be less accurate.", "warning")
            
            # Use the comprehensive chest X-ray analysis
            findings = analyze_chest_xray(filepath)
            
            # Convert any NumPy types in findings to native Python types
            findings = convert_numpy_types(findings)
            
            # Generate a more detailed interpretation
            interpretation = generate_enhanced_interpretation(findings, symptoms)
            
            # Calculate processing time
            processing_time = f"{time.time() - start_time:.1f}s"
            
            # Store full analysis as a string for display
            analysis_text = "IMAGE ANALYSIS RESULTS:\n\n"
            
            # Add if it appears to be an X-ray
            if not findings.get('is_likely_xray', True):
                analysis_text += "⚠️ NOTE: This image does not appear to be a standard medical X-ray. Analysis may be inaccurate.\n\n"
            
            # Add detected objects
            analysis_text += "DETECTED STRUCTURES:\n"
            for obj in findings.get('objects', ['None detected']):
                analysis_text += f"- {obj}\n"
            
            # Add detected features
            analysis_text += "\nDETECTED FEATURES:\n"
            for feature in findings.get('features', ['None detected']):
                analysis_text += f"- {feature}\n"
            
            # Add metrics
            analysis_text += "\nIMAGE METRICS:\n"
            for k, v in findings.get('metrics', {}).items():
                analysis_text += f"- {k}: {v}\n"
            
            # Store results in session
            session["results"] = {
                "image_path": filepath,
                "image_filename": filename,
                "analysis": analysis_text,
                "symptoms": symptoms,
                "diagnosis": interpretation,
                "is_likely_xray": findings.get('is_likely_xray', True),
                "processing_time": processing_time
            }
            
            return redirect(url_for("main.results"))
        
        except Exception as e:
            flash(f"Error processing image: {str(e)}", "danger")
            return redirect(url_for("main.index"))
    
    flash("Invalid file type. Please upload a valid image (PNG, JPG, JPEG).", "danger")
    return redirect(url_for("main.index"))

@main_bp.route("/results", methods=["GET"])
def results():
    """
    Display the analysis and diagnosis results.
    """
    results_data = session.get("results", None)
    
    if not results_data:
        flash("No results found. Please submit an X-ray for analysis.", "warning")
        return redirect(url_for("main.index"))
    
    # Add current date and time for the report
    now = datetime.now()
    
    return render_template("results.html", results=results_data, now=now)

@main_bp.route("/about", methods=["GET"])
def about():
    """
    Display information about the project.
    """
    return render_template("about.html")