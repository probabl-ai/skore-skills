# SkrubLearner + skore.evaluate — the interop pattern

*Workflow pattern (durable across library versions). For per-version
signatures of `skore.evaluate`, `Project`, the report classes, or
the `SkrubLearner` fit shape, see the workspace's
`scratch/api/<lib>/<version>/` cache populated by `python -m skore_skills api get`
Shape 0/1/2/3.*

`skore.evaluate(...)` is a dispatcher: for this one learner it
returns an `EstimatorReport` or a `CrossValidationReport`. Feeding it a
`SkrubLearner` (the learner returned by `make_learner()` on a skrub
DataOps graph) requires the **env-dict-style** fit shape, not the
sklearn-style `(X, y)`.

This doc spells out both shapes, when each applies, and how the
workspace's `experiments/01_baseline.py` uses the env-dict path.

## Two fit shapes — pick by estimator type

### Sklearn-style — `(X, y)` positional

For any estimator that fits via `estimator.fit(X, y)`:

```python
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
import skore

X, y = make_classification(random_state=42)
report = skore.evaluate(LogisticRegression(), X, y, splitter=0.2)
```

`X` and `y` are passed positionally (or by keyword). A locked
`cv` on a DataOp is reused by omitting `splitter=`. An explicit
`splitter=` overrides that `cv` and drops `split_kwargs`. See
`references/metadata-routing.md`.

### Env-dict-style — `data={"<var>": ...}`

For a `SkrubLearner` (the only common case in this workspace), the
learner's `fit` method takes a **single mapping** keyed by the names
of the `skrub.var(name=...)` declarations in the DataOps graph:

Omit `splitter=`. The locked `cv` is already on `mark_as_X`.
Passing `splitter=` drops `split_kwargs`. An omitted `splitter=`
with no DataOp `cv` is an 80/20 holdout, which is the holdout
lock only. See `evaluate-ml-pipeline/references/metadata-routing.md`.

```python
import skore
from load_forecast.pipeline import build_learner

learner = build_learner()  # binds skrub.var("data_dir")
report = skore.evaluate(
    learner,
    data={"data_dir": "/abs/path/to/data"},
)
```

`X` / `y` and `data` are **mutually exclusive** — pick the form that
matches your estimator. `SkrubLearner` only accepts `data`; calling
`skore.evaluate(skrub_learner, X, y)` raises.

## Why env-dict for SkrubLearner

The DataOps graph carries *named* source variables — `data_dir`,
`history_source`, `predict_grid`, `weather_source` — that get bound
at fit time. A sklearn-style `(X, y)` call only binds two unnamed
slots; it can't express "here's the path to the data directory, the
graph derives X and y from there". The env-dict is the natural
shape for source-bound variables.

The keys in `data={...}` must exactly match the `skrub.var(name)`
declarations in the graph. Common shapes:

| Graph root | env-dict |
|---|---|
| `skrub.var("data_dir")` | `data={"data_dir": "/path/to/data"}` |
| `skrub.var("X")`, `skrub.var("y")` | `data={"X": X_array, "y": y_array}` |
| `skrub.var("predict_grid")`, `skrub.var("history_source")` | `data={"predict_grid": grid, "history_source": "/path"}` |

For source-bound vars (paths), pass an absolute path — the same path
used for `learner.skb.preview()` if you set that up. See
`build-ml-pipeline/references/source-binding.md` for the source-vs-
materialized binding decision.

## What `evaluate` returns

The return type depends on `splitter`:

| `splitter` | Report type |
|---|---|
| `float` (e.g. `0.2`) or `None` | `EstimatorReport` — single train/test split |
| A scikit-learn or project cross-validator (`KFold`, `GroupKFold`, custom) | `CrossValidationReport` — multi-fold |
| omitted, DataOp has `mark_as_X(cv=...)` | `CrossValidationReport` — reuses the DataOp `cv` and `split_kwargs` |
| omitted, no DataOp `cv` | `EstimatorReport` — single 80/20 holdout |
| `"prefit"` on a fitted learner; `data` is the test binding only | `EstimatorReport` — the shipped test table |

