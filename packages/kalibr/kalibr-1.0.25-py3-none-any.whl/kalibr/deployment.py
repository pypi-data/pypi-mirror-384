"""
Kalibr Deployment
-----------------
Thin wrapper that forwards to the runtime router.
Keeps a simple API surface for backwards-compat commands.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any
from kalibr.runtime_router import deploy as router_deploy

@dataclass
class DeploymentConfig:
    app_name: str
    memory_mb: int = 512
    timeout_seconds: int = 30
    environment_vars: Dict[str, str] = field(default_factory=dict)

def deploy_app(file_path: str, config: DeploymentConfig, platform: str = "local") -> Dict[str, Any]:
    # Map older "platform" to runtime names used by router
    runtime = {
        "local": "local",
        "fly": "fly",
        "aws-lambda": "local",  # not supported; punt to local
        "render": "render",
    }.get(platform, platform)

    result = router_deploy(runtime=runtime, app_name=config.app_name, app_file=file_path)
    if result.get("status") in ("success", "started"):
        eps = result.get("endpoints", {})
        return {
            "status": "success",
            "endpoints": {
                "root": eps.get("root", ""),
                "mcp": eps.get("mcp", ""),
                "openapi": eps.get("openapi", ""),
                "health": eps.get("health", ""),
            }
        }
    return {"status": "error", "error": "unknown deploy outcome", "raw": result}
