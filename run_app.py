"""
Main entry point for the multimodal medical diagnosis application.
This file provides the create_app() function that Gunicorn expects.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Application factory function for Gunicorn."""
    from app import create_app as app_factory
    return app_factory()

def main():
    """Main function for running the app directly."""
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()
