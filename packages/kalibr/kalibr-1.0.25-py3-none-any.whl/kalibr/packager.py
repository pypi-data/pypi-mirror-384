"""
Packager
--------
Create a deployable MCP bundle (code + manifests + metadata).
This does not host anything; it prepares artifacts for any runtime.
"""

from __future__ import annotations
from pathlib import Path
import shutil
import json
import tempfile
from typing import Dict, Any, Optional

DEFAULT_BUNDLE = "kalibr_bundle.zip"

def package_app(app_dir: str = ".", output: str = DEFAULT_BUNDLE, models_supported: Optional[list] = None, kalibr_version: str = "unknown") -> str:
    app_dir = Path(app_dir).resolve()
    out_path = Path(output).resolve()

    # Assemble temp dir with metadata
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        # Copy source tree
        for item in app_dir.iterdir():
            if item.name == out_path.name:
                continue
            dest = tmpdir / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        # Write bundle metadata
        (tmpdir / "kalibr_manifest.json").write_text(json.dumps({
            "kalibr_version": kalibr_version,
            "models_supported": models_supported or ["mcp", "gpt-actions", "gemini", "copilot"],
        }, indent=2))

        # Zip
        shutil.make_archive(out_path.with_suffix(""), "zip", tmpdir)

    return str(out_path)
