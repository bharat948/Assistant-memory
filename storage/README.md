# Storage Module

The Storage module provides MongoDB-based data persistence for agent configurations. It includes the AppRepo module that manages agent registration, retrieval, and updates.

## 📁 Module Structure

```
storage/
├── __init__.py                    # Module exports
├── config.py                      # Storage configuration
└── agent_repo/                    # Agent repository
    ├── __init__.py
    ├── apprepo.py                # MongoDB DAO implementation
    ├── models.py                 # Pydantic models
    └── service.py                # Service layer
```

## 🎯 Key Components

### 1. AppRepo Service (`agent_repo/service.py`)

High-level service layer for agent management.

#### Class: `AppRepoService`

```python
from storage.agent_repo.service import AppRepoService
from storage.agent_repo.apprepo import AppRepoDAO

service = AppRepoService(AppRepoDAO(db))

# Register agent
agent_id = await service.register_agent(agent_data)

# Fetch agent
agent = await service.fetch_agent_by_id("my_agent")

# List agents
agents = await service.list_agents()

# Update agent
success = await service.update_agent("my_agent", update_data)

# Retire agent
success = await service.retire_agent("my_agent")
```

#### Methods

**`async register_agent(agent_data: dict) -> str`**
- Registers a new agent configuration
- Validates and stores agent data in MongoDB
- Returns agent_id

**`async fetch_agent_by_name(name: str) -> AgentConfig`**
- Retrieves agent by name
- Returns AgentConfig object

**`async fetch_agent_by_id(agent_id: str) -> AgentConfig`**
- Retrieves agent by ID
- Returns AgentConfig object
- Raises ValueError if not found

**`async list_agents(status: str = None) -> List[AgentConfig]`**
- Lists all agents (optionally filtered by status)
- Returns list of AgentConfig objects

**`async update_agent(agent_id: str, update_data: dict) -> bool`**
- Updates agent configuration
- Returns True if successful

**`async retire_agent(agent_id: str) -> bool`**
- Deletes/archives agent
- Returns True if successful

### 2. AppRepo DAO (`agent_repo/apprepo.py`)

Low-level data access object for MongoDB operations.

#### Class: `AppRepoDAO`

```python
from storage.agent_repo.apprepo import AppRepoDAO

dao = AppRepoDAO(db)

# Insert agent
agent_id = await dao.insert(agent_config)

# Get by ID
agent = await dao.get_by_id(agent_id)

# Get by name
agent = await dao.get_by_name(name)

# List all
agents = await dao.list_all(status="active")

# Update
success = await dao.update(agent_id, update_data)

# Delete
success = await dao.delete(agent_id)
```

#### MongoDB Collection Structure

**Collection**: `agents`

**Document Schema:**
```json
{
  "_id": "agent_123",
  "agent_id": "agent_123",
  "name": "My Agent",
  "agent_type": "react_agent",
  "description": "Agent description",
  "version": 1,
  "status": "active",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "created_by": "user",
  "tags": ["tag1", "tag2"],
  "llm_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 4000
  },
  "system_prompt_template": "You are...",
  "allowed_roles": ["user", "admin"],
  "allowed_tool_ids": ["web_search"],
  "dependencies": {
    "allowed_tool_names": ["WebSearchTool"],
    "allowed_sub_agent_names": []
  },
  "output_schema": null
}
```

### 3. Agent Config Model (`agent_repo/models.py`)

Pydantic model for type safety and validation.

```python
from storage.agent_repo.models import AgentConfig, LLMConfig, Dependencies

agent_config = AgentConfig(
    agent_id="my_agent",
    name="My Agent",
    agent_type="react_agent",
    description="Agent description",
    version=1,
    status="active",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
    created_by="user",
    tags=["tag1"],
    llm_config=LLMConfig(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=4000
    ),
    system_prompt_template="You are...",
    allowed_roles=["user", "admin"],
    allowed_tool_ids=["web_search"],
    dependencies=Dependencies(
        allowed_tool_names=["WebSearchTool"],
        allowed_sub_agent_names=[]
    ),
    output_schema=None
)
```

#### Models

**LLMConfig**
```python
class LLMConfig(BaseModel):
    model: str
    temperature: float
    max_tokens: int
```

