import typer
import uvicorn
import sys
import importlib.util
from pathlib import Path
import os
import requests
import json
import zipfile
import tempfile

# Initialize a Typer application
app = typer.Typer()

@app.command()
def serve(
    file: str = typer.Argument("kalibr_app.py", help="Python file with Kalibr app"),
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
    base_url: str = typer.Option("http://localhost:8000", "--base-url", "-b"),
    app_mode: bool = typer.Option(False, "--app-mode", "-a", help="Use enhanced KalibrApp instead of basic Kalibr")
):
    """Serve a Kalibr-powered API locally."""

    # Resolve the file path to an absolute path
    file_path = Path(file).resolve()
    # Check if the specified file exists
    if not file_path.exists():
        print(f"❌ Error: {file} not found")
        raise typer.Exit(1)

    # Create a module spec from the file location
    spec = importlib.util.spec_from_file_location("user_app", file_path)
    if not spec or not spec.loader:
        print(f"❌ Error: Could not load {file}")
        raise typer.Exit(1)

    # Create a new module from the spec
    module = importlib.util.module_from_spec(spec)
    # Add the module to sys.modules so it can be imported
    sys.modules["user_app"] = module

    try:
        # Execute the module's code
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"❌ Error loading {file}: {e}")
        raise typer.Exit(1)

    # Import Kalibr classes
    from kalibr import Kalibr, KalibrApp
    kalibr_instance = None

    # Iterate through the attributes of the loaded module
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        # Check if the attribute is an instance of Kalibr (or KalibrApp when implemented)
        if isinstance(attr, Kalibr) or (KalibrApp and isinstance(attr, KalibrApp)):
            kalibr_instance = attr
            # Override the base_url of the Kalibr instance if the --base-url flag was provided
            kalibr_instance.base_url = base_url
            break

    # If no Kalibr instance was found, raise an error
    if not kalibr_instance:
        print(f"❌ Error: No Kalibr/KalibrApp instance found in {file}")
        raise typer.Exit(1)

    # Get the FastAPI application from the Kalibr/KalibrApp instance
    if hasattr(kalibr_instance, 'get_app'):
        fastapi_app = kalibr_instance.get_app()
    elif hasattr(kalibr_instance, 'app'):
        fastapi_app = kalibr_instance.app
    else:
        print(f"❌ Error: Kalibr instance has no get_app() method or app attribute")
        raise typer.Exit(1)

    # Print server information
    is_enhanced = KalibrApp is not None and isinstance(kalibr_instance, KalibrApp)
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
    
    if is_enhanced:
        print(f"📁 File handlers: {list(kalibr_instance.file_handlers.keys())}")
        print(f"🌊 Stream actions: {list(kalibr_instance.stream_actions.keys())}")
        print(f"⚡ Workflows: {list(kalibr_instance.workflows.keys())}")

    # Run the FastAPI application using uvicorn
    uvicorn.run(fastapi_app, host=host, port=port)

@app.command()
def deploy(
    file: str = typer.Argument(..., help="Python file to deploy"),
    app_name: str = typer.Option("", "--name", "-n", help="App name (defaults to filename)"),
    platform: str = typer.Option("fly", "--platform", "-p", help="Deployment platform (fly, aws-lambda)"),
    memory: int = typer.Option(512, "--memory", help="Memory allocation in MB"),
    timeout: int = typer.Option(30, "--timeout", help="Timeout in seconds"),
    env_file: str = typer.Option("", "--env-file", help="Environment variables file")
):
    """Deploy a Kalibr app to your own cloud infrastructure."""
    
    from kalibr.deployment import deploy_app, DeploymentConfig
    
    # Check if file exists
    file_path = Path(file)
    if not file_path.exists():
        print(f"❌ Error: {file} not found")
        raise typer.Exit(1)
    
    # Generate app name from filename if not provided
    if not app_name:
        app_name = file_path.stem.replace('_', '-').replace('.', '-')
    
    print(f"🚀 Deploying {file} as '{app_name}' to {platform}...")
    
    # Load environment variables
    env_vars = {}
    if env_file and Path(env_file).exists():
        with open(env_file) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    # Create deployment config
    config = DeploymentConfig(
        app_name=app_name,
        memory_mb=memory,
        timeout_seconds=timeout,
        environment_vars=env_vars
    )
    
    try:
        result = deploy_app(str(file_path), config, platform)
        
        if result["status"] == "success":
            print("🎉 Deployment successful!")
            print("\n📍 Your app is live at:")
            for name, url in result["endpoints"].items():
                print(f"   {name.upper()}: {url}")
            
            print(f"\n🔗 Test it now:")
            print(f"   curl {result['endpoints']['health']}")
            
            print(f"\n🤖 Connect to AI models:")
            print(f"   GPT Actions: {result['endpoints']['openapi']}")
            print(f"   Claude MCP: {result['endpoints']['mcp']}")
            
        else:
            print(f"❌ Deployment failed: {result.get('error', 'Unknown error')}")
            if result.get('logs'):
                print(f"\n📋 Logs:")
                print(result['logs'])
            raise typer.Exit(1)
            
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        raise typer.Exit(1)

