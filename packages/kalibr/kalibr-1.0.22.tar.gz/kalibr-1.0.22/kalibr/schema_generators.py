"""
Multi-model schema generators for different AI platforms
"""
from typing import Dict, Any, List
from abc import ABC, abstractmethod

class BaseSchemaGenerator(ABC):
    """Base class for AI model schema generators"""
    
    @abstractmethod
    def generate_schema(self, actions: Dict, base_url: str) -> Dict[str, Any]:
        """Generate schema for the specific AI model"""
        pass

class MCPSchemaGenerator(BaseSchemaGenerator):
    """Claude MCP schema generator"""
    
    def generate_schema(self, actions: Dict, base_url: str) -> Dict[str, Any]:
        tools = []
        for action_name, action_data in actions.items():
            properties = {}
            required = []
            
            # Construct the input schema for the tool
            for param_name, param_info in action_data["params"].items():
                properties[param_name] = {"type": param_info["type"]}
                if param_info["required"]:
                    required.append(param_name)
            
            tools.append({
                "name": action_name,
                "description": action_data["description"],
                "input_schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                },
                "server": {
                    "url": f"{base_url}/proxy/{action_name}"
                }
            })
        
        return {
            "mcp": "1.0",
            "name": "kalibr-enhanced",
            "tools": tools
        }

class OpenAPISchemaGenerator(BaseSchemaGenerator):
    """GPT Actions OpenAPI schema generator"""
    
    def generate_schema(self, actions: Dict, base_url: str) -> Dict[str, Any]:
        paths = {}
        
        for action_name, action_data in actions.items():
            properties = {}
            required = []
            
            for param_name, param_info in action_data["params"].items():
                properties[param_name] = {"type": param_info["type"]}
                if param_info["required"]:
                    required.append(param_name)
            
            paths[f"/proxy/{action_name}"] = {
                "post": {
                    "summary": action_data["description"],
                    "operationId": action_name,
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": properties,
                                    "required": required
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {"type": "object"}
                                }
                            }
                        }
                    }
                }
            }
        
        return {
            "openapi": "3.0.0",
            "info": {
                "title": "Kalibr Enhanced API",
                "version": "2.0.0",
                "description": "Enhanced Kalibr API with app-level capabilities"
            },
            "servers": [{"url": base_url}],
            "paths": paths
        }

class GeminiSchemaGenerator(BaseSchemaGenerator):
    """Google Gemini Extensions schema generator"""
    
    def generate_schema(self, actions: Dict, base_url: str) -> Dict[str, Any]:
        functions = []
        
        for action_name, action_data in actions.items():
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param_name, param_info in action_data["params"].items():
                parameters["properties"][param_name] = {
                    "type": param_info["type"],
                    "description": f"Parameter {param_name}"
                }
                if param_info["required"]:
                    parameters["required"].append(param_name)
            
            functions.append({
                "name": action_name,
                "description": action_data["description"],
                "parameters": parameters,
                "server": {
                    "url": f"{base_url}/proxy/{action_name}"
                }
            })
        
        return {
            "gemini_extension": "1.0",
            "name": "kalibr_enhanced",
            "description": "Enhanced Kalibr API for Gemini integration",
            "functions": functions
        }

class CopilotSchemaGenerator(BaseSchemaGenerator):
    """Microsoft Copilot plugin schema generator"""
    
    def generate_schema(self, actions: Dict, base_url: str) -> Dict[str, Any]:
        apis = []
        
        for action_name, action_data in actions.items():
            request_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            for param_name, param_info in action_data["params"].items():
                request_schema["properties"][param_name] = {
                    "type": param_info["type"]
                }
                if param_info["required"]:
                    request_schema["required"].append(param_name)
            
            apis.append({
                "name": action_name,
                "description": action_data["description"],
                "url": f"{base_url}/proxy/{action_name}",
                "method": "POST",
                "request_schema": request_schema,
                "response_schema": {
                    "type": "object",
                    "description": "API response"
                }
            })
        
        return {
            "schema_version": "v1",
            "name_for_model": "kalibr_enhanced",
            "name_for_human": "Enhanced Kalibr API",
            "description_for_model": "Enhanced Kalibr API with advanced capabilities",
            "description_for_human": "API for advanced AI model integrations",
            "auth": {
                "type": "none"
            },
            "api": {
                "type": "openapi",
                "url": f"{base_url}/openapi.json"
            },
            "apis": apis
        }

class CustomModelSchemaGenerator(BaseSchemaGenerator):
    """Extensible generator for future AI models"""
    
    def __init__(self, model_name: str, schema_format: str):
        self.model_name = model_name
        self.schema_format = schema_format
    
    def generate_schema(self, actions: Dict, base_url: str) -> Dict[str, Any]:
        # Generic schema format that can be customized
        return {
            "model": self.model_name,
            "format": self.schema_format,
            "version": "2.0.0",
            "base_url": base_url,
            "actions": [
                {
                    "name": name,
                    "description": data["description"],
                    "parameters": data["params"],
                    "endpoint": f"{base_url}/proxy/{name}"
                }
                for name, data in actions.items()
            ]
        }