**Dependencies**
```python
class Dependencies(BaseModel):
    allowed_tool_names: List[str]
    allowed_sub_agent_names: List[str]
```

**AgentConfig**
```python
class AgentConfig(BaseModel):
    _id: Optional[str] = None
    agent_id: str
    name: str
    agent_type: str
    description: Optional[str]
    version: int = 1
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str]
    tags: List[str] = []
    llm_config: Optional[LLMConfig]
    system_prompt_template: Optional[str] = None
    allowed_roles: List[str] = []
    allowed_tool_ids: List[str] = []
    dependencies: Optional[Dependencies]
    output_schema: Optional[Dict[str, Any]] = None
```

### 4. Storage Configuration (`config.py`)

Configuration for storage operations.

```python
from storage.config import StorageConfig

# Access configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "agent_service_db")
```

## 🔧 Usage Examples

### Example 1: Register Agent

```python
from storage.agent_repo.service import AppRepoService
from storage.agent_repo.apprepo import AppRepoDAO

# Initialize service
service = AppRepoService(AppRepoDAO(db))

# Register agent
agent_data = {
    "agent_id": "my_agent",
    "name": "My Agent",
    "agent_type": "react_agent",
    "llm_config": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 4000
    },
    "allowed_tool_ids": ["web_search"],
    "allowed_roles": ["user", "admin"]
}

agent_id = await service.register_agent(agent_data)
print(f"Agent registered: {agent_id}")
```

### Example 2: Fetch Agent

```python
# Fetch by ID
agent = await service.fetch_agent_by_id("my_agent")
print(f"Agent name: {agent.name}")
print(f"Agent type: {agent.agent_type}")

# Fetch by name
agent = await service.fetch_agent_by_name("My Agent")
```

### Example 3: List Agents

```python
# List all agents
agents = await service.list_agents()

for agent in agents:
    print(f"{agent.name} - {agent.status}")

# List only active agents
active_agents = await service.list_agents(status="active")
```

### Example 4: Update Agent

```python
# Update agent configuration
update_data = {
    "status": "active",
    "description": "Updated description"
}

success = await service.update_agent("my_agent", update_data)
```

### Example 5: Delete Agent

```python
# Retire agent
success = await service.retire_agent("my_agent")
```

## 🔄 Integration with Other Modules

### API Module
- Uses AppRepoService for agent operations
- Service called from API endpoints

### Core Module
- AgentInitializer fetches agent configs via service
- Stores agent configurations

### Agent Service
- Wraps AppRepoService with caching
- Provides business logic layer

## 📊 Database Schema

### Agents Collection

```javascript
db.agents.createIndex({ "agent_id": 1 }, { unique: true });
db.agents.createIndex({ "name": 1 });
db.agents.createIndex({ "status": 1 });
db.agents.createIndex({ "created_at": -1 });
```

### Document Structure

```json
{
  "_id": "agent_id",
  "agent_id": "unique_identifier",
  "name": "Agent Name",
  "agent_type": "react_agent",
  "status": "active|draft|archived",
  "llm_config": {...},
  "allowed_tool_ids": [...],
  "timestamps": {...}
}
```

## 🧪 Testing

```bash
# Test agent repository
python -m pytest tests/test_agent_repo.py

# Test agent service
python -m pytest tests/test_agent_service.py
```

## 🔒 Error Handling

The storage module provides comprehensive error handling:

```python
try:
    agent = await service.fetch_agent_by_id("nonexistent")
except ValueError as e:
    print(f"Agent not found: {e}")
```

**Common Errors:**
- `ValueError`: Agent not found
- `DuplicateKeyError`: Agent ID already exists
- `ValidationError`: Invalid agent configuration

## 🎯 Best Practices

1. **Validate before storing**: Use Pydantic models for validation
2. **Handle errors gracefully**: Catch ValueError and other exceptions
3. **Use transactions**: For multi-step operations
4. **Index frequently queried fields**: agent_id, name, status
5. **Monitor database performance**: Use explain() for slow queries

## 🔗 Related Documentation

- See `../api/README.md` for API layer usage
- See `../core/README.md` for agent core usage
- See `../README.md` for overall architecture
