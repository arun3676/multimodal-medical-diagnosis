"""
Simplified route definitions for the Multimodal AI Medical Diagnosis System.
"""
import os
import uuid
import time
import json
from datetime import datetime
from functools import wraps
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    session,
    jsonify,
    send_file
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from app.core.vision_analyzer_gemini import GeminiImageAnalyzer
from app.core.diagnosis_generator import MedicalDiagnosisGenerator
from app.core.report_generator import generate_report
from app import limiter, cache

# Create blueprint
main_bp = Blueprint("main", __name__)

# Initialize analyzers
image_analyzer = GeminiImageAnalyzer()
diagnosis_generator = None  # Will be initialized when needed

def get_diagnosis_generator():
    """Get or create the diagnosis generator instance."""
    global diagnosis_generator
    if diagnosis_generator is None:
        try:
            diagnosis_generator = MedicalDiagnosisGenerator()
        except Exception as e:
            current_app.logger.error(f"Failed to initialize diagnosis generator: {e}")
            # Return None to trigger fallback behavior
            return None
    return diagnosis_generator

def allowed_file(filename):
    """Check if the uploaded file has an allowed extension."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]
    )

def validate_file_size(file):
    """Validate file size before processing."""
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size = current_app.config["MAX_CONTENT_LENGTH"]
    if file_size > max_size:
        raise RequestEntityTooLarge(f"File size exceeds maximum allowed size of {max_size // (1024*1024)}MB")
    
    return file_size

def sanitize_input(text):
    """Sanitize user input to prevent XSS and injection attacks."""
    if not text:
        return ""
    
    # Remove any HTML tags and limit length
    import re
    text = re.sub('<[^<]+?>', '', text)
    return text[:1000]  # Limit to 1000 characters

@main_bp.route("/", methods=["GET"])
@cache.cached(timeout=300)
def index():
    """Render the main page."""
    return render_template("index.html")

@main_bp.route("/analyze", methods=["POST"])
@limiter.limit("10 per hour")
def analyze():
    """Handle the form submission for image analysis and diagnosis generation."""
    try:
        # Check if image file was uploaded
        if "xray_image" not in request.files:
            flash("No file uploaded. Please select an image.", "danger")
            return redirect(url_for("main.index"))
        
        file = request.files["xray_image"]
        
        # Check if file was selected
        if file.filename == "":
            flash("No file selected. Please choose an image.", "danger")
            return redirect(url_for("main.index"))
        
        # Validate file type
        if not allowed_file(file.filename):
            flash("Invalid file type. Please upload a valid image (PNG, JPG, JPEG, WebP).", "danger")
            return redirect(url_for("main.index"))
        
        # Validate file size
        try:
            file_size = validate_file_size(file)
        except RequestEntityTooLarge as e:
            flash(str(e), "danger")
            return redirect(url_for("main.index"))
        
        # Get and sanitize patient information
        symptoms = sanitize_input(request.form.get("symptoms", ""))
        patient_age = sanitize_input(request.form.get("patient_age", ""))
        patient_gender = sanitize_input(request.form.get("patient_gender", ""))
        medical_history = sanitize_input(request.form.get("medical_history", ""))
        
        # Generate a unique filename
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        
        # Save the file
        file.save(filepath)
        
        # Record start time
        start_time = time.time()
        
        # Perform comprehensive analysis
        try:
            # Analyze the image
            analysis_results = image_analyzer.analyze_medical_image(filepath)
            
            # Prepare patient info if provided
            patient_info = None
            if any([patient_age, patient_gender, medical_history]):
                patient_info = {
                    'age': patient_age,
                    'gender': patient_gender,
                    'history': medical_history
                }
            
            # Generate diagnosis
            diagnosis_gen = get_diagnosis_generator()
            if diagnosis_gen is None:
                flash("Diagnosis service temporarily unavailable. Please try again later.", "warning")
                return redirect(url_for("main.index"))
            
            diagnosis_results = diagnosis_gen.generate_diagnosis(
                analysis_results,
                symptoms,
                patient_info
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Store results server-side
            results_payload = {
                "image_path": filepath,
                "image_filename": filename,
                "file_size": f"{file_size / (1024*1024):.2f} MB",
                "analysis": analysis_results,
                "symptoms": symptoms,
                "patient_info": patient_info,
                "diagnosis": diagnosis_results['diagnosis'],
                "structured_diagnosis": diagnosis_results['structured_data'],
                "confidence_score": diagnosis_results['confidence_score'],
                "is_medical_image": analysis_results.get('is_medical_image', False),
                "quality_metrics": analysis_results.get('quality_metrics', {}),
                "processing_time": f"{processing_time:.1f}s",
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Generate a short ID and cache the payload for 10 minutes
            result_id = str(uuid.uuid4())
            cache.set(result_id, results_payload, timeout=600)  # 10 minutes timeout
            session["result_id"] = result_id
            
            # Log successful analysis
            current_app.logger.info(f"Successfully analyzed image: {filename}")
            
            return redirect(url_for("main.results"))
        
        except Exception as e:
            current_app.logger.error(f"Error processing image {filename}: {str(e)}")
            
            # Provide user-friendly error messages for common issues
            error_msg = str(e)
            if "overloaded" in error_msg.lower():
                flash("The AI service is currently experiencing high demand. Please try again in a few minutes.", "warning")
            elif "rate limit" in error_msg.lower():
                flash("Rate limit exceeded. Please wait a moment before trying again.", "warning")
            elif "timeout" in error_msg.lower():
                flash("The analysis is taking longer than expected. Please try again.", "warning")
            elif "api key" in error_msg.lower():
                flash("Service configuration error. Please contact support.", "danger")
            else:
                flash(f"Error analyzing image: {error_msg}", "danger")
            
            # Clean up uploaded file
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return redirect(url_for("main.index"))
    
    except Exception as e:
        current_app.logger.error(f"Unexpected error in analyze route: {str(e)}")
        flash("An unexpected error occurred. Please try again.", "danger")
        return redirect(url_for("main.index"))

@main_bp.route("/results", methods=["GET"])
def results():
    """Display the analysis and diagnosis results."""
    result_id = session.get("result_id")
    results_data = cache.get(result_id) if result_id else None
    
    if not results_data:
        flash("No results found. Please submit an image for analysis.", "warning")
        return redirect(url_for("main.index"))
    
    # Add current date and time for the report
    now = datetime.now()
    
    # Format analysis for display
    if isinstance(results_data.get('analysis'), dict):
        # Convert analysis dict to readable format
        analysis_text = _format_analysis_results(results_data['analysis'])
        results_data['analysis_text'] = analysis_text
    
    # Clear the cache and session after displaying results
    if result_id:
        cache.delete(result_id)
        session.pop("result_id", None)
    
    return render_template("results.html", results=results_data, now=now)

@main_bp.route("/download_report/<report_type>", methods=["GET"])
def download_report(report_type):
    """Generate and download report in specified format."""
    result_id = session.get("result_id")
    results_data = cache.get(result_id) if result_id else None
    
    if not results_data:
        flash("No results found to generate report.", "warning")
        return redirect(url_for("main.index"))
    
    try:
        if report_type == "pdf":
            # Generate PDF report (implementation would go here)
            flash("PDF generation feature coming soon!", "info")
            return redirect(url_for("main.results"))
        
        elif report_type == "txt":
            # Generate text report
            report_path = generate_report(results_data, results_data.get('patient_info'))
            return send_file(report_path, as_attachment=True, 
                           download_name=f"MediScan_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        else:
            flash("Invalid report type requested.", "danger")
            return redirect(url_for("main.results"))
    
    except Exception as e:
        current_app.logger.error(f"Error generating report: {str(e)}")
        flash("Error generating report. Please try again.", "danger")
        return redirect(url_for("main.results"))

@main_bp.route("/api/analyze", methods=["POST"])
@limiter.limit("10 per hour")
def api_analyze():
    """API endpoint for image analysis - returns JSON response."""
    try:
        # Check if image file was uploaded
        if "xray_image" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        
        file = request.files["xray_image"]
        
        # Check if file was selected
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type. Please upload PNG, JPG, JPEG, or WebP"}), 400
        
        # Validate file size
        try:
            file_size = validate_file_size(file)
        except RequestEntityTooLarge as e:
            return jsonify({"success": False, "error": str(e)}), 413
        
        # Get symptoms (optional)
        symptoms = sanitize_input(request.form.get("symptoms", ""))
        
        # Generate a unique filename
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        
        # Save the file
        file.save(filepath)
        
        # Record start time
        start_time = time.time()
        
        # Perform analysis
        try:
            # Analyze the image
            analysis_results = image_analyzer.analyze_medical_image(filepath)
            
            # Generate diagnosis
            diagnosis_gen = get_diagnosis_generator()
            if diagnosis_gen is None:
                return jsonify({"success": False, "error": "Diagnosis service temporarily unavailable"}), 503
            
            diagnosis_results = diagnosis_gen.generate_diagnosis(
                analysis_results,
                symptoms
            )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Return JSON response
            response_data = {
                "success": True,
                "diagnosis": diagnosis_results['diagnosis'],
                "confidence_score": diagnosis_results.get('confidence_score', 0),
                "processing_time": f"{processing_time:.1f}s",
                "image_filename": filename,
                "file_size": f"{file_size / (1024*1024):.2f} MB"
            }
            
            current_app.logger.info(f"API analysis successful for {filename}")
            return jsonify(response_data)
        
        except Exception as e:
            current_app.logger.error(f"Error processing image {filename}: {str(e)}")
            return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500
        
    except Exception as e:
        current_app.logger.error(f"API error: {str(e)}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@main_bp.route("/uploads/<filename>")
def uploaded_file(filename):
    """Serve uploaded files from the upload directory."""
    import os
    from flask import send_from_directory
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main_bp.route("/about", methods=["GET"])
@cache.cached(timeout=3600)
def about():
    """Display information about the project."""
    return render_template("about.html")

@main_bp.errorhandler(413)
def request_entity_too_large(e):
    """Handle file too large error."""
    flash("File size exceeds the maximum allowed limit of 16MB.", "danger")
    return redirect(url_for("main.index"))

@main_bp.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded."""
    flash("Rate limit exceeded. Please try again later.", "warning")
    return redirect(url_for("main.index"))

