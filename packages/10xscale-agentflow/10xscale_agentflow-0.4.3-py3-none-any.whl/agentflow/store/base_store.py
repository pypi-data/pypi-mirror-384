"""
Simplified Async-First Base Store for TAF Framework

This module provides a clean, modern interface for memory stores with:
- Async-first design for better performance
- Core CRUD operations only
- Message-specific convenience methods
- Extensible for different backends (vector stores, managed services, etc.)
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from agentflow.state import Message
from agentflow.utils import run_coroutine

from .store_schema import DistanceMetric, MemorySearchResult, MemoryType, RetrievalStrategy


logger = logging.getLogger(__name__)


class BaseStore(ABC):
    """
    Simplified async-first base class for memory stores in TAF.

    This class provides a clean interface that supports:
    - Vector stores (Qdrant, Pinecone, Chroma, etc.)
    - Managed memory services (mem0, Zep, etc.)
    - Graph databases (Neo4j, etc.)

    Key Design Principles:
    - Async-first for better performance
    - Core CRUD operations only
    - User and agent-centric operations
    - Extensible filtering and metadata
    """

    def setup(self) -> Any:
        """
        Synchronous setup method for checkpointer.

        Returns:
            Any: Implementation-defined setup result.
        """
        return run_coroutine(self.asetup())

    async def asetup(self) -> Any:
        """
        Asynchronous setup method for checkpointer.

        Returns:
            Any: Implementation-defined setup result.
        """
        raise NotImplementedError

    # --- Core Memory Operations ---

    @abstractmethod
    async def astore(
        self,
        config: dict[str, Any],
        content: str | Message,
        memory_type: MemoryType = MemoryType.EPISODIC,
        category: str = "general",
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> str:
        """
        Add a new memory.

        Args:
            content: The memory content
            user_id: User identifier
            agent_id: Agent identifier
            memory_type: Type of memory (episodic, semantic, etc.)
            category: Memory category for organization
            metadata: Additional metadata
            **kwargs: Store-specific parameters

        Returns:
            Memory ID
        """
        raise NotImplementedError

    # --- Sync wrappers ---
    def store(
        self,
        config: dict[str, Any],
        content: str | Message,
        memory_type: MemoryType = MemoryType.EPISODIC,
        category: str = "general",
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> str:
        """Synchronous wrapper for `astore` that runs the async implementation."""
        return run_coroutine(
            self.astore(
                config,
                content,
                memory_type=memory_type,
                category=category,
                metadata=metadata,
                **kwargs,
            )
        )

    @abstractmethod
    async def asearch(
        self,
        config: dict[str, Any],
        query: str,
        memory_type: MemoryType | None = None,
        category: str | None = None,
        limit: int = 10,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
        retrieval_strategy: RetrievalStrategy = RetrievalStrategy.SIMILARITY,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        max_tokens: int = 4000,
        **kwargs,
    ) -> list[MemorySearchResult]:
        """
        Search memories by content similarity.

        Args:
            query: Search query
            user_id: Filter by user
            agent_id: Filter by agent
            memory_type: Filter by memory type
            category: Filter by category
            limit: Maximum results
            score_threshold: Minimum similarity score
            filters: Additional filters
            **kwargs: Store-specific parameters

        Returns:
            List of matching memories
        """
        raise NotImplementedError

    def search(
        self,
        config: dict[str, Any],
        query: str,
        memory_type: MemoryType | None = None,
        category: str | None = None,
        limit: int = 10,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
        retrieval_strategy: RetrievalStrategy = RetrievalStrategy.SIMILARITY,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        max_tokens: int = 4000,
        **kwargs,
    ) -> list[MemorySearchResult]:
        """Synchronous wrapper for `asearch` that runs the async implementation."""
        return run_coroutine(
            self.asearch(
                config,
                query,
                memory_type=memory_type,
                category=category,
                limit=limit,
                score_threshold=score_threshold,
                filters=filters,
                retrieval_strategy=retrieval_strategy,
                distance_metric=distance_metric,
                max_tokens=max_tokens,
                **kwargs,
            )
        )

    @abstractmethod
    async def aget(
        self,
        config: dict[str, Any],
        memory_id: str,
        **kwargs,
    ) -> MemorySearchResult | None:
        """Get a specific memory by ID."""
        raise NotImplementedError

    @abstractmethod
    async def aget_all(
        self,
        config: dict[str, Any],
        limit: int = 100,
        **kwargs,
    ) -> list[MemorySearchResult]:
        """Get a specific memory by user_id."""
        raise NotImplementedError

    def get(self, config: dict[str, Any], memory_id: str, **kwargs) -> MemorySearchResult | None:
        """Synchronous wrapper for `aget` that runs the async implementation."""
        return run_coroutine(self.aget(config, memory_id, **kwargs))

    def get_all(
        self,
        config: dict[str, Any],
        limit: int = 100,
        **kwargs,
    ) -> list[MemorySearchResult]:
        """Synchronous wrapper for `aget` that runs the async implementation."""
        return run_coroutine(self.aget_all(config, limit=limit, **kwargs))

    @abstractmethod
    async def aupdate(
        self,
        config: dict[str, Any],
        memory_id: str,
        content: str | Message,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> Any:
        """
        Update an existing memory.

        Args:
            memory_id: ID of memory to update
            content: New content (optional)
            metadata: New/additional metadata (optional)
            **kwargs: Store-specific parameters
        """
        raise NotImplementedError

    def update(
        self,
        config: dict[str, Any],
        memory_id: str,
        content: str | Message,
        metadata: dict[str, Any] | None = None,
        **kwargs,
    ) -> Any:
        """Synchronous wrapper for `aupdate` that runs the async implementation."""
        return run_coroutine(self.aupdate(config, memory_id, content, metadata=metadata, **kwargs))

    @abstractmethod
    async def adelete(
        self,
        config: dict[str, Any],
        memory_id: str,
        **kwargs,
    ) -> Any:
        """Delete a memory by ID."""
        raise NotImplementedError

    def delete(self, config: dict[str, Any], memory_id: str, **kwargs) -> None:
        """Synchronous wrapper for `adelete` that runs the async implementation."""
        return run_coroutine(self.adelete(config, memory_id, **kwargs))

    @abstractmethod
    async def aforget_memory(
        self,
        config: dict[str, Any],
        **kwargs,
    ) -> Any:
        """Delete a memory by for a user or agent."""
        raise NotImplementedError

    def forget_memory(
        self,
        config: dict[str, Any],
        **kwargs,
    ) -> Any:
        """Delete a memory by for a user or agent."""
        return run_coroutine(self.aforget_memory(config, **kwargs))

    # --- Cleanup and Resource Management ---

    async def arelease(self) -> None:
        """Clean up any resources used by the store (override in subclasses if needed)."""
        raise NotImplementedError

    def release(self) -> None:
        """Clean up any resources used by the store (override in subclasses if needed)."""
        return run_coroutine(self.arelease())
