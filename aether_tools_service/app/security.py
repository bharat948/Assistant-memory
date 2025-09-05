import os
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_NAME = "x-api-key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def check_api_key(api_key: str = Security(api_key_header)):
    """Checks if the provided API key is valid."""
    expected_api_key = os.getenv("AETHER_API_KEY")
    if not expected_api_key:
        raise HTTPException(
            status_code=500, detail="API key not configured on server."
        )
    if not api_key or api_key != expected_api_key:
        raise HTTPException(
            status_code=403, detail="Could not validate credentials."
        )
    return api_key
