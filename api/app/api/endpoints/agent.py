from fastapi import APIRouter, Depends, HTTPException
from typing import List
from agent_service.app.core.agent_service import AgentService
from agent_service.app.api.models.agent import (
    RegisterAgentRequest,
    AgentResponse,
    InitializeAgentResponse,
    InvokeAgentRequest,
    InvokeAgentResponse,
    ListAgentsResponse,
)
from agent_service.dependencies import get_db

router = APIRouter()

@router.post("/register", response_model=AgentResponse)
async def register_agent(
    agent_data: RegisterAgentRequest,
    db = Depends(get_db)
):
    """
    Registers a new agent in the system.
    """
    try:
        agent_service = AgentService(db)
        created_agent = await agent_service.register_agent(agent_data)
        return AgentResponse(
            agent_id=created_agent.agent_id,
            name=created_agent.name,
            agent_type=created_agent.agent_type,
            status=created_agent.status,
            description=created_agent.description
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@router.post("/{agent_id}/initialize", response_model=InitializeAgentResponse)
async def initialize_agent(
    agent_id: str,
    db = Depends(get_db)
):
    """
    Initializes an agent by its ID, making it ready for execution.
    """
    try:
        agent_service = AgentService(db)
        agent = await agent_service.initialize_agent(agent_id)
        return InitializeAgentResponse(
            agent_id=agent.agent_id,
            name=agent.name,
            status=agent.status,
            message=f"Agent '{agent.name}' initialized successfully."
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
@router.post("/{agent_id}/invoke", response_model=InvokeAgentResponse)
async def invoke_agent(
    agent_id: str,
    request: InvokeAgentRequest,
    db = Depends(get_db)
):
    """
    Invokes an agent with a user prompt and gets a response.
    The conversation history can be included for context.
    """
    try:
        agent_service = AgentService(db)
        response_content = await agent_service.invoke_agent(
            agent_id=agent_id, 
            prompt=request.prompt, 
            user_id=request.user_id,
            conversation_id=request.conversation_id
        )
        return InvokeAgentResponse(**response_content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@router.get("/", response_model=ListAgentsResponse)
async def list_all_agents(
    db = Depends(get_db)
):
    """
    Retrieves a list of all registered agents.
    """
    try:
        agent_service = AgentService(db)
        agents = await agent_service.list_all_agents()
        print(agents)
        return ListAgentsResponse(agents=[AgentResponse(**agent.dict()) for agent in agents])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
