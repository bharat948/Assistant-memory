# API Module

The API module provides the FastAPI-based REST API layer for the agent management platform. It handles agent registration, initialization, invocation, and provides a clean interface for client applications to interact with agents.

## 📁 Module Structure

```
api/
├── __init__.py                 # Module exports
├── main.py                     # FastAPI app entry point
├── dependencies.py             # FastAPI dependency injection
├── endpoints/                  # REST API endpoints
│   ├── agent.py              # Agent management endpoints
│   └── mcp.py                # MCP server endpoints
├── models/                     # Pydantic request/response models
│   └── agent.py              # Agent-related models
└── services/                   # Business logic layer
    ├── agent_service.py      # Agent lifecycle management
    └── agent_cache.py        # Agent caching service
```

## 🎯 Key Components

### 1. FastAPI Application (`main.py`)

The main entry point for the API service.

```python
from fastapi import FastAPI
from api.endpoints.agent import router as agent_router
from api.endpoints.mcp import router as mcp_router

app = FastAPI(
    title="Agent Service API",
    description="AI Agent Management Platform",
    version="1.0.0"
)

app.include_router(agent_router, prefix="/agents", tags=["Agents"])
app.include_router(mcp_router, prefix="/mcp", tags=["MCP Servers"])
```

**Features:**
- Automatic OpenAPI/Swagger documentation
- Dependency injection for database connections
- CORS support for frontend integration
- Health check endpoints

### 2. Agent Endpoints (`endpoints/agent.py`)

Provides RESTful endpoints for agent management.

#### Register Agent
```http
POST /agents/register
Content-Type: application/json

{
  "agent_id": "my_agent",
  "name": "My Agent",
  "agent_type": "react_agent",
  "description": "Agent description",
  "llm_config": {...},
  "system_prompt_template": "...",
  "allowed_tool_ids": [...],
  "allowed_roles": [...]
}
```

#### Initialize Agent
```http
POST /agents/{agent_id}/initialize
```

Initializes an agent, loading LLM, tools, and memory. The agent is cached for subsequent invocations.

#### Invoke Agent
```http
POST /agents/{agent_id}/invoke
Content-Type: application/json

{
  "prompt": "What is the weather today?",
  "user_id": "user_123",
  "conversation_id": "conv_456"
}
```

Invokes an agent with a user prompt. Requires agent to be initialized first.

#### List Agents
```http
GET /agents/
```

Returns a list of all registered agents.

### 3. Agent Service (`services/agent_service.py`)

Core business logic for agent lifecycle management.

#### Class: `AgentService`

Main service class managing agent operations.

```python
class AgentService:
    # Class-level cache for initialized agents
    _agent_cache: Dict[str, Agent] = {}
    
    def __init__(self, db):
        self.apprepo_service = AppRepoService(AppRepoDAO(db))
        self.cache_manager = AgentCacheManager(db)
```

#### Methods:

**`async register_agent(agent_data)`**
- Registers a new agent configuration
- Stores agent metadata in MongoDB
- Returns created agent configuration

**`async initialize_agent(agent_id)`**
- Checks in-memory cache for existing agent
- Checks database cache for cross-worker scenarios
- Initializes agent with LLM, tools, and memory
- Caches agent for subsequent invocations
- Returns initialized Agent instance

**`async invoke_agent(agent_id, prompt, user_id, conversation_id)`**
- Retrieves agent from cache
- Retrieves conversation history from memory
- Executes agent with user prompt
- Stores new messages to memory
- Returns agent response

**`async list_all_agents()`**
- Lists all registered agents from database
- Returns agent configurations

### 4. Agent Cache (`services/agent_cache.py`)

Manages agent caching across multiple workers/processes.

#### Features:
- **Multi-level caching**: In-memory + MongoDB persistent cache
- **Cross-worker synchronization**: Agents initialized in one worker are visible to others
- **Cache metadata**: Tracks initialization status, last accessed time
- **Cache invalidation**: Supports manual cache clearing

#### Class: `AgentCacheManager`

