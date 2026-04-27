"""Analyze validation flags from a Petra validation result and ask Claude for feedback.

Reads a validation result JSON (the output of `python -m src.main validate --out report.json`)
or a list of rule assessments, summarizes flags by verdict, and asks Claude to suggest
areas of improvement based on the failing / needs-review rules.

Usage:
    python flag_analysis/analyze_flags.py <path-to-report.json>
    python flag_analysis/analyze_flags.py <path-to-report.json> --out feedback.md

Environment:
    ANTHROPIC_API_KEY     Required.
    CLAUDE_TEXT_MODEL     Optional. Defaults to claude-sonnet-4-6.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import typer
from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

DEFAULT_MODEL = "claude-sonnet-4-6"
FAIL_VERDICTS = {"fail", "needs_review"}

cli = typer.Typer(add_completion=False, help=__doc__)
console = Console()


def _load_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise typer.BadParameter(f"Report file not found: {path}")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"Invalid JSON in {path}: {exc}") from exc


def _extract_assessments(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Pull rule assessments from a DocumentValidationResponse-shaped dict, or accept a raw list."""
    if isinstance(report, list):
        return report
    analysis = report.get("analysis") or {}
    assessments = list(analysis.get("rule_assessments") or [])
    assessments.extend(analysis.get("text_page_results") or [])
    assessments.extend(analysis.get("visual_page_results") or [])
    return assessments


def _summarize(assessments: list[dict[str, Any]]) -> dict[str, Any]:
    verdicts = Counter(a.get("verdict", "unknown") for a in assessments)
    flagged = [a for a in assessments if a.get("verdict") in FAIL_VERDICTS and not a.get("bypass")]
    by_group = Counter(a.get("group") or "ungrouped" for a in flagged)
    total = len(assessments)
    pass_count = verdicts.get("pass", 0)
    pass_rate = (pass_count / total * 100) if total else 0.0
    return {
        "total_rules": total,
        "verdict_counts": dict(verdicts),
        "flagged_count": len(flagged),
        "pass_rate_pct": round(pass_rate, 1),
        "flagged_by_group": dict(by_group.most_common()),
        "flagged": flagged,
    }


def _render_summary(summary: dict[str, Any]) -> None:
    table = Table(title="Flag Summary", show_header=True, header_style="bold")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Total rule assessments", str(summary["total_rules"]))
    table.add_row("Pass rate", f"{summary['pass_rate_pct']}%")
    table.add_row("Flagged (fail + needs_review)", str(summary["flagged_count"]))
    for verdict, count in summary["verdict_counts"].items():
        table.add_row(f"  {verdict}", str(count))
    console.print(table)

    if summary["flagged_by_group"]:
        group_table = Table(title="Flagged by Group", show_header=True, header_style="bold")
        group_table.add_column("Group")
        group_table.add_column("Count", justify="right")
        for group, count in summary["flagged_by_group"].items():
            group_table.add_row(group, str(count))
        console.print(group_table)


def _build_prompt(summary: dict[str, Any], source_filename: str | None) -> str:
    flagged_payload = [
        {
            "rule_id": a.get("rule_id"),
            "rule_name": a.get("rule_name"),
            "verdict": a.get("verdict"),
            "group": a.get("group"),
            "summary": a.get("summary"),
            "reasoning": a.get("reasoning"),
            "findings": a.get("findings", []),
            "page": a.get("page"),
        }
        for a in summary["flagged"]
    ]
    stats = {
        "source_filename": source_filename,
        "total_rules": summary["total_rules"],
        "verdict_counts": summary["verdict_counts"],
        "flagged_count": summary["flagged_count"],
        "pass_rate_pct": summary["pass_rate_pct"],
        "flagged_by_group": summary["flagged_by_group"],
    }
    return (
        "You are reviewing the results of an automated PDF validation run. "
        "Each flagged item is a rule that returned `fail` or `needs_review`. "
        "Produce concise, actionable feedback for the document author.\n\n"
        "Return Markdown with these sections:\n"
        "1. **Overview** - one paragraph on overall quality given the stats.\n"
        "2. **Top Issues** - the 3-5 most impactful flags, grouped by theme. "
        "Cite rule_id and page where useful.\n"
        "3. **Areas for Improvement** - specific changes the author should make.\n"
        "4. **Quick Wins** - low-effort fixes that would clear the most flags.\n\n"
        f"STATISTICS:\n{json.dumps(stats, indent=2)}\n\n"
        f"FLAGGED RULES:\n{json.dumps(flagged_payload, indent=2)}\n"
    )


def _ask_claude(prompt: str, model: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AI_API_KEY")
    if not api_key:
        raise typer.BadParameter("ANTHROPIC_API_KEY is not set in the environment.")
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    parts = [block.text for block in response.content if getattr(block, "type", None) == "text"]
    return "\n".join(parts).strip()


@cli.command()
def main(
    report: Path = typer.Argument(..., help="Path to a validation result JSON file."),
    out: Path | None = typer.Option(None, "--out", "-o", help="Write Claude's feedback to this Markdown file."),
    model: str = typer.Option(
        os.environ.get("CLAUDE_TEXT_MODEL", DEFAULT_MODEL),
        "--model",
        "-m",
        help="Claude model id.",
    ),
    skip_llm: bool = typer.Option(False, "--skip-llm", help="Print stats only; do not call Claude."),
) -> None:
    load_dotenv()
    payload = _load_report(report)
    assessments = _extract_assessments(payload)
    if not assessments:
        console.print("[yellow]No rule assessments found in the report.[/yellow]")
        raise typer.Exit(code=1)

    summary = _summarize(assessments)
    _render_summary(summary)

    if skip_llm:
        return

    source_filename = payload.get("source_filename") if isinstance(payload, dict) else None
    prompt = _build_prompt(summary, source_filename)
    console.print(f"\n[bold]Asking {model} for feedback...[/bold]")
    feedback = _ask_claude(prompt, model)

    console.rule("[bold]Claude Feedback[/bold]")
    console.print(feedback)

    if out:
        out.write_text(feedback)
        console.print(f"\n[green]Saved feedback to {out}[/green]")


if __name__ == "__main__":
    try:
        cli()
    except typer.BadParameter as exc:
        console.print(f"[red]{exc}[/red]")
        sys.exit(2)
