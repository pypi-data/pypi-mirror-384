"""
Kalibr Deployment Stub
-----------------------
This module provides a lightweight interface for future deployment providers.

Current supported strategy:
- Local (via Uvicorn)

Planned:
- Fly.io
- Render
- Railway

No AWS dependencies are required or used.
"""

import subprocess

def deploy_local(file_path: str):
    """Serve the Kalibr app locally using Uvicorn."""
    subprocess.run(["uvicorn", f"{file_path}:app", "--reload"], check=False)

def deploy_placeholder(file_path: str):
    """Placeholder for future remote deployment support."""
    print(f"🚀 Deployment placeholder: {file_path}")
    print("Coming soon: Fly.io and Render deployment support.")
