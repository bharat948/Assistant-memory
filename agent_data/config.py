import os
from enum import Enum

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "agentic")

# Log directory configuration
LOG_DIR = 'logger'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class CollectionType(str, Enum):
    WORK_MEETINGS = "work_meetings"
    LEARNING_NOTES = "learning_notes"
    CODE_SNIPPETS = "code_snippets"
    DECISIONS = "decisions"
    TASKS = "tasks"
    PERSONAL_LIFE = "personal_life"
    FINANCIAL = "financial_records"
    CONVERSATIONS = "conversations"
    REFLECTIONS = "reflections"
    PLANNING = "planning"
    GENERAL = "general"
    CONSOLIDATED = "consolidated"

class ChunkType(str, Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"
    CHAT = "chat"
    GENERAL = "general"
