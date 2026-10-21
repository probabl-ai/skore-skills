---
name: smoke-test-ml-pipeline
description: >
  Structural pytest: prediction count must match the predict-grid row count.

  TRIGGER when an approved experiment needs its smoke test, `pytest
  tests/smoke/` fails on row count, the user asks why the smoke test is
  failing, a pipeline edit needs proof, or the experiment script changes
  pipeline shape.

  STOP when `status.setup.pending` is non-empty (load `setup-ml-project`), or
  when there is no approved design or no matching experiment script: explain
  and send the user to setup or stay in `build-ml-pipeline`. A declined git is
  not asked again. "Why is smoke failing?" stays here. This action does not
  cover regression tests or CV interpretation. Do not write `skore.evaluate`.

  HOW TO USE: `status`, read the journal and experiment, write
  `tests/smoke/test_NN_*.py`, then `python -m skore_skills smoke run --stem
  <stem>`. Red JSON means fix the pipeline in `build-ml-pipeline`. Do not
  loosen the assertion.
metadata:
  role: helper
  modelTier: medium
---

# Smoke Test ML Pipeline

Run the smoke test in a temporary directory. A red test does not call
`experiment.run` and does not change the experiment status. Deleting the
directory afterward is success when no report was supposed to be stored.
Do not edit `JOURNAL.md` or a design note.

The minimal pytest that catches the "load → featurize → split"
anti-pattern at iteration time, before it reaches production.

**Deliverable first.** After the pre-flight checklist, the first
user-visible content is the complete test file in a fenced block
(`assert len(predictions) == n_predict_grid_rows`, predict env
with no pre-history buffer, real `data/` source, soft assertion
with the CV-mean hardcoded as a literal, no `skore` import).
Then **run** `python -m skore_skills smoke run --stem
<NN>_<short_name>`. Treat JSON `action` as authoritative. Do not
stop at a plan or leave
the file only in a thinking channel. Never tell the user or CI
to run pytest later. Name that exact
`smoke run` command. A
no-tools harness still gets a **complete** test file (use
assumed journal / experiment / package facts; no `<FILL_…>`)
and that invocation. Saying this turn cannot execute pytest is
fine; instructing the user to run it is not. Do not
AskUserQuestion for evaluate here — that gate belongs to
`build-ml-pipeline` after `smoke run` is `proceed`. After
green, the parent owns the User-facing close (narrative +
links); this skill does not narrate the pipeline.

## Stop conditions — read before anything else

- **Setup still pending.** Run `python -m skore_skills status`
  first. If `status.setup.pending` is non-empty and
  `status.skills.setup-ml-project` is true, load
  `setup-ml-project` and stop. Do not start this skill. When it
  returns, continue. Do not load it again on this turn. If that
  skill is not installed, name the pending pieces in one line
  and stop. Do not invent `git init`, scaffold, or `env init`.
  If `status.setup.env` or `status.setup.workspace` is
  `declined`, stop in one line. A declined `git` or `editable`
  is not asked again; continue.
- **No smoke test without an approved design note + script.** The pairing
  rule is hard: run
  `python -m skore_skills design consent --stem <stem>`.
  `tests/smoke/test_NN_<short_name>.py` exists only when that JSON
  is `proceed` *and*
  `experiments/NN_<short_name>.py` exists with the matching stem.
  `ask` / `stop` → do not write the smoke test.
- **Missing pytest.** If `pytest` is not importable in the project
  env, STOP. Load `add-python-package` for `pytest` on **default**
  (confirm; `env route` maps pytest off `--feature agent`). Do not
  `pip install pytest` or put it on the agent feature (use the composed
  `dev` env, default + agent).
- **Symbol from memory is forbidden.** Any skrub /
  scikit-learn name you write in the smoke test must come from
  `python -m skore_skills api get <dotted>...` or a matching cache
  read **in this turn**. Several symbols go in one call. The smoke
  test is a small file but it imports the predicting-package API
  surface; the same memory-forbidden rule applies.
- **Don't shrink the assertion.** The hard assertion is exact
  row-count equality. Not "approximately equal", not "at least 80%
  of expected rows". A row-count mismatch *is* the failure mode the
  smoke test exists to catch. Loosening the assertion silently
  reintroduces the bug.
