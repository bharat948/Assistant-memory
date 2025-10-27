
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

        # Initialize EnhancedMemory
        memory = None
        try:
            postgres_dsn = os.getenv("POSTGRES_DSN")
            if postgres_dsn:
                # Parse allowed tags and collections from environment
                allowed_tags = json.loads(os.getenv("ALLOWED_TAGS", '["general", "work", "code"]'))
                allowed_collections = json.loads(os.getenv("ALLOWED_COLLECTIONS", '["conversations", "general"]'))
                working_memory_threshold = int(os.getenv("WORKING_MEMORY_THRESHOLD", "6"))
                
                # Initialize LLM client for memory
                llm_client = GroqLLMClient()  # You can switch to MockLLMClient for testing
                
                # Create EnhancedMemory instance
                memory = EnhancedMemory(
                    db_dsn=postgres_dsn,
                    llm_client=llm_client,
                    working_memory_threshold=working_memory_threshold
                )
                
                # Register agent permissions
                memory.register_agent_permissions(
                    agent_id=agent_id,
                    allowed_tags=allowed_tags,
                    allowed_collections=allowed_collections
                )
                
                print(f"[AgentInitializer] Memory initialized for agent {agent_id}")
            else:
                print("[AgentInitializer] Warning: POSTGRES_DSN not found, memory disabled")
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
