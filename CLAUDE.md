# CLAUDE.md — Weekly Paper Digest

## What this project is

A weekly pipeline that fetches new research papers from arXiv, ranks them
against a user-defined topic list, deep-analyzes the top N, and writes one
Markdown digest per paper. Runs unattended on a GitHub Actions cron
schedule; digests are committed back to this repo.

LLM calls go through the **Claude Code CLI in headless mode** (`claude -p`),
authenticated with a **Claude subscription OAuth token** — NOT the
`anthropic` Python SDK and NOT a pay-per-token API key. See "LLM access"
below. This is a deliberate cost decision; do not "simplify" to the SDK.

Repo: https://github.com/TeyrCrimson/Weekly-paper-digest

## Architecture (keep this pipeline shape)

```
config/topics.yaml
        │
  [1] fetch.py    — arXiv API: papers from last `lookback_days` in configured categories
        │
  [2] rank.py     — one cheap LLM call (Haiku) scores relevance 0–10 per paper vs topics
        │
  [3] analyze.py  — top N papers only: download PDF, extract text, one Sonnet call each
        │
  [4] render.py   — one .md per paper + a weekly index.md
        │
  digests/YYYY-Www/   (committed by the Actions workflow)
```

Each stage is a module with a single public function. Stages communicate via
plain dataclasses (`Paper`, `RankedPaper`, `Analysis`) defined in `models.py`.
No stage imports another stage; `main.py` orchestrates. All LLM access goes
through ONE module, `llm.py` — rank.py and analyze.py never call subprocess
directly.

## LLM access — llm.py (the load-bearing module)

- Public function: `complete(prompt: str, system: str, model: str) -> LLMResult`
  where `LLMResult` carries `text`, `usage` (tokens), and `raw` (parsed JSON).
- Implementation: `subprocess.run` of
  `claude -p <prompt> --system-prompt <system> --model <model> --output-format json`
  with a timeout (default 300 s) and `check`-style error handling. Parse the
  JSON envelope for the result text and usage/cost fields.
- Pass model aliases from config (`haiku`, `sonnet`) straight to `--model`.
- No tools: these are pure completions. Do not grant any tool permissions;
  headless mode denies un-granted tool use by default, which is what we want.
- Auth is ambient: the `CLAUDE_CODE_OAUTH_TOKEN` env var (CI) or an existing
  `claude /login` session (local dev). llm.py must NOT read or handle
  credentials itself. Docs: https://code.claude.com/docs/en/authentication
- Do NOT set `ANTHROPIC_API_KEY` anywhere — if present it takes precedence
  over the subscription and silently switches billing to per-token API rates.
  llm.py should emit a loud warning at import time if that env var is set.
- Do NOT use `--bare`; bare mode does not read `CLAUDE_CODE_OAUTH_TOKEN`.
- Retry once on malformed JSON or nonzero exit, then raise.
- Fallback (documented, not default): if the user ever wants SDK access,
  only llm.py changes. Keep this boundary clean.

Headless reference: https://code.claude.com/docs/en/headless

## Code style (non-negotiable)

- Python 3.11+, type hints everywhere.
- Short, verifiable functions: aim ≤ 25 lines, one responsibility, pure where
  possible. I/O (network, disk, subprocess) isolated in thin wrappers so
  logic is unit-testable without mocks-on-mocks.
- No classes unless holding state genuinely simplifies things. Dataclasses
  for data, functions for behavior.
- Fail loudly: raise on malformed config or API errors; never silently skip
  a paper without logging why.
- Dependencies: `requests` (or `arxiv` pip package), `pyyaml`, `pypdf`,
  `jinja2`. NO `anthropic` SDK. Nothing heavier without discussion.

## Config schema — `config/topics.yaml`

```yaml
topics:
  - name: "DDS interoperability in ROS 2"
    description: >
      Cross-vendor DDS (CycloneDDS/FastDDS) interop, QoS matching,
      discovery over constrained networks.
  - name: "Delay-compensated perception for mobile robots"
    description: >
      State estimation and control under sensing latency; delayed
      measurement fusion, Kalman rewind/replay.

arxiv_categories: [cs.RO, eess.SY, cs.LG]
lookback_days: 7
max_candidates: 200        # hard cap on fetched papers
top_n: 10                  # papers that get full analysis
min_relevance_score: 6     # skip analysis below this even if in top_n

ranking_model: haiku       # Claude Code --model alias
analysis_model: sonnet
```

