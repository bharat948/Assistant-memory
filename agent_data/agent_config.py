from typing import Optional, List
from datetime import datetime
from .models.agent_config import AgentConfig
from .db import get_database

class AgentConfigService:
    COLLECTION_NAME = "agents"

    def __init__(self):
        self.db = None

    async def _get_db(self):
        if self.db is None:
            self.db = await get_database()
        return self.db

    async def create_agent(self, agent_data: dict) -> str:
        db = await self._get_db()
        agent = AgentConfig(**agent_data)
        existing = await db[self.COLLECTION_NAME].find_one({
            "$or": [
                {"agent_id": agent.agent_id},
                {"name": agent.name}
            ]
        })
        if existing:
            raise ValueError(f"Agent with agent_id '{agent.agent_id}' or name '{agent.name}' already exists.")
        result = await db[self.COLLECTION_NAME].insert_one(agent.dict(by_alias=True))
        return str(result.inserted_id)

    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentConfig]:
        db = await self._get_db()
        doc = await db[self.COLLECTION_NAME].find_one({"agent_id": agent_id})
        return AgentConfig(**doc) if doc else None

    async def get_agent_by_name(self, name: str) -> Optional[AgentConfig]:
        db = await self._get_db()
        doc = await db[self.COLLECTION_NAME].find_one({"name": name})
        return AgentConfig(**doc) if doc else None

    async def list_agents(self, status: Optional[str] = None) -> List[AgentConfig]:
        db = await self._get_db()
        query = {"status": status} if status else {}
        cursor = db[self.COLLECTION_NAME].find(query)
        return [AgentConfig(**doc) async for doc in cursor]

    async def update_agent(self, agent_id: str, update_data: dict) -> bool:
        db = await self._get_db()
        result = await db[self.COLLECTION_NAME].update_one(
            {"agent_id": agent_id},
            {"$set": {**update_data, "updated_at": datetime.now()}}
        )
        return result.modified_count > 0

    async def delete_agent(self, agent_id: str) -> bool:
        db = await self._get_db()
        result = await db[self.COLLECTION_NAME].update_one(
            {"agent_id": agent_id},
            {"$set": {"status": "retired", "updated_at": datetime.now()}}
        )
        return result.modified_count > 0
