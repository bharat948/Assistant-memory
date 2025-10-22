# Coding Practices

This document outlines the coding practices and standards for the agent service application.

## Python Style Guide

All Python code should adhere to the [PEP 8 Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/).

### Naming Conventions

-   **Modules**: `lower_case_with_underscores`
-   **Classes**: `CamelCase`
-   **Functions**: `lower_case_with_underscores`
-   **Variables**: `lower_case_with_underscores`
-   **Constants**: `UPPER_CASE_WITH_UNDERSCORES`

### Type Hinting

All function signatures should include type hints. This improves code readability and allows for static analysis.

### Docstrings

All modules, classes, and functions should have docstrings that explain their purpose. Use the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstring formatting.

### Linting and Formatting

-   **Flake8** should be used for linting to enforce PEP 8 and other style conventions.
-   **Black** should be used for automatic code formatting to ensure a consistent style across the codebase.

## FastAPI Best Practices

-   **Dependency Injection**: Use FastAPI's dependency injection system to manage dependencies like database connections.
-   **Pydantic Models**: Use Pydantic models for request and response validation.
-   **API Routers**: Organize endpoints into separate `APIRouter` instances to keep the main application file clean.

## General Best Practices

-   **Modularity**: Keep components small and focused on a single responsibility.
-   **Configuration**: Do not hard-code configuration values. Use environment variables or a configuration file.
-   **Error Handling**: Implement robust error handling to gracefully handle exceptions and provide meaningful error messages.
-   **Testing**: Write unit and integration tests for all new features and bug fixes.
