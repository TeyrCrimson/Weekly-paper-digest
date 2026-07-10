from datetime import datetime, timezone
from pathlib import Path

from paperdigest.fetch import parse_atom

FIXTURE = (Path(__file__).parent / "fixtures" / "arxiv_atom.xml").read_text()


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
