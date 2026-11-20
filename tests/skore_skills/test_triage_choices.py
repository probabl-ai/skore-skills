"""Tests for ``skore-skills triage choices``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from skore_skills.cli import cli
from skore_skills.installed_skills import SIDECAR
from skore_skills.triage_choices import triage_choices

_ENTRY = (
    "setup-ml-project",
    "explore-ml-data",
    "model-ml-pipeline",
    "review-ml-experiment",
    "manage-ml-backlog",
    "export-ml-project",
    "sync-ml-reports",
    "review-ml-choices",
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _install(root: Path, *names: str) -> None:
    target = root / ".agents" / "skills"
    _write(
        target / ".catalog.json",
        json.dumps({"skills": [{"id": name} for name in names]}) + "\n",
    )
    for name in names:
        _write(target / name / SIDECAR, json.dumps({"id": name}) + "\n")


def _isolate_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "isolated-home"
    home.mkdir()
    monkeypatch.setattr("skore_skills.installed_skills.Path.home", lambda: home)


def _skills(rows: object) -> list[str]:
    assert isinstance(rows, list)
    return [row["skill"] for row in rows]


def test_full_install_offers_every_entry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A full install offers each entry row with its human label."""
    _isolate_home(tmp_path, monkeypatch)
    _install(tmp_path, *_ENTRY)

    payload = triage_choices(tmp_path)

    assert _skills(payload["choices"]) == list(_ENTRY)
    assert payload["choices"][0]["label"] == "Set up the project"
    assert payload["not_offered"] == []
    assert payload["recommended"] == "explore-ml-data"
    assert payload["recommendation_reason"] == "no recorded data analysis yet"


def test_loop_pack_omits_the_setup_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The loop pack has no setup skill, so the board leaves that row out."""
    _isolate_home(tmp_path, monkeypatch)
    _install(tmp_path, *[name for name in _ENTRY if name != "setup-ml-project"])

    payload = triage_choices(tmp_path)

    assert "setup-ml-project" not in _skills(payload["choices"])
    assert "explore-ml-data" in _skills(payload["choices"])
    skipped = {row["skill"]: row for row in payload["not_offered"]}
    assert skipped["setup-ml-project"]["label"] == "Set up the project"
    assert skipped["setup-ml-project"]["reason"] == "setup-ml-project not installed"


def test_installed_skill_outside_the_board_is_not_offered(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Evaluate and audit are installed but never on the entry board."""
    _isolate_home(tmp_path, monkeypatch)
    _install(tmp_path, "evaluate-ml-pipeline", "audit-ml-pipeline")

    payload = triage_choices(tmp_path)

    assert payload["choices"] == []
    assert "evaluate-ml-pipeline" not in _skills(payload["not_offered"])
    assert payload["recommended"] is None


def test_unknown_install_status_is_flagged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No discoverable catalog means unknown, not a made-up menu."""
    _isolate_home(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "skore_skills.installed_skills._released_skill_ids", lambda: set()
    )

    payload = triage_choices(tmp_path)

    assert payload["choices"] == []
    assert payload["not_offered"][0]["reason"] == (
        "setup-ml-project install status unknown"
    )


def test_backlog_stage_recommends_the_backlog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A recorded analysis at the backlog stage recommends the backlog."""
    _isolate_home(tmp_path, monkeypatch)
    _install(tmp_path, *_ENTRY)
    _write(tmp_path / "data_analysis" / "data_analysis.md", "# report\n")
    _write(
        tmp_path / ".skore",
        json.dumps({"workspace": {"loop": {"stage": "backlog"}}}),
    )

    payload = triage_choices(tmp_path)

    assert payload["recommended"] == "manage-ml-backlog"
    assert payload["recommendation_reason"] == "the loop stage is backlog"


def test_missing_backlog_skill_keeps_the_other_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing backlog skill only drops its own row."""
    _isolate_home(tmp_path, monkeypatch)
    _install(tmp_path, *[name for name in _ENTRY if name != "manage-ml-backlog"])
    _write(tmp_path / "data_analysis" / "data_analysis.md", "# report\n")
    _write(
        tmp_path / ".skore",
        json.dumps({"workspace": {"loop": {"stage": "backlog"}}}),
    )

    payload = triage_choices(tmp_path)

    assert "manage-ml-backlog" not in _skills(payload["choices"])
    assert "review-ml-experiment" in _skills(payload["choices"])
    assert payload["recommended"] is None


def test_cli_prints_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``triage choices`` prints the board as JSON."""
    _isolate_home(tmp_path, monkeypatch)
    _install(tmp_path, "explore-ml-data")
    monkeypatch.chdir(tmp_path)

    result = CliRunner().invoke(cli, ["triage", "choices"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert _skills(payload["choices"]) == ["explore-ml-data"]


def test_cli_rejects_unknown_subcommand_and_directory_policy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unknown argv fails, and a ``.skore`` directory is a usage error."""
    _isolate_home(tmp_path, monkeypatch)
    monkeypatch.chdir(tmp_path)
    unknown = CliRunner().invoke(cli, ["triage", "unknown"])
    assert unknown.exit_code == 2

    (tmp_path / ".skore").mkdir()
    failed = CliRunner().invoke(cli, ["triage", "choices"])
    assert failed.exit_code != 0
    assert ".skore is a directory" in failed.output
