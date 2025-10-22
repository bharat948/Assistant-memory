# Backend Agent Service

This backend registers, initializes, and invokes AI agents backed by MongoDB and LangChain. Frontend (`client/`) is out of scope here.

## Execution flow

1. Start FastAPI with uvicorn:
```bash
uvicorn agent_service.app.main:app --reload --host 0.0.0.0 --port 8000
```
2. App startup (`agent_service/app/main.py`):
- CORS for Angular dev origins
- Connects to Mongo via `mongo_service.config.mongo_db.connect()`
- Includes agent routes at `/agents`

3. Request path:
- Endpoint (`agent_service/app/api/endpoints/agent.py`) → `AgentService` (`agent_service/app/core/agent_service.py`)
- Persistence via `AppRepoService` → `AppRepoDAO` → Mongo collection

4. Agent init:
- `AgentInitializer` loads `AgentConfig` and constructs `agent_core.Agent`
- Tools are loaded from `python_tool_module.tools.registry` using `allowed_tool_ids`

5. Agent invoke:
- `Agent.invoke(prompt, history?)` calls LangChain `AgentExecutor` and returns final output with intermediate steps and tools used

## Run

1. Install deps: `pip install -r requirements.txt`
2. Set env vars (e.g. in `.env` at repo root):
- `MONGO_URI` (e.g. `mongodb://localhost:27017`)
- `MONGO_DB_NAME` (e.g. `mydatabase`)
- `OPENAI_API_KEY`
3. Start API:
```bash
uvicorn agent_service.app.main:app --reload --host 0.0.0.0 --port 8000
```

## API

- POST `/agents/register` → register agent config
- POST `/agents/{agent_id}/initialize` → materialize agent
- POST `/agents/{agent_id}/invoke` → invoke with `{ prompt, history? }`
- GET `/agents/` → list agents

## Backend layout

- `agent_service/app/main.py`: app, CORS, lifecycle, router include
- `agent_service/app/api/endpoints/agent.py`: agent REST endpoints
- `agent_service/app/core/agent_service.py`: orchestration and DB calls
- `mongo_service/config.py`: async Mongo client and `get_database`
- `mongo_service/AppRepo/*`: models, DAO, service
- `agent_core/agent_init.py`: loads config and builds `Agent`
- `agent_core/agent.py`: LangChain wiring and invocation
- `python_tool_module/tools/registry.py`: available tools

## Sanitation notes

- Deduped imports in endpoints
- Tool loading wired from `allowed_tool_ids`
- Unified DB access via `mongo_service.config.get_database`
- Invoke response matches API model
