from typing import List, Dict, Optional
from mongo_service.AppRepo.service import AppRepoService
from mongo_service.AppRepo.apprepo import AppRepoDAO
from agent_service.app.api.models.agent import RegisterAgentRequest
from agent_core.agent_init import AgentInitializer
from agent_core.agent import Agent
from mongo_service.AppRepo.models import AgentConfig
from agent_service.app.core.agent_cache import AgentCacheManager
import os

class AgentService:
    # Class-level cache for initialized agents (process-local for performance)
    _agent_cache: Dict[str, Agent] = {}
    
    def __init__(self, db):
        self.apprepo_service = AppRepoService(AppRepoDAO(db))
        
        # Initialize PostgreSQL-backed cache manager
        postgres_dsn = os.getenv("POSTGRES_DSN")
        if postgres_dsn:
            try:
                self.cache_manager = AgentCacheManager(postgres_dsn)
                print("[AgentService] PostgreSQL cache manager initialized")
            except Exception as e:
                print(f"[AgentService] Warning: Could not initialize cache manager: {e}")
                self.cache_manager = None
        else:
            print("[AgentService] Warning: POSTGRES_DSN not found, using in-memory cache only")
            self.cache_manager = None

    async def register_agent(self, agent_data: RegisterAgentRequest) -> AgentConfig:
        agent_dict = agent_data.dict()
        agent_id = await self.apprepo_service.register_agent(agent_data=agent_dict)
        created_agent = await self.apprepo_service.fetch_agent_by_id(agent_id=agent_data.agent_id)
        return created_agent

    async def initialize_agent(self, agent_id: str) -> Agent:
        print("we are in initialize agent of agent service")
        
        # Check local cache first (fast path)
        if agent_id in self._agent_cache:
            print(f"[AgentService] Agent {agent_id} found in local cache")
            # Update last accessed in database cache
            if self.cache_manager:
                self.cache_manager.update_last_accessed(agent_id)
            return self._agent_cache[agent_id]
        
        # Check database cache for cross-worker verification
        if self.cache_manager and self.cache_manager.is_initialized(agent_id):
            print(f"[AgentService] Agent {agent_id} found in database cache, reinitializing locally")
            # Agent was initialized by another worker, reinitialize locally
            agent = await AgentInitializer.init_agent(agent_id=agent_id)
            self._agent_cache[agent_id] = agent
            print(f"[AgentService] Agent {agent_id} reinitialized and cached locally")
            return agent
        
        # Initialize agent with memory
        agent = await AgentInitializer.init_agent(agent_id=agent_id)
        
        # Cache the agent locally
        self._agent_cache[agent_id] = agent
        
        # Mark as initialized in database cache
        if self.cache_manager:
            self.cache_manager.mark_initialized(agent_id)
        
        print(f"[AgentService] Agent {agent_id} initialized and cached successfully")
        
        return agent

    async def invoke_agent(self, agent_id: str, prompt: str, 
                          user_id: str = "default_user", conversation_id: Optional[str] = None) -> Dict:
        """Invokes a cached agent with a given prompt and memory integration."""
        
        # Check local cache first
        if agent_id in self._agent_cache:
            agent = self._agent_cache[agent_id]
            if agent:
                # Update last accessed in database cache
                if self.cache_manager:
                    self.cache_manager.update_last_accessed(agent_id)
            else:
                raise ValueError(f"Agent with ID '{agent_id}' failed to initialize.")
        else:
            # Check database cache for cross-worker scenarios
            if self.cache_manager and self.cache_manager.is_initialized(agent_id):
                print(f"[AgentService] Agent {agent_id} found in database cache, reinitializing for invoke")
                # Reinitialize agent locally
                agent = await AgentInitializer.init_agent(agent_id=agent_id)
                self._agent_cache[agent_id] = agent
            else:
                raise ValueError(f"Agent with ID '{agent_id}' not found in cache. Please initialize the agent first.")

        # Invoke agent with memory integration
        response_data = await agent.invoke(
            user_query=prompt,
            user_id=user_id,
            conversation_id=conversation_id
        )

        # Extract the content from the AIMessage
        if isinstance(response_data.get("response"), dict) and "content" in response_data["response"]:
            response_data["response"] = response_data["response"]["content"]
        elif hasattr(response_data.get("response"), "content"):
            response_data["response"] = response_data["response"].content

        return response_data

    async def list_all_agents(self) -> List[AgentConfig]:
        """Lists all registered agents."""
        return await self.apprepo_service.list_agents()
