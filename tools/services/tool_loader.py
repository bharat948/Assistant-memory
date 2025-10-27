from typing import List, Dict, Any
from python_tool_module.tools.base import BaseTool
from python_tool_module.tools.registry import TOOL_REGISTRY

class ToolLoader:
    def get_allowed_tools(self, allowed_tool_ids: List[str]) -> Dict[str, BaseTool]:
        instantiated_tools: Dict[str, BaseTool] = {}
        print(f"[ToolLoader] Requested tool IDs: {allowed_tool_ids}")
        for tool_id in allowed_tool_ids:
            tool_class = TOOL_REGISTRY.get(tool_id)
            if tool_class:
                instantiated_tools[tool_id] = tool_class()
            else:
                print(f"[ToolLoader][WARN] Missing tool in registry: '{tool_id}'")
        print(f"[ToolLoader] Instantiated tools: {list(instantiated_tools.keys())} (count={len(instantiated_tools)})")
        return instantiated_tools

    def get_llm_tool_signatures(self, tools: Dict[str, BaseTool]) -> List[Dict[str, Any]]:
        return [tool.get_signature() for tool in tools.values()]

tool_loader = ToolLoader()
