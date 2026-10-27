"""Stage 3: deep-analyze the top N papers — download PDF, extract text, one
Sonnet call each. Metadata is assembled in render.py, not by the model."""
from __future__ import annotations

import io
import logging
from dataclasses import replace

import requests
from pypdf import PdfReader

from paperdigest import llm
from paperdigest.config import Config
from paperdigest.models import Analysis, RankedPaper

log = logging.getLogger(__name__)

MAX_CHARS = 80_000
HEAD_CHARS = 60_000  # abstract/intro/method live at the front …
TAIL_CHARS = 20_000  # … experiments/conclusion at the back
LOW_RELEVANCE_NOTE = ", LOW RELEVANCE: below threshold, its topic's only match"

ANALYSIS_SYSTEM_PROMPT = """\
You are writing a technical digest of ONE research paper for a strong
engineer who is not a specialist in this subfield. You are given the paper's
title, abstract, and extracted full text (possibly truncated in the middle).

Respond in Markdown with exactly these sections, in this order, and nothing
else (no title, no metadata — those are added separately):

## TL;DR
3 sentences max.

## First-principles breakdown
Explain every complex concept or method in the paper from the ground up.
Build up: what problem is being solved, why prior approaches fail, and what
this paper's mechanism actually does, step by step.

## Key insights
What is genuinely new or useful. Distinguish claimed contributions from what
the evidence actually supports.

## Caveats — stated and inferred
Limitations the authors admit, PLUS red flags inferable from the text:
simulation-only evaluation, weak or stale baselines, missing ablations,
cherry-picked metrics, unrealistic assumptions. Label each caveat as `stated`
or `inferred`. Do not invent caveats without textual grounding.

Rules:
- Base everything ONLY on the provided text.
- If something is missing, say "not addressed in the paper" rather than
  speculate.
"""


def analyze_papers(ranked: list[RankedPaper], cfg: Config) -> list[Analysis]:
    """Analyze up to top_n papers, spread across topics (see select_for_analysis)."""
    picked = select_for_analysis(ranked, [t.name for t in cfg.topics],
                                 cfg.top_n, cfg.min_relevance_score)
    log.info("analyzing %d of %d ranked papers", len(picked), len(ranked))
    analyses = []
    for rp in picked:
        low = rp.score < cfg.min_relevance_score
        if low:
            log.info("including %s below min_relevance_score (%d < %d): best match for %s",
                     rp.paper.arxiv_id, rp.score, cfg.min_relevance_score, rp.matched_topics)
        analyses.append(replace(_analyze_one(rp, cfg.analysis_model), low_relevance=low))
    return analyses


def select_for_analysis(ranked: list[RankedPaper], topic_names: list[str],
                        top_n: int, min_score: int) -> list[RankedPaper]:
    """Every topic first takes its best match whatever its score, so a sparse
    topic always surfaces something (render flags it as low relevance). Then
    topics take turns taking their best unpicked paper >= min_score, so one
    busy topic can't take every slot (2026-W37/W39: inference efficiency took
    12/12). Slots no topic can fill go to the highest remaining scores."""
    by_score = sorted(ranked, key=lambda r: r.score, reverse=True)
    eligible = [r for r in by_score if r.score >= min_score]
    picked: list[RankedPaper] = []

    def take(pool: list[RankedPaper], name: str) -> bool:
        r = next((r for r in pool if name in r.matched_topics
                  and not any(r is p for p in picked)), None)
        if r and len(picked) < top_n:
            picked.append(r)
        return r is not None

    for name in topic_names:
        take(by_score, name)
    # list, not generator: every topic gets its turn before any() short-circuits
    while len(picked) < top_n and any([take(eligible, n) for n in topic_names]):
        pass
    picked += [r for r in eligible if not any(r is p for p in picked)][:top_n - len(picked)]
    return sorted(picked, key=lambda r: r.score, reverse=True)


def _analyze_one(rp: RankedPaper, model: str) -> Analysis:
    try:
        text = _extract_text(_download_pdf(rp.paper.pdf_url))
    except Exception as e:  # any PDF failure -> stub entry, keep the run alive
        log.error("PDF for %s failed, skipping analysis: %s", rp.paper.arxiv_id, e)
        return Analysis(ranked=rp, markdown="", usage={}, error=f"PDF unavailable: {e}")
    prompt = (f"Title: {rp.paper.title}\n"
              f"Abstract: {rp.paper.abstract}\n\n"
              f"FULL TEXT:\n{_truncate(text)}")
    result = llm.complete(prompt, ANALYSIS_SYSTEM_PROMPT, model)
    return Analysis(ranked=rp, markdown=result.text, usage=result.usage)


def _download_pdf(url: str) -> bytes:
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    return resp.content


def _extract_text(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _truncate(text: str) -> str:
    if len(text) <= MAX_CHARS:
        return text
    # ponytail: head+tail keeps abstract/intro/method and conclusion; proper
    # section-aware selection only if middle-heavy papers prove to matter.
    return (text[:HEAD_CHARS] + "\n\n[... middle of paper truncated ...]\n\n"
            + text[-TAIL_CHARS:])


SUMMARY_SYSTEM_PROMPT = """\
You are writing the weekly brief that sits on top of a set of per-paper
digests. The reader has already seen a one-line-per-paper index and wants the
week condensed: what actually landed, and what deserves their reading time.

Respond in Markdown with exactly these sections, in this order, and nothing
else:

## The week in one paragraph
5 sentences max.

## Themes
2-5 bullets. Name the theme, name the papers under it by title, and say what
the cluster collectively establishes (or fails to).

## Read these
Up to 3 papers, one line each: why this one rather than its neighbours.

## Skip unless
The rest, one line each: the condition under which the paper would matter.

Rules:
- Base everything ONLY on the digests provided; do not invent findings.
- Carry the digests' caveats through: if a cluster is simulation-only or
  leans on weak baselines, say so here rather than letting the brief read
  stronger than the evidence.
"""


def summarize_week(analyses: list[Analysis], cfg: Config) -> str:
    """One extra call condensing the week's digests into SUMMARY.md."""
    blob = "\n\n---\n\n".join(
        f"# {a.ranked.paper.title} (relevance {a.ranked.score}/10"
        f"{LOW_RELEVANCE_NOTE if a.low_relevance else ''})\n{a.markdown}"
        for a in analyses if not a.error
    )
    if not blob:
        return ""
    return llm.complete(_truncate(blob), SUMMARY_SYSTEM_PROMPT, cfg.analysis_model).text
