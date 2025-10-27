
from core.agent import Agent
from agent_data.db import get_database
from agent_data.agent_config import AgentConfigService
from agent_data.memory import MemoryService
from agent_data.permissions import AccessPermissions # Assuming permissions will be used directly
from typing import Dict, Any, Optional
import os
import json
from dotenv import load_dotenv
# Assuming GroqLLMClient and MockLLMClient will be handled elsewhere or are not directly needed here
# from memory.llm_clients import GroqLLMClient, MockLLMClient

class AgentInitializer:
    @staticmethod
    async def init_agent(agent_id: str = None) -> Agent:
        if not agent_id:
            raise ValueError("Either agent_id or agent_name must be provided")

        # Load environment variables
        load_dotenv()

        # Fetch config from AgentConfigService
        agent_config_service = AgentConfigService()
        config = await agent_config_service.get_agent_by_id(agent_id)

        if not config:
            raise ValueError("Agent not found")

        # Initialize EnhancedMemory (MongoDB version - now default)
        memory = None
        try:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            mongo_db_name = os.getenv("MONGO_DB_NAME", "agentic")
            
            # Parse allowed tags and collections from environment
            allowed_tags = json.loads(os.getenv("ALLOWED_TAGS", '["general", "work", "code"]'))
            allowed_collections = json.loads(os.getenv("ALLOWED_COLLECTIONS", '["conversations", "general"]'))
            working_memory_threshold = int(os.getenv("WORKING_MEMORY_THRESHOLD", "6"))
            
            # Initialize LLM client for memory
            llm_client = GroqLLMClient()  # You can switch to MockLLMClient for testing
            
            # Create MongoDB-backed MemoryService
            memory_service = MemoryService()
            # Note: LLM client and permissions registration will need to be integrated into MemoryService
            # For now, we'll just instantiate the service.
            memory = memory_service # Assign the service directly for now. Further integration needed.

            print(f"[AgentInitializer] Memory initialized for agent {agent_id} using MemoryService")

        except Exception as e:
            print(f"[AgentInitializer] Warning: Could not initialize memory: {e}")
            memory = None # Ensure memory is None if initialization fails

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
