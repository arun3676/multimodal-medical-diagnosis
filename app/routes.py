"""
Clean routes for the Multimodal Medical Diagnosis System.
Essential functionality only - dual analysis modes (fast/detailed).
"""
import logging
import os
import uuid
import time
from typing import Dict, Any

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
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import httpx

from app.core.groq_vlm_router import GroqVLMRouter
from app.core.whisper_transcriber import WhisperTranscriber
from app.core.vision_classifier import get_classifier, analyze_xray_for_pneumonia
from app.core.security import sanitize_text, is_safe_filename
from app import limiter, cache


logger = logging.getLogger(__name__)

# Create blueprint
main_bp = Blueprint("main", __name__)

# Create shared httpx client
_http_client = httpx.Client()

# Initialize VLM Router
try:
    logger.info("🚀 Initializing VLM Router...")
    _vlm_router = GroqVLMRouter(http_client=_http_client)
    logger.info("✅ VLM Router initialized")
except Exception as exc:
    logger.error("❌ Failed to initialize VLM Router: %s", exc)
    _vlm_router = None

# Initialize Whisper Transcriber
try:
    logger.info("🎙️ Initializing Whisper Transcriber...")
    _whisper_transcriber = WhisperTranscriber(http_client=_http_client)
    logger.info("✅ Whisper Transcriber initialized")
except Exception as exc:
    logger.error("❌ Failed to initialize Whisper: %s", exc)
    _whisper_transcriber = None

# Initialize Fine-tuned Classifier
try:
    logger.info("🫁 Initializing Fine-tuned Classifier...")
    _pneumonia_classifier = get_classifier()
    if _pneumonia_classifier.is_ready():
        logger.info("✅ Fine-tuned Classifier ready")
    else:
        logger.info("ℹ️ Fine-tuned model not available - using VLM fallback")
        _pneumonia_classifier = None
except Exception as exc:
    logger.error("❌ Failed to initialize Classifier: %s", exc)
    _pneumonia_classifier = None


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
    """Sanitize user input."""
    return sanitize_text(text)


def analyze_with_finetuned_model(image_path: str, symptoms: str = "") -> Dict[str, Any]:
    """Analyze X-ray using fine-tuned pneumonia model."""
    try:
        result = analyze_xray_for_pneumonia(image_path)
        if result['success']:
            logger.info(f"✅ Fine-tuned model analysis: {result.get('model_prediction', 'Unknown')}")
            return result
        else:
            logger.warning(f"⚠️ Fine-tuned model failed: {result.get('error', 'Unknown error')}")
            return result
    except Exception as e:
        logger.error(f"❌ Fine-tuned model error: {str(e)}")
        return {
            'success': False,
            'error': f'Fine-tuned model failed: {str(e)}',
            'provider': 'fine_tuned_model',
            'is_medical_image': False,
            'diagnosis': 'Analysis failed',
            'confidence_score': 0.0
        }


def analyze_with_vlm(image_path: str, symptoms: str = "") -> Dict[str, Any]:
    """Analyze image using VLM."""
    try:
        if _vlm_router is None:
            raise Exception("VLM service not available")
        return _vlm_router.analyze_medical_image(image_path, symptoms)
    except Exception as e:
        logger.error(f"❌ VLM analysis failed: {str(e)}")
        raise e


@main_bp.route("/", methods=["GET"])
def index():
    """Render the main page."""
    return render_template("index.html")


