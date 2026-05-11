"""Markdown report renderer for AnalysisResult batches."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from . import __version__
from .analyzer import AnalysisResult, AnalysisTargets, SACRIFUNK_TARGETS, summarize


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _format_duration(sec: float) -> str:
    m, s = divmod(int(round(sec)), 60)
    return f"{m}:{s:02d}"


def _verdict_icon(r: AnalysisResult) -> str:
    if not r.ok:
        return ":x:"
    if r.verdict == "MASTERED OK":
        return ":white_check_mark:"
    return ":warning:"


def render_markdown(
    results: Iterable[AnalysisResult],
    targets: AnalysisTargets = SACRIFUNK_TARGETS,
    *,
    title: str = "Loudness Report",
    include_detail: bool = True,
) -> str:
    """Render a Markdown report for the given AnalysisResult list."""
    results = list(results)
    summary = summarize(results)

    lines: list[str] = [
        f"# {title}",
        "",
        f"_Generated {_now_iso()} by `sacrifunk-loudness` v{__version__}_",
        "",
        "## Targets",
        "",
        f"- Integrated loudness: **{targets.lufs_target:+.1f} LUFS** ±{targets.lufs_tolerance:.1f}",
        f"- True peak: **≤ {targets.true_peak_limit_dbtp:+.1f} dBTP**",
        f"- Crest factor: **{targets.crest_min_db:.0f}–{targets.crest_max_db:.0f} dB**",
        "",
        "## Summary",
        "",
        f"- **Total files:** {summary['total']}",
        f"- **OK (analyzed):** {summary['ok']}",
        f"- **Errors:** {summary['errors']}",
        f"- **Mastered OK (within all targets):** {summary['mastered_ok']}",
        f"- **LUFS off target:** {summary['lufs_off']}",
        f"- **True-peak over limit:** {summary['tp_over']}",
        f"- **Crest out of range:** {summary['crest_out']}",
        "",
        "## Per-file results",
        "",
        "| File | LUFS | TP (dBTP) | Sample peak | Crest | Duration | Verdict |",
        "|------|-----:|----------:|------------:|------:|---------:|---------|",
    ]

    for r in results:
        if not r.ok:
            lines.append(f"| `{r.filename}` | — | — | — | — | — | :x: {r.error or 'error'} |")
            continue
        icon = _verdict_icon(r)
        lines.append(
            f"| `{r.filename}` "
            f"| {r.lufs:+.2f} "
            f"| {r.true_peak_dbtp:+.2f} "
            f"| {r.sample_peak_dbfs:+.2f} dBFS "
            f"| {r.crest_db:.1f} dB "
            f"| {_format_duration(r.duration_sec)} "
            f"| {icon} {r.verdict} |"
        )

    if include_detail:
        lines.extend(["", "## Detail"])
        for r in results:
            lines.extend(["", f"### `{r.filename}`"])
            if not r.ok:
                lines.append(f"- **Error:** {r.error}")
                continue
            lines.extend([
                f"- **Path:** `{r.path}`",
                f"- **Size:** {r.size_bytes:,} bytes",
                f"- **Sample rate:** {r.sample_rate:,} Hz",
                f"- **Channels:** {r.channels}",
                f"- **Duration:** {_format_duration(r.duration_sec)} ({r.duration_sec:.2f} s)",
                f"- **Integrated loudness:** {r.lufs:+.2f} LUFS "
                f"(target {targets.lufs_target:+.1f} ±{targets.lufs_tolerance:.1f} → "
                f"{'**OFF**' if r.lufs_off_target else 'OK'})",
                f"- **True peak:** {r.true_peak_dbtp:+.2f} dBTP "
                f"(limit {targets.true_peak_limit_dbtp:+.1f} → "
                f"{'**OVER**' if r.tp_over_limit else 'OK'})",
                f"- **Sample peak:** {r.sample_peak_dbfs:+.2f} dBFS",
                f"- **Crest factor:** {r.crest_db:.1f} dB "
                f"(range {targets.crest_min_db:.0f}–{targets.crest_max_db:.0f} → "
                f"{'**OUT**' if r.crest_out_of_range else 'OK'})",
                f"- **Verdict:** {_verdict_icon(r)} {r.verdict}",
            ])

    lines.append("")
    return "\n".join(lines)
