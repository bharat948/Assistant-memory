"""
Example MCP Server implementation.
"""
import asyncio
import json
from typing import Dict, Any, List
from ..base import BaseMCPServer, MCPServerResult

class ExampleMCPServer(BaseMCPServer):
    """Example MCP server for demonstration purposes."""
    
    name = "example_mcp_server"
    description = "Example MCP server that provides basic functionality"
    version = "1.0.0"
    capabilities = ["tools", "resources", "computation"]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tools = {
            "calculate": {
                "name": "calculate",
                "description": "Perform basic mathematical calculations",
                "parameters": {
                    "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
                }
            },
            "echo": {
                "name": "echo", 
                "description": "Echo back the input message",
                "parameters": {
                    "message": {"type": "string", "description": "Message to echo back"}
                }
            }
        }
        self._resources = {
            "server_info": {
                "uri": "example://server/info",
                "name": "Server Information",
                "description": "Basic information about this MCP server"
            },
            "capabilities": {
                "uri": "example://server/capabilities", 
                "name": "Server Capabilities",
                "description": "List of capabilities this server provides"
            }
        }
    
    async def connect(self) -> bool:
        """Establish connection to the example MCP server."""
        try:
            # Simulate connection delay
            await asyncio.sleep(0.1)
            self._connected = True
            print(f"[ExampleMCPServer] Connected to {self.name}")
            return True
        except Exception as e:
            print(f"[ExampleMCPServer] Connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Close connection to the example MCP server."""
        try:
            self._connected = False
            print(f"[ExampleMCPServer] Disconnected from {self.name}")
            return True
        except Exception as e:
            print(f"[ExampleMCPServer] Disconnection failed: {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the example MCP server."""
        if not self._connected:
            raise RuntimeError("Server not connected")
        
        return list(self._tools.values())
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPServerResult:
        """Call a tool on the example MCP server."""
        if not self._connected:
            return MCPServerResult(
                data={},
                summary="Server not connected",
                server_id=self.name,
                method=tool_name,
                success=False,
                error="Server not connected"
            )
        
        if tool_name not in self._tools:
            return MCPServerResult(
                data={},
                summary=f"Tool {tool_name} not found",
                server_id=self.name,
                method=tool_name,
                success=False,
                error=f"Tool {tool_name} not found"
            )
        
        try:
            if tool_name == "calculate":
                expression = arguments.get("expression", "")
                # Simple and safe evaluation (in production, use a proper math parser)
                result = eval(expression) if expression else 0
                return MCPServerResult(
                    data={"result": result, "expression": expression},
                    summary=f"Calculated: {expression} = {result}",
                    server_id=self.name,
                    method=tool_name,
                    success=True
                )
            
            elif tool_name == "echo":
                message = arguments.get("message", "")
                return MCPServerResult(
                    data={"echoed_message": message},
                    summary=f"Echoed: {message}",
                    server_id=self.name,
                    method=tool_name,
                    success=True
                )
            
        except Exception as e:
            return MCPServerResult(
                data={},
                summary=f"Error executing tool {tool_name}",
                server_id=self.name,
                method=tool_name,
                success=False,
                error=str(e)
            )
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the example MCP server."""
        if not self._connected:
            raise RuntimeError("Server not connected")
        
        return list(self._resources.values())
    
    async def read_resource(self, resource_uri: str) -> MCPServerResult:
        """Read a resource from the example MCP server."""
        if not self._connected:
            return MCPServerResult(
                data={},
                summary="Server not connected",
                server_id=self.name,
                method="read_resource",
                success=False,
                error="Server not connected"
            )
        
        if resource_uri == "example://server/info":
            return MCPServerResult(
                data={
                    "name": self.name,
                    "description": self.description,
                    "version": self.version,
                    "capabilities": self.capabilities,
                    "connected": self._connected
                },
                summary="Retrieved server information",
                server_id=self.name,
                method="read_resource",
                success=True
            )
        
        elif resource_uri == "example://server/capabilities":
            return MCPServerResult(
                data={
                    "capabilities": self.capabilities,
                    "tools": list(self._tools.keys()),
                    "resources": list(self._resources.keys())
                },
                summary="Retrieved server capabilities",
                server_id=self.name,
                method="read_resource",
                success=True
            )
        
        else:
            return MCPServerResult(
                data={},
                summary=f"Resource {resource_uri} not found",
                server_id=self.name,
                method="read_resource",
                success=False,
                error=f"Resource {resource_uri} not found"
            )
