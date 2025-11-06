"""
Main entry point for the multimodal medical diagnosis application.
This file provides the create_app() function that Gunicorn expects.
"""

import os
from dotenv import load_dotenv

# 🛡️ PREEMPTIVE W&B ERROR SUPPRESSION - MUST BE FIRST
# This prevents ALL wandb socket/protocol errors before any imports
os.environ["WANDB_SILENT"] = "true"
os.environ["WANDB_CONSOLE"] = "off"
os.environ["WANDB_MODE"] = "offline"  # 🎯 CRITICAL: Prevents ALL socket errors
os.environ["WANDB_RUN_ID"] = "offline-run"
os.environ["WANDB_DIR"] = "/tmp/wandb"
os.environ["WANDB_SERVICE_WAIT"] = "300"
os.environ["WANDB_AGENT_DISABLE_FLAKING"] = "true"
os.environ["WANDB_DISABLE_CODE"] = "true"
os.environ["WANDB_DISABLE_STATS"] = "true"
os.environ["WANDB_DISABLE_GIT"] = "true"
os.environ["WANDB_ARTIFACTS_DISABLED"] = "true"
os.environ["WANDB_ENSURE_DIR"] = "true"
os.environ["WANDB_DISABLE_SERVICE"] = "true"  # 🛡️ EXTRA: Disable service completely
os.environ["WANDB_DISABLE_SYMLINKS"] = "true"  # Prevents symlink errors
os.environ["WANDB_RUN_GROUP"] = "offline"  # Prevents group conflicts

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
