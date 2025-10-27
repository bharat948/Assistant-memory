from agent_data.db import get_database
from fastapi import Depends

async def get_db(db = Depends(get_database)):
    return db
