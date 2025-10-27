# Core Module

The core module contains the fundamental agent classes and initialization logic. It provides the Agent class that wraps LangChain agents with memory integration and tool support.

## 📁 Module Structure

```
core/
├── __init__.py           # Module exports
├── agent.py             # Agent class with LangChain integration
├── agent_init.py        # Agent initialization logic
├── llm.py               # LLM client wrapper
└── test.py              # Test utilities
```

## 🎯 Key Components

### 1. Agent Class (`agent.py`)

The core `Agent` class that implements agent execution with LangChain integration.

#### Initialization

```python
from core.agent import Agent

agent = Agent(
    agent_id="my_agent",
    name="My Agent",
    agent_type="react_agent",
    description="Agent description",
    version=1,
    status="active",
    created_by="user",
    llm_config={
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 4000
    },
    system_prompt_template="You are a helpful assistant...",
    allowed_roles=["user", "admin"],
    dependencies={"allowed_tool_names": ["WebSearchTool"]},
    allowed_tool_ids=["web_search"],
    output_schema=None,
    memory=memory_instance  # Optional EnhancedMemory
)
```

#### Key Attributes

- `agent_id`: Unique identifier
- `name`: Display name
- `agent_type`: Type of agent (e.g., "react_agent")
- `status`: Current status ("active", "draft", etc.)
- `system_prompt_template`: System prompt for the LLM
- `allowed_roles`: Roles that can use this agent
- `dependencies`: Tool and sub-agent dependencies
- `memory`: EnhancedMemory instance (optional)
- `tools`: Dictionary of loaded tools
- `langchain_tools`: Tools converted for LangChain
- `llm`: LangChain OpenAI LLM instance
- `agent_executor`: LangChain AgentExecutor

#### Methods

**`async invoke(user_query, config, user_id, conversation_id)`**
- Main agent invocation method
- Retrieves conversation history from memory
- Executes agent with tools
- Stores conversation to memory
- Returns agent response

```python
response = await agent.invoke(
    user_query="What is the weather?",
    user_id="user_123",
    conversation_id="conv_456"
)
```

#### Agent Execution Flow

```
1. User query received
2. Retrieve conversation history from memory (if memory exists)
3. Convert history to LangChain message objects
4. Execute agent with tools (or fallback to simple chat)
5. Store conversation to memory
6. Return response
```

### 2. Agent Initialization (`agent_init.py`)

Handles agent initialization from configuration.

#### Class: `AgentInitializer`

```python
from core.agent_init import AgentInitializer

agent = await AgentInitializer.init_agent(agent_id="my_agent")
```

#### `init_agent(agent_id)` Process

1. **Load Agent Configuration**
   - Fetches agent config from MongoDB
   - Validates required fields
   
2. **Initialize LLM Client**
   - Creates LangChain ChatOpenAI client
   - Configures model parameters from config
   
3. **Initialize Memory**
   - Creates EnhancedMemory instance with MongoDB
   - Registers agent permissions
   - Sets up allowed tags and collections
   
4. **Load Tools**
   - Loads tools based on `allowed_tool_ids`
   - Converts to LangChain-compatible format
   
5. **Create Agent Instance**
   - Instantiates Agent with all components
   - Returns initialized agent

#### Configuration Requirements

```python
{
    "agent_id": "required",
    "name": "required",
    "agent_type": "required",
    "llm_config": {
        "model": "required",
        "temperature": "optional (default 0.7)",
        "max_tokens": "optional (default 4000)"
    },
    "system_prompt_template": "optional",
    "allowed_tool_ids": ["required"],
    "allowed_roles": ["required"]
}
```

### 3. LLM Wrapper (`llm.py`)

Wrapper around OpenAI's AsyncOpenAI client.

#### Class: `LLM`

```python
from core.llm import LLM

llm = LLM(
    model="gpt-4o-mini",
    temperature=0.7,
    max_tokens=4000,
    tools=[...],  # Optional
    system_instruction="You are a helpful assistant"  # Optional
)

response = await llm.chat([
    {"role": "user", "content": "Hello"}
])
```

#### Features
- Async OpenAI client wrapper
- Tool support (structured tools)
- System instruction support
- Automatic content None handling
- Configurable temperature and max_tokens

## 🔧 Agent Types

### ReAct Agent
Uses ReAct (Reasoning + Acting) pattern with LangChain's AgentExecutor.

**Characteristics:**
- Can reason about actions
- Uses tools dynamically
- Returns detailed reasoning traces
- Best for: Complex multi-step tasks

