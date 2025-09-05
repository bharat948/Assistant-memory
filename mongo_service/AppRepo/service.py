
from typing import Optional, List
from bson import ObjectId
from .apprepo import AppRepoDAO
from .models import AgentConfig
from mongo_service.config import get_database
from datetime import datetime


class AppRepoService:
    def __init__(self, dao: AppRepoDAO):
        self.dao = dao

    async def register_agent(self, agent_data: dict) -> str:
        agent = AgentConfig(**agent_data)
        return await self.dao.insert(agent)

    async def fetch_agent_by_name(self, name: str) -> AgentConfig:
        return await self.dao.get_by_name(name)

    async def fetch_agent_by_id(self, agent_id: str) -> AgentConfig:
        return await self.dao.get_by_id(agent_id)

    async def list_agents(self, status: str = None):
        return await self.dao.list_all(status=status)

    async def update_agent(self, agent_id: str, update_data: dict) -> bool:
        return await self.dao.update(agent_id, update_data)

    async def retire_agent(self, agent_id: str) -> bool:
        return await self.dao.delete(agent_id)
