# Build prompt — paste into Claude Code / Opus at repo root

Read CLAUDE.md in this repo first. It is the source of truth for
architecture, LLM access rules, code style, config schema, and output
format. Then build the project in the following phases. After each phase,
stop and show me the diff summary before continuing.

Critical constraint up front: all LLM calls go through `claude -p`
(headless Claude Code) via the single wrapper module `llm.py`,
authenticated by subscription OAuth. Do NOT import the `anthropic` SDK.
Do NOT reference or require ANTHROPIC_API_KEY anywhere.

## Phase 1 — Skeleton, models, llm.py
Create the package layout:
```
paperdigest/
  __init__.py
  models.py      # Paper, RankedPaper, Analysis, LLMResult dataclasses
  config.py      # load + validate topics.yaml, raise on any missing/invalid field
  llm.py         # the ONLY module that touches subprocess/claude
  fetch.py
  rank.py
  analyze.py
  render.py
  main.py        # argparse: --config, --dry-run; orchestrates the four stages
config/topics.yaml        # populate with the two example topics from CLAUDE.md
requirements.txt          # no anthropic SDK
tests/
```
Write `models.py`, `config.py`, and `llm.py` fully per the "LLM access"
section of CLAUDE.md, including: the import-time warning if
ANTHROPIC_API_KEY is set, the 300 s timeout, one retry on malformed
JSON/nonzero exit, and parsing of the `--output-format json` envelope
(result text + usage fields). Tests: config validation (valid file,
missing key, bad bounds) and llm.py with a monkeypatched subprocess
returning canned envelopes, including one malformed and one nonzero-exit
case.

## Phase 2 — fetch.py
Query the arXiv API (http://export.arxiv.org/api/query) for papers submitted
in the last `lookback_days` across `arxiv_categories`, up to `max_candidates`.
Respect arXiv's rate guidance (1 request / 3 s between pages). Parse the Atom
feed into `Paper` objects. Test against a canned Atom XML fixture.

## Phase 3 — rank.py
One batched call via `llm.complete(..., model=cfg.ranking_model)`: input is
the topic list (name + description) and the candidate papers (title +
abstract, numbered). Output: strict JSON array of
`{index, score, matched_topics, one_liner}`. Include the exact system prompt
as a module-level constant so I can review it. Parse defensively per
CLAUDE.md. Chunk candidates if more than 100 per call. Also implement the
zero-LLM heuristic pre-rank (keyword overlap against topic descriptions)
used by --dry-run. Test with canned model output including one
malformed-JSON case.

## Phase 4 — analyze.py
For each of the top N papers with score ≥ min_relevance_score: download the
PDF, extract text with pypdf, truncate per CLAUDE.md, and make one
`llm.complete(..., model=cfg.analysis_model)` call whose system prompt
demands digest sections 2–5 (metadata is assembled in code). The prompt
must include the stated/inferred caveat labeling rule and the "not
addressed in the paper" rule verbatim from CLAUDE.md. Return an `Analysis`
dataclass with the markdown body plus usage. Handle PDF download failure by
logging and skipping that paper (with a stub entry in the index noting the
failure).

## Phase 5 — render.py + main.py
Render per-paper .md files and the weekly index.md (table: title linked to
file, score, matched topics, one-liner; footer with total usage and run
timestamp). Wire up main.py: `--dry-run` = fetch + heuristic pre-rank only,
zero LLM calls, print candidate table, exit.

## Phase 6 — GitHub Actions + README
Write `.github/workflows/weekly.yml` per CLAUDE.md: Monday 06:00 UTC cron +
workflow_dispatch; setup-python; setup-node; install Claude Code CLI;
export CLAUDE_CODE_OAUTH_TOKEN from repo secrets; run; commit digests/
back. Write README.md covering: what the project does; generating the
token with `claude setup-token` and adding it as a repo secret (with the
~1-year expiry reminder); the first-run billing verification step from
CLAUDE.md's "Usage guardrails" (with the linked GitHub issue); local dev on
WSL2 (`claude /login`, then run); how to add a topic; and the documented
SDK fallback (only llm.py would change).

## Constraints reminder
- Short verifiable functions (≤ ~25 lines), type hints, dataclasses over
  classes, I/O isolated in thin wrappers.
- No live network or live subprocess calls in tests.
- Do not add dependencies beyond requirements.txt without asking.
- If any instruction here conflicts with CLAUDE.md, CLAUDE.md wins — flag
  the conflict instead of silently choosing.
