"""Plain dataclasses passed between pipeline stages."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Paper:
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    categories: list[str]
    published: datetime
    pdf_url: str
    abs_url: str


@dataclass(frozen=True)
class RankedPaper:
    paper: Paper
    score: int
    matched_topics: list[str]
    one_liner: str


@dataclass(frozen=True)
class Analysis:
    ranked: RankedPaper
    markdown: str
    usage: dict
    error: str | None = None


@dataclass(frozen=True)
class LLMResult:
    text: str
    usage: dict
    raw: dict = field(default_factory=dict)
