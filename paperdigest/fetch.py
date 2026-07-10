"""Stage 1: fetch recent papers from the arXiv API and parse the Atom feed."""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree

import requests

from paperdigest.config import Config
from paperdigest.models import Paper

log = logging.getLogger(__name__)

API_URL = "http://export.arxiv.org/api/query"
PAGE_SIZE = 100
REQUEST_GAP_S = 3  # arXiv rate guidance: 1 request / 3 s
ATOM = {"atom": "http://www.w3.org/2005/Atom"}


def fetch_papers(cfg: Config) -> list[Paper]:
    """Papers submitted in the last `lookback_days`, newest first, capped at
    `max_candidates`."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=cfg.lookback_days)
    papers: list[Paper] = []
    for start in range(0, cfg.max_candidates, PAGE_SIZE):
        if start:
            time.sleep(REQUEST_GAP_S)
        count = min(PAGE_SIZE, cfg.max_candidates - start)
        page = parse_atom(_get_page(cfg.arxiv_categories, start, count))
        for p in page:
            if p.published < cutoff:
                log.info("fetched %d papers (hit %d-day cutoff)", len(papers), cfg.lookback_days)
                return papers
            papers.append(p)
        if len(page) < count:
            break
    log.info("fetched %d papers", len(papers))
    return papers


def _get_page(categories: list[str], start: int, count: int) -> str:
    resp = requests.get(API_URL, timeout=30, params={
        "search_query": " OR ".join(f"cat:{c}" for c in categories),
        "start": start,
        "max_results": count,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    resp.raise_for_status()
    return resp.text


def parse_atom(xml_text: str) -> list[Paper]:
    root = ElementTree.fromstring(xml_text)
    return [_parse_entry(e) for e in root.findall("atom:entry", ATOM)]


def _parse_entry(entry: ElementTree.Element) -> Paper:
    def text(tag: str) -> str:
        return (entry.findtext(f"atom:{tag}", "", ATOM) or "").strip()

    arxiv_id = re.sub(r"v\d+$", "", text("id").rsplit("/", 1)[-1])
    return Paper(
        arxiv_id=arxiv_id,
        title=re.sub(r"\s+", " ", text("title")),
        authors=[(a.findtext("atom:name", "", ATOM) or "").strip()
                 for a in entry.findall("atom:author", ATOM)],
        abstract=re.sub(r"\s+", " ", text("summary")),
        categories=[c.get("term", "") for c in entry.findall("atom:category", ATOM)],
        published=datetime.fromisoformat(text("published")),
        pdf_url=f"https://arxiv.org/pdf/{arxiv_id}",
        abs_url=f"https://arxiv.org/abs/{arxiv_id}",
    )
