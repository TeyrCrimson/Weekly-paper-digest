import pytest

from datetime import datetime, timedelta, timezone
from pathlib import Path

from paperdigest import fetch
from paperdigest.config import Config, Topic
from paperdigest.fetch import batch_window, fetch_papers, parse_atom

FIXTURE = (Path(__file__).parent / "fixtures" / "arxiv_atom.xml").read_text()
NOW = datetime(2026, 11, 16, 15, 43, tzinfo=timezone.utc)  # the W47 run
START, END = batch_window(NOW, 7)


def _cfg(max_candidates: int, arxiv_queries: list[str] | None = None) -> Config:
    return Config(
        topics=[Topic("t", "d")], arxiv_categories=["cs.LG"], lookback_days=7,
        max_candidates=max_candidates, top_n=1, min_relevance_score=6,
        ranking_model="haiku", analysis_model="sonnet",
        arxiv_queries=arxiv_queries or [],
    )


def _entry(i: int, published: datetime) -> str:
    return f"""<entry>
      <id>http://arxiv.org/abs/2607.{i:05d}v1</id><title>P{i}</title>
      <summary>abstract</summary><published>{published.isoformat()}</published>
      <author><name>A</name></author><category term="cs.LG"/>
    </entry>"""


def _feed_factory(monkeypatch, oldest_age_days: float):
    """Serve pages of 100 entries spread over `oldest_age_days` before END, newest first."""
    def fake_get_page(query, start, count):
        entries = "".join(
            _entry(start + n, END - timedelta(days=oldest_age_days * (start + n + 1) / 300))
            for n in range(count)
        )
        return f'<feed xmlns="http://www.w3.org/2005/Atom">{entries}</feed>'
    monkeypatch.setattr(fetch, "_get_page", fake_get_page)
    monkeypatch.setattr(fetch, "REQUEST_GAP_S", 0)


def test_fetch_papers_stops_at_cutoff(monkeypatch, caplog):
    """300 papers span 21 days, so the 7-day cutoff hits before the 300 cap."""
    _feed_factory(monkeypatch, oldest_age_days=21)
    papers = fetch_papers(_cfg(max_candidates=300), now=NOW)
    assert 0 < len(papers) < 300
    assert all(START <= p.published < END for p in papers)
    assert "hit max_candidates" not in caplog.text


def test_fetch_papers_warns_when_cap_truncates_window(monkeypatch, caplog):
    """All 300 papers are within 7 days, so the 200 cap silently cuts the window."""
    _feed_factory(monkeypatch, oldest_age_days=2)
    papers = fetch_papers(_cfg(max_candidates=200), now=NOW)
    assert len(papers) == 200
    assert "hit max_candidates=200" in caplog.text


def test_fetch_papers_merges_query_streams(monkeypatch):
    """Extra queries are fetched separately and deduped against the category feed."""
    feeds = {"cat:cs.LG": [1, 2], "abs:x": [2, 3]}  # paper 2 appears in both
    seen = []
    def fake_get_page(query, start, count):
        base = query.split(") AND submittedDate:")[0].lstrip("(")
        seen.append(base)
        entries = "".join(_entry(i, END - timedelta(hours=i)) for i in feeds[base])
        return f'<feed xmlns="http://www.w3.org/2005/Atom">{entries}</feed>'
    monkeypatch.setattr(fetch, "_get_page", fake_get_page)
    monkeypatch.setattr(fetch, "REQUEST_GAP_S", 0)

    papers = fetch_papers(_cfg(max_candidates=100, arxiv_queries=["abs:x"]), now=NOW)
    assert seen == ["cat:cs.LG", "abs:x"]
    assert [p.arxiv_id for p in papers] == ["2607.00001", "2607.00002", "2607.00003"]


def test_parse_atom():
    papers = parse_atom(FIXTURE)
    assert len(papers) == 2

    p = papers[0]
    assert p.arxiv_id == "2507.01234"  # version suffix stripped
    assert p.title == "Cross-Vendor DDS Discovery for ROS 2 over Lossy Links"
    assert p.authors == ["Alice Example", "Bob Sample"]
    assert p.categories == ["cs.RO", "cs.NI"]
    assert p.published == datetime(2026, 7, 8, 12, 34, 56, tzinfo=timezone.utc)
    assert p.pdf_url == "https://arxiv.org/pdf/2507.01234"
    assert p.abs_url == "https://arxiv.org/abs/2507.01234"
    assert "QoS matching" in p.abstract

    assert papers[1].arxiv_id == "2507.05678"


