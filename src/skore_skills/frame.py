"""Read the modeling-decisions block and the next gate."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

_SECTION = re.compile(
    r"^## Modeling decisions\s*\n(.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)
_QUANTITY = re.compile(r"^(?P<value>\d+(?:\.\d+)?)\s+(?P<unit>[A-Za-z]+)$")
_FOLDS = re.compile(r"^[1-9]\d*$")
_PREDEFINED = "predefined"

_LABELS = (
    ("Status", "status"),
    ("Revised on", "revised_on"),
    ("Prediction goal", "prediction_goal"),
    ("Deployment", "deployment"),
    ("Horizon", "horizon"),
    ("Gap", "gap"),
    ("Generalize to", "generalize_to"),
    ("Known at predict", "known_at_predict"),
    ("Time role", "time_role"),
    ("Metric role", "metric_role"),
    ("Metric", "metric"),
    ("Baseline", "baseline"),
    ("Baseline note", "baseline_note"),
    ("Folds", "folds"),
)
_BY_LABEL = dict(_LABELS)

_REFERENCES = {
    "prediction_goal": "references/prediction-goal.md",
    "deployment": "references/deployment.md",
    "horizon": "references/horizon-gap.md",
    "gap": "references/horizon-gap.md",
    "time_role": "references/deployment.md",
    "generalize_to": "references/generalize-to.md",
    "known_at_predict": "references/generalize-to.md",
    "metric_role": "references/metric-role.md",
    "metric": "references/metric-role.md",
    "baseline": "references/baseline.md",
    "baseline_note": "references/baseline.md",
    "folds": "references/validation.md",
}
_BASELINES = (
    "seasonal_naive",
    "group_mean",
    "logistic",
    "production",
    "dummy",
)

_GOALS = (
    "probabilities",
    "point_labels",
    "intervals",
    "point_predictions",
)
_FALLBACK = "references/fallback.md"
_SUPPORTED_TASKS = frozenset(
    {"", "classification", "regression", "multioutput-regression"}
)
_REVISE = ["modify", "keep", "stop"]


def _cells(line: str) -> list[str]:
    return [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]


def _empty(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    return text.startswith("<") and text.endswith(">")


def _objective_text(root: Path) -> str:
    from skore_skills.project_api import open_project, project_ready

    if not project_ready(root):
        return ""
    try:
        return open_project(root).objective or ""
    except Exception:
        return ""


def _section_text(root: Path) -> str:
    objective = _objective_text(root)
    if "## Modeling decisions" in objective:
        match = _SECTION.search(objective)
        return match.group(1) if match else ""
    path = root / "journal" / "JOURNAL.md"
    if not path.is_file():
        return ""
    match = _SECTION.search(path.read_text(encoding="utf-8"))
    return match.group(1) if match else ""


def _raw_rows(root: Path) -> dict[str, str]:
    rows = {key: "" for _, key in _LABELS}
    for line in _section_text(root).splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = _cells(line)
        if len(cells) != 2 or cells[0] in {"Variable", "---"}:
            continue
        if set(cells[1]) <= {"-", ":"} and set(cells[0]) <= {"-", ":"}:
            continue
        key = _BY_LABEL.get(cells[0])
        if key is None or _empty(cells[1]):
            continue
        rows[key] = cells[1].strip()
    return rows


def modeling_decisions_state(root: Path) -> str:
    """Return ``missing``, ``draft``, or ``locked`` for the journal block."""
    status = _raw_rows(root)["status"].split()
    token = status[0].lower().rstrip(".,;:") if status else ""
    if token in {"draft", "locked"}:
        return token
    return "missing"


def _recorded_targets(root: Path) -> tuple[str, list[str]]:
    """Return the joint task and the confirmed target columns.

    ``extras.json`` stores ``targets``, a list of ``{column, task}``.
    One entry keeps that entry's task. Several regression entries are
    ``multioutput-regression``. Any other combination is returned as
    its own task name so framing can refuse it.
    """
    path = root / "scratch" / "data_analysis" / "extras.json"
    if not path.is_file():
        return "", []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "", []
    entries = payload.get("targets") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return "", []
    columns: list[str] = []
    tasks: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        column = entry.get("column")
        task = entry.get("task")
        if not isinstance(column, str) or not isinstance(task, str):
            continue
        column = column.strip()
        task = task.strip()
        if column and task:
            columns.append(column)
            tasks.append(task)
    if not columns:
        return "", []
    if len(columns) == 1:
        return tasks[0], columns
    if all(task == "regression" for task in tasks):
        return "multioutput-regression", columns
    if all(task == "classification" for task in tasks):
        return "multioutput-classification", columns
    return "mixed", columns


def _goal_candidates(root: Path) -> list[str]:
    task, _targets = _recorded_targets(root)
    if task == "classification":
        goals = ["probabilities", "point_labels"]
    elif task in {"regression", "multioutput-regression"}:
        goals = ["intervals", "point_predictions"]
    else:
        goals = list(_GOALS)
    goals.append("uncovered")
    return goals


def _metric_candidates(goal: str) -> list[str]:
    if goal == "probabilities":
        return ["proper_score", "ranking", "imposed"]
    if goal == "point_labels":
        return ["thresholded", "ranking", "imposed"]
    if goal == "intervals":
        return ["proper_score", "imposed"]
    if goal == "point_predictions":
        return ["point_error", "imposed"]
    return ["imposed", "proper_score", "ranking", "thresholded", "point_error"]


def _baseline_tokens(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _note_parts(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def _baseline_candidates(rows: dict[str, str]) -> list[str]:
    if not rows["deployment"]:
        return list(_BASELINES)
    candidates: list[str] = []
    if rows["deployment"] == "time":
        candidates.append("seasonal_naive")
    known = rows["known_at_predict"]
    if known and known != "n/a":
        candidates.append("group_mean")
    if rows["prediction_goal"] == "probabilities":
        candidates.append("logistic")
    candidates.extend(["production", "dummy"])
    return candidates


def _candidates(root: Path, key: str, rows: dict[str, str]) -> list[str] | None:
    if key == "prediction_goal":
        return _goal_candidates(root)
    if key == "deployment":
        return ["iid", "time", "groups"]
    if key == "time_role":
        return ["sort_key", "covariate"]
    if key == "metric_role":
        return _metric_candidates(rows["prediction_goal"])
    if key == "baseline":
        return _baseline_candidates(rows)
    return None


def _quantity(value: str) -> tuple[float, str] | None:
    match = _QUANTITY.fullmatch(value.strip())
    if match is None:
        return None
    return float(match.group("value")), match.group("unit").lower()


def _quantities(value: str) -> list[tuple[float, str]] | None:
    parts = [part.strip() for part in value.split(",")]
    if any(not part for part in parts):
        return None
    parsed: list[tuple[float, str]] = []
    for part in parts:
        item = _quantity(part)
        if item is None:
            return None
        parsed.append(item)
    if len({unit for _, unit in parsed}) != 1:
        return None
    return parsed


def _number(value: float) -> int | float:
    return int(value) if value.is_integer() else value


def _inapplicable(rows: dict[str, str], key: str) -> bool:
    if rows["prediction_goal"] == "uncovered":
        return key not in {"prediction_goal", "metric", "baseline_note"}
    deployment = rows["deployment"]
    if key in {"horizon", "gap", "time_role"}:
        return deployment in {"iid", "groups"}
    if key == "generalize_to":
        return deployment in {"iid", "time"}
    return False


def _valid(root: Path, key: str, rows: dict[str, str]) -> bool:
    value = rows[key]
    if _inapplicable(rows, key):
        return True
    if not value:
        return False
    if key == "horizon":
        return _quantities(value) is not None
    if key == "gap":
        return _quantity(value) is not None
    if key == "folds":
        return value == _PREDEFINED or _FOLDS.fullmatch(value) is not None
    if key == "generalize_to":
        return value != "n/a"
    if key == "baseline":
        tokens = _baseline_tokens(value)
        menu = _baseline_candidates(rows)
        return len(tokens) == 1 and tokens[0] in menu
    if key == "baseline_note":
        tokens = _baseline_tokens(rows["baseline"])
        notes = _note_parts(value)
        if tokens:
            return len(tokens) == 1 and len(notes) == 1
        return len(notes) == 1
    allowed = _candidates(root, key, rows)
    if allowed is None:
        return True
    return value in allowed


def _ask_keys(rows: dict[str, str]) -> list[str]:
    if rows["prediction_goal"] == "uncovered":
        return ["prediction_goal", "metric", "baseline_note"]
    deployment = rows["deployment"]
    keys = ["prediction_goal", "deployment"]
    if deployment in {"", "time"}:
        keys.extend(["horizon", "gap", "time_role"])
    if deployment in {"", "groups"}:
        keys.append("generalize_to")
    keys.extend(
        [
            "known_at_predict",
            "metric_role",
            "metric",
            "baseline",
            "baseline_note",
            "folds",
        ]
    )
    return keys


def _required(rows: dict[str, str]) -> list[str]:
    if rows["prediction_goal"] == "uncovered":
        return ["prediction_goal", "metric", "baseline_note"]
    keys = ["prediction_goal", "deployment"]
    deployment = rows["deployment"]
    if deployment == "time":
        keys.extend(["horizon", "gap", "time_role"])
    elif deployment == "groups":
        keys.append("generalize_to")
    keys.extend(
        [
            "known_at_predict",
            "metric_role",
            "metric",
            "baseline",
            "baseline_note",
            "folds",
        ]
    )
    return keys


def _effective(rows: dict[str, str]) -> dict[str, str]:
    values: dict[str, str] = {}
    for _, key in _LABELS:
        if key in {"status", "revised_on"}:
            continue
        if _inapplicable(rows, key) and not rows[key]:
            values[key] = "n/a"
        else:
            values[key] = rows[key]
    return values


def _note_names(note: str) -> set[str]:
    return {part for part in re.split(r"[\s,]+", note.strip()) if part}


def _conflict(rows: dict[str, str]) -> str:
    if rows["prediction_goal"] == "uncovered":
        return ""
    if rows["deployment"] == "time":
        horizons = _quantities(rows["horizon"])
        gap = _quantity(rows["gap"])
        if horizons and gap and horizons[0][1] != gap[1]:
            return "gap_unit_mismatch"
    generalize = rows["generalize_to"]
    tokens = _baseline_tokens(rows["baseline"])
    notes = _note_parts(rows["baseline_note"])
    if len(tokens) == len(notes) and generalize not in {"", "n/a"}:
        for token, note in zip(tokens, notes, strict=True):
            if token == "group_mean" and (
                note == generalize or generalize in _note_names(note)
            ):
                return "group_mean_on_generalize_to"
    return ""


def _translation(root: Path, rows: dict[str, str]) -> dict[str, Any] | None:
    if rows["prediction_goal"] == "uncovered":
        return None
    effective = _effective(rows)
    time = effective["deployment"] == "time"
    horizons = _quantities(effective["horizon"]) if time else None
    gap = _quantity(effective["gap"]) if time else None
    predefined = effective["folds"] == _PREDEFINED
    holdout = effective["folds"] == "1"
    splitter = "prefit" if predefined else None
    pattern = None
    scheme = None
    groups = None
    if not predefined and not holdout and time:
        pattern, scheme = "B", "date_time"
    elif not predefined and not holdout and effective["deployment"] == "groups":
        splitter, pattern = "GroupKFold", "B"
        groups = effective["generalize_to"]
    elif not predefined and not holdout:
        splitter, pattern = "KFold", "A"
    folds = effective["folds"]
    scored_once = holdout or predefined
    task, targets = _recorded_targets(root)
    return {
        "splitter": splitter,
        "pattern": pattern,
        "scheme": scheme,
        "n_splits": None if scored_once or not folds.isdigit() else int(folds),
        "horizons": None
        if horizons is None
        else [_number(value) for value, _ in horizons],
        "horizon_unit": None if horizons is None else horizons[0][1],
        "gap": None if gap is None else _number(gap[0]),
        "gap_unit": None if gap is None else gap[1],
        "groups": groups,
        "report": "EstimatorReport" if scored_once else None,
        "metric": effective["metric"],
        "task": task,
        "targets": targets,
    }


def _ask(
    reason: str,
    rows: dict[str, str],
    *,
    missing: list[str] | None = None,
    candidates: list[str] | None = None,
    reference: str | None = None,
    choices: list[str] | None = None,
    full: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"action": "ask", "reason": reason}
    if missing is not None:
        payload["missing"] = missing
    if candidates is not None:
        payload["candidates"] = candidates
    if reference is not None:
        payload["reference"] = reference
    if choices is not None:
        payload["choices"] = choices
    if full:
        context = _effective(rows)
    else:
        context = {
            key: value
            for key, value in rows.items()
            if value and key not in {"status", "revised_on"}
        }
    payload["context"] = context
    return payload


def frame_show(root: Path, *, revise: bool = False) -> dict[str, Any]:
    """Return the modeling-decisions gate for ``root``.

    Filesystem only: ``journal/JOURNAL.md`` and, when present,
    ``scratch/data_analysis/extras.json``. Does not write either file.
    """
    journal = root / "journal" / "JOURNAL.md"
    if not journal.is_file() and "## Modeling decisions" not in _objective_text(root):
        return {"action": "stop", "reason": "missing_scaffold"}

    rows = _raw_rows(root)
    recorded, targets = _recorded_targets(root)
    if recorded not in _SUPPORTED_TASKS and not rows["prediction_goal"]:
        payload = _ask("uncovered", rows, reference=_FALLBACK)
        payload["context"] = {"task": recorded, "targets": targets}
        return payload

    locked = rows["status"].split()[:1] == ["locked"]
    complete = all(_valid(root, key, rows) for key in _required(rows))
    if revise and locked and complete and not _conflict(rows):
        return _ask("revise", rows, choices=list(_REVISE), full=True)

    pending = [key for key in _ask_keys(rows) if not _valid(root, key, rows)]
    if pending:
        questions: list[dict[str, Any]] = []
        for key in pending:
            item: dict[str, Any] = {
                "key": key,
                "reference": (
                    _FALLBACK
                    if rows["prediction_goal"] == "uncovered"
                    else _REFERENCES[key]
                ),
            }
            candidates = _candidates(root, key, rows)
            if candidates is not None:
                item["candidates"] = candidates
            questions.append(item)
        payload = _ask("missing_keys", rows, missing=pending)
        payload["questions"] = questions
        if len(questions) == 1:
            payload["reference"] = questions[0]["reference"]
            if "candidates" in questions[0]:
                payload["candidates"] = questions[0]["candidates"]
        return payload

    conflict = _conflict(rows)
    if conflict == "gap_unit_mismatch":
        return _ask(
            conflict,
            rows,
            missing=["gap"],
            reference=_REFERENCES["gap"],
            full=True,
        )
    if conflict:
        return _ask(
            conflict,
            rows,
            missing=["baseline"],
            candidates=_baseline_candidates(rows),
            reference=_REFERENCES["baseline"],
            full=True,
        )

    if modeling_decisions_state(root) == "locked":
        return {
            "action": "proceed",
            "reason": "locked",
            "decisions": _effective(rows),
            "translation": _translation(root, rows),
        }
    return _ask("set", rows, full=True)


def render_frame_show(root: Path, *, revise: bool = False) -> str:
    """Serialize the modeling-decisions gate as JSON."""
    return json.dumps(frame_show(root, revise=revise), indent=2) + "\n"


def _blank_keys(cell: str, rows: dict[str, str]) -> list[str]:
    """Return ``cell`` and the dependents a reopen must clear."""
    extra: list[str] = []
    if cell == "prediction_goal":
        extra = ["metric_role", "metric"]
    elif cell == "deployment":
        extra = ["horizon", "gap", "time_role", "generalize_to"]
    elif cell == "known_at_predict" and "group_mean" in _baseline_tokens(
        rows["baseline"]
    ):
        extra = ["baseline", "baseline_note"]
    elif cell == "metric_role":
        extra = ["metric"]
    elif cell == "baseline":
        extra = ["baseline_note"]
    return [cell, *extra]


def _section_span(text: str) -> tuple[int, int, str]:
    match = _SECTION.search(text)
    if match is None:
        raise ValueError("modeling decisions section is missing")
    return match.start(1), match.end(1), match.group(1)


def _row_keys(section: str) -> set[str]:
    found: set[str] = set()
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = _cells(line)
        if len(cells) != 2:
            continue
        key = _BY_LABEL.get(cells[0])
        if key is not None:
            found.add(key)
    return found


def _apply_updates(section: str, updates: dict[str, str]) -> str:
    rewritten: list[str] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            rewritten.append(line)
            continue
        cells = _cells(line)
        if len(cells) != 2:
            rewritten.append(line)
            continue
        key = _BY_LABEL.get(cells[0])
        if key is None or key not in updates:
            rewritten.append(line)
            continue
        rewritten.append(f"| {cells[0]} | {updates[key]} |")
    return "\n".join(rewritten)


def frame_clear(root: Path, cell: str, *, today: date | None = None) -> dict[str, Any]:
    """Blank one framing cell and its dependents.

    Writes ``journal/JOURNAL.md``. Sets Status to ``draft`` and
    Revised on to ``today``. Does not write a new value for ``cell``.

    Raises
    ------
    ValueError
        When the journal or the cell cannot be cleared.
    """
    decision_keys = {key for _, key in _LABELS if key not in {"status", "revised_on"}}
    if cell not in decision_keys:
        raise ValueError(f"unknown framing cell: {cell}")
    path = root / "journal" / "JOURNAL.md"
    objective = _objective_text(root)
    if "## Modeling decisions" in objective:
        text = objective
    elif path.is_file():
        text = path.read_text(encoding="utf-8")
    else:
        raise ValueError("journal is missing")
    rows = _raw_rows(root)
    value = rows[cell].strip()
    if _empty(value) or value == "n/a":
        raise ValueError(f"{cell} is empty")
    blanked = _blank_keys(cell, rows)
    start, end, section = _section_span(text)
    present = _row_keys(section)
    required = ("status", "revised_on", *blanked)
    missing = [key for key in required if key not in present]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"modeling decisions table is missing {joined}")
    revised = (today or date.today()).isoformat()
    updates = dict.fromkeys(blanked, "")
    updates["status"] = "draft"
    updates["revised_on"] = revised
    cleared = text[:start] + _apply_updates(section, updates) + text[end:]
    if path.is_file() and "## Modeling decisions" not in objective:
        path.write_text(cleared, encoding="utf-8")
    from skore_skills.project_api import open_project

    try:
        open_project(root).objective = cleared
    except Exception:
        if not path.is_file():
            raise
    return {
        "action": "cleared",
        "cell": cell,
        "blanked": blanked,
        "status": "draft",
        "revised_on": revised,
    }


def render_frame_clear(root: Path, cell: str) -> str:
    """Blank one framing cell and serialize the result as JSON."""
    return json.dumps(frame_clear(root, cell), indent=2) + "\n"
