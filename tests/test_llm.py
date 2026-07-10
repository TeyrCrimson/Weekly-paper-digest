import json
import subprocess

import pytest

from paperdigest import llm

GOOD_ENVELOPE = json.dumps({
    "type": "result",
    "result": "hello from the model",
    "usage": {"input_tokens": 100, "output_tokens": 20},
    "total_cost_usd": 0.001,
})


class FakeProc:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _patch_run(monkeypatch, procs):
    """subprocess.run returns each FakeProc in order."""
    it = iter(procs)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return next(it)

    monkeypatch.setattr(llm.subprocess, "run", fake_run)
    return calls


def test_good_envelope(monkeypatch):
    llm.USAGE_LOG.clear()
    calls = _patch_run(monkeypatch, [FakeProc(stdout=GOOD_ENVELOPE)])
    result = llm.complete("prompt", "system", "haiku")
    assert result.text == "hello from the model"
    assert result.usage["input_tokens"] == 100
    assert llm.USAGE_LOG == [
        {"model": "haiku", "input_tokens": 100, "output_tokens": 20, "cost_usd": 0.001}
    ]
    cmd, kwargs = calls[0]
    assert cmd[:2] == ["claude", "-p"]
    assert "prompt" not in cmd  # prompt travels via stdin, never argv (E2BIG)
    assert kwargs["input"] == "prompt"
    assert "--output-format" in cmd and "json" in cmd


def test_retry_on_malformed_json(monkeypatch):
    _patch_run(monkeypatch, [FakeProc(stdout="not json {"), FakeProc(stdout=GOOD_ENVELOPE)])
    assert llm.complete("p", "s", "haiku").text == "hello from the model"


def test_raises_after_two_nonzero_exits(monkeypatch):
    _patch_run(monkeypatch, [FakeProc(returncode=1, stderr="boom")] * 2)
    with pytest.raises(RuntimeError, match="after retry"):
        llm.complete("p", "s", "haiku")
