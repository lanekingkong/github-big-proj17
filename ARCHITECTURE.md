# CodeTruth Architecture

## Overview

CodeTruth is designed as a modular, layered platform for AI-generated code governance. This document describes the system architecture, design decisions, and component interactions.

## High-Level Architecture

```
                    ┌─────────────────────────────────────┐
                    │            User Interfaces           │
                    │  ┌─────────┐ ┌─────┐ ┌───────────┐ │
                    │  │   CLI   │ │ API │ │ Dashboard │ │
                    │  └─────────┘ └─────┘ └───────────┘ │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │        Orchestration Layer           │
                    │  ┌─────────────────────────────────┐ │
                    │  │      Workflow Orchestrator       │ │
                    │  │  (task dispatch, result merge,   │ │
                    │  │   pipeline coordination)          │ │
                    │  └─────────────────────────────────┘ │
                    └─────────────────┬───────────────────┘
                                      │
        ┌─────────────┬───────────────┼───────────────┬─────────────┐
        │             │               │               │             │
  ┌─────▼────┐ ┌──────▼──────┐ ┌──────▼──────┐ ┌─────▼────┐ ┌─────▼────┐
  │Provenance│ │   Scoring   │ │   Graph     │ │Optimizer │ │  Memory  │
  │  Engine  │ │   Engine    │ │   Engine    │ │  Engine  │ │  Layer   │
  └─────┬────┘ └──────┬──────┘ └──────┬──────┘ └─────┬────┘ └─────┬────┘
        │             │               │               │             │
        └─────────────┴───────────────┼───────────────┴─────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │        Quality Gate Pipeline         │
                    │  ┌─────────────────────────────────┐ │
                    │  │  Rule Engine → Check → Report    │ │
                    │  └─────────────────────────────────┘ │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │            Data Layer                │
                    │  ┌──────────┐  ┌──────────────────┐ │
                    │  │  SQLite  │  │    LanceDB       │ │
                    │  │(metadata)│  │(vector storage)  │ │
                    │  └──────────┘  └──────────────────┘ │
                    └─────────────────────────────────────┘
```

## Component Design

### 1. Provenance Engine

**Purpose**: Track the complete lineage of AI-generated code.

**Data Model**:
- `ProvenanceEntry`: Contains file path, line range, AI provider, model, prompt hash, generation timestamp, modification history
- `ProvenanceReport`: Aggregates statistics by file, provider, time period

**Key Design Decisions**:
- Uses content-hash based deduplication for prompts
- Supports multiple AI providers (Claude, ChatGPT, Cursor, Copilot, Codex, Gemini)
- Status lifecycle: GENERATED → REVIEWED → MODIFIED → DEPLOYED
- Immutable audit trail: all modifications append, never overwrite

**Inspired by**: PR-Agent's code review pipeline, ECC's security layer

### 2. Trust Scoring Engine

**Purpose**: Compute objective trust scores for code blocks.

**Scoring Dimensions** (configurable weights):

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Quality | 25% | Code complexity, naming, structure |
| Security | 25% | Secrets, injection, unsafe operations |
| Testability | 15% | Test coverage, mockability |
| Performance | 15% | Algorithm complexity, resource usage |
| Documentation | 10% | Docstrings, comments, type hints |
| Maintainability | 10% | Modularity, coupling, readability |

**Score Levels**:
- 90-100: Excellent
- 75-89: Good
- 60-74: Fair
- 40-59: Warning
- 0-39: Critical

**Key Design Decisions**:
- Customizable dimension weights for different team priorities
- Each dimension independently scored then weighted-averaged
- AI-generated percentage influences scoring (bias toward human-reviewed)
- Built-in heuristics for Python code; extensible for other languages

**Inspired by**: SonarQube quality metrics, CodeGraph AST analysis

### 3. Knowledge Graph Engine

**Purpose**: Build and query a dependency graph of code entities.

**Node Types**: FILE, MODULE, CLASS, FUNCTION, METHOD, VARIABLE, IMPORT
**Edge Types**: CONTAINS, IMPORTS, CALLS, INHERITS, REFERENCES, DEPENDS_ON

**Key Design Decisions**:
- AST-based parsing for accurate dependency extraction
- Bidirectional edge traversal for impact analysis
- BFS-based shortest path for dependency chain analysis
- Support for AI-generated node marking

**Inspired by**: CodeGraph (21K stars) — reduces token usage 57% through dependency-aware context selection

### 4. Token Optimizer

**Purpose**: Compress code context for efficient AI consumption.

**Compression Strategies**:

