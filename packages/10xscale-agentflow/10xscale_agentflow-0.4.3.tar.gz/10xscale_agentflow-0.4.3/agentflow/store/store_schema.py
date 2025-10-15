from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from agentflow.state import Message


class RetrievalStrategy(Enum):
    """Memory retrieval strategies."""

    SIMILARITY = "similarity"  # Vector similarity search
    TEMPORAL = "temporal"  # Time-based retrieval
    RELEVANCE = "relevance"  # Relevance scoring
    HYBRID = "hybrid"  # Combined approaches
    GRAPH_TRAVERSAL = "graph_traversal"  # Knowledge graph navigation


class DistanceMetric(Enum):
    """Supported distance metrics for vector similarity."""

    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"


class MemoryType(Enum):
    """Types of memories that can be stored."""

    EPISODIC = "episodic"  # Conversation memories
    SEMANTIC = "semantic"  # Facts and knowledge
    PROCEDURAL = "procedural"  # How-to knowledge
    ENTITY = "entity"  # Entity-based memories
    RELATIONSHIP = "relationship"  # Entity relationships
    CUSTOM = "custom"  # Custom memory types
    DECLARATIVE = "declarative"  # Explicit facts and events


class MemorySearchResult(BaseModel):
    """Result from a memory search operation (Pydantic model)."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str = Field(default="", description="Primary textual content of the memory")
    score: float = Field(default=0.0, ge=0.0, description="Similarity / relevance score")
    memory_type: MemoryType = Field(default=MemoryType.EPISODIC)
    metadata: dict[str, Any] = Field(default_factory=dict)
    vector: list[float] | None = Field(default=None)
    user_id: str | None = None
    thread_id: str | None = None
    timestamp: datetime | None = Field(default_factory=datetime.now)

    @field_validator("vector")
    @classmethod
    def validate_vector(cls, v):
        if v is not None and (
            not isinstance(v, list) or any(not isinstance(x, (int | float)) for x in v)
        ):
            raise ValueError("vector must be list[float] or None")
        return v


class MemoryRecord(BaseModel):
    """Comprehensive memory record for storage (Pydantic model)."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    user_id: str | None = None
    thread_id: str | None = None
    memory_type: MemoryType = Field(default=MemoryType.EPISODIC)
    metadata: dict[str, Any] = Field(default_factory=dict)
    category: str = Field(default="general")
    vector: list[float] | None = None
    timestamp: datetime | None = Field(default_factory=datetime.now)

    @field_validator("vector")
    @classmethod
    def validate_vector(cls, v):
        if v is not None and (
            not isinstance(v, list) or any(not isinstance(x, (int | float)) for x in v)
        ):
            raise ValueError("vector must be list[float] or None")
        return v

    @classmethod
    def from_message(
        cls,
        message: Message,
        user_id: str | None = None,
        thread_id: str | None = None,
        vector: list[float] | None = None,
        additional_metadata: dict[str, Any] | None = None,
    ) -> "MemoryRecord":
        content = message.text()

        # Convert timestamp (float) to ISO format string
        timestamp_str = None
        if message.timestamp:
            timestamp_dt = datetime.fromtimestamp(message.timestamp)
            timestamp_str = timestamp_dt.isoformat()

        metadata = {
            "role": message.role,
            "message_id": str(message.message_id),
            "timestamp": timestamp_str,
            "has_tool_calls": bool(message.tools_calls),
            "has_reasoning": bool(message.reasoning),
            "token_usage": message.usages.model_dump() if message.usages else None,
            **(additional_metadata or {}),
        }
        return cls(
            content=content,
            user_id=user_id,
            thread_id=thread_id,
            memory_type=MemoryType.EPISODIC,
            metadata=metadata,
            vector=vector,
        )
