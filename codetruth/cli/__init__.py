"""
CodeTruth CLI - command-line interface for code trust verification.

Usage:
    codetruth analyze <file>          Analyze code trust
    codetruth optimize <file>         Optimize tokens
    codetruth scan <dir>              Scan directory
    codetruth report                  Generate trust report
    codetruth serve                   Start API server
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..engine.provenance import ProvenanceEngine, AIProvider
from ..engine.graph import KnowledgeGraphEngine
from ..engine.scoring import TrustScoringEngine
from ..engine.optimizer import TokenOptimizer, CompressionStrategy
from ..memory import MemoryLayer
from ..gates import GatePipeline
from ..config import get_settings

console = Console()


def _init_engines():
    """Initialize all engines."""
    settings = get_settings()
    return {
        "provenance": ProvenanceEngine(settings.get_db_path()),
        "graph": KnowledgeGraphEngine(settings.get_db_path()),
        "scoring": TrustScoringEngine(
            pass_threshold=settings.trust_threshold_pass,
            warn_threshold=settings.trust_threshold_warn,
        ),
        "optimizer": TokenOptimizer(
            target_ratio=settings.token_compression_target,
        ),
        "memory": MemoryLayer(settings.get_db_path()),
        "gates": GatePipeline(name="cli").build_default_rules(),
        "settings": settings,
    }


@click.group()
@click.version_option(version="1.0.0", prog_name="CodeTruth")
def cli():
    """CodeTruth - AI-Generated Code Trust & Verification Platform.

    Bridge the gap between AI code generation and production deployment.
    """
    pass


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--language", "-l", default="python", help="Programming language")
@click.option("--provider", "-p", default="unknown", help="AI provider")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON")
def analyze(file_path: str, language: str, provider: str, json_output: bool):
    """Analyze a file and compute its trust score."""
    engines = _init_engines()
    scoring = engines["scoring"]
    gates = engines["gates"]

    code = Path(file_path).read_text(encoding="utf-8", errors="replace")
    file_name = Path(file_path).name

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(f"Analyzing {file_name}...", total=None)
        trust = scoring.assess(
            entity_id=file_path,
            entity_name=file_name,
            entity_type="file",
            code=code,
            language=language,
        )
        gate_result = gates.check(code=code, file_path=file_path)

    if json_output:
        console.print_json(json.dumps({
            "trust_score": trust.to_dict(),
            "gate_check": gate_result.to_dict(),
        }, indent=2))
        return

    # Rich formatted output
    level_colors = {
        "excellent": "green",
        "good": "cyan",
        "fair": "yellow",
        "warning": "orange1",
        "critical": "red",
    }
    color = level_colors.get(trust.level.value, "white")

    console.print(Panel.fit(
        f"[bold {color}]{trust.overall_score}/100 - {trust.level.value.upper()}[/]",
        title=f"[bold]Trust Score: {file_name}[/]",
        border_style=color,
    ))

    # Dimension table
    dim_table = Table(title="Dimension Scores", title_style="bold")
    dim_table.add_column("Dimension", style="cyan")
    dim_table.add_column("Score", justify="right")
    dim_table.add_column("Issues", style="yellow")

    for dim, ds in trust.dimensions.items():
        issues_str = ", ".join(ds.issues[:3]) if ds.issues else "-"
        if len(ds.issues) > 3:
            issues_str += f" +{len(ds.issues) - 3} more"
        dim_table.add_row(dim.value, f"{ds.score:.1f}", issues_str)

    console.print(dim_table)

    # Gate result
    gate_color = "green" if gate_result.overall_status.value == "passed" else "yellow" if gate_result.overall_status.value == "warning" else "red"
    console.print(f"\n[bold]Quality Gate:[/] [{gate_color}]{gate_result.overall_status.value.upper()}[/] "
                  f"({gate_result.pass_count}P/{gate_result.fail_count}F/{gate_result.warn_count}W/{gate_result.skip_count}S)")

    # Recommendations
    if trust.recommendations:
        console.print("\n[bold]Recommendations:[/]")
        for rec in trust.recommendations[:5]:
            console.print(f"  [yellow]•[/] {rec}")


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--strategy", "-s", default="moderate",
              type=click.Choice(["minimal", "moderate", "aggressive", "semantic"]))
@click.option("--json", "json_output", is_flag=True)
def optimize(file_path: str, strategy: str, json_output: bool):
    """Optimize/compress file content for AI consumption."""
    engines = _init_engines()
    optimizer = engines["optimizer"]

    text = Path(file_path).read_text(encoding="utf-8", errors="replace")
    strat = CompressionStrategy(strategy)
    result = optimizer.optimize(text, strat)

    if json_output:
        console.print_json(json.dumps(result.to_dict(), indent=2))
        return

    ratio_pct = result.compression_ratio * 100
    console.print(Panel.fit(
        f"Original: [bold]{result.original_tokens:,}[/] tokens\n"
        f"Compressed: [bold]{result.compressed_tokens:,}[/] tokens\n"
        f"Saved: [bold green]{result.tokens_saved:,}[/] tokens ([bold]{ratio_pct:.1f}%[/])\n"
        f"Est. Cost Saved: [bold green]${result.cost_saved_estimate:.4f}[/]\n"
        f"Strategy: [cyan]{result.strategy_used.value}[/]",
        title="[bold]Token Optimization Result[/]",
        border_style="green",
    ))

    if result.warnings:
        for w in result.warnings:
            console.print(f"[yellow]Warning: {w}[/]")


@cli.command()
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option("--language", "-l", default="python", help="Filter by language")
@click.option("--json", "json_output", is_flag=True)
def scan(directory: str, language: str, json_output: bool):
    """Scan a directory and compute trust scores for all files."""
    engines = _init_engines()
    scoring = engines["scoring"]

    dir_path = Path(directory)
    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".java": "java", ".rs": "rust", ".go": "go",
        ".cpp": "cpp", ".c": "c", ".cs": "csharp",
    }

    results = []
    files_scanned = 0

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        task = progress.add_task(f"Scanning {directory}...", total=None)

        for file_path in dir_path.rglob("*"):
            if file_path.suffix in ext_map:
                try:
                    code = file_path.read_text(encoding="utf-8", errors="replace")
                    trust = scoring.assess(
                        entity_id=str(file_path),
                        entity_name=file_path.name,
                        entity_type="file",
                        code=code,
                        language=ext_map[file_path.suffix],
                    )
                    results.append({
                        "file": str(file_path.relative_to(dir_path)),
                        "score": trust.overall_score,
                        "level": trust.level.value,
                    })
                    files_scanned += 1
                except Exception:
                    pass

    if json_output:
        summary = {
            "files_scanned": files_scanned,
            "avg_score": round(sum(r["score"] for r in results) / len(results), 1) if results else 0,
            "results": results,
        }
        console.print_json(json.dumps(summary, indent=2))
        return

    # Summary table
    console.print(f"\n[bold]Scan Complete: {files_scanned} files analyzed[/]\n")

    table = Table(title="Directory Trust Scores", title_style="bold")
    table.add_column("File", style="cyan", no_wrap=True)
    table.add_column("Score", justify="right")
    table.add_column("Level")

    for r in sorted(results, key=lambda x: x["score"])[:30]:
        color = "green" if r["score"] >= 75 else "yellow" if r["score"] >= 60 else "red"
        table.add_row(r["file"], f"[{color}]{r['score']:.1f}[/]", f"[{color}]{r['level']}[/]")

    console.print(table)

    if results:
        avg = sum(r["score"] for r in results) / len(results)
        console.print(f"\n[bold]Average Trust Score: {avg:.1f}/100[/]")


@cli.command()
@click.option("--json", "json_output", is_flag=True)
def report(json_output: bool):
    """Generate a comprehensive trust report."""
    engines = _init_engines()
    scoring = engines["scoring"]
    optimizer = engines["optimizer"]
    memory = engines["memory"]
    gates = engines["gates"]

    score_stats = scoring.stats()
    opt_report = optimizer.get_report()
    mem_stats = memory.stats()
    gate_stats = gates.stats()

    report_data = {
        "trust_scoring": score_stats,
        "token_optimization": {
            "total_original": opt_report.total_original_tokens,
            "total_compressed": opt_report.total_compressed_tokens,
            "ratio": round(opt_report.overall_compression_ratio * 100, 1),
            "cost_saved": opt_report.total_cost_saved,
            "operations": opt_report.operations,
        },
        "memory": mem_stats,
        "quality_gates": gate_stats,
    }

    if json_output:
        console.print_json(json.dumps(report_data, indent=2))
        return

    console.print(Panel.fit("[bold]CodeTruth Comprehensive Report[/]", border_style="cyan"))

    if score_stats.get("total_assessments", 0) > 0:
        console.print(f"\n[bold]Trust Scoring:[/] {score_stats['total_assessments']} assessments, "
                      f"avg {score_stats['avg_score']}/100, {score_stats['pass_rate']}% pass rate")

    console.print(f"[bold]Token Optimization:[/] {opt_report.total_original_tokens:,} → "
                  f"{opt_report.total_compressed_tokens:,} tokens ({round(opt_report.overall_compression_ratio * 100, 1)}% saved), "
                  f"${opt_report.total_cost_saved:.4f} saved")

    console.print(f"[bold]Memory Layer:[/] {mem_stats['total_entries']} entries, "
                  f"{mem_stats['total_spaces']} spaces, {mem_stats['total_tags']} tags")

    console.print(f"[bold]Quality Gates:[/] {gate_stats['total_runs']} runs, "
                  f"{gate_stats['pass_rate']}% pass rate, {gate_stats['rules_enabled']} rules active")


@cli.command()
@click.option("--host", "-h", default="127.0.0.1", help="Host to bind")
@click.option("--port", "-p", default=8742, help="Port to bind")
@click.option("--reload", is_flag=True, help="Enable auto-reload")
def serve(host: str, port: int, reload: bool):
    """Start the CodeTruth API server."""
    import uvicorn
    console.print(f"[bold green]Starting CodeTruth API on http://{host}:{port}[/]")
    console.print(f"[dim]API docs: http://{host}:{port}/docs[/]")
    uvicorn.run("codetruth.api:app", host=host, port=port, reload=reload)


@cli.command()
def info():
    """Display system information."""
    settings = get_settings()
    console.print(Panel.fit(
        f"[bold cyan]CodeTruth v1.0.0[/]\n\n"
        f"Data Dir: {settings.data_dir}\n"
        f"API: {settings.api_host}:{settings.api_port}\n"
        f"Trust Threshold: {settings.trust_threshold_pass} (pass) / {settings.trust_threshold_warn} (warn)\n"
        f"Token Compression: {settings.token_compression_target * 100:.0f}% target\n"
        f"Supported Tools: {', '.join(settings.supported_ai_tools)}",
        title="[bold]System Info[/]",
        border_style="cyan",
    ))


if __name__ == "__main__":
    cli()