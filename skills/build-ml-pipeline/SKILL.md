---
name: build-ml-pipeline
description: >
  Declare a skrub DataOps graph from the data source to the predictor after
  framing is locked. Stateless steps use `.skb.apply_func`. Stateful steps use
  `.skb.apply`. After the graph exists, attach the locked splitter and any
  non-default score. No fit, tune, persistence, or `skore.evaluate`.

  TRIGGER when writing or editing any link from data source to predictor
  (loaders, preprocessing, features, composition, the final estimator),
  including a pure-Python function on that path, a step added or reordered, a
  bare `sklearn.Pipeline` as the top-level, or a request to build a pipeline,
  classifier, or regressor.

  HOW TO USE: before the first declarative line and on every structural edit.
  Read the stops and emit Pre-flight before code. Confirm new names with
  `python -m skore_skills api get`.
metadata:
  role: helper
  modelTier: big
---

# Build ML Pipeline

Build in a temporary directory. The directory is deleted at the end of the
turn. Do not treat `experiments/<stem>.py` as durable state, and do not edit
`JOURNAL.md` or a design note.

Declare a skrub DataOps graph, then attach the locked splitter
and any non-default score. Smoke is the last step here. Do not
fit, tune, persist, or call `skore.evaluate`.

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Experiment markdown, design-note Method text, and `#` comments
describe this pipeline. Questions and the checkpoint use the
same data-science language: not skill ids, `G-*` names, or the
wrapper CLI. `<!-- results-embed: … -->` is a site marker.
Authoring hints stay in this skill.

**X marker** is `.skb.mark_as_X()`. **Predict grid** is the rows
to score. **Cross-row step** reads other rows (lag, rolling,
group-agg, side join). **Layers 1 / 2 / 3** are sources, the
grid plus marker, and features after the marker.

## Procedure

1. `python -m skore_skills status`. Pending setup → S0. Then
   `python -m skore_skills design consent --stem <stem>`. JSON
   `action` is authoritative. `ask` / `stop` → do not declare
   ("build it" is not approval). `proceed` continues. Then
   `python -m skore_skills frame show` without `--revise`.
   Anything other than `proceed` loads `frame-ml-problem` and
   stops. A `proceed` whose `translation` is null stops: there
   is no splitter translation.
2. Emit 1–3 sentences before the first write: this is local
   preparation of an unfitted `build_learner`, Method cells, and
   a pipeline snapshot, then smoke. It does not train or run
   full-dataset evaluation. Do not invent a duration. Say it
   once. If approval is pending, preview only.
3. Emit Pre-flight. Tick a box only with evidence from this turn.
4. Declare `build_learner` (Rule 1–3). Sources, features, and
   the estimator first. Then attach `cv` and any non-default
   score from `translation`, still before
   `.skb.make_learner()`. `python -m skore_skills api get` for
   every new symbol. `python -m skore_skills style` after edits.
   Probes go to `scratch/` via the composed-dev Python from
   `env verify`. No inline `python -c`. No warning filters
   unless the user asks.
5. Unfitted snapshot: `references/snapshot.md`.
6. When `experiments/NN_*.py` exists for this stem, load
   `smoke-test-ml-pipeline` only if that skill is installed.
   Missing skill → one line; do not invent the pytest file.
   Then `python -m skore_skills smoke run --stem <stem>`. JSON
   `stop` / `red` / `smoke_missing` → fix the graph here. Do
   not loosen the assertion. Do not evaluate. Do not claim
   pytest is green without this command.
7. On `smoke run` `proceed`, the checkpoint below, then
   `python -m skore_skills evaluate consent --stem <stem>`.
   - `ask` — quote JSON `context` (`question`, `experiment`,
     `smoke`, `persisted_report`) in 2–4 lines: what the answer
     authorizes, the design question, and that this stem has no
     persisted report yet. Then **AskUserQuestion**, Evaluate
     (Recommended) / Modify / Stop, and stop. Do not write
     `skore.evaluate`. **Modify** → edit, then `smoke run`
     again. **Stop** → end.
   - `proceed` — a report already exists. Load
     `evaluate-ml-pipeline` if installed, or return to
     `model-ml-pipeline` when that skill called this one.
   - `stop` — smoke file missing. Do not evaluate.
   If the user answers **Evaluate**, load
   `evaluate-ml-pipeline` when installed. `smoke run`
   `proceed` is not that answer.

### Checkpoint

After `smoke run` `proceed`, before the Evaluate menu. 2–6
sentences: what was declared, that smoke is green, the learner.
Ground them in Method. Do not invent a metric. No locator yet.

