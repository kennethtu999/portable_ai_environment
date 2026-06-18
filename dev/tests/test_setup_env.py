"""Tests for setup_env.py — env file writing and reading."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

SCRIPTS_DIR = Path(__file__).parents[2] / "app" / "scripts"


def _load_module(env_file: Path):
    """Import setup_env with a patched ENV_FILE path."""
    import importlib
    import types

    spec = importlib.util.spec_from_file_location("setup_env", SCRIPTS_DIR / "setup_env.py")
    mod = importlib.util.module_from_spec(spec)

    # Patch before exec so the module-level code uses our paths
    with patch.dict("os.environ", {}, clear=False):
        with patch("builtins.input", side_effect=EOFError):
            with patch("getpass.getpass", side_effect=EOFError):
                try:
                    spec.loader.exec_module(mod)
                except (SystemExit, EOFError):
                    pass
    return mod


@pytest.fixture
def env_file(tmp_path):
    return tmp_path / "claude.env"


@pytest.fixture
def write_proxy(env_file):
    """Return _write_proxy bound to a temp ENV_FILE."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("se", SCRIPTS_DIR / "setup_env.py")
    src = spec.loader.get_source("se")

    # Compile and exec only the function definitions
    import ast, types
    tree = ast.parse(src)
    # Extract only function/class/constant defs (skip module-level side effects)
    safe_nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.Assign, ast.Import, ast.ImportFrom))]
    safe_tree = ast.Module(body=safe_nodes, type_ignores=[])
    ast.fix_missing_locations(safe_tree)

    ns = {"__builtins__": __builtins__, "ENV_FILE": env_file, "Path": Path}
    exec(compile(safe_tree, "setup_env.py", "exec"), ns)
    return ns["_write_proxy"], ns["_write_direct"], ns["_read_env"], env_file


class TestWriteProxy:
    def test_base_url_is_localhost(self, write_proxy):
        _write_proxy, _, _, env_file = write_proxy
        _write_proxy("token123", "8889", "api.example.com/ica", "claude-haiku-4-5-20251001")
        content = env_file.read_text()
        assert "ANTHROPIC_BASE_URL=\"http://127.0.0.1:8889\"" in content

    def test_token_saved(self, write_proxy):
        _write_proxy, _, _, env_file = write_proxy
        _write_proxy("mytoken", "8888", "host", "model")
        assert 'ANTHROPIC_AUTH_TOKEN="mytoken"' in env_file.read_text()

    def test_proxy_target_host_saved(self, write_proxy):
        _write_proxy, _, _, env_file = write_proxy
        _write_proxy("tok", "8888", "api.example.com/ica", "model")
        assert 'PROXY_TARGET_HOST="api.example.com/ica"' in env_file.read_text()

    def test_proxy_port_saved(self, write_proxy):
        _write_proxy, _, _, env_file = write_proxy
        _write_proxy("tok", "9000", "host", "model")
        assert 'PROXY_PORT="9000"' in env_file.read_text()


class TestWriteDirect:
    def test_full_url_used_as_base(self, write_proxy):
        _, _write_direct, _, env_file = write_proxy
        _write_direct("tok", "https://api.example.com/ica", "model")
        assert 'ANTHROPIC_BASE_URL="https://api.example.com/ica"' in env_file.read_text()

    def test_bare_host_gets_https(self, write_proxy):
        _, _write_direct, _, env_file = write_proxy
        _write_direct("tok", "api.example.com", "model")
        assert 'ANTHROPIC_BASE_URL="https://api.example.com"' in env_file.read_text()

    def test_host_with_path_no_scheme(self, write_proxy):
        _, _write_direct, _, env_file = write_proxy
        _write_direct("tok", "api.example.com/ica", "model")
        assert 'ANTHROPIC_BASE_URL="https://api.example.com/ica"' in env_file.read_text()

    def test_trailing_slash_stripped(self, write_proxy):
        _, _write_direct, _, env_file = write_proxy
        _write_direct("tok", "https://api.example.com/ica/", "model")
        content = env_file.read_text()
        assert 'ANTHROPIC_BASE_URL="https://api.example.com/ica"' in content


class TestReadEnv:
    def test_reads_key_value(self, write_proxy):
        _, _, _read_env, env_file = write_proxy
        env_file.write_text('FOO="bar"\nBAZ="qux"\n', encoding="utf-8")
        result = _read_env()
        assert result["FOO"] == "bar"
        assert result["BAZ"] == "qux"

    def test_skips_comments(self, write_proxy):
        _, _, _read_env, env_file = write_proxy
        env_file.write_text('# comment\nKEY="val"\n', encoding="utf-8")
        result = _read_env()
        assert "# comment" not in result
        assert result["KEY"] == "val"

    def test_empty_file(self, write_proxy):
        _, _, _read_env, env_file = write_proxy
        env_file.write_text("", encoding="utf-8")
        assert _read_env() == {}

    def test_strips_quotes(self, write_proxy):
        _, _, _read_env, env_file = write_proxy
        env_file.write_text('KEY="value with spaces"\n', encoding="utf-8")
        assert _read_env()["KEY"] == "value with spaces"