@app.command()
def status(
    app_url: str = typer.Argument(..., help="URL of deployed app"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information")
):
    """Check status of a deployed Kalibr app."""
    
    try:
        # Check health endpoint
        health_url = f"{app_url.rstrip('/')}/health"
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ App is healthy at {app_url}")
            print(f"   Version: {health_data.get('version', 'unknown')}")
            print(f"   Features: {health_data.get('features', {})}")
            
            if verbose:
                # Check available schemas
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
def list_platforms():
    """List available deployment platforms and their requirements."""
    
    print("🚀 Available Deployment Platforms:")
    print()
    
    platforms = [
        {
            "name": "Fly.io",
            "command": "fly",
            "requirements": [
                "Install flyctl: https://fly.io/docs/flyctl/install/",
                "Login: flyctl auth login",
                "Create app: flyctl apps create your-app-name"
            ],
            "example": "kalibr deploy my_app.py --platform fly --name my-api"
        },
        {
            "name": "AWS Lambda", 
            "command": "aws-lambda",
            "requirements": [
                "Install AWS CLI: https://aws.amazon.com/cli/",
                "Configure credentials: aws configure",
                "Set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
            ],
            "example": "kalibr deploy my_app.py --platform aws-lambda --name my-api"
        }
    ]
    
    for platform in platforms:
        print(f"📦 {platform['name']}")
        print(f"   Command: --platform {platform['command']}")
        print("   Setup Requirements:")
        for req in platform['requirements']:
            print(f"     • {req}")
        print(f"   Example: {platform['example']}")
        print()
    
    print("💡 Tips:")
    print("   • Use --env-file to load environment variables")
    print("   • Check deployment status with: kalibr status <app-url>")
    print("   • Test locally first with: kalibr serve my_app.py")

@app.command()
def setup(
    platform: str = typer.Argument(..., help="Platform to setup (fly, aws)")
):
    """Setup deployment platform credentials and configuration."""
    
    if platform == "fly":
        print("🚀 Setting up Fly.io deployment...")
        print()
        print("📋 Required steps:")
        print("1. Install flyctl:")
        print("   • macOS: brew install flyctl")  
        print("   • Windows: iwr https://fly.io/install.ps1 -useb | iex")
        print("   • Linux: curl -L https://fly.io/install.sh | sh")
        print()
        print("2. Create account and login:")
        print("   flyctl auth signup")
        print("   # or")
        print("   flyctl auth login") 
        print()
        print("3. Create your app:")
        print("   flyctl apps create your-app-name")
        print()
        print("✅ After setup, deploy with:")
        print("   kalibr deploy my_app.py --platform fly --name your-app-name")
        
    elif platform == "aws":
        print("☁️  Setting up AWS deployment...")
        print()
        print("📋 Required steps:")
        print("1. Install AWS CLI:")
        print("   • https://aws.amazon.com/cli/")
        print()
        print("2. Configure credentials:")
        print("   aws configure")
        print("   # Enter your Access Key ID and Secret Access Key")
        print()
        print("3. Set environment variables (alternative):")
        print("   export AWS_ACCESS_KEY_ID=your_access_key") 
        print("   export AWS_SECRET_ACCESS_KEY=your_secret_key")
        print("   export AWS_DEFAULT_REGION=us-east-1")
        print()
        print("✅ After setup, deploy with:")
        print("   kalibr deploy my_app.py --platform aws-lambda --name your-app")
        
    else:
        print(f"❌ Unknown platform: {platform}")
        print("Available platforms: fly, aws")
        print("Run 'kalibr list-platforms' for more details")
        raise typer.Exit(1)

@app.command()
def init(
    template: str = typer.Option("basic", "--template", "-t", help="Template type (basic, enhanced, auth, analytics)"),
    name: str = typer.Option("My API", "--name", "-n", help="API name")
):
    """Generate a starter Kalibr app with various templates."""
    
    templates = {
        "basic": {
            "filename": "kalibr_app.py",
            "content": f'''from kalibr import Kalibr

# Create your Kalibr API
app = Kalibr(title="{name}", base_url="http://localhost:8000")

@app.action("hello", "Say hello to someone")
def hello(name: str = "World"):
    return {{"message": f"Hello, {{name}}!"}}

@app.action("add_contact", "Add a CRM contact")
def add_contact(name: str, email: str):
    return {{"status": "success", "contact": {{"name": name, "email": email}}}}

@app.action("calculate", "Perform basic math operations")
def calculate(operation: str, a: float, b: float):
    operations = {{
        "add": a + b,
        "subtract": a - b,
        "multiply": a * b,
        "divide": a / b if b != 0 else "Cannot divide by zero"
    }}
    return {{"result": operations.get(operation, "Invalid operation")}}

# Deploy with: kalibr deploy kalibr_app.py --platform fly --name my-api
''',
            "description": "Basic Kalibr app with simple actions"
        },
        
        "enhanced": {
            "filename": "enhanced_app.py", 
            "content": f'''from kalibr import KalibrApp
from kalibr.types import FileUpload, Session, StreamingResponse
import asyncio

# Create enhanced Kalibr app
app = KalibrApp(title="{name}", base_url="http://localhost:8000")

@app.action("hello", "Say hello with enhanced features")
def hello(name: str = "World"):
    return {{"message": f"Hello, {{name}}!", "timestamp": "2024-01-01T00:00:00Z"}}

@app.file_handler("analyze_file", [".txt", ".json", ".csv"])
async def analyze_file(file: FileUpload):
    # Analyze uploaded files
    content = file.content.decode('utf-8')
    return {{
        "filename": file.filename,
        "size": file.size,
        "lines": len(content.split('\\n')),
        "words": len(content.split()),
        "upload_id": file.upload_id
    }}

@app.session_action("save_preference", "Save user preference")
async def save_preference(session: Session, key: str, value: str):
    session.set(key, value)
    return {{"saved": {{key: value}}, "session_id": session.session_id}}

@app.stream_action("count_progress", "Stream counting progress")
async def count_progress(max_count: int = 10):
    for i in range(max_count + 1):
        yield {{
            "count": i,
            "progress": i / max_count * 100,
            "message": f"Progress: {{i}}/{{max_count}}"
        }}
        await asyncio.sleep(0.5)

# Deploy with: kalibr deploy enhanced_app.py --platform fly --name my-enhanced-api
''',
            "description": "Enhanced app with file uploads, sessions, and streaming"
        },
        
        "auth": {
            "filename": "auth_app.py",
            "content": f'''from kalibr import KalibrApp
from kalibr.auth_helpers import KalibrAuth, InMemoryUserStore, KalibrUser
from fastapi import Depends, HTTPException
import os

# Create app with authentication
app = KalibrApp(title="{name} (with Auth)", base_url="http://localhost:8000")

# Setup authentication
auth = KalibrAuth(secret_key=os.environ.get("SECRET_KEY", "your-secret-key-here"))
user_store = InMemoryUserStore()

# Create dependency for protected routes
async def get_current_user(token_payload = Depends(auth.create_auth_dependency(user_store.get_user))):
    return token_payload

# Public endpoints
@app.action("public_hello", "Public greeting (no auth required)")
def public_hello(name: str = "World"):
    return {{"message": f"Hello, {{name}}! This is a public endpoint."}}

@app.action("register", "Register a new user")
async def register(username: str, email: str, password: str):
    try:
        user = user_store.create_user(username, email, password)
        token = auth.create_access_token({{"sub": user.id}})
        return {{
            "message": "User registered successfully",
            "user": {{"id": user.id, "username": user.username}},
            "token": token
        }}
    except ValueError as e:
        raise HTTPException(400, str(e))

@app.action("login", "Login user and get token")
async def login(email: str, password: str):
    user = user_store.get_user_by_email(email)
    if not user or not user_store.verify_password(user.id, password):
        raise HTTPException(401, "Invalid credentials")
    
    token = auth.create_access_token({{"sub": user.id}})
    return {{
        "message": "Login successful", 
        "user": {{"id": user.id, "username": user.username}},
        "token": token
    }}

# Protected endpoints
@app.action("protected_hello", "Protected greeting (requires auth)")
async def protected_hello(name: str = "User", current_user: KalibrUser = Depends(get_current_user)):
    return {{
        "message": f"Hello, {{name}}! You are authenticated as {{current_user.username}}",
        "user_id": current_user.id
    }}

# Deploy with: kalibr deploy auth_app.py --platform fly --name my-auth-api --env-file .env
# Create .env file with: SECRET_KEY=your-actual-secret-key-here
''',
            "description": "App with built-in user authentication and protected routes"
        },
        
        "analytics": {
            "filename": "analytics_app.py", 
            "content": f'''from kalibr import KalibrApp
from kalibr.analytics import kalibr_analytics, MetricsCollector
from kalibr.types import FileUpload

# Create app with built-in analytics
@kalibr_analytics(storage="file", auto_track=True)
class AnalyticsApp(KalibrApp):
    def __init__(self):
        super().__init__(title="{name} (with Analytics)", base_url="http://localhost:8000")

app = AnalyticsApp()

@app.action("hello", "Say hello with automatic analytics tracking")
def hello(name: str = "World"):
    # This call is automatically tracked for analytics
    return {{"message": f"Hello, {{name}}!"}}

@app.action("process_data", "Process some data with custom analytics")
def process_data(data: str, process_type: str = "basic"):
    # Record custom analytics event
    app.record_custom_event("data_processing", 
                           data_length=len(data), 
                           process_type=process_type)
    
    result = {{
        "processed": True,
        "input_length": len(data),
        "output_length": len(data) * 2,  # Simulated processing
        "type": process_type
    }}
    return result

@app.action("get_analytics", "Get analytics for this app")
def get_analytics():
    # Get built-in analytics
    analytics = app.get_analytics()
    return {{
        "analytics": analytics,
        "note": "Analytics are automatically tracked for all action calls"
    }}

# File handler with analytics
@app.file_handler("upload_with_analytics", [".txt", ".json"])
async def upload_with_analytics(file: FileUpload):
    # Custom analytics for file uploads
    app.record_custom_event("file_upload",
                           filename=file.filename,
                           file_size=file.size,
                           file_type=file.content_type)
    
    return {{
        "uploaded": file.filename,
        "size": file.size,
        "analytics_recorded": True
    }}

# Deploy with: kalibr deploy analytics_app.py --platform fly --name my-analytics-api
# Analytics data will be saved to kalibr_analytics.jsonl
''',
            "description": "App with built-in analytics and metrics tracking"
        }
    }
    
    if template not in templates:
        print(f"❌ Unknown template: {template}")
        print(f"Available templates: {', '.join(templates.keys())}")
        raise typer.Exit(1)
    
    template_info = templates[template]
    filename = template_info["filename"]
    
    # Write the template file
    with open(filename, "w") as f:
        f.write(template_info["content"])
    
    print(f"✅ Created {filename}")
    print(f"📝 {template_info['description']}")
    print()
    print(f"🚀 Next steps:")
    print(f"   1. Test locally: kalibr serve {filename}")
    print(f"   2. Deploy: kalibr deploy {filename} --platform fly --name my-app")
    print(f"   3. Check status: kalibr status https://my-app.fly.dev")
    
    if template == "auth":
        print(f"\n🔒 Don't forget to:")
        print(f"   • Create .env file with SECRET_KEY=your-secret-key")
        print(f"   • Use --env-file .env when deploying")
    
    if template == "analytics":
        print(f"\n📊 Analytics features:")
        print(f"   • Automatic tracking of all API calls")
        print(f"   • Custom event recording")
        print(f"   • Built-in metrics endpoint")

@app.command()  
def test(
    url: str = typer.Option("http://localhost:8000", "--url", "-u", help="Base URL of Kalibr server"),
    action: str = typer.Option("", "--action", "-a", help="Specific action to test")
):
    """Test a running Kalibr server."""
    import requests
    import json
    
    try:
        # Test health endpoint
        health_response = requests.get(f"{url}/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print("✅ Server is healthy!")
            print(f"Version: {health_data.get('version', 'unknown')}")
            print(f"Features: {health_data.get('features', {})}")
        
        # Get available actions
        root_response = requests.get(f"{url}/")
        if root_response.status_code == 200:
            root_data = root_response.json()
            actions = root_data.get("actions", [])
            print(f"📋 Available actions: {actions}")
            
            if action and action in actions:
                # Test specific action
                test_data = {"test": "data"}
                action_response = requests.post(f"{url}/proxy/{action}", json=test_data)
                print(f"🧪 Testing {action}: {action_response.status_code}")
                print(f"Response: {action_response.json()}")
        
        # Test schema endpoints
        schemas = ["mcp", "openapi", "gemini", "copilot"]
        print("\n📊 Schema endpoints:")
        for schema_type in schemas:
            schema_url = f"{url}/schemas/{schema_type}" if schema_type in ["gemini", "copilot"] else f"{url}/{schema_type}.json"
            try:
                schema_response = requests.get(schema_url)
                status = "✅" if schema_response.status_code == 200 else "❌"
                print(f"{status} {schema_type}: {schema_url}")
            except:
                print(f"❌ {schema_type}: {schema_url}")
                
    except requests.ConnectionError:
        print(f"❌ Could not connect to {url}")
        print("Make sure the Kalibr server is running")

@app.command()
def examples():
    """Copy example files to current directory."""
    import shutil
    from pathlib import Path
    import sys
    import kalibr
    
    # Find examples directory - check multiple possible locations
    kalibr_path = Path(kalibr.__file__).parent
    
    # Location 1: Sibling to kalibr package (development install)
    examples_src = kalibr_path.parent / "examples"
    
    # Location 2: In site-packages parent (wheel install with data_files)
    if not examples_src.exists():
        site_packages = Path(kalibr.__file__).parent.parent
        examples_src = site_packages.parent / "examples"
    
    # Location 3: Check sys.prefix/examples
    if not examples_src.exists():
        examples_src = Path(sys.prefix) / "examples"
    
    if not examples_src.exists():
        print(f"❌ Examples directory not found.")
        print(f"   Checked locations:")
        print(f"   - {kalibr_path.parent / 'examples'}")
        print(f"   - {Path(kalibr.__file__).parent.parent.parent / 'examples'}")
        print(f"   - {Path(sys.prefix) / 'examples'}")
        print("This might happen if kalibr was installed without examples.")
        raise typer.Exit(1)
    
    # Copy to current directory
    examples_dest = Path.cwd() / "kalibr_examples"
    
    if examples_dest.exists():
        print(f"⚠️  Directory 'kalibr_examples' already exists")
        overwrite = typer.confirm("Do you want to overwrite it?")
        if not overwrite:
            print("Cancelled.")
            raise typer.Exit(0)
        shutil.rmtree(examples_dest)
    
    shutil.copytree(examples_src, examples_dest)
    
    print(f"✅ Examples copied to: {examples_dest}")
    print(f"\n📚 Available examples:")
    for example in examples_dest.glob("*.py"):
        print(f"   - {example.name}")
    
    print(f"\n🚀 Try running:")
    print(f"   kalibr-connect serve kalibr_examples/basic_kalibr_example.py")
    print(f"   kalibr-connect serve kalibr_examples/enhanced_kalibr_example.py")

@app.command()
def version():
    """Show Kalibr version information."""
    try:
        from kalibr import __version__
    except (ImportError, AttributeError):
        __version__ = "unknown"
    
    print(f"Kalibr SDK version: {__version__}")
    print("Enhanced multi-model AI integration framework")
    print("Supports: GPT Actions, Claude MCP, Gemini Extensions, Copilot Plugins")
    print("GitHub: https://github.com/devonakelley/kalibr-sdk")

def main():
    # Load config file if it exists for token
    config_file = Path.home() / ".kalibr" / "config.json"
    if config_file.exists():
        try:
            config = json.loads(config_file.read_text())
            if "api_token" in config and not os.environ.get("KALIBR_TOKEN"):
                os.environ["KALIBR_TOKEN"] = config["api_token"]
        except:
            pass  # Ignore config file errors
    
    # Run the Typer application
    app()

if __name__ == "__main__":
    main()