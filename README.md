# 🤖 Agent Service - AI Agent Management Platform

A comprehensive FastAPI-based platform for registering, initializing, and managing AI agents with memory integration, tool support, and conversation history management.

## 🚀 Features

- **Agent Lifecycle Management**: Register, initialize, and invoke AI agents
- **Memory Integration**: Persistent conversation history with EnhancedMemory module
- **Tool System**: Modular tool architecture with BI, web search, and custom tools
- **Caching**: Efficient agent caching to avoid re-initialization
- **Database Support**: MongoDB for agent configs and memory storage
- **RESTful API**: Clean FastAPI endpoints with automatic documentation

## 🏗️ Architecture Overview

```mermaid
graph TB
    Client[Client Application] --> API[FastAPI Service]
    API --> AgentService[Agent Service]
    AgentService --> AgentCore[Agent Core]
    AgentService --> AgentData[Agent Data Module]
    AgentCore --> AgentData
    AgentCore --> ToolModule[Python Tool Module]
    AgentData --> MongoDB[(MongoDB)]
```

## 📁 Project Structure

```
├── api/                     # FastAPI application
│   ├── endpoints/           # REST endpoints
│   ├── models/              # Pydantic models
│   └── services/            # Application services
├── core/                    # Core agent functionality
│   ├── agent.py             # Agent class with memory integration
│   └── agent_init.py        # Agent initialization
├── agent_data/              # Consolidated data module
│   ├── config.py            # DB/connection configuration
│   ├── db.py                # MongoDB connection handler
│   ├── agent_config.py      # Agent CRUD + config models
│   ├── memory.py            # Agent memory logic
│   ├── permissions.py       # Shared permissions logic
│   └── models/              # Data models
│       ├── agent_config.py
│       ├── memory_chunk.py
│       └── chat_history.py
├── tools/                   # Tool system
│   ├── tools/               # Available tools
│   └── services/            # Tool loading service
└── client/                  # Frontend (Angular)
```

## 🔧 Agent Service Refactor: Initialize Once + Memory Integration

### Problem
Currently, the agent service re-initializes agents on every invoke call, which is inefficient. Additionally, there's no conversation history management via the memory module.

### Solution Overview
1. Remove redundant initialization on invoke
2. Integrate EnhancedMemory module with agent lifecycle
3. Streamline endpoint flow: register → initialize (with memory) → invoke (multiple times)
4. Clean up duplicate/unused methods

### Changes Required

#### 1. Agent Core Changes (`agent_core/`)

**`agent.py`** - Add memory support:
- Add `memory: Optional[EnhancedMemory]` attribute to `__init__`
- Store memory instance when provided during initialization
- Update `invoke()` to:
  - Retrieve short-term memory before execution
  - Include conversation history in agent execution context
  - Store chat results back to memory after execution

**`agent_init.py`** - Initialize memory with agent:
- Update `init_agent()` to create EnhancedMemory instance
- Read POSTGRES_DSN, ALLOWED_TAGS, ALLOWED_COLLECTIONS from environment
- Call `memory.register_agent_permissions()` for the agent
- Pass memory instance to Agent constructor
- **Remove** `init_and_invoke()` method (redundant with separate endpoints)

#### 2. Agent Service Changes (`agent_service/`)

**`app/core/agent_service.py`** - Implement agent caching:
- Add class-level cache: `_agent_cache: Dict[str, Agent] = {}`
- Update `initialize_agent()`:
  - Check cache first, return if exists
  - Initialize agent (with memory) via AgentInitializer
  - Store in cache, return agent
- Update `invoke_agent()`:
  - **Remove** internal `initialize_agent()` call
  - Check if agent exists in cache, raise error if not initialized
  - Create fresh `ContextualHandle` for each invoke
  - Call `agent.invoke()` with conversation history from memory
  - Return response

**`app/api/endpoints/agent.py`** - Keep endpoints as-is:
- `/register` - registers agent config to DB
- `/initialize` - initializes agent once (creates LLM, tools, memory)
- `/invoke` - invokes initialized agent (retrieves history, executes, stores result)
- `/` (list) - lists all agents

**`app/api/models/agent.py`** - Add user context:
- Add optional `user_id: Optional[str] = "default_user"` to `InvokeAgentRequest`
- Add optional `conversation_id: Optional[str] = None` to `InvokeAgentRequest`

#### 3. Environment Configuration

Create/update `.env` file with memory module config:

```
POSTGRES_DSN=postgresql://user:pass@localhost:5432/memory_db
ALLOWED_TAGS=["general", "work", "code"]
ALLOWED_COLLECTIONS=["conversations", "general"]
WORKING_MEMORY_THRESHOLD=6
```

#### 4. Code Cleanup

**Remove these methods:**
- `AgentInitializer.init_and_invoke()` in `agent_init.py` (lines 47-84)

**Keep these methods:**
- `AgentInitializer.init_agent()` - used by initialize endpoint
- `Agent.invoke()` - core execution method
- `AgentService.initialize_agent()` - caching wrapper
- `AgentService.invoke_agent()` - memory-aware invoke

### Files Modified

