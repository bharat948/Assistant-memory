from typing import Optional, List
from bson import ObjectId
from mongo_service.AppRepo.models import AgentConfig
from datetime import datetime

class AppRepoDAO:
    COLLECTION_NAME = "apprepo"

    def __init__(self, db):
        self.db = db

    async def insert(self, agent: AgentConfig) -> str:
        existing = await self.db[AppRepoDAO.COLLECTION_NAME].find_one({
            "$or": [
                {"agent_id": agent.agent_id},
                {"name": agent.name}
            ]
        })
        if existing:
            raise ValueError(f"Agent with agent_id '{agent.agent_id}' or name '{agent.name}' already exists.")
        result = await self.db[AppRepoDAO.COLLECTION_NAME].insert_one(agent.dict(by_alias=True))
        return str(result.inserted_id)

    async def get_by_id(self, agent_id: str) -> Optional[AgentConfig]:
        print(f"--- AppRepoDAO: Getting agent by ID: {agent_id} ---")
        try:
            doc = await self.db[AppRepoDAO.COLLECTION_NAME].find_one({"agent_id": agent_id})
            if doc:
                print("Document found in database.")
                return AgentConfig(**doc)
            else:
                print("Document not found in database.")
                return None
        except Exception as e:
            print(f"Error in get_by_id: {e}")
            raise
        finally:
            print(f"--- AppRepoDAO: Finished getting agent by ID: {agent_id} ---")

    async def get_by_name(self, name: str) -> Optional[AgentConfig]:
        doc = await self.db[AppRepoDAO.COLLECTION_NAME].find_one({"name": name})
        return AgentConfig(**doc) if doc else None

    async def list_all(self, status: Optional[str] = None) -> List[AgentConfig]:
        query = {"status": status} if status else {}
        cursor = self.db[AppRepoDAO.COLLECTION_NAME].find(query)
        return [AgentConfig(**doc) async for doc in cursor]

    async def update(self, agent_id: str, update_data: dict) -> bool:
        result = await self.db[AppRepoDAO.COLLECTION_NAME].update_one(
            {"agent_id": agent_id},
            {"$set": {**update_data, "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0

    async def delete(self, agent_id: str) -> bool:
        result = await self.db[AppRepoDAO.COLLECTION_NAME].update_one(
            {"_id": ObjectId(agent_id)},
            {"$set": {"status": "retired", "updated_at": datetime.utcnow()}}
        )
        return result.modified_count > 0
