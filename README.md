# sacrifunk-loudness

ITU-R BS.1770 LUFS + true-peak + crest analyzer with a Click CLI, Markdown report renderer, and optional SMTP email send. Drop a folder of WAV bounces at it and get back a JSON dump, a human-readable Markdown report, or an email straight to your inbox.

## Why

Streaming-music mastering targets `-14 LUFS ±0.5` and `True Peak ≤ -1.0 dBTP` (Sacrifunk's locked targets — same as Spotify/Apple/Tidal norms). Every bounce out of Logic Pro needs to clear those thresholds before it ships to CD Baby. This tool runs the standard analysis in one command and tells you which tracks pass and which need a second pass.

## Install

```bash
pip install sacrifunk-loudness
```

Python 3.10+. Pulls in `numpy`, `scipy`, `pyloudnorm`, and `click`.

## Usage

### Single file

```bash
sacrifunk-loudness analyze Bounces/Darko_master.wav
```

Default output is JSON on stdout, summary on stderr.

### Folder (recursive)

```bash
sacrifunk-loudness analyze Bounces/ --md report.md --json report.json
```

### Custom targets (e.g. broadcast / podcast)

```bash
sacrifunk-loudness analyze Bounces/ \
  --target -16 \
  --tolerance 1.0 \
  --tp-limit -2 \
  --crest-min 10 --crest-max 22
```

### Markdown from a saved JSON

```bash
sacrifunk-loudness report report.json --output report.md
```

### Email a report

```bash
export SMTP_HOST=smtp.gmail.com
export SMTP_USER=info@sacrifunk.com
export SMTP_PASS='app-password-here'
export SMTP_FROM='Ahmed <info@sacrifunk.com>'

sacrifunk-loudness send report.md --to ae@example.com --subject "Genesis 3 — Blues Bang final master"
```

## DSP

| Metric | Method |
|---|---|
| Integrated loudness (LUFS) | `pyloudnorm.Meter` — ITU-R BS.1770-4 K-weighted gating |
| True peak (dBTP) | 4× polyphase upsampling via `scipy.signal.resample_poly`, then `20·log10(max(abs(x)))` |
| Sample peak (dBFS) | `20·log10(max(abs(x)))` on raw samples |
| Crest factor (dB) | `sample_peak_dBFS − 20·log10(RMS)` |

Mono input is duplicated to stereo before measurement. Int16/Int24/Int32/uint8 WAVs are normalized to `[-1, 1]` float64.

## Sacrifunk defaults

The default `AnalysisTargets` matches Sacrifunk mastering canon (locked April 22, 2026):

- LUFS target `-14.0 ±0.5`
- True peak `≤ -1.0 dBTP`
- Crest factor `14–18 dB`

Override any of these via CLI flags or by passing an `AnalysisTargets` to `analyze_file()` / `analyze_folder()` programmatically.

## Library use

```python
from sacrifunk_loudness import analyze_file, analyze_folder, render_markdown, SACRIFUNK_TARGETS

result = analyze_file("Bounces/Darko_master.wav")
print(result.lufs, result.true_peak_dbtp, result.verdict)

results = analyze_folder("Bounces/", SACRIFUNK_TARGETS, recursive=True)
md = render_markdown(results)
```

## SMTP env vars

| Var | Required | Default | Notes |
|---|---|---|---|
| `SMTP_HOST` | yes | — | e.g. `smtp.gmail.com` |
| `SMTP_USER` | yes | — | full email address |
| `SMTP_PASS` | yes | — | app password, not your Google login |
| `SMTP_FROM` | no | `SMTP_USER` | `From:` header |
| `SMTP_PORT` | no | `587` | use `465` for SSL providers |
| `SMTP_SECURITY` | no | `starttls` | `starttls` / `ssl` / `none` |

Never pass credentials on the command line. `send` reads them from the environment only.

## Development

```bash
pip install -e ".[dev]"
pytest -v
```

Tests use synthetic 1 kHz sine WAVs scaled to known LUFS levels via pyloudnorm — no Sacrifunk workspace dependency.

## Roadmap

- LRA (Loudness Range, EBU R128 gated) — currently summary only.
- AAC / FLAC / AIFF input via `soundfile` fallback (today: WAV only via `scipy.io.wavfile`).
- HTML report alongside Markdown.
- `--watch` mode (chokidar-style folder watch).
- Optional Telegram digest output for mobile workflows.

The Sacrifunk production stack already runs the analyzer via an n8n cron at `_logic_pro_bounce_watch` (30s scheduler, Telegram digest to `@Sacrifunkbot`). A planned follow-up swaps `runtime/scripts/wav_quick_analyze.py` to a thin `from sacrifunk_loudness.analyzer import analyze_file` wrapper.

## License

MIT — see [LICENSE](LICENSE).
