"""Actor representation for HILT events."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Actor:
    """
    Represents an entity participating in a conversation.
    
    Attributes:
        type: Type of actor (e.g., "human", "agent", "tool", "system")
        id: Unique identifier for this actor (e.g., "user123", "gpt-4")
        name: Optional human-readable name
        metadata: Optional additional metadata
    
    Examples:
        >>> # Human user
        >>> user = Actor(type="human", id="user123", name="Alice")
        
        >>> # AI assistant
        >>> assistant = Actor(type="agent", id="gpt-4")
        
        >>> # Tool or system
        >>> retriever = Actor(type="tool", id="vector-db")
        >>> system = Actor(type="system", id="error-handler")
    """
    
    type: str
    id: str
    name: Optional[str] = None
    metadata: Optional[dict] = None
    
    def to_dict(self) -> dict:
        """Convert Actor to dictionary."""
        result = {
            "type": self.type,
            "id": self.id,
        }
        
        if self.name is not None:
            result["name"] = self.name
        
        if self.metadata is not None:
            result["metadata"] = self.metadata
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> "Actor":
        """Create Actor from dictionary."""
        return cls(
            type=data["type"],
            id=data["id"],
            name=data.get("name"),
            metadata=data.get("metadata"),
        )


__all__ = ["Actor"]