Then links. When `site build` ran this turn, say the website
has been updated and paste the `file://` line from that output
verbatim.
Do not name the design-note markdown or `html/<stem>.html`.
Otherwise do not claim the website was updated and do not name
the markdown. Still link
`[experiments/<stem>.py](experiments/<stem>.py)`.

## Entry contracts

Implement the approved design. Do not silently upgrade it.

- **Locked baseline** — the one token in the journal baseline
  cell. `dummy` is `DummyClassifier` / `DummyRegressor` in the
  normal DataOps graph; it checks that the path runs.
  `logistic`, `seasonal_naive`, `group_mean`, and `production`
  are that one comparison model. `api get` the class.
- **EDA-backed** — only Method-cited findings. A missing choice
  stops for a question. A temporal finding is the locked `cv`,
  not a license for three layers, lags, or `AlignXy` unless
  Method names those steps.
- **Backlog / discussion** — Method is the boundary.

On a feature, transform, or leakage question, load
`research-ml-practice` if it is installed and the concern is
not already in scratch. Abstract the problem class. If scratch
already lists `declare` or `measure` rows, do not load research
again and do not write pipeline code. AskUserQuestion
`allow_multiple` on the `declare` rows that do not violate a
stop, and stop. The question's last line is exactly: Select each
one you want. Nothing follows that line. Name each `measure`
row as an open EDA question. `measure` revisits EDA and does not
edit `data_analysis.py`.
The splitter still comes from
`frame show`.
`evaluate` names `evaluate-ml-pipeline`. `confirm` asks the
user. Missing skill → one line.

## Rule 1 — Skrub DataOps is the pipeline entry point

Root at `skrub.var(...)`, not a bare `sklearn.Pipeline`.
`skrub.X` / `skrub.y` are not roots (S4). If the user asks for
`sklearn.Pipeline` or `build_pipeline()`, do not import
`Pipeline`, even as an inner estimator. Redirect to `skrub.var`
and `build_learner` returning `predictions.skb.make_learner()`.
Do not illustrate the refusal with a `Pipeline([...])`
constructor.

```python
import skrub
from sklearn.ensemble import HistGradientBoostingRegressor

from <pkg>.data import TARGET_COL, load_raw


def build_learner(data_dir_preview=None):
    """Return the unfit learner (skrub SkrubLearner)."""
    data_dir = (
        skrub.var("data_dir", value=str(data_dir_preview))
        if data_dir_preview is not None
        else skrub.var("data_dir")
    )
    data = data_dir.skb.apply_func(load_raw)
    X = data.drop(columns=[TARGET_COL]).skb.mark_as_X()
    y = data[TARGET_COL].skb.mark_as_y()
    predictions = X.skb.apply(
        HistGradientBoostingRegressor(random_state=0), y=y
    )
    return predictions.skb.make_learner()
```

`translation.task` `multioutput-regression` predicts every column
in `translation.targets` together. Drop all of them from X. `y`
stays a DataFrame, one column per output:

```python
TARGET_COLS = ["load", "temp"]
X = data.drop(columns=TARGET_COLS).skb.mark_as_X()
y = data[TARGET_COLS].skb.mark_as_y()
predictions = X.skb.apply(
    HistGradientBoostingRegressor(random_state=0), y=y
)
```

Use an estimator that fits a numeric target matrix, such as
`HistGradientBoostingRegressor`, `RandomForestRegressor`, or
`Ridge`. When the chosen estimator fits only one output, wrap it
with `MultiOutputRegressor`. Confirm both symbols with `api get`.
Do not use `MultiOutputClassifier` for this task, and do not leave
a target column in X. One column still uses `TARGET_COL` as above.
Details: `references/common_patterns.md`.

A quick traditional baseline uses `skrub.tabular_pipeline` (or
`TableVectorizer`) plus one task-appropriate estimator. Confirm
both with `api get`. Do not hand-tune columns or search
hyperparameters here. Other shapes:
`references/common_patterns.md`.

## Rule 2 — Mark X early; featurize after

Per-row math and fit-time encoders: marker on the loaded frame.
Any cross-row step: marker upstream of that step. Code for the
three layers, including the loader-baked horizon refusal:
`references/layer_examples.md`. Read it before proposing Layer 2.

`value=` is preview only. Expose `data_dir_preview=None` on
`build_learner`. Do not bake a relative path into `pipeline.py`.

## Splitter and scoring, after the graph

