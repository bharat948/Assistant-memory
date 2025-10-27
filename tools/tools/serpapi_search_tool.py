import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import serpapi
from tools.tools.base import BaseTool, ToolResult

load_dotenv() # Load environment variables from .env file

class SerpAPISearchArgs(BaseModel):
    q: str = Field(..., description="The search query string.")
    engine: str = Field("google", description="The search engine to use (e.g., 'google', 'bing', 'youtube').")
    location: Optional[str] = Field(None, description="Specifies the location for the search (e.g., 'Austin, Texas').")
    hl: Optional[str] = Field(None, description="Host language (e.g., 'en').")
    gl: Optional[str] = Field(None, description="Host geolocation (e.g., 'us').")
    num: Optional[int] = Field(None, description="Number of results to return.")
    # Add other common SerpAPI parameters as needed

class SerpAPISearchTool(BaseTool):
    name = "serpapi_search"
    description = "Performs a web search using SerpAPI to get up-to-date information from various search engines."
    args_schema = SerpAPISearchArgs

    async def run(self, **kwargs) -> ToolResult:
        print(f"--- TOOL EXECUTING: {self.name} ---")
        print(f"    Params: {kwargs}")

        serpapi_api_key = os.getenv("SERPAPI_API_KEY")
        if not serpapi_api_key:
            raise ValueError("SERPAPI_API_KEY not found in environment variables.")

        client = serpapi.Client(api_key=serpapi_api_key)
        
        response = client.search(**kwargs)
        
        return ToolResult(
            data=response,
            summary=f"SerpAPI search completed for query: '{kwargs.get('q')}' using engine '{kwargs.get('engine')}'."
        )
