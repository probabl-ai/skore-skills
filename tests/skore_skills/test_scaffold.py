"""Tests for ``skore_skills scaffold``."""

from __future__ import annotations

import compileall
from pathlib import Path

import pytest
from click.testing import CliRunner

from skore_skills.cli import cli


def test_scaffold_tree_and_no_placeholders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scaffold substitutes ``<pkg>`` and matches the skill file set."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["scaffold", "--package", "demo_pkg"])
    assert result.exit_code == 0, result.output
    src = tmp_path / "src" / "demo_pkg"
    assert (src / "__init__.py").is_file()
    assert (src / "data.py").is_file()
    assert (src / "features.py").is_file()
    assert (src / "pipeline.py").is_file()
    assert (src / "evaluate.py").is_file()
    evaluate_stub = (src / "evaluate.py").read_text(encoding="utf-8")
    assert "Do not pass ``splitter=``" in evaluate_stub
    assert "splitter = None" in evaluate_stub
    assert not (tmp_path / "experiments" / "01_baseline.py").exists()
    assert not (tmp_path / "data" / "data_analysis.py").exists()
    for rel in (
        "src/README.md",
        "experiments/README.md",
        "journal/README.md",
        "data_analysis/README.md",
        "data/README.md",
        "audit/README.md",
        "tests/smoke/README.md",
        "scratch/README.md",
    ):
        assert (tmp_path / rel).is_file(), rel
    assert not (tmp_path / "reports").exists()
    assert not (tmp_path / "reports" / "README.md").exists()
    assert (tmp_path / "pyproject.toml").is_file()
    assert (tmp_path / ".gitignore").is_file()
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".*" in gitignore.splitlines()
    assert "!.gitignore" in gitignore
    pyproject = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert not (tmp_path / "ruff.toml").exists()
    assert not (tmp_path / "journal" / "JOURNAL.md").exists()
    assert "[tool.ruff]" in pyproject
    assert '"data_analysis/**"' in pyproject
    assert 'name = "demo-pkg"' in pyproject
    for path in tmp_path.rglob("*"):
        if path.is_file() and path.suffix in {".py", ".toml", ".md"}:
            text = path.read_text(encoding="utf-8")
            assert "<pkg>" not in text
    assert compileall.compile_dir(str(src), quiet=1)


