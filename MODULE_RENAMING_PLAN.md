# Module Renaming Plan - Consistent Naming Convention

## Current Structure (Inconsistent)

```
Modules/
├── agent_core/              ← underscore
├── memory_module/            ← "module" suffix
├── python_tool_module/       ← "module" suffix
├── mcp_server_module/        ← "module" suffix
├── agent_service/            ← underscore + "service"
├── mongo_service/            ← underscore + "service"
└── myenv/                    ← virtual environment
```

## Proposed Structure (Consistent)

```
Modules/
├── core/                     ← Agent core functionality
│   ├── __init__.py
│   ├── agent.py
│   ├── agent_init.py
│   ├── llm.py
│   └── test.py
│
├── memory/                   ← Memory management
│   ├── __init__.py
│   ├── enhanced_memory.py
│   ├── models.py
│   ├── config.py
│   ├── permissions.py
│   ├── tagging.py
│   ├── llm_clients.py
│   ├── utils.py
│   └── logging_config.py
│
├── tools/                    ← Python tools
│   ├── __init__.py
│   ├── base.py
│   ├── bi_tools.py
│   ├── registry.py
│   ├── serpapi_search_tool.py
│   ├── web_search_tool.py
│   └── services/
│       ├── __init__.py
│       └── tool_loader.py
│
├── storage/                  ← Database & storage
│   ├── __init__.py
│   ├── config.py
│   └── agent_repo/
│       ├── __init__.py
│       ├── models.py
│       ├── apprepo.py
│       └── service.py
│
├── mcp/                      ← MCP server integration
│   ├── __init__.py
│   ├── base.py
│   ├── registry.py
│   ├── README.md
│   ├── servers/
│   │   ├── __init__.py
│   │   ├── example_mcp_server.py
│   │   └── filesystem_mcp_server.py
│   └── services/
│       ├── __init__.py
│       └── mcp_loader.py
│
├── api/                      ← FastAPI service
│   ├── __init__.py
│   ├── dependencies.py
│   ├── main.py
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── agent.py
│   │   └── mcp.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── agent.py
│   └── services/
│       ├── __init__.py
│       ├── agent_service.py
│       └── agent_cache.py
│
└── tests/                    ← All tests
    ├── __init__.py
    ├── test_agent.py
    ├── test_memory.py
    ├── test_tools.py
    └── test_integration.py
```

## Renaming Strategy

### Phase 1: Core Modules (Low Impact)

| Current Name | Proposed Name | Reason |
|-------------|---------------|--------|
| `agent_core/` | `core/` | Shorter, clearer purpose |
| `memory_module/` | `memory/` | Removes redundant "module" suffix |
| `python_tool_module/` | `tools/` | Shorter, "python" is redundant |

### Phase 2: Service Modules

| Current Name | Proposed Name | Reason |
|-------------|---------------|--------|
| `agent_service/` | `api/` or `api_service/` | More descriptive |
| `mongo_service/` | `storage/` or `database/` | Broader scope (supports MongoDB/PostgreSQL) |

### Phase 3: Specialized Modules

| Current Name | Proposed Name | Reason |
|-------------|---------------|--------|
| `mcp_server_module/` | `mcp/` | Shorter, consistent |

### Phase 4: Subdirectories

| Current Name | Proposed Name |
|-------------|---------------|
| `mongo_service/AppRepo/` | `storage/agent_repo/` |
| `python_tool_module/services/` | `tools/services/` |
| `mcp_server_module/services/` | `mcp/services/` |
| `mcp_server_module/servers/` | `mcp/servers/` |
| `agent_service/app/api/endpoints/` | `api/endpoints/` |
| `agent_service/app/api/models/` | `api/models/` |
| `agent_service/app/core/` | `api/services/` |

## Import Statement Changes

### Before (Current)

```python
from agent_core import Agent, AgentInitializer
from memory_module import EnhancedMemory, GroqLLMClient
from python_tool_module.tools import BaseTool
from mongo_service.AppRepo.service import AppRepoService
from agent_service.app.core.agent_service import AgentService
```

### After (Proposed)

```python
from core import Agent, AgentInitializer
from memory import EnhancedMemory, GroqLLMClient
from tools import BaseTool
from storage import AppRepoService
from api import AgentService
```

## Benefits

