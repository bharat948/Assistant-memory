"""
Test the complete agent workflow: Register → Initialize → Invoke
"""
import asyncio
import requests
import json

BASE_URL = "http://localhost:8000"

def test_full_workflow():
    """Test complete agent lifecycle"""
    
    print("="*70)
    print("TESTING COMPLETE AGENT WORKFLOW")
    print("="*70)
    
    # Step 1: Register Agent
    print("\n📝 Step 1: Register Agent")
    
    payload = {
        "agent_id": "test_workflow_agent",
        "name": "Test Workflow Agent",
        "agent_type": "general_agent",
        "description": "Test agent for workflow validation",
        "llm_config": {
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "system_prompt_template": "You are a helpful test assistant.",
        "allowed_tool_ids": ["web_search"],
        "allowed_roles": ["user"],
        "dependencies": {
            "allowed_tool_names": ["WebSearchTool"],
            "allowed_sub_agent_names": []
        },
        "created_by": "test_user"
    }
    
    response = requests.post(f"{BASE_URL}/agents/register", json=payload)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        agent_data = response.json()
        print(f"   ✅ Agent registered: {agent_data.get('agent_id')}")
    else:
        print(f"   ❌ Error: {response.text}")
        return
    
    # Step 2: Initialize Agent
    print("\n🚀 Step 2: Initialize Agent")
    
    agent_id = payload["agent_id"]
    response = requests.post(f"{BASE_URL}/agents/{agent_id}/initialize")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Agent initialized successfully")
    else:
        print(f"   ⚠️  Response: {response.text}")
    
    # Step 3: Invoke Agent
    print("\n💬 Step 3: Invoke Agent")
    
    invoke_payload = {
        "prompt": "Hello! Can you explain what async/await is in Python?",
        "user_id": "test_user",
        "conversation_id": "test_conv_001"
    }
    
    response = requests.post(
        f"{BASE_URL}/agents/{agent_id}/invoke",
        json=invoke_payload
    )
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Agent responded!")
        print(f"   Response: {result.get('response', 'No response')[:200]}...")
    else:
        print(f"   ❌ Error: {response.text}")
    
    # Step 4: List all agents
    print("\n📋 Step 4: List All Agents")
    
    response = requests.get(f"{BASE_URL}/agents/")
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        agents = response.json()
        agent_count = len(agents.get('agents', []))
        print(f"   ✅ Found {agent_count} agents in system")
    else:
        print(f"   ❌ Error: {response.text}")
    
    print("\n" + "="*70)
    print("WORKFLOW TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_full_workflow()

