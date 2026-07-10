import pytest

from paperdigest.config import load_config

VALID = """\
topics:
  - name: "DDS interoperability in ROS 2"
    description: "Cross-vendor DDS interop, QoS matching."
arxiv_categories: [cs.RO, eess.SY]
lookback_days: 7
max_candidates: 200
top_n: 10
min_relevance_score: 6
ranking_model: haiku
analysis_model: sonnet
"""


def _write(tmp_path, text):
    p = tmp_path / "topics.yaml"
    p.write_text(text)
    return p


def test_valid_config(tmp_path):
    cfg = load_config(_write(tmp_path, VALID))
    assert cfg.topics[0].name == "DDS interoperability in ROS 2"
    assert cfg.arxiv_categories == ["cs.RO", "eess.SY"]
    assert cfg.top_n == 10
    assert cfg.ranking_model == "haiku"


def test_missing_key(tmp_path):
    text = VALID.replace("top_n: 10\n", "")
    with pytest.raises(ValueError, match="top_n"):
        load_config(_write(tmp_path, text))


def test_bad_bounds(tmp_path):
    text = VALID.replace("min_relevance_score: 6", "min_relevance_score: 15")
    with pytest.raises(ValueError, match="min_relevance_score"):
        load_config(_write(tmp_path, text))


def test_empty_topics(tmp_path):
    text = "topics: []\narxiv_categories" + VALID.split("arxiv_categories", 1)[1]
    with pytest.raises(ValueError, match="topics"):
        load_config(_write(tmp_path, text))
