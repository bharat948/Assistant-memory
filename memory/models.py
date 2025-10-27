"""
Data models and structures for the memory module.
"""
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from .utils import iso_str

@dataclass
class ContextualHandle:
    """
    A handle carrying stable identifiers for a user and their long-term tasks.
    This is used to link memory chunks across different sessions.
    """
    user_id: str
    task_id: Optional[str] = None
    conversation_id: str = field(default_factory=lambda: f"conv_{uuid.uuid4()}")

@dataclass
class ChatHistoryChunk:
    messages: List[Dict[str, str]]
    agent_sender: str
    agent_receiver: str
    timestamp: datetime
    conversation_id: Optional[str] = None
    raw_metadata: Optional[Dict[str, Any]] = None
    
    def __str__(self):
        return f"ChatHistory(conversation={self.conversation_id}, messages={len(self.messages)}, {self.agent_sender}->{self.agent_receiver})"

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
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['tags'] = list(self.tags)
        for f in ['created_at', 'updated_at', 'last_accessed']:
            d[f] = iso_str(d[f])
        return d
    
    def __str__(self):
        return f"MemoryChunk(id={self.id[:8]}, collection={self.collection}, importance={self.importance:.2f}, tags={len(self.tags)})"