Read `translation` from the `frame show` that returned
`proceed`. Attach on the existing X marker, then
`.skb.make_learner()`. skrub requires `cv=` whenever
`split_kwargs` is set. Integer `cv` is not a splitter. Evaluate
omits `splitter=` so skore reuses this `cv`
(`evaluate-ml-pipeline/references/metadata-routing.md`).

That `cv` copies the locked deployment: a scored fit contains
only rows that deployment would already have seen. The shapes
below are the usual ones. When the deployment is a different
structure, open `references/custom-splitter.md` and write
`split` for that setting.

- `scheme` `date_time` — open the time series section of
  `references/custom-splitter.md`. `cv=` is the project-local
  class that section describes. Build one of those splitters per
  entry in `translation.horizons`. Each one is one predictor.
  `split_kwargs` carries the timestamp values. The timestamp
  column is the one the EDA or the text shipped with the data
  already names. Ask which column holds the timestamps only when
  those sources do not name one. `time_role` `covariate` keeps
  that column in the features. `sort_key` drops it from the
  features and still passes it in `split_kwargs`.
- `splitter` `GroupKFold` — `cv=GroupKFold(n_splits=<folds>)`
  and `split_kwargs={"groups": data["<translation.groups>"]}`.
- `splitter` `KFold` — `cv=KFold(n_splits=<folds>)` and empty
  `split_kwargs`.
- `splitter` `prefit` — the data already has a training table
  and a test table. No `cv`. The graph loads the training table
  only. Do not add the test table as a second source, and do not
  concatenate the two files. Both tables share the schema the
  loader expects, including the target. The experiment binds the
  test table later. Do not call `train_test_split`.
- Holdout (`report` `EstimatorReport` and `splitter` null) or
  `translation` null — no `cv`. This holdout is one split drawn
  from a single table. It is not the shipped train/test pair.

Scoring uses `translation.metric`. For
`multioutput-regression`, skore already shows each output of MSE,
RMSE, MAE, and R² (`multioutput="raw_values"`). The locked
comparison is still one number, so attach `.skb.with_scoring(...)`
for that name with an explicit aggregation: `uniform_average`
unless the user named `variance_weighted` or a weight per output.
That aggregate is the headline. Leave the per-output metrics in
the report. For any other task, if the name is one skore already
reports (regression: MSE, RMSE, MAE, R²; binary: accuracy,
precision, recall, F1, ROC-AUC; multiclass: macro and micro
variants; multilabel: per-label and averages), do not attach a
scorer. Otherwise `.skb.with_scoring(...)` in this same late step.
The callable shape is `evaluate-ml-pipeline/references/custom-metrics.md`.
Do not pass `scoring=` to `skore.evaluate`.

Do not write `skore.evaluate(...)` here. Do not call
`train_test_split` from pipeline code.

## Rule 3 — Attach: stateless function, stateful estimator

- `.skb.apply_func(fn)` — output depends only on the current
  row and constants.
- `.skb.apply(estimator)` — learns on training, reapplies on
  test.
- `skrub.deferred` — rare; only when combining several DataOps
  and no skrub joiner fits. Default is `apply_func`.
  Details: `references/source-binding.md`.

A custom class is the mixin, then `BaseEstimator`. The mixin
is the first base. That order matters: `BaseEstimator` first
hides the mixin, because `BaseEstimator.__sklearn_tags__` is
resolved before it and does not call through. A transformer is
`TransformerMixin, BaseEstimator`. A predictor is
`RegressorMixin, BaseEstimator` or
`ClassifierMixin, BaseEstimator`. `BaseEstimator` alone has no
`score`, so skrub never exposes `SkrubLearner.score` and a
`with_scoring` name never appears in `summarize()`.
Details: `references/common_patterns.md`.

Would the output change on the training subset versus the whole
frame? Yes → `.skb.apply`. Means, medians, quantiles,
vocabularies, target encoding, TF-IDF: stateful.

```
STOP — target encoding / apply_func. When the user asks for
`def target_encode` + `.skb.apply_func`: refuse. Do not paste
the leaky function body and then the fix. Propose sklearn
TargetEncoder (or TransformerMixin, then BaseEstimator) via
`.skb.apply`. Name `api get` for the signature.
```

## Reproducibility

`done` History rows stay runnable. Details:
`references/reproducibility_mechanics.md`.

- **Option 1** — a default-preserving flag on the existing
  function. Small append. The default keeps prior callers
  unchanged (`include_calendar_features: bool = False`).
- **Option 2** — a new function called only from the new
  experiment.
- **Option 3** — branch the module. Last resort.

