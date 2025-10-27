# app/core/agent.py
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from tools.tools.base import BaseTool
from langchain.agents import AgentExecutor
from tools.services.tool_loader import tool_loader
from langchain import hub
from memory import EnhancedMemory, ContextualHandle, ChatHistoryChunk

class Agent:
    def __init__(
        self,
        agent_id: str,
        name: str,
        agent_type: str,
        description: str,
        version: int,
        status: str,
        created_by: str,
        llm_config: Dict[str, Any],
        system_prompt_template: str,
        allowed_roles: List[str],
        dependencies: Dict[str, List[str]],
        allowed_tool_ids: List[str],
        output_schema: Optional[Dict[str, Any]] = None,
        memory: Optional[EnhancedMemory] = None,
    ):
        self.agent_id = agent_id
        self.name = name
        self.agent_type = agent_type
        self.description = description
        self.version = version
        self.status = status
        self.created_by = created_by
        self.system_prompt_template = system_prompt_template or "You are a helpful AI assistant with access to BI tools."
        self.allowed_roles = allowed_roles
        self.dependencies = dependencies
        self.output_schema = output_schema
        self.memory = memory
        
        # Instantiate and convert allowed tools
        print(f"[Agent:init] allowed_tool_ids={allowed_tool_ids}")
        instantiated_tools = tool_loader.get_allowed_tools(allowed_tool_ids)
        self.langchain_tools = self._convert_to_langchain_tools(instantiated_tools)
        print(f"[Agent:init] langchain_tools count={len(self.langchain_tools)} names={[t.name for t in self.langchain_tools]}")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        print("LLM initialized:", self.llm)
        
        # Create the prompt for ReAct agent
        print("About to create chat prompt...")
        try:
            # Option 1: Use a custom ReAct prompt template
            react_prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt_template + """

            You have access to the following tools:
            {tools}

            Use the following format:

            Question: the input question you must answer
            Thought: you should always think about what to do
            Action: the action to take, should be one of [{tool_names}]
            Action Input: the input to the action
            Observation: the result of the action
            ... (this Thought/Action/Action Input/Observation can repeat N times)
            Thought: I now know the final answer
            Final Answer: the final answer to the original input question"""),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
                ("human", "{input}")
            ])
            
            print("Custom ReAct prompt created successfully")
            
        except Exception as e:
            print(f"Error creating custom prompt, falling back to hub prompt: {e}")
            # Option 2: Use the standard ReAct prompt from hub (fallback)
            try:
                react_prompt = hub.pull("hwchase17/react")
                print("Hub ReAct prompt loaded successfully")
            except Exception as hub_error:
                print(f"Hub prompt also failed: {hub_error}")
                # Option 3: Simple fallback prompt
                react_prompt = ChatPromptTemplate.from_messages([
                    ("system", self.system_prompt_template),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad")
                ])
                print("Simple fallback prompt created")

        # Create the agent (functions if tools available, otherwise simple chat)
        try:
            if self.langchain_tools:
                from langchain.agents import create_openai_functions_agent
                print("[Agent:init] Creating functions agent with tools...")
                self._agent = create_openai_functions_agent(
                    llm=self.llm,
                    tools=self.langchain_tools,
                    prompt=ChatPromptTemplate.from_messages([
                        ("system", self.system_prompt_template),
                        MessagesPlaceholder(variable_name="chat_history", optional=True),
                        ("human", "{input}"),
                        MessagesPlaceholder(variable_name="agent_scratchpad")
                    ])
                )
                print("[Agent:init] Functions agent created")
                # Create the agent executor
                self.agent_executor = AgentExecutor(
                    agent=self._agent, 
                    tools=self.langchain_tools,
                    verbose=True,
                    handle_parsing_errors=True
                )
                print("[Agent:init] AgentExecutor created (functions mode)")
            else:
                print("[Agent:init][WARN] No tools available; will use simple chat on invoke")
                self._agent = None
                self.agent_executor = None
        except Exception as e:
            print(f"[Agent:init][ERROR] Error creating agent: {e} | tools_count={len(self.langchain_tools)} tool_names={[t.name for t in self.langchain_tools]}")
            raise
        
        self.created_at = datetime.utcnow()
        self.tools = instantiated_tools
        self.sub_agents = []
        print("Agent initialization complete")

    def _convert_to_langchain_tools(self, tools: Dict[str, BaseTool]):
        """Convert our custom tools to LangChain-compatible tools."""
        from langchain_core.tools import StructuredTool
        
        langchain_tools = []
        for tool_id, tool in tools.items():
            # Create a proper closure for each tool
            def make_tool_func(tool_instance):
                async def wrapper(**kwargs):
                    result = await tool_instance.run(**kwargs)
                    return f"{result.summary}\n\nData: {result.data}"
                return wrapper
            
            langchain_tool = StructuredTool(
                name=tool.name,
                description=tool.description,
                func=None,
                coroutine=make_tool_func(tool),
                args_schema=tool.args_schema
            )
            langchain_tools.append(langchain_tool)
        
        return langchain_tools

    async def invoke(self, user_query: str, config: Optional[Dict[str, Any]] = None, 
                    user_id: str = "default_user", conversation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Invoke the agent with a user query and memory integration.
        
        Args:
            user_query: The user's input query
            config: Optional configuration for the agent execution
            user_id: User identifier for memory retrieval
            conversation_id: Optional conversation ID for memory context
            
        Returns:
            Dict containing the agent's response and any tool outputs
        """
        try:
            # Create context handle for memory operations
            context_handle = ContextualHandle(
                user_id=user_id,
                conversation_id=conversation_id or f"conv_{self.agent_id}_{user_id}"
            )
            
            # Retrieve conversation history from memory if available
            conversation_history = []
            if self.memory:
                try:
                    # Check if memory is async (MongoDBEnhancedMemory)
                    if hasattr(self.memory, 'get_short_term_memory_by_user'):
                        if callable(self.memory.get_short_term_memory_by_user):
                            import inspect
                            if inspect.iscoroutinefunction(self.memory.get_short_term_memory_by_user):
                                # Async MongoDB
                                recent_messages = await self.memory.get_short_term_memory_by_user(
                                    user_id=user_id, 
                                    agent_id=self.agent_id, 
                                    limit=10
                                )
                            else:
                                # Sync PostgreSQL
                                recent_messages = self.memory.get_short_term_memory_by_user(
                                    user_id=user_id, 
                                    agent_id=self.agent_id, 
                                    limit=10
                                )
                            conversation_history = recent_messages or []
                            print(f"[Agent:invoke] Retrieved {len(conversation_history)} messages from memory")
                except Exception as e:
                    print(f"[Agent:invoke] Warning: Could not retrieve memory: {e}")
            
            # Convert conversation history to LangChain message objects
            chat_history = []
            if conversation_history:
                for msg in conversation_history:
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        if msg['role'] == 'user':
                            chat_history.append(HumanMessage(content=msg['content']))
                        elif msg['role'] == 'assistant':
                            chat_history.append(AIMessage(content=msg['content']))
            
            if self.agent_executor is None:
                print("[Agent:invoke][WARN] No AgentExecutor; returning simple LLM response")
                # Fallback to simple chat using ChatOpenAI directly
                # Build message list for LLM
                messages = chat_history + [HumanMessage(content=user_query)]
                ai_message = await self.llm.ainvoke(messages) if hasattr(self.llm, "ainvoke") else None
                response_content = ai_message.content if ai_message else ""
            else:
                print(f"[Agent:invoke] Invoking with tools_count={len(self.langchain_tools)}")
                result = await self.agent_executor.ainvoke({
                    "input": user_query,
                    "chat_history": chat_history
                }, config=config or {})
                
                # Some LC outputs may contain AIMessage objects; normalize to strings
                response_content = result.get("output", "No response generated")
                try:
                    if hasattr(response_content, "content"):
                        print("[Agent:invoke] Normalizing AIMessage to string")
                        response_content = response_content.content
                except Exception:
                    pass

            # Store conversation to memory
            if self.memory:
                try:
                    # Create chat chunk for memory storage
                    chat_chunk = ChatHistoryChunk(
                        messages=[
                            {"role": "user", "content": user_query},
                            {"role": "assistant", "content": response_content}
                        ],
                        agent_sender="user",
                        agent_receiver=self.agent_id,
                        timestamp=datetime.utcnow(),
                        conversation_id=context_handle.conversation_id
                    )
                    
                    # Commit to working memory (handle both sync and async)
                    import inspect
                    if hasattr(self.memory, 'commit_working_memory'):
                        if inspect.iscoroutinefunction(self.memory.commit_working_memory):
                            # Async MongoDB
                            await self.memory.commit_working_memory(
                                chat=chat_chunk,
                                agent_id=self.agent_id,
                                context_handle=context_handle
                            )
                        else:
                            # Sync PostgreSQL
                            self.memory.commit_working_memory(
                                chat=chat_chunk,
                                agent_id=self.agent_id,
                                context_handle=context_handle
                            )
                        print(f"[Agent:invoke] Stored conversation to memory")
                except Exception as e:
                    print(f"[Agent:invoke] Warning: Could not store to memory: {e}")

            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "response": response_content,
                "intermediate_steps": result.get("intermediate_steps", []) if 'result' in locals() else [],
                "tools_used": [step[0].tool for step in result.get("intermediate_steps", [])] if 'result' in locals() else []
            }
            
        except Exception as e:
            print(f"Error during agent invocation: {e}")
            return {
                "agent_id": self.agent_id,
                "agent_name": self.name,
                "error": str(e),
                "response": f"An error occurred while processing your request: {str(e)}"
            }

    def __repr__(self):
        return f"<Agent name={self.name}, type={self.agent_type}, status={self.status}>"

    def is_active(self):
        return self.status == "active"
