import pytest

from paperdigest import analyze, llm
from paperdigest.config import Config, Topic
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

    # top_n=2, but the score-4 paper is below min_relevance_score
    analyses = analyze.analyze_papers([_ranked(0, 9), _ranked(1, 4)], _cfg(topics))

    assert len(analyses) == 1
    assert analyses[0].markdown == "## TL;DR\ndigest body"
    assert analyses[0].error is None
    prompt, system, model = calls[0]
    assert model == "sonnet"
    assert system == analyze.ANALYSIS_SYSTEM_PROMPT
    assert "extracted paper text" in prompt


def test_select_for_analysis_spreads_across_topics():
    def rp(i, score, topic):
        return RankedPaper(paper=make_paper(i), score=score, matched_topics=[topic], one_liner="")
    busy = [rp(i, 10, "busy") for i in range(5)]
    narrow = rp(5, 7, "narrow")
    noise = rp(6, 9, "unmatched")
    low = rp(7, 5, "narrow")

    picked = analyze.select_for_analysis([*busy, noise, narrow, low], ["busy", "narrow"], 3, 6)
    assert picked == [busy[0], busy[1], narrow]  # narrow's 7 beats busy's third 10

    # narrow runs dry: leftover slots go to busy, then to unmatched by score
    picked = analyze.select_for_analysis([*busy[:2], noise, narrow], ["busy", "narrow"], 4, 6)
    assert picked == [busy[0], busy[1], noise, narrow]


def test_low_scoring_paper_is_topics_guaranteed_slot():
    def rp(i, score, topic):
        return RankedPaper(paper=make_paper(i), score=score, matched_topics=[topic], one_liner="")
    busy = [rp(i, 10, "busy") for i in range(3)]
    sparse, unmatched = rp(3, 2, "sparse"), rp(4, 1, "other")
    picked = analyze.select_for_analysis([*busy, sparse, unmatched], ["busy", "sparse"], 3, 6)
    assert picked == [busy[0], busy[1], sparse]  # unmatched low paper never guaranteed


def test_analyze_flags_low_relevance(monkeypatch, topics):
    monkeypatch.setattr(analyze, "_download_pdf", lambda url: b"%PDF-fake")
    monkeypatch.setattr(analyze, "_extract_text", lambda b: "text")
    monkeypatch.setattr(llm, "complete", lambda p, s, m: LLMResult(text="body", usage={}))
    analyses = analyze.analyze_papers([_ranked(0, 9), _ranked(1, 3)],
                                      _cfg([topics[0], Topic("other", "x")]))
    assert [a.low_relevance for a in analyses] == [False]  # topic already filled

    low = RankedPaper(paper=make_paper(2), score=3, matched_topics=["other"], one_liner="")
    analyses = analyze.analyze_papers([_ranked(0, 9), low], _cfg([topics[0], Topic("other", "x")]))
    assert [a.low_relevance for a in analyses] == [False, True]


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


def test_summarize_week(monkeypatch, topics):
    from paperdigest.models import Analysis
    calls = []

    def fake_complete(prompt, system, model):
        calls.append((prompt, system, model))
        return LLMResult(text="## The week in one paragraph\nbrief", usage={})

    monkeypatch.setattr(llm, "complete", fake_complete)
    ok = Analysis(ranked=_ranked(0, 9), markdown="## TL;DR\nbody", usage={})
    broken = Analysis(ranked=_ranked(1, 9), markdown="", usage={}, error="PDF unavailable: 404")

    assert analyze.summarize_week([ok, broken], _cfg(topics)).startswith("## The week")
    prompt, system, model = calls[0]
    assert model == "sonnet" and system == analyze.SUMMARY_SYSTEM_PROMPT
    assert "part 0" in prompt and "part 1" not in prompt  # failed analyses excluded


def test_summarize_week_skips_call_when_nothing_analyzed(monkeypatch, topics):
    monkeypatch.setattr(llm, "complete", lambda *a: pytest.fail("no papers -> no call"))
    assert analyze.summarize_week([], _cfg(topics)) == ""
