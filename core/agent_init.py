
from storage.agent_repo.apprepo import AppRepoDAO
from storage.agent_repo.service import AppRepoService
from core.agent import Agent
from storage.config import get_database
from typing import Dict, Any, Optional
import os
import json
from dotenv import load_dotenv
from memory import EnhancedMemory, GroqLLMClient, MockLLMClient

class AgentInitializer:
    @staticmethod
    async def init_agent(agent_id: str = None) -> Agent:
        if not agent_id:
            raise ValueError("Either agent_id or agent_name must be provided")

        # Load environment variables
        load_dotenv()

        db = await get_database()
        dao = AppRepoDAO(db)
        service = AppRepoService(dao)

        # Fetch config from AppRepo
        config = await service.fetch_agent_by_id(agent_id)

        if not config:
            raise ValueError("Agent not found")

        # Initialize EnhancedMemory (MongoDB version preferred)
        memory = None
        try:
            # Try MongoDB first (recommended)
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            mongo_db_name = os.getenv("MONGO_DB_NAME", "agentic")
            
            # Parse allowed tags and collections from environment
            allowed_tags = json.loads(os.getenv("ALLOWED_TAGS", '["general", "work", "code"]'))
            allowed_collections = json.loads(os.getenv("ALLOWED_COLLECTIONS", '["conversations", "general"]'))
            working_memory_threshold = int(os.getenv("WORKING_MEMORY_THRESHOLD", "6"))
            
            # Initialize LLM client for memory
            llm_client = GroqLLMClient()  # You can switch to MockLLMClient for testing
            
            # Use MongoDB EnhancedMemory (recommended)
            from memory.mongodb_memory import MongoDBEnhancedMemory
            
            memory = MongoDBEnhancedMemory(
                mongo_uri=mongo_uri,
                db_name=mongo_db_name,
                llm_client=llm_client,
                working_memory_threshold=working_memory_threshold
            )
            
            # Register agent permissions
            memory.register_agent_permissions(
                agent_id=agent_id,
                allowed_tags=allowed_tags,
                allowed_collections=allowed_collections
            )
            
            print(f"[AgentInitializer] Memory initialized for agent {agent_id} using MongoDB")
            
        except Exception as e:
            print(f"[AgentInitializer] Warning: Could not initialize memory: {e}")

        agent = Agent(
            agent_id=str(config.agent_id),
            name=config.name,
            agent_type=config.agent_type,
            description=config.description,
            version=config.version,
            status=config.status,
            created_by=config.created_by,
            llm_config=config.llm_config.dict() if config.llm_config else {},
            system_prompt_template=config.system_prompt_template,
            allowed_roles=config.allowed_roles,
            dependencies=config.dependencies.dict() if config.dependencies else {},
            output_schema=config.output_schema,
            allowed_tool_ids=config.allowed_tool_ids or [],
            memory=memory,
        )
        print("Initialized agent:", agent)
        # Best-effort introspection of tool count
        try:
            tool_count = len(getattr(agent, "langchain_tools", []) or [])
            print(f"[AgentInitializer] Agent langchain_tools count={tool_count}")
        except Exception as _:
            pass
        return agent
