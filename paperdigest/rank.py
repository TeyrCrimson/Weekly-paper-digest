"""Stage 2: score candidate papers against the topic list.

`rank_papers` = one batched Haiku call (chunked if >100 candidates).
`heuristic_rank` = zero-LLM keyword pre-rank used by --dry-run.
"""
from __future__ import annotations

import json
import logging
import re

from paperdigest import llm
from paperdigest.config import Config, Topic
from paperdigest.models import Paper, RankedPaper

log = logging.getLogger(__name__)

CHUNK_SIZE = 100

RANK_SYSTEM_PROMPT = """\
You are a research paper triage assistant. You are given a list of TOPICS
(name plus description — the description is what matters) and a numbered list
of PAPERS (title plus abstract). For EVERY paper, score its relevance to the
topic list from 0 (unrelated) to 10 (directly on-topic).

Respond with ONLY a JSON array, no prose, no code fences. One object per
paper, in any order, shaped exactly like:
  {"index": <paper number as int>, "score": <int 0-10>,
   "matched_topics": [<names of topics it matches, possibly empty>],
   "one_liner": "<one short sentence on what the paper does>"}

Every paper index must appear exactly once. Scores must be integers.
"""


def rank_papers(papers: list[Paper], cfg: Config) -> list[RankedPaper]:
    """LLM-score all candidates; returns papers sorted by score, descending."""
    ranked: list[RankedPaper] = []
    for i in range(0, len(papers), CHUNK_SIZE):
        chunk = papers[i:i + CHUNK_SIZE]
        rows = _rank_chunk(_build_prompt(cfg.topics, chunk), cfg.ranking_model, len(chunk))
        ranked += [
            RankedPaper(
                paper=chunk[r["index"]],
                score=r["score"],
                matched_topics=r["matched_topics"],
                one_liner=r["one_liner"],
            )
            for r in rows
        ]
    return sorted(ranked, key=lambda r: r.score, reverse=True)


def _build_prompt(topics: list[Topic], chunk: list[Paper]) -> str:
    tlines = "\n".join(f"- {t.name}: {t.description}" for t in topics)
    plines = "\n\n".join(f"[{i}] {p.title}\n{p.abstract}" for i, p in enumerate(chunk))
    return f"TOPICS:\n{tlines}\n\nPAPERS:\n{plines}"


def _rank_chunk(prompt: str, model: str, n_papers: int) -> list[dict]:
    """One LLM call; retries the call once if the model's JSON is malformed."""
    for attempt in (1, 2):
        result = llm.complete(prompt, RANK_SYSTEM_PROMPT, model)
        try:
            return _parse_scores(result.text, n_papers)
        except ValueError as e:
            log.warning("ranking JSON attempt %d/2 malformed: %s", attempt, e)
    raise RuntimeError("ranking output still malformed after one retry")


def _parse_scores(text: str, n_papers: int) -> list[dict]:
    rows = json.loads(_strip_fences(text))
    if not isinstance(rows, list):
        raise ValueError("expected a JSON array")
    seen: set[int] = set()
    for r in rows:
        idx, score = r.get("index"), r.get("score")
        if not _is_int(idx, 0, n_papers - 1) or idx in seen:
            raise ValueError(f"bad or duplicate index: {idx!r}")
        if not _is_int(score, 0, 10):
            raise ValueError(f"score for paper {idx} not an int in 0-10: {score!r}")
        if not isinstance(r.get("matched_topics"), list) or not isinstance(r.get("one_liner"), str):
            raise ValueError(f"paper {idx}: bad matched_topics or one_liner")
        seen.add(idx)
    if len(seen) != n_papers:
        raise ValueError(f"got {len(seen)} scores for {n_papers} papers")
    return rows


def _is_int(v: object, lo: int, hi: int) -> bool:
    return isinstance(v, int) and not isinstance(v, bool) and lo <= v <= hi


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n|\n```$", "", text)
    return text


def heuristic_rank(papers: list[Paper], topics: list[Topic]) -> list[RankedPaper]:
    """Keyword-overlap pre-rank for --dry-run. Zero LLM calls."""
    topic_kw = {t.name: _keywords(f"{t.name} {t.description}") for t in topics}
    ranked = []
    for p in papers:
        words = _keywords(f"{p.title} {p.abstract}")
        overlap = {name: len(words & kw) for name, kw in topic_kw.items()}
        # ponytail: crude 1-hit-per-point score; the real ranker is the LLM
        ranked.append(RankedPaper(
            paper=p,
            score=min(10, max(overlap.values(), default=0)),
            matched_topics=sorted(n for n, c in overlap.items() if c >= 2),
            one_liner="",
        ))
    return sorted(ranked, key=lambda r: r.score, reverse=True)


def _keywords(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9-]+", text.lower()) if len(w) > 3}
