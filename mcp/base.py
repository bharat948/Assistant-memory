"""
Base classes for MCP (Model Context Protocol) servers.
"""
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Type, Dict, Any, List, Optional
import asyncio
import json

class MCPServerResult(BaseModel):
    """Result from MCP server execution."""
    data: Dict[str, Any] | List[Dict[str, Any]]
    summary: str = "MCP server executed successfully."
    server_id: str
    method: str
    success: bool = True
    error: Optional[str] = None

class BaseMCPServer(ABC):
    """Base class for MCP servers."""
    
    name: str
    description: str
    version: str = "1.0.0"
    capabilities: List[str] = []
    connection_config: Dict[str, Any] = {}
    
    def __init__(self, **kwargs):
        """Initialize MCP server with configuration."""
        self.connection_config.update(kwargs)
        self._connected = False
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to MCP server."""
        raise NotImplementedError
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to MCP server."""
        raise NotImplementedError
    
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server."""
        raise NotImplementedError
    
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPServerResult:
        """Call a tool on the MCP server."""
        raise NotImplementedError
    
    @abstractmethod
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the MCP server."""
        raise NotImplementedError
    
    @abstractmethod
    async def read_resource(self, resource_uri: str) -> MCPServerResult:
        """Read a resource from the MCP server."""
        raise NotImplementedError
    
    async def health_check(self) -> bool:
        """Check if the MCP server is healthy."""
        try:
            if not self._connected:
                await self.connect()
            return self._connected
        except Exception:
            return False
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get information about this MCP server."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "capabilities": self.capabilities,
            "connected": self._connected
        }
    
    @classmethod
    def get_signature(cls) -> Dict[str, Any]:
        """Get the server signature for registration."""
        return {
            "name": cls.name,
            "description": cls.description,
            "version": cls.version,
            "capabilities": cls.capabilities
        }
