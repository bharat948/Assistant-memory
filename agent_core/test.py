import asyncio
from agent_core.agent_init import AgentInitializer

async def test_agent_initializer():
    agent = await AgentInitializer.init_agent(agent_name="InsightScribeOrchestrator")
    print(agent)

    if agent.is_active():
        # Note: llm_config is not a direct attribute of Agent anymore.
        # It's used to configure agent.llm.
        print(f"Agent {agent.name} is ready to use with model {agent.llm.model}")

async def test_agent_with_llm():
    agent = await AgentInitializer.init_agent(agent_name="InsightScribeOrchestrator")

    response = await agent.llm.chat([
        {"role": "user", "content": "Get all the cube metadata.Using the provided tools, list all the cube metadata available in the system."}
    ])

    print("Agent Response:", response)

if __name__ == "__main__":
    asyncio.run(test_agent_with_llm())
