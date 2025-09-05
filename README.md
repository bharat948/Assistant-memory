# Agent & Tool Microservice Monorepo

This repository contains a backend-focused implementation of a "Tool + Agent" ecosystem. It provides two distinct approaches:

1.  **Python-Native System**: A tightly-coupled system where an agent core (`agent_core`) directly uses tools defined in Python (`python_tool_module`) and loads its configuration from MongoDB (`mongo_service`).
2.  **Microservice Architecture**: A decoupled system featuring a FastAPI microservice (`aether_tools_service`) for registering and invoking tools via a declarative YAML configuration. A separate LangChain-based agent (`aether_agent`) consumes these tools over HTTP.

## ✨ Core Concepts

### 1. Python-Native System

*   **`mongo_service`**: Manages all database interactions for loading agent configurations.
*   **`agent_core`**: Contains the primary agent logic, including the LLM wrapper and initialization from the database.
*   **`python_tool_module`**: A library of tools written in Python, registered in a central dictionary, and loaded directly by the agent at runtime.

### 2. Microservice Architecture (Aether Tools)

*   **`aether_tools_service`**: A central API (`app/main.py`) that exposes tools defined in a YAML configuration. It handles security, validation, rate limiting, and auditing.
*   **Declarative Tools**: Tools are defined in `aether_agent/agent/examples/tools.yaml`, specifying their type (`http` or `local`), input schema, and other metadata.
*   **`aether_agent`**: A standalone script (`agent/agent_runner.py`) that loads tool configurations from the microservice, presents them to a LangChain agent, and provides an interactive command line.

## How to Run

### Running the Aether Tools Microservice

1.  Navigate to the `aether_agent` directory and create a `.env` file from the `.env.example`. Fill in your `OPENAI_API_KEY` and `AETHER_API_KEY`.
    ```bash
    cd aether_agent
    cp .env.example .env
    # Edit .env with your keys
    ```
2.  Navigate to the `aether_tools_service` directory.
    ```bash
    cd ../aether_tools_service
    ```
3.  Build and run the Docker container.
    ```bash
    docker-compose up --build
    ```
    The service will be available at `http://localhost:8000`.

### Running the Aether Agent

1.  Make sure the microservice is running.
2.  In a new terminal, navigate to the `aether_agent` directory.
    ```bash
    cd aether_agent
    ```
3.  Install the required Python packages (it's recommended to use a virtual environment).
    ```bash
    pip install -r ../aether_tools_service/requirements.txt
    ```
4.  Run the agent runner.
    ```bash
    python -m agent.agent_runner
