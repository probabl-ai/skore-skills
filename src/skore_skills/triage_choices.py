"""Compute the deterministic entry board for the triage workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from skore_skills.workspace import snapshot

# Board order and human labels match the triage SKILL.md. Evaluate,
# audit, shaping, literature, and internals stay off the board.
ENTRY_BOARD = (
    ("setup-ml-project", "Set up the project"),
    ("explore-ml-data", "Explore the data"),
    ("model-ml-pipeline", "Build a model"),
    ("review-ml-experiment", "Review the last experiment"),
    ("manage-ml-backlog", "Record / decide what next"),
    ("export-ml-project", "Export"),
    ("sync-ml-reports", "Sync reports"),
    ("review-ml-choices", "Review choices"),
)


def _recommended(
    status: dict[str, Any], skills: dict[str, bool | None]
) -> tuple[str | None, str | None]:
    if status["data_analysis"] == "missing" and skills.get("explore-ml-data") is True:
        return "explore-ml-data", "no recorded data analysis yet"
    if (
        status["data_analysis"] in {"present", "skipped"}
        and status["loop_stage"] == "backlog"
        and skills.get("manage-ml-backlog") is True
    ):
        return "manage-ml-backlog", "the loop stage is backlog"
    return None, None


def triage_choices(root: Path) -> dict[str, Any]:
    """Return the entry board for ``root``, installed skills only.

    Read-only. Does not write ``.skore`` or the journal.
    """
    status = snapshot(root)
    skills = status["skills"]
    choices = [
        {"skill": skill_id, "label": label}
        for skill_id, label in ENTRY_BOARD
        if skills.get(skill_id) is True
    ]
    unknown = "install status unknown" if not skills else "not installed"
    not_offered = [
        {"skill": skill_id, "label": label, "reason": f"{skill_id} {unknown}"}
        for skill_id, label in ENTRY_BOARD
        if skills.get(skill_id) is not True
    ]
    recommended, reason = _recommended(status, skills)
    return {
        "choices": choices,
        "recommended": recommended,
        "recommendation_reason": reason,
        "not_offered": not_offered,
        "data_analysis": status["data_analysis"],
        "loop_stage": status["loop_stage"],
    }


def render_triage_choices(root: Path) -> str:
    """Serialize the entry board as JSON."""
    return json.dumps(triage_choices(root), indent=2) + "\n"
