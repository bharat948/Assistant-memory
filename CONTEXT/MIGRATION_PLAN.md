# Migration Plan: PostgreSQL to MongoDB for Memory Module

## Overview
Current system uses PostgreSQL for memory storage. This document outlines how to migrate to MongoDB while maintaining all existing functionality.

## Current PostgreSQL Schema

### Tables:
1. **short_term_memory**: Stores recent conversation messages
2. **long_term_memory**: Stores long-term knowledge chunks
3. **agent_cache**: Tracks agent initialization state

## Migration Strategy

### Phase 1: Dual Database Support (Recommended)
Implement MongoDB support alongside PostgreSQL, allowing gradual migration.

### Phase 2: MongoDB Schema Design

#### Collection: `short_term_memory`
```python
{
    "_id": UUID,
    "agent_id": str,
    "conversation_id": str,
    "user_id": str,
    "task_id": str (optional),
    "role": str,  # "user" or "assistant"
    "content": str,
    "timestamp": datetime,
    "metadata": dict
}

# Indexes:
# - agent_id + conversation_id (compound)
# - timestamp (descending)
# - user_id
```

#### Collection: `long_term_memory`
```python
{
    "_id": UUID,
    "agent_id": str,
    "user_id": str,
    "task_id": str (optional),
    "conversation_id": str,
    "content": str,
    "summary": str (optional),
    "tags": [str],  # Array of tags
    "collection": str,
    "chunk_type": str,
    "importance": float,
    "metadata": dict,
    "source_message_ids": [UUID],
    "parent_chunk_ids": [UUID],
    "created_at": datetime,
    "updated_at": datetime,
    "last_accessed": datetime,
    "access_count": int,
    "archived": bool
}

# Indexes:
# - agent_id
# - user_id + task_id (compound)
# - conversation_id
# - tags (text index)
# - collection
# - importance (descending)
# - created_at (descending)
# - archived (sparse)
```

#### Collection: `agent_cache`
```python
{
    "agent_id": str (unique),
    "initialized_at": datetime,
    "last_accessed": datetime,
    "worker_id": str,
    "metadata": dict
}

# Indexes:
# - agent_id (unique)
# - worker_id
```

### Phase 3: MongoDB Advantages

1. **No JOIN operations needed** - MongoDB documents are self-contained
2. **Native array support** - Tags array more natural
3. **Flexible schema** - Easier to add new fields
4. **JSON-native** - Metadata storage is seamless
5. **Sharding support** - Better horizontal scaling
6. **Full-text search** - Native text indexes

### Phase 4: Implementation Approach

#### Step 1: Create MongoDB adapter layer
```python
# memory_module/mongodb_memory.py
from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

class MongoDBEnhancedMemory:
    def __init__(self, mongo_uri: str, db_name: str, llm_client=None):
        self.client = AsyncIOMotorClient(mongo_uri)
        self.db = self.client[db_name]
        
        # Collections
        self.short_term = self.db['short_term_memory']
        self.long_term = self.db['long_term_memory']
        
        # Create indexes
        self._create_indexes()
    
    def _create_indexes(self):
        # Short-term memory indexes
        self.short_term.create_index([
            ("agent_id", 1), ("conversation_id", 1)
        ])
        self.short_term.create_index([("timestamp", -1)])
        self.short_term.create_index("user_id")
        
        # Long-term memory indexes
        self.long_term.create_index("agent_id")
        self.long_term.create_index([
            ("user_id", 1), ("task_id", 1)
        ])
        self.long_term.create_index("conversation_id")
        self.long_term.create_index("tags")  # Array index
        self.long_term.create_index("collection")
        self.long_term.create_index([("importance", -1)])
        self.long_term.create_index([("created_at", -1)])
        
        # Full-text search index
        self.long_term.create_index([
            ("content", "text"),
            ("tags", "text")
        ])
```

#### Step 2: Implement Core Methods

**Short-term memory operations:**
```python
async def commit_working_memory(self, chat, agent_id, context_handle):
    messages = []
    for msg in chat.messages:
        message_doc = {
            "_id": uuid.uuid4(),
            "agent_id": agent_id,
            "conversation_id": context_handle.conversation_id,
            "user_id": context_handle.user_id,
            "task_id": context_handle.task_id,
            "role": msg['role'],
            "content": msg['content'],
            "timestamp": chat.timestamp,
            "metadata": chat.raw_metadata or {}
        }
        messages.append(message_doc)
    
    await self.short_term.insert_many(messages)

async def get_short_term_memory_by_user(self, user_id, agent_id, limit):
    query = {"user_id": user_id}
    if agent_id:
        query["agent_id"] = agent_id
    
    cursor = self.short_term.find(query)\
        .sort("timestamp", -1)\
        .limit(limit)
    
    return await cursor.to_list(length=limit)
```

