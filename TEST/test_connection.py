import asyncio
from dotenv import load_dotenv
from storage.agent_repo.apprepo import AppRepoDAO
from storage.config import mongo_db, get_database
from storage.agent_repo.service import AppRepoService

load_dotenv()

async def main():
    print("Attempting to connect to MongoDB...")
    await mongo_db.connect()
    
    print("\nTesting MongoDB connection...")
    if await mongo_db.test_connection():
        print("Connection test passed!")
    else:
        print("Connection test failed!")
        return  # Exit early if connection fails
    
    print("\nAttempting to get database instance...")
    db = await get_database()
    if db is not None:
        print(f"Successfully got database: {db.name}")
        
        # Optional: Test a simple database operation
        try:
            collections = await db.list_collection_names()
            print(f"Available collections: {collections}")
        except Exception as e:
            print(f"Error listing collections: {e}")
    else:
        print("Failed to get database instance.")

    print("\nClosing MongoDB connection...")
    await mongo_db.close()

async def test():
    # Register new agent
    mongo_db = await get_database()
    apprepo_dao = AppRepoService(AppRepoDAO(mongo_db))
    agent_data = {
        "agent_id": "some-unique-id",
        "name": "InsightScribeOrchestrator",
        "agent_type": "super_agent",
        "description": "The primary conversational AI companion for healthcare BI",
        "created_by": "system_admin",
        "llm_config": {
            "model": "gpt-4.1-mini",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "allowed_tool_ids":["get_cube_metadata", "execute_bi_query"],
        "allowed_roles": ["admin", "compliance_officer"],
        "dependencies": {
            "allowed_tool_names": ["ExecuteBIQueryTool"],
            "allowed_sub_agent_names": ["QueryGeneratorAgent"]
        }
    }
    agent_id = await apprepo_dao.register_agent(agent_data=agent_data)

    print("New agent created:", agent_id)

    # Fetch by agent_id
    agent_by_id = await apprepo_dao.fetch_agent_by_id("some-unique-id")
    print("\nFetched by agent_id:")
    print(agent_by_id)

    # Fetch by name
    agent_by_name = await apprepo_dao.fetch_agent_by_name("InsightScribeOrchestrator")
    print("\nFetched by name:")
    print(agent_by_name)

    # List all agents
    all_agents = await apprepo_dao.list_agents()
    print("\nList all agents:")
    for agent in all_agents:
        print(agent)

    # Update agent
    update_data = {
        "description": "Updated description for InsightScribeOrchestrator",
        "status": "active"
    }
    update_result = await apprepo_dao.update_agent("some-unique-id", update_data)
    print("\nUpdate result:", update_result)

    # Fetch again to verify update
    updated_agent = await apprepo_dao.fetch_agent_by_id("some-unique-id")
    print("\nUpdated agent:")
    print(updated_agent)

    
if __name__ == "__main__":
    asyncio.run(test())
