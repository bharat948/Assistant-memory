"""
Test script to demonstrate MCP server integration with agents.
"""
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.agent_init import AgentInitializer
from mcp import mcp_loader

async def test_mcp_servers():
    """Test MCP server functionality."""
    print("=== Testing MCP Server Integration ===\n")
    
    # Test 1: Initialize MCP servers directly
    print("1. Testing MCP server initialization...")
    try:
        # Get example servers
        servers = mcp_loader.get_allowed_servers(["example_mcp_server", "filesystem_mcp_server"])
        print(f"   Initialized servers: {list(servers.keys())}")
        
        # Connect to servers
        connection_results = await mcp_loader.connect_all_servers(servers)
        print(f"   Connection results: {connection_results}")
        
        # Test server tools
        for server_id, server in servers.items():
            print(f"\n   Testing server: {server_id}")
            
            # List tools
            tools = await server.list_tools()
            print(f"   Tools available: {[tool['name'] for tool in tools]}")
            
            # List resources
            resources = await server.list_resources()
            print(f"   Resources available: {[resource['name'] for resource in resources]}")
            
            # Test tool calls
            if server_id == "example_mcp_server":
                # Test calculate tool
                result = await server.call_tool("calculate", {"expression": "2 + 3 * 4"})
                print(f"   Calculate result: {result.summary}")
                
                # Test echo tool
                result = await server.call_tool("echo", {"message": "Hello MCP!"})
                print(f"   Echo result: {result.summary}")
            
            elif server_id == "filesystem_mcp_server":
                # Test file operations
                result = await server.call_tool("write_file", {
                    "file_path": "test_mcp.txt",
                    "content": "Hello from MCP filesystem server!"
                })
                print(f"   Write file result: {result.summary}")
                
                result = await server.call_tool("read_file", {"file_path": "test_mcp.txt"})
                print(f"   Read file result: {result.summary}")
        
        # Disconnect from servers
        await mcp_loader.disconnect_all_servers()
        print("\n   Disconnected from all servers")
        
    except Exception as e:
        print(f"   Error testing MCP servers: {e}")
    
    print("\n=== MCP Server Test Complete ===")

async def test_agent_with_mcp():
    """Test agent initialization with MCP servers."""
    print("\n=== Testing Agent with MCP Servers ===\n")
    
    try:
        # Note: This would require a valid agent_id in your database
        # For demonstration, we'll show how it would work
        print("To test agent with MCP servers, you would:")
        print("1. Create an agent configuration with allowed_mcp_server_ids")
        print("2. Initialize the agent using AgentInitializer.init_agent(agent_id)")
        print("3. The agent would automatically connect to the specified MCP servers")
        print("4. You could then call agent methods like:")
        print("   - agent.list_mcp_servers()")
        print("   - agent.get_mcp_server_tools(server_id)")
        print("   - agent.call_mcp_server_tool(server_id, tool_name, arguments)")
        
    except Exception as e:
        print(f"Error in agent MCP test: {e}")

if __name__ == "__main__":
    asyncio.run(test_mcp_servers())
    asyncio.run(test_agent_with_mcp())
