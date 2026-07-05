"""
Provenance engine - tracks the origin and lineage of AI-generated code blocks.

Inspired by: SuperMemory (memory tuples), ECC (memory layer), PR-Agent (diff tracking)
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional, Any


class AIProvider(str, Enum):
    """Supported AI coding tool providers."""
    CLAUDE_CODE = "claude_code"
    CURSOR = "cursor"
    GITHUB_COPILOT = "github_copilot"
    CODEX = "codex"
    WINDSURF = "windsurf"
    CONTINUE = "continue_dev"
    UNKNOWN = "unknown"


class ProvenanceStatus(str, Enum):
    """Status of a provenance entry."""
    GENERATED = "generated"
    MODIFIED = "modified"
    REVIEWED = "reviewed"
    TRUSTED = "trusted"
    REJECTED = "rejected"
    IN_PRODUCTION = "in_production"


@dataclass
class ProvenanceEntry:
    """A single provenance entry tracking one AI-generated code block."""

    entry_id: str
    file_path: str
    line_start: int
    line_end: int
    provider: AIProvider
    model: str
    prompt_hash: str
    prompt_preview: str
    generated_at: datetime
    modified_at: datetime
    status: ProvenanceStatus
    trust_score: float = 0.0
    tokens_used: int = 0
    context_snapshot: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        d = asdict(self)
        d["provider"] = self.provider.value
        d["status"] = self.status.value
        d["generated_at"] = self.generated_at.isoformat()
        d["modified_at"] = self.modified_at.isoformat()
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProvenanceEntry":
        """Deserialize from dictionary."""
        data["provider"] = AIProvider(data["provider"])
        data["status"] = ProvenanceStatus(data["status"])
        data["generated_at"] = datetime.fromisoformat(data["generated_at"])
        data["modified_at"] = datetime.fromisoformat(data["modified_at"])
        return cls(**data)

    @property
    def age_hours(self) -> float:
        """Age of this entry in hours."""
        delta = datetime.now(timezone.utc) - self.generated_at
        return delta.total_seconds() / 3600.0

    @property
    def is_stale(self) -> bool:
        """Check if entry is older than 72 hours without review."""
        return self.age_hours > 72 and self.status == ProvenanceStatus.GENERATED


@dataclass
class ProvenanceReport:
    """Aggregated report for a file or project."""

    total_entries: int
    by_provider: dict[str, int]
    by_status: dict[str, int]
    avg_trust_score: float
    total_tokens_consumed: int
    stale_entries: int
    entries: list[ProvenanceEntry]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "total_entries": self.total_entries,
            "by_provider": self.by_provider,
            "by_status": self.by_status,
            "avg_trust_score": self.avg_trust_score,
            "total_tokens_consumed": self.total_tokens_consumed,
            "stale_entries": self.stale_entries,
            "entries": [e.to_dict() for e in self.entries],
            "generated_at": self.generated_at.isoformat(),
        }


class ProvenanceEngine:
    """
    Core provenance tracking engine.

    Records every AI-generated code block with full lineage:
    - Which AI tool generated it
    - Which model and prompt were used
    - When and in what context
    - How it has been modified since generation
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._entries: dict[str, ProvenanceEntry] = {}
        self._index_by_file: dict[str, list[str]] = {}

    def _hash_prompt(self, prompt: str) -> str:
        """Create a deterministic hash of a prompt for deduplication."""
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]

    def record(
        self,
        file_path: str,
        line_start: int,
        line_end: int,
        provider: AIProvider,
        model: str,
        prompt: str,
        code_content: str = "",
        tokens_used: int = 0,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ProvenanceEntry:
        """Record a new AI-generated code block."""
        prompt_hash = self._hash_prompt(prompt)
        entry_id = hashlib.sha256(
            f"{file_path}:{line_start}:{line_end}:{prompt_hash}:{time.time_ns()}".encode()
        ).hexdigest()[:20]

        now = datetime.now(timezone.utc)
        entry = ProvenanceEntry(
            entry_id=entry_id,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            provider=provider,
            model=model,
            prompt_hash=prompt_hash,
            prompt_preview=prompt[:200],
            generated_at=now,
            modified_at=now,
            status=ProvenanceStatus.GENERATED,
            tokens_used=tokens_used,
            metadata=metadata or {},
        )
        self._entries[entry_id] = entry

        if file_path not in self._index_by_file:
            self._index_by_file[file_path] = []
        self._index_by_file[file_path].append(entry_id)

        return entry

    def update_status(
        self,
        entry_id: str,
        new_status: ProvenanceStatus,
        trust_score: Optional[float] = None,
    ) -> Optional[ProvenanceEntry]:
        """Update the status and trust score of a provenance entry."""
        entry = self._entries.get(entry_id)
        if not entry:
            return None
        entry.status = new_status
        entry.modified_at = datetime.now(timezone.utc)
        if trust_score is not None:
            entry.trust_score = trust_score
        return entry

    def get_entry(self, entry_id: str) -> Optional[ProvenanceEntry]:
        """Get a single provenance entry by ID."""
        return self._entries.get(entry_id)

    def get_file_entries(self, file_path: str) -> list[ProvenanceEntry]:
        """Get all provenance entries for a given file."""
        entry_ids = self._index_by_file.get(file_path, [])
        return [self._entries[eid] for eid in entry_ids if eid in self._entries]

    def get_stale_entries(self, hours: int = 72) -> list[ProvenanceEntry]:
        """Get entries that have not been reviewed within the given hours."""
        cutoff = datetime.now(timezone.utc)
        return [
            e for e in self._entries.values()
            if e.status == ProvenanceStatus.GENERATED
            and (cutoff - e.generated_at).total_seconds() > hours * 3600
        ]

    def generate_report(self, file_path: Optional[str] = None) -> ProvenanceReport:
        """Generate a provenance report for a file or the entire project."""
        if file_path:
            entries = self.get_file_entries(file_path)
        else:
            entries = list(self._entries.values())

        by_provider: dict[str, int] = {}
        by_status: dict[str, int] = {}
        scores = []
        total_tokens = 0
        stale_count = 0

        for e in entries:
            by_provider[e.provider.value] = by_provider.get(e.provider.value, 0) + 1
            by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
            if e.trust_score > 0:
                scores.append(e.trust_score)
            total_tokens += e.tokens_used
            if e.is_stale:
                stale_count += 1

        return ProvenanceReport(
            total_entries=len(entries),
            by_provider=by_provider,
            by_status=by_status,
            avg_trust_score=sum(scores) / len(scores) if scores else 0.0,
            total_tokens_consumed=total_tokens,
            stale_entries=stale_count,
            entries=entries,
        )

    def stats(self) -> dict[str, Any]:
        """Get engine statistics."""
        return {
            "total_entries": len(self._entries),
            "tracked_files": len(self._index_by_file),
            "stale_count": len(self.get_stale_entries()),
        }