| Strategy | Token Reduction | Use Case |
|----------|----------------|----------|
| MINIMAL | 10-30% | Short code, simple files |
| MODERATE | 30-60% | Medium complexity |
| AGGRESSIVE | 50-80% | Large projects |
| SEMANTIC | 40-95% | Mixed code+documentation |

**Key Design Decisions**:
- Multi-strategy pipeline with auto-selection based on input size
- Comment stripping, whitespace normalization, dead code removal
- Semantic compression keeps function signatures and key logic
- Cost estimation model based on popular LLM pricing

**Inspired by**: Headroom (10K stars) — 60-95% token reduction with semantic preservation

### 5. Memory Layer

**Purpose**: Persistent context for AI tools across sessions.

**Memory Types**: FACT, PREFERENCE, DECISION, CONTEXT, PATTERN, MISTAKE

**Structured Memory Tuple**: (who, what, when, where, why)

**Key Design Decisions**:
- SQLite-backed with optional LanceDB vector indexing
- Importance-weighted retrieval (0.0-1.0)
- TTL-based auto-expiry for stale memories
- Memory Spaces for organizational grouping
- Tag-based categorization

**Inspired by**: SuperMemory (25K stars) MemoryOS, Hermes Agent persistent memory

### 6. Quality Gate Pipeline

**Purpose**: Block deployments that don't meet quality standards.

**10 Built-in Rules**:

| Rule | Severity | Category |
|------|----------|----------|
| No Hardcoded Secrets | BLOCKER | security |
| Input Validation | CRITICAL | security |
| Injection Prevention | BLOCKER | security |
| Code Complexity | MAJOR | quality |
| Line Length | MINOR | quality |
| Test Presence | MAJOR | coverage |
| Documentation | MINOR | documentation |
| N+1 Query Prevention | CRITICAL | performance |
| Style Consistency | MINOR | style |
| No Circular Dependencies | CRITICAL | architecture |

**Key Design Decisions**:
- Rules are individually configurable (enable/disable, severity override)
- BLOCKER severity failures → gate FAILED (block deployment)
- CRITICAL severity failures → gate FAILED
- MAJOR/MINOR → gate WARNING (deploy with caution)
- Extensible rule system: add custom rules as GateRule instances

**Inspired by**: SonarQube Quality Gates, PR-Agent automated review

## Data Flow

### Analysis Pipeline

```
User submits code
       │
       ▼
┌──────────────────┐
│ 1. Parse & Normalize│  ← AST parsing, language detection
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ 2. Provenance Record│  ← Track origin, provider, prompt
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ 3. Build Graph    │  ← Extract dependencies
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ 4. Score & Assess │  ← 6-dimension trust scoring
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ 5. Quality Gates  │  ← Pass/Fail/Warning
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ 6. Store Memory   │  ← Persist context
└──────┬───────────┘
       │
       ▼
   Trust Report
```

## Technology Choices

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Core Language | Python 3.10+ | Rich ecosystem, AI/ML tooling |
| API Framework | FastAPI | Performance, auto-docs, async |
| Data Validation | Pydantic v2 | Type safety, serialization |
| CLI Framework | Click | Composable commands |
| Terminal UI | Rich | Beautiful CLI output |
| Default DB | SQLite | Zero-config, embedded |
| Vector DB | LanceDB | Columnar, fast, embedded |
| Testing | pytest | Industry standard |
| Linting | Ruff | 10-100x faster than alternatives |
| Formatting | Black | Deterministic, no-config |

## Extensibility

### Adding a New Trust Dimension

1. Add dimension to `Dimension` enum in `engine/scoring/__init__.py`
2. Implement scoring logic in `TrustScoringEngine._assess_dimension()`
3. Add to default weights
4. Update tests

### Adding a New Quality Gate Rule

```python
from codetruth.gates import GateRule, GateSeverity

rule = GateRule(
    rule_id="my_custom_rule",
    name="My Custom Rule",
    description="What this rule checks",
    category="custom",
    severity=GateSeverity.MAJOR,
)
pipeline.add_rule(rule)
```

### Adding a New Compression Strategy

1. Add strategy to `CompressionStrategy` enum
2. Implement method on `TokenOptimizer`
3. Add to `auto_optimize()` selection logic

## Performance Considerations

- **SQLite**: Suitable for up to ~100K provenance entries; migrate to PostgreSQL beyond
- **LanceDB**: Designed for million-scale vector searches
- **Token Optimizer**: Processes ~10K tokens/sec on CPU
- **AST Parsing**: ~50 files/sec for medium Python files
- **API**: Async FastAPI handles ~1000 req/sec on standard hardware

## Security

- No network calls for code analysis (fully local)
- API keys and secrets never persisted in plaintext
- SQLite database files can be encrypted at rest
- Quality gates enforce security best practices pre-deployment
- Provenance trail is append-only (immutable audit)