@main_bp.route("/api/analyze", methods=["POST"])
@limiter.limit("10 per hour")
@cache.cached(timeout=300, query_string=True)  # Cache for 5 minutes
def api_analyze():
    """Main API endpoint for dual analysis modes."""
    logger.info("🚀 API: /api/analyze called")
    
    try:
        # Validate file upload
        if "xray_image" not in request.files:
            return jsonify({"success": False, "error": "No file uploaded"}), 400
        
        file = request.files["xray_image"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type. Please upload PNG, JPG, JPEG, or WebP"}), 400
        
        # Validate file size
        file_size = validate_file_size(file)
        
        # Get form data
        symptoms = sanitize_input(request.form.get("symptoms", ""))
        analysis_type = sanitize_input(request.form.get("analysis_type", "detailed")).lower()
        if analysis_type not in ["fast", "detailed"]:
            analysis_type = "detailed"
        
        logger.info(f"🎯 Analysis type: {analysis_type}")
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(filepath)
        
        start_time = time.time()
        
        try:
            # Perform analysis based on type
            if analysis_type == "fast":
                # Fast analysis: Fine-tuned model only
                logger.info("🚀 Fast analysis - using fine-tuned model...")
                if _pneumonia_classifier and _pneumonia_classifier.is_ready():
                    try:
                        analysis_results = analyze_with_finetuned_model(filepath, symptoms)
                        if analysis_results['success']:
                            analysis_method = "fast_finetuned"
                            logger.info("✅ Fast analysis successful")
                        else:
                            error_msg = analysis_results.get('error', 'Unknown error')
                            logger.error(f"❌ Fast analysis failed: {error_msg}", exc_info=True)
                            return jsonify({"success": False, "error": f"Fast analysis failed: {error_msg}"}), 500
                    except Exception as fast_error:
                        logger.error(f"❌ CRITICAL: Fast analysis exception: {str(fast_error)}", exc_info=True)
                        return jsonify({"success": False, "error": f"Fast analysis crashed: {str(fast_error)}"}), 500
                else:
                    logger.warning("⚠️ Fine-tuned model not available or not ready")
                    logger.warning(f"⚠️ Classifier status: exists={_pneumonia_classifier is not None}, ready={_pneumonia_classifier.is_ready() if _pneumonia_classifier else False}")
                    return jsonify({"success": False, "error": "Fast analysis not available - fine-tuned model not configured"}), 503
            
            elif analysis_type == "detailed":
                # Detailed analysis: VLM only
                logger.info("🔍 Detailed analysis - using VLM...")
                try:
                    analysis_results = analyze_with_vlm(filepath, symptoms)
                    
                    if 'error' not in analysis_results:
                        analysis_method = "detailed_vlm"
                        logger.info("✅ Detailed analysis successful")
                    else:
                        error_msg = analysis_results.get('error', 'Unknown error')
                        logger.error(f"❌ Detailed analysis failed: {error_msg}", exc_info=True)
                        return jsonify({"success": False, "error": f"Detailed analysis failed: {error_msg}"}), 500
                except Exception as detailed_error:
                    logger.error(f"❌ CRITICAL: Detailed analysis exception: {str(detailed_error)}", exc_info=True)
                    return jsonify({"success": False, "error": f"Detailed analysis crashed: {str(detailed_error)}"}), 500
            
            # Validate analysis results
            if 'error' in analysis_results:
                error_msg = analysis_results.get('error', 'Analysis failed')
                logger.error(f"❌ Analysis validation failed: {error_msg}")
                raise Exception(error_msg)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Extract diagnosis data
            diagnosis_results = {
                'diagnosis': analysis_results.get('overall_impression', '') or analysis_results.get('diagnosis', ''),
                'overall_assessment': analysis_results.get('overall_assessment', 'Analysis Complete'),
                'structured_data': {
                    'findings': analysis_results.get('findings', []),
                    'recommendations': analysis_results.get('recommendations', []),
                    'urgency': analysis_results.get('urgency', 'routine'),
                    'image_type': analysis_results.get('image_type', 'unknown')
                },
                'confidence_score': analysis_results.get('confidence_score', 0.0)
            }
            
            # Build response
            response_data = {
                "success": True,
                "diagnosis": diagnosis_results['diagnosis'],
                "overall_assessment": diagnosis_results.get('overall_assessment', 'Analysis Complete'),
                "confidence_score": diagnosis_results.get('confidence_score', 0),
                "processing_time": f"{processing_time:.1f}s",
                "image_filename": filename,
                "file_size": f"{file_size / (1024*1024):.2f} MB",
                "vision_provider": analysis_results.get('provider', 'openai'),
                "analysis_type": analysis_type,
                "analysis_method": analysis_method,
            }
            
            # Add analysis-specific data
            if analysis_type == "fast":
                response_data["model_prediction"] = analysis_results.get('model_prediction', '')
                response_data["model_probabilities"] = analysis_results.get('model_probabilities', {})
                response_data["analysis_description"] = "Fast pneumonia detection using fine-tuned CNN model"
            elif analysis_type == "detailed":
                response_data["findings"] = analysis_results.get('findings', [])
                response_data["recommendations"] = analysis_results.get('recommendations', [])
                response_data["urgency"] = analysis_results.get('urgency', 'routine')
                response_data["analysis_description"] = "Comprehensive analysis using Vision Language Model"
            
            logger.info(f"✅ Analysis completed in {processing_time:.1f}s")
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"❌ FATAL: Analysis exception: {str(e)}", exc_info=True)
            logger.error(f"❌ Exception type: {type(e).__name__}")
            logger.error(f"❌ Analysis type attempted: {analysis_type}")
            logger.error(f"❌ File path: {filepath}")
            return jsonify({"success": False, "error": f"Analysis failed: {str(e)}"}), 500
        
        finally:
            # Clean up uploaded file
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"🧹 Cleaned up file: {filepath}")
            except Exception as cleanup_error:
                logger.warning(f"⚠️ Cleanup error: {cleanup_error}")
    
    except Exception as e:
        logger.error(f"❌ FATAL: General exception in /api/analyze: {str(e)}", exc_info=True)
        logger.error(f"❌ Exception type: {type(e).__name__}")
        return jsonify({"success": False, "error": f"Request failed: {str(e)}"}), 500


