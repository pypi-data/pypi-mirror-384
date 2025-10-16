"""
Validator
---------
- Validates MCP manifest structure (lightweight JSONSchema)
- Detects spec drift (compares manifest version vs. embedded known latest)
- Provides 'update-schemas' hook (stub here; can fetch from GH in future)

Note: We keep it offline-safe. You can later wire network fetch if desired.
"""

from __future__ import annotations
from typing import Dict, Any
import json
from jsonschema import validate, Draft7Validator

# Minimal MCP JSON schema (aligned with your generator shape)
MCP_SCHEMA = {
  "type": "object",
  "required": ["mcp", "name", "tools"],
  "properties": {
    "mcp": {"type": "string"},
    "name": {"type": "string"},
    "tools": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "description", "input_schema", "server"],
        "properties": {
          "name": {"type": "string"},
          "description": {"type": "string"},
          "input_schema": {
            "type": "object",
            "required": ["type", "properties"],
            "properties": {
              "type": {"type": "string"},
              "properties": {"type": "object"},
              "required": {"type": "array", "items": {"type": "string"}}
            }
          },
          "server": {
            "type": "object",
            "required": ["url"],
            "properties": {"url": {"type": "string"}}
          }
        }
      }
    }
  }
}

LATEST_MCP_SPEC_VERSION = "1.0"  # bump here as spec evolves

def validate_mcp_manifest(manifest: Dict[str, Any]) -> None:
    # Structural validation
    validate(instance=manifest, schema=MCP_SCHEMA)
    # Version guidance
    version = str(manifest.get("mcp", ""))
    if version != LATEST_MCP_SPEC_VERSION:
        print(f"⚠️  MCP spec version in manifest is '{version}'. Latest known is '{LATEST_MCP_SPEC_VERSION}'.")
        print("    Run `kalibr update-schemas` after updating the SDK, or regenerate the manifest.")

def update_schemas() -> None:
    """
    Stub: In a connected environment, fetch updated schema templates.
    Here, we simply print guidance so the CLI can expose the command now.
    """
    print("🔄 Update schemas (stub):")
    print("   - Upgrade kalibr SDK to latest version: pip install -U kalibr")
    print("   - Re-run manifest generation to pick up spec changes.")

