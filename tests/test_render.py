from datetime import datetime, timezone

from paperdigest.models import Analysis, RankedPaper
from paperdigest.render import render_digests
from tests.conftest import make_paper

RUN_TIME = datetime(2026, 7, 6, 6, 0, tzinfo=timezone.utc)  # ISO week 2026-W28
USAGE = [
    {"model": "haiku", "input_tokens": 100, "output_tokens": 10, "cost_usd": 0.0},
    {"model": "sonnet", "input_tokens": 500, "output_tokens": 200, "cost_usd": 0.0},
]


def _analysis(i, score=8, error=None):
    rp = RankedPaper(paper=make_paper(i), score=score,
                     matched_topics=["DDS interoperability in ROS 2"],
                     one_liner="Does a thing.")
    md = "" if error else "## TL;DR\nShort digest."
    return Analysis(ranked=rp, markdown=md, usage={}, error=error)


def test_render_digests(tmp_path):
    week_dir = render_digests(tmp_path, [_analysis(0), _analysis(1, error="PDF unavailable: 404")],
                              USAGE, RUN_TIME)
    assert week_dir.name == "2026-W28"

    index = (week_dir / "index.md").read_text()
    paper_file = "2507.00000-cross-vendor-dds-discovery-for-ros-2-par.md"
    assert f"]({paper_file})" in index
    assert "analysis skipped: PDF unavailable: 404" in index  # stub row, no file
    assert "600 in / 210 out tokens" in index
    assert "2 LLM calls" in index

    body = (week_dir / paper_file).read_text()
    assert body.startswith("# Cross-vendor DDS discovery for ROS 2, part 0")
    assert "**Relevance:** 8/10" in body
    assert "## TL;DR" in body
    assert len(list(week_dir.iterdir())) == 2  # index + one digest


def test_rerun_is_idempotent(tmp_path):
    render_digests(tmp_path, [_analysis(0)], USAGE, RUN_TIME)
    week_dir = render_digests(tmp_path, [_analysis(1)], USAGE, RUN_TIME)
    files = {f.name for f in week_dir.iterdir()}
    assert "index.md" in files and len(files) == 2
    assert not any("00000" in f for f in files)  # old week's file gone