@main_bp.route("/api/transcribe", methods=["POST"])
@limiter.limit("10 per hour")
def api_transcribe():
    """Audio transcription endpoint."""
    try:
        if "audio_file" not in request.files:
            return jsonify({"success": False, "error": "No audio file uploaded"}), 400
        
        file = request.files["audio_file"]
        if file.filename == "":
            return jsonify({"success": False, "error": "No audio file selected"}), 400
        
        # Validate audio file
        allowed_audio_extensions = {"wav", "mp3", "m4a", "ogg", "flac"}
        if "." not in file.filename or file.filename.rsplit(".", 1)[1].lower() not in allowed_audio_extensions:
            return jsonify({"success": False, "error": "Invalid audio format. Please upload WAV, MP3, M4A, OGG, or FLAC"}), 400
        
        # Check file size (max 25MB)
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        
        max_audio_size = 25 * 1024 * 1024  # 25MB
        if file_size > max_audio_size:
            return jsonify({"success": False, "error": f"Audio file size exceeds {max_audio_size // (1024*1024)}MB limit"}), 413
        
        # Save temporary file
        import tempfile
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)
        
        try:
            # Transcribe audio
            if _whisper_transcriber is None:
                return jsonify({"success": False, "error": "Transcription service unavailable"}), 503
            
            result = _whisper_transcriber.transcribe_audio(temp_path)
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            if "error" in result:
                return jsonify({"success": False, "error": result["error"]}), 500
            
            return jsonify({
                "success": True,
                "symptoms": result.get("symptoms", ""),
                "duration": result.get("duration", 0.0),
                "transcription": result.get("transcription", ""),
                "provider": result.get("provider", "unknown")
            })
            
        except Exception as e:
            # Clean up on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e
            
    except Exception as e:
        logger.error(f"Error in audio transcription: {str(e)}")
        return jsonify({"success": False, "error": f"Transcription failed: {str(e)}"}), 500


@main_bp.route("/health")
@limiter.exempt
def health_check():
    """Health check endpoint."""
    return {
        'status': 'healthy', 
        'version': '2.0.0',
        'services': {
            'flask': 'running',
            'openai': 'available' if os.getenv("OPENAI_API_KEY") else 'not_configured',
            'gemini': 'available' if os.getenv("GEMINI_API_KEY") else 'not_configured'
        }
    }, 200


@main_bp.route("/api/re_analyze", methods=["POST"])
@limiter.limit("10 per hour")
def api_re_analyze():
    """API endpoint for re-analyzing an existing image with detailed analysis."""
    logger.info("🚀 API: /api/re_analyze called")
    
    try:
        data = request.get_json()
        if not data or "filename" not in data:
            return jsonify({"success": False, "error": "Missing filename"}), 400
            
        filename = data["filename"]
        
        # Security: ensure filename is safe
        if not is_safe_filename(filename):
            return jsonify({"success": False, "error": "Invalid filename"}), 400
            
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "File not found"}), 404
            
        symptoms = sanitize_input(data.get("symptoms", ""))
        
        start_time = time.time()
        
        # Perform detailed analysis
        analysis_results = analyze_with_vlm(filepath, symptoms)
        
        if 'error' in analysis_results:
            return jsonify({"success": False, "error": f"Detailed analysis failed: {analysis_results.get('error', 'Unknown error')}"}), 500
            
        processing_time = time.time() - start_time
        
        # Build and return the response
        response_data = {
            "success": True,
            "diagnosis": analysis_results.get('diagnosis', ''),
            "overall_assessment": analysis_results.get('overall_assessment', 'Analysis Complete'),
            "confidence_score": analysis_results.get('confidence_score', 0),
            "processing_time": f"{processing_time:.1f}s",
            "image_filename": filename,
            "vision_provider": analysis_results.get('provider', 'openai'),
            "analysis_type": "detailed",
            "analysis_method": "detailed_vlm",
            "findings": analysis_results.get('findings', []),
            "recommendations": analysis_results.get('recommendations', []),
            "urgency": analysis_results.get('urgency', 'routine'),
            "analysis_description": "Comprehensive analysis using Vision Language Model"
        }
        
        logger.info(f"✅ Re-analysis completed in {processing_time:.1f}s")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Re-analysis exception: {str(e)}")
        return jsonify({"success": False, "error": f"Re-analysis failed: {str(e)}"}), 500
