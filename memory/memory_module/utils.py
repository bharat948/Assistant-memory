"""
Utility functions for the memory module.
"""
import json
import re
from datetime import datetime, timezone
from typing import Set, Tuple
from .config import CollectionType, ChunkType
from .logging_config import llm_logger, logger

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso_str(dt: datetime) -> str:
    return dt.replace(tzinfo=timezone.utc).isoformat()

def safe_json_parse(raw: str) -> dict:
    """Parse JSON from LLM response with multiple fallback strategies"""
    if not isinstance(raw, str):
        raise ValueError(f"Expected string from LLM, got {type(raw)}")
    
    llm_logger.debug(f"Attempting to parse LLM response (length: {len(raw)})")
    
    # Try direct parsing first
    try:
        result = json.loads(raw)
        llm_logger.debug("Direct JSON parsing successful")
        return result
    except json.JSONDecodeError as e:
        llm_logger.debug(f"Direct parsing failed: {e}, trying fallback methods")
    
    # Try regex pattern matching
    json_pattern = r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}' 
    candidates = re.findall(json_pattern, raw, flags=re.DOTALL)
    
    for idx, candidate in enumerate(reversed(candidates)):
        try:
            result = json.loads(candidate)
            llm_logger.debug(f"Successfully parsed JSON from candidate {idx}")
            return result
        except json.JSONDecodeError:
            continue
    
    # Try markdown code blocks
    markers = [
        (r'```json\s*(.*?)\s*```', re.DOTALL),
        (r'```\s*(.*?)\s*```', re.DOTALL),
        (r'JSON:\s*(\{.*?\})', re.DOTALL)
    ]
    
    for pattern, flags in markers:
        match = re.search(pattern, raw, flags)
        if match:
            try:
                result = json.loads(match.group(1))
                llm_logger.debug(f"Successfully parsed JSON from markdown block")
                return result
            except json.JSONDecodeError:
                continue
    
    llm_logger.error(f"Failed to extract valid JSON. Raw response preview: {raw[:200]}")
    raise ValueError("Could not extract valid JSON from LLM response")

def normalize_tag(tag: str) -> str:
    """Normalize tags to consistent format"""
    if not isinstance(tag, str):
        tag = str(tag)
    original = tag
    tag = tag.strip().lower()
    tag = re.sub(r'\s+', '_', tag)
    tag = re.sub(r'[^a-z0-9_]', '_', tag)
    tag = re.sub(r'_+', '_', tag)
    tag = tag.strip('_')
    normalized = tag[:64] or "tag"
    
    if original != normalized:
        logger.debug(f"Tag normalized: '{original}' -> '{normalized}'")
    
    return normalized

def validate_llm_output(data: dict, required_keys: Set[str]) -> Tuple[bool, str]:
    """Validate LLM output structure and content"""
    llm_logger.debug(f"Validating LLM output with required keys: {required_keys}")
    
    if not isinstance(data, dict):
        return False, "Response is not a JSON object"
    
    for key in required_keys:
        if key not in data:
            llm_logger.warning(f"Missing required key in LLM response: '{key}'")
            return False, f"Missing required key: '{key}'"
    
    if 'tags' in data:
        if not isinstance(data['tags'], list) or not data['tags']:
            return False, "'tags' must be a non-empty list"
        llm_logger.debug(f"Validated {len(data['tags'])} tags")
    
    if 'collection' in data:
        valid_collections = [c.value for c in CollectionType]
        if data['collection'] not in valid_collections:
            llm_logger.warning(f"Invalid collection: {data['collection']}")
            return False, f"Invalid collection: {data['collection']}"
    
    if 'importance' in data:
        try:
            imp = float(data['importance'])
            if not 0.0 <= imp <= 1.0:
                return False, "'importance' must be between 0.0 and 1.0"
            llm_logger.debug(f"Validated importance: {imp}")
        except (ValueError, TypeError):
            return False, "'importance' must be numeric"
    
    if 'chunk_type' in data:
        valid_types = [t.value for t in ChunkType]
        if data['chunk_type'] not in valid_types:
            return False, f"Invalid chunk_type: {data['chunk_type']}"
    
    llm_logger.debug("LLM output validation passed")
    return True, ""
