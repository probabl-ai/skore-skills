"""Render, show, and import the journal through the skore project."""

from __future__ import annotations

import re
from pathlib import Path

from skore_skills.project_api import open_project, project_ready

_GENERATED = "<!-- generated, do not edit -->\n"
_SECTION = re.compile(r"^## (?P<name>.+?)\s*$", re.MULTILINE)
_SOURCE = re.compile(
    r"^(?:audit:(?P<audit>[^:]+):checks\.(?P<code>\S+)|design:(?P<design>\S+)|user)$"
)


def _sections(text: str) -> dict[str, str]:
    matches = list(_SECTION.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group("name")] = text[start:stop]
    return result


def _rows(section: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in section.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if any("<!--" in cell for cell in cells):
            continue
        if all(not cell or set(cell) <= {"-", ":"} for cell in cells):
            continue
        if cells and cells[0].lower() in {"question", "stem", "#"}:
            continue
        rows.append(cells)
    return rows


def show_journal(root: Path) -> str:
    """Return the journal rendered from the project."""
    return open_project(root).summarize().to_markdown()


def render_journal(root: Path) -> list[Path]:
    """Write a generated journal. The files are not authored by hand."""
    project = open_project(root)
    journal = root / "journal"
    journal.mkdir(parents=True, exist_ok=True)
    written = [journal / "JOURNAL.md"]
    written[0].write_text(_GENERATED + show_journal(root), encoding="utf-8")
    frame = project.experiments.frame
    selected = frame[frame["status"].isin(["backlog", "history"])]
    for _, row in selected.iterrows():
        path = journal / f"{row['stem']}.md"
        path.write_text(
            _GENERATED
            + f"# {row['stem']}\n\n{row['question']}\n\n{row['plan'] or ''}\n",
            encoding="utf-8",
        )
        written.append(path)
    return written


def render_if_project_has_content(root: Path) -> None:
    """Refresh generated journal files when the project already has content."""
    if not project_ready(root):
        return
    project = open_project(root)
    if not project.objective and project.experiments.frame.empty:
        return
    render_journal(root)


def _source_parts(source: str) -> tuple[str | None, str | None]:
    match = _SOURCE.fullmatch(source.strip())
    if match is None or match.group(0) == "user":
        return None, None
    if match.group("code"):
        return match.group("audit"), match.group("code")
    return match.group("design"), None


def import_journal(root: Path) -> int:
    """Import JOURNAL.md and idea files once. Existing stems are left in place."""
    from skore.agent import create_experiment

    project = open_project(root)
    index = root / "journal" / "JOURNAL.md"
    if not index.is_file():
        raise ValueError("journal/JOURNAL.md is missing")
    sections = _sections(index.read_text(encoding="utf-8"))
    existing = set(project.experiments.frame["stem"].astype(str))
    created = 0

    def add(stem: str, question: str, *, status_plan: str | None, source: str) -> None:
        nonlocal created, existing
        if stem in existing or not question:
            return
        source_stem, check_code = _source_parts(source)
        source_id = None
        if source_stem:
            frame = project.experiments.frame
            parent = frame.loc[frame["stem"].astype(str) == source_stem]
            if not parent.empty:
                source_id = str(parent.iloc[0]["id"])
        plan = status_plan
        note = root / "journal" / f"{stem}.md"
        if plan is None and note.is_file():
            plan = note.read_text(encoding="utf-8")
        create_experiment(
            project,
            stem=stem,
            question=question,
            plan=plan,
            source_id=source_id,
            check_code=check_code,
        )
        existing.add(stem)
        created += 1

    for cells in _rows(sections.get("History", "")):
        if len(cells) < 2:
            continue
        status = cells[2].lower() if len(cells) > 2 else ""
        plan = cells[5] if len(cells) > 5 else None
        if status in {"done", "running"} and not (plan and plan.strip()):
            plan = "Imported."
        add(cells[0], cells[1], status_plan=plan, source="user")
        experiment = project.experiments.frame
        matched = experiment.loc[experiment["stem"].astype(str) == cells[0]]
        if matched.empty:
            continue
        status = cells[2].lower() if len(cells) > 2 else ""
        if status in {"done", "running"}:
            row = matched.iloc[0].to_dict()
            if row["status"] == "backlog":
                project._write_experiment({**row, "status": "history"})

    for cells in _rows(sections.get("Backlog", "")):
        if len(cells) < 3 or not cells[0].startswith("B"):
            continue
        add(
            f"backlog_{cells[0].lower()}",
            cells[1],
            status_plan="Imported.",
            source=cells[2],
        )

    ideas = root / "journal" / "ideas"
    idea_rows = _rows(sections.get("Ideas", ""))
    for cells in idea_rows:
        if len(cells) < 4:
            continue
        question, status, stem, source = cells[0], cells[1].lower(), cells[2], cells[3]
        add(stem, question, status_plan=None, source=source)
        if status in {"aside", "discarded"}:
            frame = project.experiments.frame
            matched = frame.loc[frame["stem"].astype(str) == stem]
            if not matched.empty and matched.iloc[0]["status"] == "idea":
                project.experiments.get(str(matched.iloc[0]["id"])).decide(status)
    if ideas.is_dir():
        for path in sorted(ideas.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            heading = next(
                (
                    line.lstrip("#").strip()
                    for line in text.splitlines()
                    if line.startswith("#")
                ),
                path.stem,
            )
            add(path.stem, heading, status_plan=None, source="user")
    return created
