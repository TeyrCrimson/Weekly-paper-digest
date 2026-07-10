"""The ONLY module that talks to the LLM, via `claude -p` (headless Claude Code).

Auth is ambient: CLAUDE_CODE_OAUTH_TOKEN in CI, or an existing `claude /login`
session locally. This module never reads or handles credentials.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess

from paperdigest.models import LLMResult

log = logging.getLogger(__name__)

TIMEOUT_S = 300

# Every completion appends its token/cost numbers here; render.py puts the
# totals in the weekly index footer.
USAGE_LOG: list[dict] = []

if os.environ.get("ANTHROPIC_API_KEY"):
    log.warning(
        "!!! ANTHROPIC_API_KEY is set. It takes precedence over the Claude "
        "subscription OAuth token and will silently bill per-token API rates. "
        "Unset it before running this pipeline. !!!"
    )


def complete(prompt: str, system: str, model: str) -> LLMResult:
    """One pure completion via `claude -p`. Retries once on nonzero exit or a
    malformed JSON envelope, then raises RuntimeError."""
    last_err: Exception | None = None
    for attempt in (1, 2):
        try:
            return _call(prompt, system, model)
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
            last_err = e
            log.warning("claude -p attempt %d/2 failed: %s", attempt, e)
    raise RuntimeError(f"claude -p failed after retry: {last_err!r}") from last_err


def _call(prompt: str, system: str, model: str) -> LLMResult:
    # Prompt goes on stdin, not argv: paper batches exceed the kernel's
    # per-argument size limit (E2BIG).
    cmd = [
        "claude", "-p",
        "--system-prompt", system,
        "--model", model,
        "--output-format", "json",
    ]
    proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                          timeout=TIMEOUT_S)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd[0], proc.stdout, proc.stderr)
    envelope = json.loads(proc.stdout)
    usage = envelope.get("usage", {})
    USAGE_LOG.append({
        "model": model,
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "cost_usd": envelope.get("total_cost_usd", 0) or 0,
    })
    return LLMResult(text=envelope["result"], usage=usage, raw=envelope)
