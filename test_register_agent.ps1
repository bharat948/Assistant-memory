# Test agent registration
$headers = @{
    "Content-Type" = "application/json"
}

$body = @{
    agent_id = "bi_analyst_test"
    name = "BI Data Analyst"
    agent_type = "analytical_agent"
    description = "Specialized in BI data analysis and reporting"
    llm_config = @{
        model = "gpt-4o-mini"
        temperature = 0.3
        max_tokens = 4000
    }
    system_prompt_template = "You are a professional BI Data Analyst with expertise in data analysis and MDX querying."
    allowed_tool_ids = @("get_cube_metadata", "execute_bi_query")
    allowed_roles = @("analyst", "admin")
    dependencies = @{
        allowed_tool_names = @("GetCubeMetadataTool", "ExecuteBIQueryTool")
        allowed_sub_agent_names = @()
    }
    created_by = "api"
} | ConvertTo-Json -Depth 10

Write-Host "Registering agent..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "http://localhost:8000/agents/register" -Method Post -Headers $headers -Body $body

Write-Host "`nResponse:" -ForegroundColor Green
$response | ConvertTo-Json -Depth 10