def test_get_page_retries_on_429(monkeypatch):
    codes = iter([429, 200])
    slept = []
    monkeypatch.setattr(fetch.time, "sleep", slept.append)

    class Resp:
        def __init__(self, code):
            self.status_code, self.headers, self.text = code, {"Retry-After": "7"}, "<feed/>"

        def raise_for_status(self):
            if self.status_code >= 400:
                raise AssertionError(f"unexpected raise for {self.status_code}")

    monkeypatch.setattr(fetch.requests, "get", lambda *a, **k: Resp(next(codes)))
    assert fetch._get_page("cat:cs.CV", 0, 100) == "<feed/>"
    assert slept == [7]  # honoured Retry-After, then succeeded


def test_get_page_retries_transport_errors(monkeypatch):
    import requests as rq

    attempts = []
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)

    class Resp:
        status_code, headers, text = 200, {}, "<feed/>"

        def raise_for_status(self):
            pass

    def flaky(*a, **k):
        attempts.append(1)
        if len(attempts) == 1:
            raise rq.Timeout("read timed out")
        if len(attempts) == 2:
            raise rq.ConnectionError("reset")
        return Resp()

    monkeypatch.setattr(fetch.requests, "get", flaky)
    assert fetch._get_page("cat:cs.CV", 0, 100) == "<feed/>"
    assert len(attempts) == 3


def test_get_page_gives_up_loudly(monkeypatch):
    import requests as rq

    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    monkeypatch.setattr(fetch.requests, "get",
                        lambda *a, **k: (_ for _ in ()).throw(rq.Timeout("nope")))
    with pytest.raises(RuntimeError, match="arXiv unreachable"):
        fetch._get_page("cat:cs.CV", 0, 100)


def test_get_page_does_not_retry_client_errors(monkeypatch):
    import requests as rq

    calls = []

    class Bad:
        status_code, headers, text = 400, {}, "bad query"

        def raise_for_status(self):
            raise rq.HTTPError("400 Bad Request")

    def once(*a, **k):
        calls.append(1)
        return Bad()

    monkeypatch.setattr(fetch.requests, "get", once)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: pytest.fail("must not retry a 400"))
    with pytest.raises(rq.HTTPError):
        fetch._get_page("cat:cs.CV", 0, 100)
    assert len(calls) == 1


def _utc(*a):
    return datetime(*a, tzinfo=timezone.utc)


def test_window_ends_on_last_announced_friday_batch():
    """W47 run: Fri 13 Nov 14:00 EST batch was announced Sun 15 Nov 20:00 EST."""
    assert batch_window(NOW, 7) == (_utc(2026, 11, 6, 19), _utc(2026, 11, 13, 19))


def test_window_skips_batch_not_yet_announced():
    """One minute before Sun 20:00 ET the latest Friday batch isn't public yet."""
    before = _utc(2026, 11, 16, 0, 59)  # Sun 15 Nov 19:59 EST
    assert batch_window(before, 7)[1] == _utc(2026, 11, 6, 19)
    assert batch_window(before + timedelta(minutes=1), 7)[1] == _utc(2026, 11, 13, 19)


def test_window_keeps_14h_et_across_dst_end():
    """DST ended Sun 1 Nov: start is 14:00 EDT (18:00 UTC), end 14:00 EST (19:00 UTC)."""
    assert batch_window(_utc(2026, 11, 9, 15), 7) == (_utc(2026, 10, 30, 18), _utc(2026, 11, 6, 19))


def test_consecutive_runs_tile_without_gap_or_overlap():
    """Monday runs at any hour, a week apart, share their boundary exactly."""
    a = batch_window(_utc(2026, 11, 9, 6), 7)
    b = batch_window(_utc(2026, 11, 16, 15, 43), 7)
    assert a[1] == b[0]


def test_query_is_bounded_server_side():
    q = fetch._with_window("abs:x", START, END)
    assert q == "(abs:x) AND submittedDate:[202611061900 TO 202611131859]"


def test_papers_after_window_end_are_dropped_and_flagged(monkeypatch, caplog):
    """If the server range and <published> ever disagree, we drop and warn."""
    times = [END + timedelta(hours=1), END - timedelta(hours=1), START - timedelta(hours=1)]
    def fake_get_page(query, start, count):
        entries = "".join(_entry(i, t) for i, t in enumerate(times))
        return f'<feed xmlns="http://www.w3.org/2005/Atom">{entries}</feed>'
    monkeypatch.setattr(fetch, "_get_page", fake_get_page)
    papers = fetch_papers(_cfg(max_candidates=100), now=NOW)
    assert [p.arxiv_id for p in papers] == ["2607.00001"]
    assert "dropped 1 papers published after the window end" in caplog.text
