"""sacrifunk-loudness — batch LUFS + true-peak + crest + LRA analyzer with CLI + Markdown + email."""

__version__ = "0.1.0"

from .analyzer import (
    AnalysisResult,
    AnalysisTargets,
    SACRIFUNK_TARGETS,
    analyze_file,
    analyze_folder,
)
from .report import render_markdown

__all__ = [
    "__version__",
    "AnalysisResult",
    "AnalysisTargets",
    "SACRIFUNK_TARGETS",
    "analyze_file",
    "analyze_folder",
    "render_markdown",
]
