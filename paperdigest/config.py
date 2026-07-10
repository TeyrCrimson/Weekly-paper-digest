"""Load and validate config/topics.yaml. Raises ValueError on anything malformed."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Topic:
    name: str
    description: str


@dataclass(frozen=True)
class Config:
    topics: list[Topic]
    arxiv_categories: list[str]
    lookback_days: int
    max_candidates: int
    top_n: int
    min_relevance_score: int
    ranking_model: str
    analysis_model: str


def load_config(path: str | Path) -> Config:
    raw = yaml.safe_load(Path(path).read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: config must be a mapping")
    missing = {f.name for f in Config.__dataclass_fields__.values()} - raw.keys()
    if missing:
        raise ValueError(f"{path}: missing config keys: {sorted(missing)}")
    cfg = Config(
        topics=_parse_topics(raw["topics"]),
        arxiv_categories=_require_str_list(raw, "arxiv_categories"),
        lookback_days=_require_int(raw, "lookback_days", 1, 60),
        max_candidates=_require_int(raw, "max_candidates", 1, 2000),
        top_n=_require_int(raw, "top_n", 1, 100),
        min_relevance_score=_require_int(raw, "min_relevance_score", 0, 10),
        ranking_model=_require_str(raw, "ranking_model"),
        analysis_model=_require_str(raw, "analysis_model"),
    )
    return cfg


def _parse_topics(raw: object) -> list[Topic]:
    if not isinstance(raw, list) or not raw:
        raise ValueError("topics: must be a non-empty list")
    topics = []
    for i, t in enumerate(raw):
        if not isinstance(t, dict) or not t.get("name") or not t.get("description"):
            raise ValueError(f"topics[{i}]: needs non-empty 'name' and 'description'")
        topics.append(Topic(name=str(t["name"]).strip(), description=str(t["description"]).strip()))
    return topics


def _require_int(raw: dict, key: str, lo: int, hi: int) -> int:
    v = raw[key]
    if not isinstance(v, int) or isinstance(v, bool) or not lo <= v <= hi:
        raise ValueError(f"{key}: must be an int in [{lo}, {hi}], got {v!r}")
    return v


def _require_str(raw: dict, key: str) -> str:
    v = raw[key]
    if not isinstance(v, str) or not v.strip():
        raise ValueError(f"{key}: must be a non-empty string, got {v!r}")
    return v.strip()


def _require_str_list(raw: dict, key: str) -> list[str]:
    v = raw[key]
    if not isinstance(v, list) or not v or not all(isinstance(s, str) and s.strip() for s in v):
        raise ValueError(f"{key}: must be a non-empty list of strings, got {v!r}")
    return [s.strip() for s in v]
