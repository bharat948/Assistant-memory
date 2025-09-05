# This file contains the actual implementation for 'local' tools.

def echo(payload: dict) -> dict:
    """A simple tool that echoes back the input payload."""
    print(f"Executing 'echo' tool with payload: {payload}")
    return payload

def add(payload: dict) -> dict:
    """A tool to add two numbers."""
    a = payload.get("a", 0)
    b = payload.get("b", 0)
    result = a + b
    print(f"Executing 'add' tool: {a} + {b} = {result}")
    return {"sum": result}
