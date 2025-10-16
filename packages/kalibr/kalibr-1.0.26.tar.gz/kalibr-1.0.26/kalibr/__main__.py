import typer
import uvicorn
import sys
import importlib.util
from pathlib import Path
import os
import requests
import json

app = typer.Typer()

def _load_user_module(file: str):
    file_path = Path(file).resolve()
    if not file_path.exists():
        print(f"❌ Error: {file} not found")
        raise typer.Exit(1)
    spec = importlib.util.spec_from_file_location("user_app", file_path)
    if not spec or not spec.loader:
        print(f"❌ Error: Could not load {file}")
        raise typer.Exit(1)
    module = importlib.util.module_from_spec(spec)
    sys.modules["user_app"] = module
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"❌ Error loading {file}: {e}")
        raise typer.Exit(1)
    return module

@app.command()
def serve(
    file: str = typer.Argument("kalibr_app.py", help="Python file with Kalibr app"),
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", "-b"),
):
    """Serve a Kalibr-powered API locally."""
    module = _load_user_module(file)

    # Import Kalibr classes
    from kalibr import Kalibr, KalibrApp
    kalibr_instance = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, Kalibr) or (KalibrApp and isinstance(attr, KalibrApp)):
            kalibr_instance = attr
            kalibr_instance.base_url = base_url
            break
    if not kalibr_instance:
        print(f"❌ Error: No Kalibr/KalibrApp instance found in {file}")
        raise typer.Exit(1)

    if hasattr(kalibr_instance, 'get_app'):
        fastapi_app = kalibr_instance.get_app()
    elif hasattr(kalibr_instance, 'app'):
        fastapi_app = kalibr_instance.app
    else:
        print(f"❌ Error: Kalibr instance has no get_app() method or app attribute")
        raise typer.Exit(1)

    is_enhanced = 'KalibrApp' in str(type(kalibr_instance))
    print(f"🚀 Starting {'Enhanced ' if is_enhanced else ''}Kalibr server from {file}")
    print(f"📍 GPT (OpenAPI):     {base_url}/openapi.json")
    print(f"📍 Claude (MCP):      {base_url}/mcp.json")
    if is_enhanced:
        print(f"📍 Gemini:            {base_url}/schemas/gemini")
        print(f"📍 Copilot:           {base_url}/schemas/copilot")
        print(f"📍 Supported Models:  {base_url}/models/supported")
        print(f"📍 Health Check:      {base_url}/health")
    print(f"📍 Swagger UI:        {base_url}/docs")
    print(f"🔌 Actions registered: {list(kalibr_instance.actions.keys())}")

    uvicorn.run(fastapi_app, host=host, port=port)

@app.command()
def package(
    app_dir: str = typer.Option(".", "--app-dir", "-d", help="Directory containing your app"),
    output: str = typer.Option("kalibr_bundle.zip", "--output", "-o", help="Bundle file"),
    models: str = typer.Option("mcp,gpt-actions,gemini,copilot", "--models", "-m", help="Comma-separated models supported")
):
    """Create a deployable MCP bundle (code + schemas + metadata)."""
    from kalibr.packager import package_app
    try:
        models_supported = [x.strip() for x in models.split(",") if x.strip()]
        # Version best-effort
        try:
            from kalibr import __version__ as kalibr_version
        except Exception:
            kalibr_version = "unknown"
        bundle_path = package_app(app_dir=app_dir, output=output, models_supported=models_supported, kalibr_version=kalibr_version)
        print(f"📦 Bundle created: {bundle_path}")
    except Exception as e:
        print(f"❌ Packaging error: {e}")
        raise typer.Exit(1)

@app.command()
def deploy(
    file: str = typer.Argument(..., help="Python file to serve/deploy (e.g., kalibr_app.py)"),
    name: str = typer.Option("", "--name", "-n", help="App name (defaults to filename)"),
    runtime: str = typer.Option("local", "--runtime", "-r", help="Runtime: local|fly|render"),
    host: str = typer.Option("0.0.0.0", "--host"),
    port: int = typer.Option(8000, "--port"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url"),
):
    """Deploy via runtime router (no hosting burden on Kalibr)."""
    from kalibr.runtime_router import deploy as router_deploy
    file_path = Path(file)
    if not file_path.exists():
        print(f"❌ Error: {file} not found")
        raise typer.Exit(1)
    if not name:
        name = file_path.stem.replace('_', '-').replace('.', '-')
    try:
        result = router_deploy(runtime=runtime, app_name=name, app_file=str(file_path), host=host, port=port, base_url=base_url)
        if result.get("status") in ("success", "started"):
            print("🎉 Deploy OK")
            eps = result.get("endpoints", {})
            if eps:
                print("📍 Endpoints:")
                for k, v in eps.items():
                    print(f"   - {k}: {v}")
        else:
            print("⚠️  Deploy finished with unknown status:", result)
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        raise typer.Exit(1)

@app.command()
def validate(
    url: str = typer.Option("http://localhost:8000/mcp.json", "--mcp-url", help="URL to MCP manifest"),
):
    """Validate MCP manifest against minimal JSON schema & version hint."""
    from kalibr.validator import validate_mcp_manifest
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        manifest = resp.json()
        validate_mcp_manifest(manifest)
        print("✅ MCP manifest looks structurally valid.")
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        raise typer.Exit(1)

@app.command()
def update_schemas():
    """Stub: instruct users to upgrade SDK and regenerate manifests."""
    from kalibr.validator import update_schemas as _upd
    _upd()

@app.command()
def status(
    app_url: str = typer.Argument(..., help="URL of deployed Kalibr app"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information")
):
    """Check status of a deployed Kalibr app."""
    try:
        health_url = f"{app_url.rstrip('/')}/health"
        response = requests.get(health_url, timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ App is healthy at {app_url}")
            print(f"   Version: {health_data.get('version', 'unknown')}")
            print(f"   Features: {health_data.get('features', {})}")
            if verbose:
                schemas = ["mcp.json", "openapi.json", "schemas/gemini", "schemas/copilot"]
                print(f"\n📊 Available AI model schemas:")
                for schema in schemas:
                    schema_url = f"{app_url.rstrip('/')}/{schema}"
                    try:
                        schema_response = requests.get(schema_url, timeout=5)
                        status_emoji = "✅" if schema_response.status_code == 200 else "❌"
                        model_name = schema.replace(".json", "").replace("schemas/", "")
                        print(f"   {status_emoji} {model_name.upper()}: {schema_url}")
                    except:
                        print(f"   ❌ {schema}: Connection failed")
        else:
            print(f"❌ App at {app_url} is not responding (HTTP {response.status_code})")
            raise typer.Exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to {app_url}: {e}")
        raise typer.Exit(1)

@app.command()
def version():
    try:
        from kalibr import __version__
    except (ImportError, AttributeError):
        __version__ = "unknown"
    print(f"Kalibr SDK version: {__version__}")
    print("Enhanced multi-model AI integration framework")
    print("Supports: GPT Actions, Claude MCP, Gemini Extensions, Copilot Plugins")
    print("GitHub: https://github.com/devonakelley/kalibr-sdk")

def main():
    config_file = Path.home() / ".kalibr" / "config.json"
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
            if "api_token" in config and not os.environ.get("KALIBR_TOKEN"):
                os.environ["KALIBR_TOKEN"] = config["api_token"]
        except:
            pass
    app()

if __name__ == "__main__":
    main()