```
agent_core/agent.py
agent_core/agent_init.py
agent_service/app/core/agent_service.py
agent_service/app/api/models/agent.py
.env (create new)
```

### Expected Flow After Changes

1. User calls `/register` with agent config → stored in MongoDB
2. User calls `/initialize/{agent_id}` → creates Agent + Memory → cached in memory
3. User calls `/invoke/{agent_id}` (multiple times):
   - Retrieves agent from cache
   - Gets conversation history from memory
   - Executes agent with history context
   - Stores new messages to memory
   - Returns response

## 🛠️ Installation

### Prerequisites

- Python 3.12+
- MongoDB
- Node.js 18+ (for frontend)

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd agent-service
```

2. **Create virtual environment**
```bash
python -m venv myenv
source myenv/bin/activate  # On Windows: myenv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Environment Configuration**
Create a `.env` file in the root directory:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=agent_service_db

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Memory Module Configuration
ALLOWED_TAGS=["general", "work", "code", "bi", "search"]
ALLOWED_COLLECTIONS=["conversations", "general", "work_meetings"]
WORKING_MEMORY_THRESHOLD=6

# Optional: Tool API Keys
TAVILY_API_KEY=your_tavily_api_key
SERPAPI_API_KEY=your_serpapi_key
GROQ_API_KEY=your_groq_api_key
```

5. **Start the service**
```bash
uvicorn agent_service.app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Core Components

### 1. Agent Core (`agent_core/`)

The heart of the system, handling agent creation and execution.

#### Agent Class
```python
class Agent:
    def __init__(self, agent_id, name, agent_type, description, 
                 version, status, created_by, llm_config, 
                 system_prompt_template, allowed_roles, 
                 dependencies, allowed_tool_ids, 
                 output_schema=None, memory=None):
        # Initialize agent with memory integration
        self.memory = memory
        # Load tools based on allowed_tool_ids
        # Setup LangChain agent executor
```

#### Key Features:
- **Memory Integration**: Automatic conversation history retrieval and storage
- **Tool Loading**: Dynamic tool loading based on `allowed_tool_ids`
- **LangChain Integration**: Uses LangChain's AgentExecutor for tool execution
- **Error Handling**: Graceful fallback to simple chat when tools fail

#### Agent Initialization Flow:
```python
# 1. Load agent config from MongoDB
config = await service.fetch_agent_by_id(agent_id)

# 2. Initialize EnhancedMemory
memory = EnhancedMemory(
    mongo_uri=mongo_uri,
    llm_client=llm_client,
    working_memory_threshold=threshold
)

# 3. Register agent permissions
memory.register_agent_permissions(
    agent_id=agent_id,
    allowed_tags=allowed_tags,
    allowed_collections=allowed_collections
)

# 4. Create Agent instance
agent = Agent(..., memory=memory)
```

### 2. Agent Data Module (`agent_data/`)

Consolidated module for agent configurations, memory, and database interactions.

#### Key Components:
- **`config.py`**: Centralized database and connection configurations.
- **`db.py`**: Handles MongoDB connection and provides a shared client.
- **`agent_config.py`**: Service layer for agent CRUD operations and configuration management.
- **`memory.py`**: Service layer for agent memory logic, including chat history and long-term memory.
- **`permissions.py`**: Shared logic for access permissions.
- **`models/`**: Directory containing individual data models for `agent_config`, `memory_chunk`, and `chat_history`.

#### Memory Operations (via `agent_data.memory.MemoryService`):
```python
# Retrieve conversation history
recent_messages = await memory_service.get_chat_history(
    user_id=user_id, 
    agent_id=agent_id, 
    limit=10
)

# Store conversation
await memory_service.add_chat_history(
    chat_history=chat_chunk
)
```

### 3. Python Tool Module (`python_tool_module/`)

Modular tool system for agent capabilities.

#### Tool Architecture:
```python
class BaseTool(ABC):
    name: str
    description: str
    args_schema: Type[BaseModel]
    
    @abstractmethod
    async def run(self, **kwargs) -> ToolResult:
        pass
```

#### Available Tools:

**BI Tools:**
- `get_cube_metadata`: Retrieve BI cube structure
- `execute_bi_query`: Execute MDX/SQL queries

**Web Search Tools:**
- `web_search`: Tavily-powered web search
- `serpapi_search`: SerpAPI search integration

#### Tool Registration:
```python
TOOL_REGISTRY = {
    "get_cube_metadata": GetCubeMetadataTool,
    "execute_bi_query": ExecuteBIQueryTool,
    "web_search": WebSearchTool,
    "serpapi_search": SerpAPISearchTool,
}
```

#### Tool Loading:
```python
# Load tools based on agent configuration
instantiated_tools = tool_loader.get_allowed_tools(allowed_tool_ids)
```

### 4. Agent Service (`agent_service/`)

FastAPI service with agent caching and lifecycle management.

#### Agent Caching:
```python
class AgentService:
    _agent_cache: Dict[str, Agent] = {}
    
    async def initialize_agent(self, agent_id: str) -> Agent:
        # Check cache first
        if agent_id in self._agent_cache:
            return self._agent_cache[agent_id]
        
        # Initialize and cache
        agent = await AgentInitializer.init_agent(agent_id)
        self._agent_cache[agent_id] = agent
        return agent
```

