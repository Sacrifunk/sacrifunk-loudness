"""CLI entry point: `sacrifunk-loudness` with `analyze` / `report` / `send` subcommands."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from . import __version__
from .analyzer import (
    AnalysisResult,
    AnalysisTargets,
    SACRIFUNK_TARGETS,
    analyze_file,
    analyze_folder,
    summarize,
)
from .report import render_markdown


def _targets_from_opts(target, tolerance, tp_limit, crest_min, crest_max) -> AnalysisTargets:
    return AnalysisTargets(
        lufs_target=target,
        lufs_tolerance=tolerance,
        true_peak_limit_dbtp=tp_limit,
        crest_min_db=crest_min,
        crest_max_db=crest_max,
    )


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="sacrifunk-loudness")
def main() -> None:
    """LUFS + true-peak + crest analyzer with batch CLI, Markdown report, and email."""


# ── analyze ──────────────────────────────────────────────────────────────


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--json", "json_out", type=click.Path(path_type=Path), help="Write JSON to this file (omit for stdout).")
@click.option("--md", "md_out", type=click.Path(path_type=Path), help="Write Markdown to this file (omit to skip).")
@click.option("--target", type=float, default=SACRIFUNK_TARGETS.lufs_target, show_default=True, help="LUFS target.")
@click.option("--tolerance", type=float, default=SACRIFUNK_TARGETS.lufs_tolerance, show_default=True, help="LUFS tolerance.")
@click.option("--tp-limit", type=float, default=SACRIFUNK_TARGETS.true_peak_limit_dbtp, show_default=True, help="True-peak ceiling (dBTP).")
@click.option("--crest-min", type=float, default=SACRIFUNK_TARGETS.crest_min_db, show_default=True, help="Crest factor minimum (dB).")
@click.option("--crest-max", type=float, default=SACRIFUNK_TARGETS.crest_max_db, show_default=True, help="Crest factor maximum (dB).")
@click.option("--recursive/--no-recursive", default=True, show_default=True, help="Recurse into subfolders.")
@click.option("--ext", multiple=True, default=(".wav",), show_default=True, help="File extensions to scan (folder mode).")
@click.option("--fail-on-warning", is_flag=True, help="Exit non-zero if any track is out of target.")
def analyze(
    path: Path,
    json_out: Path | None,
    md_out: Path | None,
    target: float,
    tolerance: float,
    tp_limit: float,
    crest_min: float,
    crest_max: float,
    recursive: bool,
    ext: tuple[str, ...],
    fail_on_warning: bool,
) -> None:
    """Run analysis on a single WAV file or a folder of WAVs."""
    targets = _targets_from_opts(target, tolerance, tp_limit, crest_min, crest_max)

    if path.is_dir():
        results = analyze_folder(path, targets, recursive=recursive, extensions=ext)
    else:
        results = [analyze_file(path, targets)]

    payload = {
        "summary": summarize(results),
        "targets": {
            "lufs_target": targets.lufs_target,
            "lufs_tolerance": targets.lufs_tolerance,
            "true_peak_limit_dbtp": targets.true_peak_limit_dbtp,
            "crest_min_db": targets.crest_min_db,
            "crest_max_db": targets.crest_max_db,
        },
        "results": [r.to_dict() for r in results],
    }
    payload_str = json.dumps(payload, indent=2) + "\n"

    if json_out:
        json_out.write_text(payload_str, encoding="utf-8")
        click.echo(f"Wrote JSON → {json_out}")
    elif not md_out:
        # Default: JSON to stdout.
        click.echo(payload_str, nl=False)

    if md_out:
        md = render_markdown(results, targets, title=f"Loudness Report — {path.name}")
        md_out.write_text(md, encoding="utf-8")
        click.echo(f"Wrote Markdown → {md_out}")

    # Console summary on stderr so JSON-to-stdout pipelines stay clean
    summary = payload["summary"]
    click.echo(
        f"  → {summary['total']} files, "
        f"{summary['ok']} ok, "
        f"{summary['mastered_ok']} mastered-OK, "
        f"{summary['lufs_off']} LUFS off, "
        f"{summary['tp_over']} TP over, "
        f"{summary['errors']} errors",
        err=True,
    )

    if fail_on_warning and (summary["lufs_off"] or summary["tp_over"] or summary["crest_out"] or summary["errors"]):
        sys.exit(1)


# ── report ───────────────────────────────────────────────────────────────


@main.command()
@click.argument("json_input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Write Markdown to this file (omit for stdout).")
@click.option("--title", default="Loudness Report", show_default=True)
def report(json_input: Path, output: Path | None, title: str) -> None:
    """Render a Markdown report from a previously written JSON file."""
    payload = json.loads(json_input.read_text())

    raw_results = payload.get("results", payload if isinstance(payload, list) else [payload])
    targets_dict = payload.get("targets", {}) if isinstance(payload, dict) else {}
    targets = AnalysisTargets(
        lufs_target=targets_dict.get("lufs_target", SACRIFUNK_TARGETS.lufs_target),
        lufs_tolerance=targets_dict.get("lufs_tolerance", SACRIFUNK_TARGETS.lufs_tolerance),
        true_peak_limit_dbtp=targets_dict.get("true_peak_limit_dbtp", SACRIFUNK_TARGETS.true_peak_limit_dbtp),
        crest_min_db=targets_dict.get("crest_min_db", SACRIFUNK_TARGETS.crest_min_db),
        crest_max_db=targets_dict.get("crest_max_db", SACRIFUNK_TARGETS.crest_max_db),
    )
    results = [_dict_to_result(r) for r in raw_results]
    md = render_markdown(results, targets, title=title)

    if output:
        output.write_text(md, encoding="utf-8")
        click.echo(f"Wrote Markdown → {output}")
    else:
        click.echo(md)


def _dict_to_result(d: dict) -> AnalysisResult:
    """Rehydrate an AnalysisResult from its JSON dict form."""
    if not d.get("ok"):
        return AnalysisResult(ok=False, path=d.get("path", ""), filename=d.get("filename", ""), error=d.get("error"))
    return AnalysisResult(
        ok=True,
        path=d.get("path", ""),
        filename=d.get("filename", ""),
        size_bytes=d.get("size_bytes", 0),
        duration_sec=d.get("duration_sec", 0.0),
        sample_rate=d.get("sample_rate", 0),
        channels=d.get("channels", 0),
        lufs=d.get("lufs"),
        true_peak_dbtp=d.get("true_peak_dbtp"),
        sample_peak_dbfs=d.get("sample_peak_dbfs"),
        crest_db=d.get("crest_db"),
        lufs_target=d.get("lufs_target"),
        tp_limit=d.get("tp_limit"),
        lufs_off_target=d.get("lufs_off_target"),
        tp_over_limit=d.get("tp_over_limit"),
        crest_out_of_range=d.get("crest_out_of_range"),
        verdict=d.get("verdict", ""),
        flags=d.get("flags", []),
    )


# ── send ─────────────────────────────────────────────────────────────────


@main.command()
@click.argument("markdown_input", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--to", "to_addr", required=True, help="Recipient email address.")
@click.option("--subject", default=None, help="Subject line (default: derived from filename + date).")
@click.option("--dry-run", is_flag=True, help="Print what would be sent; don't connect to SMTP.")
def send(markdown_input: Path, to_addr: str, subject: str | None, dry_run: bool) -> None:
    """Send a Markdown report by email (SMTP creds via env vars)."""
    from datetime import date
    from .mail import SMTPConfigError, send_report

    body = markdown_input.read_text(encoding="utf-8")
    subject = subject or f"Loudness report — {markdown_input.stem} — {date.today().isoformat()}"

    if dry_run:
        click.echo(f"[DRY-RUN] To: {to_addr}")
        click.echo(f"[DRY-RUN] Subject: {subject}")
        click.echo(f"[DRY-RUN] Body size: {len(body)} bytes")
        click.echo("[DRY-RUN] SMTP_HOST / SMTP_USER / SMTP_PASS would be read from env")
        return

    try:
        meta = send_report(to=to_addr, subject=subject, markdown_body=body)
    except SMTPConfigError as exc:
        click.secho(f"SMTP config error: {exc}", fg="red", err=True)
        sys.exit(2)
    except Exception as exc:
        click.secho(f"send failed: {exc}", fg="red", err=True)
        sys.exit(3)

    click.echo(f"Sent → {meta['to']} via {meta['host']}:{meta['port']} ({meta['security']})")


if __name__ == "__main__":
    main()
