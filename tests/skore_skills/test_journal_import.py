"""Import a hand-written journal and render the same tables from the project."""

from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from skore_skills.cli import cli

JOURNAL = """\
# Journal

## History

| Stem | Intent | Status | Headline result | Report | Design note |
| --- | --- | --- | --- | --- | --- |
| 01_dummy | What MAE does a constant predictor reach? | done | rmse=1.2 | old | DummyRegressor. |

## Backlog

| # | Item | Source |
| --- | --- | --- |
| B1 | Fit a linear model. | user |

## Ideas

| Question | Status | Experiment | Source |
| --- | --- | --- | --- |
| Drop outliers? | open | 03_outliers | user |
| Try a log target? | aside | 04_log | design:01_dummy |
| Ignore the unused feature. | discarded | 05_unused | audit:01_dummy:checks.SKD004 |
"""


def test_journal_import_round_trips_the_three_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    journal = tmp_path / "journal"
    journal.mkdir()
    (journal / "JOURNAL.md").write_text(JOURNAL, encoding="utf-8")

    imported = CliRunner().invoke(cli, ["journal", "import"])
    assert imported.exit_code == 0, imported.output

    shown = CliRunner().invoke(cli, ["journal", "show"])
    assert shown.exit_code == 0, shown.output
    text = shown.output
    assert "What MAE does a constant predictor reach?" in text
    assert "| done |" in text or "| done |" in text.replace(" ", "")
    assert "Fit a linear model." in text
    assert "| B1 |" in text
    assert "Drop outliers?" in text
    assert "| open |" in text
    assert "Try a log target?" in text
    assert "| aside |" in text
    assert "Ignore the unused feature." in text
    assert "| discarded |" in text
    assert "audit:01_dummy:checks.SKD004" in text
    assert "design:01_dummy" in text

    again = CliRunner().invoke(cli, ["journal", "import"])
    assert again.exit_code == 0, again.output
    assert again.output.strip() == "0"
