"""
PostgreSQL-backed agent cache manager for multi-worker deployments.
"""
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor


class AgentCacheManager:
    """
    Manages agent initialization state in PostgreSQL for multi-worker deployments.
    Uses a simple flag-based approach rather than full serialization.
    """
    
    def __init__(self, db_dsn: str, pool_size: int = 5):
        """
        Initialize the cache manager with PostgreSQL connection.
        
        Args:
            db_dsn: PostgreSQL connection string
            pool_size: Connection pool size
        """
        self.db_dsn = db_dsn
        self._pool = None
        self._init_connection_pool(pool_size)
        self._init_cache_table()
    
    def _init_connection_pool(self, pool_size: int):
        """Initialize PostgreSQL connection pool."""
        try:
            self._pool = pool.ThreadedConnectionPool(
                1, pool_size, dsn=self.db_dsn
            )
            print(f"[AgentCacheManager] Connection pool created (size: {pool_size})")
        except Exception as e:
            print(f"[AgentCacheManager] Failed to create connection pool: {e}")
            raise
    
    def _init_cache_table(self):
        """Initialize the agent_cache table if it doesn't exist."""
        with self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS agent_cache (
                        agent_id TEXT PRIMARY KEY,
                        initialized_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        last_accessed TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        worker_id TEXT,
                        metadata JSONB DEFAULT '{}'
                    )
                """)
                
                # Create index for performance
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_agent_cache_worker 
                    ON agent_cache(worker_id)
                """)
                
                conn.commit()
                print("[AgentCacheManager] Cache table initialized")
            except Exception as e:
                conn.rollback()
                print(f"[AgentCacheManager] Failed to initialize cache table: {e}")
                raise
            finally:
                cur.close()
    
    def _get_connection(self):
        """Get a connection from the pool."""
        return self._pool.getconn()
    
    def _return_connection(self, conn):
        """Return a connection to the pool."""
        self._pool.putconn(conn)
    
    def is_initialized(self, agent_id: str) -> bool:
        """
        Check if an agent is marked as initialized in the database.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if agent is initialized, False otherwise
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "SELECT agent_id FROM agent_cache WHERE agent_id = %s",
                    (agent_id,)
                )
                result = cur.fetchone()
                return result is not None
            except Exception as e:
                print(f"[AgentCacheManager] Error checking initialization: {e}")
                return False
            finally:
                cur.close()
    
    def mark_initialized(self, agent_id: str, worker_id: Optional[str] = None, 
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
        
        with self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO agent_cache (agent_id, initialized_at, last_accessed, worker_id, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (agent_id) DO UPDATE SET
                        last_accessed = EXCLUDED.last_accessed,
                        worker_id = EXCLUDED.worker_id,
                        metadata = EXCLUDED.metadata
                """, (
                    agent_id,
                    datetime.now(timezone.utc),
                    datetime.now(timezone.utc),
                    worker_id,
                    json.dumps(metadata)
                ))
                
                conn.commit()
                print(f"[AgentCacheManager] Marked agent {agent_id} as initialized")
                return True
            except Exception as e:
                conn.rollback()
                print(f"[AgentCacheManager] Failed to mark agent as initialized: {e}")
                return False
            finally:
                cur.close()
    
    def update_last_accessed(self, agent_id: str) -> bool:
        """
        Update the last accessed timestamp for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if successful, False otherwise
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE agent_cache 
                    SET last_accessed = %s 
                    WHERE agent_id = %s
                """, (datetime.now(timezone.utc), agent_id))
                
                conn.commit()
                return cur.rowcount > 0
            except Exception as e:
                conn.rollback()
                print(f"[AgentCacheManager] Failed to update last accessed: {e}")
                return False
            finally:
                cur.close()
    
    def get_cache_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cache information for an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Dictionary with cache info or None if not found
        """
        with self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=DictCursor)
            try:
                cur.execute("""
                    SELECT agent_id, initialized_at, last_accessed, worker_id, metadata
                    FROM agent_cache 
                    WHERE agent_id = %s
                """, (agent_id,))
                
                result = cur.fetchone()
                if result:
                    return dict(result)
                return None
            except Exception as e:
                print(f"[AgentCacheManager] Failed to get cache info: {e}")
                return None
            finally:
                cur.close()
    
    def clear_agent_cache(self, agent_id: str) -> bool:
        """
        Remove an agent from the cache.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if successful, False otherwise
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM agent_cache WHERE agent_id = %s", (agent_id,))
                conn.commit()
                success = cur.rowcount > 0
                if success:
                    print(f"[AgentCacheManager] Cleared cache for agent {agent_id}")
                return success
            except Exception as e:
                conn.rollback()
                print(f"[AgentCacheManager] Failed to clear cache: {e}")
                return False
            finally:
                cur.close()
    
    def get_all_cached_agents(self) -> list:
        """
        Get list of all cached agent IDs.
        
        Returns:
            List of agent IDs
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT agent_id FROM agent_cache ORDER BY last_accessed DESC")
                return [row[0] for row in cur.fetchall()]
            except Exception as e:
                print(f"[AgentCacheManager] Failed to get cached agents: {e}")
                return []
            finally:
                cur.close()
    
    def cleanup_old_entries(self, hours: int = 24) -> int:
        """
        Remove cache entries older than specified hours.
        
        Args:
            hours: Age threshold in hours
            
        Returns:
            Number of entries removed
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        with self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("""
                    DELETE FROM agent_cache 
                    WHERE last_accessed < %s
                """, (cutoff,))
                
                count = cur.rowcount
                conn.commit()
                
                if count > 0:
                    print(f"[AgentCacheManager] Cleaned up {count} old cache entries")
                
                return count
            except Exception as e:
                conn.rollback()
                print(f"[AgentCacheManager] Failed to cleanup old entries: {e}")
                return 0
            finally:
                cur.close()
    
    def close(self):
        """Close the connection pool."""
        if self._pool:
            self._pool.closeall()
            print("[AgentCacheManager] Connection pool closed")
