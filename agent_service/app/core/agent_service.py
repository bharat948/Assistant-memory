from typing import List, Dict, Optional
from mongo_service.AppRepo.service import AppRepoService
from mongo_service.AppRepo.apprepo import AppRepoDAO
from agent_service.app.api.models.agent import RegisterAgentRequest
from agent_core.agent_init import AgentInitializer
from agent_core.agent import Agent
from mongo_service.AppRepo.models import AgentConfig

class AgentService:
    # Class-level cache for initialized agents
    _agent_cache: Dict[str, Agent] = {}
    
    def __init__(self, db):
        self.apprepo_service = AppRepoService(AppRepoDAO(db))

    async def register_agent(self, agent_data: RegisterAgentRequest) -> AgentConfig:
        agent_dict = agent_data.dict()
        agent_id = await self.apprepo_service.register_agent(agent_data=agent_dict)
        created_agent = await self.apprepo_service.fetch_agent_by_id(agent_id=agent_data.agent_id)
        return created_agent

    async def initialize_agent(self, agent_id: str) -> Agent:
        print("we are in initialize agent of agent service")
        
        # Check if agent is already cached
        if agent_id in self._agent_cache:
            print(f"[AgentService] Agent {agent_id} found in cache")
            return self._agent_cache[agent_id]
        
        # Initialize agent with memory
        agent = await AgentInitializer.init_agent(agent_id=agent_id)
        
        # Cache the agent
        self._agent_cache[agent_id] = agent
        print(f"[AgentService] Agent {agent_id} cached successfully")
        
        return agent

    async def invoke_agent(self, agent_id: str, prompt: str, history: List[Dict[str, str]] = None, 
                          user_id: str = "default_user", conversation_id: Optional[str] = None) -> Dict:
        """Invokes a cached agent with a given prompt and memory integration."""
        
        # Check if agent is cached, if not raise error
        if agent_id not in self._agent_cache:
            raise ValueError(f"Agent with ID '{agent_id}' not found in cache. Please initialize the agent first.")
        
        agent = self._agent_cache[agent_id]
        
        if not agent:
            raise ValueError(f"Agent with ID '{agent_id}' not found or failed to initialize.")

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
