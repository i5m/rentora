"""Validate the Agent Skill package under skills/rentora/.

Checks YAML frontmatter (agentskills.io naming rules), required files,
and that assets/sample-request.json matches Pydantic tool inputs.

Usage:
    uv run python scripts/validate_rentora_skill.py

Optional ecosystem validator (warn-only if missing):
    skills-ref validate ./skills/rentora
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SKILL_ROOT = _REPO_ROOT / "skills" / "rentora"
_SKILL_MD = _SKILL_ROOT / "SKILL.md"
_SAMPLE_JSON = _SKILL_ROOT / "assets" / "sample-request.json"

_REQUIRED_PATHS = [
    _SKILL_ROOT / "references" / "tool-reference.md",
    _SKILL_ROOT / "references" / "presentation-rules.md",
    _SKILL_ROOT / "references" / "semantics.md",
]

_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _prepend_src_path() -> None:
    src = _REPO_ROOT / "src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))


def _validate_frontmatter(data: dict) -> list[str]:
    errs: list[str] = []
    name = data.get("name")
    if not isinstance(name, str) or not name:
        errs.append("frontmatter missing non-empty string field 'name'")
        return errs
    if name != _SKILL_ROOT.name:
        errs.append(f"name '{name}' must match directory {_SKILL_ROOT.name!r}")
    if not _NAME_PATTERN.fullmatch(name):
        errs.append(
            "name must be lowercase alphanumeric with single hyphens "
            "(no leading/trailing/double hyphen)"
        )
    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        errs.append("frontmatter missing non-empty string field 'description'")
    elif not (1 <= len(desc) <= 1024):
        errs.append(f"description length must be 1..1024 chars, got {len(desc)}")
    return errs


def _parse_skill_md(path: Path) -> tuple[dict, list[str]]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, ["SKILL.md must start with YAML frontmatter ---"]
    rest = text.removeprefix("---").lstrip("\n")
    end = rest.find("\n---\n")
    if end == -1:
        return {}, ["SKILL.md missing closing --- after frontmatter"]
    fm_raw = rest[:end]
    try:
        data = yaml.safe_load(fm_raw)
    except yaml.YAMLError as e:
        return {}, [f"Invalid YAML frontmatter: {e}"]
    if not isinstance(data, dict):
        return {}, ["Frontmatter must parse to a mapping"]
    return data, []


def _validate_sample_json(path: Path) -> list[str]:
    _prepend_src_path()
    from models import (
        HelocInput,
        HouseInput,
        InflationInput,
        InvestmentInput,
        LocationInput,
        RentInput,
    )

    class RentVsBuyToolPayload(BaseModel):
        location: LocationInput
        rent: RentInput
        house: HouseInput
        inflation: InflationInput
        investments: InvestmentInput
        heloc: HelocInput
        years_to_simulate: int = Field(ge=1)

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"sample-request.json is not valid JSON: {e}"]
    try:
        RentVsBuyToolPayload.model_validate(raw)
    except Exception as e:
        return [f"sample-request.json failed Pydantic validation: {e}"]
    return []


def _maybe_skills_ref() -> None:
    exe = shutil.which("skills-ref")
    if not exe:
        print("(optional) skills-ref not on PATH; skip external validation.")
        return
    try:
        subprocess.run(
            [exe, "validate", str(_SKILL_ROOT)],
            cwd=_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        print("skills-ref validate: OK")
    except subprocess.CalledProcessError as e:
        print("skills-ref validate: FAILED (non-blocking)\n", e.stderr or e.stdout, file=sys.stderr)


def main() -> int:
    errs: list[str] = []
    if not _SKILL_MD.is_file():
        print(f"FAIL: missing {_SKILL_MD}", file=sys.stderr)
        return 1

    fm, perrs = _parse_skill_md(_SKILL_MD)
    errs.extend(perrs)
    if fm:
        errs.extend(_validate_frontmatter(fm))

    for rel in _REQUIRED_PATHS:
        if not rel.is_file():
            errs.append(f"missing required file {rel.relative_to(_REPO_ROOT)}")

    if not _SAMPLE_JSON.is_file():
        errs.append(f"missing {_SAMPLE_JSON.relative_to(_REPO_ROOT)}")
    else:
        errs.extend(_validate_sample_json(_SAMPLE_JSON))

    if errs:
        for line in errs:
            print(f"FAIL: {line}", file=sys.stderr)
        return 1

    print("Agent skill validation passed.")
    _maybe_skills_ref()
    return 0


if __name__ == "__main__":
    sys.exit(main())
