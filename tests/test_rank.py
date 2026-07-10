import json

import pytest

from paperdigest import llm, rank
from paperdigest.config import Config
from paperdigest.models import LLMResult
from tests.conftest import make_paper


def _cfg(topics) -> Config:
    return Config(
        topics=topics, arxiv_categories=["cs.RO"], lookback_days=7,
        max_candidates=200, top_n=10, min_relevance_score=6,
        ranking_model="haiku", analysis_model="sonnet",
    )


def _patch_complete(monkeypatch, texts):
    """llm.complete returns each canned text in order; records prompts."""
    it = iter(texts)
    prompts = []

    def fake_complete(prompt, system, model):
        prompts.append((prompt, system, model))
        return LLMResult(text=next(it), usage={"input_tokens": 1, "output_tokens": 1})

    monkeypatch.setattr(llm, "complete", fake_complete)
    return prompts


GOOD = json.dumps([
    {"index": 1, "score": 9, "matched_topics": ["DDS interoperability in ROS 2"],
     "one_liner": "DDS discovery study."},
    {"index": 0, "score": 3, "matched_topics": [], "one_liner": "Off-topic."},
])


def test_rank_papers(monkeypatch, topics):
    papers = [make_paper(0), make_paper(1)]
    prompts = _patch_complete(monkeypatch, [GOOD])
    ranked = rank.rank_papers(papers, _cfg(topics))
    assert [r.score for r in ranked] == [9, 3]  # sorted descending
    assert ranked[0].paper is papers[1]
    assert ranked[0].matched_topics == ["DDS interoperability in ROS 2"]
    prompt, system, model = prompts[0]
    assert model == "haiku"
    assert system == rank.RANK_SYSTEM_PROMPT
    assert "[1] Cross-vendor DDS discovery for ROS 2, part 1" in prompt


def test_malformed_then_good(monkeypatch, topics):
    _patch_complete(monkeypatch, ["not json at all", GOOD])
    ranked = rank.rank_papers([make_paper(0), make_paper(1)], _cfg(topics))
    assert len(ranked) == 2


def test_malformed_twice_raises(monkeypatch, topics):
    bad = json.dumps([{"index": 0, "score": 99, "matched_topics": [], "one_liner": ""}])
    _patch_complete(monkeypatch, [bad, bad])
    with pytest.raises(RuntimeError, match="malformed"):
        rank.rank_papers([make_paper(0)], _cfg(topics))


def test_code_fences_stripped(monkeypatch, topics):
    fenced = "```json\n" + json.dumps(
        [{"index": 0, "score": 7, "matched_topics": [], "one_liner": "x"}]) + "\n```"
    _patch_complete(monkeypatch, [fenced])
    assert rank.rank_papers([make_paper(0)], _cfg(topics))[0].score == 7


def test_heuristic_rank(topics):
    on_topic = make_paper(0)
    off_topic = make_paper(1, title="Quantum cryptography survey",
                           abstract="Lattice-based encryption schemes.")
    ranked = rank.heuristic_rank([off_topic, on_topic], topics)
    assert ranked[0].paper is on_topic
    assert ranked[0].score > ranked[1].score
    assert "DDS interoperability in ROS 2" in ranked[0].matched_topics
