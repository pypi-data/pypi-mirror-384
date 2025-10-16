"""
Runtime Router
--------------
Abstraction over deployment targets without hosting them ourselves.
Generates minimal configs and invokes the target's CLI/API where possible.

Supported:
- local (uvicorn)
- fly (fly.io)   -> generates fly.toml and basic Dockerfile
- render         -> generates render.yaml

Note: We do not ship vendor SDKs. We shell out to their CLIs if present.
"""

from __future__ import annotations
from pathlib import Path
import subprocess
import shutil
import os
import json
from typing import Dict, Any, Optional, Tuple

HERE = Path(__file__).parent

def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)

def ensure_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content)

def generate_fly_files(app_name: str) -> Tuple[Path, Path]:
    fly_toml = Path("fly.toml")
    dockerfile = Path("Dockerfile")
    ensure_file(fly_toml, f"""# fly.toml
app = "{app_name}"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "off"
  auto_start_machines = true
  min_machines_running = 1
""")
    ensure_file(dockerfile, """# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir fastapi uvicorn typer pydantic requests
EXPOSE 8000
CMD ["python", "-m", "kalibr", "serve", "kalibr_app.py", "--host", "0.0.0.0", "--port", "8000", "--base-url", "http://0.0.0.0:8000"]
""")
    return fly_toml, dockerfile

def generate_render_file(service_name: str) -> Path:
    render_yaml = Path("render.yaml")
    ensure_file(render_yaml, f"""# render.yaml
services:
  - type: web
    name: {service_name}
    env: docker
    plan: free
    dockerfilePath: ./Dockerfile
    autoDeploy: true
""")
    return render_yaml

def deploy_local(app_file: str, host: str = "0.0.0.0", port: int = 8000, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    # Run uvicorn inline (non-blocking not handled here - CLI uses this to print guidance)
    cmd = ["python", "-m", "kalibr", "serve", app_file, "--host", host, "--port", str(port), "--base-url", base_url]
    print("▶︎", " ".join(cmd))
    subprocess.run(cmd, check=False)
    return {
        "status": "started",
        "endpoints": {
            "root": f"{base_url}/",
            "mcp": f"{base_url}/mcp.json",
            "openapi": f"{base_url}/openapi.json",
            "health": f"{base_url}/health"
        }
    }

def deploy_fly(app_name: str) -> Dict[str, Any]:
    if not which("flyctl"):
        raise RuntimeError("flyctl is not installed. See https://fly.io/docs/flyctl/install/")
    # Ensure files exist
    generate_fly_files(app_name)
    # Launch or deploy
    print("▶︎ flyctl apps list")
    subprocess.run(["flyctl", "apps", "list"], check=False)
    print(f"▶︎ flyctl deploy --app {app_name}")
    subprocess.run(["flyctl", "deploy", "--app", app_name], check=False)
    url = f"https://{app_name}.fly.dev"
    return {
        "status": "success",
        "endpoints": {
            "root": f"{url}/",
            "mcp": f"{url}/mcp.json",
            "openapi": f"{url}/openapi.json",
            "health": f"{url}/health"
        }
    }

def deploy_render(service_name: str) -> Dict[str, Any]:
    # We just generate render.yaml and Dockerfile. User connects repo in Render UI.
    generate_render_file(service_name)
    ensure_file(Path("Dockerfile"), """# Dockerfile for Render
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir fastapi uvicorn typer pydantic requests
EXPOSE 8000
CMD ["python", "-m", "kalibr", "serve", "kalibr_app.py", "--host", "0.0.0.0", "--port", "8000", "--base-url", "https://$RENDER_EXTERNAL_URL"]
""")
    print("📄 Generated render.yaml and Dockerfile. Connect your repo in Render.com and auto-deploy.")
    return {
        "status": "success",
        "endpoints": {},
        "note": "Connect this repository to Render; it will build from render.yaml."
    }

def deploy(runtime: str, app_name: str, app_file: str, host: str = "0.0.0.0", port: int = 8000, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    runtime = runtime.lower()
    if runtime in ("local", "dev"):
        return deploy_local(app_file, host, port, base_url)
    if runtime in ("fly", "flyio"):
        return deploy_fly(app_name)
    if runtime == "render":
        return deploy_render(app_name)
    raise ValueError(f"Unknown runtime: {runtime}")

