from typing import Dict, Any

def record(tool_id: str, api_key: str, payload: Dict, result: Dict, status: str):
    """Placeholder for an audit logging mechanism."""
    print(f"AUDIT | tool_id='{tool_id}' | status='{status}' | payload={payload} | result={result}")
