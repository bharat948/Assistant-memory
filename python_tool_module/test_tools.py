import asyncio
from python_tool_module.services.tool_loader import tool_loader

async def main():
    print("--- Testing Tool Module ---")

    allowed_tool_ids = ["get_cube_metadata", "execute_bi_query"]
    instantiated_tools = tool_loader.get_allowed_tools(allowed_tool_ids)
    print(f"\nInstantiated Tools: {list(instantiated_tools.keys())}")

    llm_signatures = tool_loader.get_llm_tool_signatures(instantiated_tools)
    print("\nLLM Tool Signatures:")
    for signature in llm_signatures:
        print(f"- {signature['function']['name']}: {signature['function']['description']}")
        print(f"  Parameters: {signature['function']['parameters']}")

    print("\n--- Executing GetCubeMetadataTool ---")
    get_cube_metadata_tool = instantiated_tools.get("get_cube_metadata")
    if get_cube_metadata_tool:
        try:
            result = await get_cube_metadata_tool.run(cube_id="sales_data_cube")
            print(f"Tool Result Summary: {result.summary}")
            print(f"Tool Result Data: {result.data}")
        except Exception as e:
            print(f"Error executing tool: {e}")

    print("\n--- Executing ExecuteBIQueryTool (successful) ---")
    execute_bi_query_tool = instantiated_tools.get("execute_bi_query")
    if execute_bi_query_tool:
        try:
            result = await execute_bi_query_tool.run(cube_id="sales_data_cube", query_string="SELECT ...")
            print(f"Tool Result Summary: {result.summary}")
            print(f"Tool Result Data: {result.data}")
        except Exception as e:
            print(f"Error executing tool: {e}")

if __name__ == "__main__":
    asyncio.run(main())