An explicit `splitter=` always overrides a DataOp `cv` and drops
`split_kwargs`. Omit `splitter=` when the locked `cv` is on the
marker. `splitter="prefit"` is the exception: the learner is
already fitted on the training table, and `data` binds only the
test table. Do not concatenate the two tables, and do not pass
the training table into that call. See
`references/metadata-routing.md`.

```python
fitted = learner.fit({"table": train_df})
report = skore.evaluate(
    fitted,
    data={"table": test_df},
    splitter="prefit",
)
```

Confirm the exact dispatch rules via `python -m skore_skills api get`
(`inspect.signature(skore.evaluate)` + the docstring) against the
installed skore version — the dispatch table can evolve.

## Custom metrics on a SkrubLearner

A comparison metric that is not a skore default attaches with
`.skb.with_scoring(...)` before `.skb.make_learner()`, whether
or not it needs row metadata. Row-aligned kwargs such as
per-row sample weights are DataOps aligned with the marked X
rows. They are not CV `split_kwargs`. See
`references/custom-metrics.md`.

After `skore.evaluate`, the attached name is a row in
`report.metrics.summarize().frame()`.

## Persisting to the Project store

Every report goes under a **stable key** in the workspace's
`skore.Project` so future runs can read it back (the
`audit-ml-pipeline` skill renders each report to a markdown
digest, and `review-ml-experiment` reads that digest to write idea
candidates).

The Project init form depends on the workspace's `skore mode:`
decision (`status.policy.skore_mode`; gate owned by
`evaluate-ml-pipeline` § "G-SKORE-MODE"). Three forms; pick the one
matching the workspace:

```python
# local mode
project = skore.Project(
    name="load-forecast",
    mode="local",
    workspace=str(PROJECT_ROOT / "reports"),
)
project.put("01_baseline", report)
```

```python
# hub mode
from skore import login
login(mode="hub")  # interactive on first run; cached after
project = skore.Project(
    name="load-forecast",
    mode="hub",
    workspace="<hub-workspace>",  # the Skore Hub org/team identifier
)
project.put("01_baseline", report)
```

```python
# mlflow mode  (no login — auth is the MLflow server's concern)
project = skore.Project(
    name="load-forecast",            # MLflow experiment name
    mode="mlflow",
    tracking_uri="http://127.0.0.1:5000",  # recorded at G-SKORE-MODE
)
project.put("01_baseline", report)   # key = MLflow run name
```

- **Key convention**: file stem of the experiment script. Re-using
  the key in a later run overwrites the previous report — fork into
  a new experiment file if you want both. (In mlflow mode the key
  is the run name under the experiment.)
- **`workspace=`** — required by local and hub modes, with a
  different meaning each: local takes an **on-disk directory**
  (`str(PROJECT_ROOT / "reports")`, created on first `put`), hub
  takes the **Skore Hub org/team identifier** (`workspace="<hub-workspace>"`).
  **Not** a valid kwarg in mlflow mode.
- **mlflow-mode `tracking_uri=`** — the MLflow tracking server URI
  (HTTP(S) server, `sqlite:///…`, or `file:./mlruns` backend).
  mlflow-only kwarg; no `login()`. `skore[mlflow]` extra required.
  `project.delete(...)` is supported for mlflow-mode projects (it
  removes the matching experiment; raises `LookupError` if none
  exists at the `tracking_uri`).
- **`name=`** — short, stable, per-workspace name, used directly as
  the bare project name in **all** modes (mlflow uses it as the
  experiment name). Set once at project bootstrap inside each
  experiment script's `skore.Project(...)` call (the agent reads
  the value from `experiments/01_baseline.py` when needed; there is
  no auto-discovery script).

## Reading back later

The skore Project keys reports by an internal id (a long hash), not by
the user-facing string key. To retrieve, `summarize()` first to get
the id:

```python
import skore

# Project init form follows the workspace's `skore mode:` decision.
# Local-mode form shown here; for hub mode see the previous section.
project = skore.Project(
    name="load-forecast",
    mode="local",
    workspace=str(PROJECT_ROOT / "reports"),
)
frame = project.summarize().frame()
id_ = frame.index[frame["key"] == "01_baseline"][0]
report = project.get(id_)
report.metrics.summarize().frame()  # task-appropriate headline metrics
report.checks.summarize().frame()    # automated checks (passed / issue / tip)
```

