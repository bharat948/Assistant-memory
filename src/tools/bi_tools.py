import random
from pydantic import BaseModel, Field

from src.tools.base import BaseTool, ToolResult

# --- 1. Definition for the 'get_cube_metadata' Tool ---

class GetCubeMetadataArgs(BaseModel):
    """Defines the input arguments for the GetCubeMetadataTool."""
    cube_id: str = Field(..., description="The unique identifier of the BI cube to inspect.")

class GetCubeMetadataTool(BaseTool):
    """A tool to retrieve the schema (dimensions and measures) of a BI cube."""
    name = "get_cube_metadata"
    description = "Returns the available dimensions and measures for a BI cube. Use this to understand the data structure before building a query."
    args_schema = GetCubeMetadataArgs
    
    async def run(self, cube_id: str) -> ToolResult:
        """Simulates an API call to fetch cube metadata."""
        print(f"--- TOOL EXECUTING: {self.name} ---")
        print(f"    Params: cube_id='{cube_id}'")
        
        # In a real system, this would be an async httpx call to your Java API
        mock_data = {
            "cube_id": cube_id,
            "dimensions": ["ProviderNPI", "ClaimStatus", "ServiceDate", "PayerType"],
            "measures": ["ClaimCount", "AmountPaid", "DenialRate"]
        }
        
        return ToolResult(
            data=mock_data,
            summary=f"Successfully retrieved metadata for cube '{cube_id}'. Found 4 dimensions and 3 measures."
        )


# --- 2. Definition for the 'execute_bi_query' Tool ---

class ExecuteBIQueryArgs(BaseModel):
    """Defines the input arguments for the ExecuteBIQueryTool."""
    cube_id: str = Field(..., description="The ID of the cube to query.")
    query_string: str = Field(..., description="A complete and valid MDX or SQL query to execute against the cube.")

class ExecuteBIQueryTool(BaseTool):
    """A tool to run a query against the BI backend and get data."""
    name = "execute_bi_query"
    description = "Executes a BI query (e.g., MDX) against a specified cube and returns the analytical results."
    args_schema = ExecuteBIQueryArgs

    async def run(self, cube_id: str, query_string: str) -> ToolResult:
        """Simulates executing a query and returning data."""
        print(f"--- TOOL EXECUTING: {self.name} ---")
        print(f"    Params: cube_id='{cube_id}', query='{query_string[:50]}...'")

        if "error" in query_string.lower():
            raise ValueError("Simulated query syntax error. Please check your MDX.")
        
        mock_data = [
            {"Provider": "Provider A", "DeniedClaims": random.randint(100, 200)},
            {"Provider": "Provider B", "DeniedClaims": random.randint(50, 150)},
            {"Provider": "Provider C", "DeniedClaims": random.randint(20, 100)},
        ]
        
        return ToolResult(
            data=mock_data,
            summary=f"Query executed against cube '{cube_id}', returning {len(mock_data)} rows of data."
        )
