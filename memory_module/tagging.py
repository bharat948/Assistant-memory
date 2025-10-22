"""
LLM tagging logic and policies for the memory module.
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
from .models import ChatHistoryChunk, MemoryChunk
from .config import CollectionType, ChunkType
from .logging_config import llm_logger

@dataclass
class LLMTaggingResponse:
    tags: List[str]
    collection: str
    metadata: Dict[str, Any]
    importance: float
    chunk_type: str
    summary: Optional[str] = None
    
    def __str__(self):
        return f"LLMResponse(collection={self.collection}, importance={self.importance:.2f}, tags={len(self.tags)})"

class LLMTaggingPolicy:
    @staticmethod
    def get_tagging_prompt(chat: ChatHistoryChunk, existing_tags: List[str], 
                        allowed_tags: Set[str], allowed_collections: Set[str]) -> str:
        """Generate tagging prompt with permission constraints"""
        msgs = "\n".join(f"{m['role']}: {m['content']}" for m in chat.messages)
        context = f"\nExisting popular tags: {', '.join(existing_tags[:50])}" if existing_tags else ""
        
        prompt = f"""You are an intelligent memory tagging system. Analyze the conversation and return ONLY valid JSON.

    Conversation:
    {msgs}
    {context}

    PERMISSION CONSTRAINTS:
    - You MUST only use tags from this allowed list: {', '.join(sorted(allowed_tags))}
    - You MUST only use collections from: {', '.join(sorted(allowed_collections))}

    Return JSON with these exact fields:
    {{
        "tags": ["tag1", "tag2", "tag3"],  // 3-10 tags (ONLY from allowed list)
        "collection": "one of: {', '.join(sorted(allowed_collections))}",
        "metadata": {{"key_entities": [], "sentiment": "positive/neutral/negative", "topics": []}},
        "importance": 0.5,  // 0.0 to 1.0
        "chunk_type": "one of: episodic, semantic, procedural, working, chat, general",
        "summary": "Brief 1-2 sentence summary"
    }}"""
        
        llm_logger.debug(f"Generated tagging prompt with {len(allowed_tags)} allowed tags")
        return prompt
    
    @staticmethod
    def get_consolidation_prompt(chunks: List[MemoryChunk], 
                                allowed_tags: Set[str], 
                                allowed_collections: Set[str]) -> str:
        """Generate consolidation prompt with permission constraints"""
        summary = "\n".join(
            f"- Chunk {c.id[:8]} (Importance: {c.importance:.2f}, Tags: {', '.join(list(c.tags)[:5])}): {c.content[:150]}..."
            for c in chunks
        )
        
        prompt = f"""You are a memory consolidation system. Analyze these {len(chunks)} related chunks and decide if they should be consolidated.

    Chunks to analyze:
    {summary}

    PERMISSION CONSTRAINTS:
    - Consolidated tags MUST be from: {', '.join(sorted(allowed_tags))}
    - Consolidated collection MUST be from: {', '.join(sorted(allowed_collections))}

    Return JSON:
    {{
        "should_consolidate": true/false,
        "consolidated_summary": "If consolidating, provide merged summary",
        "tags": ["consolidated", "tag1", "tag2"],  // ONLY from allowed list
        "importance": 0.85,
        "collection": "one of: {', '.join(sorted(allowed_collections))}",
        "metadata": {{"consolidation_reason": "why these were merged", "source_count": {len(chunks)}}}
    }}"""
        
        llm_logger.debug(f"Generated consolidation prompt with permissions")
        return prompt
