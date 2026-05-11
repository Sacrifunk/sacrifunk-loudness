# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] — 2026-05-11

### Changed
- `requires-python` lowered from `>=3.10` to `>=3.9`. The codebase has always used `from __future__ import annotations`, so the few `X | None`-style type hints are stringified at parse time and never evaluated at runtime. No 3.10+ runtime features are used. Verified empirically against Apple's system Python 3.9.6 (`/usr/bin/python3`) on 2026-05-11 — `analyze_file` returned bit-for-bit identical output to the Python 3.14 reference run on a 60 MB master.
- Added `Programming Language :: Python :: 3.9` classifier.

### Why this matters
The original v0.1.0 pin to `>=3.10` was conservative-by-default rather than necessary. It forced production callers running under Apple's system Python (the n8n `_logic_pro_bounce_watch` cron uses `/usr/bin/python3`) to install via `pip install --ignore-requires-python` — a flag that masks legitimate future incompatibilities. v0.1.1 removes the need for the flag.

Surfaced by the Learning Lab Task 2.5 swap and tracked as [issue #1](https://github.com/Sacrifunk/sacrifunk-loudness/issues/1).

## [0.1.0] — 2026-05-11

### Added
- `analyze_file(path, targets)` — integrated LUFS (pyloudnorm BS.1770-4) + true peak (scipy 4× oversampled) + sample peak + crest factor on a single WAV.
- `analyze_folder(folder, targets, recursive=True, extensions=...)` — batch analysis of every WAV in a folder.
- `AnalysisTargets` dataclass with `SACRIFUNK_TARGETS` constant: `-14 LUFS ±0.5`, TP `≤-1 dBTP`, crest `14–18 dB`.
- `render_markdown(results, targets)` — Markdown report with summary header + per-file table + per-file detail blocks.
- `sacrifunk_loudness.mail.send_report()` — SMTP send of a Markdown report. Credentials from `SMTP_*` env vars; STARTTLS/SSL/plaintext.
- `sacrifunk-loudness` CLI with three subcommands: `analyze` / `report` / `send`.
- `sacrifunk-loudness analyze --fail-on-warning` for CI integration.
- Pytest suite with synthetic 1 kHz sine fixtures scaled via pyloudnorm to known LUFS levels.

### DSP parity
Algorithm matches `runtime/scripts/wav_quick_analyze.py` (LIVE in the `_logic_pro_bounce_watch` n8n workflow on a 30s cron). This package is a fresh implementation — the production script stays untouched. A follow-up will swap that script to import from this package.
