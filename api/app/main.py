from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from agent_service.app.api.endpoints import agent
from mongo_service.config import mongo_db

app = FastAPI(title="Agent Service")

# Configure CORS
origins = [
    "http://localhost:4200",  # Angular frontend default port
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_db_client():
    await mongo_db.connect()

@app.on_event("shutdown")
async def shutdown_db_client():
    await mongo_db.close()

app.include_router(agent.router, prefix="/agents", tags=["agents"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Agent Service"}
