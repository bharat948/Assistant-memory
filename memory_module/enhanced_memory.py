"""
Enhanced Memory System - Main memory management class.
"""
import json
import time
import threading
import uuid
import traceback
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple

import psycopg2
import psycopg2.extras
from psycopg2 import pool

from .config import CollectionType, ChunkType
from .logging_config import logger, storage_logger, llm_logger
from .models import MemoryChunk, ChatHistoryChunk, ContextualHandle
from .permissions import AccessPermissions
from .tagging import LLMTaggingResponse, LLMTaggingPolicy
from .utils import now_utc, safe_json_parse, validate_llm_output, normalize_tag
from .llm_clients import GroqLLMClient, MockLLMClient

class EnhancedMemory:
    def __init__(self, db_dsn: str, llm_client=None, pool_size: int = 5, max_overflow: int = 10, working_memory_threshold: int = 6):
        logger.info("="*70)
        logger.info("Initializing Enhanced Memory System v5.0")
        logger.info("="*70)
        
        self.llm_client = llm_client or GroqLLMClient()
        self._lock = threading.RLock()
        self._permissions_map: Dict[str, AccessPermissions] = {}
        # --- NEW: Working Memory Buffer ---
        self.working_memory_threshold = working_memory_threshold
        self._working_memory: Dict[str, List[Dict[str, Any]]] = {} # {conversation_id: [messages]}
        
        try:
            self._pool = pool.ThreadedConnectionPool(
                1, pool_size + max_overflow, 
                dsn=db_dsn
            )
            logger.info(f"[OK] Connection pool created (size: {pool_size}, max_overflow: {max_overflow})")
        except Exception as e:
            logger.critical(f"Failed to create connection pool: {e}")
            raise
        
        self._init_database()
        self._stats = {
            'chunks_stored': 0,
            'chunks_retrieved': 0,
            'chunks_consolidated': 0,
            'llm_calls': 0,
            'llm_failures': 0
        }
        
        logger.info("[OK] Enhanced Memory System initialized successfully")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self._pool.getconn()
            storage_logger.debug("Connection acquired from pool")
            yield conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if conn:
                self._pool.putconn(conn)
                storage_logger.debug("Connection returned to pool")

    def _init_database(self):
        """Initialize database schema with short-term and long-term memory tables"""
        logger.info("Initializing database schema...")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            
            try:
                # ==========================================
                # SHORT-TERM MEMORY TABLE
                # ==========================================
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS short_term_memory (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        agent_id TEXT NOT NULL,
                        conversation_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        task_id TEXT,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        metadata JSONB DEFAULT '{}'
                    )
                """)
                logger.debug("[OK] short_term_memory table created")
                
                # Short-term memory indexes
                stm_indexes = [
                    ("idx_stm_agent_conv", "short_term_memory(agent_id, conversation_id)"),
                    ("idx_stm_timestamp", "short_term_memory(timestamp DESC)"),
                    ("idx_stm_user", "short_term_memory(user_id)")
                ]
                
                for idx_name, idx_def in stm_indexes:
                    cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
                    logger.debug(f"[OK] Index {idx_name} created")
                
                # ==========================================
                # LONG-TERM MEMORY TABLE
                # ==========================================
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS long_term_memory (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        agent_id TEXT NOT NULL,
                        user_id TEXT NOT NULL,
                        task_id TEXT,
                        conversation_id TEXT NOT NULL,
                        
                        content TEXT NOT NULL,
                        summary TEXT,
                        
                        tags TEXT[] NOT NULL DEFAULT '{}',
                        collection TEXT NOT NULL,
                        chunk_type TEXT NOT NULL,
                        importance REAL NOT NULL DEFAULT 0.5,
                        metadata JSONB DEFAULT '{}',
                        
                        source_message_ids UUID[] DEFAULT '{}',
                        parent_chunk_ids UUID[] DEFAULT '{}',
                        
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        last_accessed TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        access_count INTEGER DEFAULT 0,
                        archived BOOLEAN DEFAULT FALSE
                    )
                """)
                logger.debug("[OK] long_term_memory table created")
                
                # Long-term memory indexes
                ltm_indexes = [
                    ("idx_ltm_agent", "long_term_memory(agent_id)"),
                    ("idx_ltm_user_task", "long_term_memory(user_id, task_id)"),
                    ("idx_ltm_conversation", "long_term_memory(conversation_id)"),
                    ("idx_ltm_tags", "long_term_memory USING GIN(tags)"),
                    ("idx_ltm_collection", "long_term_memory(collection) WHERE NOT archived"),
                    ("idx_ltm_importance", "long_term_memory(importance DESC)"),
                    ("idx_ltm_created", "long_term_memory(created_at DESC)"),
                    ("idx_ltm_content_fts", "long_term_memory USING GIN(to_tsvector('english', content))")
                ]
                
                for idx_name, idx_def in ltm_indexes:
                    cur.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
                    logger.debug(f"[OK] Index {idx_name} created")
                
                conn.commit()
                logger.info("[OK] Database schema initialized successfully")
                logger.info(f"  - short_term_memory: Ready with {len(stm_indexes)} indexes")
                logger.info(f"  - long_term_memory: Ready with {len(ltm_indexes)} indexes")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to initialize database: {e}")
                logger.error(traceback.format_exc())
                raise
            finally:
                cur.close()

    def commit_working_memory(self, chat: ChatHistoryChunk, agent_id: str = None, context_handle: ContextualHandle = None):
        """
        Store ChatHistoryChunk messages in short_term_memory.
        """
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
        
        with self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            stored_message_ids = []
            
            # Store each message from the chat in short_term_memory
            for message in chat.messages:
                cur.execute("""
                    INSERT INTO short_term_memory (
                        agent_id, conversation_id, user_id, task_id,
                        role, content, timestamp, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    agent_id,
                    context_handle.conversation_id,
                    context_handle.user_id,
                    context_handle.task_id,
                    message['role'],
                    message['content'],
                    chat.timestamp,
                    json.dumps(chat.raw_metadata or {})
                ))
                
                message_id = cur.fetchone()[0]
                stored_message_ids.append(str(message_id))
            
            conn.commit()
            
            logger.info(f"[OK] Stored {len(chat.messages)} messages in short_term_memory for conversation {context_handle.conversation_id}")
            return context_handle.conversation_id

    def get_short_term_memory_by_user(self, user_id: str, agent_id: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retrieve short-term memory messages for a specific user.
        Returns messages ordered by timestamp (most recent first).
        """
        with self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Build query with optional agent_id filter
            if agent_id:
                cur.execute("""
                    SELECT * FROM short_term_memory
                    WHERE user_id = %s AND agent_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (user_id, agent_id, limit))
            else:
                cur.execute("""
                    SELECT * FROM short_term_memory
                    WHERE user_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s
                """, (user_id, limit))
            
            messages = cur.fetchall()
            cur.close()
            
            # Convert to list of dictionaries
            result = []
            for msg in messages:
                result.append({
                    'id': str(msg['id']),
                    'agent_id': msg['agent_id'],
                    'conversation_id': msg['conversation_id'],
                    'user_id': msg['user_id'],
                    'task_id': msg['task_id'],
                    'role': msg['role'],
                    'content': msg['content'],
                    'timestamp': msg['timestamp'],
                    'metadata': msg['metadata']
                })
            
            logger.info(f"[OK] Retrieved {len(result)} short-term messages for user {user_id}")
            return result

    def clear_short_term_memory_by_user(self, user_id: str, agent_id: str = None) -> int:
        """
        Clear short-term memory messages for a specific user.
        Returns the number of messages deleted.
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            if agent_id:
                cur.execute("""
                    DELETE FROM short_term_memory
                    WHERE user_id = %s AND agent_id = %s
                """, (user_id, agent_id))
            else:
                cur.execute("""
                    DELETE FROM short_term_memory
                    WHERE user_id = %s
                """, (user_id,))
            
            deleted_count = cur.rowcount
            conn.commit()
            cur.close()
            
            logger.info(f"[OK] Cleared {deleted_count} short-term messages for user {user_id}")
            return deleted_count

    def get_short_term_memory_count(self, user_id: str, agent_id: str = None) -> int:
        """
        Get the count of short-term memory messages for a specific user.
        More efficient than retrieving all messages just for counting.
        """
        with self._get_connection() as conn:
            cur = conn.cursor()
            
            if agent_id:
                cur.execute("""
                    SELECT COUNT(*) FROM short_term_memory
                    WHERE user_id = %s AND agent_id = %s
                """, (user_id, agent_id))
            else:
                cur.execute("""
                    SELECT COUNT(*) FROM short_term_memory
                    WHERE user_id = %s
                """, (user_id,))
            
            count = cur.fetchone()[0]
            cur.close()
            
            return count

    def _commit_to_long_term_memory(self, chat: ChatHistoryChunk, agent_id: str, context_handle: ContextualHandle, retry: int = 2) -> str:
        """
         PRIMARY METHOD: Receive and process chat history into memory with permission checks
        """
        logger.info(f">>> RECEIVING CHAT HISTORY from agent: {agent_id}")
        logger.info(f"    Chat: {chat}")
        
        # CHECK PERMISSIONS
        permissions = self._check_access(agent_id, "write")
        
        content = "\n".join(f"{m['role']}: {m['content']}" for m in chat.messages)
        storage_logger.info(f"Chat content length: {len(content)} characters")
        storage_logger.debug(f"Chat preview: {content[:200]}...")
        
        # Get existing tags filtered by permissions
        existing_tags = self._get_popular_tags(100)
        allowed_existing_tags = list(permissions.filter_tags(set(existing_tags)))
        logger.debug(f"Retrieved {len(allowed_existing_tags)} allowed popular tags")
        
        llm_resp = None
        
        # Try LLM tagging with retries
        for attempt in range(retry + 1):
            try:
                self._stats['llm_calls'] += 1
                # PASS PERMISSIONS TO PROMPT
                prompt = LLMTaggingPolicy.get_tagging_prompt(
                    chat, 
                    allowed_existing_tags,
                    permissions.allowed_tags,
                    permissions.allowed_collections
                )
                
                llm_logger.info(f"LLM tagging attempt {attempt + 1}/{retry + 1}")
                raw = self.llm_client.complete(prompt)
                
                if isinstance(raw, bytes):
                    raw = raw.decode()
                
                parsed = safe_json_parse(raw)
                ok, err = validate_llm_output(parsed, {'tags', 'collection', 'importance', 'chunk_type'})
                
                if not ok:
                    raise ValueError(err)
                
                # VALIDATE PERMISSIONS
                suggested_collection = parsed['collection']
                if suggested_collection not in permissions.allowed_collections:
                    raise PermissionError(f"Collection '{suggested_collection}' not allowed for agent '{agent_id}'")
                
                # FILTER TAGS TO ALLOWED ONLY
                suggested_tags = {normalize_tag(t) for t in parsed['tags'][:15]}
                filtered_tags = permissions.filter_tags(suggested_tags)
                
                if not filtered_tags:
                    logger.warning(f"No allowed tags in LLM response, using fallback")
                    filtered_tags = {'general', normalize_tag(agent_id)}
                
                llm_resp = LLMTaggingResponse(
                    tags=list(filtered_tags),
                    collection=parsed['collection'],
                    metadata=parsed.get('metadata', {}),
                    importance=float(parsed['importance']),
                    chunk_type=parsed['chunk_type'],
                    summary=parsed.get('summary')
                )
                
                llm_logger.info(f"[OK] LLM processing successful (filtered to {len(filtered_tags)} allowed tags)")
                break
                
            except Exception as e:
                self._stats['llm_failures'] += 1
                llm_logger.warning(f"LLM attempt {attempt + 1} failed: {e}")
                
                if attempt < retry:
                    sleep_time = 0.5 * (2 ** attempt)
                    llm_logger.info(f"Retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
        
        # Fallback if LLM fails
        if not llm_resp:
            llm_logger.warning("All LLM attempts failed, using fallback tagging")
            llm_resp = self._fallback_tagging(chat, content, permissions)
        
        # ADD THIS: Ensure metadata includes agent info
        metadata = llm_resp.metadata.copy() if llm_resp.metadata else {}
        metadata['stored_by_agent'] = agent_id
        metadata['user_id'] = context_handle.user_id
        if context_handle.task_id:
            metadata['task_id'] = context_handle.task_id
        # Store the chunk - THIS MUST RETURN A VALUE
        try:
            chunk_id = self._store_chunk(
                content=llm_resp.summary or content,
                tags=set(llm_resp.tags),
                collection=llm_resp.collection,
                metadata=metadata,
                importance=llm_resp.importance,
                chunk_type=llm_resp.chunk_type,
                source_conversation_id=chat.conversation_id
            )
            
            self._stats['chunks_stored'] += 1
            logger.info(f"[OK] Chat history processed and stored: {chunk_id[:8]}")
            
            return chunk_id  # CRITICAL: Must return the chunk_id
            
        except Exception as e:
            logger.error(f"Failed to store chunk: {e}")
            logger.error(traceback.format_exc())
            raise  # Re-raise to let caller know storage failed

    def _fallback_tagging(self, chat: ChatHistoryChunk, content: str, permissions: AccessPermissions) -> LLMTaggingResponse:
        """Fallback tagging when LLM is unavailable or fails"""
        llm_logger.info("Using fallback tagging strategy")
        
        tags = {'chat', normalize_tag(chat.agent_sender), normalize_tag(chat.agent_receiver)}
        
        # Simple heuristics
        if '?' in content:
            tags.add('question')
        if any(word in content.lower() for word in ['error', 'bug', 'issue']):
            tags.add('problem')
        if any(word in content.lower() for word in ['thanks', 'thank you']):
            tags.add('appreciation')
        
        metadata = {
            'sender': chat.agent_sender,
            'receiver': chat.agent_receiver,
            'fallback': True,
            'message_count': len(chat.messages)
        }
        
        response = LLMTaggingResponse(
            tags=list(tags),
            collection=CollectionType.CONVERSATIONS.value,
            metadata=metadata,
            importance=0.4,
            chunk_type=ChunkType.CHAT.value
        )
        
        llm_logger.info(f"Fallback tagging generated: {response}")
        return response

    def _store_chunk(self, **kwargs) -> str:
        """
        CORE METHOD: Store a memory chunk in the database
        """
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            
            raw_id = kwargs.get('id', uuid.uuid4())
            chunk_id = str(raw_id)
            now = now_utc()
            
            storage_logger.info(f">>> STORING CHUNK: {chunk_id[:8]}")
            storage_logger.info(f"    Collection: {kwargs['collection']}")
            storage_logger.info(f"    Importance: {kwargs['importance']:.2f}")
            storage_logger.info(f"    Type: {kwargs['chunk_type']}")
            storage_logger.info(f"    Tags: {len(kwargs.get('tags', []))}")
            storage_logger.info(f"    Content length: {len(kwargs['content'])} chars")
            
            # Validate parent chunks
            parent_chunks_for_db = kwargs.get('parent_chunks', [])
            if parent_chunks_for_db:
                try:
                    for pc in parent_chunks_for_db:
                        uuid.UUID(pc)
                    storage_logger.debug(f"    Parent chunks: {parent_chunks_for_db}")
                except (ValueError, TypeError) as e:
                    storage_logger.error(f"Invalid UUID in parent_chunks: {e}")
                    parent_chunks_for_db = []
            
            try:
                # Insert chunk
                cur.execute("""
                    INSERT INTO chunks (
                        id, content, collection, importance, chunk_type, metadata,
                        source_conversation_id, parent_chunks, created_at, updated_at,
                        last_accessed, access_count, archived
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s::uuid[],%s,%s,%s,0,False)
                """, (
                    chunk_id, kwargs['content'], kwargs['collection'], kwargs['importance'],
                    kwargs['chunk_type'], json.dumps(kwargs.get('metadata', {})),
                    kwargs.get('source_conversation_id'), parent_chunks_for_db,
                    now, now, now
                ))
                
                # Insert tags
                tags = kwargs.get('tags', [])
                if tags:
                    psycopg2.extras.execute_values(
                        cur,
                        "INSERT INTO tags (chunk_id, tag) VALUES %s ON CONFLICT DO NOTHING",
                        [(chunk_id, t) for t in tags]
                    )
                    storage_logger.debug(f"    Inserted {len(tags)} tags: {', '.join(list(tags)[:10])}")
                
                # Update collections
                cur.execute("""
                    INSERT INTO collections(name, created_at, last_updated, chunk_count)
                    VALUES(%s, %s, %s, 1)
                    ON CONFLICT(name) DO UPDATE SET
                        chunk_count = collections.chunk_count + 1,
                        last_updated = EXCLUDED.last_updated
                """, (kwargs['collection'], now, now))
                
                conn.commit()
                storage_logger.info(f"✓ Chunk {chunk_id[:8]} stored successfully")
                
                return chunk_id
                
            except Exception as e:
                conn.rollback()
                storage_logger.error(f"Failed to store chunk: {e}")
                storage_logger.error(traceback.format_exc())
                raise
            finally:
                cur.close()

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
        
        with self._lock:
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

    def get_chunk(self, chunk_id: str, agent_id: str) -> Optional[MemoryChunk]:
        """
        PRIMARY METHOD: Retrieve a memory chunk by ID with permission check
        """
        logger.info(f">>> RETRIEVING CHUNK: {chunk_id[:8]} by agent: {agent_id}")
        
        # CHECK PERMISSIONS
        permissions = self._check_access(agent_id, "read")
        
        self._stats['chunks_retrieved'] += 1
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            try:
                cur.execute("SELECT * FROM chunks WHERE id=%s", (chunk_id,))
                row = cur.fetchone()
                
                if not row:
                    logger.warning(f"✗ Chunk {chunk_id[:8]} not found")
                    return None
                
                # Get tags
                cur.execute("SELECT tag FROM tags WHERE chunk_id=%s", (chunk_id,))
                tags = {r[0] for r in cur.fetchall()}
                
                chunk = self._row_to_chunk(dict(row), tags)
                
                # CHECK ACCESS PERMISSION
                if not permissions.can_access_chunk(chunk):
                    logger.warning(f"✗ ACCESS DENIED: Agent '{agent_id}' cannot access chunk {chunk_id[:8]}")
                    logger.warning(f"    Chunk collection: {chunk.collection}")
                    logger.warning(f"    Chunk tags: {chunk.tags}")
                    return None
                
                # Update access statistics
                cur.execute(
                    "UPDATE chunks SET access_count=access_count+1, last_accessed=%s WHERE id=%s",
                    (now_utc(), chunk_id)
                )
                
                conn.commit()
                
                storage_logger.info(f"✓ Retrieved: {chunk}")
                storage_logger.info(f"    Access count: {chunk.access_count + 1}")
                
                return chunk
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to retrieve chunk: {e}")
                raise
            finally:
                cur.close()

    def find_chunks(self, agent_id: str, tags: List[str] = None, 
                collection: str = None, limit: int = 50):
        """
        Search long_term_memory with tag array overlap.
        """
        with self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            conditions = ["archived = FALSE", "agent_id = %s"]
            params = [agent_id]
            
            if tags:
                conditions.append("tags && %s")  # Array overlap operator
                params.append(tags)
            
            if collection:
                conditions.append("collection = %s")
                params.append(collection)
            
            query = f"""
                SELECT * FROM long_term_memory
                WHERE {' AND '.join(conditions)}
                ORDER BY importance DESC, created_at DESC
                LIMIT %s
            """
            params.append(limit)
            
            cur.execute(query, params)
            return cur.fetchall()

    def search_content(self, query: str, limit: int = 20) -> List[MemoryChunk]:
        """
        PRIMARY METHOD: Full-text search across content
        """
        logger.info(f">>> FULL-TEXT SEARCH: '{query}' (limit: {limit})")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            try:
                sql = """
                    SELECT c.*,
                           ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) as rank
                    FROM chunks c
                    WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                      AND NOT c.archived
                    ORDER BY rank DESC, c.importance DESC
                    LIMIT %s
                """
                
                cur.execute(sql, (query, query, limit))
                rows = cur.fetchall()
                
                chunks = self._rows_to_chunks(rows)
                
                logger.info(f"✓ Search found {len(chunks)} matches")
                for idx, chunk in enumerate(chunks[:3], 1):
                    storage_logger.debug(f"    {idx}. {chunk} (rank: {rows[idx-1].get('rank', 0):.4f})")
                
                return chunks
                
            except Exception as e:
                logger.error(f"Full-text search failed: {e}")
                raise
            finally:
                cur.close()

    def get_recent_chunks(self, hours: int = 24, limit: int = 100) -> List[MemoryChunk]:
        """
        SECONDARY METHOD: Get recent chunks within time window
        """
        logger.info(f">>> GETTING RECENT CHUNKS (last {hours}h, limit: {limit})")
        
        cutoff = now_utc() - timedelta(hours=hours)
        storage_logger.debug(f"Cutoff timestamp: {cutoff}")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            try:
                cur.execute(
                    "SELECT * FROM chunks WHERE created_at >= %s AND NOT archived ORDER BY created_at DESC LIMIT %s",
                    (cutoff, limit)
                )
                rows = cur.fetchall()
                
                chunks = self._rows_to_chunks(rows)
                
                logger.info(f"✓ Found {len(chunks)} recent chunks")
                if chunks:
                    storage_logger.debug(f"    Oldest: {chunks[-1].created_at}")
                    storage_logger.debug(f"    Newest: {chunks[0].created_at}")
                
                return chunks
                
            except Exception as e:
                logger.error(f"Failed to get recent chunks: {e}")
                raise
            finally:
                cur.close()

    def consolidate_chunks(self, chunk_ids: List[str], agent_id: str) -> Optional[str]:
        """
        ADVANCED METHOD: Consolidate multiple chunks with permission checks
        """
        logger.info(f">>> CONSOLIDATING {len(chunk_ids)} CHUNKS for agent: {agent_id}")
        
        # CHECK PERMISSIONS
        permissions = self._check_access(agent_id, "write")
        
        if not self.llm_client:
            logger.warning("✗ Consolidation requires LLM client")
            return None
        
        if len(chunk_ids) < 2:
            logger.warning("✗ Need at least 2 chunks for consolidation")
            return None
        
        # Retrieve chunks with permission check
        chunks = []
        for cid in chunk_ids:
            chunk = self.get_chunk(cid, agent_id)
            if chunk:
                chunks.append(chunk)
        
        if len(chunks) < 2:
            logger.warning(f"✗ Only {len(chunks)} accessible chunks found")
            return None
        
        logger.info(f"Retrieved {len(chunks)} accessible chunks for consolidation")
        
        try:
            self._stats['llm_calls'] += 1
            
            # PASS PERMISSIONS TO CONSOLIDATION PROMPT
            prompt = LLMTaggingPolicy.get_consolidation_prompt(
                chunks,
                permissions.allowed_tags,
                permissions.allowed_collections
            )
            
            llm_logger.info("Requesting consolidation from LLM with permissions")
            raw = self.llm_client.consolidate(prompt)
            parsed = safe_json_parse(raw)
            
            if not parsed.get("should_consolidate"):
                logger.info("✗ LLM decided not to consolidate")
                return None
            
            # VALIDATE PERMISSIONS
            suggested_collection = parsed.get('collection', CollectionType.CONSOLIDATED.value)
            if suggested_collection not in permissions.allowed_collections:
                logger.error(f"✗ Consolidated collection '{suggested_collection}' not allowed")
                return None
            
            suggested_tags = {normalize_tag(t) for t in parsed['tags']}
            filtered_tags = permissions.filter_tags(suggested_tags)
            
            if not filtered_tags:
                logger.warning("No allowed tags in consolidation, using 'consolidated'")
                filtered_tags = {'consolidated'}
            
            llm_logger.info("✓ LLM approved consolidation with valid permissions")
            
            # Store consolidated chunk
            metadata = parsed.get('metadata', {})
            metadata['consolidated_by_agent'] = agent_id
            
            new_id = self._store_chunk(
                content=parsed['consolidated_summary'],
                tags=filtered_tags,
                collection=suggested_collection,
                metadata=metadata,
                importance=parsed['importance'],
                chunk_type=ChunkType.SEMANTIC.value,
                parent_chunks=[c.id for c in chunks]
            )
            
            # Archive source chunks
            with self._lock, self._get_connection() as conn:
                cur = conn.cursor()
                try:
                    cur.execute(
                        "UPDATE chunks SET archived=TRUE WHERE id IN %s",
                        (tuple(chunk_ids),)
                    )
                    conn.commit()
                    storage_logger.info(f"Archived {len(chunk_ids)} source chunks")
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to archive source chunks: {e}")
                    raise
                finally:
                    cur.close()
            
            self._stats['chunks_consolidated'] += len(chunks)
            logger.info(f"✓ Consolidation successful: {new_id[:8]}")
            
            return new_id
            
        except Exception as e:
            self._stats['llm_failures'] += 1
            logger.error(f"Consolidation failed: {e}")
            logger.error(traceback.format_exc())
            return None

    def update_chunk_importance(self, chunk_id: str, new_importance: float) -> bool:
        """UTILITY METHOD: Update chunk importance score"""
        importance = max(0.0, min(1.0, new_importance))
        logger.info(f">>> UPDATING IMPORTANCE: {chunk_id[:8]} -> {importance:.2f}")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE chunks SET importance=%s, updated_at=%s WHERE id=%s",
                    (importance, now_utc(), chunk_id)
                )
                success = cur.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"✓ Importance updated")
                else:
                    logger.warning(f"✗ Chunk not found")
                
                return success
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to update importance: {e}")
                raise
            finally:
                cur.close()

    def add_tags_to_chunk(self, chunk_id: str, new_tags: Set[str]) -> int:
        """UTILITY METHOD: Add tags to existing chunk"""
        normalized_tags = {normalize_tag(t) for t in new_tags}
        logger.info(f">>> ADDING TAGS to {chunk_id[:8]}: {normalized_tags}")
        
        added = 0
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            try:
                for tag in normalized_tags:
                    cur.execute(
                        "INSERT INTO tags(chunk_id, tag) VALUES(%s, %s) ON CONFLICT DO NOTHING",
                        (chunk_id, tag)
                    )
                    added += cur.rowcount
                conn.commit()
                
                logger.info(f"✓ Added {added} new tags")
                return added
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to add tags: {e}")
                raise
            finally:
                cur.close()

    def remove_tags_from_chunk(self, chunk_id: str, tags_to_remove: Set[str]) -> int:
        """UTILITY METHOD: Remove tags from chunk"""
        normalized_tags = tuple(normalize_tag(t) for t in tags_to_remove)
        logger.info(f">>> REMOVING TAGS from {chunk_id[:8]}: {normalized_tags}")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "DELETE FROM tags WHERE chunk_id=%s AND tag IN %s",
                    (chunk_id, normalized_tags)
                )
                removed = cur.rowcount
                conn.commit()
                
                logger.info(f"✓ Removed {removed} tags")
                return removed
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to remove tags: {e}")
                raise
            finally:
                cur.close()

    def archive_chunk(self, chunk_id: str) -> bool:
        """UTILITY METHOD: Archive a chunk (soft delete)"""
        logger.info(f">>> ARCHIVING CHUNK: {chunk_id[:8]}")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE chunks SET archived=TRUE, updated_at=%s WHERE id=%s",
                    (now_utc(), chunk_id)
                )
                success = cur.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"✓ Chunk archived")
                else:
                    logger.warning(f"✗ Chunk not found")
                
                return success
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to archive chunk: {e}")
                raise
            finally:
                cur.close()

    def delete_chunk(self, chunk_id: str) -> bool:
        """UTILITY METHOD: Permanently delete a chunk"""
        logger.info(f">>> DELETING CHUNK: {chunk_id[:8]}")
        logger.warning("Permanent deletion - cannot be undone!")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM chunks WHERE id=%s", (chunk_id,))
                success = cur.rowcount > 0
                conn.commit()
                
                if success:
                    logger.info(f"✓ Chunk deleted permanently")
                else:
                    logger.warning(f"✗ Chunk not found")
                
                return success
            except Exception as e:
                conn.rollback()
                logger.error(f"Failed to delete chunk: {e}")
                raise
            finally:
                cur.close()

    def cleanup_old_chunks(self, days: int = 90, min_importance: float = 0.3) -> int:
        """MAINTENANCE METHOD: Archive old, low-importance chunks"""
        cutoff = now_utc() - timedelta(days=days)
        logger.info(f">>> CLEANUP: Archiving chunks older than {days} days with importance < {min_importance}")
        storage_logger.debug(f"Cutoff date: {cutoff.date()}")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(
                    """UPDATE chunks SET archived=TRUE, updated_at=%s 
                       WHERE created_at < %s AND importance < %s AND NOT archived""",
                    (now_utc(), cutoff, min_importance)
                )
                count = cur.rowcount
                conn.commit()
                
                logger.info(f"✓ Archived {count} old chunks")
                return count
            except Exception as e:
                conn.rollback()
                logger.error(f"Cleanup failed: {e}")
                raise
            finally:
                cur.close()

    def get_statistics(self) -> Dict[str, Any]:
        """METADATA METHOD: Get comprehensive memory statistics"""
        logger.info(">>> GENERATING STATISTICS")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            try:
                stats = {}
                
                # Total chunks
                cur.execute("SELECT COUNT(*) AS total FROM chunks WHERE NOT archived")
                stats['total_chunks'] = cur.fetchone()['total']
                
                # Archived chunks
                cur.execute("SELECT COUNT(*) AS archived FROM chunks WHERE archived")
                stats['archived_chunks'] = cur.fetchone()['archived']
                
                # By type
                cur.execute("SELECT chunk_type, COUNT(*) AS cnt FROM chunks WHERE NOT archived GROUP BY chunk_type")
                stats['by_type'] = {r['chunk_type']: r['cnt'] for r in cur.fetchall()}
                
                # Top collections
                cur.execute("SELECT collection, COUNT(*) AS cnt FROM chunks WHERE NOT archived GROUP BY collection ORDER BY cnt DESC LIMIT 10")
                stats['top_collections'] = {r['collection']: r['cnt'] for r in cur.fetchall()}
                
                # Importance stats
                cur.execute("SELECT AVG(importance) AS avg, MIN(importance) AS min, MAX(importance) AS max FROM chunks WHERE NOT archived")
                imp = cur.fetchone()
                stats['importance'] = {
                    'avg': round(imp['avg'] or 0, 3),
                    'min': imp['min'] or 0,
                    'max': imp['max'] or 0
                }
                
                # Unique tags
                cur.execute("SELECT COUNT(DISTINCT tag) AS unique_tags FROM tags")
                stats['unique_tags'] = cur.fetchone()['unique_tags']
                
                # Most accessed
                cur.execute("SELECT id, content, access_count FROM chunks WHERE NOT archived ORDER BY access_count DESC LIMIT 5")
                stats['most_accessed'] = [
                    {'id': str(r['id'])[:8], 'content': r['content'][:100], 'count': r['access_count']}
                    for r in cur.fetchall()
                ]
                
                # Runtime stats
                stats['runtime'] = self._stats.copy()
                
                logger.info("✓ Statistics generated")
                storage_logger.debug(f"Total chunks: {stats['total_chunks']}")
                storage_logger.debug(f"Unique tags: {stats['unique_tags']}")
                
                return stats
                
            except Exception as e:
                logger.error(f"Failed to generate statistics: {e}")
                raise
            finally:
                cur.close()

    def get_all_collections(self) -> List[Dict[str, Any]]:
        """METADATA METHOD: Get all collection information"""
        logger.info(">>> RETRIEVING ALL COLLECTIONS")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cur.execute("SELECT * FROM collections ORDER BY chunk_count DESC")
                collections = [dict(r) for r in cur.fetchall()]
                
                logger.info(f"✓ Retrieved {len(collections)} collections")
                for col in collections:
                    storage_logger.debug(f"    - {col['name']}: {col['chunk_count']} chunks")
                
                return collections
            except Exception as e:
                logger.error(f"Failed to get collections: {e}")
                raise
            finally:
                cur.close()

    def get_all_tags(self, limit: int = 200) -> List[Dict[str, Any]]:
        """METADATA METHOD: Get all tags with usage counts"""
        logger.info(f">>> RETRIEVING ALL TAGS (limit: {limit})")
        
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                cur.execute(
                    "SELECT tag, COUNT(*) AS cnt FROM tags GROUP BY tag ORDER BY cnt DESC LIMIT %s",
                    (limit,)
                )
                tags = [{'tag': r['tag'], 'count': r['cnt']} for r in cur.fetchall()]
                
                logger.info(f"✓ Retrieved {len(tags)} tags")
                if tags:
                    storage_logger.debug(f"    Most used: {tags[0]['tag']} ({tags[0]['count']} chunks)")
                
                return tags
            except Exception as e:
                logger.error(f"Failed to get tags: {e}")
                raise
            finally:
                cur.close()

    def _rows_to_chunks(self, rows) -> List[MemoryChunk]:
        """Helper: Convert database rows to MemoryChunk objects"""
        if not rows:
            return []
        
        ids = tuple(r['id'] for r in rows)
        
        with self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute("SELECT chunk_id, tag FROM tags WHERE chunk_id IN %s", (ids,))
            
            tags_map = {}
            for r in cur.fetchall():
                tags_map.setdefault(r['chunk_id'], set()).add(r['tag'])
            
            cur.close()
        
        return [self._row_to_chunk(dict(r), tags_map.get(r['id'], set())) for r in rows]

    def _row_to_chunk(self, row: dict, tags: Set[str]) -> MemoryChunk:
        """Helper: Convert database row to MemoryChunk object"""
        return MemoryChunk(
            id=str(row['id']),
            content=row['content'],
            tags=tags,
            collection=row['collection'],
            metadata=row['metadata'],
            importance=row['importance'],
            chunk_type=row['chunk_type'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            last_accessed=row['last_accessed'],
            access_count=row['access_count'],
            source_conversation_id=row.get('source_conversation_id'),
            parent_chunks=[str(p) for p in row.get('parent_chunks', [])],
            archived=row.get('archived', False)
        )

    def _get_popular_tags(self, limit: int = 100) -> List[str]:
        """Helper: Get most popular tags for LLM context"""
        with self._lock, self._get_connection() as conn:
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                "SELECT tag, COUNT(*) AS cnt FROM tags GROUP BY tag ORDER BY cnt DESC LIMIT %s",
                (limit,)
            )
            tags = [r['tag'] for r in cur.fetchall()]
            cur.close()
            return tags

    def close(self):
        """Close connection pool and cleanup"""
        logger.info(">>> CLOSING ENHANCED MEMORY SYSTEM")
        
        with self._lock:
            if self._pool:
                self._pool.closeall()
                logger.info("[OK] Connection pool closed")
        
        # Final statistics
        logger.info("="*70)
        logger.info("SESSION STATISTICS")
        logger.info("="*70)
        for key, value in self._stats.items():
            logger.info(f"{key:.<30} {value}")
        logger.info("="*70)


