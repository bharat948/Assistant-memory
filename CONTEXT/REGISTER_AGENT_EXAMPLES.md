# Agent Registration Examples

## Quick Reference

### Available Tools
- `get_cube_metadata` - Get BI cube structure
- `execute_bi_query` - Execute MDX/SQL queries  
- `web_search` - Web search using Tavily
- `serpapi_search` - Advanced search using SerpAPI

---

## Example 1: BI Data Analyst Agent

```json
{
  "agent_id": "bi_analyst_001",
  "name": "BI Data Analyst",
  "agent_type": "analytical_agent",
  "description": "Specialized in Business Intelligence data analysis, cube exploration, and MDX query execution.",
  "llm_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.3,
    "max_tokens": 4000
  },
  "system_prompt_template": "You are a professional BI Data Analyst with expertise in data analysis, cube exploration, and MDX querying. Your role is to help users analyze BI cubes, execute MDX queries, generate reports, and provide data-driven recommendations.",
  "allowed_tool_ids": ["get_cube_metadata", "execute_bi_query"],
  "allowed_roles": ["analyst", "admin"],
  "dependencies": {
    "allowed_tool_names": ["GetCubeMetadataTool", "ExecuteBIQueryTool"],
    "allowed_sub_agent_names": []
  },
  "created_by": "api"
}
```

**Use Case:** Analyze business data, explore BI cubes, execute MDX queries

---

## Example 2: Research Assistant Agent

```json
{
  "agent_id": "research_assistant_001",
  "name": "Research Assistant",
  "agent_type": "research_agent",
  "description": "A research-focused AI assistant for web information gathering and analysis.",
  "llm_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.4,
    "max_tokens": 3000
  },
  "system_prompt_template": "You are a research assistant specializing in web information gathering. Use web search tools to find, verify, and analyze information from multiple sources. Always cite your sources and provide well-researched responses.",
  "allowed_tool_ids": ["web_search", "serpapi_search"],
  "allowed_roles": ["researcher", "analyst"],
  "dependencies": {
    "allowed_tool_names": ["WebSearchTool", "SerpAPISearchTool"],
    "allowed_sub_agent_names": []
  },
  "created_by": "api"
}
```

**Use Case:** Market research, competitive analysis, fact-finding

---

## Example 3: General Assistant (Simple)

```json
{
  "agent_id": "general_assistant_001",
  "name": "General Assistant",
  "agent_type": "general_agent",
  "description": "A versatile AI assistant for general questions and web research.",
  "llm_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "system_prompt_template": "You are a helpful AI assistant. Help users with questions, provide information, and use web search when needed for current information.",
  "allowed_tool_ids": ["web_search"],
  "allowed_roles": ["user", "admin"],
  "dependencies": {
    "allowed_tool_names": ["WebSearchTool"],
    "allowed_sub_agent_names": []
  },
  "created_by": "api"
}
```

**Use Case:** General questions, web search, information lookup

---

## Example 4: Full-Stack Agent (All Tools)

```json
{
  "agent_id": "full_stack_001",
  "name": "Full-Stack Assistant",
  "agent_type": "super_agent",
  "description": "Comprehensive AI assistant with BI analytics, web search, and research capabilities.",
  "llm_config": {
    "model": "gpt-4o",
    "temperature": 0.5,
    "max_tokens": 4000
  },
  "system_prompt_template": "You are a full-stack AI assistant with comprehensive capabilities: BI data analysis, web research, and general assistance. Choose the right tool for each task and provide accurate, well-reasoned responses.",
  "allowed_tool_ids": ["get_cube_metadata", "execute_bi_query", "web_search", "serpapi_search"],
  "allowed_roles": ["admin", "power_user"],
  "dependencies": {
    "allowed_tool_names": ["GetCubeMetadataTool", "ExecuteBIQueryTool", "WebSearchTool", "SerpAPISearchTool"],
    "allowed_sub_agent_names": []
  },
  "created_by": "api"
}
```

**Use Case:** All-in-one assistant with full tool access

---

## Testing the Registration

### Using cURL

```bash
# Register BI Analyst
curl -X POST http://localhost:8000/agents/register \
  -H "Content-Type: application/json" \
  -d @example_agent_payloads.json

# Or register inline
curl -X POST http://localhost:8000/agents/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "bi_analyst_001",
    "name": "BI Data Analyst",
    "agent_type": "analytical_agent",
    "description": "Specialized in BI data analysis",
    "llm_config": {
      "model": "gpt-4o-mini",
      "temperature": 0.3,
      "max_tokens": 4000
    },
    "system_prompt_template": "You are a BI Data Analyst...",
    "allowed_tool_ids": ["get_cube_metadata", "execute_bi_query"],
    "allowed_roles": ["analyst", "admin"],
    "dependencies": {
      "allowed_tool_names": ["GetCubeMetadataTool", "ExecuteBIQueryTool"],
      "allowed_sub_agent_names": []
    },
    "created_by": "api"
  }'
```

### Using Python

```python
import requests

payload = {
    "agent_id": "bi_analyst_001",
    "name": "BI Data Analyst",
    "agent_type": "analytical_agent",
    "description": "Specialized in BI data analysis",
    "llm_config": {
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "max_tokens": 4000
    },
    "system_prompt_template": "You are a BI Data Analyst...",
    "allowed_tool_ids": ["get_cube_metadata", "execute_bi_query"],
    "allowed_roles": ["analyst", "admin"],
    "dependencies": {
        "allowed_tool_names": ["GetCubeMetadataTool", "ExecuteBIQueryTool"],
        "allowed_sub_agent_names": []
    },
    "created_by": "api"
}

response = requests.post(
    "http://localhost:8000/agents/register",
    json=payload
)
print(response.json())
```

---

## Workflow After Registration

1. **Register Agent** → Returns agent configuration
2. **Initialize Agent** → `POST /agents/{agent_id}/initialize`
3. **Invoke Agent** → `POST /agents/{agent_id}/invoke`