**Long-term memory operations:**
```python
async def _store_chunk(self, **kwargs):
    chunk_doc = {
        "_id": kwargs.get('id', uuid.uuid4()),
        "agent_id": kwargs.get('agent_id', 'default_agent'),
        "user_id": kwargs.get('user_id', 'default_user'),
        "task_id": kwargs.get('task_id'),
        "conversation_id": kwargs.get('source_conversation_id'),
        "content": kwargs['content'],
        "summary": kwargs.get('summary'),
        "tags": list(kwargs.get('tags', [])),  # Already a list
        "collection": kwargs['collection'],
        "chunk_type": kwargs['chunk_type'],
        "importance": kwargs['importance'],
        "metadata": kwargs.get('metadata', {}),
        "source_message_ids": kwargs.get('source_message_ids', []),
        "parent_chunk_ids": kwargs.get('parent_chunks', []),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_accessed": datetime.utcnow(),
        "access_count": 0,
        "archived": False
    }
    
    await self.long_term.insert_one(chunk_doc)
    return str(chunk_doc["_id"])
```

**Search operations:**
```python
async def search_content(self, query, limit=20):
    # MongoDB text search
    cursor = self.long_term.find({
        "$text": {"$search": query},
        "archived": False
    }).sort([
        ("score", {"$meta": "textScore"}),
        ("importance", -1)
    ]).limit(limit)
    
    return await self._cursor_to_chunks(cursor)

async def find_chunks(self, agent_id, tags=None, collection=None, limit=50):
    query = {"agent_id": agent_id, "archived": False}
    
    if tags:
        query["tags"] = {"$in": tags}  # Array intersection
    
    if collection:
        query["collection"] = collection
    
    cursor = self.long_term.find(query)\
        .sort([("importance", -1), ("created_at", -1)])\
        .limit(limit)
    
    return await self._cursor_to_chunks(cursor)
```

#### Step 3: MongoDB-specific optimizations

**Array operations:**
```python
# Add tags
await self.long_term.update_one(
    {"_id": chunk_id},
    {"$addToSet": {"tags": {"$each": new_tags}}}
)

# Remove tags
await self.long_term.update_one(
    {"_id": chunk_id},
    {"$pull": {"tags": {"$in": tags_to_remove}}}
)

# Update importance
await self.long_term.update_one(
    {"_id": chunk_id},
    {
        "$set": {
            "importance": new_importance,
            "updated_at": datetime.utcnow()
        }
    }
)
```

### Phase 5: Compatibility Layer

Create a unified interface:
```python
# memory_module/__init__.py
from typing import Optional

class MemoryBackend:
    def __init__(self, storage_type: str = "postgres"):
        if storage_type == "postgres":
            from .enhanced_memory import EnhancedMemory
            self.memory = EnhancedMemory
        elif storage_type == "mongo":
            from .mongodb_memory import MongoDBEnhancedMemory
            self.memory = MongoDBEnhancedMemory
        else:
            raise ValueError(f"Unknown storage type: {storage_type}")
```

## Migration Benefits

### Performance
- **No JOIN overhead** - All data in single documents
- **Faster writes** - No foreign key constraints
- **Better scalability** - Native sharding support
- **Index flexibility** - Compound indexes for common queries

### Development
- **Simpler queries** - Natural document structure
- **No schema migrations** - Schema evolves organically
- **Type consistency** - All data native to MongoDB

### Architecture
- **Single database** - All data in MongoDB
- **Easier deployment** - One database to manage
- **Consistent tooling** - Motor/pymongo for everything

## Migration Checklist

- [ ] Create `mongodb_memory.py` with all EnhancedMemory methods
- [ ] Implement async/await throughout
- [ ] Add MongoDB indexes matching PostgreSQL performance
- [ ] Create data migration script for existing PostgreSQL data
- [ ] Add feature flag to switch between PostgreSQL/MongoDB
- [ ] Update configuration to support MONGO_URI
- [ ] Update tests to run against MongoDB
- [ ] Performance testing and optimization
- [ ] Documentation update

## Configuration Changes

### Current (.env):
```env
POSTGRES_DSN=postgresql://user:pass@localhost:5432/memory_db
```

### New (.env):
```env
# Choose one
STORAGE_TYPE=mongo  # or "postgres"

# MongoDB config
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=agent_memory_db

# Or keep PostgreSQL for gradual migration
POSTGRES_DSN=postgresql://user:pass@localhost:5432/memory_db
```

## Estimated Migration Time: 2-3 weeks

### Week 1: MongoDB implementation
- Create mongodb_memory.py
- Implement all core methods
- Add indexes

### Week 2: Testing and optimization
- Unit tests
- Integration tests
- Performance tuning

### Week 3: Migration and deployment
- Data migration script
- Deploy to staging
- Production migration

