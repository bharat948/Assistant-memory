"""
Memory Module - Enhanced Memory System

This module provides a comprehensive memory management system with:
- Short-term and long-term memory storage
- LLM-powered tagging and consolidation
- Permission-based access control
- Full-text search capabilities
- Multi-agent support

Main Components:
- EnhancedMemory: Core memory management class
- GroqLLMClient/MockLLMClient: LLM integration
- MemoryChunk/ChatHistoryChunk: Data models
- AccessPermissions: Security and access control
"""

# Import all public classes and functions for backward compatibility
from .config import (
    CollectionType,
    ChunkType,
    safe_log,
    LOG_DIR
)

from .logging_config import (
    logger,
    storage_logger,
    llm_logger,
    ColoredFormatter
)

from .utils import (
    now_utc,
    iso_str,
    safe_json_parse,
    normalize_tag,
    validate_llm_output
)

from .models import (
    ContextualHandle,
    ChatHistoryChunk,
    MemoryChunk
)

from .permissions import (
    AccessPermissions
)

from .llm_clients import (
    GroqLLMClient,
    MockLLMClient
)

from .tagging import (
    LLMTaggingResponse,
    LLMTaggingPolicy
)

# MongoDB EnhancedMemory is now the only implementation
from .mongodb_memory import MongoDBEnhancedMemory as EnhancedMemory

# Re-export everything for backward compatibility
__all__ = [
    # Configuration
    'CollectionType',
    'ChunkType', 
    'safe_log',
    'LOG_DIR',
    
    # Logging
    'logger',
    'storage_logger',
    'llm_logger',
    'ColoredFormatter',
    
    # Utilities
    'now_utc',
    'iso_str',
    'safe_json_parse',
    'normalize_tag',
    'validate_llm_output',
    
    # Models
    'ContextualHandle',
    'ChatHistoryChunk',
    'MemoryChunk',
    
    # Permissions
    'AccessPermissions',
    
    # LLM Clients
    'GroqLLMClient',
    'MockLLMClient',
    
    # Tagging
    'LLMTaggingResponse',
    'LLMTaggingPolicy',
    
    # Main Classes
    'EnhancedMemory',  # Now uses MongoDB backend
    'MongoDBEnhancedMemory'  # Also available explicitly
]

# Version information
__version__ = "6.0.0"
__author__ = "Enhanced Memory System"
__description__ = "Comprehensive memory management with LLM integration and MongoDB backend"
