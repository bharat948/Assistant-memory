# Memory Module

The Memory module provides a comprehensive MongoDB-based memory management system with LLM-powered tagging, consolidation, and permission-based access control.

## 📁 Module Structure

```
memory/
├── __init__.py              # Module exports and EnhancedMemory alias
├── config.py                # Configuration constants and enums
├── mongodb_memory.py        # MongoDB-based EnhancedMemory implementation
├── models.py                # Data models (MemoryChunk, ChatHistoryChunk, etc.)
├── permissions.py           # Access control and permissions
├── tagging.py               # LLM-powered tagging system
├── llm_clients.py           # LLM client implementations
├── logging_config.py        # Logging setup
└── utils.py                 # Utility functions
```

## 🎯 Key Components

### 1. EnhancedMemory Class

**Location**: `mongodb_memory.py`  
**Primary export**: `from memory import EnhancedMemory`

The main memory management class using MongoDB as the backend.

```python
from memory import EnhancedMemory
from memory.llm_clients import GroqLLMClient

# Initialize memory
memory = EnhancedMemory(
    mongo_uri="mongodb://localhost:27017",
    llm_client=GroqLLMClient(),
    db_name="agentic",
    working_memory_threshold=6
)
```

#### Database Structure

**Database**: `agentic`

**Collections:**

1. **`short_term`** - Recent conversation messages
   - Indexed by: `agent_id`, `conversation_id`, `user_id`, `timestamp`
   - Stores: Chat history chunks

2. **`long_term`** - Persistent knowledge chunks
   - Indexed by: `agent_id`, `tags`, `collection`, `importance`
   - Full-text search index on `content`
   - Stores: Memory chunks

3. **`agent_cache`** - Agent initialization cache
   - Indexed by: `agent_id` (unique), `worker_id`
   - Stores: Agent cache metadata

#### Key Methods

**Memory Operations:**

```python
# Store conversation
await memory.commit_working_memory(
    chat=ChatHistoryChunk(...),
    agent_id="agent_123",
    context_handle=ContextualHandle(...)
)

# Retrieve conversation history
messages = await memory.get_short_term_memory_by_user(
    user_id="user_123",
    agent_id="agent_123",
    limit=10
)

# Get memory statistics
stats = await memory.get_statistics()
```

**Search Operations:**

```python
# Full-text search
chunks = await memory.search_content("query", limit=20)

# Find chunks by tags
chunks = await memory.find_chunks(
    agent_id="agent_123",
    tags=["work", "meeting"],
    collection="work_meetings",
    limit=50
)

# Get recent chunks
chunks = await memory.get_recent_chunks(hours=24, limit=100)
```

**Permission Management:**

```python
# Register agent permissions
memory.register_agent_permissions(
    agent_id="agent_123",
    allowed_tags={"work", "meeting", "decision"},
    allowed_collections={"work_meetings", "decisions"}
)

# Get agent permissions
permissions = memory.get_agent_permissions("agent_123")

# Get chunk (with permission check)
chunk = await memory.get_chunk(chunk_id="chunk_123", agent_id="agent_123")
```

### 2. Data Models (`models.py`)

#### ContextualHandle
Carries stable identifiers for users and conversations.

```python
@dataclass
class ContextualHandle:
    user_id: str
    task_id: Optional[str] = None
    conversation_id: str = field(default_factory=lambda: f"conv_{uuid.uuid4()}")
```

**Usage:**
```python
handle = ContextualHandle(
    user_id="user_123",
    task_id="task_456",
    conversation_id="conv_789"
)
```

#### ChatHistoryChunk
Represents a chunk of conversation history.

```python
@dataclass
class ChatHistoryChunk:
    messages: List[Dict[str, str]]  # [{"role": "user", "content": "..."}, ...]
    agent_sender: str
    agent_receiver: str
    timestamp: datetime
    conversation_id: Optional[str] = None
    raw_metadata: Optional[Dict[str, Any]] = None
```

