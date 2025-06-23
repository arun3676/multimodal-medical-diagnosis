"""
Multimodal AI Medical Diagnosis System application factory.
"""
import os
from flask import Flask
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app(test_config=None):
    """
    Create and configure the Flask application.
    
    Args:
        test_config: Test configuration dictionary
        
    Returns:
        Flask application instance
    """
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev"),
        # Save uploaded images inside the static folder so they can be served
        # directly by Flask without an additional route.
        UPLOAD_FOLDER=os.path.join(app.root_path, "static", "uploads"),
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # Max upload size of 16 MB
        ALLOWED_EXTENSIONS={"png", "jpg", "jpeg"},
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path, exist_ok=True)
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    except OSError:
        pass

    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app