
from agent_init import AgentInitializer
import asyncio
import json

async def test_agent_initializer():
    """Test basic agent initialization"""
    agent = await AgentInitializer.init_agent(agent_name="InsightScribeOrchestrator")
    print(agent)
    
    if agent.is_active():
        print(f"Agent {agent.name} is ready to use")

async def test_agent_with_single_query():
    """Test agent with a single query"""
    # Initialize agent first
    agent = await AgentInitializer.init_agent(agent_id="some-unique-id")
    
    # Then invoke it
    result = await agent.invoke(
        user_query="Get all the cube metadata. Using the provided tools, Use the tool"
    )
    
    print("\n=== Agent Response ===")
    print(f"Agent: {result.get('agent_name')}")
    print(f"Response: {result.get('response')}")
    if result.get('tools_used'):
        print(f"Tools Used: {result.get('tools_used')}")

async def interactive_agent_loop():
    """Interactive loop for testing the agent with multiple queries"""
    print("\n=== Interactive Agent Testing ===")
    print("Commands:")
    print("  'exit' - Exit the program")
    print("  'list' - List all available agents")
    print("  'init <agent_id or agent_name>' - Initialize a specific agent")
    print("  Any other input will be sent as a query to the current agent\n")
    
    current_agent = None
    current_agent_id = None
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if user_input.lower() == 'exit':
                print("Exiting...")
                break
            
            elif user_input.lower() == 'list':
                # List all agents
                from mongo_service.config import get_database
                from mongo_service.AppRepo.apprepo import AppRepoDAO
                from mongo_service.AppRepo.service import AppRepoService
                
                db = await get_database()
                dao = AppRepoDAO(db)
                service = AppRepoService(dao)
                agents = await service.list_agents()
                
                print("\n=== Available Agents ===")
                for agent in agents:
                    print(f"  - {agent.name} (ID: {agent.agent_id}) - Status: {agent.status}")
                    print(f"    Description: {agent.description}")
                continue
            
            elif user_input.lower().startswith('init '):
                # Initialize a specific agent
                agent_identifier = user_input[5:].strip()
                
                try:
                    # Try to initialize by ID first, then by name
                    if agent_identifier.replace('-', '').replace('_', '').isalnum():
                        # Looks like an ID
                        current_agent = await AgentInitializer.init_agent(agent_id=agent_identifier)
                    else:
                        # Treat as name
                        current_agent = await AgentInitializer.init_agent(agent_name=agent_identifier)
                    
                    current_agent_id = current_agent.agent_id
                    print(f"\n✓ Successfully initialized agent: {current_agent.name}")
                    print(f"  Type: {current_agent.agent_type}")
                    print(f"  Status: {current_agent.status}")
                    print(f"  Available tools: {[tool.name for tool in current_agent.langchain_tools]}")
                    
                except Exception as e:
                    print(f"\n✗ Failed to initialize agent: {str(e)}")
                    current_agent = None
                    current_agent_id = None
                continue
            
            else:
                # Send query to current agent
                if not current_agent:
                    print("No agent initialized. Use 'init <agent_id or agent_name>' first.")
                    continue
                
                if not current_agent.is_active():
                    print(f"Agent {current_agent.name} is not active. Status: {current_agent.status}")
                    continue
                
                print(f"\nProcessing query with {current_agent.name}...")
                
                # Invoke the agent
                result = await current_agent.invoke(
                    user_query=user_input,
                    user_id="test_user",
                    conversation_id=f"test_conv_{current_agent_id}"
                )
                
                # Display results
                print("\n=== Agent Response ===")
                if result.get('error'):
                    print(f"✗ Error: {result.get('error')}")
                else:
                    print(f"Response: {result.get('response')}")
                    
                    if result.get('tools_used'):
                        print(f"\nTools Used: {', '.join(result.get('tools_used', []))}")
                    
                    # Optionally show full conversation for debugging
                    show_full = input("\nShow full conversation? (y/n): ").strip().lower()
                    if show_full == 'y':
                        print("\n=== Full Conversation ===")
                        for msg in result.get('full_conversation', []):
                            print(f"{msg['role']}: {msg['content'][:200]}...")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted. Use 'exit' to quit properly.")
        except Exception as e:
            print(f"\n✗ Unexpected error: {str(e)}")

async def register_test_agent():
    """Register a test agent for demonstration"""
    from mongo_service.config import get_database
    from mongo_service.AppRepo.apprepo import AppRepoDAO
    from mongo_service.AppRepo.service import AppRepoService
    
    db = await get_database()
    dao = AppRepoDAO(db)
    service = AppRepoService(dao)
    
    agent_data = {
        "agent_id": "test-langgraph-agent",
        "name": "TestLangGraphAgent",
        "agent_type": "react_agent",
        "description": "Test agent for LangGraph ReAct implementation",
        "created_by": "system_test",
        "llm_config": {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "system_prompt_template": """You are a helpful AI assistant with access to various tools.
Your goal is to help users by using the available tools when necessary.
Always be clear about what tools you're using and why.
If you encounter any errors, explain them clearly to the user.""",
        "allowed_tool_ids": ["get_cube_metadata", "execute_bi_query"],
        "allowed_roles": ["admin", "user"],
        "dependencies": {
            "allowed_tool_names": [],
            "allowed_sub_agent_names": []
        }
    }
    
    try:
        agent_id = await service.register_agent(agent_data=agent_data)
        print(f"✓ Test agent registered successfully with ID: {agent_id}")
    except ValueError as e:
        if "already exists" in str(e):
            print("Test agent already exists")
        else:
            raise

async def main():
    print("=== LangGraph Agent Testing Suite ===\n")
    print("1. Register test agent")
    print("2. Test single query")
    print("3. Interactive testing loop")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        await register_test_agent()
    elif choice == "2":
        await test_agent_with_single_query()
    elif choice == "3":
        await interactive_agent_loop()
    elif choice == "4":
        print("Exiting...")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    asyncio.run(main())