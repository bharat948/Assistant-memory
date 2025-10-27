# Module Renaming - Quick Reference Guide

## Visual Comparison

### Current Structure (Inconsistent)
```
Modules/
├── agent_core/              ← Mixed naming
│   ├── agent.py
│   └── agent_init.py
├── memory_module/            ← "module" suffix
├── python_tool_module/       ← Long, redundant
├── mcp_server_module/        ← "module" suffix
├── agent_service/            ← Nested app/ structure
│   └── app/
│       ├── api/
│       └── core/
├── mongo_service/            ← Mixed naming
│   └── AppRepo/
│       ├── apprepo.py
│       └── service.py
└── myenv/
```

### Proposed Structure (Consistent)
```
Modules/
├── core/                   ← Clean, clear
│   ├── __init__.py
│   ├── agent.py
│   ├── agent_init.py
│   └── llm.py
├── memory/                  ← No redundant suffix
│   ├── __init__.py
│   ├── enhanced_memory.py
│   └── models.py
├── tools/                   ← Short, direct
│   ├── __init__.py
│   ├── base.py
│   └── services/
├── storage/                 ← Better organization
│   ├── __init__.py
│   └── agent_repo/
├── mcp/                     ← Concise
│   └── servers/
├── api/                     ← Flat structure
│   ├── __init__.py
│   ├── endpoints/
│   ├── models/
│   └── services/
└── tests/                   ← All tests together
```

## Import Statement Changes

### Pattern 1: Agent Core
```python
# OLD
from agent_core import Agent, AgentInitializer
from agent_core.agent import Agent
from agent_core.agent_init import AgentInitializer

# NEW
from core import Agent, AgentInitializer
from core.agent import Agent
from core.agent_init import AgentInitializer
```

### Pattern 2: Memory Module
```python
# OLD
from memory_module import EnhancedMemory, GroqLLMClient
from memory_module.enhanced_memory import EnhancedMemory
from memory_module.models import MemoryChunk

# NEW
from memory import EnhancedMemory, GroqLLMClient
from memory.enhanced_memory import EnhancedMemory
from memory.models import MemoryChunk
```

### Pattern 3: Python Tools
```python
# OLD
from python_tool_module.tools.base import BaseTool
from python_tool_module.services.tool_loader import tool_loader
from python_tool_module.tools.registry import TOOL_REGISTRY

# NEW
from tools.base import BaseTool
from tools.services.tool_loader import tool_loader
from tools.registry import TOOL_REGISTRY
```

### Pattern 4: MongoDB Service
```python
# OLD
from mongo_service.AppRepo.service import AppRepoService
from mongo_service.AppRepo.apprepo import AppRepoDAO
from mongo_service.AppRepo.models import AgentConfig
from mongo_service.config import mongo_db

# NEW
from storage.agent_repo.service import AppRepoService
from storage.agent_repo.apprepo import AppRepoDAO
from storage.agent_repo.models import AgentConfig
from storage.config import mongo_db
```

### Pattern 5: Agent Service
```python
# OLD
from agent_service.app.api.models.agent import RegisterAgentRequest
from agent_service.app.core.agent_service import AgentService
from agent_service.app.core.agent_cache import AgentCacheManager

# NEW
from api.models.agent import RegisterAgentRequest
from api.services.agent_service import AgentService
from api.services.agent_cache import AgentCacheManager
```

### Pattern 6: MCP Server
```python
# OLD
from mcp_server_module import BaseMCPServer, MCPServerResult
from mcp_server_module.services.mcp_loader import mcp_loader
from mcp_server_module.servers import ExampleMCPServer

# NEW
from mcp import BaseMCPServer, MCPServerResult
from mcp.services.mcp_loader import mcp_loader
from mcp.servers import ExampleMCPServer
```

## Complete Mapping Table

