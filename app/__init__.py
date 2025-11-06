"""
Multimodal AI Medical Diagnosis System application factory.
Enhanced with modern security, caching, and monitoring features.
"""
import os
import logging
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from dotenv import load_dotenv

# Import our new logging and monitoring components
from app.core.better_stack_handler import setup_better_stack_logging
from app.core.monitoring_middleware import APIMonitoringMiddleware
from app.core.fresh_wandb_monitor import start_new_session, get_fresh_monitor
from app.core.logging_config import setup_logging
from app.config import settings

# Optional Sentry import - won't break if not available
try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    sentry_sdk = None
    FlaskIntegration = None

# Initialize extensions
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=settings.REDIS_URL
)
cache = Cache()

def create_app(test_config=None):
    """
    Create and configure the Flask application with enhanced features.
    
    Args:
        test_config: Test configuration dictionary
        
    Returns:
        Flask application instance
    """
    # Initialize centralized logging first
    setup_logging()
    
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Configure Better Stack logging
    logger = setup_better_stack_logging(settings.BETTER_STACK_SOURCE_TOKEN, settings.LOG_LEVEL)
    app.logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))
    
    # Enhanced configuration
    app.config.from_mapping(
        SECRET_KEY=settings.SECRET_KEY,
        UPLOAD_FOLDER=os.path.join(app.instance_path, "uploads"),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # Max upload size of 16 MB
        ALLOWED_EXTENSIONS={"png", "jpg", "jpeg", "webp"},
        
        # Security headers
        SECURITY_HEADERS={
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        },
        
        # Cache configuration
        CACHE_TYPE=settings.CACHE_TYPE,
        CACHE_REDIS_URL=settings.CACHE_REDIS_URL,
        CACHE_DEFAULT_TIMEOUT=300,
        
        # Session configuration
        SESSION_COOKIE_SECURE=settings.FLASK_ENV == "production",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Initialize Sentry for error tracking in production (optional)
    if SENTRY_AVAILABLE and settings.SENTRY_DSN:
        if settings.SENTRY_DSN.startswith("http"):  # Only init if valid DSN
            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                integrations=[FlaskIntegration()],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1,
            )

    # Initialize extensions with app
    CORS(app, origins=settings.ALLOWED_ORIGINS)
    limiter.init_app(app)
    cache.init_app(app)
    
    # Initialize monitoring middleware
    APIMonitoringMiddleware(app)
    
    # Initialize Fresh W&B monitoring - creates new run for each server start
    session_started = start_new_session()
    if session_started:
        monitor = get_fresh_monitor()
        session_info = monitor.get_session_info()
        app.logger.info(f"🎯 Fresh W&B session started: {session_info['session_id']}")
        app.logger.info(f"📊 Dashboard: https://wandb.ai/arunchukkala-lamar-university/multimodal-medical-diagnosis")
    else:
        app.logger.info("📊 W&B monitoring disabled")

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    except OSError:
        pass

    # Register security headers
    @app.after_request
    def set_security_headers(response):
        for header, value in app.config['SECURITY_HEADERS'].items():
            response.headers[header] = value
        return response

    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Health check endpoint
    @app.route('/health')
    @limiter.exempt
    def health_check():
        return {
            'status': 'healthy', 
            'version': '2.0.0',
            'services': {
                'flask': 'running',
                'gemini': 'available' if settings.GEMINI_API_KEY else 'not_configured',
                'openai': 'available' if settings.OPENAI_API_KEY else 'not_configured'
            }
        }, 200

    return app