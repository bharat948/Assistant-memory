import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Any, Optional

@dataclass
class ChatHistoryChunk:
    messages: List[Dict[str, str]]
    agent_sender: str
    agent_receiver: str
    timestamp: datetime
    conversation_id: Optional[str] = None
    raw_metadata: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    agent_id: Optional[str] = None

    def __str__(self):
        return f"ChatHistory(conversation={self.conversation_id}, messages={len(self.messages)}, {self.agent_sender}->{self.agent_receiver})"
