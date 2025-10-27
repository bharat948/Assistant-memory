"""
Memory system configuration - Choose between PostgreSQL and MongoDB.
"""
import os
from typing import Optional
from .mongodb_memory import MongoDBEnhancedMemory
from .enhanced_memory import EnhancedMemory


def create_memory_instance(
    storage_type: Optional[str] = None,
    **kwargs
):
    """
    Create a memory instance based on configuration.
    
    Args:
        storage_type: "postgres" or "mongo" (default: auto-detect from env)
        **kwargs: Additional arguments passed to memory constructor
    
    Returns:
        EnhancedMemory or MongoDBEnhancedMemory instance
    """
    # Auto-detect storage type from environment
    if storage_type is None:
        if os.getenv("POSTGRES_DSN"):
            storage_type = "postgres"
        elif os.getenv("MONGO_URI"):
            storage_type = "mongo"
        else:
            # Default to MongoDB
            storage_type = "mongo"
    
    if storage_type == "mongo":
        mongo_uri = kwargs.get('mongo_uri', os.getenv("MONGO_URI", "mongodb://localhost:27017"))
        db_name = kwargs.get('db_name', os.getenv("MONGO_DB_NAME", "agentic"))
        return MongoDBEnhancedMemory(
            mongo_uri=mongo_uri,
            db_name=db_name,
            **{k: v for k, v in kwargs.items() if k not in ['mongo_uri', 'db_name']}
        )
    elif storage_type == "postgres":
        db_dsn = kwargs.get('db_dsn', os.getenv("POSTGRES_DSN"))
        if not db_dsn:
            raise ValueError("POSTGRES_DSN environment variable must be set")
        return EnhancedMemory(
            db_dsn=db_dsn,
            **{k: v for k, v in kwargs.items() if k != 'db_dsn'}
        )
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")


# Backward compatibility - default to MongoDB
# Use create_memory_instance() for automatic selection
def get_memory_instance(**kwargs):
    """Get memory instance (defaults to MongoDB)"""
    return create_memory_instance(storage_type=None, **kwargs)

