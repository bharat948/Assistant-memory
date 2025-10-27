# MCP Server Module

The MCP (Model Context Protocol) Server Module provides a framework for integrating external MCP servers with your AI agents. This module follows the same architectural patterns as the existing tool system, making it easy to add MCP server capabilities to your agents.

## Architecture

```
mcp_server_module/
├── __init__.py              # Module exports
├── base.py                  # Base MCP server classes
├── registry.py              # Server registry
├── services/
│   ├── __init__.py
│   └── mcp_loader.py        # MCP server loader service
├── servers/
│   ├── __init__.py
│   ├── example_mcp_server.py    # Example implementation
│   └── filesystem_mcp_server.py # Filesystem MCP server
└── README.md
```

## Key Components

### BaseMCPServer
The abstract base class that all MCP servers must implement:

```python
class BaseMCPServer(ABC):
    name: str
    description: str
    version: str
    capabilities: List[str]
    
    @abstractmethod
    async def connect(self) -> bool
    @abstractmethod
    async def disconnect(self) -> bool
    @abstractmethod
    async def list_tools(self) -> List[Dict[str, Any]]
    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPServerResult
    @abstractmethod
    async def list_resources(self) -> List[Dict[str, Any]]
    @abstractmethod
    async def read_resource(self, resource_uri: str) -> MCPServerResult
```

### MCPLoader
Service for loading and managing MCP servers:

```python
mcp_loader = MCPLoader()

# Get instantiated servers
servers = mcp_loader.get_allowed_servers(["example_mcp_server"])

# Connect to all servers
await mcp_loader.connect_all_servers(servers)

# Call tools
result = await mcp_loader.call_server_tool("example_mcp_server", "calculate", {"expression": "2+2"})
```

## Usage

### 1. Creating a Custom MCP Server

```python
from mcp_server_module.base import BaseMCPServer, MCPServerResult

class MyMCPServer(BaseMCPServer):
    name = "my_mcp_server"
    description = "My custom MCP server"
    version = "1.0.0"
    capabilities = ["tools", "resources"]
    
    async def connect(self) -> bool:
        # Implement connection logic
        self._connected = True
        return True
    
    async def disconnect(self) -> bool:
        # Implement disconnection logic
        self._connected = False
        return True
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        # Return available tools
        return [{"name": "my_tool", "description": "My custom tool"}]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> MCPServerResult:
        # Implement tool execution
        return MCPServerResult(
            data={"result": "success"},
            summary="Tool executed successfully",
            server_id=self.name,
            method=tool_name
        )
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        # Return available resources
        return [{"uri": "my://resource", "name": "My Resource"}]
    
    async def read_resource(self, resource_uri: str) -> MCPServerResult:
        # Implement resource reading
        return MCPServerResult(
            data={"content": "resource data"},
            summary="Resource read successfully",
            server_id=self.name,
            method="read_resource"
        )
```

### 2. Registering MCP Servers

```python
from mcp_server_module.registry import register_mcp_server

@register_mcp_server
class MyMCPServer(BaseMCPServer):
    # ... implementation
```

Or manually:

```python
from mcp_server_module.registry import MCP_SERVER_REGISTRY
MCP_SERVER_REGISTRY["my_mcp_server"] = MyMCPServer
```

### 3. Using MCP Servers in Agents

MCP servers are automatically loaded when initializing agents if they are specified in the agent configuration:

```python
# Agent configuration should include:
{
    "allowed_mcp_server_ids": ["example_mcp_server", "filesystem_mcp_server"]
}
```

### 4. Agent MCP Methods

Once an agent is initialized with MCP servers, you can use these methods:

```python
# List all MCP servers
servers = await agent.list_mcp_servers()

# Get tools from a specific server
tools = await agent.get_mcp_server_tools("example_mcp_server")

# Call a tool on a specific server
result = await agent.call_mcp_server_tool(
    "example_mcp_server", 
    "calculate", 
    {"expression": "2+2"}
)

# Read a resource from a specific server
result = await agent.read_mcp_server_resource(
    "filesystem_mcp_server", 
    "filesystem://test.txt"
)
```

## API Endpoints

The module provides REST API endpoints for MCP server operations:

- `GET /agents/mcp/servers/{agent_id}` - List all MCP servers for an agent
- `GET /agents/mcp/servers/{agent_id}/{server_id}/info` - Get server information
- `GET /agents/mcp/servers/{agent_id}/{server_id}/tools` - Get server tools
- `GET /agents/mcp/servers/{agent_id}/{server_id}/resources` - Get server resources
- `POST /agents/mcp/servers/{agent_id}/{server_id}/tools/{tool_name}/call` - Call a tool
- `POST /agents/mcp/servers/{agent_id}/{server_id}/resources/read` - Read a resource

## Example Implementations

### ExampleMCPServer
A demonstration server with basic mathematical and echo capabilities.

### FilesystemMCPServer
A server that provides filesystem operations like reading, writing, and listing files.

## Integration with Agent Core

MCP servers are integrated into the agent initialization process:

1. Agent configuration includes `allowed_mcp_server_ids`
2. During agent initialization, MCP servers are loaded and connected
3. Agents can access MCP server tools and resources through dedicated methods
4. MCP servers are automatically managed (connected/disconnected) with the agent lifecycle

## Error Handling

The module includes comprehensive error handling:

- Connection failures are logged and don't prevent agent initialization
- Tool call errors return structured error responses
- Resource access errors are handled gracefully
- All operations include success/failure indicators

## Security Considerations

- MCP servers should implement proper authentication
- File system operations include path validation
- Resource access should be restricted to authorized operations
- All user inputs should be validated before processing
