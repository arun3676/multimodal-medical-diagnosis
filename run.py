"""
Entry point for the Multimodal AI Medical Diagnosis System web application.
"""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Get port from environment variable (for Render deployment) or default to 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)