- **Don't shrink the expected count either.** The assertion is a
  pair — the `==` *and* the number on its right. Redefining
  `n_predict_grid_rows` down to whatever the pipeline emitted
  ("predict grid minus embargo", "minus the cold-start window") is
  the same defect with the equality left intact. If you believe the
  gap is intended, that is an X-marker question for
  `build-ml-pipeline`: say so and stop. Do not propose a number.
- **A hedge does not license the content.** A conditional offer is
  an offer: "if the 24 rows turn out to be a documented embargo,
  then the right change is …" proposes the forbidden edit. Refusals
  end at the refusal plus the route-back; they do not carry a
  caveat that lands in the same place.
- **Don't synthesize the fixture.** The smoke test reads the real
  `data/` source. Synthetic fixtures look fine but skip the
  loaders that actually break in production.
- **No wrappers, no NaN-handling, no `eval_mode` hacks.** If the
  smoke test only passes after wrapping the predictor or
  conditioning on `eval_mode`, the pipeline is wrong. Go back to
  build (§ Back to build) and fix the X-marker placement.
  Wrappers paper over the failure mode; they don't solve it.
- **The smoke test uses *only* the predicting package's API.**
  For a `SkrubLearner` produced by `build-ml-pipeline` that means
  skrub's `fit` / `predict` / (optionally `score`) plus
  `sklearn.metrics` for any metric the soft assertion uses.
  **Do not import `skore`** (or any other tracking / reporting
  library) in the test file. The smoke test must be runnable in
  any environment that can `import skrub` + `import sklearn` —
  the skore Project is a side artifact, not a test dependency.
  Soft-assertion baselines (CV-mean MAE, etc.) are **hardcoded
  from the design note's Status.headline** with a comment pointing to
  the design note; update by hand when the experiment's headline number
  changes.
- **Don't filter warnings.** No
  `@pytest.mark.filterwarnings(...)`, no
  `warnings.filterwarnings(...)` in the test body, no
  `filterwarnings = [...]` in `pytest.ini` /
  `pyproject.toml` — unless the user explicitly asks. See
  `python -m skore_skills style` § Stop conditions.

## Before execution

After design / script pairing and pytest availability are
confirmed, emit 1–3 natural sentences before the test-file write.
Say that this is a **local real-data smoke computation**: it will
fit the declared learner on a small real-data slice, predict a
disjoint slice with no pre-history buffer, and check exact output
row count plus the optional soft metric. Name
`tests/smoke/test_<stem>.py` and the exact `smoke run` command.

Explain that this slice is intentionally much smaller than
full-dataset cross-validation, but its runtime still depends on
the loader, feature graph, and learner. Do not promise minutes
unless a measured duration is already available, and never
replace real data with synthetic rows to make the estimate
shorter. Emit this preview once, not once per pytest action.
If a mandatory gate is pending, preview the possible test but do
not write or run it. This skill performs no LLM research and no
full evaluation.

## Pre-flight — emit this checklist as visible text before any test code

