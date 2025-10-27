"""
Registry for MCP servers.
"""
from typing import Dict, Type, List
from .base import BaseMCPServer

# Import MCP server implementations
from .servers.example_mcp_server import ExampleMCPServer
from .servers.filesystem_mcp_server import FilesystemMCPServer

MCP_SERVER_REGISTRY: Dict[str, Type[BaseMCPServer]] = {
    ExampleMCPServer.name: ExampleMCPServer,
    FilesystemMCPServer.name: FilesystemMCPServer,
}

def register_mcp_server(server_class: Type[BaseMCPServer]):
    """Register an MCP server class."""
    MCP_SERVER_REGISTRY[server_class.name] = server_class
    return server_class

def get_mcp_server_class(server_name: str) -> Type[BaseMCPServer]:
    """Get MCP server class by name."""
    return MCP_SERVER_REGISTRY.get(server_name)

def list_available_servers() -> List[str]:
    """List all available MCP server names."""
    return list(MCP_SERVER_REGISTRY.keys())
