"""
Access permissions and authorization for the memory module.
"""
from dataclasses import dataclass
from typing import Set
from .models import MemoryChunk

@dataclass
class AccessPermissions:
    """Defines what tags and collections an agent can access"""
    allowed_tags: Set[str]
    allowed_collections: Set[str]
    agent_id: str
    
    def can_access_chunk(self, chunk: MemoryChunk) -> bool:
        """Check if agent can access a chunk"""
        # Check collection access
        if chunk.collection not in self.allowed_collections:
            return False
        
        # Check tag access (chunk must have at least one allowed tag)
        if not self.allowed_tags.intersection(chunk.tags):
            return False
        
        return True
    
    def filter_tags(self, tags: Set[str]) -> Set[str]:
        """Filter tags to only allowed ones"""
        return tags.intersection(self.allowed_tags)
    
    def __str__(self):
        return f"Permissions(agent={self.agent_id}, collections={len(self.allowed_collections)}, tags={len(self.allowed_tags)})"
