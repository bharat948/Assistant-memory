"""
Test agent initialization and invocation after PostgreSQL removal
"""
import requests
import asyncio

BASE_URL = "http://localhost:8000"

def test_agent():
    """Test existing agent"""
    
    agent_id = "test_workflow_agent"
    
    print("="*70)
    print("TESTING AGENT INVOKE")
    print("="*70)
    
    # Step 1: Initialize
    print(f"\n🚀 Initializing agent: {agent_id}")
    response = requests.post(f"{BASE_URL}/agents/{agent_id}/initialize")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Step 2: Invoke
    print(f"\n💬 Invoking agent: {agent_id}")
    invoke_payload = {
        "prompt": "What is Python?",
        "user_id": "test_user",
        "conversation_id": "test_conv_002"
    }
    
    response = requests.post(
        f"{BASE_URL}/agents/{agent_id}/invoke",
        json=invoke_payload
    )
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Agent responded!")
        print(f"   Response preview: {result.get('response', '')[:200]}...")
    else:
        print(f"   ❌ Error: {response.text}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_agent()

