import os
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, List
from aether_tools_service.app.tools_registry import registry, register_from_config
from aether_tools_service.app.validators import validate_input
from aether_tools_service.app.audit import record
from aether_tools_service.app.rate_limit import allow
from aether_tools_service.app.security import check_api_key

app = FastAPI(
   title="Aether Tools Microservice",
   description="A central microservice to expose and manage tools for AI agents.",
)

# Use relative path for default config
default_config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'aether_agent', 'agent', 'examples', 'tools.yaml')
CONFIG_PATH = os.getenv("TOOLS_CONFIG", default_config_path)
register_from_config(CONFIG_PATH)

class ToolInvokeRequest(BaseModel):
   payload: Dict[str, Any] = Field(default_factory=dict)

class ToolInvokeResponse(BaseModel):
   status: str = "ok"
   result: Dict[str, Any]

@app.get("/tools", response_model=List[Dict])
def list_available_tools(api_key: str = Depends(check_api_key)):
   """Lists all registered tools with their metadata."""
   return registry.list_tools()

@app.post("/tools/{tool_id}/invoke", response_model=ToolInvokeResponse)
def invoke_tool(
   tool_id: str,
   body: ToolInvokeRequest,
   api_key: str = Depends(check_api_key)
):
   """Invokes a registered tool by its ID."""
   tool_record = registry.get(tool_id)
   if not tool_record:
       raise HTTPException(status_code=404, detail=f"Tool with id '{tool_id}' not found.")
   
   cfg = tool_record.config
   if not allow(cfg.id):
       raise HTTPException(status_code=429, detail="Rate limit exceeded.")
   
   is_valid, error_message = validate_input(cfg.input_schema, body.payload)
   if not is_valid:
       record(cfg.id, api_key, body.payload, {"error": error_message}, status="validation_error")
       raise HTTPException(status_code=400, detail=f"Input validation failed: {error_message}")
   
   try:
       result = tool_record.handler(body.payload)
       record(cfg.id, api_key, body.payload, result, status="ok")
       return {"status": "ok", "result": result}
   except Exception as e:
       record(cfg.id, api_key, body.payload, {"error": str(e)}, status="error")
       raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")