def run_comprehensive_tests():
    """Run comprehensive test suite for Enhanced Memory System"""
    
    POSTGRES_DSN = "dbname=DB-8 user=postgres password=techlab host=localhost port=5432"
    
    def print_test_header(title):
        print("\n" + "="*80)
        print(f"  TEST: {title}")
        print("="*80)
    
    def print_test_result(success, message=""):
        status = "[PASS]" if success else "[FAIL]"
        print(f"\n{status}: {message}")
    
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  ENHANCED MEMORY MODULE v5.0 - COMPREHENSIVE TEST SUITE".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    # Initialize system
    llm = MockLLMClient()
    memory = EnhancedMemory(db_dsn=POSTGRES_DSN, llm_client=llm, pool_size=3)
    
    test_results = []
    stored_chunk_ids = []
    
    # ==================== PRIMARY METHODS TESTS ====================
    
    print_test_header("1. STORING CHAT HISTORY (Primary Method)")
    try:
        chat1 = ChatHistoryChunk(
            messages=[
                {"role": "user", "content": "Can you explain Python async/await?"},
                {"role": "assistant", "content": "async/await is used for asynchronous programming..."}
            ],
            agent_sender="user",
            agent_receiver="PythonTutor",
            timestamp=now_utc(),
            conversation_id="conv_001"
        )
        cid1 = memory.commit_working_memory(chat1)
        stored_chunk_ids.append(cid1)
        print_test_result(True, f"Stored chunk: {cid1[:8]}")
        test_results.append(("Store Chat History", True))
    except Exception as e:
        print_test_result(False, str(e))
        test_results.append(("Store Chat History", False))
    
    # Cleanup
    memory.close()
    
    return test_results

if __name__ == "__main__":
    run_comprehensive_tests()