**Usage:**
```python
from datetime import datetime

chunk = ChatHistoryChunk(
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ],
    agent_sender="user_123",
    agent_receiver="agent_123",
    timestamp=datetime.utcnow(),
    conversation_id="conv_789"
)

await memory.commit_working_memory(chunk, agent_id="agent_123", context_handle=handle)
```

#### MemoryChunk
Represents a long-term memory chunk with metadata.

```python
@dataclass
class MemoryChunk:
    id: str
    content: str
    tags: Set[str]
    collection: str
    metadata: Dict[str, Any]
    importance: float
    chunk_type: str
    created_at: datetime
    updated_at: datetime
    last_accessed: datetime
    access_count: int = 0
    source_conversation_id: Optional[str] = None
    parent_chunks: List[str] = field(default_factory=list)
    archived: bool = False
```

### 3. Access Permissions (`permissions.py`)

Role-based access control for memory chunks.

```python
from memory.permissions import AccessPermissions

permissions = AccessPermissions(
    agent_id="agent_123",
    allowed_tags={"work", "meeting"},
    allowed_collections={"work_meetings", "general"}
)

# Check access
if permissions.can_access_chunk(chunk):
    # Agent can access this chunk
    pass
```

**Features:**
- Tag-based filtering
- Collection-based filtering
- Agent-specific permissions
- Access logging and auditing

### 4. LLM Integration (`llm_clients.py`)

LLM clients for tagging and consolidation.

#### GroqLLMClient

```python
from memory.llm_clients import GroqLLMClient

llm_client = GroqLLMClient()

response = await llm_client.generate_tags(
    content="Meeting about project updates",
    policy=LLMTaggingPolicy()
)
```

#### MockLLMClient

For testing without API calls:

```python
from memory.llm_clients import MockLLMClient

llm_client = MockLLMClient()
```

### 5. Tagging System (`tagging.py`)

LLM-powered automatic tagging.

```python
from memory.tagging import LLMTaggingResponse, LLMTaggingPolicy

response = LLMTaggingResponse(
    tags=["work", "meeting", "project"],
    summary="Project status update meeting",
    collection="work_meetings",
    chunk_type="chat"
)

policy = LLMTaggingPolicy(
    allowed_tags={"work", "personal", "code"},
    allowed_collections={"general", "work_meetings"}
)
```

## 🔧 Configuration

### Environment Variables

```env
# MongoDB Connection
MONGO_URI=mongodb://localhost:27017

# Groq API (for tagging)
GROQ_API_KEY=your_groq_api_key

# Memory Settings
ALLOWED_TAGS=["general", "work", "code", "bi", "search"]
ALLOWED_COLLECTIONS=["conversations", "general", "work_meetings"]
WORKING_MEMORY_THRESHOLD=6
```

### Collection Types (`config.py`)

Predefined collection types:

```python
from memory.config import CollectionType

CollectionType.WORK_MEETINGS       # Work meeting notes
CollectionType.LEARNING_NOTES      # Learning materials
CollectionType.CODE_SNIPPETS       # Code snippets
CollectionType.DECISIONS           # Decision records
CollectionType.TASKS              # Task notes
CollectionType.PERSONAL_LIFE      # Personal information
CollectionType.FINANCIAL          # Financial records
CollectionType.CONVERSATIONS      # General conversations
CollectionType.REFLECTIONS        # Reflections
CollectionType.PLANNING           # Planning documents
CollectionType.GENERAL            # General storage
CollectionType.CONSOLIDATED        # Consolidated chunks
```

### Chunk Types (`config.py`)

```python
from memory.config import ChunkType

ChunkType.EPISODIC      # Event-based memories
ChunkType.SEMANTIC      # Factual knowledge
ChunkType.PROCEDURAL   # How-to knowledge
ChunkType.WORKING      # Working memory
ChunkType.CHAT         # Chat messages
ChunkType.GENERAL      # General chunks
```

## 📊 Usage Examples

### Example 1: Store Conversation

