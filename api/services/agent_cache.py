"""
MongoDB-backed agent cache manager for multi-worker deployments.
"""
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase


class AgentCacheManager:
    """
    Manages agent initialization state in MongoDB for multi-worker deployments.
    Uses a simple flag-based approach stored in the 'agentic' database.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize the cache manager with MongoDB connection.
        
        Args:
            db: MongoDB database instance
        """
        self.db = db
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Ensure cache collection is initialized"""
        if not self._initialized:
            await self._init_cache_collection()
            self._initialized = True
    
    async def _init_cache_collection(self):
        """Initialize the agent_cache collection if it doesn't exist."""
        try:
            collection = self.db['agent_cache']
            # Create indexes
            await collection.create_index([("agent_id", 1)], unique=True)
            await collection.create_index([("worker_id", 1)])
            await collection.create_index([("last_accessed", -1)])
            print("[AgentCacheManager] Cache collection initialized")
        except Exception as e:
            print(f"[AgentCacheManager] Failed to initialize cache collection: {e}")
            raise
    
    async def is_initialized(self, agent_id: str) -> bool:
        """
        Check if an agent is marked as initialized in the database.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if agent is initialized, False otherwise
        """
        await self._ensure_initialized()
        
        collection = self.db['agent_cache']
        
        try:
            doc = await collection.find_one({"agent_id": agent_id})
            return doc is not None
        except Exception as e:
            print(f"[AgentCacheManager] Error checking initialization: {e}")
            return False
    
    async def mark_initialized(self, agent_id: str, worker_id: Optional[str] = None, 
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark an agent as initialized in the database.
        
        Args:
            agent_id: Agent identifier
            worker_id: Optional worker identifier
            metadata: Optional metadata to store
            
        Returns:
            True if successful, False otherwise
        """
        if worker_id is None:
            worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        
        if metadata is None:
            metadata = {}
        
        await self._ensure_initialized()
        collection = self.db['agent_cache']
        
        try:
            await collection.update_one(
                {"agent_id": agent_id},
                {
                    "$set": {
                        "agent_id": agent_id,
                        "initialized_at": datetime.now(timezone.utc),
                        "last_accessed": datetime.now(timezone.utc),
                        "worker_id": worker_id,
                        "metadata": metadata
                    }
                },
                upsert=True
            )
            
            print(f"[AgentCacheManager] Marked agent {agent_id} as initialized")
            return True
        except Exception as e:
            print(f"[AgentCacheManager] Failed to mark agent as initialized: {e}")
            return False
    
    async def update_last_accessed(self, agent_id: str) -> bool:
        """
        Update the last accessed timestamp for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if successful, False otherwise
        """
        await self._ensure_initialized()
        collection = self.db['agent_cache']
        
        try:
            result = await collection.update_one(
                {"agent_id": agent_id},
                {"$set": {"last_accessed": datetime.now(timezone.utc)}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"[AgentCacheManager] Failed to update last accessed: {e}")
            return False
    
    async def get_cache_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cache information for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary with cache info or None if not found
        """
        await self._ensure_initialized()
        collection = self.db['agent_cache']
        
        try:
            doc = await collection.find_one({"agent_id": agent_id})
            if doc:
                doc['_id'] = str(doc['_id'])
                return doc
            return None
        except Exception as e:
            print(f"[AgentCacheManager] Failed to get cache info: {e}")
            return None
    
    async def clear_agent_cache(self, agent_id: str) -> bool:
        """
        Remove an agent from the cache.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if successful, False otherwise
        """
        await self._ensure_initialized()
        collection = self.db['agent_cache']
        
        try:
            result = await collection.delete_one({"agent_id": agent_id})
            success = result.deleted_count > 0
            if success:
                print(f"[AgentCacheManager] Cleared cache for agent {agent_id}")
            return success
        except Exception as e:
            print(f"[AgentCacheManager] Failed to clear cache: {e}")
            return False
    
    async def get_all_cached_agents(self) -> list:
        """
        Get list of all cached agent IDs.
        
        Returns:
            List of agent IDs
        """
        await self._ensure_initialized()
        collection = self.db['agent_cache']
        
        try:
            cursor = collection.find({}).sort("last_accessed", -1)
            docs = await cursor.to_list(length=None)
            return [doc['agent_id'] for doc in docs]
        except Exception as e:
            print(f"[AgentCacheManager] Failed to get cached agents: {e}")
            return []
    
    async def cleanup_old_entries(self, hours: int = 24) -> int:
        """
        Remove cache entries older than specified hours.
        
        Args:
            hours: Age threshold in hours
            
        Returns:
            Number of entries removed
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        await self._ensure_initialized()
        collection = self.db['agent_cache']
        
        try:
            result = await collection.delete_many({"last_accessed": {"$lt": cutoff}})
            count = result.deleted_count
            
            if count > 0:
                print(f"[AgentCacheManager] Cleaned up {count} old cache entries")
            
            return count
        except Exception as e:
            print(f"[AgentCacheManager] Failed to cleanup old entries: {e}")
            return 0

