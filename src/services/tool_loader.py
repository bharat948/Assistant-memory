from typing import List, Dict, Any

from src.tools.base import BaseTool
from src.tools.registry import TOOL_REGISTRY

class ToolLoader:
    """
    A service that acts as the bridge between the AppRepo configuration
    and the self-contained tool module.
    """
    def get_allowed_tools(self, allowed_tool_ids: List[str]) -> Dict[str, BaseTool]:
        """
        Given a list of tool unique IDs from an AppRepo configuration, this method
        looks them up in the central TOOL_REGISTRY and returns a dictionary of
        instantiated, ready-to-use tool objects.

        Args:
            allowed_tool_ids: A list of strings, e.g., ["get_cube_metadata", "execute_bi_query"].

        Returns:
            A dictionary mapping the tool name to its instantiated class object.
        """
        instantiated_tools: Dict[str, BaseTool] = {}
        for tool_id in allowed_tool_ids:
            tool_class = TOOL_REGISTRY.get(tool_id)
            if tool_class:
                # Instantiate the tool class
                instantiated_tools[tool_id] = tool_class()
            else:
                # Log a warning if a configured tool is not found in the registry.
                # This helps diagnose configuration mismatches.
                print(f"Warning: Tool '{tool_id}' is configured in AppRepo but was not found in the Tool Registry.")
        
        return instantiated_tools

    def get_llm_tool_signatures(self, tools: Dict[str, BaseTool]) -> List[Dict[str, Any]]:
        """
        Takes a dictionary of instantiated tools and generates a list of their
        JSON Schema signatures. This list is in the precise format required by
        modern LLMs for their tool-calling functionality.

        This is the critical "binding" step that informs the model of the
        capabilities it has been granted for a given session.

        Args:
            tools: A dictionary of tool names to instantiated BaseTool objects.

        Returns:
            A list of JSON Schema dictionaries representing the function signatures.
        """
        return [tool.get_signature() for tool in tools.values()]

# Create a singleton instance for easy, consistent access throughout the application.
tool_loader = ToolLoader()
