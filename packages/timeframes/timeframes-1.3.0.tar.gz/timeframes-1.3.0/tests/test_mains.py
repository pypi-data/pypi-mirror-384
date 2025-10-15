import subprocess
import sys
from pathlib import Path

# root of your package (adjust as needed)
PKG_DIR = Path(__file__).resolve().parents[1] / "timeframes"

def _scripts():
    """Yield all Python modules containing an if-main block."""
    for py in PKG_DIR.rglob("*.py"):
        if "__main__" in py.read_text(errors="ignore"):
            yield py

import pytest

@pytest.mark.parametrize("script", list(_scripts()))
def test_run_main_blocks(script):
    """Run each module as a standalone script to trigger its __main__ block."""
    res = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert res.returncode == 0, f"{script} failed:\n{res.stderr or res.stdout}"
