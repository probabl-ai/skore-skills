"""Decide whether first-eval HITL is required before ``skore.evaluate``."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from skore_skills.gate_context import design_context

_HISTORY_SECTION = re.compile(r"^## History\s*$", re.MULTILINE)
_PERSISTED_REPORT = re.compile(
    r"^\s*-\s*\*\*Persisted report:\*\*\s*(.+?)\s*$",
    re.MULTILINE,
)
_ASK_CHOICES = ["evaluate", "modify", "stop"]


def _history_section(text: str) -> str:
    match = _HISTORY_SECTION.search(text)
    if match is None:
        return ""
    start = match.end()
    next_heading = re.search(r"^## ", text[start:], re.MULTILINE)
    stop = start + next_heading.start() if next_heading else len(text)
    return text[start:stop]


def _cells(line: str) -> list[str]:
    return [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]


def _is_separator(cells: list[str]) -> bool:
    return all(not cell or set(cell) <= {"-", ":"} for cell in cells)


def _is_real_locator(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    lowered = text.lower()
    if lowered == "n/a" or lowered.startswith("n/a"):
        return False
    return not (text.startswith("<") and text.endswith(">"))


def _history_report(root: Path, stem: str) -> str:
    path = root / "journal" / "JOURNAL.md"
    if not path.is_file():
        return ""
    report_index: int | None = None
    for line in _history_section(path.read_text(encoding="utf-8")).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = _cells(line)
        if any("<!--" in cell for cell in cells) or _is_separator(cells):
            continue
        if cells and cells[0].lower() == "stem":
            lowered = [cell.lower() for cell in cells]
            report_index = lowered.index("report") if "report" in lowered else None
            continue
        if cells[0] != stem:
            continue
        if report_index is not None and report_index < len(cells):
            return cells[report_index]
        return ""
    return ""


def _design_note_report(root: Path, stem: str) -> str:
    path = root / "journal" / f"{stem}.md"
    if not path.is_file():
        return ""
    match = _PERSISTED_REPORT.search(path.read_text(encoding="utf-8"))
    return match.group(1).strip() if match else ""


def evaluate_consent(root: Path, stem: str) -> dict[str, Any]:
    """Return the first-eval vs re-eval gate for ``stem``.

    Filesystem only: smoke pairing plus History / design-note locators.
    Does not run pytest or ``project.summarize()``.
    """
    cleaned = stem.strip()
    if not cleaned:
        raise ValueError("stem is required")

    from skore_skills.project_api import experiment_by_stem

    experiment = experiment_by_stem(root, cleaned)
    if experiment is not None:
        if experiment.status == "history":
            return {"stem": cleaned, "action": "proceed", "reason": "persisted_report"}
        if experiment.status != "backlog":
            return {
                "stem": cleaned,
                "action": "stop",
                "reason": f"status_{experiment.status}",
            }
        return {
            "stem": cleaned,
            "action": "ask",
            "reason": "first_eval",
            "choices": list(_ASK_CHOICES),
            "context": {
                "note": experiment.id,
                "question": experiment.question,
                "experiment": experiment.stem,
                "smoke": "",
                "persisted_report": "none",
            },
        }

    smoke = root / "tests" / "smoke" / f"test_{cleaned}.py"
    if not smoke.is_file():
        return {"stem": cleaned, "action": "stop", "reason": "smoke_missing"}

    if _is_real_locator(_history_report(root, cleaned)) or _is_real_locator(
        _design_note_report(root, cleaned)
    ):
        return {"stem": cleaned, "action": "proceed", "reason": "persisted_report"}

    note = design_context(root, cleaned)
    return {
        "stem": cleaned,
        "action": "ask",
        "reason": "first_eval",
        "choices": list(_ASK_CHOICES),
        "context": {
            "note": note["note"],
            "question": note["question"],
            "experiment": f"experiments/{cleaned}.py",
            "smoke": f"tests/smoke/test_{cleaned}.py",
            "persisted_report": "none",
        },
    }


def render_evaluate_consent(root: Path, stem: str) -> str:
    """Serialize the evaluate-consent gate as JSON."""
    return json.dumps(evaluate_consent(root, stem), indent=2) + "\n"
