import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None
    
    async def connect(self):
        from dotenv import load_dotenv
        load_dotenv()
        if self.client is None:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            
            # Enhanced connection options for MongoDB Atlas
            connection_options ={
    "retryWrites": True,
    "w": "majority",
    "connectTimeoutMS": 60000,
    "socketTimeoutMS": 60000,
}   
            try:
                self.client = AsyncIOMotorClient(mongo_uri, **connection_options)
                self.db = self.client.get_database(os.getenv("MONGO_DB_NAME", "mydatabase"))
                print("MongoDB client created successfully!")
            except Exception as e:
                print(f"Failed to create MongoDB client: {e}")
                raise

    async def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            print("MongoDB connection closed.")

    async def test_connection(self):
        if not self.client:
            print("No client available for connection test")
            return False
            
        try:
            # Test with a longer timeout
            await self.client.admin.command('ping', maxTimeMS=30000)
            print("MongoDB connection test successful!")
            return True
        except ConnectionFailure as e:
            print(f"MongoDB connection test failed: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during connection test: {e}")
            return False

mongo_db = MongoDB()

async def get_database():
    if mongo_db.db is None:
        await mongo_db.connect()
    return mongo_db.db