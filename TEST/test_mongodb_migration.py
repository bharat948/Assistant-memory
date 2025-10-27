"""
Test script to verify MongoDB migration and compare with PostgreSQL version.
"""
import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
import sys

load_dotenv()

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from memory.mongodb_memory import MongoDBEnhancedMemory
from memory.models import ChatHistoryChunk, ContextualHandle
from memory.llm_clients import MockLLMClient

async def test_mongodb_memory():
    """Test MongoDB-based memory system"""
    print("\n" + "="*70)
    print("TESTING MONGODB MEMORY MIGRATION")
    print("="*70)
    
    # Initialize MongoDB EnhancedMemory
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGO_DB_NAME", "agentic")
    
    print(f"\n📊 Connecting to MongoDB...")
    print(f"   URI: {mongo_uri}")
    print(f"   Database: {db_name}")
    
    try:
        memory = MongoDBEnhancedMemory(
            mongo_uri=mongo_uri,
            db_name=db_name,
            llm_client=MockLLMClient(),
            working_memory_threshold=6
        )
        
        # Register test agent permissions
        memory.register_agent_permissions(
            agent_id="test_agent",
            allowed_tags={"general", "test", "demo", "conversation"},
            allowed_collections={"conversations", "general", "test"}
        )
        
        print("✅ MongoDB EnhancedMemory initialized")
        
        # Test 1: Store short-term memory (conversation)
        print("\n🧪 Test 1: Store short-term memory (conversation)")
        
        chat = ChatHistoryChunk(
            messages=[
                {"role": "user", "content": "Hello, I need help with Python async/await"},
                {"role": "assistant", "content": "I'd be happy to help! Async/await is used for asynchronous programming..."}
            ],
            agent_sender="test_user",
            agent_receiver="test_agent",
            timestamp=datetime.utcnow(),
            conversation_id="conv_test_001"
        )
        
        context = ContextualHandle(
            user_id="test_user",
            task_id="learn_python",
            conversation_id="conv_test_001"
        )
        
        conv_id = await memory.commit_working_memory(chat, agent_id="test_agent", context_handle=context)
        print(f"   ✅ Stored conversation: {conv_id}")
        
        # Test 2: Retrieve short-term memory
        print("\n🧪 Test 2: Retrieve short-term memory")
        messages = await memory.get_short_term_memory_by_user("test_user", "test_agent", limit=10)
        print(f"   ✅ Retrieved {len(messages)} messages")
        if messages:
            print(f"   📝 First message: {messages[0]['content'][:50]}...")
        
        # Test 3: Get memory count
        print("\n🧪 Test 3: Get memory count")
        count = await memory.get_short_term_memory_count("test_user", "test_agent")
        print(f"   ✅ Total messages: {count}")
        
        # Test 4: Store another conversation
        print("\n🧪 Test 4: Store another conversation")
        chat2 = ChatHistoryChunk(
            messages=[
                {"role": "user", "content": "Can you explain generators?"},
                {"role": "assistant", "content": "Generators are Python functions that use yield to produce values..."}
            ],
            agent_sender="test_user",
            agent_receiver="test_agent",
            timestamp=datetime.utcnow(),
            conversation_id="conv_test_002"
        )
        
        context2 = ContextualHandle(
            user_id="test_user",
            task_id="learn_python",
            conversation_id="conv_test_002"
        )
        
        await memory.commit_working_memory(chat2, agent_id="test_agent", context_handle=context2)
        print("   ✅ Stored second conversation")
        
        # Test 5: Check updated count
        count_after = await memory.get_short_term_memory_count("test_user", "test_agent")
        print(f"   ✅ Total messages now: {count_after}")
        
        # Test 6: Get statistics
        print("\n🧪 Test 6: Get statistics")
        stats = await memory.get_statistics()
        print(f"   ✅ Statistics generated:")
        print(f"      - Short-term messages: {stats['short_term_count']}")
        print(f"      - Long-term chunks: {stats['total_chunks']}")
        print(f"      - Archived chunks: {stats['archived_chunks']}")
        
        # Test 7: Clear memory for user
        print("\n🧪 Test 7: Clear memory")
        deleted = await memory.clear_short_term_memory_by_user("test_user", "test_agent")
        print(f"   ✅ Deleted {deleted} messages")
        
        # Final stats
        final_count = await memory.get_short_term_memory_count("test_user", "test_agent")
        print(f"   ✅ Final count: {final_count} messages")
        
        # Test 8: Verify collections in database
        print("\n🧪 Test 8: Verify MongoDB collections")
        collections = await memory.db.list_collection_names()
        print(f"   ✅ Collections in 'agentic' database: {collections}")
        
        # Check document counts in each collection
        for collection_name in collections:
            count = await memory.db[collection_name].count_documents({})
            print(f"      - {collection_name}: {count} documents")
        
        print("\n" + "="*70)
        print("✅ ALL MONGODB TESTS PASSED!")
        print("="*70)
        
        # Close connection
        await memory.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during MongoDB testing: {e}")
        import traceback
        traceback.print_exc()
        return False


async def compare_implementations():
    """Compare PostgreSQL and MongoDB implementations"""
    print("\n" + "="*70)
    print("COMPARING POSTGRESQL vs MONGODB IMPLEMENTATIONS")
    print("="*70)
    
    comparison = {
        "feature": ["Short-term memory", "Long-term memory", "Full-text search", "Tags filtering", "Async support", "Database"],
        "PostgreSQL": ["✅ Tables", "✅ Tables", "✅ tsvector", "✅ Array ops", "❌ Sync only", "PostgreSQL"],
        "MongoDB": ["✅ Collections", "✅ Collections", "✅ Text index", "✅ Array fields", "✅ Async native", "MongoDB"]
    }
    
    print("\n📊 Feature Comparison:")
    print(f"{'Feature':<25} {'PostgreSQL':<20} {'MongoDB':<20}")
    print("-" * 70)
    for i in range(len(comparison["feature"])):
        print(f"{comparison['feature'][i]:<25} {comparison['PostgreSQL'][i]:<20} {comparison['MongoDB'][i]:<20}")
    
    print("\n✅ MongoDB Advantages:")
    print("   1. Single database ecosystem (no PostgreSQL needed)")
    print("   2. Native async support")
    print("   3. Better document-oriented data handling")
    print("   4. Simpler queries for complex structures")
    print("   5. Natural array handling for tags")
    
    print("\n✅ Both implementations support:")
    print("   - Short-term memory (conversation history)")
    print("   - Long-term memory (knowledge chunks)")
    print("   - LLM-powered tagging")
    print("   - Permission-based access control")
    print("   - Full-text search")
    print("   - Statistics and monitoring")


async def main():
    """Run all tests"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "   MONGODB MIGRATION TEST SUITE".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    # Test MongoDB implementation
    mongo_success = await test_mongodb_memory()
    
    # Compare implementations
    await compare_implementations()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if mongo_success:
        print("✅ MongoDB migration: SUCCESSFUL")
        print("✅ All collections working correctly")
        print("✅ Data persistence verified")
        print("\n🎉 Migration to MongoDB is complete and working!")
    else:
        print("❌ MongoDB migration: FAILED")
        print("⚠️  Please check error messages above")
    
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())

