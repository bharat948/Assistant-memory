import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from tavily import TavilyClient
from tools.tools.base import BaseTool, ToolResult

load_dotenv() # Load environment variables from .env file

class WebSearchArgs(BaseModel):
    query: str = Field(..., description="The search query string.")
    search_depth: str = Field("basic", description="The depth of the search. 'basic' for quick searches, 'advanced' for more comprehensive results.", pattern="^(basic|advanced)$")
    max_results: int = Field(5, description="The maximum number of results to return.")
    time_range: Optional[str] = Field(None, description="Filter results by time range (e.g., 'day', 'week', 'month', 'year').")
    include_raw_content: Optional[str] = Field(None, description="Include raw content of the search results. 'text' for text content, 'html' for HTML content.", pattern="^(text|html)$")
    chunks_per_source: Optional[int] = Field(None, description="Number of chunks to return per source when include_raw_content is enabled.")
    country: Optional[str] = Field(None, description="Filter results by country (e.g., 'us', 'gb', 'in').")
    include_domains: Optional[List[str]] = Field(None, description="A list of domains to specifically include in the search.")
    exclude_domains: Optional[List[str]] = Field(None, description="A list of domains to specifically exclude from the search.")

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Performs a web search using Tavily API to get up-to-date information."
    args_schema = WebSearchArgs

    async def run(self, **kwargs) -> ToolResult:
        print(f"--- TOOL EXECUTING: {self.name} ---")
        print(f"    Params: {kwargs}")

        tavily_api_key = os.getenv("TAVILY_API_KEY")
        if not tavily_api_key:
            raise ValueError("TAVILY_API_KEY not found in environment variables.")

        client = TavilyClient(tavily_api_key)
        
        response = client.search(**kwargs)
        
        return ToolResult(
            data=response,
            summary=f"Web search completed for query: '{kwargs.get('query')}' with {len(response.get('results', []))} results."
        )
