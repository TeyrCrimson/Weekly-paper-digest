"""Stage 4: write one .md per analyzed paper plus the weekly index.md."""
from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from paperdigest.models import Analysis


def render_digests(digests_root: Path, analyses: list[Analysis],
                   usage_log: list[dict], run_time: datetime) -> Path:
    """Write digests/YYYY-Www/. Idempotent: an existing week folder is replaced."""
    iso = run_time.isocalendar()
    week_dir = digests_root / f"{iso.year}-W{iso.week:02d}"
    if week_dir.exists():
        shutil.rmtree(week_dir)
    week_dir.mkdir(parents=True)

    rows = []
    for a in analyses:
        p = a.ranked.paper
        title = p.title.replace("|", "\\|")
        topics = ", ".join(a.ranked.matched_topics) or "—"
        if a.error:
            rows.append(f"| {title} | {a.ranked.score} | {topics} | ⚠ analysis skipped: {a.error} |")
            continue
        fname = f"{p.arxiv_id}-{_slug(p.title)}.md"
        (week_dir / fname).write_text(_paper_md(a), encoding="utf-8")
        rows.append(f"| [{title}]({fname}) | {a.ranked.score} | {topics} | {a.ranked.one_liner} |")

    (week_dir / "index.md").write_text(_index_md(rows, usage_log, run_time), encoding="utf-8")
    return week_dir


def _paper_md(a: Analysis) -> str:
    p = a.ranked.paper
    matched = ", ".join(a.ranked.matched_topics) or "—"
    return (
        f"# {p.title}\n\n"
        f"**Authors:** {', '.join(p.authors)}\n\n"
        f"**arXiv:** [{p.arxiv_id}]({p.abs_url})\n\n"
        f"**Categories:** {', '.join(p.categories)}\n\n"
        f"**Submitted:** {p.published:%Y-%m-%d}\n\n"
        f"**Relevance:** {a.ranked.score}/10 — matched: {matched}\n\n"
        f"---\n\n"
        f"{a.markdown.strip()}\n"
    )


def _index_md(rows: list[str], usage_log: list[dict], run_time: datetime) -> str:
    body = "\n".join(rows) if rows else "_No papers met the relevance threshold this week._"
    tokens_in = sum(u.get("input_tokens", 0) for u in usage_log)
    tokens_out = sum(u.get("output_tokens", 0) for u in usage_log)
    cost = sum(u.get("cost_usd", 0) or 0 for u in usage_log)
    return (
        f"# Weekly paper digest\n\n"
        f"| Title | Score | Topics | One-liner |\n"
        f"|---|---|---|---|\n"
        f"{body}\n\n"
        f"---\n\n"
        f"_Run: {run_time:%Y-%m-%d %H:%M} UTC · {len(usage_log)} LLM calls · "
        f"{tokens_in} in / {tokens_out} out tokens · reported cost ${cost:.4f} "
        f"(subscription usage — should be $0 on API billing)_\n"
    )


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40].rstrip("-")
