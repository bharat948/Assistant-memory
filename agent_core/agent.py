from typing import List, Dict, Any, Optional
from datetime import datetime
from agent_core.llm import LLM
from python_tool_module.services.tool_loader import tool_loader

class Agent:
    def __init__(
        self,
        agent_id: str,
        name: str,
        agent_type: str,
        description: str,
        version: int,
        status: str,
        created_by: str,
        llm_config: Dict[str, Any],
        system_prompt_template: str,
        allowed_roles: List[str],
        dependencies: Dict[str, List[str]],
        allowed_tool_ids: List[str],
        output_schema: Optional[Dict[str, Any]] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.version = version
        self.status = status
        self.created_by = created_by
        self.system_prompt_template = system_prompt_template
        self.allowed_roles = allowed_roles
        self.dependencies = dependencies
        self.output_schema = output_schema
        
        instantiated_tools = tool_loader.get_allowed_tools(allowed_tool_ids)
        llm_signatures = tool_loader.get_llm_tool_signatures(instantiated_tools)
        
        self.llm = LLM(
            model=llm_config.get("model", "gpt-4o-mini"),
            temperature=llm_config.get("temperature", 0.7),
            max_tokens=llm_config.get("max_tokens", 4000),
            tools=llm_signatures,
            system_instruction=self.system_prompt_template
        )
        self.created_at = datetime.utcnow()
        self.tools = instantiated_tools
        self.sub_agents = []

    def __repr__(self):
        return f"<Agent name={self.name}, type={self.agent_type}, status={self.status}>"

    def is_active(self):
        return self.status == "active"
