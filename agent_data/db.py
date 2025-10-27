from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from .config import MONGO_URI, MONGO_DB_NAME

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

    async def connect(self):
        if self.client is None:
            try:
                self.client = AsyncIOMotorClient(MONGO_URI)
                self.db = self.client[MONGO_DB_NAME]
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

    async def get_db(self):
        if self.db is None:
            await self.connect()
        return self.db

mongo_db = MongoDB()

async def get_database():
    return await mongo_db.get_db()
