"""
Configuration constants, enums, and Windows console setup for the memory module.
"""
import os
import sys
from enum import Enum

# IMMEDIATE FIX: Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Log directory configuration
LOG_DIR = 'logger'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
    print(f"Created log directory: {LOG_DIR}")

def safe_log(msg: str) -> str:
    """Replace Unicode characters with ASCII for Windows console"""
    if os.name == 'nt':  # Windows
        return msg.replace('✓', '[OK]').replace('✗', '[FAIL]').replace('→', '->')
    
    return msg

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
