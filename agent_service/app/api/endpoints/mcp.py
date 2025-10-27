"""
MCP Server API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from ...core.agent_service import AgentService
from ...core.agent_cache import get_agent_service

router = APIRouter(prefix="/mcp", tags=["MCP Servers"])

@router.get("/servers/{agent_id}")
async def list_mcp_servers(agent_id: str, agent_service: AgentService = Depends(get_agent_service)):
    """List all MCP servers for an agent."""
    try:
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        servers_info = await agent.list_mcp_servers()
        return {
            "agent_id": agent_id,
            "mcp_servers": servers_info,
            "count": len(servers_info)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/servers/{agent_id}/{server_id}/info")
async def get_mcp_server_info(
    agent_id: str, 
    server_id: str, 
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get information about a specific MCP server."""
    try:
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        server_info = await agent.get_mcp_server_info(server_id)
        if "error" in server_info:
            raise HTTPException(status_code=404, detail=server_info["error"])
        
        return {
            "agent_id": agent_id,
            "server_id": server_id,
            "server_info": server_info
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/servers/{agent_id}/{server_id}/tools")
async def get_mcp_server_tools(
    agent_id: str, 
    server_id: str, 
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get tools from a specific MCP server."""
    try:
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        tools = await agent.get_mcp_server_tools(server_id)
        return {
            "agent_id": agent_id,
            "server_id": server_id,
            "tools": tools,
            "count": len(tools)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/servers/{agent_id}/{server_id}/resources")
async def get_mcp_server_resources(
    agent_id: str, 
    server_id: str, 
    agent_service: AgentService = Depends(get_agent_service)
):
    """Get resources from a specific MCP server."""
    try:
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        resources = await agent.get_mcp_server_resources(server_id)
        return {
            "agent_id": agent_id,
            "server_id": server_id,
            "resources": resources,
            "count": len(resources)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servers/{agent_id}/{server_id}/tools/{tool_name}/call")
async def call_mcp_server_tool(
    agent_id: str,
    server_id: str,
    tool_name: str,
    arguments: Dict[str, Any],
    agent_service: AgentService = Depends(get_agent_service)
):
    """Call a tool on a specific MCP server."""
    try:
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        result = await agent.call_mcp_server_tool(server_id, tool_name, arguments)
        return {
            "agent_id": agent_id,
            "server_id": server_id,
            "tool_name": tool_name,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servers/{agent_id}/{server_id}/resources/read")
async def read_mcp_server_resource(
    agent_id: str,
    server_id: str,
    resource_uri: str,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Read a resource from a specific MCP server."""
    try:
        agent = await agent_service.get_agent(agent_id)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        result = await agent.read_mcp_server_resource(server_id, resource_uri)
        return {
            "agent_id": agent_id,
            "server_id": server_id,
            "resource_uri": resource_uri,
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
