import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mongo_service.AppRepo.apprepo import AppRepoDAO
from mongo_service.AppRepo.service import AppRepoService
from agent import Agent
from mongo_service.config import MongoDB
mongo_db = MongoDB()

async def get_database():
    if mongo_db.db is None:
        await mongo_db.connect()
    return mongo_db.db

class AgentInitializer:
    @staticmethod
    async def init_agent(agent_id: str = None, agent_name: str = None) -> Agent:
        if not agent_id and not agent_name:
            raise ValueError("Either agent_id or agent_name must be provided")

        db = await get_database()
        dao = AppRepoDAO(db)
        service = AppRepoService(dao)

        # Fetch config from AppRepo
        if agent_id:
            config = await service.fetch_agent_by_id(agent_id)
        else:
            config = await service.fetch_agent_by_name(agent_name)

        if not config:
            raise ValueError("Agent not found")

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
        )

        # TODO (future): resolve dependencies
        # - Fetch tools from ToolRegistryDAO
        # - Fetch sub-agents via recursive AgentInitializer.init_agent

        return agent
