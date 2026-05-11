"""Loudness + true-peak + crest factor analyzer.

The DSP core matches the algorithm in `My AIs/Claude OS/runtime/scripts/
wav_quick_analyze.py` (LIVE in the `_logic_pro_bounce_watch` n8n workflow on
a 30s cron). This module is a *fresh implementation* so the production
script stays untouched. A follow-up will swap that script to a thin
`from sacrifunk_loudness.analyzer import analyze_file` wrapper.

References:
  - ITU-R BS.1770-4 — Algorithms to measure audio programme loudness
  - EBU R 128 — Loudness normalisation and permitted maximum level
  - pyloudnorm — Python port of BS.1770 by Steinmetz
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional, Sequence

import numpy as np
import pyloudnorm as pyln
import scipy.io.wavfile as wav
import scipy.signal

warnings.filterwarnings("ignore", category=wav.WavFileWarning)


# ── Targets ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class AnalysisTargets:
    """Pass/fail thresholds for a programme. Defaults to streaming-music norms."""

    lufs_target: float = -14.0
    lufs_tolerance: float = 0.5
    true_peak_limit_dbtp: float = -1.0
    crest_min_db: float = 14.0
    crest_max_db: float = 18.0


SACRIFUNK_TARGETS = AnalysisTargets(
    lufs_target=-14.0,
    lufs_tolerance=0.5,
    true_peak_limit_dbtp=-1.0,
    crest_min_db=14.0,
    crest_max_db=18.0,
)
"""Sacrifunk mastering targets — locked April 22, 2026 per workspace canon."""


# ── Result type ──────────────────────────────────────────────────────────


@dataclass
class AnalysisResult:
    """Per-file analysis output. Mirrors wav_quick_analyze.py JSON shape + extras."""

    ok: bool
    path: str
    filename: str
    size_bytes: int = 0
    duration_sec: float = 0.0
    sample_rate: int = 0
    channels: int = 0

    lufs: Optional[float] = None
    true_peak_dbtp: Optional[float] = None
    sample_peak_dbfs: Optional[float] = None
    crest_db: Optional[float] = None

    # Pass/fail evaluation
    lufs_target: Optional[float] = None
    tp_limit: Optional[float] = None
    lufs_off_target: Optional[bool] = None
    tp_over_limit: Optional[bool] = None
    crest_out_of_range: Optional[bool] = None
    verdict: str = ""

    error: Optional[str] = None
    flags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """JSON-serialisable shape; matches wav_quick_analyze.py keys where possible."""
        if not self.ok:
            return {"ok": False, "path": self.path, "filename": self.filename, "error": self.error}
        return {
            "ok": True,
            "path": self.path,
            "filename": self.filename,
            "size_bytes": self.size_bytes,
            "duration_sec": round(self.duration_sec, 1),
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "lufs": round(self.lufs, 2) if self.lufs is not None else None,
            "true_peak_dbtp": round(self.true_peak_dbtp, 2) if self.true_peak_dbtp is not None else None,
            "sample_peak_dbfs": round(self.sample_peak_dbfs, 2) if self.sample_peak_dbfs is not None else None,
            "crest_db": round(self.crest_db, 1) if self.crest_db is not None else None,
            "lufs_target": self.lufs_target,
            "tp_limit": self.tp_limit,
            "lufs_off_target": self.lufs_off_target,
            "tp_over_limit": self.tp_over_limit,
            "crest_out_of_range": self.crest_out_of_range,
            "verdict": self.verdict,
            "flags": self.flags,
        }


# ── Internal helpers ─────────────────────────────────────────────────────


def _to_stereo_float(samples: np.ndarray, dtype) -> np.ndarray:
    """Normalize a wavfile.read() array to float64 stereo in [-1, 1]."""
    if dtype.kind == "i":
        max_int = float(np.iinfo(dtype).max)
        samples = samples.astype(np.float64) / max_int
    elif dtype.kind == "u":
        max_int = float(np.iinfo(dtype).max)
        samples = (samples.astype(np.float64) - max_int / 2.0) / (max_int / 2.0)
    else:
        samples = samples.astype(np.float64)

    if samples.ndim == 1:
        return np.column_stack([samples, samples])
    if samples.shape[1] == 1:
        return np.column_stack([samples[:, 0], samples[:, 0]])
    return samples[:, :2]


def _measure(stereo: np.ndarray, sample_rate: int) -> dict:
    """Pure DSP — return raw metrics on a float64 stereo (N,2) array."""
    meter = pyln.Meter(sample_rate)
    lufs = float(meter.integrated_loudness(stereo))

    upsampled = scipy.signal.resample_poly(stereo, 4, 1, axis=0)
    tp_lin = float(np.max(np.abs(upsampled)))
    true_peak_dbtp = 20.0 * np.log10(tp_lin) if tp_lin > 0 else -120.0

    sp_lin = float(np.max(np.abs(stereo)))
    sample_peak_dbfs = 20.0 * np.log10(sp_lin) if sp_lin > 0 else -120.0

    rms = float(np.sqrt(np.mean(stereo ** 2)))
    crest = (sample_peak_dbfs - 20.0 * np.log10(rms)) if rms > 0 else 0.0

    return {
        "lufs": lufs,
        "true_peak_dbtp": true_peak_dbtp,
        "sample_peak_dbfs": sample_peak_dbfs,
        "crest_db": crest,
    }


def _evaluate(metrics: dict, targets: AnalysisTargets) -> tuple[list[str], str, dict]:
    """Apply targets → flags + verdict + pass/fail booleans."""
    flags: list[str] = []
    lufs_off = abs(metrics["lufs"] - targets.lufs_target) > targets.lufs_tolerance
    tp_over = metrics["true_peak_dbtp"] > targets.true_peak_limit_dbtp
    crest_out = not (targets.crest_min_db <= metrics["crest_db"] <= targets.crest_max_db)

    if lufs_off:
        flags.append("LUFS off")
    if tp_over:
        flags.append("TP over")
    if crest_out:
        flags.append("crest out of range")

    verdict = "MASTERED OK" if not flags else " | ".join(flags)
    return flags, verdict, {
        "lufs_off_target": bool(lufs_off),
        "tp_over_limit": bool(tp_over),
        "crest_out_of_range": bool(crest_out),
    }


# ── Public API ───────────────────────────────────────────────────────────


def analyze_file(path: os.PathLike | str, targets: AnalysisTargets = SACRIFUNK_TARGETS) -> AnalysisResult:
    """Analyze a single WAV file. Returns AnalysisResult with `ok=False` on error."""
    path_str = str(path)
    filename = os.path.basename(path_str)

    if not os.path.exists(path_str):
        return AnalysisResult(ok=False, path=path_str, filename=filename, error=f"file not found: {path_str}")

    try:
        sr, raw = wav.read(path_str)
    except Exception as exc:
        return AnalysisResult(ok=False, path=path_str, filename=filename, error=f"wav read failed: {exc}")

    try:
        stereo = _to_stereo_float(raw, raw.dtype)
        duration = stereo.shape[0] / float(sr)
        metrics = _measure(stereo, sr)
        flags, verdict, pass_fail = _evaluate(metrics, targets)
    except Exception as exc:
        return AnalysisResult(ok=False, path=path_str, filename=filename, error=f"analysis failed: {exc}")

    return AnalysisResult(
        ok=True,
        path=path_str,
        filename=filename,
        size_bytes=os.path.getsize(path_str),
        duration_sec=duration,
        sample_rate=int(sr),
        channels=int(raw.shape[1]) if raw.ndim == 2 else 1,
        lufs=metrics["lufs"],
        true_peak_dbtp=metrics["true_peak_dbtp"],
        sample_peak_dbfs=metrics["sample_peak_dbfs"],
        crest_db=metrics["crest_db"],
        lufs_target=targets.lufs_target,
        tp_limit=targets.true_peak_limit_dbtp,
        lufs_off_target=pass_fail["lufs_off_target"],
        tp_over_limit=pass_fail["tp_over_limit"],
        crest_out_of_range=pass_fail["crest_out_of_range"],
        verdict=verdict,
        flags=flags,
    )


def analyze_folder(
    folder: os.PathLike | str,
    targets: AnalysisTargets = SACRIFUNK_TARGETS,
    *,
    recursive: bool = True,
    extensions: Sequence[str] = (".wav",),
) -> list[AnalysisResult]:
    """Analyze every audio file in `folder` (recursive by default)."""
    folder = Path(folder)
    if not folder.is_dir():
        raise NotADirectoryError(f"not a directory: {folder}")

    pattern = "**/*" if recursive else "*"
    ext_lower = tuple(e.lower() for e in extensions)

    paths = sorted(
        p for p in folder.glob(pattern)
        if p.is_file() and p.suffix.lower() in ext_lower
    )

    return [analyze_file(p, targets) for p in paths]


def summarize(results: Iterable[AnalysisResult]) -> dict:
    """Aggregate counts for the report header line."""
    results = list(results)
    ok = [r for r in results if r.ok]
    return {
        "total": len(results),
        "ok": len(ok),
        "errors": len(results) - len(ok),
        "mastered_ok": sum(1 for r in ok if r.verdict == "MASTERED OK"),
        "lufs_off": sum(1 for r in ok if r.lufs_off_target),
        "tp_over": sum(1 for r in ok if r.tp_over_limit),
        "crest_out": sum(1 for r in ok if r.crest_out_of_range),
    }
