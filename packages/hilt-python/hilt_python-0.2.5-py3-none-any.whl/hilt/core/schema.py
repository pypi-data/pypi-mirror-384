"""JSON Schema definitions for HILT events."""

from __future__ import annotations

from typing import Any, Dict


# JSON Schema for Actor
ACTOR_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "id": {"type": "string"},
        "name": {"type": ["string", "null"]},
        "metadata": {"type": ["object", "null"]},
    },
    "required": ["type", "id"],
    "additionalProperties": False,
}


# JSON Schema for Content
CONTENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "text": {"type": ["string", "null"]},
        "images": {"type": ["array", "null"]},
        "metadata": {"type": ["object", "null"]},
    },
    "additionalProperties": True,
}


# JSON Schema for Metrics
METRICS_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "tokens": {
            "type": ["object", "null"],
            "properties": {
                "prompt": {"type": "integer"},
                "completion": {"type": "integer"},
                "total": {"type": "integer"},
            },
        },
        "cost_usd": {"type": ["number", "null"]},
        "latency_ms": {"type": ["integer", "null"]},
    },
    "additionalProperties": True,
}


# JSON Schema for Event
EVENT_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "event_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "session_id": {"type": "string"},
        "actor": ACTOR_SCHEMA,
        "action": {"type": "string"},
        "content": {
            "oneOf": [
                CONTENT_SCHEMA,
                {"type": "null"}
            ]
        },
        "metrics": {
            "oneOf": [
                METRICS_SCHEMA,
                {"type": "null"}
            ]
        },
        "provenance": {"type": ["object", "null"]},
        "extensions": {"type": ["object", "null"]},
    },
    "required": ["event_id", "timestamp", "session_id", "actor", "action"],
    "additionalProperties": False,
}


def validate_event(event_dict: Dict[str, Any]) -> bool:
    """
    Validate an event dictionary against the schema.
    
    Args:
        event_dict: Event as dictionary
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If event is invalid
    """
    try:
        import jsonschema
        jsonschema.validate(instance=event_dict, schema=EVENT_SCHEMA)
        return True
    except ImportError:
        # jsonschema not installed, skip validation
        return True
    except jsonschema.ValidationError as e:
        from hilt.core.exceptions import ValidationError
        raise ValidationError(f"Event validation failed: {e.message}")


__all__ = [
    "ACTOR_SCHEMA",
    "CONTENT_SCHEMA",
    "METRICS_SCHEMA",
    "EVENT_SCHEMA",
    "validate_event",
]