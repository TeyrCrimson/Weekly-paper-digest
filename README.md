# Weekly paper digest

Every Monday a GitHub Actions cron job fetches the last week's arXiv papers
in your configured categories, ranks them against your topic list with a
cheap Haiku call, deep-analyzes the top N with Sonnet, and commits one
Markdown digest per paper to `digests/YYYY-Www/` — including a weekly
`index.md` with scores, matched topics, and token/cost totals.

All LLM calls go through **Claude Code in headless mode** (`claude -p`),
billed against a **Claude subscription** (Pro/Max/Team/Enterprise) via an
OAuth token — not the pay-per-token API. There is no `anthropic` SDK and no
`ANTHROPIC_API_KEY` anywhere in this project; keep it that way (see
[Billing verification](#first-run-billing-verification)).

## Setup

1. **Generate the OAuth token** (locally, once, on a machine where Claude
   Code is installed and logged into your subscription account):

   ```
   claude setup-token
   ```

   ⚠️ **The token lasts about one year.** Put a calendar reminder to
   regenerate it — the workflow will start failing silently on auth when it
   expires. (Token generated: check your repo secret's "updated" date.)

2. **Add it as a repo secret** named `CLAUDE_CODE_OAUTH_TOKEN`
   (Settings → Secrets and variables → Actions → New repository secret).
   Never commit it, and never add an `ANTHROPIC_API_KEY` secret.

3. **Adjust `config/topics.yaml`** (see below) and push. The workflow runs
   Mondays 06:00 UTC, or trigger it manually via Actions → weekly-digest →
   Run workflow.

## First-run billing verification

**Do this once after the first scheduled run.** There is a reported bug
where `claude -p` with an OAuth token can bill as API usage for accounts
that also have an API organization:
[anthropics/claude-code#43333](https://github.com/anthropics/claude-code/issues/43333).

- Check the **claude.ai subscription usage dashboard** — the run's usage
  should appear there.
- Check the **Anthropic API console** — it should show **no** new usage.

If usage lands on the API side, stop the schedule and investigate before
the next run.

## Local dev (WSL2 / Linux)

```bash
claude /login                # once, with the subscription account
pip install -r requirements.txt

# zero-cost smoke test: fetch + keyword pre-rank, NO LLM calls at all
python -m paperdigest.main --config config/topics.yaml --dry-run

# full run (Haiku ranking + top-N Sonnet analyses)
python -m paperdigest.main --config config/topics.yaml

pytest                       # no network, no subprocess — all canned fixtures
```

## Adding a topic

Edit `config/topics.yaml`:

```yaml
topics:
  - name: "Short display name"
    description: >
      What the ranker actually sees — spend your effort here. Name the
      subproblems, methods, and keywords that make a paper relevant.
```

The `description` matters far more than `name`. Also check
`arxiv_categories` covers where such papers get posted.

Keep `top_n` modest (default 10): each analyzed paper is one Sonnet call,
and subscription plans have rolling usage limits.

## Architecture

```
config/topics.yaml
  → fetch.py    arXiv API, last lookback_days, ≤ max_candidates papers
  → rank.py     one batched Haiku call scores relevance 0–10 vs topics
  → analyze.py  top_n papers ≥ min_relevance_score: PDF → text → one Sonnet call
  → render.py   digests/YYYY-Www/: one .md per paper + index.md
```

Stages communicate via dataclasses in `models.py`; `main.py` orchestrates.
All LLM access goes through `llm.py`, which shells out to
`claude -p … --output-format json`.

## SDK fallback (documented, not default)

If you ever want to switch to the `anthropic` Python SDK (pay-per-token),
**only `llm.py` changes**: reimplement `complete(prompt, system, model) ->
LLMResult` on top of the SDK and map model aliases to model IDs. No other
module knows how completions happen. This is deliberately not the default —
the subscription is the cost decision this project is built around.
