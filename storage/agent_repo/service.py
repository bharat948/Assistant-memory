from typing import Optional, List
from storage.agent_repo.apprepo import AppRepoDAO
from storage.agent_repo.models import AgentConfig

class AppRepoService:
    def __init__(self, dao: AppRepoDAO):
        self.dao = dao

    async def register_agent(self, agent_data: dict) -> str:
        agent = AgentConfig(**agent_data)
        return await self.dao.insert(agent)

    async def fetch_agent_by_name(self, name: str) -> AgentConfig:
        return await self.dao.get_by_name(name)

    async def fetch_agent_by_id(self, agent_id: str) -> AgentConfig:
        print(f"--- AppRepoService: Fetching agent by ID: {agent_id} ---")
        try:
            agent = await self.dao.get_by_id(agent_id)
            if agent:
                print(f"Agent found: {agent.name}")
            else:
                print("Agent not found.")
            return agent
        except Exception as e:
            print(f"Error fetching agent by ID: {e}")
            raise
        finally:
            print(f"--- AppRepoService: Finished fetching agent by ID: {agent_id} ---")

    async def list_agents(self, status: str = None):
        return await self.dao.list_all(status=status)

    async def update_agent(self, agent_id: str, update_data: dict) -> bool:
        return await self.dao.update(agent_id, update_data)

    async def retire_agent(self, agent_id: str) -> bool:
        return await self.dao.delete(agent_id)
