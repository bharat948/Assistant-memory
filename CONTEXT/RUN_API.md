# Running the API Service

## Quick Start

The FastAPI application is located in `api/main.py`

### Run Command (from project root)

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Run with virtual environment

```bash
# Activate virtual environment
myenv\Scripts\activate

# Run the API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

Once running, access:

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Available Endpoints

```
POST   /agents/register              - Register new agent
POST   /agents/{agent_id}/initialize - Initialize agent
POST   /agents/{agent_id}/invoke     - Invoke agent
GET    /agents/                      - List all agents
GET    /                             - Welcome message
```

## Background Mode

To run in background (Windows):
```powershell
Start-Process -FilePath "uvicorn" -ArgumentList "api.main:app --reload --host 0.0.0.0 --port 8000"
```

## Test the API

```bash
# Test root endpoint
curl http://localhost:8000/

# List agents
curl http://localhost:8000/agents/
```

## Environment Variables Required

Make sure `.env` file has:
```env
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=agentic
OPENAI_API_KEY=your_key
GROQ_API_KEY=your_key
```

