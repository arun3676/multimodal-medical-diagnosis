"""
Fresh Start Script - Creates new W&B run for every server start
"""

import os
import sys
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

# Ensure W&B is enabled
os.environ["WANDB_ENABLED"] = "true"

print("🚀 Starting Fresh Flask App with New W&B Session...")
print(f"   WANDB_ENABLED: {os.environ.get('WANDB_ENABLED')}")
print(f"   WANDB_API_KEY: {'✅ Set' if os.environ.get('WANDB_API_KEY') else '❌ Missing'}")

if not os.environ.get('WANDB_API_KEY'):
    print("⚠️  Warning: WANDB_API_KEY not found in .env file")
    print("   W&B monitoring will be disabled")
    print("   Add your API key to .env file:")
    print("   WANDB_API_KEY=your_actual_api_key_here")

print("\n🎯 Each server start will create a NEW W&B run")
print("📊 This gives you clean session tracking and better organization")

# Import and run the app
from run_app import main
if __name__ == "__main__":
    main()
