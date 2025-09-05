import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, model_validator
import yaml

class ToolConfig(BaseModel):
   id: str
   name: str
   description: str
   type: str
   endpoint: Optional[str] = None
   method: Optional[str] = "GET"
   auth_env: Optional[str] = None
   input_schema: Optional[Dict[str, Any]] = None
   local_handler: Optional[str] = None
   
   @model_validator(mode='after')
   def check_type_specific_fields(self) -> 'ToolConfig':
       if self.type == "http" and not self.endpoint:
           raise ValueError("Tools of type 'http' must have an 'endpoint' defined.")
       if self.type == "local" and not self.local_handler:
           raise ValueError("Tools of type 'local' must have a 'local_handler' defined.")
       return self

class AppConfig(BaseModel):
   tools: List[ToolConfig]

def load_config(path: str) -> AppConfig:
   """Loads and validates the tools configuration from a YAML file."""
   with open(path, 'r') as f:
       raw_config = yaml.safe_load(f)
   return AppConfig(**raw_config)