### Simple Chat Agent
Fallback when no tools are available.

**Characteristics:**
- Direct LLM interaction
- No tool usage
- Simpler responses
- Best for: General Q&A

## 🧠 Memory Integration

The agent seamlessly integrates with the EnhancedMemory module:

```python
# Agent automatically:
# 1. Retrieves conversation history before execution
recent_messages = await self.memory.get_short_term_memory_by_user(
    user_id=user_id,
    agent_id=self.agent_id,
    limit=10
)

# 2. Uses history in agent execution
agent_executor.ainvoke({
    "input": user_query,
    "chat_history": chat_history
})

# 3. Stores conversation after execution
await memory.commit_working_memory(
    chat=chat_chunk,
    agent_id=agent_id,
    context_handle=context_handle
)
```

## 🛠️ Tool Integration

### Loading Tools

Tools are loaded based on `allowed_tool_ids`:

```python
# Agent configuration
{
    "allowed_tool_ids": ["web_search", "get_cube_metadata"]
}

# Tools are automatically:
# 1. Loaded via tool_loader
instantiated_tools = tool_loader.get_allowed_tools(allowed_tool_ids)

# 2. Converted to LangChain format
self.langchain_tools = self._convert_to_langchain_tools(instantiated_tools)

# 3. Used in agent execution
agent_executor = AgentExecutor(
    agent=self._agent,
    tools=self.langchain_tools,
    verbose=True
)
```

### Converting Tools to LangChain Format

```python
def _convert_to_langchain_tools(self, tools: Dict[str, BaseTool]):
    """Convert custom tools to LangChain tools"""
    langchain_tools = []
    for tool_id, tool in tools.items():
        langchain_tool = StructuredTool(
            name=tool.name,
            description=tool.description,
            func=None,
            coroutine=make_tool_func(tool),
            args_schema=tool.args_schema
        )
        langchain_tools.append(langchain_tool)
    return langchain_tools
```

## 🔄 Error Handling

The Agent class includes comprehensive error handling:

1. **Memory Errors**: Gracefully handles memory retrieval/storage failures
2. **Tool Errors**: Falls back to simple chat if tools fail
3. **LLM Errors**: Returns error message in response
4. **AgentExecutor Errors**: Parsing errors are handled gracefully

```python
try:
    if self.agent_executor is None:
        # Fallback to simple LLM chat
        ai_message = await self.llm.ainvoke(messages)
    else:
        # Use agent with tools
        result = await self.agent_executor.ainvoke(...)
except Exception as e:
    return {
        "error": str(e),
        "response": f"An error occurred: {str(e)}"
    }
```

## 🧪 Testing

The module includes test utilities:

```bash
# Run core tests
python core/test.py
```

Test file structure:
```python
# test.py
async def test_agent_initialization():
    agent = await AgentInitializer.init_agent("test_agent")
    assert agent is not None

async def test_agent_invoke():
    agent = await AgentInitializer.init_agent("test_agent")
    response = await agent.invoke("Hello")
    assert "response" in response
```

## 📊 Agent Lifecycle

```
1. Registration
   - Agent config stored in MongoDB
   - Returns agent_id

2. Initialization
   - Load config from MongoDB
   - Initialize LLM + Tools + Memory
   - Cache agent instance

3. Invocation (multiple times)
   - Retrieve from cache
   - Get conversation history
   - Execute with tools
   - Store to memory

4. (Optional) Retire
   - Remove from cache
   - Archive in database
```

## 🔗 Integration with Other Modules

### API Module
- Receives HTTP requests
- Calls AgentService
- Returns responses

### Storage Module
- Fetches agent configurations
- AppRepoService manages MongoDB operations

### Memory Module
- EnhancedMemory provides conversation history
- Stores agent interactions

### Tools Module
- tool_loader loads tools dynamically
- Converts tools to LangChain format

## 🎯 Best Practices

1. **Always initialize agents before use**: Use AgentInitializer
2. **Handle memory gracefully**: Check if memory exists before operations
3. **Error handling**: Always wrap agent calls in try/except
4. **Tool validation**: Ensure tools are properly loaded before agent execution
5. **Memory context**: Always provide user_id and conversation_id for proper memory management

## 🔗 Related Documentation

- See `../api/README.md` for API layer usage
- See `../memory/README.md` for memory system
- See `../tools/README.md` for tool system
- See `../README.md` for overall architecture