```
Pre-flight (smoke-test-ml-pipeline):
- [ ] Tier 1 mandatory libs importable: pytest + sklearn + skrub
      (stage libraries per `python -m skore_skills env stack`). **Not skore** —
      see the Stop conditions; the smoke test is intentionally
      portable to any skrub-capable environment
- [ ] API confirmed for skrub / sklearn symbols used in
      the test: <symbols, or "none">
      Evidence: python -m skore_skills api get <dotted>...
                | Read scratch/api/<lib>/<version>/<topic>.md (this turn)
                | Write scratch/api/<lib>/<version>/<topic>.md (this turn)
                | "n/a — test only uses symbols already present in
                  src/<pkg>/ (build_learner / load_training_table / etc.)"
- [ ] `journal/NN_<short_name>.md` read this turn (frozen sections:
      Question, Method) so the test asserts what the experiment claims
- [ ] `experiments/NN_<short_name>.py` skimmed this turn for the env-dict
      keys `build_learner` consumes (`data_dir` / `start` + `end` /
      `raw_frame` / etc.)
- [ ] `src/<pkg>/data.py` skimmed this turn for the loader signature
      (so the predict-env construction matches the loader's expectations)
- [ ] Test category & stem decided: `tests/smoke/test_NN_<short_name>.py`
- [ ] Predict-grid size decided: smallest window that still triggers
      the failure mode (default: a single horizon-length slice; for
      time series, the most recent N steps such that the target is
      *just* observable for assertion)
- [ ] Hard assertion wired: `len(predictions) == n_predict_grid_rows`,
      plus output width (1 for one target; `translation.targets`
      for multi-output regression, including column names)
- [ ] Soft assertion wired (or explicitly skipped): smoke MAE within
      `3 × CV_MEAN_HARDCODED_FROM_PLAN` (or task-appropriate
      analogue). Value is a literal pulled from the matching
      `journal/NN_<short_name>.md` § Status.headline; the test does
      not import `skore` / read the project store at runtime.
- [ ] Pytest run this turn on `tests/smoke/test_NN_<short_name>.py`.
      Red → back to build (§ Back to build). Green (sub-step) →
      return to build for the design HITL.
```

## What the smoke test asserts

Two assertions, two severities:

### Hard — the row-count check

```python
assert len(predictions) == n_predict_grid_rows
```

