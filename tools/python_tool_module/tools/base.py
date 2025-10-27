from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Type, Dict, Any, List

class ToolResult(BaseModel):
    data: Dict[str, Any] | List[Dict[str, Any]]
    summary: str = "Tool executed successfully."

class BaseTool(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        raise NotImplementedError

    @classmethod
    def get_signature(cls) -> Dict[str, Any]:
        schema = cls.args_schema.schema()
        return {
            "type": "function",
            "function": {
                "name": cls.name,
                "description": cls.description,
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                },
            },
        }
