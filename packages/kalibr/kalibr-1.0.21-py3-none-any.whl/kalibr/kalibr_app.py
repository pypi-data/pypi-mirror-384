from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse as FastAPIStreamingResponse
from typing import Callable, Dict, Any, List, Optional, get_type_hints
import inspect
import asyncio
from datetime import datetime
import uuid
import os

from kalibr.types import FileUpload, Session, WorkflowState


class KalibrApp:
    """
    Enhanced app-level Kalibr framework with advanced capabilities:
    - File upload handling
    - Session management
    - Streaming responses
    - Complex workflows
    - Multi-model schema generation
    """

    def __init__(self, title="Kalibr Enhanced API", version="2.0.0", base_url: Optional[str] = None):
        """
        Initialize the Kalibr enhanced app.
        Automatically determines correct base URL for deployed environments.

        Priority:
        1. Explicit `base_url` passed by user
        2. Env var `KALIBR_BASE_URL`
        3. Env var `FLY_APP_NAME` -> https://<fly_app_name>.fly.dev
        4. Default localhost for dev
        """
        self.app = FastAPI(title=title, version=version)

        if base_url:
            self.base_url = base_url
        elif os.getenv("KALIBR_BASE_URL"):
            self.base_url = os.getenv("KALIBR_BASE_URL")
        elif os.getenv("FLY_APP_NAME"):
            self.base_url = f"https://{os.getenv('FLY_APP_NAME')}.fly.dev"
        else:
            self.base_url = "http://localhost:8000"

        # Storage for different action types
        self.actions: Dict[str, Any] = {}
        self.file_handlers: Dict[str, Any] = {}
        self.session_actions: Dict[str, Any] = {}
        self.stream_actions: Dict[str, Any] = {}
        self.workflows: Dict[str, Any] = {}

        # Session and workflow memory
        self.sessions: Dict[str, Session] = {}
        self.workflow_states: Dict[str, WorkflowState] = {}

        self._setup_routes()

    # -------------------------------------------------------------------------
    # Action registration decorators
    # -------------------------------------------------------------------------

    def action(self, name: str, description: str = ""):
        def decorator(func: Callable):
            self.actions[name] = {
                "func": func,
                "description": description,
                "params": self._extract_params(func),
            }

            endpoint_path = f"/proxy/{name}"

            async def endpoint_handler(request: Request):
                params = {}
                if request.method == "POST":
                    try:
                        body = await request.json()
                        params = body if isinstance(body, dict) else {}
                    except Exception:
                        params = {}
                else:
                    params = dict(request.query_params)

                try:
                    result = func(**params)
                    if inspect.isawaitable(result):
                        result = await result
                    return JSONResponse(content=result)
                except Exception as e:
                    return JSONResponse(content={"error": str(e)}, status_code=500)

            self.app.post(endpoint_path)(endpoint_handler)
            self.app.get(endpoint_path)(endpoint_handler)
            return func

        return decorator

    def file_handler(self, name: str, allowed_extensions: List[str] = None, description: str = ""):
        def decorator(func: Callable):
            self.file_handlers[name] = {
                "func": func,
                "description": description,
                "allowed_extensions": allowed_extensions or [],
                "params": self._extract_params(func),
            }

            endpoint_path = f"/files/{name}"

            async def file_endpoint(file: UploadFile = File(...)):
                try:
                    if allowed_extensions:
                        file_ext = "." + file.filename.split(".")[-1] if "." in file.filename else ""
                        if file_ext not in allowed_extensions:
                            return JSONResponse(
                                content={"error": f"File type {file_ext} not allowed. Allowed: {allowed_extensions}"},
                                status_code=400,
                            )

                    content = await file.read()
                    file_upload = FileUpload(
                        filename=file.filename,
                        content_type=file.content_type or "application/octet-stream",
                        size=len(content),
                        content=content,
                    )

                    result = func(file_upload)
                    if inspect.isawaitable(result):
                        result = await result
                    return JSONResponse(content=result)
                except Exception as e:
                    return JSONResponse(content={"error": str(e)}, status_code=500)

            self.app.post(endpoint_path)(file_endpoint)
            return func

        return decorator

    def session_action(self, name: str, description: str = ""):
        def decorator(func: Callable):
            self.session_actions[name] = {
                "func": func,
                "description": description,
                "params": self._extract_params(func),
            }

            endpoint_path = f"/session/{name}"

            async def session_endpoint(request: Request):
                try:
                    session_id = request.headers.get("X-Session-ID") or request.cookies.get("session_id")
                    if not session_id or session_id not in self.sessions:
                        session_id = str(uuid.uuid4())
                        session = Session(session_id=session_id)
                        self.sessions[session_id] = session
                    else:
                        session = self.sessions[session_id]
                        session.last_accessed = datetime.now()

                    body = await request.json() if request.method == "POST" else {}

                    sig = inspect.signature(func)
                    if "session" in sig.parameters:
                        func_params = {k: v for k, v in body.items() if k != "session"}
                        result = func(session=session, **func_params)
                    else:
                        result = func(**body)

                    if inspect.isawaitable(result):
                        result = await result

                    response = JSONResponse(content=result)
                    response.set_cookie("session_id", session_id)
                    response.headers["X-Session-ID"] = session_id
                    return response
                except Exception as e:
                    return JSONResponse(content={"error": str(e)}, status_code=500)

            self.app.post(endpoint_path)(session_endpoint)
            return func

        return decorator

    def stream_action(self, name: str, description: str = ""):
        def decorator(func: Callable):
            self.stream_actions[name] = {
                "func": func,
                "description": description,
                "params": self._extract_params(func),
            }

            endpoint_path = f"/stream/{name}"

            async def stream_endpoint(request: Request):
                try:
                    params = dict(request.query_params) if request.method == "GET" else {}
                    if request.method == "POST":
                        body = await request.json()
                        params.update(body)

                    sig = inspect.signature(func)
                    type_hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}
                    converted_params = {}
                    for key, value in params.items():
                        if key in sig.parameters:
                            param_type = type_hints.get(key, str)
                            try:
                                if param_type == int:
                                    converted_params[key] = int(value)
                                elif param_type == float:
                                    converted_params[key] = float(value)
                                elif param_type == bool:
                                    converted_params[key] = value.lower() in ("true", "1", "yes")
                                else:
                                    converted_params[key] = value
                            except Exception:
                                converted_params[key] = value

                    result = func(**converted_params)

                    async def generate():
                        import json
                        if inspect.isasyncgen(result):
                            async for item in result:
                                yield json.dumps(item) + "\n"
                        elif inspect.isgenerator(result):
                            for item in result:
                                yield json.dumps(item) + "\n"

                    return FastAPIStreamingResponse(generate(), media_type="application/x-ndjson")
                except Exception as e:
                    return JSONResponse(content={"error": str(e)}, status_code=500)

            self.app.get(endpoint_path)(stream_endpoint)
            self.app.post(endpoint_path)(stream_endpoint)
            return func

        return decorator

    # -------------------------------------------------------------------------
    # Schema generation routes
    # -------------------------------------------------------------------------

    def _setup_routes(self):
        from kalibr.schema_generators import (
            OpenAPISchemaGenerator,
            MCPSchemaGenerator,
            GeminiSchemaGenerator,
            CopilotSchemaGenerator,
        )

        openapi_gen = OpenAPISchemaGenerator()
        mcp_gen = MCPSchemaGenerator()
        gemini_gen = GeminiSchemaGenerator()
        copilot_gen = CopilotSchemaGenerator()

        @self.app.get("/")
        def root():
            return {
                "message": "Kalibr Enhanced API is running",
                "actions": list(self.actions.keys()),
                "schemas": {
                    "gpt_actions": f"{self.base_url}/gpt-actions.json",
                    "claude_mcp": f"{self.base_url}/mcp.json",
                    "gemini": f"{self.base_url}/schemas/gemini",
                    "copilot": f"{self.base_url}/schemas/copilot",
                },
            }

        @self.app.get("/gpt-actions.json")
        def gpt_actions_schema():
            all_actions = {**self.actions, **self.file_handlers, **self.session_actions}
            return openapi_gen.generate_schema(all_actions, self.base_url)

        @self.app.get("/mcp.json")
        def mcp_manifest():
            all_actions = {**self.actions, **self.file_handlers, **self.session_actions}
            return mcp_gen.generate_schema(all_actions, self.base_url)

        @self.app.get("/schemas/gemini")
        def gemini_schema():
            all_actions = {**self.actions, **self.file_handlers, **self.session_actions}
            return gemini_gen.generate_schema(all_actions, self.base_url)

        @self.app.get("/schemas/copilot")
        def copilot_schema():
            all_actions = {**self.actions, **self.file_handlers, **self.session_actions}
            return copilot_gen.generate_schema(all_actions, self.base_url)

        @self.app.get("/health")
        def health_check():
            return {"status": "healthy", "service": "Kalibr Enhanced API"}

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _extract_params(self, func: Callable) -> Dict[str, Any]:
        sig = inspect.signature(func)
        params = {}
        type_hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}

        for param_name, param in sig.parameters.items():
            if param_name in ["session", "workflow_state", "file"]:
                continue

            param_type = "string"
            anno = type_hints.get(param_name, param.annotation)
            if anno == int:
                param_type = "integer"
            elif anno == bool:
                param_type = "boolean"
            elif anno == float:
                param_type = "number"
            elif anno == list:
                param_type = "array"
            elif anno == dict:
                param_type = "object"

            is_required = param.default == inspect.Parameter.empty
            params[param_name] = {"type": param_type, "required": is_required}

        return params
