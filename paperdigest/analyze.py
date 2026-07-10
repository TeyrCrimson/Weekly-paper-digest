"""Stage 3: deep-analyze the top N papers — download PDF, extract text, one
Sonnet call each. Metadata is assembled in render.py, not by the model."""
from __future__ import annotations

import io
import logging

import requests
from pypdf import PdfReader

from paperdigest import llm
from paperdigest.config import Config
from paperdigest.models import Analysis, RankedPaper

log = logging.getLogger(__name__)

MAX_CHARS = 80_000
HEAD_CHARS = 60_000  # abstract/intro/method live at the front …
TAIL_CHARS = 20_000  # … experiments/conclusion at the back

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
    """Analyze the top_n papers scoring >= min_relevance_score."""
    analyses = []
    for rp in ranked[:cfg.top_n]:
        if rp.score < cfg.min_relevance_score:
            log.info("skipping %s: score %d < min_relevance_score %d",
                     rp.paper.arxiv_id, rp.score, cfg.min_relevance_score)
            continue
        analyses.append(_analyze_one(rp, cfg.analysis_model))
    return analyses


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
