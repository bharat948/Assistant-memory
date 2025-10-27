"""
MCP Server loader service.
"""
from typing import List, Dict, Any
from ..base import BaseMCPServer, MCPServerResult
from ..registry import MCP_SERVER_REGISTRY

class MCPLoader:
    """Service for loading and managing MCP servers."""
    
    def __init__(self):
        self._active_servers: Dict[str, BaseMCPServer] = {}
    
    def get_allowed_servers(self, allowed_server_ids: List[str]) -> Dict[str, BaseMCPServer]:
        """Get instantiated MCP servers based on allowed IDs."""
        instantiated_servers: Dict[str, BaseMCPServer] = {}
        print(f"[MCPLoader] Requested server IDs: {allowed_server_ids}")
        
        for server_id in allowed_server_ids:
            server_class = MCP_SERVER_REGISTRY.get(server_id)
            if server_class:
                try:
                    server_instance = server_class()
                    instantiated_servers[server_id] = server_instance
                    self._active_servers[server_id] = server_instance
                    print(f"[MCPLoader] Initialized MCP server: {server_id}")
                except Exception as e:
                    print(f"[MCPLoader][ERROR] Failed to initialize server {server_id}: {e}")
            else:
                print(f"[MCPLoader][WARN] Missing server in registry: '{server_id}'")
        
        print(f"[MCPLoader] Instantiated servers: {list(instantiated_servers.keys())} (count={len(instantiated_servers)})")
        return instantiated_servers
    
    async def connect_all_servers(self, servers: Dict[str, BaseMCPServer]) -> Dict[str, bool]:
        """Connect to all MCP servers."""
        connection_results = {}
        
        for server_id, server in servers.items():
            try:
                connected = await server.connect()
                connection_results[server_id] = connected
                if connected:
                    print(f"[MCPLoader] Connected to MCP server: {server_id}")
                else:
                    print(f"[MCPLoader][WARN] Failed to connect to MCP server: {server_id}")
            except Exception as e:
                print(f"[MCPLoader][ERROR] Error connecting to server {server_id}: {e}")
                connection_results[server_id] = False
        
        return connection_results
    
    async def disconnect_all_servers(self) -> Dict[str, bool]:
        """Disconnect from all active MCP servers."""
        disconnection_results = {}
        
        for server_id, server in self._active_servers.items():
            try:
                disconnected = await server.disconnect()
                disconnection_results[server_id] = disconnected
                if disconnected:
                    print(f"[MCPLoader] Disconnected from MCP server: {server_id}")
            except Exception as e:
                print(f"[MCPLoader][ERROR] Error disconnecting from server {server_id}: {e}")
                disconnection_results[server_id] = False
        
        self._active_servers.clear()
        return disconnection_results
    
    async def get_server_tools(self, server_id: str) -> List[Dict[str, Any]]:
        """Get tools from a specific MCP server."""
        server = self._active_servers.get(server_id)
        if not server:
            print(f"[MCPLoader][WARN] Server {server_id} not found")
            return []
        
        try:
            return await server.list_tools()
        except Exception as e:
            print(f"[MCPLoader][ERROR] Error getting tools from server {server_id}: {e}")
            return []
    
    async def get_server_resources(self, server_id: str) -> List[Dict[str, Any]]:
        """Get resources from a specific MCP server."""
        server = self._active_servers.get(server_id)
        if not server:
            print(f"[MCPLoader][WARN] Server {server_id} not found")
            return []
        
        try:
            return await server.list_resources()
        except Exception as e:
            print(f"[MCPLoader][ERROR] Error getting resources from server {server_id}: {e}")
            return []
    
    async def call_server_tool(self, server_id: str, tool_name: str, arguments: Dict[str, Any]) -> MCPServerResult:
        """Call a tool on a specific MCP server."""
        server = self._active_servers.get(server_id)
        if not server:
            return MCPServerResult(
                data={},
                summary=f"Server {server_id} not found",
                server_id=server_id,
                method=tool_name,
                success=False,
                error=f"Server {server_id} not found"
            )
        
        try:
            return await server.call_tool(tool_name, arguments)
        except Exception as e:
            return MCPServerResult(
                data={},
                summary=f"Error calling tool {tool_name}",
                server_id=server_id,
                method=tool_name,
                success=False,
                error=str(e)
            )
    
    async def read_server_resource(self, server_id: str, resource_uri: str) -> MCPServerResult:
        """Read a resource from a specific MCP server."""
        server = self._active_servers.get(server_id)
        if not server:
            return MCPServerResult(
                data={},
                summary=f"Server {server_id} not found",
                server_id=server_id,
                method="read_resource",
                success=False,
                error=f"Server {server_id} not found"
            )
        
        try:
            return await server.read_resource(resource_uri)
        except Exception as e:
            return MCPServerResult(
                data={},
                summary=f"Error reading resource {resource_uri}",
                server_id=server_id,
                method="read_resource",
                success=False,
                error=str(e)
            )
    
    def get_server_info(self, server_id: str) -> Dict[str, Any]:
        """Get information about a specific MCP server."""
        server = self._active_servers.get(server_id)
        if not server:
            return {"error": f"Server {server_id} not found"}
        
        return server.get_server_info()
    
    def list_active_servers(self) -> List[str]:
        """List all active MCP server IDs."""
        return list(self._active_servers.keys())

# Global instance
mcp_loader = MCPLoader()