## 📡 API Endpoints

### Agent Management

#### Register Agent
```http
POST /agents/register
Content-Type: application/json

{
  "agent_id": "bi_analyst_001",
  "name": "BI Data Analyst",
  "agent_type": "react_agent",
  "description": "Specialized in BI data analysis",
  "llm_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "system_prompt_template": "You are a BI data analyst...",
  "allowed_tool_ids": ["get_cube_metadata", "execute_bi_query"],
  "allowed_roles": ["analyst", "admin"]
}
```

#### Initialize Agent
```http
POST /agents/{agent_id}/initialize
```

#### Invoke Agent
```http
POST /agents/{agent_id}/invoke
Content-Type: application/json

{
  "prompt": "Analyze the sales data for Q4",
  "user_id": "user_123",
  "conversation_id": "conv_456"
}
```

#### List Agents
```http
GET /agents/
```

## 🔧 Agent Configuration

### Agent Registration Schema

```python
class RegisterAgentRequest(BaseModel):
    agent_id: str                    # Unique identifier
    name: str                        # Display name
    agent_type: str                  # Agent type (react_agent, etc.)
    description: Optional[str]       # Agent description
    llm_config: Optional[LLMConfig] # LLM configuration
    system_prompt_template: Optional[str]  # Custom system prompt
    allowed_tool_ids: List[str]      # Available tools
    allowed_roles: List[str]          # Access roles
    dependencies: Optional[Dependencies]  # Agent dependencies
    output_schema: Optional[Dict]    # Response schema
```

### LLM Configuration
```python
class LLMConfig(BaseModel):
    model: str           # e.g., "gpt-4o-mini", "gpt-4"
    temperature: float   # 0.0 to 1.0
    max_tokens: int      # Maximum response length
```

### Tool Configuration
Available tools are configured via `allowed_tool_ids`:
- `get_cube_metadata`: BI cube structure analysis
- `execute_bi_query`: BI query execution
- `web_search`: Web search capabilities
- `serpapi_search`: Advanced search with SerpAPI

### Memory Configuration
Memory behavior is controlled via environment variables:
- `MONGO_URI`: MongoDB connection string (used for both agent configs and memory)
- `ALLOWED_TAGS`: Memory tagging categories
- `ALLOWED_COLLECTIONS`: Memory storage collections
- `WORKING_MEMORY_THRESHOLD`: Short-term memory limit

## 🔄 Execution Flow

### 1. Agent Registration
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant AgentService
    participant MongoDB
    
    Client->>API: POST /agents/register
    API->>AgentService: register_agent()
    AgentService->>MongoDB: Store agent config
    MongoDB-->>AgentService: Agent created
    AgentService-->>API: Agent response
    API-->>Client: Success
```

### 2. Agent Initialization
```mermaid
sequenceDiagram
    participant API
    participant AgentService
    participant AgentCore
    participant Memory
    participant MongoDB
    
    API->>AgentService: POST /agents/{id}/initialize
    AgentService->>AgentCore: init_agent()
    AgentCore->>Memory: Create EnhancedMemory
    Memory->>MongoDB: Setup memory collections
    AgentCore->>AgentCore: Create Agent instance
    AgentService->>AgentService: Cache agent
    AgentService-->>API: Agent initialized
```

### 3. Agent Invocation
```mermaid
sequenceDiagram
    participant Client
    participant API
    participant AgentService
    participant Agent
    participant Memory
    participant Tools
    
    Client->>API: POST /agents/{id}/invoke
    API->>AgentService: invoke_agent()
    AgentService->>Agent: invoke()
    Agent->>Memory: get_short_term_memory()
    Memory-->>Agent: Conversation history
    Agent->>Tools: Execute tools
    Tools-->>Agent: Tool results
    Agent->>Memory: commit_working_memory()
    Agent-->>AgentService: Response
    AgentService-->>API: Final response
    API-->>Client: Agent response
```

## 🧪 Testing

### Run Tests
```bash
# Backend tests
python -m pytest

# Agent core tests
python agent_core/test.py

# Tool tests
python python_tool_module/test_tools.py
```

### Interactive Testing
```bash
# Start interactive agent testing
python agent_core/test.py
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "agent_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
Ensure all required environment variables are set:
- `MONGO_URI`: MongoDB connection string
- `OPENAI_API_KEY`: OpenAI API key
- `TAVILY_API_KEY`: Tavily API key (optional)
- `SERPAPI_API_KEY`: SerpAPI key (optional)

## 📊 Monitoring

### Health Checks
```http
GET /health
```

### Metrics
- Agent cache hit rate
- Memory operations count
- Tool execution statistics
- LLM API usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow coding practices (see `rules/coding_practises.md`)
4. Add tests for new features
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create an issue in the repository
- Check the documentation in `rules/`
- Review the architecture guide in `rules/architecture.md`

---

**Built with ❤️ using FastAPI, LangChain, and Enhanced Memory System**
