from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from mongo_service.AppRepo.models import LLMConfig, Dependencies

class RegisterAgentRequest(BaseModel):
    agent_id: str
    name: str
    agent_type: str
    description: Optional[str] = None
    llm_config: Optional[LLMConfig] = None
    system_prompt_template: Optional[str] = None
    allowed_tool_ids: List[str] = []
    dependencies: Optional[Dependencies] = None
    allowed_roles: List[str] = []
    created_by: Optional[str] = "api"

class AgentResponse(BaseModel):
    agent_id: str
    name: str
    agent_type: str
    status: str
    description: Optional[str] = None

    class Config:
        from_attributes = True # Allows creating model from ORM objects

class InitializeAgentResponse(BaseModel):
    agent_id: str
    name: str
    status: str
    message: str

class InvokeAgentResponse(BaseModel):
    agent_id: str
    agent_name: str
    response: str
    intermediate_steps: list = []
    tools_used: list = []
    
class InvokeAgentRequest(BaseModel):
    prompt: str
    user_id: Optional[str] = Field(
        default="default_user",
        description="User identifier for memory retrieval"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation ID for memory context"
    )

class ListAgentsResponse(BaseModel):
    agents: List[AgentResponse]
