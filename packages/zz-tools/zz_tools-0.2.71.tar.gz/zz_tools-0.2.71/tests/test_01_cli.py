import re
import subprocess
import sys


def test_cli_version_subprocess():
    # Vérifie que l’entrypoint "python -m mcgt --version" marche
    cmd = [sys.executable, "-m", "mcgt", "--version"]
    cp = subprocess.run(cmd, capture_output=True, text=True)
    assert cp.returncode == 0
    out = (cp.stdout or cp.stderr).strip()
    # match "0.1.x" ou "0.1.x.dev0"
    assert re.search(r"\b\d+\.\d+\.\d+(?:\.\w+)?\b", out)


def test_cli_help_subprocess():
    cmd = [sys.executable, "-m", "mcgt", "--help"]
    cp = subprocess.run(cmd, capture_output=True, text=True)
    assert cp.returncode == 0
    text = (cp.stdout or cp.stderr).lower()
    # heuristique: le help contient souvent "usage" ou "options"
    assert "usage" in text or "options" in text
