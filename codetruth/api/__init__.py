"""
CodeTruth FastAPI REST API.

Provides endpoints for:
- Project analysis and trust scoring
- Provenance tracking and reporting
- Knowledge graph queries
- Quality gate management
- Memory layer access
- Token optimization
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field

from ..engine.provenance import ProvenanceEngine, AIProvider, ProvenanceStatus
from ..engine.graph import KnowledgeGraphEngine, NodeType
from ..engine.scoring import TrustScoringEngine, Dimension
from ..engine.optimizer import TokenOptimizer, CompressionStrategy
from ..memory import MemoryLayer, MemoryType
from ..gates import GatePipeline
from ..config import get_settings


# -- Request/Response Models --

class AnalyzeRequest(BaseModel):
    code: str
    file_path: str = ""
    language: str = "python"
    provider: str = "unknown"
    model: str = ""
    prompt: str = ""
    ai_generated_pct: float = 0.0


class TrustScoreResponse(BaseModel):
    entity_id: str
    entity_name: str
    overall_score: float
    level: str
    dimensions: dict
    recommendations: list[str]


class OptimizeRequest(BaseModel):
    text: str
    strategy: str = "moderate"


class MemoryRequest(BaseModel):
    memory_type: str
    subject: str
    content: str
    context: str = ""
    importance: float = 0.5
    tags: list[str] = []


# -- App Factory --

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="CodeTruth API",
        description="AI-Generated Code Trust & Verification Platform",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize engines
    provenance = ProvenanceEngine(settings.get_db_path())
    graph = KnowledgeGraphEngine(settings.get_db_path())
    scoring = TrustScoringEngine(
        pass_threshold=settings.trust_threshold_pass,
        warn_threshold=settings.trust_threshold_warn,
    )
    optimizer = TokenOptimizer(
        target_ratio=settings.token_compression_target,
        max_context_tokens=settings.max_context_tokens,
    )
    memory_layer = MemoryLayer(
        settings.get_db_path(),
        max_entries=settings.memory_max_entries,
        ttl_days=settings.memory_ttl_days,
    )
    gates = GatePipeline(name="default").build_default_rules()

    # -- Health --

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "1.0.0", "timestamp": datetime.now(timezone.utc).isoformat()}

    # -- Analysis --

    @app.post("/api/analyze", response_model=TrustScoreResponse)
    async def analyze_code(req: AnalyzeRequest):
        """Analyze code and return trust score."""
        import hashlib
        entity_id = hashlib.sha256(
            f"{req.file_path}:{req.code[:100]}".encode()
        ).hexdigest()[:16]

        trust = scoring.assess(
            entity_id=entity_id,
            entity_name=req.file_path or "inline_code",
            entity_type="code_block",
            code=req.code,
            language=req.language,
            ai_generated_pct=req.ai_generated_pct,
        )

        return TrustScoreResponse(
            entity_id=trust.entity_id,
            entity_name=trust.entity_name,
            overall_score=trust.overall_score,
            level=trust.level.value,
            dimensions=trust.to_dict()["dimensions"],
            recommendations=trust.recommendations,
        )

    @app.post("/api/analyze/batch")
    async def analyze_batch(files: list[AnalyzeRequest]):
        """Batch analyze multiple code files."""
        results = []
        for f in files:
            result = await analyze_code(f)
            results.append(result)
        return {"total": len(results), "results": [r.model_dump() for r in results]}

    # -- Optimization --

    @app.post("/api/optimize")
    async def optimize(req: OptimizeRequest):
        """Optimize/compress text for AI consumption."""
        try:
            strategy = CompressionStrategy(req.strategy)
        except ValueError:
            raise HTTPException(400, f"Unknown strategy: {req.strategy}")
        result = optimizer.optimize(req.text, strategy)
        return result.to_dict()

    @app.get("/api/optimize/report")
    async def get_optimization_report():
        """Get optimization statistics."""
        report = optimizer.get_report()
        return {
            "total_original_tokens": report.total_original_tokens,
            "total_compressed_tokens": report.total_compressed_tokens,
            "overall_compression_ratio": round(report.overall_compression_ratio, 3),
            "total_cost_saved": report.total_cost_saved,
            "operations": report.operations,
        }

    # -- Provenance --

    @app.get("/api/provenance/file")
    async def get_file_provenance(file_path: str):
        """Get provenance entries for a file."""
        entries = provenance.get_file_entries(file_path)
        return {"file_path": file_path, "entries": [e.to_dict() for e in entries]}

    @app.get("/api/provenance/report")
    async def get_provenance_report(file_path: Optional[str] = None):
        """Get a provenance report."""
        report = provenance.generate_report(file_path)
        return report.to_dict()

    @app.get("/api/provenance/stale")
    async def get_stale_entries(hours: int = 72):
        """Get stale provenance entries."""
        entries = provenance.get_stale_entries(hours)
        return {"stale_count": len(entries), "entries": [e.to_dict() for e in entries[:50]]}

    # -- Knowledge Graph --

    @app.get("/api/graph/stats")
    async def get_graph_stats():
        """Get knowledge graph statistics."""
        return graph.stats()

    @app.get("/api/graph/query")
    async def query_graph(name: str, node_type: Optional[str] = None):
        """Query the knowledge graph."""
        nt = NodeType(node_type) if node_type else None
        nodes = graph.query_node(name, nt)
        return {"query": name, "results": [n.to_dict() for n in nodes[:50]]}

    @app.get("/api/graph/neighbors")
    async def get_neighbors(node_id: str, depth: int = 1):
        """Get neighboring nodes."""
        nodes = graph.get_neighbors(node_id, depth)
        return {"node_id": node_id, "depth": depth, "neighbors": [n.to_dict() for n in nodes]}

    @app.get("/api/graph/path")
    async def find_path(source_id: str, target_id: str):
        """Find shortest path between two nodes."""
        path = graph.find_path(source_id, target_id)
        return {"source": source_id, "target": target_id, "path": path}

    # -- Quality Gates --

    @app.get("/api/gates/rules")
    async def get_gate_rules():
        """Get all quality gate rules."""
        return {
            "rules": [
                {
                    "rule_id": r.rule_id,
                    "name": r.name,
                    "category": r.category,
                    "severity": r.severity.value,
                    "enabled": r.enabled,
                }
                for r in gates.get_rules()
            ]
        }

    @app.post("/api/gates/check")
    async def run_gate_check(req: AnalyzeRequest):
        """Run quality gate checks on code."""
        result = gates.check(
            code=req.code,
            file_path=req.file_path,
            ai_generated_pct=req.ai_generated_pct,
        )
        return result.to_dict()

    @app.get("/api/gates/history")
    async def get_gate_history(limit: int = 10):
        """Get quality gate check history."""
        return {"history": [h.to_dict() for h in gates.get_history(limit)]}

    # -- Memory --

    @app.post("/api/memory")
    async def store_memory(req: MemoryRequest):
        """Store a memory entry."""
        try:
            mt = MemoryType(req.memory_type)
        except ValueError:
            raise HTTPException(400, f"Unknown memory type: {req.memory_type}")
        entry = memory_layer.remember(
            memory_type=mt,
            subject=req.subject,
            content=req.content,
            context=req.context,
            importance=req.importance,
            tags=req.tags,
        )
        return entry.to_dict()

    @app.get("/api/memory")
    async def recall_memory(
        memory_type: Optional[str] = None,
        tag: Optional[str] = None,
        subject_contains: Optional[str] = None,
        limit: int = 20,
    ):
        """Recall memory entries."""
        mt = MemoryType(memory_type) if memory_type else None
        results = memory_layer.recall(
            memory_type=mt,
            tag=tag,
            subject_contains=subject_contains,
            limit=limit,
        )
        return {"count": len(results), "results": [r.to_dict() for r in results]}

    @app.get("/api/memory/stats")
    async def get_memory_stats():
        """Get memory statistics."""
        return memory_layer.stats()

    # -- Dashboard HTML --

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve the CodeTruth dashboard."""
        from pathlib import Path
        dashboard_path = Path(__file__).parent.parent.parent / "frontend" / "dist" / "index.html"
        if dashboard_path.exists():
            return dashboard_path.read_text(encoding="utf-8")
        # Fallback dashboard
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CodeTruth Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'JetBrains Mono', 'Fira Code', monospace; background: #0a0e17; color: #c9d1d9; }
        .container { max-width: 1200px; margin: 0 auto; padding: 40px 20px; }
        h1 { font-size: 2.5rem; background: linear-gradient(135deg, #00f0ff, #00ff88); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { color: #8b949e; margin: 10px 0 30px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 24px; margin-bottom: 20px; }
        .card h2 { color: #00f0ff; font-size: 1.2rem; margin-bottom: 12px; }
        .card p, .card li { color: #8b949e; line-height: 1.6; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .endpoint { background: #0d1117; padding: 12px; border-radius: 4px; margin: 8px 0; font-size: 0.9rem; }
        .method { color: #00ff88; font-weight: bold; }
        .path { color: #00f0ff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CodeTruth</h1>
        <p class="subtitle">AI-Generated Code Trust & Verification Platform v1.0.0</p>

        <div class="card">
            <h2>API Endpoints</h2>
            <div class="endpoint"><span class="method">POST</span> <span class="path">/api/analyze</span> - Trust score analysis</div>
            <div class="endpoint"><span class="method">POST</span> <span class="path">/api/optimize</span> - Token optimization</div>
            <div class="endpoint"><span class="method">GET</span> <span class="path">/api/provenance/report</span> - Provenance report</div>
            <div class="endpoint"><span class="method">GET</span> <span class="path">/api/graph/stats</span> - Graph statistics</div>
            <div class="endpoint"><span class="method">POST</span> <span class="path">/api/gates/check</span> - Quality gate check</div>
            <div class="endpoint"><span class="method">POST/GET</span> <span class="path">/api/memory</span> - Memory layer</div>
            <div class="endpoint"><span class="method">GET</span> <span class="path">/docs</span> - Swagger UI</div>
        </div>

        <div class="grid">
            <div class="card">
                <h2>Trust Scoring</h2>
                <p>Multi-dimensional code quality assessment across Quality, Security, Testability, Performance, Documentation, and Maintainability.</p>
            </div>
            <div class="card">
                <h2>Provenance Tracking</h2>
                <p>Complete lineage tracking for every AI-generated code block: which model, what prompt, when, and in what context.</p>
            </div>
            <div class="card">
                <h2>Knowledge Graph</h2>
                <p>AST-based code dependency visualization showing classes, functions, imports, and call chains.</p>
            </div>
            <div class="card">
                <h2>Quality Gates</h2>
                <p>Configurable verification checkpoints with 10 built-in rules covering security, quality, and architecture.</p>
            </div>
            <div class="card">
                <h2>Token Optimizer</h2>
                <p>Intelligent context compression saving 60-95% of tokens while preserving semantic meaning.</p>
            </div>
            <div class="card">
                <h2>Memory Layer</h2>
                <p>Persistent AI context with structured memory tuples (who/what/when/where/why).</p>
            </div>
        </div>
    </div>
</body>
</html>"""

    return app


app = create_app()


def main():
    """Entry point for uvicorn."""
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "codetruth.api:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=False,
    )


if __name__ == "__main__":
    main()