def test_scaffold_refuses_without_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second run on a complete layout exits non-zero unless ``--force``."""
    monkeypatch.chdir(tmp_path)
    runner = CliRunner()
    first = runner.invoke(cli, ["scaffold", "--package", "demo_pkg"])
    assert first.exit_code == 0, first.output
    second = runner.invoke(cli, ["scaffold", "--package", "demo_pkg"])
    assert second.exit_code != 0
    assert "refusing" in second.output
    forced = runner.invoke(cli, ["scaffold", "--package", "demo_pkg", "--force"])
    assert forced.exit_code == 0, forced.output


def test_scaffold_on_manager_only_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A ``pixi init`` root still scaffolds and keeps the manager's files."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pixi.toml").write_text(
        '[workspace]\nname = "demo"\n', encoding="utf-8"
    )
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "demo"\n', encoding="utf-8")
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("# pixi\n.pixi/\n", encoding="utf-8")
    result = CliRunner().invoke(cli, ["scaffold", "--package", "demo_pkg"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "src" / "demo_pkg" / "pipeline.py").is_file()
    assert not (tmp_path / "journal" / "JOURNAL.md").exists()
    kept = pyproject.read_text(encoding="utf-8")
    assert '[project]\nname = "demo"\n' in kept
    assert "[tool.ruff]" in kept
    assert gitignore.read_text(encoding="utf-8") == "# pixi\n.pixi/\n"


def test_full_scaffold_refuses_journal_only_workspace_without_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A journal-only workspace is existing and its index is preserved."""
    journal = tmp_path / "journal"
    journal.mkdir()
    index = journal / "JOURNAL.md"
    index.write_text("# Existing journal\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["scaffold", "--package", "demo_pkg"])
    assert result.exit_code != 0
    assert "refusing to overwrite" in result.output
    assert index.read_text(encoding="utf-8") == "# Existing journal\n"
    assert not (tmp_path / "src").exists()


def test_scaffold_specializes_env_init_skeleton(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Env-init Hatch metadata is rewritten once G-PKG-NAME is known."""
    from skore_skills.env import _PIXI_TABLE, _SKELETON

    monkeypatch.chdir(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(_SKELETON.lstrip() + "\n" + _PIXI_TABLE.strip() + "\n")
    result = CliRunner().invoke(cli, ["scaffold", "--package", "demo_pkg"])
    assert result.exit_code == 0, result.output
    text = pyproject.read_text(encoding="utf-8")
    assert 'name = "demo-pkg"' in text
    assert 'name = "workspace"' not in text
    assert 'packages = ["src/demo_pkg"]' in text
    assert 'packages = ["src"]' not in text
    assert "[tool.pixi.workspace]" in text
    assert "Workspace package for the demo_pkg ML experiments." in text


def test_scaffold_keeps_existing_tool_pixi(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scaffold does not replace a pyproject that already has ``[tool.pixi]``."""
    monkeypatch.chdir(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "demo"\n\n'
        '[tool.pixi.workspace]\nchannels = ["conda-forge"]\n',
        encoding="utf-8",
    )
    result = CliRunner().invoke(cli, ["scaffold", "--package", "demo_pkg"])
    assert result.exit_code == 0, result.output
    text = pyproject.read_text(encoding="utf-8")
    assert "[tool.pixi.workspace]" in text
    assert 'name = "demo"' in text
    assert "[tool.ruff]" in text


def test_scaffold_force_replaces_preserved_root_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``--force`` still replaces the packaged root configuration."""
    monkeypatch.chdir(tmp_path)
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text('[project]\nname = "stale"\n', encoding="utf-8")
    result = CliRunner().invoke(cli, ["scaffold", "--package", "demo_pkg", "--force"])
    assert result.exit_code == 0, result.output
    assert 'name = "demo-pkg"' in pyproject.read_text(encoding="utf-8")


def test_scaffold_requires_package() -> None:
    """A scaffold mode is mandatory."""
    result = CliRunner().invoke(cli, ["scaffold"])
    assert result.exit_code != 0
    assert "--package or --journal" in result.output


def test_scaffold_rejects_invalid_package(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Hyphenated names are not importable package directories."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["scaffold", "--package", "demo-pkg"])
    assert result.exit_code != 0
    assert "identifier" in result.output


def test_scaffold_journal_index_and_design(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Journal mode initializes the index and a substituted design note."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        cli,
        ["scaffold", "--journal", "--stem", "02_target_transform"],
    )
    assert result.exit_code == 0, result.output
    assert not (tmp_path / "journal" / "JOURNAL.md").exists()
    assert not (tmp_path / "journal" / "02_target_transform.md").exists()


def test_scaffold_journal_preserves_index_and_refuses_existing_design(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Journal mode preserves the index and requires force for a design."""
    journal_dir = tmp_path / "journal"
    journal_dir.mkdir()
    index = journal_dir / "JOURNAL.md"
    index.write_text("# Existing\n", encoding="utf-8")
    design = journal_dir / "01_baseline.md"
    design.write_text("# Existing design\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(
        cli,
        ["scaffold", "--journal", "--stem", "01_baseline"],
    )
    assert result.exit_code == 0, result.output
    assert index.read_text(encoding="utf-8") == "# Existing\n"
    assert design.read_text(encoding="utf-8") == "# Existing design\n"
    forced = CliRunner().invoke(
        cli,
        ["scaffold", "--journal", "--stem", "01_baseline", "--force"],
    )
    assert forced.exit_code == 0, forced.output
    assert index.read_text(encoding="utf-8") == "# Existing\n"
    assert design.read_text(encoding="utf-8") == "# Existing design\n"


@pytest.mark.parametrize(
    "argv",
    [
        ["scaffold", "--journal", "--stem", "../bad"],
        ["scaffold", "--package", "demo", "--stem", "01_baseline"],
        ["scaffold", "--package", "demo", "--journal"],
    ],
)
def test_scaffold_journal_rejects_bad_modes(argv: list[str]) -> None:
    """Journal mode rejects unsafe stems and conflicting options."""
    result = CliRunner().invoke(cli, argv)
    assert result.exit_code != 0


def test_specialize_env_skeleton_missing_file(tmp_path: Path) -> None:
    """Specialization is a no-op when env init has not written pyproject.toml."""
    from skore_skills.scaffold import specialize_env_skeleton

    assert specialize_env_skeleton(tmp_path / "pyproject.toml", "demo_pkg") is False


def test_scaffold_missing_templates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A package without the template tree cannot scaffold."""
    from skore_skills.scaffold import scaffold

    monkeypatch.setattr(
        "skore_skills.scaffold.template_root", lambda: tmp_path / "missing-templates"
    )
    with pytest.raises(ValueError, match="templates are missing"):
        scaffold(tmp_path / "proj", "demo_pkg")
