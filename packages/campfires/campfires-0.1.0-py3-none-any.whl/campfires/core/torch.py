"""
Torch data structure for passing lightweight messages between campfires.
"""

import time
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class Torch(BaseModel):
    """
    A lightweight message carrying distilled results between campfires.
    
    Torches only carry text metadata, not raw assets. Assets are stored
    in the Party Box and referenced by path or URL.
    """
    
    claim: str = Field(
        description="The main claim or result from the campfire"
    )
    
    path: Optional[str] = Field(
        default=None,
        description="Path to asset in Party Box (e.g., './party_box/abc123.jpg')"
    )
    
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the claim (0.0 to 1.0)"
    )
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata and context"
    )
    
    timestamp: float = Field(
        default_factory=time.time,
        description="Unix timestamp when torch was created"
    )
    
    source_campfire: str = Field(
        description="Name of the campfire that created this torch"
    )
    
    channel: str = Field(
        description="MCP channel this torch is being sent to"
    )
    
    torch_id: Optional[str] = Field(
        default=None,
        description="Unique identifier for this torch"
    )
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.torch_id is None:
            # Generate a simple torch ID based on timestamp and source
            self.torch_id = f"{self.source_campfire}_{int(self.timestamp * 1000)}"
    
    def to_mcp_message(self) -> Dict[str, Any]:
        """
        Convert torch to MCP message format.
        
        Returns:
            Dict containing the torch data in MCP format
        """
        return {
            "type": "torch",
            "id": self.torch_id,
            "channel": self.channel,
            "source": self.source_campfire,
            "timestamp": self.timestamp,
            "payload": {
                "claim": self.claim,
                "path": self.path,
                "confidence": self.confidence,
                "metadata": self.metadata
            }
        }
    
    @classmethod
    def from_mcp_message(cls, message: Dict[str, Any]) -> "Torch":
        """
        Create a Torch from an MCP message.
        
        Args:
            message: MCP message dictionary
            
        Returns:
            Torch instance
        """
        payload = message.get("payload", {})
        
        return cls(
            claim=payload.get("claim", ""),
            path=payload.get("path"),
            confidence=payload.get("confidence", 1.0),
            metadata=payload.get("metadata", {}),
            timestamp=message.get("timestamp", time.time()),
            source_campfire=message.get("source", "unknown"),
            channel=message.get("channel", "default"),
            torch_id=message.get("id")
        )
    
    def add_metadata(self, key: str, value: Any) -> None:
        """
        Add metadata to the torch.
        
        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get metadata value by key.
        
        Args:
            key: Metadata key
            default: Default value if key not found
            
        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)
    
    def is_expired(self, max_age_seconds: int = 1200) -> bool:
        """
        Check if torch is expired (older than max_age_seconds).
        
        Args:
            max_age_seconds: Maximum age in seconds (default: 20 minutes)
            
        Returns:
            True if torch is expired
        """
        return (time.time() - self.timestamp) > max_age_seconds
    
    def __str__(self) -> str:
        """String representation of the torch."""
        return f"Torch({self.torch_id}): {self.claim[:50]}..."
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (
            f"Torch(id={self.torch_id}, source={self.source_campfire}, "
            f"channel={self.channel}, confidence={self.confidence})"
        )