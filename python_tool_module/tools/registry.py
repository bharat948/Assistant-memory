from typing import Dict, Type
from python_tool_module.tools.base import BaseTool
from python_tool_module.tools.bi_tools import GetCubeMetadataTool, ExecuteBIQueryTool

TOOL_REGISTRY: Dict[str, Type[BaseTool]] = {
    GetCubeMetadataTool.name: GetCubeMetadataTool,
    ExecuteBIQueryTool.name: ExecuteBIQueryTool,
}
