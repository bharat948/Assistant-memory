"""
Enhanced Memory System - MongoDB version
Migrated from PostgreSQL to MongoDB for better integration.
"""
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Set
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT
from pymongo.errors import DuplicateKeyError

from .config import CollectionType, ChunkType
from .logging_config import logger, storage_logger, llm_logger
from .models import MemoryChunk, ChatHistoryChunk, ContextualHandle
from .permissions import AccessPermissions
from .tagging import LLMTaggingResponse, LLMTaggingPolicy
from .utils import now_utc, safe_json_parse, validate_llm_output, normalize_tag
from .llm_clients import GroqLLMClient, MockLLMClient


class MongoDBEnhancedMemory:
    """
    Enhanced Memory System using MongoDB instead of PostgreSQL.
    Collections structure in 'agentic' database:
    - short_term: Recent conversation messages
    - long_term: Persistent knowledge chunks
    - agent_cache: Agent initialization cache
    """
    
    def __init__(
        self, 
        mongo_uri: str,
        llm_client=None, 
        db_name: str = "agentic",
        working_memory_threshold: int = 6
    ):
        logger.info("="*70)
        logger.info("Initializing MongoDB Enhanced Memory System v6.0")
        logger.info("="*70)
        
        self.llm_client = llm_client or GroqLLMClient()
        self._permissions_map: Dict[str, AccessPermissions] = {}
        self.working_memory_threshold = working_memory_threshold
        self._working_memory: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize MongoDB connection
        try:
            self.client = AsyncIOMotorClient(mongo_uri)
            self.db: AsyncIOMotorDatabase = self.client[db_name]
            logger.info(f"[OK] Connected to MongoDB database: {db_name}")
        except Exception as e:
            logger.critical(f"Failed to connect to MongoDB: {e}")
            raise
        
        # Collections will be initialized on first access (lazy initialization)
        
        self._stats = {
            'chunks_stored': 0,
            'chunks_retrieved': 0,
            'chunks_consolidated': 0,
            'llm_calls': 0,
            'llm_failures': 0
        }
        
        logger.info("[OK] MongoDB Enhanced Memory System initialized successfully")

    async def _init_collections(self):
        """Initialize MongoDB collections and indexes"""
        logger.info("Initializing MongoDB collections...")
        
        try:
            # Short-term memory collection
            short_term_collection = self.db['short_term']
            await short_term_collection.create_index([("agent_id", ASCENDING), ("conversation_id", ASCENDING)])
            await short_term_collection.create_index([("timestamp", DESCENDING)])
            await short_term_collection.create_index([("user_id", ASCENDING)])
            await short_term_collection.create_index([("agent_id", ASCENDING), ("user_id", ASCENDING)])
            logger.debug("[OK] short_term collection indexes created")
            
            # Long-term memory collection
            long_term_collection = self.db['long_term']
            await long_term_collection.create_index([("agent_id", ASCENDING)])
            await long_term_collection.create_index([("user_id", ASCENDING), ("task_id", ASCENDING)])
            await long_term_collection.create_index([("conversation_id", ASCENDING)])
            await long_term_collection.create_index([("tags", ASCENDING)])
            await long_term_collection.create_index([("collection", ASCENDING)])
            await long_term_collection.create_index([("importance", DESCENDING)])
            await long_term_collection.create_index([("created_at", DESCENDING)])
            await long_term_collection.create_index([("archived", ASCENDING)])
            # Text search index
            await long_term_collection.create_index([("content", TEXT)])
            logger.debug("[OK] long_term collection indexes created")
            
            # Agent cache collection
            agent_cache_collection = self.db['agent_cache']
            await agent_cache_collection.create_index([("agent_id", ASCENDING)], unique=True)
            await agent_cache_collection.create_index([("worker_id", ASCENDING)])
            logger.debug("[OK] agent_cache collection indexes created")
            
            logger.info("[OK] MongoDB collections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {e}")
            raise

    async def _ensure_collections_initialized(self):
        """Ensure collections are initialized (lazy init)"""
        if not hasattr(self, '_collections_initialized'):
            await self._init_collections()
            self._collections_initialized = True
    
    async def commit_working_memory(
        self, 
        chat: ChatHistoryChunk, 
        agent_id: str = None, 
        context_handle: ContextualHandle = None
    ):
        """Store ChatHistoryChunk messages in short_term collection"""
        
        # Ensure collections are initialized
        await self._ensure_collections_initialized()
        
        # Use agent_sender as agent_id if not provided
        if agent_id is None:
            agent_id = chat.agent_sender
            
        # Create default context handle if not provided
        if context_handle is None:
            context_handle = ContextualHandle(
                user_id="default_user",
                task_id="default_task",
                conversation_id=chat.conversation_id or f"conv_{uuid.uuid4()}"
            )
        
        collection = self.db['short_term']
        
        # Store each message from the chat
        message_documents = []
        for message in chat.messages:
            message_doc = {
                '_id': str(uuid.uuid4()),
                'agent_id': agent_id,
                'conversation_id': context_handle.conversation_id,
                'user_id': context_handle.user_id,
                'task_id': context_handle.task_id,
                'role': message['role'],
                'content': message['content'],
                'timestamp': chat.timestamp,
                'metadata': chat.raw_metadata or {}
            }
            message_documents.append(message_doc)
        
        if message_documents:
            await collection.insert_many(message_documents)
            logger.info(f"[OK] Stored {len(message_documents)} messages in short_term for conversation {context_handle.conversation_id}")
        
        return context_handle.conversation_id

    async def get_short_term_memory_by_user(
        self, 
        user_id: str, 
        agent_id: str = None, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retrieve short-term memory messages for a specific user"""
        
        await self._ensure_collections_initialized()
        collection = self.db['short_term']
        
        # Build query
        query = {"user_id": user_id}
        if agent_id:
            query["agent_id"] = agent_id
        
        # Execute query
        cursor = collection.find(query).sort("timestamp", DESCENDING).limit(limit)
        messages = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        result = []
        for msg in messages:
            result.append({
                'id': str(msg['_id']),
                'agent_id': msg['agent_id'],
                'conversation_id': msg['conversation_id'],
                'user_id': msg['user_id'],
                'task_id': msg.get('task_id'),
                'role': msg['role'],
                'content': msg['content'],
                'timestamp': msg['timestamp'],
                'metadata': msg.get('metadata', {})
            })
        
        logger.info(f"[OK] Retrieved {len(result)} short-term messages for user {user_id}")
        return result

    async def clear_short_term_memory_by_user(self, user_id: str, agent_id: str = None) -> int:
        """Clear short-term memory messages for a specific user"""
        
        await self._ensure_collections_initialized()
        collection = self.db['short_term']
        
        query = {"user_id": user_id}
        if agent_id:
            query["agent_id"] = agent_id
        
        result = await collection.delete_many(query)
        deleted_count = result.deleted_count
        
        logger.info(f"[OK] Cleared {deleted_count} short-term messages for user {user_id}")
        return deleted_count

    async def get_short_term_memory_count(self, user_id: str, agent_id: str = None) -> int:
        """Get the count of short-term memory messages for a specific user"""
        
        await self._ensure_collections_initialized()
        collection = self.db['short_term']
        
        query = {"user_id": user_id}
        if agent_id:
            query["agent_id"] = agent_id
        
        count = await collection.count_documents(query)
        return count

    async def get_chunk(self, chunk_id: str, agent_id: str) -> Optional[MemoryChunk]:
        """Retrieve a memory chunk by ID with permission check"""
        
        logger.info(f">>> RETRIEVING CHUNK: {chunk_id[:8]} by agent: {agent_id}")
        
        # CHECK PERMISSIONS
        permissions = self._check_access(agent_id, "read")
        
        self._stats['chunks_retrieved'] += 1
        
        collection = self.db['long_term']
        
        try:
            doc = await collection.find_one({"_id": chunk_id})
            
            if not doc:
                logger.warning(f"✗ Chunk {chunk_id[:8]} not found")
                return None
            
            # Convert to MemoryChunk
            chunk = self._doc_to_chunk(doc)
            
            # CHECK ACCESS PERMISSION
            if not permissions.can_access_chunk(chunk):
                logger.warning(f"✗ ACCESS DENIED: Agent '{agent_id}' cannot access chunk {chunk_id[:8]}")
                return None
            
            # Update access statistics
            await collection.update_one(
                {"_id": chunk_id},
                {"$inc": {"access_count": 1}, "$set": {"last_accessed": now_utc()}}
            )
            
            storage_logger.info(f"✓ Retrieved: {chunk}")
            
            return chunk
            
        except Exception as e:
            logger.error(f"Failed to retrieve chunk: {e}")
            raise

    async def search_content(self, query: str, limit: int = 20) -> List[MemoryChunk]:
        """Full-text search across content"""
        
        logger.info(f">>> FULL-TEXT SEARCH: '{query}' (limit: {limit})")
        
        collection = self.db['long_term']
        
        try:
            # MongoDB text search
            cursor = collection.find(
                {"$text": {"$search": query}, "archived": {"$ne": True}}
            ).sort([("score", {"$meta": "textScore"}), ("importance", DESCENDING)]).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            
            chunks = [self._doc_to_chunk(doc) for doc in docs]
            
            logger.info(f"✓ Search found {len(chunks)} matches")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Full-text search failed: {e}")
            # Fallback to regex search
            return await self._fallback_text_search(query, limit)

    async def _fallback_text_search(self, query: str, limit: int) -> List[MemoryChunk]:
        """Fallback text search using regex"""
        
        collection = self.db['long_term']
        
        cursor = collection.find({
            "content": {"$regex": query, "$options": "i"},
            "archived": {"$ne": True}
        }).sort("importance", DESCENDING).limit(limit)
        
        docs = await cursor.to_list(length=limit)
        return [self._doc_to_chunk(doc) for doc in docs]

    async def find_chunks(
        self, 
        agent_id: str, 
        tags: List[str] = None, 
        collection: str = None, 
        limit: int = 50
    ):
        """Search long-term memory with tag filtering"""
        
        query = {"agent_id": agent_id, "archived": {"$ne": True}}
        
        if tags:
            query["tags"] = {"$in": tags}
        
        if collection:
            query["collection"] = collection
        
        long_term_collection = self.db['long_term']
        
        cursor = long_term_collection.find(query).sort(
            [("importance", DESCENDING), ("created_at", DESCENDING)]
        ).limit(limit)
        
        docs = await cursor.to_list(length=limit)
        return docs

    async def get_recent_chunks(self, hours: int = 24, limit: int = 100) -> List[MemoryChunk]:
        """Get recent chunks within time window"""
        
        logger.info(f">>> GETTING RECENT CHUNKS (last {hours}h, limit: {limit})")
        
        cutoff = now_utc() - timedelta(hours=hours)
        
        collection = self.db['long_term']
        
        try:
            cursor = collection.find({
                "created_at": {"$gte": cutoff},
                "archived": {"$ne": True}
            }).sort("created_at", DESCENDING).limit(limit)
            
            docs = await cursor.to_list(length=limit)
            
            chunks = [self._doc_to_chunk(doc) for doc in docs]
            
            logger.info(f"✓ Found {len(chunks)} recent chunks")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to get recent chunks: {e}")
            raise

    def register_agent_permissions(self, agent_id: str, allowed_tags: Set[str], allowed_collections: Set[str]):
        """Register access permissions for an agent"""
        
        logger.info(f">>> REGISTERING PERMISSIONS for agent: {agent_id}")
        logger.info(f"    Allowed collections: {allowed_collections}")
        logger.info(f"    Allowed tags: {len(allowed_tags)} tags")
        
        permissions = AccessPermissions(
            agent_id=agent_id,
            allowed_tags={normalize_tag(t) for t in allowed_tags},
            allowed_collections=allowed_collections
        )
        
        self._permissions_map[agent_id] = permissions
        logger.info(f"✓ Permissions registered: {permissions}")

    def get_agent_permissions(self, agent_id: str) -> Optional[AccessPermissions]:
        """Get permissions for an agent"""
        return self._permissions_map.get(agent_id)

    def _check_access(self, agent_id: str, operation: str = "access") -> AccessPermissions:
        """Check if agent has permissions, raise if not"""
        permissions = self.get_agent_permissions(agent_id)
        if not permissions:
            error_msg = f"Agent '{agent_id}' has no registered permissions"
            logger.error(f"✗ ACCESS DENIED: {error_msg}")
            raise PermissionError(error_msg)
        
        logger.debug(f"✓ Access granted for {agent_id} ({operation})")
        return permissions

    async def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive memory statistics"""
        
        await self._ensure_collections_initialized()
        logger.info(">>> GENERATING STATISTICS")
        
        stats = {}
        
        # Short-term memory stats
        short_term = await self.db['short_term'].count_documents({})
        stats['short_term_count'] = short_term
        
        # Long-term memory stats
        long_term = await self.db['long_term'].count_documents({"archived": {"$ne": True}})
        archived = await self.db['long_term'].count_documents({"archived": True})
        
        stats['total_chunks'] = long_term
        stats['archived_chunks'] = archived
        
        # Runtime stats
        stats['runtime'] = self._stats.copy()
        
        logger.info("✓ Statistics generated")
        logger.info(f"  Short-term messages: {stats['short_term_count']}")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        
        return stats

    def _doc_to_chunk(self, doc: Dict[str, Any]) -> MemoryChunk:
        """Convert MongoDB document to MemoryChunk object"""
        return MemoryChunk(
            id=str(doc['_id']),
            content=doc['content'],
            tags=set(doc.get('tags', [])),
            collection=doc['collection'],
            metadata=doc.get('metadata', {}),
            importance=doc['importance'],
            chunk_type=doc['chunk_type'],
            created_at=doc['created_at'],
            updated_at=doc['updated_at'],
            last_accessed=doc['last_accessed'],
            access_count=doc.get('access_count', 0),
            source_conversation_id=doc.get('conversation_id'),
            parent_chunks=doc.get('parent_chunk_ids', []),
            archived=doc.get('archived', False)
        )

    async def close(self):
        """Close MongoDB connection"""
        logger.info(">>> CLOSING MONGODB ENHANCED MEMORY SYSTEM")
        
        if self.client:
            self.client.close()
            logger.info("[OK] MongoDB connection closed")
        
        # Final statistics
        logger.info("="*70)
        logger.info("SESSION STATISTICS")
        logger.info("="*70)
        for key, value in self._stats.items():
            logger.info(f"{key:.<30} {value}")
        logger.info("="*70)

