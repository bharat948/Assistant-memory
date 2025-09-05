from typing import Dict, Type
from src.tools.base import BaseTool

# Step 1: Import the concrete tool classes from their respective files.
from src.tools.bi_tools import GetCubeMetadataTool, ExecuteBIQueryTool
# from .admin_tools import CreateUserTool # Example of another tool file

# Step 2: Create the TOOL_REGISTRY dictionary.
# This registry maps a tool's unique `name` to its implementation class.
# It is the single source of truth for all tools available in the agentic system.
TOOL_REGISTRY: Dict[str, Type[BaseTool]] = {
    GetCubeMetadataTool.name: GetCubeMetadataTool,
    ExecuteBIQueryTool.name: ExecuteBIQueryTool,
    # When you create a new tool, you register it here:
    # CreateUserTool.name: CreateUserTool, 
}
