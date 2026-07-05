# CodeTruth

> AI-Generated Code Trust & Verification Platform — Bridge the gap between AI code generation and production deployment.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## What is CodeTruth?

**CodeTruth** is the first open-source platform designed to bridge the critical trust gap between AI-generated code and production deployment. As AI coding tools flood repositories with generated code, organizations face an unprecedented challenge: **how do you trust code you didn't write?**

CodeTruth provides the missing infrastructure layer — provenance tracking, multi-dimensional trust scoring, knowledge graph analysis, quality gate pipelines, and persistent memory — to make AI-generated code auditable, verifiable, and trustworthy.

### Why CodeTruth?

- **96% of developers** don't fully trust AI-generated code
- **AI coding tools produce 55% more code** but review capacity hasn't scaled
- **Agent multi-step task success rate** is only 77%
- **No standard exists** for tracking AI code lineage or quality

CodeTruth solves this by building the **governance layer** the AI coding ecosystem desperately needs.

## Key Features

### Provenance Engine
Track every AI-generated code block with complete lineage — which model, what prompt, when, and in what context. Never lose the "who wrote what" trail again.

### Trust Scoring Engine
Multi-dimensional quality assessment across **6 axes**: Quality, Security, Testability, Performance, Documentation, and Maintainability. Get an objective trust score (0-100) for every code block.

### Code Knowledge Graph
AST-based dependency mapping showing classes, functions, imports, and call chains. Understand how AI code connects to your existing codebase.

### Quality Gate Pipeline
Configurable verification checkpoints with **10 built-in rules** covering security, quality, and architecture. Block deployments that don't meet your standards.

### Token Optimizer
Intelligent context compression saving **60-95% of tokens** while preserving semantic meaning. Dramatically reduce AI API costs.

### Memory Layer
Persistent context memory with structured memory tuples (who/what/when/where/why). AI tools remember your codebase across sessions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CodeTruth Platform                       │
├─────────────────────────────────────────────────────────────────┤
│  CLI  │  REST API  │  Web Dashboard  │  IDE Plugin (coming)     │
├─────────────────────────────────────────────────────────────────┤
│                    Orchestration Layer                            │
├──────────┬──────────┬──────────┬──────────┬────────────────────┤
│Provenance│ Scoring  │  Graph   │Optimizer │   Memory Layer     │
│ Engine   │ Engine   │ Engine   │ Engine   │                    │
├──────────┴──────────┴──────────┴──────────┴────────────────────┤
│                    Quality Gate Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                    Data Layer (SQLite + LanceDB)                 │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Installation

```bash
pip install codetruth
```

### CLI Usage

```bash
# Analyze a file's trust score
codetruth analyze src/main.py

# Scan entire directory
codetruth scan ./src

# Optimize tokens for AI consumption
codetruth optimize src/main.py --strategy moderate

# Generate comprehensive report
codetruth report

# Start API server
codetruth serve
```

### Python API

```python
from codetruth.engine.scoring import TrustScoringEngine
from codetruth.engine.optimizer import TokenOptimizer

# Analyze code trust
engine = TrustScoringEngine()
score = engine.assess("func1", "calculate_sum", "function", code, "python")
print(f"Trust Score: {score.overall_score}/100")

# Optimize for AI
optimizer = TokenOptimizer()
result = optimizer.auto_optimize(large_code)
print(f"Saved {result.tokens_saved} tokens ({result.compression_ratio:.0%})")
```

### REST API

```bash
# Start server
codetruth serve

# Analyze code
curl -X POST http://localhost:8742/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"code": "def hello(): return \"world\"", "language": "python"}'

# API docs available at http://localhost:8742/docs
```

## Project Structure

```
github_big_proj17/
├── codetruth/              # Main package
│   ├── __init__.py
│   ├── config/             # Configuration management
│   ├── engine/             # Core engines
│   │   ├── provenance/     # Code lineage tracking
│   │   ├── graph/          # Knowledge graph
│   │   ├── scoring/        # Trust scoring
│   │   └── optimizer/      # Token compression
│   ├── memory/             # Persistent memory layer
│   ├── gates/              # Quality gate pipeline
│   ├── cli/                # Command-line interface
│   ├── api/                # FastAPI REST API
│   └── web/                # Web dashboard
├── tests/                  # Test suite
├── frontend/               # Web dashboard (React)
├── docs/                   # Documentation
├── skills/                 # Built-in skills
├── examples/               # Usage examples
├── pyproject.toml          # Project configuration
├── Makefile                # Build automation
├── README.md               # English documentation
├── README_CN.md            # Chinese documentation
├── ARCHITECTURE.md         # Architecture details
├── CONTRIBUTING.md         # Contribution guide
└── LICENSE                 # MIT License
```

## 5W1H Architecture

| Dimension | Description |
|-----------|-------------|
| **What** | AI-Generated Code Trust & Verification Platform |
| **Why** | 96% of developers don't trust AI code; no standard governance exists |
| **Who** | Development teams, engineering managers, DevOps, security teams |
| **When** | Integrated into CI/CD pipeline, pre-commit hooks, and PR reviews |
| **Where** | CLI, REST API, IDE plugin, CI/CD integration |
| **How** | Provenance tracking + trust scoring + knowledge graph + quality gates |

## Technology Stack

- **Backend**: Python 3.10+, FastAPI, Pydantic
- **Database**: SQLite (default), LanceDB (vector), PostgreSQL (production)
- **Frontend**: React, Tailwind CSS
- **CLI**: Click, Rich
- **Testing**: pytest, coverage
- **Code Quality**: Black, Ruff, mypy

## Inspiration

CodeTruth draws inspiration from several groundbreaking open-source projects:

- **Hermes Agent** (179K stars): Agentic architecture with persistent memory
- **CodeGraph** (21K stars): AST-based dependency analysis reducing token usage 57%
- **SuperMemory** (25K stars): Structured memory tuples model
- **Headroom** (10K stars): Context compression saving 60-95% tokens
- **PR-Agent**: Automated code review and quality gates
- **ECC** (205K stars): Multi-layer AI coding platform architecture

## Roadmap

- [x] Core engines (provenance, scoring, graph, optimizer)
- [x] Quality gate pipeline
- [x] REST API and CLI
- [x] Web dashboard
- [ ] IDE plugins (VS Code, JetBrains)
- [ ] GitHub/GitLab CI/CD integration
- [ ] Vector-based semantic search
- [ ] Multi-language support (JS/TS, Java, Rust, Go)
- [ ] Team-based risk dashboards
- [ ] Blockchain-anchored provenance (immutable audit trail)
- [ ] LLM-as-judge for automated code review

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines. We welcome all contributions — code, docs, issues, and ideas!

```bash
git clone https://github.com/lanekingkong/codetruth.git
cd codetruth
pip install -e ".[dev]"
pre-commit install
pytest
```

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <b>CodeTruth</b> — Making AI-generated code auditable, verifiable, and trustworthy.
</p>