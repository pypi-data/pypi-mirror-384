# kalibr/kalibr.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Callable, Dict, Any, get_type_hints
import inspect

class Kalibr:
    """
    A framework for creating API endpoints that can be easily integrated with AI models.
    Kalibr simplifies the process of exposing Python functions as API actions,
    providing automatic documentation, request handling, and metadata generation
    for services like Claude's MCP and OpenAI's function calling.
    """
    def __init__(self, title="Kalibr API", version="1.0.0", base_url="http://localhost:8000"):
        """
        Initializes the Kalibr API.

        Args:
            title (str): The title of the API. Defaults to "Kalibr API".
            version (str): The version of the API. Defaults to "1.0.0".
            base_url (str): The base URL of the API, used for generating tool URLs.
                            Defaults to "http://localhost:8000".
        """
        self.app = FastAPI(title=title, version=version)
        self.base_url = base_url
        self.actions = {}  # Stores registered actions and their metadata
        self._setup_routes()

    def action(self, name: str, description: str = ""):
        """
        Decorator to register a Python function as an API action.

        This decorator automatically handles request routing (both GET and POST),
        parameter extraction, and response formatting. It also generates metadata
        required by AI model integrations.

        Args:
            name (str): The unique name of the action. This will be used as the
                        API endpoint path and in AI model tool definitions.
            description (str): A human-readable description of what the action does.
                               This is used in AI model tool descriptions. Defaults to "".

        Returns:
            Callable: A decorator function.
        """
        def decorator(func: Callable):
            # Store the function and its metadata
            self.actions[name] = {
                "func": func,
                "description": description,
                "params": self._extract_params(func)
            }
            
            # Define the endpoint path for this action
            endpoint_path = f"/proxy/{name}"
            
            # Create a unified handler that accepts both GET (query params) and POST (JSON body)
            async def endpoint_handler(request: Request):
                params = {}
                if request.method == "POST":
                    # For POST requests, try to get parameters from the JSON body
                    try:
                        body = await request.json()
                        params = body if isinstance(body, dict) else {}
                    except Exception:
                        # If JSON parsing fails or body is not a dict, treat as empty params
                        params = {}
                else:
                    # For GET requests, use query parameters
                    params = dict(request.query_params)
                
                # Call the original registered function with extracted parameters
                try:
                    result = func(**params)
                    # If the result is a coroutine, await it
                    if inspect.isawaitable(result):
                        result = await result
                    return JSONResponse(content=result)
                except Exception as e:
                    # Basic error handling for function execution
                    return JSONResponse(content={"error": str(e)}, status_code=500)
            
            # Register both POST and GET endpoints for the same path
            self.app.post(endpoint_path)(endpoint_handler)
            self.app.get(endpoint_path)(endpoint_handler)
            
            return func  # Return the original function
        return decorator
    
    def _extract_params(self, func: Callable) -> Dict:
        """
        Extracts parameter names, types, and requirements from a function's signature.

        This method inspects the function's signature and type hints to generate
        a schema representation of its parameters, suitable for API documentation
        and AI model integrations.

        Args:
            func (Callable): The function to inspect.

        Returns:
            Dict: A dictionary where keys are parameter names and values are dictionaries
                  containing 'type' (JSON schema type) and 'required' (boolean) information.
        """
        sig = inspect.signature(func)
        params = {}
        
        # Get type hints from annotations if available
        type_hints = get_type_hints(func) if hasattr(func, '__annotations__') else {}
        
        for param_name, param in sig.parameters.items():
            param_type = "string"  # Default type if none is inferred
            
            # Determine the annotation for the parameter
            if param_name in type_hints:
                anno = type_hints[param_name]
            elif param.annotation != inspect.Parameter.empty:
                anno = param.annotation
            else:
                anno = str  # Fallback to string if no annotation
            
            # Map common Python types to their JSON schema equivalents
            if anno == int:
                param_type = "integer"
            elif anno == bool:
                param_type = "boolean"
            elif anno == float:
                param_type = "number"
            elif anno == list or anno == dict:
                # For lists and dicts, we can't automatically infer element/key types
                # without more complex introspection or explicit type hints like List[str], Dict[str, int]
                # For simplicity, we'll mark them as general objects/arrays.
                # A more robust implementation might use a library like pydantic for schema generation.
                if anno == list:
                    param_type = "array"
                else:
                    param_type = "object"
            
            # Determine if the parameter is required
            is_required = param.default == inspect.Parameter.empty
            
            params[param_name] = {
                "type": param_type,
                "required": is_required
            }
        
        return params
    
    def _setup_routes(self):
        """
        Sets up the core routes for the Kalibr API.

        This includes:
        - A root endpoint ("/") for basic API status and available actions.
        - Multi-model schema endpoints for all major AI platforms:
          - /openapi.json (GPT Actions)
          - /mcp.json (Claude MCP)
          - /schemas/gemini (Google Gemini)
          - /schemas/copilot (Microsoft Copilot)
        """
        from kalibr.schema_generators import (
            OpenAPISchemaGenerator, 
            MCPSchemaGenerator, 
            GeminiSchemaGenerator, 
            CopilotSchemaGenerator
        )
        
        @self.app.get("/")
        def root():
            """
            Root endpoint providing API status and a list of available actions.
            """
            return {
                "message": "Kalibr API is running", 
                "actions": list(self.actions.keys()),
                "schemas": {
                    "gpt_actions": f"{self.base_url}/gpt-actions.json",
                    "openapi_swagger": f"{self.base_url}/openapi.json",
                    "claude_mcp": f"{self.base_url}/mcp.json",
                    "gemini": f"{self.base_url}/schemas/gemini",
                    "copilot": f"{self.base_url}/schemas/copilot"
                }
            }
        
        # Initialize schema generators
        openapi_gen = OpenAPISchemaGenerator()
        mcp_gen = MCPSchemaGenerator()
        gemini_gen = GeminiSchemaGenerator()
        copilot_gen = CopilotSchemaGenerator()
        
        @self.app.get("/gpt-actions.json")
        def gpt_actions_schema():
            """
            Generates OpenAPI 3.0 schema for GPT Actions integration.
            (Alternative endpoint since /openapi.json is used by FastAPI)
            """
            return openapi_gen.generate_schema(self.actions, self.base_url)
        
        @self.app.get("/mcp.json")
        def mcp_manifest():
            """
            Generates Claude MCP manifest for AI model integration.
            """
            return mcp_gen.generate_schema(self.actions, self.base_url)
        
        @self.app.get("/schemas/gemini")
        def gemini_schema():
            """
            Generates Google Gemini Extensions schema.
            """
            return gemini_gen.generate_schema(self.actions, self.base_url)
        
        @self.app.get("/schemas/copilot")
        def copilot_schema():
            """
            Generates Microsoft Copilot plugin schema.
            """
            return copilot_gen.generate_schema(self.actions, self.base_url)
        
        # Override FastAPI's default OpenAPI generation to include servers configuration
        def custom_openapi():
            """
            Customizes the OpenAPI schema generation for Swagger UI.
            """
            if self.app.openapi_schema:
                return self.app.openapi_schema
            
            from fastapi.openapi.utils import get_openapi
            # Generate the default OpenAPI schema
            openapi_schema = get_openapi(
                title=self.app.title,
                version=self.app.version,
                routes=self.app.routes,
            )
            
            # Add the 'servers' block to the schema
            openapi_schema["servers"] = [{"url": self.base_url}]
            
            self.app.openapi_schema = openapi_schema
            return self.app.openapi_schema
        
        # Assign the custom OpenAPI generator to the FastAPI app
        self.app.openapi = custom_openapi
    
    def get_app(self):
        """
        Returns the FastAPI application instance.

        This allows the Kalibr API to be run using standard ASGI servers like Uvicorn.

        Returns:
            FastAPI: The configured FastAPI application.
        """
        return self.app

if __name__ == '__main__':
    print("Kalibr SDK loaded. Use this class to build your API.")
    print("See the __main__ block for example usage.")