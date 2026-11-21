"""Stage 1: fetch recent papers from the arXiv API and parse the Atom feed."""
from __future__ import annotations

import logging
import re
import time
from datetime import datetime, timedelta, timezone
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

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
# arXiv's weekly batch boundary: Fri 14:00 ET submissions close, announced
# Sun 20:00 ET (info.arxiv.org/help/availability.html). Windows end on this
# boundary so a Monday run never searches submissions not yet announced.
ET = ZoneInfo("America/New_York")
FRIDAY = 4


def batch_window(now: datetime, lookback_days: int) -> tuple[datetime, datetime]:
    """[start, end) in UTC. end = latest Fri 14:00 ET whose Sun 20:00 ET
    announcement has passed; start = lookback_days earlier (ET wall clock,
    so DST shifts don't move the boundary off 14:00)."""
    day = now.astimezone(ET).date()
    while True:
        if day.weekday() == FRIDAY:
            end = datetime.combine(day, datetime.min.time().replace(hour=14), ET)
            announced = datetime.combine(day + timedelta(days=2),
                                         datetime.min.time().replace(hour=20), ET)
            if announced <= now:
                break
        day -= timedelta(days=1)
    start = datetime.combine(day - timedelta(days=lookback_days), end.timetz())
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def _with_window(query: str, start: datetime, end: datetime) -> str:
    """Bound a query server-side so max_candidates only counts in-window papers.
    arXiv's range is GMT, minute precision, inclusive: stop one minute early."""
    fmt = "%Y%m%d%H%M"
    last = end - timedelta(minutes=1)
    return f"({query}) AND submittedDate:[{start:{fmt}} TO {last:{fmt}}]"


def fetch_papers(cfg: Config, now: datetime | None = None) -> list[Paper]:
    """Papers in the last announced `lookback_days` batch window (see
    batch_window) from the category feed plus
    each `arxiv_queries` stream, deduped by id, newest first. Each stream is
    capped at `max_candidates` on its own, so a narrow query never loses its
    few papers to a flooded category feed."""
    start, end = batch_window(now or datetime.now(timezone.utc), cfg.lookback_days)
    log.info("window: %s to %s UTC", f"{start:%Y-%m-%d %H:%M}", f"{end:%Y-%m-%d %H:%M}")
    category_query = " OR ".join(f"cat:{c}" for c in cfg.arxiv_categories)
    by_id: dict[str, Paper] = {}
    for i, query in enumerate((category_query, *cfg.arxiv_queries)):
        if i:
            time.sleep(REQUEST_GAP_S)
        for p in _fetch_stream(query, cfg, start, end):
            by_id.setdefault(p.arxiv_id, p)
    papers = sorted(by_id.values(), key=lambda p: p.published, reverse=True)
    log.info("fetched %d unique papers from %d streams", len(papers), 1 + len(cfg.arxiv_queries))
    return papers


def _fetch_stream(query: str, cfg: Config, start: datetime, end: datetime) -> list[Paper]:
    papers: list[Paper] = []
    too_new = 0  # should stay 0: the server-side range already excludes them
    for offset in range(0, cfg.max_candidates, PAGE_SIZE):
        if offset:
            time.sleep(REQUEST_GAP_S)
        count = min(PAGE_SIZE, cfg.max_candidates - offset)
        page = parse_atom(_get_page(_with_window(query, start, end), offset, count))
        for p in page:
            if p.published >= end:
                too_new += 1
                continue
            if p.published < start:
                _log_stream(query, papers, too_new, "hit window start")
                return papers
            papers.append(p)
        if len(page) < count:
            break
    else:
        _warn_truncated(query, papers, cfg)
    _log_stream(query, papers, too_new)
    return papers


def _warn_truncated(query: str, papers: list[Paper], cfg: Config) -> None:
    """Exhausted max_candidates inside the window: older papers were never seen."""
    log.warning("%s: hit max_candidates=%d before the %d-day window start — oldest "
                "fetched is %s; raise max_candidates or narrow the query",
                query, cfg.max_candidates, cfg.lookback_days,
                papers[-1].published.date() if papers else "n/a")


def _log_stream(query: str, papers: list[Paper], too_new: int, note: str = "") -> None:
    log.info("%s: %d papers%s", query, len(papers), f" ({note})" if note else "")
    if too_new:
        log.warning("%s: dropped %d papers published after the window end; "
                    "submittedDate and <published> disagree", query, too_new)


def _get_page(query: str, start: int, count: int) -> str:
    """One page of results, retried through arXiv's transient failures: 429 and
    503 (documented when it is overloaded) plus read/connection timeouts. A
    weekly cron that dies on any of them loses the whole week. Other HTTP
    errors — a malformed query — fail immediately and loudly.
    """
    params = {
        "search_query": query,
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