This is the *structural-correctness* assertion. It is a binary
pass/fail and it is the **whole point** of the smoke test. A
correctly built pipeline (per `build-ml-pipeline`'s X-marker rule)
satisfies this trivially. A pipeline that loads-then-features-
then-splits will fail it because predict-time featurization on the
predict env runs with no pre-history buffer and silently drops
cold-start rows.

`n_predict_grid_rows` is the count of rows the predict env
*claims* to want predictions for — typically the number of
target-time rows in the predict-time grid. If the pipeline's
source binding is a directory of raw files, it's the row count of
the supervised frame derived from the predict env at predict time
(usable via `build_supervised_frame(predict_dir)`).

`len` counts rows. Also assert the output width: 1 for one
target. For multi-output regression, the width and, when
`predict` returns a DataFrame, the column names equal
`translation.targets`. A matrix with the right row count and
the wrong outputs is still a shape failure.

### Soft — the metric-vs-CV gap

```python
smoke_mae = mean_absolute_error(y_true, predictions)
assert smoke_mae < 3 * cv_mae_mean, (
    f"smoke MAE {smoke_mae:.0f} is more than 3× the CV mean "
    f"({cv_mae_mean:.0f}); predictions may be NaN-poisoned even "
    f"though the count matches."
)
```

The metric gap catches the second-order failure mode: the
prediction count is right, but the values are garbage because some
features are NaN at predict time (e.g. an encoder hasn't seen a
new category, a lag is null because the upstream history reference
wasn't wired correctly). The `3×` bound is a starting heuristic;
adjust per task. The smoke window is a single seasonal slice, so
the bound has to be loose enough that a *legitimate* hard-season
window doesn't trip it.

The soft assertion is **opt-out, not opt-in**: skip it only if the
task has no obvious metric-vs-CV comparator (e.g. the smoke fixture
deliberately has no ground truth). If you skip it, leave a comment
on *why* in the test file.

## The diagnostic-by-construction property

The fixture is built specifically to **fail on the buggy shape and
pass on the correct one**. This is the single most important
property of the smoke test; if you take the fixture construction
shortcut and it doesn't have this property, the test is worthless.

Concretely, the predict-time env-dict carries **only the rows we
want predictions for, with no pre-history buffer beyond what
predict-time-known features absolutely require**. Two consequences:

- **Late-`mark_as_X` pipeline**: features are computed inside the
  graph from the predict env's data alone. Backward lags / rolling
  windows / target shifts have NaN at the cold-start rows. The
  pre-marker `drop_nulls` (or the model's NaN intolerance) drops
  those rows. `len(predictions) < n_predict_grid_rows`. **Test
  fails.**
- **Early-`mark_as_X` pipeline**: the marker lands on the
  predict-grid node (Layer 2 of `build-ml-pipeline`'s rule 2);
  history-dependent features take the upstream history DataOp as
  an additional `apply_func` argument. At predict time, the
  history node resolves to the full available history (bound
  from the same source the train env uses), and the join in each
  feature step produces real values for every row in the predict
  grid. `len(predictions) == n_predict_grid_rows`. **Test
  passes.**

The two outcomes are deterministic. The smoke test cannot be
"flaky" — if the row count is off by one, the pipeline is wrong.

For the predict-grid size: **smallest is best**. Use the smallest
predict window that is still an honest predict-time grid. A
single horizon-length slice (e.g. one day for a t+24 model) is
enough to expose the failure; anything larger only hides it
behind volume.

## Fixture construction — `data/` is the source

The fixture **reads from the real `data/` source**, not from a
synthetic generator and not from a checked-in fixture file. The
loaders the experiment uses are the loaders the smoke test must
exercise. Synthetic fixtures defeat the purpose.

Construction depends on the experiment's source binding (read
`experiments/NN_*.py` to find out which env-dict keys
`build_learner` consumes), but the shape is always the same:

1. Identify the predict-grid time bounds (`predict_start`,
   `predict_end`). For time series, the most recent
   horizon-equivalent window of the data.
2. Identify the train env. The cleanest choice is *all data
   strictly before `predict_start - HORIZON`* (embargo equal to
   the forecast horizon). For tabular IID, just exclude the rows
   in the predict grid.
3. Build two env-dicts:
   - `train_env`: whatever shape the experiment uses for its
     fit binding, restricted to data before the embargo.
   - `predict_env`: the predict-grid description, with **no
     additional history padding** (this is the diagnostic
     property; if you pad, the test passes spuriously).
4. Compute `n_predict_grid_rows` independently of the prediction —
   the count comes from the supervised representation of the
   predict env (not from the prediction itself).
5. Compute `y_true` from the supervised representation of the
   predict env (the soft assertion's ground truth).

The fixture **must not write derived files to `data/holdout/`,
`data/train/`, etc.** Those are workspace-level artifacts owned
by the project's setup script(s); the smoke test fixture is
ephemeral. Use `tmp_path` (the pytest-built-in temporary
directory fixture) when the experiment's source binding requires
on-disk inputs.

Three common source-binding shapes — the smoke fixture has to
match whichever the experiment uses:

| Binding shape | Predict env construction | `n_predict_grid_rows` |
|---|---|---|
| **Directory of raw files** — `build_learner` binds a `data_dir`-style var; the loader globs / reads files from it. | Write a tiny temp dir with the time-sliced raw files inside the test (use the `tmp_path` pytest built-in). Bind it as `data_dir`. | The row count of the supervised representation of the predict env (e.g. `len(build_supervised_frame(predict_dir))` in load-forecasting), known a priori from the slice. |
| **Predict-grid + raw-history sources** — the early-mark shape from `build-ml-pipeline` rule 2: `predict_grid` plus `history_source` / `weather_source` / etc. as separate vars. | Build the in-memory `predict_grid` value (a list of timestamps, a panel-key grid, …) and the source identifiers. No file write needed. | `len(predict_grid)`. |
| **Materialized `(X, y)` IID** — `build_learner` binds `X` and `y` directly (or a single `data` env-dict mapping to `{"X": ..., "y": ...}`). | Hold out a small subset of rows from the materialized `X` (and the matching `y`) before fit; `train_env` gets the rest, `predict_env` gets the held-out subset. | `len(predict_subset)`. |

For the second shape (predict-grid + raw-history sources), the
three layers — sources → predict-grid + alignment + `mark_as_X`
→ features after (with history as an upstream reference) — are
described in `build-ml-pipeline` Rule 2, with worked code in
`build-ml-pipeline/references/layer_examples.md`. Read that
reference before constructing the predict env for an early-mark
pipeline.

### IID flat-table problems — what the smoke test still buys you

For pipelines with **no cross-row dependencies** (per-row math,
stateful encoders that learn at fit and apply per-row at
predict, no lags / rolling / joins-with-history), the smoke
test reduces to "fit on the train subset, predict on the
held-out subset, assert `len(predictions) == len(predict_subset)`".

The **diagnostic-by-construction property does not apply** —
there are no cross-row reaches for the test to break, so the
hard assertion will pass on a correctly-built pipeline *and* on
a buggy one. What the smoke test still catches in the IID case:

- Loader bugs that drop or duplicate rows on a smaller input
  than CV used.
- Shape mismatches between `learner.predict(env)`'s output and
  the predict-env row count. `len` on a DataFrame is the row
  count, so also check the output width. One target has width 1.
  Multi-output regression must match `translation.targets` in
  width and column names.
- Accidental NaN-poisoning when an encoder has never seen a
  category present in the predict subset (the soft assertion
  on smoke-MAE-vs-CV-mean catches this; keep it on).

Treat the IID smoke test as a **sanity check**, not a
CV-replacement. The CV-replacement role is what the test
plays for cross-row pipelines, where the diagnostic-by-
construction property is the load-bearing guarantee.

## The standard pytest shape

One test function per smoke test file. The function name mirrors
the experiment stem so pytest output is self-explanatory.

```python
"""Smoke test for `experiments/NN_<short_name>.py`."""

# stdlib + numpy first
import pytest

from <pkg> import PROJECT_ROOT
from <pkg>.pipeline import build_learner
# additional imports per the experiment's binding shape

DATA_DIR = PROJECT_ROOT / "data"


@pytest.fixture
def train_predict_envs(tmp_path):
    """Build a (train_env, predict_env, n_predict_grid_rows, y_true) tuple.

    Diagnostic by construction: predict_env carries only the
    rows we want predictions for, with no pre-history padding.
    """
    # ... per-experiment fixture construction ...
    return train_env, predict_env, n_predict_grid_rows, y_true


def test_NN_<short_name>(train_predict_envs):
    """Predict-time replay must produce one prediction per predict-grid row."""
    train_env, predict_env, n_predict_grid_rows, y_true = train_predict_envs

    learner = build_learner()
    learner.fit(train_env)
    predictions = learner.predict(predict_env)

    # HARD: structural correctness. n_outputs is 1 for one target.
    # Multi-output regression sets n_outputs and target_names from
    # translation.targets.
    n_outputs = 1
    target_names: list[str] = []
    assert len(predictions) == n_predict_grid_rows, (
        f"got {len(predictions)} predictions for "
        f"{n_predict_grid_rows} predict-grid rows — pipeline is "
        f"dropping cold-start rows; check `mark_as_X` placement "
        f"and that history-dependent features reference an "
        f"upstream history node, not a per-slice computation."
    )
    width = predictions.shape[1] if getattr(predictions, "ndim", 1) == 2 else 1
    assert width == n_outputs, (
        f"got {width} outputs, expected {n_outputs}"
    )
    if target_names:
        assert list(predictions.columns) == target_names, list(predictions.columns)

    # SOFT: predictions are not NaN-poisoned.
    from sklearn.metrics import mean_absolute_error
    smoke_mae = mean_absolute_error(y_true, predictions)
    # CV_MAE_MEAN is hardcoded at the top of the file from
    # `journal/NN_<short_name>.md` § Status.headline. The smoke test
    # uses only the predicting package's API (skrub/sklearn) —
    # no skore import, so it runs anywhere skrub does.
    assert smoke_mae < 3 * CV_MAE_MEAN, (
        f"smoke MAE {smoke_mae:.0f} > 3 × CV mean "
        f"({CV_MAE_MEAN:.0f}) — predictions may be NaN-poisoned."
    )
```

`tmp_path` is the pytest built-in for a per-test temporary
directory; use it whenever the experiment's source binding
requires on-disk inputs.

## Failure semantics

A failing smoke test is a **pipeline-shape problem**, not a
metric problem.

- **Hard-assertion failure** (row count) → the pipeline is broken.
  Go back to build (§ Back to build), audit the X-marker placement
  and the history-dependent feature steps. Don't tune the model;
  don't loosen the assertion; don't add a wrapper. Fix the shape.
- **Soft-assertion failure** (metric way off) → the predictions
  exist but are garbage on the smoke window. Most common cause:
  an upstream history node isn't being correctly resolved at
  predict time, so a lag column is silently NaN. Inspect
  `learner.skb.full_report()` and look for nodes whose value at
  predict time doesn't match what fit time saw.
- **Failure blocks `done` status.** `manage-ml-backlog`
  record-outcome refuses to flip an experiment to `done` until
  the matching smoke test passes.   `evaluate-ml-pipeline` also
  STOPs while `smoke run` is `stop` (or the smoke file is missing on a
  history-dependent pipeline).

## Back to build

A pipeline fix belongs to `build-ml-pipeline`. How to get there
depends on who loaded this skill:

- **Sub-step** — `build-ml-pipeline` loaded this skill: return to
  it. Its instructions are still loaded; continue its loop.
- **Direct debug** — this skill was loaded on its own (for example
  "why is smoke failing?"): load `model-ml-pipeline` when
  `status.skills.model-ml-pipeline` is true, and name the stem. It
  resumes the approved design and re-enters build for the fix, on
  the model tier that build declares. Do not load
  `build-ml-pipeline` from here: a sub-step this skill loads runs
  on at most this skill's own tier. Missing `model-ml-pipeline` →
  say in one line that the pipeline needs a fix in build, and stop.

On a direct debug request that only asks *why* smoke is failing,
the diagnosis is the answer; go back to build only when the user
wants the pipeline fixed.

## What this skill does NOT do

- Write the design note or the experiment script. Those are
  `model-ml-pipeline` and `setup-workspace` /
  `build-ml-pipeline`.
- Touch the skore Project. The smoke test does not call
  `project.put` — it's a pre-flight check, not a metric
  artifact. CV metrics come from `evaluate-ml-pipeline`.
- Define what "good metrics" mean. The hard assertion is
  structural; the soft assertion is a sanity bound, not a
  performance target. Performance judgment is the user's, per
  `triage-ml-task`'s rule that the user judges results.
- Ask Evaluate (Recommended) / Modify / Stop. After `smoke run`, return to
  `build-ml-pipeline` (parent) or report pass/fail on a
  direct debug request.

## Run pytest

This is the executable proof. After the test file is written or
updated, run `python -m skore_skills smoke run --stem
<NN>_<short_name>`. It streams pytest on
`tests/smoke/test_NN_<short_name>.py` then prints JSON. Do not
claim green without `action: proceed`. `stop` / `red` → back to
build to modify the pipeline (§ Back to build);
do not start evaluate. `proceed` → return to build for the
design HITL when this skill was loaded as a sub-step.

## Companion skills

- **`build-ml-pipeline`** — parent. Owns the X-marker placement
  rule the smoke test asserts, and the post-green HITL. Smoke
  failure goes back there for a pipeline-shape fix, through
  `model-ml-pipeline` on a direct debug (§ Back to build).
  Pytest is the loop: `smoke run` red → modify pipeline → `smoke run` again.
- **`manage-ml-backlog`** — record-outcome writes `done`. Requires
  the smoke test to pass before an experiment can flip to `done`.
- **`evaluate-ml-pipeline`** — owns CV. Do not load it from here.
- **`python -m skore_skills api get`** — symbol references for
  the predicting-package APIs the smoke test uses. Consult
  before naming any imported function in the test body.
  `python -m skore_skills api get` is **not** a smoke-test dependency — see the
  "no skore import" Stop condition above. **Cache hits first**:
  check `scratch/api/<lib>/<version>/` before WebSearching;
  cache new findings back there (per `python -m skore_skills api get` Shape 0/3).
- **`python -m skore_skills env stack`** — declares pytest as a
  stage library for any workspace using this skill.
- **`python -m skore_skills style`** — **must be invoked** after writing or
  editing `tests/smoke/test_NN_*.py`. Running a manager-specific ruff
  check` directly without invoking this skill silently drops the
  NumPyDoc docstring convention the stack expects: ruff's
  `D`-rules pass on a one-line summary, but only the skill body
  teaches the parameter-shape-in-type-slot and the section
  layout (`Parameters` / `Returns` / `Notes`) the test fixture +
  test function should use.

## Need a package?

When an import is missing, load `add-python-package` if
`status.skills.add-python-package` is true. That skill owns
`env add` and the unmanaged ask. Do not run `env add` here.
If the skill is not installed, name the package and stop.
