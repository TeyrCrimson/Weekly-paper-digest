"""Orchestrates fetch -> rank -> analyze -> render. The only module that
imports the stages."""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timezone
from pathlib import Path

from paperdigest import llm
from paperdigest.analyze import analyze_papers
from paperdigest.config import load_config
from paperdigest.fetch import fetch_papers
from paperdigest.models import RankedPaper
from paperdigest.rank import heuristic_rank, rank_papers
from paperdigest.render import render_digests

log = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = _parse_args(argv)
    cfg = load_config(args.config)
    papers = fetch_papers(cfg)

    if args.dry_run:  # fetch + heuristic pre-rank only, zero LLM calls
        _print_candidates(heuristic_rank(papers, cfg.topics))
        return

    ranked = rank_papers(papers, cfg)
    analyses = analyze_papers(ranked, cfg)
    week_dir = render_digests(Path("digests"), analyses, llm.USAGE_LOG,
                              datetime.now(timezone.utc))
    log.info("wrote %d digests to %s", len(analyses), week_dir)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Weekly arXiv paper digest")
    parser.add_argument("--config", default="config/topics.yaml")
    parser.add_argument("--dry-run", action="store_true",
                        help="fetch + keyword pre-rank only; no LLM calls")
    return parser.parse_args(argv)


def _print_candidates(ranked: list[RankedPaper]) -> None:
    print(f"{'score':>5}  {'arXiv id':<12}  title")
    for r in ranked:
        print(f"{r.score:>5}  {r.paper.arxiv_id:<12}  {r.paper.title[:90]}")


if __name__ == "__main__":
    main()
