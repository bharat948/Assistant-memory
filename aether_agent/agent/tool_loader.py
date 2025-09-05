import json
import os
import requests
from typing import List
from langchain.tools import Tool
from aether_tools_service.app.config import load_config, ToolConfig

def _create_http_tool_adapter(config: ToolConfig) -> callable:
   """Creates a function that calls the microservice /invoke endpoint."""
   def tool_func(input_str: str) -> str:
       try:
           payload = json.loads(input_str)
       except json.JSONDecodeError:
           return f"Error: Invalid input. Please provide a valid JSON string. Your input was: {input_str}"
       
       api_key = os.getenv("AETHER_API_KEY")
       if not api_key:
           return "Error: AETHER_API_KEY environment variable not set."
           
       headers = {"x-api-key": api_key, "Content-Type": "application/json"}
       url = f"http://localhost:8000/tools/{config.id}/invoke"
       
       try:
           response = requests.post(url, headers=headers, json={"payload": payload}, timeout=15)
           response.raise_for_status()
           return json.dumps(response.json())
       except requests.exceptions.HTTPError as e:
           return f"Error: API call failed with status {e.response.status_code}. Response: {e.response.text}"
       except requests.exceptions.RequestException as e:
           return f"Error: Could not connect to the tool service: {e}"
   return tool_func

def load_tools_from_yaml(path: str) -> List[Tool]:
   """Loads tool definitions from YAML and wraps them as LangChain Tools."""
   cfg = load_config(path)
   tools = []
   for c in cfg.tools:
       agent_desc = (
           f"{c.description}. "
           f"The input to this tool must be a JSON string. "
           f"The JSON schema for the input is: {json.dumps(c.input_schema)}"
       )
       tool_adapter = _create_http_tool_adapter(c)
       tools.append(
           Tool.from_function(
               func=tool_adapter,
               name=c.name,
               description=agent_desc,
           )
       )
   return tools
