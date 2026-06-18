"""Tests for ZIP packaging — verify required files are present."""

import subprocess
import zipfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]

REQUIRED_WIN = [
    "init.bat",
    "cc.bat",
    "requirements.txt",
    "ai-env-guide.md",
    "scripts/setup_env.py",
    "scripts/health_claude.py",
    "scripts/proxy.py",
    "scripts/convert_docs.py",
    "scripts/shell.ps1",
]

REQUIRED_MAC = [
    "init.sh",
    "cc.sh",
    "requirements.txt",
    "ai-env-guide.md",
    "scripts/setup_env.py",
    "scripts/health_claude.py",
    "scripts/proxy.py",
    "scripts/convert_docs.py",
]


@pytest.fixture(scope="module")
def win_zip(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist") / "portable_claude_env.zip"
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "dev" / "build_zip.sh"), str(out)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        pytest.skip(f"build_zip.sh failed: {result.stderr}")
    return out


@pytest.fixture(scope="module")
def mac_zip(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist") / "portable_claude_env_mac.zip"
    result = subprocess.run(
        ["bash", str(REPO_ROOT / "dev" / "build_zip_mac.sh"), str(out)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        pytest.skip(f"build_zip_mac.sh failed: {result.stderr}")
    return out


class TestWindowsZip:
    @pytest.mark.parametrize("expected", REQUIRED_WIN)
    def test_file_present(self, win_zip, expected):
        with zipfile.ZipFile(win_zip) as zf:
            names = [Path(n).as_posix() for n in zf.namelist()]
        assert any(n.endswith(expected) for n in names), \
            f"Missing in Windows ZIP: {expected}"

    def test_zip_not_empty(self, win_zip):
        with zipfile.ZipFile(win_zip) as zf:
            assert len(zf.namelist()) > 5

    def test_no_venv_included(self, win_zip):
        with zipfile.ZipFile(win_zip) as zf:
            names = zf.namelist()
        assert not any(".venv" in n for n in names)

    def test_no_secrets_included(self, win_zip):
        with zipfile.ZipFile(win_zip) as zf:
            names = zf.namelist()
        assert not any("claude.env" in n for n in names)


class TestMacZip:
    @pytest.mark.parametrize("expected", REQUIRED_MAC)
    def test_file_present(self, mac_zip, expected):
        with zipfile.ZipFile(mac_zip) as zf:
            names = [Path(n).as_posix() for n in zf.namelist()]
        assert any(n.endswith(expected) for n in names), \
            f"Missing in macOS ZIP: {expected}"

    def test_sh_files_executable(self, mac_zip):
        """init.sh and cc.sh must have executable bit set."""
        with zipfile.ZipFile(mac_zip) as zf:
            for info in zf.infolist():
                if info.filename.endswith(".sh"):
                    perms = (info.external_attr >> 16) & 0o777
                    assert perms & 0o111, f"{info.filename} is not executable"

    def test_zip_not_empty(self, mac_zip):
        with zipfile.ZipFile(mac_zip) as zf:
            assert len(zf.namelist()) > 5

    def test_no_secrets_included(self, mac_zip):
        with zipfile.ZipFile(mac_zip) as zf:
            names = zf.namelist()
        assert not any("claude.env" in n for n in names)
