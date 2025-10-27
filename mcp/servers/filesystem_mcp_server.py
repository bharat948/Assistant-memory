"""
Filesystem MCP Server implementation.
"""
import os
import asyncio
from typing import Dict, Any, List
from ..base import BaseMCPServer, MCPServerResult

class FilesystemMCPServer(BaseMCPServer):
    """MCP server that provides filesystem operations."""
    
    name = "filesystem_mcp_server"
    description = "MCP server for filesystem operations like reading, writing, and listing files"
    version = "1.0.0"
    capabilities = ["tools", "resources", "filesystem"]
    
    def __init__(self, base_path: str = ".", **kwargs):
        super().__init__(**kwargs)
        self.base_path = os.path.abspath(base_path)
        self._tools = {
            "read_file": {
                "name": "read_file",
                "description": "Read contents of a file",
                "parameters": {
                    "file_path": {"type": "string", "description": "Path to the file to read"}
                }
            },
            "write_file": {
                "name": "write_file",
                "description": "Write content to a file",
                "parameters": {
                    "file_path": {"type": "string", "description": "Path to the file to write"},
                    "content": {"type": "string", "description": "Content to write to the file"}
                }
            },
            "list_directory": {
                "name": "list_directory",
                "description": "List contents of a directory",
                "parameters": {
                    "directory_path": {"type": "string", "description": "Path to the directory to list"}
                }
            },
            "file_info": {
                "name": "file_info",
                "description": "Get information about a file or directory",
                "parameters": {
                    "file_path": {"type": "string", "description": "Path to the file or directory"}
                }
            }
        }
    
    async def connect(self) -> bool:
        """Establish connection to the filesystem MCP server."""
        try:
            # Verify base path exists
            if not os.path.exists(self.base_path):
                os.makedirs(self.base_path, exist_ok=True)
            
            self._connected = True
            print(f"[FilesystemMCPServer] Connected to {self.name} with base path: {self.base_path}")
            return True
        except Exception as e:
            print(f"[FilesystemMCPServer] Connection failed: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Close connection to the filesystem MCP server."""
        try:
            self._connected = False
            print(f"[FilesystemMCPServer] Disconnected from {self.name}")
            return True
        except Exception as e:
            print(f"[FilesystemMCPServer] Disconnection failed: {e}")
            return False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the filesystem MCP server."""
        if not self._connected:
            raise RuntimeError("Server not connected")
        
        return list(self._tools.values())
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPServerResult:
        """Call a tool on the filesystem MCP server."""
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
            if tool_name == "read_file":
                file_path = arguments.get("file_path", "")
                full_path = os.path.join(self.base_path, file_path)
                
                # Security check - ensure path is within base_path
                if not os.path.abspath(full_path).startswith(os.path.abspath(self.base_path)):
                    raise ValueError("Access denied: Path outside base directory")
                
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return MCPServerResult(
                    data={"content": content, "file_path": file_path},
                    summary=f"Read file: {file_path}",
                    server_id=self.name,
                    method=tool_name,
                    success=True
                )
            
            elif tool_name == "write_file":
                file_path = arguments.get("file_path", "")
                content = arguments.get("content", "")
                full_path = os.path.join(self.base_path, file_path)
                
                # Security check - ensure path is within base_path
                if not os.path.abspath(full_path).startswith(os.path.abspath(self.base_path)):
                    raise ValueError("Access denied: Path outside base directory")
                
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return MCPServerResult(
                    data={"file_path": file_path, "bytes_written": len(content.encode('utf-8'))},
                    summary=f"Wrote file: {file_path}",
                    server_id=self.name,
                    method=tool_name,
                    success=True
                )
            
            elif tool_name == "list_directory":
                directory_path = arguments.get("directory_path", "")
                full_path = os.path.join(self.base_path, directory_path)
                
                # Security check - ensure path is within base_path
                if not os.path.abspath(full_path).startswith(os.path.abspath(self.base_path)):
                    raise ValueError("Access denied: Path outside base directory")
                
                items = []
                for item in os.listdir(full_path):
                    item_path = os.path.join(full_path, item)
                    is_dir = os.path.isdir(item_path)
                    items.append({
                        "name": item,
                        "type": "directory" if is_dir else "file",
                        "path": os.path.join(directory_path, item)
                    })
                
                return MCPServerResult(
                    data={"items": items, "directory_path": directory_path},
                    summary=f"Listed directory: {directory_path} ({len(items)} items)",
                    server_id=self.name,
                    method=tool_name,
                    success=True
                )
            
            elif tool_name == "file_info":
                file_path = arguments.get("file_path", "")
                full_path = os.path.join(self.base_path, file_path)
                
                # Security check - ensure path is within base_path
                if not os.path.abspath(full_path).startswith(os.path.abspath(self.base_path)):
                    raise ValueError("Access denied: Path outside base directory")
                
                if not os.path.exists(full_path):
                    return MCPServerResult(
                        data={},
                        summary=f"File not found: {file_path}",
                        server_id=self.name,
                        method=tool_name,
                        success=False,
                        error="File not found"
                    )
                
                stat = os.stat(full_path)
                return MCPServerResult(
                    data={
                        "file_path": file_path,
                        "size": stat.st_size,
                        "is_directory": os.path.isdir(full_path),
                        "is_file": os.path.isfile(full_path),
                        "modified": stat.st_mtime
                    },
                    summary=f"File info: {file_path}",
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
        """List available resources from the filesystem MCP server."""
        if not self._connected:
            raise RuntimeError("Server not connected")
        
        return [
            {
                "uri": f"filesystem://{self.base_path}",
                "name": "Base Directory",
                "description": f"Base directory: {self.base_path}"
            }
        ]
    
    async def read_resource(self, resource_uri: str) -> MCPServerResult:
        """Read a resource from the filesystem MCP server."""
        if not self._connected:
            return MCPServerResult(
                data={},
                summary="Server not connected",
                server_id=self.name,
                method="read_resource",
                success=False,
                error="Server not connected"
            )
        
        if resource_uri.startswith("filesystem://"):
            path = resource_uri.replace("filesystem://", "")
            full_path = os.path.join(self.base_path, path)
            
            # Security check
            if not os.path.abspath(full_path).startswith(os.path.abspath(self.base_path)):
                return MCPServerResult(
                    data={},
                    summary="Access denied",
                    server_id=self.name,
                    method="read_resource",
                    success=False,
                    error="Access denied: Path outside base directory"
                )
            
            if os.path.isfile(full_path):
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return MCPServerResult(
                    data={"content": content, "path": path},
                    summary=f"Read resource: {resource_uri}",
                    server_id=self.name,
                    method="read_resource",
                    success=True
                )
            else:
                return MCPServerResult(
                    data={},
                    summary=f"Resource not found: {resource_uri}",
                    server_id=self.name,
                    method="read_resource",
                    success=False,
                    error="Resource not found"
                )
        
        return MCPServerResult(
            data={},
            summary=f"Unknown resource: {resource_uri}",
            server_id=self.name,
            method="read_resource",
            success=False,
            error="Unknown resource"
        )
