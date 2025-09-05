from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Type, Dict, Any, List

class ToolResult(BaseModel):
    """
    A standardized data structure for returning the result of a tool's execution.
    This ensures that the agent orchestrator receives a predictable output format.
    """
    data: Dict[str, Any] | List[Dict[str, Any]]
    summary: str = "Tool executed successfully."

class BaseTool(ABC):
    """
    Abstract Base Class for all agent tools.

    This class enforces a standard interface for defining a tool's:
    1.  `name`: A unique, machine-readable identifier.
    2.  `description`: A natural language description for the LLM to understand its purpose.
    3.  `args_schema`: A Pydantic model defining the input arguments and their types.
    4.  `run`: The core asynchronous execution logic.
    """
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        """
        The main execution method for the tool. This method must be implemented
        by all concrete tool classes. It receives arguments as keyword arguments
        that have been validated against the `args_schema`.
        """
        raise NotImplementedError

    @classmethod
    def get_signature(cls) -> Dict[str, Any]:
        """
        Generates an LLM-compatible JSON Schema dictionary representing the
        tool's function signature. This is used to bind the tool to the model
        at the time of agent initialization.
        """
        # Pydantic's .schema() method creates a JSON Schema from the model
        schema = cls.args_schema.schema()
        
        # Format the schema into the structure expected by most LLM tool-calling APIs
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
