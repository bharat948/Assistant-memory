import os
from dotenv import load_dotenv
from langchain_openai import OpenAI
from langchain.agents import initialize_agent, AgentType
from aether_agent.agent.tool_loader import load_tools_from_yaml

def main():
   # Load environment variables from .env file in parent directory
   dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
   load_dotenv(dotenv_path=dotenv_path)

   if not os.getenv("OPENAI_API_KEY"):
       print("Error: OPENAI_API_KEY environment variable not set.")
       return

   tools_yaml_path = os.path.join(os.path.dirname(__file__), 'examples', 'tools.yaml')
   print(f"Loading tools from: {tools_yaml_path}")
   
   try:
       tools = load_tools_from_yaml(tools_yaml_path)
   except Exception as e:
       print(f"Failed to load tools: {e}")
       return
   
   print("--- Tools Loaded ---")
   for tool in tools:
       print(f"- {tool.name}: {tool.description}")
   print("--------------------")
   
   llm = OpenAI(temperature=0)
   agent = initialize_agent(
       tools,
       llm,
       agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
       verbose=True,
       handle_parsing_errors=True
   )
   
   print("\nAgent is ready. Ask a question or type 'exit' to quit.")
   try:
       while True:
           prompt = input("User > ")
           if prompt.strip().lower() in ("exit", "quit"):
               break
           if prompt:
               try:
                   response = agent.run(prompt)
                   print(f"Agent > {response}")
               except Exception as e:
                   print(f"An error occurred while running the agent: {e}")
   except KeyboardInterrupt:
       print("\nExiting.")

if __name__ == "__main__":
   main()