| Current Import | New Import |
|----------------|------------|
| `agent_core` | `core` |
| `memory_module` | `memory` |
| `python_tool_module` | `tools` |
| `mongo_service` | `storage` |
| `agent_service` | `api` |
| `mcp_server_module` | `mcp` |
| `agent_service.app.api` | `api` |
| `agent_service.app.core` | `api.services` |
| `mongo_service.AppRepo` | `storage.agent_repo` |
| `python_tool_module.tools` | `tools` |
| `python_tool_module.services` | `tools.services` |
| `mcp_server_module.servers` | `mcp.servers` |
| `mcp_server_module.services` | `mcp.services` |

## File-by-File Changes

### core/agent.py
```python
# BEFORE
from python_tool_module.tools.base import BaseTool
from python_tool_module.services.tool_loader import tool_loader
from memory_module import EnhancedMemory, ContextualHandle, ChatHistoryChunk

# AFTER
from tools.base import BaseTool
from tools.services.tool_loader import tool_loader
from memory import EnhancedMemory, ContextualHandle, ChatHistoryChunk
```

### core/agent_init.py
```python
# BEFORE
from mongo_service.AppRepo.apprepo import AppRepoDAO
from mongo_service.AppRepo.service import AppRepoService
from agent_core.agent import Agent
from mongo_service.config import get_database
from memory_module import EnhancedMemory, GroqLLMClient, MockLLMClient

# AFTER
from storage.agent_repo.apprepo import AppRepoDAO
from storage.agent_repo.service import AppRepoService
from core.agent import Agent
from storage.config import get_database
from memory import EnhancedMemory, GroqLLMClient, MockLLMClient
```

### api/services/agent_service.py
```python
# BEFORE
from mongo_service.AppRepo.service import AppRepoService
from mongo_service.AppRepo.apprepo import AppRepoDAO
from agent_service.app.api.models.agent import RegisterAgentRequest
from agent_core.agent_init import AgentInitializer
from agent_core.agent import Agent
from agent_service.app.core.agent_cache import AgentCacheManager

# AFTER
from storage.agent_repo.service import AppRepoService
from storage.agent_repo.apprepo import AppRepoDAO
from api.models.agent import RegisterAgentRequest
from core.agent_init import AgentInitializer
from core.agent import Agent
from api.services.agent_cache import AgentCacheManager
```

### api/main.py
```python
# BEFORE
from agent_service.app.api.endpoints import agent
from mongo_service.config import mongo_db

# AFTER
from api.endpoints import agent
from storage.config import mongo_db
```

### api/endpoints/agent.py
```python
# BEFORE
from agent_service.app.core.agent_service import AgentService

# AFTER
from api.services.agent_service import AgentService
```

## Testing After Rename

```bash
# Test imports
python -c "from core import Agent; print('✓ core works')"
python -c "from memory import EnhancedMemory; print('✓ memory works')"
python -c "from tools import BaseTool; print('✓ tools works')"
python -c "from storage import AppRepoService; print('✓ storage works')"
python -c "from api import AgentService; print('✓ api works')"
python -c "from mcp import BaseMCPServer; print('✓ mcp works')"
```

## Directory Renaming Commands

```bash
# On Unix/Mac/Git Bash
git mv agent_core core
git mv memory_module memory
git mv python_tool_module tools
git mv mongo_service storage
git mv agent_service api
git mv mcp_server_module mcp

# Rename subdirectories
git mv storage/AppRepo storage/agent_repo
git mv api/app/api api/api
git mv api/app/core api/services
```

## Verification Checklist

After renaming, verify:

- [ ] All imports updated
- [ ] All tests passing
- [ ] API documentation updated
- [ ] README updated
- [ ] Requirements.txt updated
- [ ] Configuration files updated
- [ ] Environment variables documented
- [ ] Deployment scripts updated

## Rollback Plan

If issues arise:

```bash
# Revert rename
git revert HEAD
# Or manually
git mv core agent_core
git mv memory memory_module
# ... etc
```

