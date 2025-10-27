from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class LLMConfig(BaseModel):
    model: str
    temperature: float
    max_tokens: int

class Dependencies(BaseModel):
    allowed_tool_names: List[str]
    allowed_sub_agent_names: List[str]

class AgentConfig(BaseModel):
    _id: Optional[str] = None
    agent_id: str
    name: str
    agent_type: str
    description: Optional[str]
    version: int = 1
    status: str = "draft"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str]
    tags: List[str] = []
    llm_config: Optional[LLMConfig]
    system_prompt_template: Optional[str] = None
    allowed_roles: List[str] = []
    allowed_tool_ids:List[str] = []
    dependencies: Optional[Dependencies]
    output_schema: Optional[Dict[str, Any]] = None
