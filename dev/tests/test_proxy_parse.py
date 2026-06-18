"""Tests for proxy.py URL parsing and request rewriting logic."""

import json
from urllib.parse import urlparse


# ── URL parsing (mirrors proxy.py logic) ─────────────────────────────────────

def _parse_target(raw: str):
    parsed = urlparse(raw if "://" in raw else "https://" + raw)
    return {
        "host": parsed.hostname or "",
        "port": parsed.port or 443,
        "prefix": parsed.path.rstrip("/"),
    }


class TestTargetParsing:
    def test_full_url(self):
        r = _parse_target("https://api.example.com/abc")
        assert r["host"] == "api.example.com"
        assert r["port"] == 443
        assert r["prefix"] == "/abc"

    def test_host_and_path_no_scheme(self):
        r = _parse_target("api.example.com/abc")
        assert r["host"] == "api.example.com"
        assert r["prefix"] == "/abc"

    def test_bare_hostname(self):
        r = _parse_target("api.example.com")
        assert r["host"] == "api.example.com"
        assert r["prefix"] == ""

    def test_custom_port(self):
        r = _parse_target("https://api.example.com:8443/abc")
        assert r["port"] == 8443
        assert r["prefix"] == "/abc"

    def test_empty_string(self):
        r = _parse_target("")
        assert r["host"] == ""
        assert r["prefix"] == ""

    def test_deep_path(self):
        r = _parse_target("https://api.example.com/a/b/c")
        assert r["prefix"] == "/a/b/c"

    def test_trailing_slash_stripped(self):
        r = _parse_target("https://api.example.com/abc/")
        assert r["prefix"] == "/abc"


# ── Path rewriting ────────────────────────────────────────────────────────────

class TestPathRewriting:
    def _rewrite(self, prefix: str, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return prefix + path

    def test_prefix_prepended(self):
        assert self._rewrite("/abc", "/v1/messages") == "/abc/v1/messages"

    def test_empty_prefix(self):
        assert self._rewrite("", "/v1/messages") == "/v1/messages"

    def test_path_without_leading_slash(self):
        assert self._rewrite("/abc", "v1/messages") == "/abc/v1/messages"


# ── Request body rewriting ────────────────────────────────────────────────────

MODEL_MAPPING = {"claude-haiku-4-5-20251001": "claude-haiku-4-5"}


def _rewrite_body(data: dict) -> dict:
    """Mirrors the JSON rewriting in proxy.py forward()."""
    data = dict(data)
    if "model" in data and data["model"] in MODEL_MAPPING:
        data["model"] = MODEL_MAPPING[data["model"]]
    if data.get("top_p") == -1:
        data.pop("top_p")
    if data.get("top_k") == -1:
        data.pop("top_k")
    data.pop("context_management", None)
    return data


class TestBodyRewriting:
    def test_model_mapping_applied(self):
        result = _rewrite_body({"model": "claude-haiku-4-5-20251001"})
        assert result["model"] == "claude-haiku-4-5"

    def test_unknown_model_unchanged(self):
        result = _rewrite_body({"model": "some-other-model"})
        assert result["model"] == "some-other-model"

    def test_top_p_minus1_removed(self):
        result = _rewrite_body({"top_p": -1, "model": "x"})
        assert "top_p" not in result

    def test_top_p_valid_kept(self):
        result = _rewrite_body({"top_p": 0.9, "model": "x"})
        assert result["top_p"] == 0.9

    def test_top_k_minus1_removed(self):
        result = _rewrite_body({"top_k": -1})
        assert "top_k" not in result

    def test_context_management_removed(self):
        result = _rewrite_body({"context_management": {"type": "auto"}})
        assert "context_management" not in result

    def test_other_fields_preserved(self):
        data = {"model": "x", "max_tokens": 100, "messages": []}
        result = _rewrite_body(data)
        assert result["max_tokens"] == 100
        assert result["messages"] == []
