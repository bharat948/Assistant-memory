# Application Architecture

This document outlines the architecture of the agent service application.

## Overview

The application is a FastAPI-based service that allows for the registration, initialization, and invocation of AI agents. It uses MongoDB to store agent configurations and has a modular tool system that agents can leverage.

## Core Components

The application is divided into several key components:

-   **`agent_service`**: This is the main FastAPI application that exposes the API endpoints for managing and interacting with agents.
    -   **`app/main.py`**: The entry point of the FastAPI application.
    -   **`app/api/endpoints`**: Contains the API endpoint definitions.
    -   **`app/core/agent_service.py`**: Implements the business logic for the agent service.
-   **`agent_core`**: This component contains the core logic for the AI agents.
    -   **`agent.py`**: Defines the `Agent` class, which encapsulates the agent's functionality.
    -   **`agent_init.py`**: Handles the initialization of agents.
-   **`mongo_service`**: This component is responsible for all interactions with the MongoDB database.
    -   **`AppRepo/apprepo.py`**: Implements the Data Access Object (DAO) for agent configurations.
-   **`python_tool_module`**: This component provides a modular system for tools that agents can use.
    -   **`tools/base.py`**: Defines the base class for all tools.
    -   **`services/tool_loader.py`**: Loads the tools that are available to the agents.
-   **`client`**: This is the frontend application (Angular) that interacts with the agent service.

## Data Flow

1.  A user interacts with the frontend client.
2.  The client sends requests to the `agent_service` FastAPI application.
3.  The `agent_service` uses the `mongo_service` to retrieve or store agent configurations.
4.  When an agent is invoked, the `agent_core` is used to create an instance of the agent.
5.  The agent uses the `python_tool_module` to access and execute tools.
6.  The result is returned to the client through the `agent_service`.