Three or more flags, or a flag that changes an existing
caller's default → Option 2, or stop. After the change, pytest
all of `tests/smoke/`.

## Stops

### S0. Setup still pending

`status` first. If `status.setup.pending` is non-empty and
`status.skills.setup-ml-project` is true, load
`setup-ml-project` and stop. Do not start this skill. When it
returns, continue. Do not load it again on this turn. If that
skill is not installed, name the pending pieces in one line and
stop. Do not invent `git init`, scaffold, or `env init`. If
`status.setup.env` or `status.setup.workspace` is `declined`,
stop in one line. A declined `git` or `editable` is not asked
again; continue. Missing design: `design consent`; `ask` /
`stop` stay here. Missing data contract: explain and stop.

### S0b. Modeling decisions are not locked

- **Rule:** `status.modeling_decisions` must be `locked`, and
  `python -m skore_skills frame show` must return `proceed` with
  a non-null `translation`, before any declaration.
- **Recovery:** load `frame-ml-problem` when installed. A null
  `translation` stops with no pipeline. Do not invent the table.

### S1. Missing dependency

`import skrub` / `sklearn` failure, or a DataOp HTML stub, loads
`add-python-package` for `skrub` and `scikit-learn`. Do not
`env add` here. Do not substitute `sklearn.Pipeline`.

### S2. Symbol from memory is forbidden

Every new skrub, sklearn, or skore name comes from `api get` or
a matching cache read this turn.

### S4. `skrub.X` / `skrub.y` are not graph roots

Root on `skrub.var("<source>", value=preview)`. An existing
`skrub.X` graph: show the alternative and ask. Do not
auto-rewrite. Catalogue: `references/source-binding.md`.

```
Refuse: skrub.X / skrub.y are not graph roots (S4).
They bake the marker at the source and defeat Layer 1.

Alternative (refactor — ask before rewriting):
  data = skrub.var("data_dir", value=preview).skb.apply_func(load_raw)
  X = data.drop(columns=[TARGET_COL]).skb.mark_as_X()
  y = data[TARGET_COL].skb.mark_as_y()
```

### S5. Late `mark_as_X` when any feature is cross-row

The marker sits upstream of every cross-row step. Symptom:
`len(predictions) != n_predict_grid_rows`, `feature_steps=[]`,
or a wrapper whose job is to filter NaNs the pipeline produced.
Recovery: `references/layer_examples.md`. Do not loosen smoke.

A loader that computes `y = col.shift(-H)` and then marks X is
S5 and S6. Horizon lives in Layer 2. Do not invent a wrapper
estimator that shifts, `dropna`s, or filters nulls.

### S6. Layer 1 doesn't know the question

Loaders describe what data exists. Horizon, lag, window, and
task filters belong in Layer 2+. If an external consumer could
not derive the step without knowing the task, push it past
Layer 1.

## Pre-flight — emit before any code

```
Pre-flight (build-ml-pipeline):
- [ ] sklearn, skrub, skore import
      Evidence: scratch/<ts>_check_tier1.py. Not inline python -c.
- [ ] api get for new skrub and sklearn symbols this turn
- [ ] Each skrub.var is a source id, not a baked path
- [ ] mark_as_X placement (loaded frame, or predict grid if cross-row)
- [ ] Layer 1 has no horizon, lag, or task filter
- [ ] cv on mark_as_X matches translation
      (date class | GroupKFold | KFold | no cv on holdout
      | prefit: training table only, test table not joined)
- [ ] Non-default translation.metric uses with_scoring
      before make_learner (n/a for a listed skore default;
      required for a multi-output regression aggregate)
- [ ] data_dir_preview=None; no path literal in pipeline.py
```

Re-emit it with evidence before the final message.

## References

- `references/snapshot.md` — unfitted Method report, experiment
  cells, optional site build.
- `references/layer_examples.md` — three layers. Read before
  proposing Layer 2.
- `references/source-binding.md` — identifier versus materialized
  roots.
- `references/reproducibility_mechanics.md` — Option 1 / 2 / 3.
- `references/common_patterns.md` — tabular shapes with code,
  including a custom predictor (mixin, then `BaseEstimator`).
- `references/custom-splitter.md` — the split copies the locked
  deployment. The time series section is the date splitter when
  `translation.scheme` is `date_time`.
- `evaluate-ml-pipeline/references/metadata-routing.md` — evaluate
  omits `splitter=`.
- `evaluate-ml-pipeline/references/custom-metrics.md` — a score
  that is not a skore default.
