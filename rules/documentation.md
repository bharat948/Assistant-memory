# Documentation Guidelines

This document provides guidelines for documenting the agent service application.

## General Principles

-   **Clarity**: Write clear and concise documentation that is easy to understand.
-   **Completeness**: Ensure that all features and components are adequately documented.
-   **Accuracy**: Keep the documentation up-to-date with the latest changes in the codebase.

## README Files

Each major component (`agent_core`, `agent_service`, etc.) should have its own `README.md` file that provides an overview of the component and instructions on how to use it.

## API Documentation

The FastAPI application automatically generates interactive API documentation (using Swagger UI and ReDoc). Ensure that all API endpoints have clear and descriptive docstrings that explain their purpose, parameters, and responses.

## Code Comments

Use inline comments to explain complex or non-obvious parts of the code. Avoid over-commenting simple code.

## Contribution Guidelines

If you are contributing to the project, please ensure that you update the relevant documentation along with your code changes. This includes:

-   Updating `README.md` files.
-   Adding or updating docstrings for new or modified functions and classes.
-   Updating the API documentation if you are changing any endpoints.
