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
# 429 backoff, then give up loudly. Sized against an observed arXiv-wide
# throttle (2026-09-13) that outlasted 255s: a weekly cron that gives up
# early loses the whole week, so patience is cheaper than a missed run.
RETRY_BACKOFF_S = (30, 120, 300, 900)
RETRYABLE_STATUS = {429, 503}  # throttled / overloaded; anything else is our bug
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
    else:
        # Exhausted max_candidates without reaching the cutoff: the lookback
        # window is silently truncated and older papers were never seen.
        log.warning("hit max_candidates=%d before the %d-day cutoff — oldest fetched "
                    "is %s; raise max_candidates or narrow arxiv_categories",
                    cfg.max_candidates, cfg.lookback_days,
                    papers[-1].published.date() if papers else "n/a")
    log.info("fetched %d papers", len(papers))
    return papers


def _get_page(categories: list[str], start: int, count: int) -> str:
    """One page of results, retried through arXiv's transient failures: 429 and
    503 (documented when it is overloaded) plus read/connection timeouts. A
    weekly cron that dies on any of them loses the whole week. Other HTTP
    errors — a malformed query — fail immediately and loudly.
    """
    params = {
        "search_query": " OR ".join(f"cat:{c}" for c in categories),
        "start": start,
        "max_results": count,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    last = "no attempt made"
    for backoff in (*RETRY_BACKOFF_S, None):  # None = last try, don't sleep after it
        try:
            resp = requests.get(API_URL, timeout=30, params=params)
            if resp.status_code not in RETRYABLE_STATUS:
                resp.raise_for_status()
                return resp.text
            last = f"HTTP {resp.status_code}"
            wait = int(resp.headers.get("Retry-After") or backoff or 0)
        except (requests.Timeout, requests.ConnectionError) as e:
            last, wait = type(e).__name__, backoff or 0
        if backoff is None:
            break
        log.warning("arXiv %s at start=%d; retrying in %ds", last, start, wait)
        time.sleep(wait)
    raise RuntimeError(f"arXiv unreachable at start={start} after "
                       f"{len(RETRY_BACKOFF_S)} retries: {last}")


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
