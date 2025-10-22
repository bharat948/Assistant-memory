from typing import Dict, Type
from python_tool_module.tools.base import BaseTool
from python_tool_module.tools.bi_tools import GetCubeMetadataTool, ExecuteBIQueryTool
from python_tool_module.tools.web_search_tool import WebSearchTool
from python_tool_module.tools.serpapi_search_tool import SerpAPISearchTool

TOOL_REGISTRY: Dict[str, Type[BaseTool]] = {
    GetCubeMetadataTool.name: GetCubeMetadataTool,
    ExecuteBIQueryTool.name: ExecuteBIQueryTool,
    WebSearchTool.name: WebSearchTool,
    SerpAPISearchTool.name: SerpAPISearchTool,
}
