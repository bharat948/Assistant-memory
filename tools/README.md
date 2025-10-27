# Tools Module

The Tools module provides a modular tool architecture for extending agent capabilities. It supports various tools like BI analysis, web search, and custom tools with automatic registration and loading.

## 📁 Module Structure

```
tools/
├── __init__.py                  # Module exports
├── test_tools.py               # Tool testing utilities
├── services/                   # Tool services
│   └── tool_loader.py         # Tool loading service
└── tools/                      # Tool implementations
    ├── base.py                # Base tool abstract class
    ├── registry.py            # Tool registry
    ├── bi_tools.py           # BI analysis tools
    ├── web_search_tool.py     # Web search tool
    └── serpapi_search_tool.py # SerpAPI search tool
```

## 🎯 Key Components

### 1. Base Tool (`tools/base.py`)

All tools inherit from `BaseTool`.

#### Class: `BaseTool`

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel

class ToolResult(BaseModel):
    data: Dict[str, Any] | List[Dict[str, Any]]
    summary: str = "Tool executed successfully."

class BaseTool(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]

    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        raise NotImplementedError
```

#### Implementing a Custom Tool

```python
from tools.tools.base import BaseTool, ToolResult
from pydantic import BaseModel

class MyToolArgs(BaseModel):
    query: str
    limit: int = 10

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something useful"
    args_schema = MyToolArgs

    async def run(self, query: str, limit: int = 10) -> ToolResult:
        # Tool implementation
        result = perform_operation(query, limit)
        
        return ToolResult(
            data={"result": result},
            summary=f"Processed query: {query}"
        )
```

### 2. Tool Registry (`tools/registry.py`)

Central registry for all available tools.

#### Registering Tools

```python
from tools.tools.registry import register_tool

@register_tool
class MyTool(BaseTool):
    name = "my_tool"
    # ... implementation

# Or manually
from tools.tools.registry import TOOL_REGISTRY

TOOL_REGISTRY["my_tool"] = MyTool
```

#### Accessing Registry

```python
from tools.tools.registry import TOOL_REGISTRY

# Get tool class
tool_class = TOOL_REGISTRY["my_tool"]

# List all registered tools
for name, tool_class in TOOL_REGISTRY.items():
    print(f"{name}: {tool_class.description}")
```

### 3. Tool Loader Service (`services/tool_loader.py`)

Service for loading and instantiating tools.

#### Class: `ToolLoader`

```python
from tools.services.tool_loader import tool_loader

# Get instantiated tools
tools = tool_loader.get_allowed_tools(["web_search", "bi_query"])

# Load specific tool
tool = tool_loader.get_tool("web_search")
```

#### Methods

**`get_allowed_tools(allowed_tool_ids: List[str]) -> Dict[str, BaseTool]`**
- Returns instantiated tools based on allowed IDs
- Filters tools by ID list
- Returns dictionary mapping tool_id -> tool_instance

**`get_tool(tool_id: str) -> BaseTool`**
- Returns single tool instance
- Raises KeyError if not found

### 4. Available Tools

#### BI Tools (`tools/bi_tools.py`)

**GetCubeMetadataTool**
```python
tool = GetCubeMetadataTool()
result = await tool.run(cube_name="SalesCube", environment="production")

# Returns ToolResult with:
# - data: cube metadata structure
# - summary: cube information summary
```

**ExecuteBIQueryTool**
```python
tool = ExecuteBIQueryTool()
result = await tool.run(
    query="SELECT * FROM sales WHERE year=2024",
    query_type="MDX",
    environment="production"
)

# Returns ToolResult with:
# - data: query results
# - summary: result summary
```

#### Web Search Tool (`tools/web_search_tool.py`)

**WebSearchTool**
```python
tool = WebSearchTool()
result = await tool.run(
    query="Python programming",
    max_results=10,
    search_depth="medium"
)

# Returns ToolResult with:
# - data: list of search results
# - summary: top results summary
```

**Configuration:**
- API: Tavily
- Requires `TAVILY_API_KEY` environment variable

#### SerpAPI Search Tool (`tools/serpapi_search_tool.py`)

**SerpAPISearchTool**
```python
tool = SerpAPISearchTool()
result = await tool.run(
    query="AI latest news",
    location="United States",
    num_results=10
)

# Returns ToolResult with:
# - data: search results with rich data
# - summary: top results summary
```

**Configuration:**
- API: SerpAPI
- Requires `SERPAPI_API_KEY` environment variable

## 🔧 Usage Examples

### Example 1: Using Tools in Agent

```python
from tools.services.tool_loader import tool_loader