`project.summarize()` returns a display. `.frame()` is the pandas
DataFrame, indexed by id, with columns: `key`, `date`, `learner`,
`ml_task`, `report_type`, `dataset` (hash), plus the per-metric
`<metric>_mean` columns. The lookup filters `key` and reads that
index. The exact columns evolve with skore; see
`python -m skore_skills api get` § skore.

## Worked example — `experiments/01_baseline.py`

This is the actual experiment script from the workspace:

```python
# %% [markdown]
# # Experiment 01 — Baseline (t+12 load forecast)

# %%
import skore

from load_forecast import PROJECT_ROOT
from load_forecast.pipeline import build_learner

# %% [markdown]
# ## Paths

# %%
DATA_DIR = PROJECT_ROOT / "data"

# %% [markdown]
# ## Project

# %%
project = skore.Project(
    name="load-forecast",
    mode="local",
    workspace=str(PROJECT_ROOT / "reports"),
)

# %% [markdown]
# ## Method
#
# Unfitted learner. After fitting, the same diagram reflects a
# fitted fold.

# %% [markdown]
# ## Learner

# %%
learner = build_learner(data_dir_preview=DATA_DIR)
learner

# %% [markdown]
# ## Evaluate

# %%
report = skore.evaluate(
    learner,
    data={"data_dir": str(DATA_DIR)},
)
# A custom check the user asked for is added here, before summarize.
report.checks.summarize()

# %% [markdown]
# ## Persist

# %%
project.put("01_baseline", report)
report
```

The agent does not run that file. Copy `templates/materialize.py`
to `scratch/results/01_baseline/materialize.py`, put the same
`skore.evaluate` / `checks.summarize()` / `project.put` in the
`<CALL>` block, and run that file once. The tail writes
`report.html`, `report.txt`, `checks.html`, `metrics.html`,
`id.txt`, and the Method files (`pipeline.svg` and the DataOp
report `pipeline/`, from `eval=False`). Write `locator.txt`
from `id.txt`. When
notebooks are on, `notebook fill` the experiment with empty
outputs. Do not `notebook convert` it.

Note the clean separation:

- **`data_dir_preview=DATA_DIR`** on `build_learner()` makes
  `learner.skb.preview()` work interactively; it does **not** affect
  what `evaluate` actually fits on.
- **`data={"data_dir": str(DATA_DIR)}`** is what `evaluate` uses to
  bind the source var at fit/CV time.
- **No `splitter=`.** The locked `cv` is already on the learner.
  See `evaluate-ml-pipeline/references/metadata-routing.md`.
- **No agent-only `print` calls or HTML writes** — inspection
  and the HTML / locator files are the agent's scratch problem
  (`scratch/results/<stem>/materialize.py`; see
  `python -m skore_skills api get` § "`scratch/` conventions"),
  not the experiment script. `report.checks.summarize()` runs
  before `project.put` so the stored report holds the check
  results. The bare `report` line after `put` is jupytext
  display, not a debug print.

## When `evaluate` is too coarse — escalate

If the default `evaluate(...)` dispatch doesn't fit (you need
explicit `train_data=` / `test_data=` on `EstimatorReport` for
this one learner), construct that report class directly.
Look up the signatures via `python -m skore_skills api get` against the installed skore
version — the kwargs differ between `EstimatorReport` (uses
`train_data` / `test_data`) and `CrossValidationReport` (uses
`splitter`).

## Companion references

- `build-ml-pipeline/references/layer_examples.md` — the 3-layer
  DataOps pattern that produces the `SkrubLearner` consumed here.
- `build-ml-pipeline/references/source-binding.md` — when to use
  source-bound vars vs materialized `(X, y)` bindings.
- `evaluate-ml-pipeline` — the call, the locator, and the close.
  CV wiring is `references/metadata-routing.md`.
- `review-ml-experiment` — reads the audit digest at
  `scratch/audit/<stem>/audit.md` (produced by `audit-ml-pipeline`)
  and writes one idea file per `issue` / `tip` line.
