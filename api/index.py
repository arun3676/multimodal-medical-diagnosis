"""
Vercel serverless entrypoint for the Flask app.
Keeps the application code unchanged; simply exposes `app` for Vercel.
"""
import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path so `import app` works when run locally
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app

app = create_app()

# Ensure a writable working directory and upload path only on Vercel serverless
if os.getenv("VERCEL") == "1":
    try:
        os.chdir(os.environ.get("TMPDIR", "/tmp"))
    except Exception:
        pass
    tmp_upload = os.path.join(os.environ.get("TMPDIR", "/tmp"), "uploads")
    os.makedirs(tmp_upload, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = tmp_upload

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Run locally if executed directly; Vercel will import `app` instead
    app.run(debug=False, host="0.0.0.0", port=port)
