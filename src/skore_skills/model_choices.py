"""Compute the deterministic entry menu for the model workflow."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from skore_skills.frame import _raw_rows, modeling_decisions_state
from skore_skills.workspace import snapshot

_SECTION = re.compile(r"^## (?P<name>History|Backlog)\s*$", re.MULTILINE)
_BACKLOG_ID = re.compile(r"^B\d+$")
_MODEL_STATUSES = frozenset({"running", "done", "abandoned"})


def _sections(text: str) -> dict[str, str]:
    matches = list(_SECTION.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group("name")] = text[start:stop]
    return result


def _table_rows(section: str, columns: int) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) != columns:
            continue
        if any("<!--" in cell for cell in cells):
            continue
        if all(not cell or set(cell) <= {"-", ":"} for cell in cells):
            continue
        rows.append(cells)
    return rows


def _journal_facts(root: Path) -> tuple[set[str], list[dict[str, str]], bool]:
    from skore_skills.project_api import open_project, project_ready

    if project_ready(root):
        frame = open_project(root).experiments.frame
        history_stems = set(
            frame.loc[frame["status"].eq("history"), "stem"].astype(str)
        )
        backlog = [
            {
                "id": f"B{number}",
                "item": str(row["question"]),
                "source": str(row["stem"]),
            }
            for number, (_, row) in enumerate(
                frame.loc[frame["status"].eq("backlog")].iterrows(), start=1
            )
        ]
        return history_stems, backlog, False

    sections = _sections((root / "journal" / "JOURNAL.md").read_text(encoding="utf-8"))

    history_stems = {
        row[0]
        for row in _table_rows(sections.get("History", ""), 6)
        if row[2].lower() in _MODEL_STATUSES
    }
    backlog = [
        {"id": row[0], "item": row[1], "source": row[2]}
        for row in _table_rows(sections.get("Backlog", ""), 3)
        if _BACKLOG_ID.fullmatch(row[0]) and row[1] and row[2]
    ]
    return history_stems, backlog, True


def model_choices(root: Path) -> dict[str, Any]:
    """Return model-entry choices justified by workspace evidence."""
    status = snapshot(root)
    if modeling_decisions_state(root) != "locked":
        return {
            "action": "stop",
            "reason": "modeling_decisions_unlocked",
            "modeling_decisions": status["modeling_decisions"],
        }

    history_stems, backlog, include_scripts = _journal_facts(root)
    experiment_stems: set[str] = set()
    if include_scripts:
        experiments = root / "experiments"
        if experiments.is_dir():
            experiment_stems = {
                path.stem
                for path in experiments.glob("*.py")
                if path.is_file() and path.stem != "__init__"
            }
    model_stems = sorted(history_stems | experiment_stems)

    rows = _raw_rows(root)
    choices: list[dict[str, str]] = []
    if not model_stems:
        choices.append(
            {
                "id": "baseline",
                "reason": (
                    f"locked baseline is {rows['baseline']}: {rows['baseline_note']}"
                ),
            }
        )
    if status["data_analysis"] == "present":
        choices.append(
            {
                "id": "eda_proposal",
                "reason": "recorded EDA is available",
            }
        )
    if backlog:
        choices.append(
            {
                "id": "backlog",
                "reason": f"{len(backlog)} backlog item(s) available",
            }
        )
    choices.append(
        {
            "id": "discuss",
            "reason": "discussion is always available",
        }
    )
    return {
        "model_stems": model_stems,
        "data_analysis": status["data_analysis"],
        "backlog": backlog,
        "choices": choices,
    }


def render_model_choices(root: Path) -> str:
    """Serialize the model-entry choice snapshot as JSON."""
    return json.dumps(model_choices(root), indent=2) + "\n"
