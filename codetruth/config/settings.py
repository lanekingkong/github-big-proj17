"""
Configuration management for CodeTruth.
Uses pydantic-settings for environment variable and file-based configuration.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings for CodeTruth platform."""

    model_config = SettingsConfigDict(
        env_prefix="CODETRUTH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    # Core paths
    data_dir: Path = Field(
        default_factory=lambda: Path.home() / ".codetruth",
        description="Root data directory for CodeTruth storage",
    )
    db_path: Optional[Path] = Field(
        default=None,
        description="SQLite database path (defaults to data_dir/codetruth.db)",
    )

    # LanceDB for vector storage
    vector_db_path: Optional[Path] = Field(
        default=None,
        description="LanceDB path for vector embeddings",
    )

    # Trust scoring thresholds
    trust_threshold_pass: float = Field(
        default=70.0,
        ge=0.0,
        le=100.0,
        description="Minimum trust score to pass quality gates",
    )
    trust_threshold_warn: float = Field(
        default=50.0,
        ge=0.0,
        le=100.0,
        description="Trust score below which warnings are raised",
    )

    # Token optimizer settings
    token_compression_target: float = Field(
        default=0.7,
        ge=0.1,
        le=0.95,
        description="Target compression ratio for token optimizer",
    )
    max_context_tokens: int = Field(
        default=128000,
        description="Maximum context tokens before compression triggers",
    )

    # Knowledge graph settings
    graph_max_nodes: int = Field(
        default=50000,
        description="Maximum nodes in code knowledge graph",
    )
    graph_index_languages: list[str] = Field(
        default_factory=lambda: [
            "python", "typescript", "javascript", "java",
            "rust", "go", "cpp", "c", "csharp",
        ],
        description="Languages for AST-based graph indexing",
    )

    # API settings
    api_host: str = Field(default="127.0.0.1", description="API server host")
    api_port: int = Field(default=8742, description="API server port")
    api_workers: int = Field(default=1, description="Number of API workers")

    # Memory layer
    memory_max_entries: int = Field(
        default=100000,
        description="Maximum memory entries per project",
    )
    memory_ttl_days: int = Field(
        default=90,
        description="Days before memory entries are considered stale",
    )

    # Integrations
    supported_ai_tools: list[str] = Field(
        default_factory=lambda: [
            "claude_code", "cursor", "github_copilot",
            "codex", "windsurf", "continue_dev",
        ],
        description="Supported AI coding tools for integration",
    )

    def get_db_path(self) -> str:
        """Get the resolved database path."""
        if self.db_path:
            return str(self.db_path)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return str(self.data_dir / "codetruth.db")

    def get_vector_db_path(self) -> str:
        """Get the resolved vector database path."""
        if self.vector_db_path:
            return str(self.vector_db_path)
        vec_dir = self.data_dir / "vectors"
        vec_dir.mkdir(parents=True, exist_ok=True)
        return str(vec_dir)


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings