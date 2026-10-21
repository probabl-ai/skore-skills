"""Coverage for the experiment loop without a released ``skore.agent``."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pandas as pd
import pytest
from click.testing import CliRunner

from skore_skills.cli import cli
from skore_skills.design_consent import design_consent
from skore_skills.evaluate_consent import evaluate_consent
from skore_skills.frame import frame_clear, frame_show
from skore_skills.journal_api import (
    import_journal,
    render_if_project_has_content,
    render_journal,
    show_journal,
)
from skore_skills.loop import loop_artifacts, loop_locator
from skore_skills.model_choices import model_choices
from skore_skills.project_api import experiment_by_stem, open_project, project_ready
from skore_skills.review_consent import review_consent
from skore_skills.workspace import snapshot

COLUMNS = [
    "id",
    "stem",
    "status",
    "question",
    "source_id",
    "check_code",
    "plan",
]


class _Handle:
    def __init__(self, project: Project, row: dict[str, object]) -> None:
        self._project = project
        self._row = row
        self.id = row["id"]
        self.stem = row["stem"]
        self.status = row["status"]
        self.question = row["question"]
        self.plan = row.get("plan")
        self.source_id = row.get("source_id")

    def decide(self, status: str) -> None:
        self._row["status"] = status
        self.status = status

    def promote(self, plan: str) -> None:
        self._row["status"] = "backlog"
        self._row["plan"] = plan
        self.status = "backlog"
        self.plan = plan


class Project:
    """Stand-in for the rows the skills read and write."""

    def __init__(self) -> None:
        self.objective = ""
        self.rows: list[dict[str, object]] = []
        self.reports: dict[str, object] = {}
        self.experiments = self

    @property
    def frame(self) -> pd.DataFrame:
        if not self.rows:
            return pd.DataFrame(columns=COLUMNS)
        return pd.DataFrame(self.rows)

    def get(self, experiment_id: str) -> _Handle:
        matched = [row for row in self.rows if row["id"] == experiment_id]
        if not matched:
            raise KeyError(experiment_id)
        return _Handle(self, matched[0])

    def _write_experiment(self, row: dict[str, object]) -> None:
        for stored in self.rows:
            if stored["id"] == row["id"]:
                stored.update(row)
                return
        self.rows.append(row)

    def summarize(self) -> Project:
        return self

    def to_markdown(self) -> str:
        questions = " ".join(str(row["question"]) for row in self.rows)
        return f"# Objective\n\n{self.objective}\n{questions}\n"


def _install_agent(monkeypatch: pytest.MonkeyPatch, project: Project) -> None:
    def create_experiment(
        target: Project,
        *,
        stem: str,
        question: str,
        plan: str | None = None,
        source_id: str | None = None,
        check_code: str | None = None,
    ) -> _Handle:
        row = {
            "id": f"id-{stem}",
            "stem": stem,
            "status": "backlog" if plan else "idea",
            "question": question,
            "source_id": source_id,
            "check_code": check_code,
            "plan": plan,
        }
        target.rows.append(row)
        return _Handle(target, row)

    module = types.ModuleType("skore.agent")
    module.create_experiment = create_experiment
    monkeypatch.setitem(sys.modules, "skore.agent", module)
    monkeypatch.setattr("skore_skills.journal_api.open_project", lambda root: project)
    monkeypatch.setattr("skore_skills.project_api.open_project", lambda root: project)


def _journal(root: Path) -> None:
    journal = root / "journal"
    journal.mkdir(exist_ok=True)
    (journal / "JOURNAL.md").write_text(
        "\n".join(
            [
                "# Journal",
                "## History",
                "| Stem | Intent | Status | Headline result | Report | Design note |",
                "| --- | --- | --- | --- | --- | --- |",
                "| 01_dummy | What MAE? | done | rmse=1.2 | old | Plan. |",
                "| short |",
                "| 12_imported | No plan. | done |",
                "|  |  | done |",
                "## Backlog",
                "| # | Item | Source |",
                "| --- | --- | --- |",
                "| B1 | Fit a linear model. | user |",
                "| X1 | skip me | user |",
                "## Ideas",
                "| Question | Status | Experiment | Source |",
                "| --- | --- | --- | --- |",
                "| Drop outliers? | open | 03_outliers | user |",
                "| Try a log target? | aside | 04_log | design:01_dummy |",
                "| Ignore it. | discarded | 05_unused | audit:01_dummy:checks.SKD004 |",
                "|  | open | 06_blank | user |",
                "| Mystery? | open | 08_mystery | mystery |",
                "| Orphan? | open | 09_orphan | design:missing-parent |",
                "| only | two |",
                "| <!-- skip --> | a | b | c |",
            ]
        ),
        encoding="utf-8",
    )
    ideas = journal / "ideas"
    ideas.mkdir()
    (ideas / "07_file.md").write_text("# From a file\n", encoding="utf-8")
    (ideas / "10_plain.md").write_text("plain body\n", encoding="utf-8")
    (journal / "03_outliers.md").write_text("note body\n", encoding="utf-8")


def test_import_renders_and_skips_a_second_pass(tmp_path: Path, monkeypatch) -> None:
    project = Project()
    _install_agent(monkeypatch, project)
    with pytest.raises(ValueError, match="JOURNAL.md is missing"):
        import_journal(tmp_path)
    _journal(tmp_path)
    assert import_journal(tmp_path) == 10
    assert import_journal(tmp_path) == 0
    history = project.frame.loc[project.frame["stem"].eq("01_dummy")].iloc[0]
    assert history["status"] == "history"
    imported = project.frame.loc[project.frame["stem"].eq("12_imported")].iloc[0]
    assert imported["status"] == "history"
    assert imported["plan"] == "Imported."
    aside = project.frame.loc[project.frame["stem"].eq("04_log")].iloc[0]
    assert aside["status"] == "aside"
    assert aside["source_id"] == "id-01_dummy"
    orphan = project.frame.loc[project.frame["stem"].eq("09_orphan")].iloc[0]
    assert pd.isna(orphan["source_id"])
    plain = project.frame.loc[project.frame["stem"].eq("10_plain")].iloc[0]
    assert plain["question"] == "10_plain"
    next(row for row in project.rows if row["stem"] == "01_dummy")["plan"] = None
    written = render_journal(tmp_path)
    assert "None" not in (tmp_path / "journal" / "01_dummy.md").read_text()
    assert any(path.name == "JOURNAL.md" for path in written)
    assert "What MAE?" in show_journal(tmp_path)
    render_if_project_has_content(tmp_path)
    project.objective = ""
    project.rows.clear()
    render_if_project_has_content(tmp_path)


def test_render_skips_a_project_that_is_not_ready(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("skore_skills.journal_api.project_ready", lambda root: False)
    render_if_project_has_content(tmp_path)


def test_cli_experiment_commands(tmp_path: Path, monkeypatch) -> None:
    project = Project()
    _install_agent(monkeypatch, project)
    monkeypatch.chdir(tmp_path)
    created = CliRunner().invoke(
        cli,
        [
            "experiment",
            "create",
            "--stem",
            "01_dummy",
            "--question",
            "What MAE?",
            "--plan",
            "A plan.",
            "--source-id",
            "parent",
            "--check-code",
            "SKD004",
        ],
    )
    assert created.exit_code == 0, created.output
    experiment_id = created.output.strip()
    decided = CliRunner().invoke(cli, ["experiment", "decide", experiment_id, "aside"])
    assert decided.exit_code == 0
    promoted = CliRunner().invoke(
        cli, ["experiment", "promote", experiment_id, "--plan", "Revised."]
    )
    assert promoted.exit_code == 0
    listed = CliRunner().invoke(cli, ["experiment", "list", "--status", "backlog"])
    assert "What MAE?" in listed.output
    assert CliRunner().invoke(cli, ["experiment", "list"]).exit_code == 0
    assert (
        CliRunner().invoke(cli, ["objective", "set", "Predict."]).output.strip()
        == "Predict."
    )
    assert CliRunner().invoke(cli, ["objective", "show"]).output.strip() == "Predict."
    assert "Predict." in CliRunner().invoke(cli, ["journal", "show"]).output
    missing = CliRunner().invoke(cli, ["journal", "import"])
    assert missing.exit_code != 0
    assert CliRunner().invoke(cli, ["journal", "render"]).exit_code == 0
    _journal(tmp_path)
    imported = CliRunner().invoke(cli, ["journal", "import"])
    assert imported.exit_code == 0, imported.output


def test_consents_follow_the_experiment_status(tmp_path: Path, monkeypatch) -> None:
    project = Project()

    def by_stem(root: Path, stem: str):
        if stem == "missing":
            return None
        row = {
            "history": ("history", "id-h", True),
            "backlog": ("backlog", "id-b", False),
            "idea": ("idea", "id-i", False),
            "discarded": ("discarded", "id-d", False),
            "broken": ("history", "id-x", "raise"),
            "bare": ("idea", "id-bare", False),
        }[stem]
        handle = _Handle(
            project,
            {
                "id": row[1],
                "stem": stem,
                "status": row[0],
                "question": "Q?",
                "plan": None if stem == "bare" else "Plan.",
                "source_id": None if stem == "bare" else "src",
            },
        )
        if row[2] == "raise":

            def fail(experiment_id: str):
                raise RuntimeError("missing report")

            handle._project.get = fail
        elif row[2]:
            project.reports[row[1]] = object()
            handle._project.get = lambda experiment_id: project.reports.get(
                experiment_id
            )
        else:
            handle._project.get = lambda experiment_id: None
        return handle

    monkeypatch.setattr("skore_skills.project_api.experiment_by_stem", by_stem)

    assert design_consent(tmp_path, "backlog")["reason"] == "approved"
    assert design_consent(tmp_path, "history")["reason"] == "done"
    assert design_consent(tmp_path, "discarded")["reason"] == "abandoned"
    assert design_consent(tmp_path, "idea")["reason"] == "first_approval"
    bare = design_consent(tmp_path, "bare")
    assert bare["context"]["source"] == ""
    assert bare["context"]["change"] == ""
    assert evaluate_consent(tmp_path, "history")["reason"] == "persisted_report"
    assert evaluate_consent(tmp_path, "idea")["reason"] == "status_idea"
    assert evaluate_consent(tmp_path, "backlog")["reason"] == "first_eval"
    assert review_consent(tmp_path, "idea")["reason"] == "report_missing"
    assert review_consent(tmp_path, "broken")["reason"] == "report_missing"
    assert review_consent(tmp_path, "history")["reason"] == "stored_report"
    assert loop_artifacts(tmp_path, "history")["reason"] == "report_stored"
    assert loop_artifacts(tmp_path, "backlog")["reason"] == "ready_to_run"
    assert loop_artifacts(tmp_path, "idea")["reason"] == "status_idea"
    assert loop_artifacts(tmp_path, "broken")["files"]["report"] is False
    assert loop_locator(tmp_path, "history")["locator"] == "id-h"
    assert loop_locator(tmp_path, "idea")["reason"] == "missing"


def test_open_project_and_lookup_by_stem(tmp_path: Path, monkeypatch) -> None:
    created: dict[str, object] = {}

    class FakeProject:
        def __init__(self, name: str, mode: str, workspace: Path) -> None:
            created.update(name=name, mode=mode, workspace=workspace)
            self.experiments = self
            self.rows = [
                {"id": "id-1", "stem": "01_dummy", "status": "idea"},
            ]

        @property
        def frame(self) -> pd.DataFrame:
            return pd.DataFrame(self.rows)

        def get(self, experiment_id: str) -> str:
            return experiment_id

    import skore

    monkeypatch.setattr(skore, "Project", FakeProject)
    assert open_project(tmp_path) is not None
    assert created["mode"] == "local"
    assert project_ready(tmp_path) is False
    assert experiment_by_stem(tmp_path, "01_dummy") is None
    marker = tmp_path / ".skore"
    marker.mkdir()
    (marker / ".SKORE_WORKSPACE").write_text("", encoding="utf-8")
    assert experiment_by_stem(tmp_path, "01_dummy") == "id-1"
    assert experiment_by_stem(tmp_path, "missing") is None
    empty = FakeProject("ml", "local", marker)
    empty.rows = []
    monkeypatch.setattr(skore, "Project", lambda *args, **kwargs: empty)
    assert experiment_by_stem(tmp_path, "01_dummy") is None


def test_frame_and_model_choices_read_the_objective(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lines = [
        "# JOURNAL",
        "",
        "## Modeling decisions",
        "",
        "| Variable | Value |",
        "|---|---|",
        "| Status | locked |",
        "| Revised on | n/a |",
        "| Prediction goal | point_predictions |",
        "| Deployment | iid |",
        "| Horizon | n/a |",
        "| Gap | n/a |",
        "| Generalize to | n/a |",
        "| Known at predict | n/a |",
        "| Time role | n/a |",
        "| Metric role | point_error |",
        "| Metric | MAE |",
        "| Baseline | dummy |",
        "| Baseline note | global mean |",
        "| Folds | 5 |",
        "",
    ]
    project = Project()
    project.objective = "\n".join(lines)
    project.rows = [
        {
            "id": "h",
            "stem": "01_dummy",
            "status": "history",
            "question": "Done?",
            "source_id": None,
            "check_code": None,
            "plan": "Plan.",
        },
        {
            "id": "b",
            "stem": "02_next",
            "status": "backlog",
            "question": "Next?",
            "source_id": None,
            "check_code": None,
            "plan": "Plan.",
        },
    ]
    monkeypatch.setattr("skore_skills.project_api.project_ready", lambda root: True)
    monkeypatch.setattr("skore_skills.project_api.open_project", lambda root: project)

    choices = model_choices(tmp_path)
    assert any(choice["id"] == "backlog" for choice in choices["choices"])
    shown = frame_show(tmp_path)
    assert shown.get("reason") != "missing_scaffold"
    cleared = frame_clear(
        tmp_path, "metric", today=__import__("datetime").date(2026, 9, 27)
    )
    assert cleared["cell"] == "metric"
    assert "draft" in project.objective

    class Readable:
        objective = project.objective

    calls = {"n": 0}

    def flaky(root: Path) -> Readable:
        calls["n"] += 1
        if calls["n"] <= 2:
            return Readable()
        raise RuntimeError("unavailable")

    monkeypatch.setattr("skore_skills.project_api.open_project", flaky)
    with pytest.raises(RuntimeError):
        frame_clear(tmp_path, "baseline")

    class Down:
        @property
        def objective(self) -> str:
            raise RuntimeError("unavailable")

    monkeypatch.setattr("skore_skills.project_api.open_project", lambda root: Down())
    assert frame_show(tmp_path)["reason"] == "missing_scaffold"
    journal = tmp_path / "journal"
    journal.mkdir()
    (journal / "JOURNAL.md").write_text("\n".join(lines), encoding="utf-8")
    frame_clear(tmp_path, "baseline")


def test_temporary_workspace_is_already_set_up(tmp_path: Path) -> None:
    (tmp_path / ".skore-temporary").write_text("", encoding="utf-8")
    payload = snapshot(tmp_path)
    assert payload["workspace"] == "temporary"
    assert payload["setup"]["workspace"] == "done"
    assert "workspace" not in payload["setup"]["pending"]
