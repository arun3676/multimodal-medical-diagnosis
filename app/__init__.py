"""
Multimodal AI Medical Diagnosis System application factory.
Enhanced with modern security, caching, and monitoring features.
"""
import os
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from dotenv import load_dotenv
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Load environment variables
load_dotenv()

# Initialize extensions
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=os.getenv("REDIS_URL", "memory://")
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
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    
    # Enhanced configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", os.urandom(32)),
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
        CACHE_TYPE=os.getenv("CACHE_TYPE", "simple"),
        CACHE_REDIS_URL=os.getenv("REDIS_URL"),
        CACHE_DEFAULT_TIMEOUT=300,
        
        # Session configuration
        SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Initialize Sentry for error tracking in production (DISABLED FOR DEBUGGING)
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn and sentry_dsn.startswith("http"):  # Only init if valid DSN
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
        )

    # Initialize extensions with app
    CORS(app, origins=os.getenv("ALLOWED_ORIGINS", "*").split(","))
    limiter.init_app(app)
    cache.init_app(app)

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
    def health_check():
        return {'status': 'healthy', 'version': '2.0.0'}, 200

    return app