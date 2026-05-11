from sacrifunk_loudness import analyze_file, render_markdown
from sacrifunk_loudness.analyzer import SACRIFUNK_TARGETS


def test_render_markdown_smoke(near_target_wav, loud_wav):
    results = [analyze_file(near_target_wav), analyze_file(loud_wav)]
    md = render_markdown(results, SACRIFUNK_TARGETS)

    # Header + targets section
    assert "# Loudness Report" in md
    assert "## Targets" in md
    assert "-14.0 LUFS" in md
    assert "-1.0 dBTP" in md

    # Summary
    assert "**Total files:** 2" in md
    assert "**OK (analyzed):** 2" in md

    # Per-file table
    assert "near_target.wav" in md
    assert "loud.wav" in md
    assert ":warning:" in md  # the loud file should flag


def test_render_markdown_includes_detail_section(near_target_wav):
    results = [analyze_file(near_target_wav)]
    md = render_markdown(results, SACRIFUNK_TARGETS, include_detail=True)
    assert "## Detail" in md
    assert "**Path:**" in md


def test_render_markdown_can_skip_detail(near_target_wav):
    results = [analyze_file(near_target_wav)]
    md = render_markdown(results, SACRIFUNK_TARGETS, include_detail=False)
    assert "## Detail" not in md


def test_render_handles_error_results():
    from sacrifunk_loudness.analyzer import AnalysisResult
    err = AnalysisResult(ok=False, path="/x.wav", filename="x.wav", error="not found")
    md = render_markdown([err])
    assert "x.wav" in md
    assert ":x:" in md
    assert "not found" in md