1. **Consistency**: All modules use snake_case, no redundant suffixes
2. **Clarity**: Clear, purposeful names without redundancy
3. **Simplicity**: Shorter import paths
4. **Scalability**: Better organization for future growth
5. **Professional**: Follows Python packaging best practices

## Implementation Steps

### Step 1: Rename Directories
```bash
# Rename directories
git mv agent_core core
git mv memory_module memory
git mv python_tool_module tools
git mv mongo_service storage
git mv agent_service api
git mv mcp_server_module mcp
```

### Step 2: Update Import Statements

**Files to update:**
- `core/agent.py`
- `core/agent_init.py`
- `api/main.py`
- `api/services/agent_service.py`
- `api/endpoints/agent.py`
- All test files
- `README.md`
- Documentation files

**Search and replace:**
```python
# Old imports
from agent_core import Agent
from memory_module import EnhancedMemory
from python_tool_module.tools import BaseTool
from mongo_service.AppRepo.service import AppRepoService

# New imports
from core import Agent
from memory import EnhancedMemory
from tools import BaseTool
from storage import AppRepoService
```

### Step 3: Update Internal Imports

Update relative imports in each module:
- `core/__init__.py`
- `memory/__init__.py`
- `tools/__init__.py`
- `storage/__init__.py`
- `api/__init__.py`
- `mcp/__init__.py`

### Step 4: Update Configuration Files

Update references in:
- `requirements.txt`
- `setup.py` (if exists)
- `config.py` files
- `.env` files
- Documentation

### Step 5: Update Documentation

Update:
- `README.md`
- `rules/architecture.md`
- All markdown files
- API documentation

## Migration Script

```python
# migrate_imports.py
import os
import re

def update_imports(file_path):
    """Update import statements in a Python file"""
    
    replacements = [
        (r'from agent_core import', 'from core import'),
        (r'from memory_module import', 'from memory import'),
        (r'from python_tool_module', 'from tools'),
        (r'from mongo_service', 'from storage'),
        (r'from agent_service', 'from api'),
        (r'from mcp_server_module', 'from mcp'),
        (r'agent_core\.', 'core.'),
        (r'memory_module\.', 'memory.'),
        (r'python_tool_module\.', 'tools.'),
        (r'mongo_service\.', 'storage.'),
        (r'agent_service\.', 'api.'),
        (r'mcp_server_module\.', 'mcp.'),
    ]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old, new in replacements:
        content = re.sub(old, new, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

# Walk through all Python files
for root, dirs, files in os.walk('.'):
    if 'myenv' in root or '__pycache__' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            update_imports(os.path.join(root, file))
```

## Directory Structure Comparison

### Current (Inconsistent)
```
Modules/
├── agent_core/
├── memory_module/
├── python_tool_module/
├── mcp_server_module/
├── agent_service/
└── mongo_service/
```

### Proposed (Consistent)
```
Modules/
├── core/
├── memory/
├── tools/
├── storage/
├── mcp/
└── api/
```

## Rollout Plan

### Week 1: Planning & Preparation
- [ ] Review all files that need updating
- [ ] Create backup
- [ ] Update this migration plan

### Week 2: Core Renaming
- [ ] Rename directories
- [ ] Update __init__.py files
- [ ] Run migration script

### Week 3: Testing & Verification
- [ ] Run all tests
- [ ] Verify imports work
- [ ] Update documentation

### Week 4: Final Cleanup
- [ ] Remove old references
- [ ] Update documentation
- [ ] Deploy to production

## Backward Compatibility (Optional)

If needed, you can add compatibility shims:

```python
# core/__init__.py
# For backward compatibility
import sys
import os

# Keep old module name in sys.modules
sys.modules['agent_core'] = sys.modules[__name__]
```

## Impact Analysis

### Files to Update: ~50-70 files
- Python files: ~30-40
- Documentation: ~5-10
- Configuration: ~3-5
- Tests: ~5-10

### Estimated Time: 2-3 days
- Renaming: 2 hours
- Script updates: 4 hours
- Testing: 6 hours
- Documentation: 4 hours

## Recommendation

✅ **Proceed with renaming for long-term maintainability**

The inconsistencies will cause confusion and make the codebase harder to navigate. The proposed structure is:
- More intuitive
- Follows Python conventions
- Easier to understand for new developers
- Professional and scalable