```python
from memory import EnhancedMemory, ChatHistoryChunk, ContextualHandle
from datetime import datetime

# Initialize memory
memory = EnhancedMemory(mongo_uri="mongodb://localhost:27017")

# Register agent permissions
memory.register_agent_permissions(
    agent_id="my_agent",
    allowed_tags={"general", "work"},
    allowed_collections={"conversations", "general"}
)

# Create chat chunk
chat_chunk = ChatHistoryChunk(
    messages=[
        {"role": "user", "content": "What is Python?"},
        {"role": "assistant", "content": "Python is a programming language..."}
    ],
    agent_sender="user_123",
    agent_receiver="my_agent",
    timestamp=datetime.utcnow()
)

# Store conversation
await memory.commit_working_memory(
    chat=chat_chunk,
    agent_id="my_agent",
    context_handle=ContextualHandle(
        user_id="user_123",
        conversation_id="conv_456"
    )
)
```

### Example 2: Retrieve Conversation History

```python
# Retrieve recent messages
messages = await memory.get_short_term_memory_by_user(
    user_id="user_123",
    agent_id="my_agent",
    limit=10
)

for msg in messages:
    print(f"{msg['role']}: {msg['content']}")
```

### Example 3: Full-Text Search

```python
# Search for relevant chunks
chunks = await memory.search_content(
    query="Python programming",
    limit=20
)

for chunk in chunks:
    print(f"{chunk.collection}: {chunk.content[:100]}...")
```

### Example 4: Find by Tags

```python
# Find chunks by tags
chunks = await memory.find_chunks(
    agent_id="my_agent",
    tags=["work", "meeting"],
    collection="work_meetings",
    limit=50
)
```

### Example 5: Get Statistics

```python
# Get memory statistics
stats = await memory.get_statistics()

print(f"Short-term messages: {stats['short_term_count']}")
print(f"Total chunks: {stats['total_chunks']}")
print(f"Archived chunks: {stats['archived_chunks']}")
print(f"Runtime stats: {stats['runtime']}")
```

## 🔒 Security and Permissions

### Permission System

Agents must be registered with permissions before accessing memory:

```python
# Register permissions
memory.register_agent_permissions(
    agent_id="agent_123",
    allowed_tags={"work", "meeting"},       # Allowed tags
    allowed_collections={"work_meetings"}    # Allowed collections
)

# Attempt to access chunk
chunk = await memory.get_chunk(
    chunk_id="chunk_123",
    agent_id="agent_123"  # Permission checked automatically
)
```

### Access Control Flow

```
1. Agent requests chunk
2. System retrieves agent permissions
3. Check if agent can access chunk's tags/collection
4. If allowed: return chunk
5. If denied: return None
```

## 📈 Performance Optimization

### Indexes

MongoDB collections automatically have indexes on:
- `agent_id`, `conversation_id`, `user_id` (short_term)
- `tags`, `collection`, `importance` (long_term)
- Full-text search on `content` (long_term)

### Lazy Initialization

Collections are initialized on first access:

```python
async def _ensure_collections_initialized(self):
    if not hasattr(self, '_collections_initialized'):
        await self._init_collections()
        self._collections_initialized = True
```

### Connection Pooling

Uses Motor's AsyncIOMotorClient with automatic connection pooling.

## 🧪 Testing

```bash
# Run memory tests
python -m pytest tests/test_mongodb_memory.py

# Test memory migration
python test_mongodb_migration.py
```

## 🔗 Integration with Other Modules

### Core Module
- Agents use EnhancedMemory for conversation history
- Agent.invoke() retrieves/stores via memory

### API Module
- Memory operations triggered by API endpoints
- AgentService coordinates memory usage

### Storage Module
- Both use MongoDB
- Memory uses `agentic` database
- Storage uses `agent_service_db` (or configured name)

## 🎯 Best Practices

1. **Register permissions**: Always register agent permissions before use
2. **Use conversation IDs**: Enable proper conversation tracking
3. **Set appropriate limits**: Avoid fetching too many messages
4. **Handle errors gracefully**: Memory operations may fail
5. **Monitor statistics**: Track memory usage and performance
6. **Close connections**: Call `memory.close()` when done

## 🔗 Related Documentation

- See `../core/README.md` for agent integration
- See `../api/README.md` for API usage
- See `../README.md` for overall architecture
- See `mcp/README.md` for MCP server integration
