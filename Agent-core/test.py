from agent_init import AgentInitializer

async def test_agent_initializer():
    # Initialize by name
    agent = await AgentInitializer.init_agent(agent_name="InsightScribeOrchestrator")
    print(agent)

    if agent.is_active():
        print(f"Agent {agent.name} is ready to use with model {agent.llm_config['model']}")

async def test_agent_with_llm():
    agent = await AgentInitializer.init_agent(agent_name="InsightScribeOrchestrator")

    # Use LLM
    response = await agent.llm.chat([
        {"role": "system", "content": agent.system_prompt_template},
        {"role": "user", "content": "Get all the cube metadata.Using the provided tools, list all the cube metadata available in the system."}
    ])

    print("Agent Response:", response)
import asyncio

if __name__ == "__main__":
    asyncio.run(test_agent_with_llm())