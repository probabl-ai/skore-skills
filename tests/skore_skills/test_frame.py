"""Tests for ``skore-skills frame show``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from skore_skills.cli import cli
from skore_skills.frame import frame_show
from skore_skills.workspace import snapshot

_LABELS = (
    "Status",
    "Revised on",
    "Prediction goal",
    "Deployment",
    "Horizon",
    "Gap",
    "Generalize to",
    "Known at predict",
    "Time role",
    "Metric role",
    "Metric",
    "Baseline",
    "Baseline note",
    "Folds",
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _journal(root: Path, **values: str) -> None:
    lines = [
        "# JOURNAL",
        "",
        "## Modeling decisions",
        "",
        "| Variable | Value |",
        "|---|---|",
    ]
    lines.extend(f"| {label} | {values.get(label, '')} |" for label in _LABELS)
    lines.extend(["", "## History", ""])
    _write(root / "journal" / "JOURNAL.md", "\n".join(lines))


def _locked_iid(**overrides: str) -> dict[str, str]:
    rows = {
        "Status": "locked",
        "Revised on": "n/a",
        "Prediction goal": "point_predictions",
        "Deployment": "iid",
        "Horizon": "n/a",
        "Gap": "n/a",
        "Generalize to": "n/a",
        "Known at predict": "n/a",
        "Time role": "n/a",
        "Metric role": "point_error",
        "Metric": "MAE",
        "Baseline": "dummy",
        "Baseline note": "global mean",
        "Folds": "5",
    }
    rows.update(overrides)
    return rows


def test_missing_scaffold(tmp_path: Path) -> None:
    assert frame_show(tmp_path) == {"action": "stop", "reason": "missing_scaffold"}


def test_missing_journal_file_is_stop(tmp_path: Path) -> None:
    (tmp_path / "journal").mkdir()

    assert frame_show(tmp_path)["reason"] == "missing_scaffold"


def _question(payload: dict, key: str) -> dict:
    questions = payload["questions"]
    assert isinstance(questions, list)
    return next(item for item in questions if item["key"] == key)


def _targets(*items: tuple[str, str]) -> str:
    return (
        json.dumps(
            {"targets": [{"column": column, "task": task} for column, task in items]}
        )
        + "\n"
    )


def test_blank_journal_asks_every_missing_decision(tmp_path: Path) -> None:
    _journal(tmp_path)
    _write(
        tmp_path / "scratch" / "data_analysis" / "extras.json",
        _targets(("label", "classification")),
    )

    payload = frame_show(tmp_path)

    assert payload["action"] == "ask"
    assert payload["reason"] == "missing_keys"
    assert payload["missing"] == [
        "prediction_goal",
        "deployment",
        "known_at_predict",
        "metric_role",
        "metric",
        "baseline",
        "baseline_note",
        "folds",
    ]
    assert "fill_na" not in payload
    goal = _question(payload, "prediction_goal")
    assert goal["candidates"] == ["probabilities", "point_labels", "uncovered"]
    assert goal["reference"] == "references/prediction-goal.md"
    for key in ("horizon", "gap", "time_role", "generalize_to"):
        assert key not in payload["missing"]
    assert _question(payload, "baseline")["candidates"] == [
        "seasonal_naive",
        "group_mean",
        "logistic",
        "production",
        "dummy",
    ]


def test_time_deployment_asks_the_remaining_cells(tmp_path: Path) -> None:
    _journal(
        tmp_path,
        **{
            "Status": "draft",
            "Prediction goal": "point_predictions",
            "Deployment": "time",
        },
    )

    payload = frame_show(tmp_path)

    assert "generalize_to" not in payload["missing"]
    assert payload["fill_na"] == ["generalize_to"]
    assert "horizon" in payload["missing"]
    assert "folds" in payload["missing"]
    horizon = _question(payload, "horizon")
    assert horizon["reference"] == "references/horizon-gap.md"
    assert "candidates" not in horizon
    assert _question(payload, "time_role")["reference"] == "references/time-role.md"


def test_complete_draft_asks_to_set(tmp_path: Path) -> None:
    _journal(tmp_path, **_locked_iid(Status="draft"))

    payload = frame_show(tmp_path)

    assert payload["action"] == "ask"
    assert payload["reason"] == "set"
    assert "choices" not in payload
    assert payload["context"]["metric"] == "MAE"
    assert payload["context"]["folds"] == "5"


def test_locked_iid_translates_to_kfold(tmp_path: Path) -> None:
    _journal(tmp_path, **_locked_iid())

    payload = frame_show(tmp_path)

    assert payload["action"] == "proceed"
    assert payload["reason"] == "locked"
    assert payload["translation"] == {
        "splitter": "KFold",
        "pattern": "A",
        "scheme": None,
        "n_splits": 5,
        "horizons": None,
        "horizon_unit": None,
        "gap": None,
        "gap_unit": None,
        "groups": None,
        "report": None,
        "metric": "MAE",
        "task": "",
        "targets": [],
    }


def test_locked_time_translates_to_a_date_splitter(tmp_path: Path) -> None:
    _journal(
        tmp_path,
        **_locked_iid(
            Deployment="time",
            Horizon="7 day",
            Gap="7 day",
            **{"Time role": "sort_key"},
            **{"Generalize to": "n/a"},
            Baseline="seasonal_naive",
            **{"Baseline note": "last observed week"},
            Folds="4",
        ),
    )

    payload = frame_show(tmp_path)

    assert payload["translation"]["splitter"] is None
    assert payload["translation"]["pattern"] == "B"
    assert payload["translation"]["scheme"] == "date_time"
    assert payload["translation"]["groups"] is None
    assert payload["translation"]["n_splits"] == 4
    assert payload["translation"]["horizons"] == [7]
    assert payload["translation"]["horizon_unit"] == "day"
    assert payload["translation"]["gap"] == 7
    assert payload["translation"]["gap_unit"] == "day"


def test_locked_groups_translate_to_group_kfold(tmp_path: Path) -> None:
    _journal(
        tmp_path,
        **_locked_iid(
            Deployment="groups",
            **{"Generalize to": "store_id"},
            **{"Known at predict": "region"},
            Baseline="group_mean",
            **{"Baseline note": "region"},
        ),
    )

    payload = frame_show(tmp_path)

    assert payload["translation"]["splitter"] == "GroupKFold"
    assert payload["translation"]["pattern"] == "B"
    assert payload["translation"]["groups"] == "store_id"
    assert payload["translation"]["n_splits"] == 5


def test_one_fold_translates_to_estimator_report(tmp_path: Path) -> None:
    _journal(tmp_path, **_locked_iid(Folds="1"))

    payload = frame_show(tmp_path)

    assert payload["translation"]["splitter"] is None
    assert payload["translation"]["report"] == "EstimatorReport"
    assert payload["translation"]["n_splits"] is None


def test_predefined_folds_translate_to_prefit(tmp_path: Path) -> None:
    _journal(tmp_path, **_locked_iid(Folds="predefined"))

    payload = frame_show(tmp_path)

    assert payload["action"] == "proceed"
    translation = payload["translation"]
    assert translation["splitter"] == "prefit"
    assert translation["report"] == "EstimatorReport"
    assert translation["n_splits"] is None
    assert translation["pattern"] is None
    assert translation["scheme"] is None


def test_predefined_time_does_not_become_a_date_splitter(tmp_path: Path) -> None:
    _journal(
        tmp_path,
        **_locked_iid(
            Deployment="time",
            Horizon="7 day",
            Gap="7 day",
            **{"Time role": "sort_key"},
            **{"Generalize to": "n/a"},
            Baseline="seasonal_naive",
            **{"Baseline note": "last observed week"},
            Folds="predefined",
        ),
    )

    payload = frame_show(tmp_path)

    assert payload["translation"]["splitter"] == "prefit"
    assert payload["translation"]["scheme"] is None
    assert payload["translation"]["pattern"] is None
    assert payload["translation"]["report"] == "EstimatorReport"


def test_prefit_is_not_a_folds_cell(tmp_path: Path) -> None:
    _journal(tmp_path, **_locked_iid(Folds="prefit"))

    payload = frame_show(tmp_path)

    assert payload["reason"] == "missing_keys"
    assert "folds" in payload["missing"]


def test_horizon_list_locks_with_one_baseline(tmp_path: Path) -> None:
    _journal(
        tmp_path,
        **_locked_iid(
            Deployment="time",
            Horizon="1 hour, 24 hour",
            Gap="0 hour",
            **{"Time role": "sort_key"},
            Baseline="seasonal_naive",
            **{"Baseline note": "last week"},
        ),
    )

    payload = frame_show(tmp_path)

    assert payload["action"] == "proceed"
    assert payload["translation"]["horizons"] == [1, 24]
    assert payload["translation"]["horizon_unit"] == "hour"
    assert payload["translation"]["gap"] == 0
    assert payload["decisions"]["baseline"] == "seasonal_naive"


def test_several_baselines_stay_open(tmp_path: Path) -> None:
    """The baseline cell and its note are one token and one phrase."""
    _journal(
        tmp_path,
        **_locked_iid(
            Baseline="dummy, logistic",
            **{"Baseline note": "majority class; logistic probabilities"},
        ),
    )

    payload = frame_show(tmp_path)

    assert "baseline" in payload["missing"]
    assert "baseline_note" in payload["missing"]


def test_zero_gap_with_a_longer_horizon_proceeds(tmp_path: Path) -> None:
    _journal(
        tmp_path,
        **_locked_iid(
            Deployment="time",
            Horizon="7 day",
            Gap="0 day",
            **{"Time role": "sort_key"},
            Baseline="seasonal_naive",
            **{"Baseline note": "last observed week"},
        ),
    )

    payload = frame_show(tmp_path)

    assert payload["action"] == "proceed"
    assert payload["translation"]["gap"] == 0
    assert payload["translation"]["horizons"] == [7]


def test_mismatched_gap_units_ask_instead_of_converting(tmp_path: Path) -> None:
    _journal(
        tmp_path,
        **_locked_iid(
            Deployment="time",
            Horizon="7 day",
            Gap="24 hour",
            **{"Time role": "sort_key"},
            Baseline="seasonal_naive",
            **{"Baseline note": "last observed week"},
        ),
    )

    assert frame_show(tmp_path)["reason"] == "gap_unit_mismatch"


def test_group_mean_on_the_generalize_to_column_does_not_lock(tmp_path: Path) -> None:
    _journal(
        tmp_path,
        **_locked_iid(
            Deployment="groups",
            **{"Generalize to": "store_id"},
            **{"Known at predict": "store_id"},
            Baseline="group_mean",
            **{"Baseline note": "store_id"},
        ),
    )

    payload = frame_show(tmp_path)

    assert payload["action"] == "ask"
    assert payload["reason"] == "group_mean_on_generalize_to"
    assert "seasonal_naive" not in payload["candidates"]
    assert "group_mean" in payload["candidates"]


def test_iid_deployment_fills_time_and_group_cells(tmp_path: Path) -> None:
    """Independent rows do not ask horizon, gap, time role, or generalize-to."""
    _journal(
        tmp_path,
        **_locked_iid(
            Horizon="",
            Gap="",
            **{"Time role": "", "Generalize to": ""},
        ),
    )

    payload = frame_show(tmp_path)

    assert payload["action"] == "ask"
    assert payload["reason"] == "fill_na"
    assert payload["fill_na"] == ["horizon", "gap", "time_role", "generalize_to"]
    assert "missing" not in payload
    assert "questions" not in payload


def test_iid_time_role_answer_is_replaced_not_asked(tmp_path: Path) -> None:
    """A volunteered time role on an i.i.d. deployment is n/a, not a question."""
    from skore_skills.frame import _raw_rows, frame_fill

    _journal(tmp_path, **_locked_iid(**{"Time role": "covariate"}))
    before = (tmp_path / "journal" / "JOURNAL.md").read_text(encoding="utf-8")

    payload = frame_show(tmp_path)

    assert payload["reason"] == "fill_na"
    assert payload["fill_na"] == ["time_role"]
    assert "questions" not in payload
    assert payload["action"] != "proceed"

    filled = frame_fill(tmp_path)

    assert filled == {"action": "filled", "filled": ["time_role"]}
    assert _raw_rows(tmp_path)["time_role"] == "n/a"
    assert _raw_rows(tmp_path)["status"] == "locked"
    assert "Revised on | n/a" in before
    text = (tmp_path / "journal" / "JOURNAL.md").read_text(encoding="utf-8")
    assert "| Revised on | n/a |" in text
    assert frame_show(tmp_path)["action"] == "proceed"
    assert frame_fill(tmp_path) == {"action": "unchanged", "filled": []}


def test_groups_deployment_asks_generalize_to_and_fills_time(
    tmp_path: Path,
) -> None:
    """Group deployment asks the id column and fills the time cells."""
    _journal(
        tmp_path,
        **_locked_iid(
            Status="draft",
            Deployment="groups",
            Horizon="",
            Gap="",
            **{"Time role": "", "Generalize to": ""},
        ),
    )

    payload = frame_show(tmp_path)

    assert payload["missing"] == ["generalize_to"]
    assert payload["fill_na"] == ["horizon", "gap", "time_role"]
    assert "candidates" not in _question(payload, "generalize_to")


def test_frame_fill_on_time_writes_only_generalize_to(tmp_path: Path) -> None:
    """A time deployment keeps horizon and gap and clears generalize-to."""
    from skore_skills.frame import _raw_rows, frame_fill

    _journal(
        tmp_path,
        **{
            "Status": "draft",
            "Revised on": "2026-09-25",
            "Prediction goal": "point_predictions",
            "Deployment": "time",
            "Horizon": "1 hour",
            "Generalize to": "store_id",
        },
    )

    payload = frame_fill(tmp_path)
    rows = _raw_rows(tmp_path)

    assert payload["filled"] == ["generalize_to"]
    assert rows["generalize_to"] == "n/a"
    assert rows["horizon"] == "1 hour"
    assert rows["gap"] == ""
    assert rows["status"] == "draft"
    assert rows["revised_on"] == "2026-09-25"


def test_frame_fill_before_deployment_changes_nothing(tmp_path: Path) -> None:
    """An unknown deployment has no n/a cells to write."""
    from skore_skills.frame import frame_fill

    _journal(tmp_path)
    before = (tmp_path / "journal" / "JOURNAL.md").read_text(encoding="utf-8")

    assert frame_fill(tmp_path) == {"action": "unchanged", "filled": []}
    assert (tmp_path / "journal" / "JOURNAL.md").read_text(encoding="utf-8") == before


def test_frame_fill_rejects_a_missing_row(tmp_path: Path) -> None:
    """Filling fails when the table has no row for that cell, and does not write."""
    from skore_skills.frame import frame_fill

    path = tmp_path / "journal" / "JOURNAL.md"
    _write(
        path,
        "\n".join(
            [
                "# JOURNAL",
                "",
                "## Modeling decisions",
                "",
                "| Variable | Value |",
                "|---|---|",
                "| Deployment | iid |",
                "| Horizon | 7 day |",
                "",
                "## History",
                "",
            ]
        ),
    )
    before = path.read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="missing gap, time_role, generalize_to"):
        frame_fill(tmp_path)

    assert path.read_text(encoding="utf-8") == before


def test_iid_rejects_a_seasonal_baseline(tmp_path: Path) -> None:
    """A time-only baseline is asked again once deployment is iid."""
    _journal(tmp_path, **_locked_iid(Baseline="seasonal_naive"))

    payload = frame_show(tmp_path)

    assert payload["missing"] == ["baseline"]
    assert payload["candidates"] == ["production", "dummy"]


def test_iid_baseline_omits_seasonal_naive(tmp_path: Path) -> None:
    rows = _locked_iid(Status="draft")
    rows["Baseline"] = ""
    rows["Baseline note"] = ""
    _journal(tmp_path, **rows)

    payload = frame_show(tmp_path)

    assert "baseline" in payload["missing"]
    assert _question(payload, "baseline")["candidates"] == ["production", "dummy"]
    assert _question(payload, "baseline")["reference"] == "references/baseline.md"


def test_revise_asks_and_draft_blocks_proceed(tmp_path: Path) -> None:
    _journal(tmp_path, **_locked_iid())

    revise = frame_show(tmp_path, revise=True)

    assert revise["action"] == "ask"
    assert revise["reason"] == "revise"
    assert revise["choices"] == ["modify", "keep", "stop"]
    assert frame_show(tmp_path)["action"] == "proceed"

    _journal(tmp_path, **_locked_iid(Status="draft", **{"Revised on": "2026-09-25"}))

    draft = frame_show(tmp_path)
    assert draft["reason"] == "set"
    assert "choices" not in draft
    assert frame_show(tmp_path, revise=True)["reason"] == "set"


def test_status_reads_the_block(tmp_path: Path) -> None:
    assert snapshot(tmp_path)["modeling_decisions"] == "missing"
    _journal(tmp_path, **_locked_iid(Status="draft"))
    assert snapshot(tmp_path)["modeling_decisions"] == "draft"
    _journal(tmp_path, **_locked_iid())
    assert snapshot(tmp_path)["modeling_decisions"] == "locked"


def test_unsupported_task_uses_the_fallback(tmp_path: Path) -> None:
    _journal(tmp_path)
    _write(
        tmp_path / "scratch" / "data_analysis" / "extras.json",
        _targets(("segment", "clustering")),
    )

    payload = frame_show(tmp_path)

    assert payload["action"] == "ask"
    assert payload["reason"] == "uncovered"
    assert payload["reference"] == "references/fallback.md"
    assert payload["context"] == {"task": "clustering", "targets": ["segment"]}
    assert "candidates" not in payload


def test_uncovered_prose_locks_without_a_translation(tmp_path: Path) -> None:
    _journal(
        tmp_path,
        **{
            "Status": "draft",
            "Prediction goal": "uncovered",
            "Metric": "a clustering that matches the known segments",
            "Baseline note": "one cluster per site",
        },
    )

    draft = frame_show(tmp_path)

    assert draft["reason"] == "set"
    assert "choices" not in draft
    assert draft["context"]["prediction_goal"] == "uncovered"

    _journal(
        tmp_path,
        **{
            "Status": "locked",
            "Prediction goal": "uncovered",
            "Metric": "a clustering that matches the known segments",
            "Baseline note": "one cluster per site",
        },
    )

    locked = frame_show(tmp_path)

    assert locked["action"] == "proceed"
    assert locked["translation"] is None


def test_cli_prints_json(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["frame", "show"])

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["reason"] == "missing_scaffold"


def test_alignment_row_and_corrupt_task_file(tmp_path: Path) -> None:
    """A colon alignment row is not a value, and corrupt extras.json is ignored."""
    _journal(tmp_path, **_locked_iid())
    path = tmp_path / "journal" / "JOURNAL.md"
    path.write_text(
        path.read_text(encoding="utf-8").replace("|---|---|", "|:---|:---|"),
        encoding="utf-8",
    )
    assert frame_show(tmp_path)["action"] == "proceed"

    _journal(tmp_path)
    _write(tmp_path / "scratch" / "data_analysis" / "extras.json", "{")
    payload = frame_show(tmp_path)
    assert payload["reason"] == "missing_keys"
    assert payload["missing"][0] == "prediction_goal"
    assert _question(payload, "prediction_goal")["candidates"] == [
        "probabilities",
        "point_labels",
        "intervals",
        "point_predictions",
        "uncovered",
    ]


def test_unusable_target_entries_leave_the_full_menu(tmp_path: Path) -> None:
    """A targets payload that is not column/task pairs records no task."""
    _journal(tmp_path)
    extras = tmp_path / "scratch" / "data_analysis" / "extras.json"
    full_menu = [
        "probabilities",
        "point_labels",
        "intervals",
        "point_predictions",
        "uncovered",
    ]
    payloads = [
        "[]",
        json.dumps({"targets": {"column": "label", "task": "classification"}}),
        json.dumps({"targets": []}),
        json.dumps(
            {
                "targets": [
                    "label",
                    {"column": 1, "task": "regression"},
                    {"column": "amount", "task": None},
                    {"column": " ", "task": "classification"},
                    {"column": "label", "task": " "},
                ]
            }
        ),
    ]
    for text in payloads:
        _write(extras, text)
        payload = frame_show(tmp_path)
        assert _question(payload, "prediction_goal")["candidates"] == full_menu


def test_regression_task_offers_interval_goals(tmp_path: Path) -> None:
    """A recorded regression task asks for intervals or point predictions."""
    _journal(tmp_path)
    _write(
        tmp_path / "scratch" / "data_analysis" / "extras.json",
        _targets(("amount", "regression")),
    )
    payload = frame_show(tmp_path)
    assert _question(payload, "prediction_goal")["candidates"] == [
        "intervals",
        "point_predictions",
        "uncovered",
    ]


def test_multioutput_regression_offers_interval_goals(tmp_path: Path) -> None:
    """Several regression outputs use the regression goal menu."""
    _journal(tmp_path)
    _write(
        tmp_path / "scratch" / "data_analysis" / "extras.json",
        _targets(("load", "regression"), ("temp", "regression")),
    )
    payload = frame_show(tmp_path)
    assert _question(payload, "prediction_goal")["candidates"] == [
        "intervals",
        "point_predictions",
        "uncovered",
    ]


def test_multioutput_regression_translates_the_target_list(tmp_path: Path) -> None:
    """A locked multi-output problem exposes every target column."""
    _journal(tmp_path, **_locked_iid())
    _write(
        tmp_path / "scratch" / "data_analysis" / "extras.json",
        _targets(("load", "regression"), ("temp", "regression")),
    )
    payload = frame_show(tmp_path)
    assert payload["action"] == "proceed"
    assert payload["translation"]["task"] == "multioutput-regression"
    assert payload["translation"]["targets"] == ["load", "temp"]


def test_multioutput_classification_is_uncovered(tmp_path: Path) -> None:
    """Several classification outputs are not a supported joint task."""
    _journal(tmp_path)
    _write(
        tmp_path / "scratch" / "data_analysis" / "extras.json",
        _targets(("label_a", "classification"), ("label_b", "classification")),
    )
    payload = frame_show(tmp_path)
    assert payload["reason"] == "uncovered"
    assert payload["context"] == {
        "task": "multioutput-classification",
        "targets": ["label_a", "label_b"],
    }


def test_mixed_targets_are_uncovered(tmp_path: Path) -> None:
    """A mix of regression and classification outputs is not modeled jointly."""
    _journal(tmp_path)
    _write(
        tmp_path / "scratch" / "data_analysis" / "extras.json",
        _targets(("amount", "regression"), ("label", "classification")),
    )
    payload = frame_show(tmp_path)
    assert payload["reason"] == "uncovered"
    assert payload["context"] == {
        "task": "mixed",
        "targets": ["amount", "label"],
    }


@pytest.mark.parametrize(
    ("goal", "expected"),
    [
        ("probabilities", ["proper_score", "ranking", "imposed"]),
        ("point_labels", ["thresholded", "ranking", "imposed"]),
        ("intervals", ["proper_score", "imposed"]),
    ],
)
def test_metric_role_candidates_follow_the_goal(
    tmp_path: Path, goal: str, expected: list[str]
) -> None:
    """The metric-role menu depends on the locked prediction goal."""
    _journal(
        tmp_path,
        **{
            "Prediction goal": goal,
            "Deployment": "iid",
            "Known at predict": "n/a",
        },
    )
    payload = frame_show(tmp_path)
    assert "metric_role" in payload["missing"]
    assert _question(payload, "metric_role")["candidates"] == expected


def test_uncovered_goal_metric_menu_is_the_full_list() -> None:
    """A goal outside the four named ones gets every metric role."""
    from skore_skills.frame import _metric_candidates

    assert _metric_candidates("uncovered") == [
        "imposed",
        "proper_score",
        "ranking",
        "thresholded",
        "point_error",
    ]


def test_probability_baseline_includes_logistic(tmp_path: Path) -> None:
    """Probabilities add a logistic baseline to the menu."""
    _journal(
        tmp_path,
        **{
            "Prediction goal": "probabilities",
            "Deployment": "iid",
            "Known at predict": "n/a",
            "Metric role": "proper_score",
            "Metric": "log loss",
        },
    )
    payload = frame_show(tmp_path)
    assert "baseline" in payload["missing"]
    assert _question(payload, "baseline")["candidates"] == [
        "logistic",
        "production",
        "dummy",
    ]


def test_blank_horizon_segment_stays_missing(tmp_path: Path) -> None:
    """A trailing comma leaves an empty horizon entry, which is asked again."""
    _journal(
        tmp_path,
        **{
            "Prediction goal": "point_predictions",
            "Deployment": "time",
            "Horizon": "1 hour,",
        },
    )
    payload = frame_show(tmp_path)
    assert "horizon" in payload["missing"]


def test_unparsable_horizon_stays_missing(tmp_path: Path) -> None:
    """A horizon that is not a quantity is asked again."""
    _journal(
        tmp_path,
        **{
            "Prediction goal": "point_predictions",
            "Deployment": "time",
            "Horizon": "soon",
        },
    )
    payload = frame_show(tmp_path)
    assert "horizon" in payload["missing"]
    assert "candidates" not in _question(payload, "horizon")


def test_partial_uncovered_block_uses_the_fallback(tmp_path: Path) -> None:
    """An uncovered goal with a blank metric cites the fallback note."""
    _journal(tmp_path, **{"Prediction goal": "uncovered"})
    payload = frame_show(tmp_path)
    assert payload["missing"] == ["metric", "baseline_note"]
    assert _question(payload, "metric")["reference"] == "references/fallback.md"


def test_frame_clear_metric_reopens_only_that_cell(tmp_path: Path) -> None:
    """Clearing the metric blanks that cell and leaves the rest locked open."""
    from datetime import date

    from skore_skills.frame import frame_clear

    _journal(tmp_path, **_locked_iid())
    original = (tmp_path / "journal" / "JOURNAL.md").read_text(encoding="utf-8")
    payload = frame_clear(tmp_path, "metric", today=date(2026, 9, 27))

    assert payload["blanked"] == ["metric"]
    assert payload["revised_on"] == "2026-09-27"
    rows = frame_show(tmp_path)
    assert rows["reason"] == "missing_keys"
    assert rows["missing"] == ["metric"]
    text = (tmp_path / "journal" / "JOURNAL.md").read_text(encoding="utf-8")
    assert "## History" in text
    assert "intervals" not in text
    assert original != text


def test_frame_clear_goal_blanks_metric_dependents(tmp_path: Path) -> None:
    """A prediction-goal reopen also clears the metric role and metric."""
    from skore_skills.frame import frame_clear

    _journal(tmp_path, **_locked_iid())
    payload = frame_clear(tmp_path, "prediction_goal")

    assert payload["blanked"] == ["prediction_goal", "metric_role", "metric"]
    assert payload["status"] == "draft"
    shown = frame_show(tmp_path)
    assert shown["missing"] == ["prediction_goal", "metric_role", "metric"]


def test_frame_clear_group_mean_baseline_follows_known_at_predict(
    tmp_path: Path,
) -> None:
    """A group-mean baseline is cleared with the known-at-predict cell."""
    from skore_skills.frame import _raw_rows, frame_clear

    _journal(
        tmp_path,
        **_locked_iid(
            **{
                "Known at predict": "store_id",
                "Baseline": "group_mean",
                "Baseline note": "store_id",
            }
        ),
    )
    payload = frame_clear(tmp_path, "known_at_predict")

    assert payload["blanked"] == ["known_at_predict", "baseline", "baseline_note"]
    rows = _raw_rows(tmp_path)
    assert rows["deployment"] == "iid"
    assert rows["baseline"] == ""


def test_frame_clear_keeps_a_non_group_baseline(tmp_path: Path) -> None:
    """Known-at-predict does not clear a baseline that is not group_mean."""
    from skore_skills.frame import frame_clear

    _journal(tmp_path, **_locked_iid(**{"Known at predict": "none"}))
    payload = frame_clear(tmp_path, "known_at_predict")

    assert payload["blanked"] == ["known_at_predict"]


def test_frame_clear_deployment_blanks_time_and_group_cells(tmp_path: Path) -> None:
    """A deployment reopen clears horizon, gap, time role, and generalize-to."""
    from skore_skills.frame import frame_clear

    _journal(tmp_path, **_locked_iid())
    payload = frame_clear(tmp_path, "deployment")

    assert payload["blanked"] == [
        "deployment",
        "horizon",
        "gap",
        "time_role",
        "generalize_to",
    ]


def test_frame_clear_metric_role_blanks_the_metric(tmp_path: Path) -> None:
    """A metric-role reopen also clears the metric."""
    from skore_skills.frame import frame_clear

    _journal(tmp_path, **_locked_iid())
    payload = frame_clear(tmp_path, "metric_role")

    assert payload["blanked"] == ["metric_role", "metric"]


def test_frame_clear_baseline_blanks_its_note(tmp_path: Path) -> None:
    """A baseline reopen also clears the baseline note."""
    from skore_skills.frame import frame_clear

    _journal(tmp_path, **_locked_iid())
    payload = frame_clear(tmp_path, "baseline")

    assert payload["blanked"] == ["baseline", "baseline_note"]


def test_frame_clear_ignores_rows_that_are_not_pairs(tmp_path: Path) -> None:
    """A pipe row that is not a label/value pair is left in place."""
    from skore_skills.frame import frame_clear

    _journal(tmp_path, **_locked_iid())
    path = tmp_path / "journal" / "JOURNAL.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("## History", "| leftover note |\n| a | b | c |\n\n## History"),
        encoding="utf-8",
    )

    payload = frame_clear(tmp_path, "metric")
    cleared = path.read_text(encoding="utf-8")

    assert payload["blanked"] == ["metric"]
    assert "| leftover note |" in cleared
    assert "| a | b | c |" in cleared


def test_frame_clear_rejects_a_table_missing_a_dependent(tmp_path: Path) -> None:
    """Clearing a cell fails when a dependent row is absent, and does not write."""
    from skore_skills.frame import frame_clear

    path = tmp_path / "journal" / "JOURNAL.md"
    _write(
        path,
        "\n".join(
            [
                "# JOURNAL",
                "",
                "## Modeling decisions",
                "",
                "| Variable | Value |",
                "|---|---|",
                "| Status | locked |",
                "| Revised on | n/a |",
                "| Prediction goal | point_predictions |",
                "",
                "## History",
                "",
            ]
        ),
    )
    before = path.read_text(encoding="utf-8")

    with pytest.raises(ValueError, match="missing metric_role, metric"):
        frame_clear(tmp_path, "prediction_goal")

    assert path.read_text(encoding="utf-8") == before


def test_section_span_requires_the_modeling_block() -> None:
    """A journal without the modeling section cannot be rewritten."""
    from skore_skills.frame import _section_span

    with pytest.raises(ValueError, match="modeling decisions section is missing"):
        _section_span("# JOURNAL\n")


def test_frame_clear_cli_rejects_unknown_and_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unknown keys and empty cells are usage errors and do not write."""
    monkeypatch.chdir(tmp_path)
    missing = CliRunner().invoke(cli, ["frame", "clear", "--cell", "metric"])
    assert missing.exit_code != 0
    assert "journal is missing" in missing.output

    _journal(tmp_path, **_locked_iid(**{"Horizon": "n/a"}))
    before = (tmp_path / "journal" / "JOURNAL.md").read_text(encoding="utf-8")
    unknown = CliRunner().invoke(cli, ["frame", "clear", "--cell", "splitter"])
    empty = CliRunner().invoke(cli, ["frame", "clear", "--cell", "horizon"])
    assert unknown.exit_code != 0
    assert "unknown framing cell" in unknown.output
    assert empty.exit_code != 0
    assert "horizon is empty" in empty.output
    assert (tmp_path / "journal" / "JOURNAL.md").read_text(encoding="utf-8") == before
    bare = CliRunner().invoke(cli, ["frame", "clear"])
    assert bare.exit_code != 0


def test_frame_fill_cli_writes_na_and_rejects_a_missing_journal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The fill command prints JSON, and a missing journal is a usage error."""
    monkeypatch.chdir(tmp_path)
    missing = CliRunner().invoke(cli, ["frame", "fill"])
    assert missing.exit_code != 0
    assert "journal is missing" in missing.output

    _journal(
        tmp_path,
        **_locked_iid(
            Status="draft",
            Horizon="",
            Gap="",
            **{"Time role": "covariate", "Generalize to": "store_id"},
        ),
    )
    filled = CliRunner().invoke(cli, ["frame", "fill"])
    assert filled.exit_code == 0, filled.output
    payload = json.loads(filled.output)
    assert payload["action"] == "filled"
    assert payload["filled"] == ["horizon", "gap", "time_role", "generalize_to"]
    shown = json.loads(CliRunner().invoke(cli, ["frame", "show"]).output)
    assert shown["reason"] == "set"
    assert "fill_na" not in shown
