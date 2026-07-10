from datetime import datetime, timezone

import pytest

from paperdigest.config import Topic
from paperdigest.models import Paper


def make_paper(i: int = 0, **overrides) -> Paper:
    defaults = dict(
        arxiv_id=f"2507.0000{i}",
        title=f"Cross-vendor DDS discovery for ROS 2, part {i}",
        authors=["A. Author"],
        abstract="QoS matching and discovery for CycloneDDS/FastDDS interop.",
        categories=["cs.RO"],
        published=datetime(2026, 7, 8, tzinfo=timezone.utc),
        pdf_url=f"https://arxiv.org/pdf/2507.0000{i}",
        abs_url=f"https://arxiv.org/abs/2507.0000{i}",
    )
    return Paper(**{**defaults, **overrides})


@pytest.fixture
def topics() -> list[Topic]:
    return [
        Topic("DDS interoperability in ROS 2",
              "Cross-vendor DDS (CycloneDDS/FastDDS) interop, QoS matching, discovery."),
        Topic("Delay-compensated perception",
              "State estimation under sensing latency; Kalman rewind/replay."),
    ]
