"""Smoke-test scripts/validate_rentora_skill.py."""

import subprocess
import sys
from pathlib import Path


def test_validate_rentora_skill_script():
    repo = Path(__file__).resolve().parent.parent
    script = repo / "scripts" / "validate_rentora_skill.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
