import requests
import os
import logging
import importlib
from typing import Callable, Dict, List, Optional
from aether_tools_service.app.config import ToolConfig, load_config

logger = logging.getLogger(__name__)

class ToolRecord:
   def __init__(self, config: ToolConfig, handler: Callable):
       self.config = config
       self.handler = handler

class ToolsRegistry:
   def __init__(self):
       self._tools: Dict[str, ToolRecord] = {}
   
   def register(self, config: ToolConfig, handler: Callable):
       if config.id in self._tools:
           logger.warning("Overwriting tool registration for: %s", config.id)
       self._tools[config.id] = ToolRecord(config, handler)
       logger.info("Registered tool: %s", config.id)
   
   def get(self, tool_id: str) -> Optional[ToolRecord]:
       return self._tools.get(tool_id)
   
   def list_tools(self) -> List[Dict]:
       return [
           {
               "id": t.config.id,
               "name": t.config.name,
               "description": t.config.description,
               "input_schema": t.config.input_schema,
           }
           for t in self._tools.values()
       ]

registry = ToolsRegistry()

def make_http_handler(config: ToolConfig) -> Callable:
   def handler(payload: dict) -> dict:
       headers = {}
       if config.auth_env and (token := os.getenv(config.auth_env)):
           headers["Authorization"] = f"Bearer {token}"
       method = (config.method or "GET").upper()
       try:
           if method == "GET":
               url = config.endpoint.format(**payload)
               response = requests.get(url, headers=headers, timeout=10)
           else:
               response = requests.request(
                   method, config.endpoint, json=payload, headers=headers, timeout=10
               )
           response.raise_for_status()
           return response.json()
       except requests.exceptions.RequestException as e:
           logger.error("HTTP Tool '%s' failed: %s", config.id, e)
           raise ConnectionError(f"API call failed: {e}") from e
   return handler

def register_from_config(cfg_path: str):
   """Loads config and registers all defined tools."""
   cfg = load_config(cfg_path)
   for t in cfg.tools:
       handler = None
       if t.type == "http":
           handler = make_http_handler(t)
       elif t.type == "local":
           try:
               modname, fnname = t.local_handler.rsplit(".", 1)
               # Adjust path for service context
               full_modname = f"aether_tools_service.app.{modname}"
               module = importlib.import_module(full_modname)
               handler = getattr(module, fnname)
           except (ImportError, AttributeError) as e:
               logger.error("Could not import local handler '%s': %s", t.local_handler, e)
               continue
       if handler:
           registry.register(t, handler)
