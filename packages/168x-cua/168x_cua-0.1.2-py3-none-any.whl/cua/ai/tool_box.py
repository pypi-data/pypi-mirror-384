import logging
logger = logging.getLogger(__name__)

from pydantic import BaseModel
import asyncio


class ToolResult(BaseModel):
    id : str | None = None
    text : str | None = None
    base64_png_list : list[str] | None = None
     
    def __str__(self) -> str:
        return f"text: {self.text}, base64_png: {self.base64_png[:10] if self.base64_png else None}, base64_png_list: {len(self.base64_png_list) if self.base64_png_list else None}"


class Tool:
    def __init__(self, name: str, description: str, input_model: type[BaseModel], create_ui_message: bool = True):
        self.name = name
        self.description = description
        self.input_model = input_model
        self.create_ui_message = create_ui_message
    
    def get_anthropic_definition(self) -> dict:
        schema = self.input_model.model_json_schema()    
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
        
    def get_openai_definition(self) -> dict:
        schema = self.input_model.model_json_schema()    
        properties = schema.get("properties", {})
        # Require all fields for OpenAI function parameters
        required = list(properties.keys()) if properties else []
        
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False
            },
            "strict": True
        }
        
    def get_ui_tool_name(self, args) -> str:
        return self.name


class ToolBox:
    def __init__(self):
        self.tools = {}
        
        
    def register_tool(self, tool: Tool):
        self.tools[tool.name] = tool
        
        
    def get_tool(self, name: str) -> Tool:
        return self.tools.get(name)
    
    
    async def get_anthropic_tool_definitions(self) -> list[dict]:
        definitions = []
        for tool in self.tools.values():
            if asyncio.iscoroutinefunction(tool.get_anthropic_definition):
                definition = await tool.get_anthropic_definition()
            else:
                definition = tool.get_anthropic_definition()
            definitions.append(definition)
        return definitions
    
    
    async def get_openai_tool_definitions(self) -> list[dict]:
        definitions = []
        for tool in self.tools.values():
            if asyncio.iscoroutinefunction(tool.get_openai_definition):
                definition = await tool.get_openai_definition()
            else:
                definition = tool.get_openai_definition()
            definitions.append(definition)
        return definitions