# Load allowed tools
tools = tool_loader.get_allowed_tools(["web_search", "get_cube_metadata"])

# Use tool
web_search_tool = tools["web_search"]
result = await web_search_tool.run(query="Python tutorial", max_results=5)

print(result.summary)
print(result.data)
```

### Example 2: Implementing Custom Tool

```python
from tools.tools.base import BaseTool, ToolResult
from tools.tools.registry import register_tool
from pydantic import BaseModel

class WeatherToolArgs(BaseModel):
    location: str
    units: str = "celsius"

@register_tool
class WeatherTool(BaseTool):
    name = "weather"
    description = "Get weather information for a location"
    args_schema = WeatherToolArgs

    async def run(self, location: str, units: str = "celsius") -> ToolResult:
        # Fetch weather data
        weather_data = await fetch_weather(location, units)
        
        return ToolResult(
            data={"temperature": weather_data["temp"], "condition": weather_data["condition"]},
            summary=f"Weather in {location}: {weather_data['temp']}°{units}, {weather_data['condition']}"
        )

# Now available in registry
tool = tool_loader.get_tool("weather")
result = await tool.run(location="New York")
```

### Example 3: Tool Result Processing

```python
# Execute tool
result = await tool.run(...)

# Access data
if isinstance(result.data, list):
    for item in result.data:
        print(item)
else:
    print(result.data)

# Access summary
print(result.summary)
```

## 📊 Tool Architecture

### Tool Execution Flow

```
1. Agent requests tool execution
2. ToolLoader instantiates tool
3. Tool validates input via args_schema
4. Tool.run() executes
5. ToolResult returned with data and summary
6. Summary used by LLM, data available for processing
```

### Tool Registration Flow

```
1. Tool class defined with @register_tool decorator
2. Registry adds tool to TOOL_REGISTRY
3. ToolLoader can instantiate on demand
4. Agent references tool by ID
```

## 🔐 Configuration

### Environment Variables

```env
# API Keys (if using external APIs)
TAVILY_API_KEY=your_tavily_key
SERPAPI_API_KEY=your_serpapi_key

# BI Configuration (if using BI tools)
BI_ENVIRONMENT=production
BI_CUBE_SERVER=server.example.com
```

### Tool Configuration

Some tools support runtime configuration:

```python
# WebSearchTool configuration
tool = WebSearchTool()
tool.max_results = 20
tool.search_depth = "advanced"

# BI tools configuration
tool = ExecuteBIQueryTool()
tool.environment = "development"
tool.timeout = 60
```

## 🧪 Testing

```bash
# Run tool tests
python tools/test_tools.py

# Test specific tool
python -m pytest tests/test_bi_tools.py
```

### Example Test

```python
async def test_web_search_tool():
    tool = WebSearchTool()
    result = await tool.run(query="Python", max_results=5)
    
    assert isinstance(result, ToolResult)
    assert "data" in result.dict()
    assert "summary" in result.dict()
    assert len(result.data) <= 5
```

## 🔗 Integration with Other Modules

### Core Module
- Agent class loads tools via ToolLoader
- Converts tools to LangChain format
- Executes tools through AgentExecutor

### API Module
- Tools exposed through agent endpoints
- Tool results included in agent responses

### Memory Module
- Tool outputs can be stored in memory
- Tool usage tracked in conversation history

## 🎯 Best Practices

1. **Define args_schema**: Use Pydantic models for input validation
2. **Return structured data**: Always return ToolResult with data and summary
3. **Handle errors gracefully**: Return appropriate error messages
4. **Register tools**: Use @register_tool decorator for automatic registration
5. **Test tools**: Write tests for each tool
6. **Document tools**: Add clear descriptions and examples

## 🔧 Creating New Tools

### Step-by-Step Guide

1. **Create Pydantic model for arguments:**
```python
class MyToolArgs(BaseModel):
    param1: str
    param2: int = 10
```

2. **Implement tool class:**
```python
@register_tool
class MyTool(BaseTool):
    name = "my_tool_id"
    description = "Clear description"
    args_schema = MyToolArgs
    
    async def run(self, param1: str, param2: int = 10) -> ToolResult:
        # Implementation
        return ToolResult(data={...}, summary="...")
```

3. **Register in registry** (auto via decorator)

4. **Use in agents:**
```json
{
  "allowed_tool_ids": ["my_tool_id"]
}
```

## 🔗 Related Documentation

- See `../core/README.md` for agent integration
- See `../api/README.md` for API usage
- See `../README.md` for overall architecture
