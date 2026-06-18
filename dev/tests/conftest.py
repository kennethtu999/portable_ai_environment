import sys
from pathlib import Path

# Make app/scripts importable
SCRIPTS_DIR = Path(__file__).parents[2] / "app" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import pytest


@pytest.fixture
def tmp_project(tmp_path):
    """Temp dir simulating: project-root/ with ai-env/ inside."""
    aienv = tmp_path / "ai-env"
    (aienv / "scripts").mkdir(parents=True)
    (aienv / "ai-state").mkdir()
    return tmp_path


@pytest.fixture
def aienv_dir(tmp_project):
    return tmp_project / "ai-env"
