import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
from .db import get_database
from .models.memory_chunk import MemoryChunk
from .models.chat_history import ChatHistoryChunk
from .config import CollectionType, ChunkType

class MemoryService:
    SHORT_TERM_COLLECTION = "short_term"
    LONG_TERM_COLLECTION = "long_term"

    def __init__(self):
        self.db = None
        self.client = None

    async def _get_db(self):
        if self.db is None:
            self.db = await get_database()
            # Store client reference from the global mongo_db instance
            from .db import mongo_db
            self.client = mongo_db.client
        return self.db

    # Short-Term Memory (Chat History)
    async def add_chat_history(self, chat_history: ChatHistoryChunk) -> str:
        db = await self._get_db()
        result = await db[self.SHORT_TERM_COLLECTION].insert_one(chat_history.__dict__)
        return str(result.inserted_id)

    async def get_chat_history(self, user_id: str, agent_id: str, limit: int = 50) -> List[ChatHistoryChunk]:
        db = await self._get_db()
        cursor = db[self.SHORT_TERM_COLLECTION].find({"user_id": user_id, "agent_id": agent_id}).sort("timestamp", -1).limit(limit)
        result = []
        async for doc in cursor:
            # Remove MongoDB _id field before creating ChatHistoryChunk
            doc.pop('_id', None)
            result.append(ChatHistoryChunk(**doc))
        return result

    # Long-Term Memory (Memory Chunks)
    async def create_memory_chunk(self, memory_chunk: MemoryChunk) -> str:
        db = await self._get_db()
        result = await db[self.LONG_TERM_COLLECTION].insert_one(memory_chunk.to_dict())
        return str(result.inserted_id)

    async def get_memory_chunk(self, chunk_id: str) -> Optional[MemoryChunk]:
        db = await self._get_db()
        doc = await db[self.LONG_TERM_COLLECTION].find_one({"id": chunk_id})
        return MemoryChunk(**doc) if doc else None

    async def find_memory_chunks(self, user_id: str, agent_id: str, tags: List[str] = None, collection: str = None, limit: int = 50) -> List[MemoryChunk]:
        db = await self._get_db()
        query = {"user_id": user_id, "agent_id": agent_id}
        if tags:
            query["tags"] = {"$in": tags}
        if collection:
            query["collection"] = collection
        cursor = db[self.LONG_TERM_COLLECTION].find(query).sort("importance", -1).limit(limit)
        return [MemoryChunk(**doc) async for doc in cursor]

    async def update_memory_chunk(self, chunk_id: str, update_data: dict) -> bool:
        db = await self._get_db()
        result = await db[self.LONG_TERM_COLLECTION].update_one(
            {"id": chunk_id},
            {"$set": {**update_data, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def delete_memory_chunk(self, chunk_id: str) -> bool:
        db = await self._get_db()
        result = await db[self.LONG_TERM_COLLECTION].delete_one({"id": chunk_id})
        return result.deleted_count > 0

    # Tagging and Consolidation (to be implemented)
    async def tag_chat_history(self, chat_history: ChatHistoryChunk) -> dict:
        # Placeholder for LLM-based tagging
        return {"tags": ["sample", "tag"], "collection": "general"}

    async def consolidate_memory_chunks(self, chunks: List[MemoryChunk]) -> Optional[MemoryChunk]:
        # Placeholder for LLM-based consolidation
        return None

    # Additional methods for statistics and utilities
    async def get_short_term_memory_count(self, user_id: str, agent_id: str = None) -> int:
        """Get the count of short-term memory messages for a specific user"""
        db = await self._get_db()
        query = {"user_id": user_id}
        if agent_id:
            query["agent_id"] = agent_id
        count = await db[self.SHORT_TERM_COLLECTION].count_documents(query)
        return count

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        db = await self._get_db()
        stats = {}
        
        # Short-term memory stats
        short_term_count = await db[self.SHORT_TERM_COLLECTION].count_documents({})
        stats['short_term_count'] = short_term_count
        
        # Long-term memory stats
        long_term_count = await db[self.LONG_TERM_COLLECTION].count_documents({"archived": {"$ne": True}})
        archived_count = await db[self.LONG_TERM_COLLECTION].count_documents({"archived": True})
        
        stats['total_chunks'] = long_term_count
        stats['archived_chunks'] = archived_count
        
        return stats

    async def get_db(self):
        """Get the database instance"""
        return await self._get_db()