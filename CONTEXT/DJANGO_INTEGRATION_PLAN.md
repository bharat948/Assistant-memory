# Django Integration Plan: Agent & Memory Modules as Packages

## Overview
Restructure the project to package `agent_core` and `memory_module` as separate installable packages, and integrate them as endpoints in a Django project.

## Current Architecture

```
Modules/
├── agent_core/              # Agent creation & execution
├── memory_module/            # Memory management (PostgreSQL-based)
├── agent_service/            # FastAPI service
├── mongo_service/            # Agent configuration storage
└── python_tool_module/       # Tool system
```

## Proposed Architecture

```
agent-core-package/           # Standalone package
├── agent_core/
│   ├── agent.py
│   ├── agent_init.py
│   └── llm.py
└── setup.py

memory-core-package/          # Standalone package
├── memory_module/
│   ├── enhanced_memory.py
│   ├── models.py
│   └── ...
└── setup.py

django-agent-service/         # Django project
├── config/
│   └── settings.py
├── agent/
│   ├── urls.py
│   ├── views.py
│   └── serializers.py
├── memory/
│   ├── urls.py
│   ├── views.py
│   └── serializers.py
└── requirements.txt
```

## Implementation Plan

### Phase 1: Package Structure

#### 1.1 Create `agent-core` Package

**Structure:**
```
agent-core/
├── setup.py
├── README.md
├── MANIFEST.in
├── agent_core/
│   ├── __init__.py
│   ├── agent.py
│   ├── agent_init.py
│   └── llm.py
├── tests/
│   └── test_agent.py
└── requirements.txt
```

**setup.py:**
```python
from setuptools import setup, find_packages

setup(
    name="agent-core",
    version="0.1.0",
    description="Core agent functionality for AI agents",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.3.0",
        "langchain-openai>=0.3.0",
        "langchain-core>=0.3.0",
        "openai>=1.0.0",
        "motor>=3.0.0",
        "pymongo>=4.0.0",
    ],
    python_requires=">=3.8",
)
```

#### 1.2 Create `memory-core` Package

**Structure:**
```
memory-core/
├── setup.py
├── README.md
├── MANIFEST.in
├── memory_module/
│   ├── __init__.py
│   ├── enhanced_memory.py
│   ├── models.py
│   ├── config.py
│   └── ...
├── tests/
│   └── test_memory.py
└── requirements.txt
```

**setup.py:**
```python
from setuptools import setup, find_packages

setup(
    name="memory-core",
    version="0.1.0",
    description="Enhanced memory system for AI agents",
    packages=find_packages(),
    install_requires=[
        "psycopg2-binary>=2.9.0",
        "motor>=3.0.0",  # For future MongoDB support
        "pymongo>=4.0.0",
        "openai>=1.0.0",
    ],
    python_requires=">=3.8",
)
```

### Phase 2: Django Project Structure

#### 2.1 Django Project Setup

```bash
# Create Django project
django-admin startproject agent_service
cd agent_service

# Create apps
python manage.py startapp agent
python manage.py startapp memory
```

#### 2.2 Django Settings (config/settings.py)

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'agent',
    'memory',
]

# Memory Module Configuration
POSTGRES_DSN = os.getenv('POSTGRES_DSN', 'postgresql://localhost/memory_db')
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'agent_db')