The `description` field is what the ranker sees — it matters more than `name`.

## Analysis prompt requirements (analyze.py)

Each digest .md must contain, in order:

1. **Metadata** — title, authors, arXiv link, categories, submission date,
   relevance score + which topics it matched. (Assembled in code, not by
   the model.)
2. **TL;DR** — 3 sentences max.
3. **First-principles breakdown** — every complex concept/method in the paper
   explained from the ground up, assuming a strong engineer who is not a
   specialist in this subfield. Build up: what problem, why prior approaches
   fail, what this paper's mechanism actually does step by step.
4. **Key insights** — what is genuinely new or useful; distinguish claimed
   contributions from what the evidence actually supports.
5. **Caveats — stated and inferred** — limitations the authors admit, PLUS
   red flags inferable from the text: simulation-only evaluation, weak or
   stale baselines, missing ablations, cherry-picked metrics, unrealistic
   assumptions. Label each caveat as `stated` or `inferred`. Do not invent
   caveats without textual grounding.

Instruct the model to say "not addressed in the paper" rather than
speculate. Pass the extracted full text (truncate to ~80k chars if needed,
keeping abstract + intro + method + experiments + conclusion preferentially).

## Output layout

```
digests/
  2026-W27/
    index.md                  # table: title | score | topics | one-liner
    2506.01234-short-slug.md
    ...
```

Idempotent: re-running a week overwrites that week's folder.

## Scheduling — GitHub Actions

`.github/workflows/weekly.yml`:
- `on: schedule: - cron: "0 6 * * 1"` (Mondays 06:00 UTC) plus
  `workflow_dispatch` for manual runs.
- Steps: checkout → setup-python → setup-node →
  `npm install -g @anthropic-ai/claude-code` →
  `pip install -r requirements.txt` → `python -m paperdigest.main` →
  commit & push `digests/` with `github-actions[bot]` identity.
- Auth: `CLAUDE_CODE_OAUTH_TOKEN` from repo secrets, exported as an env var
  for the run step. Generated once locally with `claude setup-token`
  (requires Pro/Max/Team/Enterprise; token lasts ~1 year — put an expiry
  reminder in the README). Never commit it; never set ANTHROPIC_API_KEY.
- Note: GitHub cron can drift/skip under load — the run must tolerate a
  `lookback_days` window rather than assume exactly-7-days gaps.

## Local dev

Runs fine on WSL2 (Ubuntu) with Claude Code installed and logged in
(`claude /login` with the subscription account):
```
python -m paperdigest.main --config config/topics.yaml --dry-run   # fetch+rank only? NO — see below
python -m paperdigest.main --config config/topics.yaml
```
`--dry-run` = fetch + heuristic keyword pre-rank only, NO LLM calls at all
(not even Haiku), prints the candidate table and exits. This is the
zero-cost smoke test for config and fetch logic.

## Testing

- `pytest` with fixture files: a canned arXiv Atom response, a canned PDF,
  canned `claude -p --output-format json` envelopes. No live network and no
  live subprocess in tests — llm.py's subprocess call is the only thing
  monkeypatched.
- Every stage's public function gets at least one test.
- Ranking output is JSON from the model: parse defensively, validate scores
  are ints 0–10, and fail the run (not silently) if the JSON is malformed
  after one retry.

## Usage guardrails

- Ranking: one batched Haiku call over titles+abstracts (chunk if >100).
- Analysis: `top_n` Sonnet calls max per week. Subscription plans have
  rolling usage limits, so keep top_n modest; spread is not needed since
  10 calls/week is well within limits.
- BILLING VERIFICATION (first run only): after the first scheduled run,
  confirm usage appears on the claude.ai subscription dashboard and NOT on
  the API console. There is a reported bug where `claude -p` with OAuth can
  bill as API usage for accounts that also have an API organization:
  https://github.com/anthropics/claude-code/issues/43333
  The README must tell the user to perform this check.
- Log the usage/cost fields from each JSON envelope into the week's
  `index.md` footer.
