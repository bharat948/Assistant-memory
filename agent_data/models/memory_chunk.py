import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Set

@dataclass
class MemoryChunk:
    id: str
    user_id: str
    agent_id: str
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
            d[f] = d[f].isoformat()
        return d

    def __str__(self):
        return f"MemoryChunk(id={self.id[:8]}, collection={self.collection}, importance={self.importance:.2f}, tags={len(self.tags)})"
