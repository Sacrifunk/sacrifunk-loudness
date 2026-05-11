"""Synthetic WAV fixtures so tests run without the Sacrifunk workspace."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyloudnorm as pyln
import pytest
import scipy.io.wavfile as wav


SAMPLE_RATE = 48_000
DURATION_SEC = 4.0  # pyloudnorm needs >= ~3s of audio for integrated loudness


def _write_wav(path: Path, stereo: np.ndarray, sample_rate: int = SAMPLE_RATE) -> Path:
    pcm = np.clip(stereo, -1.0, 1.0)
    pcm16 = (pcm * 32767.0).astype(np.int16)
    wav.write(str(path), sample_rate, pcm16)
    return path


def _sine_stereo(freq: float, amplitude: float, duration: float = DURATION_SEC, sr: int = SAMPLE_RATE) -> np.ndarray:
    t = np.arange(int(sr * duration)) / sr
    mono = amplitude * np.sin(2 * np.pi * freq * t)
    return np.column_stack([mono, mono])


def _scale_to_lufs(stereo: np.ndarray, target_lufs: float, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Measure current loudness with pyloudnorm and rescale to target_lufs."""
    meter = pyln.Meter(sr)
    current = meter.integrated_loudness(stereo)
    if not np.isfinite(current):
        return stereo
    gain_db = target_lufs - current
    gain_lin = 10 ** (gain_db / 20.0)
    return stereo * gain_lin


@pytest.fixture
def near_target_wav(tmp_path: Path) -> Path:
    """A 1 kHz tone scaled to ~-14 LUFS (within Sacrifunk tolerance)."""
    stereo = _sine_stereo(freq=1000.0, amplitude=0.5)
    scaled = _scale_to_lufs(stereo, target_lufs=-14.0)
    return _write_wav(tmp_path / "near_target.wav", scaled)


@pytest.fixture
def loud_wav(tmp_path: Path) -> Path:
    """A 1 kHz tone scaled to ~-6 LUFS (well over target, should flag LUFS off)."""
    stereo = _sine_stereo(freq=1000.0, amplitude=0.5)
    scaled = _scale_to_lufs(stereo, target_lufs=-6.0)
    return _write_wav(tmp_path / "loud.wav", scaled)


@pytest.fixture
def quiet_wav(tmp_path: Path) -> Path:
    """A 1 kHz tone scaled to ~-30 LUFS (well under target)."""
    stereo = _sine_stereo(freq=1000.0, amplitude=0.5)
    scaled = _scale_to_lufs(stereo, target_lufs=-30.0)
    return _write_wav(tmp_path / "quiet.wav", scaled)


@pytest.fixture
def clipped_wav(tmp_path: Path) -> Path:
    """A 1 kHz tone at maximum amplitude — true peak will exceed -1 dBTP after oversampling."""
    stereo = _sine_stereo(freq=1000.0, amplitude=1.0)
    return _write_wav(tmp_path / "clipped.wav", stereo)


@pytest.fixture
def mono_wav(tmp_path: Path) -> Path:
    """Mono file — analyzer must duplicate to stereo and not crash."""
    t = np.arange(int(SAMPLE_RATE * DURATION_SEC)) / SAMPLE_RATE
    mono = 0.3 * np.sin(2 * np.pi * 1000.0 * t)
    pcm16 = (np.clip(mono, -1.0, 1.0) * 32767.0).astype(np.int16)
    p = tmp_path / "mono.wav"
    wav.write(str(p), SAMPLE_RATE, pcm16)
    return p


@pytest.fixture
def small_folder(tmp_path: Path, near_target_wav, loud_wav) -> Path:
    """A folder with two named bounces inside it."""
    folder = tmp_path / "Bounces"
    folder.mkdir()
    # Move the two fixtures into the folder
    (folder / near_target_wav.name).write_bytes(near_target_wav.read_bytes())
    (folder / loud_wav.name).write_bytes(loud_wav.read_bytes())
    return folder