# LLM Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Memory Configuration
ALLOWED_TAGS = json.loads(os.getenv('ALLOWED_TAGS', '["general", "work"]'))
ALLOWED_COLLECTIONS = json.loads(os.getenv('ALLOWED_COLLECTIONS', '["conversations"]'))
WORKING_MEMORY_THRESHOLD = int(os.getenv('WORKING_MEMORY_THRESHOLD', '6'))
```

#### 2.3 Agent App (agent/views.py)

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from agent_core import Agent, AgentInitializer
from memory_module import EnhancedMemory, GroqLLMClient
from mongo_service import get_agent_config
import os
import json

# In-memory cache for agents
_agent_cache = {}

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def register_agent(request):
    """Register a new agent"""
    try:
        agent_data = request.data
        agent_id = await save_agent_config(agent_data)
        return Response({
            'status': 'success',
            'agent_id': agent_id
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def initialize_agent(request, agent_id):
    """Initialize an agent"""
    try:
        if agent_id in _agent_cache:
            return Response({
                'status': 'success',
                'message': 'Agent already initialized'
            })
        
        # Get agent config
        config = await get_agent_config(agent_id)
        
        # Initialize memory
        memory = EnhancedMemory(
            db_dsn=settings.POSTGRES_DSN,
            llm_client=GroqLLMClient(),
            working_memory_threshold=settings.WORKING_MEMORY_THRESHOLD
        )
        memory.register_agent_permissions(
            agent_id=agent_id,
            allowed_tags=settings.ALLOWED_TAGS,
            allowed_collections=settings.ALLOWED_COLLECTIONS
        )
        
        # Initialize agent
        agent = await AgentInitializer.init_agent(agent_id)
        agent.memory = memory
        
        # Cache agent
        _agent_cache[agent_id] = agent
        
        return Response({
            'status': 'success',
            'agent_id': agent_id
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def invoke_agent(request, agent_id):
    """Invoke an agent"""
    try:
        if agent_id not in _agent_cache:
            return Response({
                'status': 'error',
                'message': 'Agent not initialized'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        agent = _agent_cache[agent_id]
        
        # Get request data
        prompt = request.data.get('prompt')
        user_id = request.user.username
        conversation_id = request.data.get('conversation_id')
        
        # Invoke agent
        result = await agent.invoke(
            user_query=prompt,
            user_id=user_id,
            conversation_id=conversation_id
        )
        
        return Response({
            'status': 'success',
            'response': result['response']
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
async def list_agents(request):
    """List all registered agents"""
    try:
        agents = await list_all_agents()
        return Response({
            'status': 'success',
            'agents': agents
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

#### 2.4 Agent URLs (agent/urls.py)

```python
from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_agent, name='register_agent'),
    path('initialize/<str:agent_id>/', views.initialize_agent, name='initialize_agent'),
    path('invoke/<str:agent_id>/', views.invoke_agent, name='invoke_agent'),
    path('list/', views.list_agents, name='list_agents'),
]
```

#### 2.5 Memory App (memory/views.py)

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
from memory_module import EnhancedMemory, GroqLLMClient

# Single memory instance (singleton)
memory = None

def get_memory():
    global memory
    if memory is None:
        memory = EnhancedMemory(
            db_dsn=settings.POSTGRES_DSN,
            llm_client=GroqLLMClient(),
            working_memory_threshold=settings.WORKING_MEMORY_THRESHOLD
        )
    return memory

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_conversation_history(request):
    """Get conversation history"""
    try:
        user_id = request.user.username
        agent_id = request.GET.get('agent_id')
        limit = int(request.GET.get('limit', 50))
        
        memory = get_memory()
        messages = memory.get_short_term_memory_by_user(
            user_id=user_id,
            agent_id=agent_id,
            limit=limit
        )
        
        return Response({
            'status': 'success',
            'messages': messages
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_memory(request):
    """Search long-term memory"""
    try:
        query = request.GET.get('q')
        limit = int(request.GET.get('limit', 20))
        
        memory = get_memory()
        chunks = memory.search_content(query=query, limit=limit)
        
        return Response({
            'status': 'success',
            'chunks': [c.to_dict() for c in chunks]
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_memory_stats(request):
    """Get memory statistics"""
    try:
        memory = get_memory()
        stats = memory.get_statistics()
        
        return Response({
            'status': 'success',
            'stats': stats
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=500)
```

#### 2.6 Memory URLs (memory/urls.py)

```python
from django.urls import path
from . import views

urlpatterns = [
    path('history/', views.get_conversation_history, name='get_history'),
    path('search/', views.search_memory, name='search_memory'),
    path('stats/', views.get_memory_stats, name='get_stats'),
]
```

#### 2.7 Main URLs (config/urls.py)

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/agents/', include('agent.urls')),
    path('api/memory/', include('memory.urls')),
]
```

### Phase 3: Requirements

**requirements.txt:**
```
# Django
Django>=5.0.0
djangorestframework>=3.14.0
django-cors-headers>=4.0.0

# Our packages (install from local packages)
agent-core>=0.1.0
memory-core>=0.1.0

# Dependencies
langchain>=0.3.0
langchain-openai>=0.3.0
openai>=1.0.0
motor>=3.0.0
pymongo>=4.0.0
psycopg2-binary>=2.9.0
python-dotenv>=1.0.0
```

**Installation:**
```bash
# Install local packages
pip install -e ../agent-core
pip install -e ../memory-core

# Install Django dependencies
pip install -r requirements.txt
```

### Phase 4: Django Project Structure

```
django-agent-service/
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── agent/
│   ├── __init__.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── memory/
│   ├── __init__.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── requirements.txt
└── .env
```

## API Endpoints

### Agent Endpoints
- `POST /api/agents/register/` - Register new agent
- `POST /api/agents/initialize/<agent_id>/` - Initialize agent
- `POST /api/agents/invoke/<agent_id>/` - Invoke agent
- `GET /api/agents/list/` - List all agents

### Memory Endpoints
- `GET /api/memory/history/` - Get conversation history
- `GET /api/memory/search/?q=<query>` - Search memory
- `GET /api/memory/stats/` - Get memory statistics

## Benefits of This Architecture

1. **Modularity**: Each component is independently deployable
2. **Reusability**: Packages can be used in other projects
3. **Scalability**: Django handles multiple workers natively
4. **Admin Interface**: Built-in Django admin for agent management
5. **Authentication**: Django's auth system for agent access
6. **Database**: Can use Django ORM alongside custom memory system
7. **Testing**: Django's test framework for comprehensive testing

## Migration Checklist

- [ ] Create agent-core package
- [ ] Create memory-core package
- [ ] Setup Django project
- [ ] Create agent app with views
- [ ] Create memory app with views
- [ ] Configure Django settings
- [ ] Create URL routing
- [ ] Add authentication middleware
- [ ] Write unit tests
- [ ] Document API endpoints
- [ ] Deploy to production

## Example Usage

```python
# Django app using our packages
from agent_core import Agent, AgentInitializer
from memory_module import EnhancedMemory

# In a Django view
async def my_view(request):
    agent = await AgentInitializer.init_agent('my_agent')
    result = await agent.invoke('Hello!', user_id=request.user.username)
    return JsonResponse(result)
```

