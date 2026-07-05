"""
Memory layer for persistent AI context across sessions.

Inspired by: SuperMemory (MemoryOS + Memory APIs + MemorySDK),
             ECC (Memory layer with FAISS + SQLite hybrid)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Any


class MemoryType(str, Enum):
    """Types of memory entries like SuperMemory's Memory Tuples."""
    FACT = "fact"
    PREFERENCE = "preference" 
    DECISION = "decision"
    CONTEXT = "context"
    PATTERN = "pattern"
    ERROR = "error"
    CONVENTION = "convention"


@dataclass
class MemoryEntry:
    """Structured memory unit (who/what/when/where/why model)."""

    memory_id: str
    memory_type: MemoryType
    subject: str          # who/what
    content: str          # what
    context: str          # where (file, function, module)
    timestamp: datetime   # when
    importance: float     # 0-1 priority score
    tags: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)  # related memory_ids
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "subject": self.subject,
            "content": self.content,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "tags": self.tags,
            "references": self.references,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }


@dataclass
class MemorySpace:
    """A named memory space for organizing related memories."""

    space_id: str
    name: str
    description: str = ""
    memory_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MemoryLayer:
    """
    Persistent context memory for AI tools.

    Provides structured memory with:
    - Who/What/When/Where/Why model (inspired by SuperMemory)
    - Memory Spaces for organization
    - Importance-based recall
    - Automatic staleness tracking
    """

    def __init__(self, db_path: str, max_entries: int = 100000, ttl_days: int = 90):
        self._db_path = db_path
        self._max_entries = max_entries
        self._ttl_days = ttl_days
        self._entries: dict[str, MemoryEntry] = {}
        self._spaces: dict[str, MemorySpace] = {}
        self._tags_index: dict[str, set[str]] = {}
        self._counter = 0

    def _generate_id(self) -> str:
        """Generate a unique memory ID."""
        self._counter += 1
        ts = int(time.time() * 1000)
        return f"mem_{ts}_{self._counter:06d}"

    def remember(
        self,
        memory_type: MemoryType,
        subject: str,
        content: str,
        context: str = "",
        importance: float = 0.5,
        tags: Optional[list[str]] = None,
        references: Optional[list[str]] = None,
        ttl_days: Optional[int] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> MemoryEntry:
        """Store a new memory entry."""
        if len(self._entries) >= self._max_entries:
            self._evict_stale()

        memory_id = self._generate_id()
        now = datetime.now(timezone.utc)

        entry = MemoryEntry(
            memory_id=memory_id,
            memory_type=memory_type,
            subject=subject,
            content=content,
            context=context,
            timestamp=now,
            importance=min(1.0, max(0.0, importance)),
            tags=tags or [],
            references=references or [],
            access_count=0,
            last_accessed=None,
            expires_at=(
                datetime.fromtimestamp(
                    now.timestamp() + (ttl_days or self._ttl_days) * 86400, tz=timezone.utc
                )
                if ttl_days or self._ttl_days > 0
                else None
            ),
            metadata=metadata or {},
        )

        self._entries[memory_id] = entry
        for tag in entry.tags:
            if tag not in self._tags_index:
                self._tags_index[tag] = set()
            self._tags_index[tag].add(memory_id)

        return entry

    def recall(
        self,
        memory_id: Optional[str] = None,
        memory_type: Optional[MemoryType] = None,
        tag: Optional[str] = None,
        subject_contains: Optional[str] = None,
        limit: int = 20,
    ) -> list[MemoryEntry]:
        """Recall memories matching criteria."""
        results = list(self._entries.values())

        if memory_id:
            entry = self._entries.get(memory_id)
            results = [entry] if entry else []
        if memory_type:
            results = [e for e in results if e.memory_type == memory_type]
        if tag and tag in self._tags_index:
            tagged_ids = self._tags_index[tag]
            results = [e for e in results if e.memory_id in tagged_ids]
        if subject_contains:
            query = subject_contains.lower()
            results = [e for e in results if query in e.subject.lower()]

        # Sort by importance then recency
        results.sort(key=lambda e: (e.importance, e.timestamp.timestamp()), reverse=True)

        # Update access stats
        for entry in results[:limit]:
            entry.access_count += 1
            entry.last_accessed = datetime.now(timezone.utc)

        return results[:limit]

    def recall_recent(self, hours: int = 24, limit: int = 20) -> list[MemoryEntry]:
        """Recall recently stored memories."""
        cutoff = datetime.now(timezone.utc).timestamp() - hours * 3600
        recent = [e for e in self._entries.values() if e.timestamp.timestamp() > cutoff]
        recent.sort(key=lambda e: e.timestamp.timestamp(), reverse=True)
        return recent[:limit]

    def forget(self, memory_id: str) -> bool:
        """Remove a specific memory entry."""
        entry = self._entries.pop(memory_id, None)
        if entry:
            for tag in entry.tags:
                if tag in self._tags_index:
                    self._tags_index[tag].discard(memory_id)
            return True
        return False

    def _evict_stale(self) -> int:
        """Remove stale/expired entries."""
        now = datetime.now(timezone.utc)
        stale_ids = []
        for mid, entry in self._entries.items():
            if entry.expires_at and entry.expires_at < now:
                stale_ids.append(mid)
        for mid in stale_ids:
            self.forget(mid)
        return len(stale_ids)

    def create_space(self, name: str, description: str = "") -> MemorySpace:
        """Create a new memory space."""
        space_id = f"space_{int(time.time())}"
        space = MemorySpace(space_id=space_id, name=name, description=description)
        self._spaces[space_id] = space
        return space

    def add_to_space(self, space_id: str, memory_id: str) -> bool:
        """Add a memory to a space."""
        space = self._spaces.get(space_id)
        if not space or memory_id not in self._entries:
            return False
        if memory_id not in space.memory_ids:
            space.memory_ids.append(memory_id)
        return True

    def get_space(self, space_id: str) -> Optional[MemorySpace]:
        """Get a memory space by ID."""
        return self._spaces.get(space_id)

    def stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        by_type = {}
        for e in self._entries.values():
            t = e.memory_type.value
            by_type[t] = by_type.get(t, 0) + 1
        stale = self._evict_stale()
        return {
            "total_entries": len(self._entries),
            "total_spaces": len(self._spaces),
            "total_tags": len(self._tags_index),
            "by_type": by_type,
            "stale_evicted": stale,
        }