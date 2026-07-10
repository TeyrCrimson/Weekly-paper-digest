import pytest

from paperdigest import analyze, llm
from paperdigest.config import Config
from paperdigest.models import LLMResult, RankedPaper
from tests.conftest import make_paper


def _cfg(topics) -> Config:
    return Config(
        topics=topics, arxiv_categories=["cs.RO"], lookback_days=7,
        max_candidates=200, top_n=2, min_relevance_score=6,
        ranking_model="haiku", analysis_model="sonnet",
    )


def _ranked(i, score):
    return RankedPaper(paper=make_paper(i), score=score,
                       matched_topics=["DDS interoperability in ROS 2"], one_liner="x")


def test_analyze_papers(monkeypatch, topics):
    monkeypatch.setattr(analyze, "_download_pdf", lambda url: b"%PDF-fake")
    monkeypatch.setattr(analyze, "_extract_text", lambda b: "extracted paper text")
    calls = []

    def fake_complete(prompt, system, model):
        calls.append((prompt, system, model))
        return LLMResult(text="## TL;DR\ndigest body", usage={"output_tokens": 5})

    monkeypatch.setattr(llm, "complete", fake_complete)

    # top_n=2: third paper never analyzed; score-4 paper filtered out
    analyses = analyze.analyze_papers(
        [_ranked(0, 9), _ranked(1, 4), _ranked(2, 8)], _cfg(topics))

    assert len(analyses) == 1
    assert analyses[0].markdown == "## TL;DR\ndigest body"
    assert analyses[0].error is None
    prompt, system, model = calls[0]
    assert model == "sonnet"
    assert system == analyze.ANALYSIS_SYSTEM_PROMPT
    assert "extracted paper text" in prompt


def test_pdf_failure_gives_stub(monkeypatch, topics):
    def boom(url):
        raise OSError("404 not found")

    monkeypatch.setattr(analyze, "_download_pdf", boom)
    monkeypatch.setattr(llm, "complete",
                        lambda *a: pytest.fail("LLM must not be called on PDF failure"))

    analyses = analyze.analyze_papers([_ranked(0, 9)], _cfg(topics))
    assert len(analyses) == 1
    assert analyses[0].error == "PDF unavailable: 404 not found"
    assert analyses[0].markdown == ""


def test_truncate_keeps_head_and_tail():
    text = "A" * 70_000 + "B" * 70_000
    out = analyze._truncate(text)
    assert len(out) < 82_000
    assert out.startswith("A") and out.endswith("B")
    assert "truncated" in out
