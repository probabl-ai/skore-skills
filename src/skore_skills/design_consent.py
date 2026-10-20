"""Decide whether a design note is approved before implementation."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from skore_skills.gate_context import design_context

_STATE = re.compile(r"^\s*-\s*\*\*State:\*\*\s*(.+?)\s*$", re.MULTILINE)
_STATE_LINE = re.compile(
    r"^(?P<prefix>\s*-\s*\*\*State:\*\*)(?P<value>[^\n]*)$",
    re.MULTILINE,
)
_APPROVED_LINE = re.compile(
    r"^(?P<prefix>\s*-\s*\*\*Approved by user on:\*\*)[^\n]*$",
    re.MULTILINE,
)
_PROCEED_STATES = frozenset({"approved", "running", "done"})
_APPROVABLE_STATES = frozenset({"", "planned"})
_ASK_CHOICES = ["approve", "modify", "stop"]


def _token(value: str) -> str:
    token = value.strip().strip("`")
    parts = token.split()
    if not parts:
        return ""
    return parts[0].lower().rstrip(".,;:")


def _state(text: str) -> str:
    match = _STATE.search(text)
    if match is None:
        return ""
    return _token(match.group(1))


def design_consent(root: Path, stem: str) -> dict[str, Any]:
    """Return the design-approval gate for ``stem``.

    Filesystem only: ``journal/<stem>.md`` Status. Does not run pytest.
    """
    cleaned = stem.strip()
    if not cleaned:
        raise ValueError("stem is required")

    from skore_skills.project_api import experiment_by_stem

    experiment = experiment_by_stem(root, cleaned)
    if experiment is not None:
        if experiment.status in {"backlog", "history"}:
            return {
                "stem": cleaned,
                "action": "proceed",
                "reason": "approved" if experiment.status == "backlog" else "done",
            }
        if experiment.status == "discarded":
            return {"stem": cleaned, "action": "stop", "reason": "abandoned"}
        return {
            "stem": cleaned,
            "action": "ask",
            "reason": "first_approval",
            "choices": list(_ASK_CHOICES),
            "context": {
                "note": experiment.id,
                "question": experiment.question,
                "source": experiment.source_id or "",
                "files_touched": "",
                "change": experiment.plan or "",
                "risks": [],
            },
        }

    path = root / "journal" / f"{cleaned}.md"
    if not path.is_file():
        return {"stem": cleaned, "action": "stop", "reason": "missing_design"}

    state = _state(path.read_text(encoding="utf-8"))
    if state == "abandoned":
        return {"stem": cleaned, "action": "stop", "reason": "abandoned"}
    if state in _PROCEED_STATES:
        return {"stem": cleaned, "action": "proceed", "reason": state}

    return {
        "stem": cleaned,
        "action": "ask",
        "reason": "first_approval",
        "choices": list(_ASK_CHOICES),
        "context": design_context(root, cleaned),
    }


def render_design_consent(root: Path, stem: str) -> str:
    """Serialize the design-consent gate as JSON."""
    return json.dumps(design_consent(root, stem), indent=2) + "\n"


def design_approve(
    root: Path, stem: str, *, today: date | None = None
) -> dict[str, Any]:
    """Stamp design approval for ``stem``.

    Writes ``journal/<stem>.md``. Sets State to ``approved`` and
    Approved by user on to ``today``. Accepts a ``planned`` or blank
    State. Does not overwrite an existing approval date.

    Raises
    ------
    ValueError
        When the note is missing, incomplete, or not awaiting approval.
    """
    cleaned = stem.strip()
    if not cleaned:
        raise ValueError("stem is required")

    path = root / "journal" / f"{cleaned}.md"
    if not path.is_file():
        raise ValueError("design note is missing")

    text = path.read_text(encoding="utf-8")
    state_line = _STATE_LINE.search(text)
    approved_line = _APPROVED_LINE.search(text)
    if state_line is None:
        raise ValueError("design note is missing State")
    if approved_line is None:
        raise ValueError("design note is missing Approved by user on")

    state = _token(state_line.group("value"))
    if state not in _APPROVABLE_STATES:
        raise ValueError(f"design note state is {state}")

    approved_on = (today or date.today()).isoformat()
    # Replace the later line first so the earlier span stays valid.
    replacements = (
        (
            state_line.start(),
            state_line.end(),
            f"{state_line.group('prefix')} approved",
        ),
        (
            approved_line.start(),
            approved_line.end(),
            f"{approved_line.group('prefix')} {approved_on}",
        ),
    )
    for start, end, new in sorted(replacements, reverse=True):
        text = f"{text[:start]}{new}{text[end:]}"
    path.write_text(text, encoding="utf-8")
    return {
        "action": "approved",
        "stem": cleaned,
        "state": "approved",
        "approved_on": approved_on,
    }


def render_design_approve(root: Path, stem: str) -> str:
    """Stamp design approval and serialize the result as JSON."""
    return json.dumps(design_approve(root, stem), indent=2) + "\n"