@main_bp.route("/clear_cache", methods=["GET"])
def clear_cache():
    """Clear all cached results for debugging."""
    try:
        # Clear the session
        session.clear()
        
        # Clear all cache (if using simple cache)
        if hasattr(cache, 'clear'):
            cache.clear()
        
        flash("Cache cleared successfully. You can now perform fresh analysis.", "success")
        return redirect(url_for("main.index"))
    
    except Exception as e:
        current_app.logger.error(f"Error clearing cache: {str(e)}")
        flash("Error clearing cache.", "danger")
        return redirect(url_for("main.index"))

def _format_analysis_results(analysis_data):
    """Format analysis dictionary into readable text."""
    lines = []
    
    if not analysis_data.get('is_medical_image'):
        lines.append("⚠️ WARNING: This image may not be a medical image.\n")
    
    if 'quality_metrics' in analysis_data:
        qm = analysis_data['quality_metrics']
        lines.append(f"IMAGE QUALITY: {qm.get('quality_rating', 'Unknown')}")
        lines.append(f"Quality Score: {qm.get('quality_score', 0):.2f}")
        lines.append(f"Sharpness: {qm.get('sharpness', 0):.1f}")
        lines.append(f"Contrast: {qm.get('contrast', 0):.1f}\n")
    
    if 'labels' in analysis_data:
        lines.append("DETECTED FEATURES:")
        for label in analysis_data['labels'][:10]:
            lines.append(f"- {label['description']} ({label['score']:.1%})")
        lines.append("")
    
    if 'objects' in analysis_data:
        lines.append("DETECTED STRUCTURES:")
        for obj in analysis_data['objects'][:10]:
            lines.append(f"- {obj['name']} ({obj['score']:.1%})")
        lines.append("")
    
    if 'statistics' in analysis_data:
        stats = analysis_data['statistics']
        lines.append("IMAGE STATISTICS:")
        lines.append(f"- Mean intensity: {stats.get('mean_intensity', 0):.1f}")
        lines.append(f"- Standard deviation: {stats.get('std_intensity', 0):.1f}")
        lines.append(f"- Contrast: {stats.get('contrast', 0):.1f}")
        lines.append(f"- Entropy: {stats.get('entropy', 0):.1f}")
    
    return "\n".join(lines)