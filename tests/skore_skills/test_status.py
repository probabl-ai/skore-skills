"""Tests for ``skore_skills status`` and ``check workspace``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from skore_skills.cli import cli
from skore_skills.installed_skills import SIDECAR
from skore_skills.workspace import STATUS_KEYS, snapshot


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_sidecar(target: Path, skill_id: str) -> None:
    _write(
        target / skill_id / SIDECAR,
        json.dumps({"id": skill_id, "release": "v0", "hash": "abc"}) + "\n",
    )


def _write_catalog(target: Path, skill_ids: list[str]) -> None:
    skills = [{"id": name, "path": f"skills/{name}"} for name in skill_ids]
    _write(
        target / ".catalog.json",
        json.dumps({"sources": {"probabl-ai/skore-skills": {"skills": skills}}}) + "\n",
    )


@pytest.fixture(autouse=True)
def _isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Keep ``--global`` installs from leaking into status tests."""
    home = tmp_path / "isolated-home"
    home.mkdir()
    monkeypatch.setattr("skore_skills.installed_skills.Path.home", lambda: home)
    return home


def test_status_empty_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """An empty tree reports ``env_manager=none`` and no ``src/``."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["status", "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert list(payload) == list(STATUS_KEYS)
    assert payload["env_manager"] == "none"
    assert payload["has_src"] is False
    assert payload["package"] is None
    assert payload["data_analysis"] == "missing"
    assert payload["git"] is False
    assert payload["last_history_stem"] is None
    assert payload["loop_stage"] == "setup"
    assert payload["policy"]["git"]["autocommit"] is None
    flags = payload["skills"]
    assert flags
    assert flags["setup-git"] is False
    assert all(value is False for value in flags.values())


def test_status_text_format(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``--format text`` is parseable key: value lines."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["status", "--format", "text"])
    assert result.exit_code == 0, result.output
    assert result.output.startswith("package: None")
    assert "env_manager: none" in result.output


def test_status_organized_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A tree with organize-like layout fills the frozen keys."""
    _write(tmp_path / "pyproject.toml", '[project]\nname = "demo-pkg"\n')
    _write(tmp_path / "pixi.toml", '[workspace]\nname = "demo"\n')
    (tmp_path / "src" / "demo_pkg").mkdir(parents=True)
    (tmp_path / "experiments").mkdir()
    (tmp_path / "journal").mkdir()
    _write(tmp_path / "journal" / "JOURNAL.md", "# placeholder\n")
    _write(tmp_path / "journal" / "01_baseline.md", "# note\n")
    (tmp_path / "tests").mkdir()
    _write(tmp_path / "data_analysis" / "data_analysis.md", "# eda\n")
    _write(tmp_path / "ruff.toml", 'target-version = "py311"\n')
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["status"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    skills = payload.pop("skills")
    assert payload == {
        "package": "demo-pkg",
        "env_manager": "pixi",
        "managers": ["pixi"],
        "evidence": {"pixi": ["pixi.toml"]},
        "ambiguous": False,
        "mismatch": False,
        "has_src": True,
        "has_experiments": True,
        "has_journal": True,
        "has_tests": True,
        "data_analysis": "present",
        "modeling_decisions": "missing",
        "ruff_toml": True,
        "git": True,
        "last_history_stem": "01_baseline",
        "policy": {
            "env_manager": None,
            "package": None,
            "tabular": None,
            "skore_mode": None,
            "notebooks": None,
            "site": None,
            "env": {"managed": None},
            "git": {"autocommit": None, "snapshot": None},
            "loop": {"stage": None, "stem": None},
            "setup": {
                "env": None,
                "workspace": None,
                "editable": None,
                "git": None,
            },
        },
        "setup": {
            "env": "missing",
            "workspace": "done",
            "editable": "missing",
            "git": "missing",
            "pending": ["env", "editable", "git"],
        },
        "loop_stage": "implement",
        "workspace": "durable",
    }
    assert skills
    assert all(value is False for value in skills.values())


def test_status_data_analysis_reads_data_analysis_dir_not_data_dir(
    tmp_path: Path,
) -> None:
    """The report lives in ``data_analysis/``; ``data/`` is raw data."""
    _write(tmp_path / "data" / "data_analysis.md", "# stale\n")
    assert snapshot(tmp_path)["data_analysis"] == "missing"
    _write(tmp_path / "data_analysis" / "data_analysis.md", "# report\n")
    assert snapshot(tmp_path)["data_analysis"] == "present"


def test_status_data_analysis_skipped_from_journal(tmp_path: Path) -> None:
    """JOURNAL Status skipped is ``data_analysis: skipped``."""
    (tmp_path / "src").mkdir()
    _write(
        tmp_path / "journal" / "JOURNAL.md",
        "## Data understanding\n\n"
        "| Variable | Value |\n"
        "|---|---|\n"
        "| Status | skipped — 2026-09-18 |\n\n"
        "## History\n",
    )
    payload = snapshot(tmp_path)
    assert payload["data_analysis"] == "skipped"
    assert payload["loop_stage"] == "implement"


def test_status_data_analysis_present_overrides_journal_skipped(tmp_path: Path) -> None:
    """``data_analysis/data_analysis.md`` wins when JOURNAL still says skipped."""
    (tmp_path / "src").mkdir()
    _write(
        tmp_path / "journal" / "JOURNAL.md",
        "## Data understanding\n\n"
        "| Variable | Value |\n"
        "|---|---|\n"
        "| Status | skipped — 2026-09-18 |\n",
    )
    _write(tmp_path / "data_analysis" / "data_analysis.md", "# report\n")
    assert snapshot(tmp_path)["data_analysis"] == "present"


def test_status_hatchling_build_is_not_hatch_env_manager(tmp_path: Path) -> None:
    """``[tool.hatch.build]`` alone is a build backend, not hatch envs."""
    _write(
        tmp_path / "pyproject.toml",
        '[tool.hatch.build.targets.wheel]\npackages = ["src/pkg"]\n',
    )
    assert snapshot(tmp_path)["env_manager"] == "none"
    _write(tmp_path / "pyproject.toml", "[tool.ruff]\nline-length = 88\n")
    assert snapshot(tmp_path)["ruff_toml"] is True


@pytest.mark.parametrize(
    ("files", "dirs", "toml", "expected"),
    [
        ({"pixi.lock": ""}, (), None, "pixi"),
        ({"uv.lock": ""}, (), None, "uv"),
        (
            {},
            (),
            "[tool.uv]\ndev-dependencies = []\n",
            "uv",
        ),
        ({"poetry.lock": ""}, (), None, "poetry"),
        ({}, (), '[tool.poetry]\nname = "x"\n', "poetry"),
        ({"hatch.toml": ""}, (), None, "hatch"),
        ({}, (), "[tool.hatch.envs.default]\n", "hatch"),
        ({}, (), "[tool.pixi.workspace]\nchannels = []\n", "pixi"),
        ({"environment.yml": "name: x\n"}, (), None, "conda"),
        ({"environment.yaml": "name: x\n"}, (), None, "conda"),
        ({"requirements.txt": "click\n"}, (".venv",), None, "pip-venv"),
        ({"requirements.txt": "click\n"}, ("venv",), None, "pip-venv"),
    ],
)
def test_status_each_manager_signal(
    tmp_path: Path,
    files: dict[str, str],
    dirs: tuple[str, ...],
    toml: str | None,
    expected: str,
) -> None:
    """Each documented manager signal is detected from the filesystem."""
    for name, body in files.items():
        _write(tmp_path / name, body)
    for name in dirs:
        (tmp_path / name).mkdir()
    if toml is not None:
        _write(tmp_path / "pyproject.toml", toml)
    assert snapshot(tmp_path)["env_manager"] == expected


def test_status_pyproject_without_tool_is_not_a_manager(tmp_path: Path) -> None:
    """``[project]`` alone does not imply an env manager."""
    _write(tmp_path / "pyproject.toml", '[project]\nname = "solo"\n')
    assert snapshot(tmp_path)["env_manager"] == "none"
    assert snapshot(tmp_path)["package"] == "solo"


def test_status_package_from_src_dir(tmp_path: Path) -> None:
    """Without ``[project].name``, the first ``src/`` directory is used."""
    (tmp_path / "src" / "fromsrc").mkdir(parents=True)
    assert snapshot(tmp_path)["package"] == "fromsrc"


def test_check_workspace_exit_codes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exit 1 if ``src/`` is missing **and** ``journal/`` is missing.

    Either directory alone is enough to count as scaffolded.
    """
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    empty = runner.invoke(cli, ["check", "workspace", "--format", "json"])
    assert empty.exit_code == 1
    assert json.loads(empty.output) == {"scaffolded": False}

    (tmp_path / "src").mkdir()
    with_src = runner.invoke(cli, ["check", "workspace"])
    assert with_src.exit_code == 0
    assert json.loads(with_src.output) == {"scaffolded": True}

    (tmp_path / "src").rmdir()
    (tmp_path / "journal").mkdir()
    with_journal = runner.invoke(cli, ["check", "workspace", "--format", "text"])
    assert with_journal.exit_code == 0
    assert with_journal.output == "scaffolded\n"


def test_check_workspace_empty_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Empty dir text format still exits 1."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["check", "workspace", "--format", "text"])
    assert result.exit_code == 1
    assert result.output == "not scaffolded\n"


def test_status_skills_fallback_catalog_all_false(tmp_path: Path) -> None:
    """No sidecars: released catalog ids are present and all ``false``."""
    flags = snapshot(tmp_path)["skills"]
    assert flags["setup-git"] is False
    assert flags["setup-workspace"] is False
    assert all(value is False for value in flags.values())


def test_status_skills_ignores_skill_md_without_sidecar(tmp_path: Path) -> None:
    """A bare ``SKILL.md`` is not an install record."""
    _write(tmp_path / ".claude" / "skills" / "setup-git" / "SKILL.md")
    flags = snapshot(tmp_path)["skills"]
    assert flags["setup-git"] is False


def test_status_skills_from_sidecar_and_target_catalog(tmp_path: Path) -> None:
    """Sidecars mark install; the target catalog is the id universe."""
    target = tmp_path / ".agents" / "skills"
    _write_catalog(target, ["setup-git", "setup-workspace", "setup-python-env"])
    _write_sidecar(target, "setup-git")
    flags = snapshot(tmp_path)["skills"]
    assert flags == {
        "setup-git": True,
        "setup-python-env": False,
        "setup-workspace": False,
    }


def test_status_skills_from_global_home(tmp_path: Path, _isolated_home: Path) -> None:
    """A ``--global`` sidecar under ``$HOME`` counts as installed."""
    target = _isolated_home / ".agents" / "skills"
    _write_catalog(target, ["setup-git", "setup-workspace"])
    _write_sidecar(target, "setup-workspace")
    flags = snapshot(tmp_path)["skills"]
    assert flags["setup-workspace"] is True
    assert flags["setup-git"] is False


def test_status_skills_unknown_without_any_catalog(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No sidecars and no readable released catalog → empty mapping."""
    monkeypatch.setattr(
        "skore_skills.installed_skills._released_skill_ids", lambda: set()
    )
    assert snapshot(tmp_path)["skills"] == {}


def test_status_skills_from_unknown_harness_dir(tmp_path: Path) -> None:
    """A harness this package never heard of is still discovered."""
    target = tmp_path / ".futureharness" / "skills"
    _write_sidecar(target, "setup-git")
    assert snapshot(tmp_path)["skills"]["setup-git"] is True


def test_status_skills_from_nested_harness_dir(tmp_path: Path) -> None:
    """A target one level deeper (``.codeium/windsurf/skills``) is found."""
    target = tmp_path / ".codeium" / "windsurf" / "skills"
    _write_catalog(target, ["setup-git", "setup-workspace"])
    _write_sidecar(target, "setup-git")
    flags = snapshot(tmp_path)["skills"]
    assert flags == {"setup-git": True, "setup-workspace": False}


def test_status_skills_catalog_only_target(tmp_path: Path) -> None:
    """A target catalog with no sidecars defines the universe as false."""
    _write_catalog(tmp_path / ".agents" / "skills", ["alpha-skill", "beta-skill"])
    flags = snapshot(tmp_path)["skills"]
    assert flags == {"alpha-skill": False, "beta-skill": False}


def test_first_manager_follows_table_order() -> None:
    """The first manifest in manager order wins; an empty map is ``none``."""
    from skore_skills.workspace import first_manager

    assert first_manager({"uv": ["uv.lock"], "pixi": ["pixi.toml"]}) == "pixi"
    assert first_manager({"conda": ["environment.yml"]}) == "conda"
    assert first_manager({}) == "none"


def test_status_setup_empty_tree_is_pending(tmp_path: Path) -> None:
    """A fresh tree has every setup piece missing except editable."""
    setup = snapshot(tmp_path)["setup"]
    assert setup == {
        "env": "missing",
        "workspace": "missing",
        "editable": "missing",
        "git": "missing",
        "pending": ["env", "workspace", "git"],
    }


def test_status_setup_infers_done_pieces(tmp_path: Path) -> None:
    """A recorded env, scaffold, and git are done; editable stays missing."""
    from skore_skills.policy import set_policy_value

    _write(tmp_path / "pixi.toml", '[workspace]\nname = "demo"\n')
    (tmp_path / "src" / "demo").mkdir(parents=True)
    (tmp_path / ".git").mkdir()
    set_policy_value(tmp_path, "env_manager", "pixi")
    set_policy_value(tmp_path, "env.managed", "true")
    set_policy_value(tmp_path, "git.autocommit", "on")
    setup = snapshot(tmp_path)["setup"]
    assert setup["env"] == "done"
    assert setup["workspace"] == "done"
    assert setup["git"] == "done"
    assert setup["editable"] == "missing"
    assert setup["pending"] == ["editable"]


def test_status_setup_declined_wins_over_inference(tmp_path: Path) -> None:
    """A stored decline stays declined even when the files exist."""
    from skore_skills.policy import set_policy_value

    (tmp_path / "journal").mkdir()
    (tmp_path / ".git").mkdir()
    set_policy_value(tmp_path, "git.autocommit", "off")
    set_policy_value(tmp_path, "setup.workspace", "declined")
    set_policy_value(tmp_path, "setup.git", "declined")
    setup = snapshot(tmp_path)["setup"]
    assert setup["workspace"] == "declined"
    assert setup["git"] == "declined"
    assert "workspace" not in setup["pending"]
    assert "git" not in setup["pending"]


def test_status_setup_unmanaged_env_is_done(tmp_path: Path) -> None:
    """``env.managed`` false with a recorded manager needs no manifest."""
    from skore_skills.policy import set_policy_value

    set_policy_value(tmp_path, "env_manager", "uv")
    set_policy_value(tmp_path, "env.managed", "false")
    assert snapshot(tmp_path)["setup"]["env"] == "done"


def test_status_setup_managed_without_manifest_stays_missing(tmp_path: Path) -> None:
    """A managed manager is done only after its manifest matches."""
    from skore_skills.policy import set_policy_value

    set_policy_value(tmp_path, "env_manager", "pixi")
    set_policy_value(tmp_path, "env.managed", "true")
    assert snapshot(tmp_path)["setup"]["env"] == "missing"


def test_status_setup_ignores_non_object_record() -> None:
    """A non-object ``setup`` value falls back to inference."""
    from skore_skills.policy import empty_policy
    from skore_skills.workspace import setup_status

    policy = empty_policy()
    policy["setup"] = "nope"
    setup = setup_status(
        policy,
        env_manager=None,
        ambiguous=False,
        has_src=False,
        has_journal=True,
        git=False,
    )
    assert setup["workspace"] == "done"
    assert setup["env"] == "missing"
    assert setup["pending"] == ["env", "editable", "git"]


def test_status_skills_ignores_out_of_bound_depth(tmp_path: Path) -> None:
    """Sidecars deeper than ``<dot-dir>/<sub>/skills`` are not scanned."""
    deep = tmp_path / ".cache" / "a" / "b" / "skills"
    _write_sidecar(deep, "deep-skill")
    flags = snapshot(tmp_path)["skills"]
    assert "deep-skill" not in flags
    assert all(value is False for value in flags.values())
