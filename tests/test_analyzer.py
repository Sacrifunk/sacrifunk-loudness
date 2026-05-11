import numpy as np

from sacrifunk_loudness import analyze_file, analyze_folder, SACRIFUNK_TARGETS
from sacrifunk_loudness.analyzer import summarize, AnalysisTargets


def test_near_target_passes(near_target_wav):
    r = analyze_file(near_target_wav)
    assert r.ok
    assert r.lufs is not None
    assert abs(r.lufs - SACRIFUNK_TARGETS.lufs_target) <= SACRIFUNK_TARGETS.lufs_tolerance
    assert not r.lufs_off_target


def test_loud_signal_flags_lufs_off(loud_wav):
    r = analyze_file(loud_wav)
    assert r.ok
    assert r.lufs_off_target is True
    assert "LUFS off" in r.flags


def test_quiet_signal_flags_lufs_off(quiet_wav):
    r = analyze_file(quiet_wav)
    assert r.ok
    assert r.lufs_off_target is True


def test_clipped_signal_flags_tp_over(clipped_wav):
    r = analyze_file(clipped_wav)
    assert r.ok
    # Full-scale sine produces sample peak ≈ 0 dBFS; with 4x oversample TP slightly exceeds.
    assert r.true_peak_dbtp > SACRIFUNK_TARGETS.true_peak_limit_dbtp
    assert r.tp_over_limit is True


def test_mono_file_handled(mono_wav):
    r = analyze_file(mono_wav)
    assert r.ok
    assert r.channels == 1
    assert r.lufs is not None


def test_missing_file_returns_error_result(tmp_path):
    r = analyze_file(tmp_path / "does_not_exist.wav")
    assert r.ok is False
    assert "not found" in r.error


def test_metrics_match_wav_quick_analyze_shape(near_target_wav):
    """Smoke-check the JSON dict matches wav_quick_analyze.py's key set."""
    r = analyze_file(near_target_wav)
    d = r.to_dict()
    required = {
        "ok", "path", "filename", "size_bytes", "duration_sec", "sample_rate",
        "lufs", "true_peak_dbtp", "sample_peak_dbfs", "crest_db",
        "lufs_target", "tp_limit", "lufs_off_target", "tp_over_limit", "verdict",
    }
    assert required.issubset(d.keys())


def test_custom_targets(near_target_wav):
    """Overriding targets flips the verdict appropriately."""
    strict = AnalysisTargets(lufs_target=-23.0, lufs_tolerance=0.1, true_peak_limit_dbtp=-2.0)
    r = analyze_file(near_target_wav, strict)
    assert r.ok
    assert r.lufs_target == -23.0
    assert r.lufs_off_target is True  # -14 is far from -23


def test_folder_sorts_results(small_folder):
    results = analyze_folder(small_folder)
    assert len(results) == 2
    filenames = [r.filename for r in results]
    assert filenames == sorted(filenames)


def test_summarize_counts(small_folder):
    results = analyze_folder(small_folder)
    s = summarize(results)
    assert s["total"] == 2
    assert s["ok"] == 2
    assert s["errors"] == 0
    # one near-target + one loud → at least 1 lufs_off
    assert s["lufs_off"] >= 1


def test_folder_not_directory_raises(tmp_path):
    import pytest
    with pytest.raises(NotADirectoryError):
        analyze_folder(tmp_path / "missing")