```python
class AgentCacheManager:
    async def mark_initialized(agent_id: str)
    async def is_initialized(agent_id: str) -> bool
    async def update_last_accessed(agent_id: str)
    async def clear_cache(agent_id: str)
    async def get_cache_stats() -> Dict
```

### 5. Request/Response Models (`models/agent.py`)

Pydantic models for type safety and validation.

#### Request Models:

```python
class RegisterAgentRequest(BaseModel):
    agent_id: str
    name: str
    agent_type: str
    description: Optional[str]
    llm_config: Optional[LLMConfig]
    system_prompt_template: Optional[str]
    allowed_tool_ids: List[str]
    allowed_roles: List[str]
    dependencies: Optional[Dependencies]
    output_schema: Optional[Dict[str, Any]]

class InvokeAgentRequest(BaseModel):
    prompt: str
    user_id: str = "default_user"
    conversation_id: Optional[str] = None
```

#### Response Models:

```python
class AgentResponse(BaseModel):
    agent_id: str
    name: str
    agent_type: str
    status: str
    description: Optional[str]

class InitializeAgentResponse(BaseModel):
    agent_id: str
    name: str
    status: str
    message: str

class InvokeAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    response: str
    tools_used: List[str]
    intermediate_steps: List[Dict]
```

## 🔄 Request Flow

### Agent Registration Flow
```
1. Client → POST /agents/register
2. AgentService.register_agent()
3. AppRepoService → MongoDB
4. Returns registered agent config
```

### Agent Initialization Flow
```
1. Client → POST /agents/{id}/initialize
2. AgentService.initialize_agent()
   - Check local cache
   - Check database cache (cross-worker)
   - AgentInitializer.init_agent()
   - Load LLM + Tools + Memory
   - Cache agent (local + database)
3. Returns initialized agent
```

### Agent Invocation Flow
```
1. Client → POST /agents/{id}/invoke
2. AgentService.invoke_agent()
   - Retrieve agent from cache
   - Get conversation history from memory
   - Execute agent with tools
   - Store conversation to memory
3. Returns agent response
```

## 🔌 Dependencies

The API module depends on:
- `core/`: Agent initialization and execution
- `storage/`: Database persistence layer
- `tools/`: Tool loading and execution
- `memory/`: Memory integration for conversation history
- `mcp/`: MCP server integration

## 🚀 Usage

### Starting the API Server

```bash
# Development
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Environment Variables

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=agent_service_db

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Memory Configuration
POSTGRES_DSN=postgresql://user:pass@localhost:5432/memory_db
ALLOWED_TAGS=["general", "work", "code"]
ALLOWED_COLLECTIONS=["conversations", "general"]
WORKING_MEMORY_THRESHOLD=6

# Optional: Tool API Keys
TAVILY_API_KEY=your_tavily_key
SERPAPI_API_KEY=your_serpapi_key
```

### API Documentation

Once the server is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI Schema: http://localhost:8000/openapi.json

## 🧪 Testing

```bash
# Run API tests
python -m pytest tests/test_api_endpoints.py

# Test agent workflow
python test_full_agent_workflow.py
```

## 🔒 Security Considerations

- Input validation using Pydantic models
- API key management for LLM providers
- Database connection pooling
- Memory access control via permissions
- Rate limiting (recommended for production)

## 📊 Error Handling

The API provides structured error responses:

```json
{
  "detail": "Error message"
}
```

Common error codes:
- `400`: Bad Request (validation errors)
- `404`: Not Found (agent not found)
- `500`: Internal Server Error (unexpected errors)

## 🎯 Best Practices

1. **Always initialize agents before invoking**: Use `/initialize` endpoint first
2. **Use conversation IDs**: Enable proper memory management with conversation IDs
3. **Cache management**: Agents are cached automatically, no need to reinitialize
4. **Error handling**: Implement retry logic for transient errors
5. **Monitor API health**: Use health check endpoints in production

## 🔗 Related Documentation

- See `../README.md` for overall architecture
- See `../core/README.md` for agent core functionality
- See `../memory/README.md` for memory system
- See `../tools/README.md` for tool system
- See `../REGISTER_AGENT_EXAMPLES.md` for registration examples
