from typing import Dict, Type
from tools.tools.base import BaseTool
from tools.tools.bi_tools import GetCubeMetadataTool, ExecuteBIQueryTool
from tools.tools.web_search_tool import WebSearchTool
from tools.tools.serpapi_search_tool import SerpAPISearchTool

TOOL_REGISTRY: Dict[str, Type[BaseTool]] = {
    GetCubeMetadataTool.name: GetCubeMetadataTool,
    ExecuteBIQueryTool.name: ExecuteBIQueryTool,
    WebSearchTool.name: WebSearchTool,
    SerpAPISearchTool.name: SerpAPISearchTool,
}
