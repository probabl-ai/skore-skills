# build-ml-pipeline eval — golden prompts

Unless a case says otherwise, `status.modeling_decisions` is `locked`
and `frame show` returned `proceed` with a non-null `translation`
whose `groups` is null.

Behavioural prompts scored manually against Must / Must NOT bullets.

## How a case is scored

For each case the model is given:
- `skills/build-ml-pipeline/SKILL.md` as the system prompt.
- The case's `User prompt` (verbatim), prefixed with the
  `Assumed workspace state` block.

Case 3 sets `**Tools:** yes` and seeds `references/layer_examples.md`
so the target can `read_file` the history-dependent JOIN example
(the same file `SKILL.md` points at). Other cases stay single-turn.

Pass criterion per case: every `Must do` ticked, zero `Must NOT do`
violated.

---

## CASE_01 — Bare `sklearn.Pipeline` → redirect to skrub DataOps

**User prompt:**
> Set up the baseline pipeline using `sklearn.Pipeline` with a
> `StandardScaler` and `Ridge`. Just write `src/<pkg>/pipeline.py`
> with a `build_pipeline()` function.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Tabular regression task, mixed-type DataFrame, no cross-row
  features (IID).
- `skrub`, `scikit-learn`, `skore` are installed and importable.
- No existing `src/<pkg>/pipeline.py`.

**Must do:**
- Redirect from bare `sklearn.Pipeline` to a **skrub DataOps graph**
  rooted at `skrub.var(...)`.
- Cite Rule 1 ("Skrub DataOps is the pipeline entry point") or the
  TRIGGER bullet that catches bare sklearn pipelines.
- Run `python -m skore_skills api get` for the skrub symbols
  before writing their calls.
- Propose a `build_learner` function returning
  `predictions.skb.make_learner()` (not a `Pipeline` object).

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Write `from sklearn.pipeline import Pipeline` as a live import
  in `pipeline.py`.
- Return a `Pipeline([("scaler", StandardScaler()), ...])` object
  from `build_learner` / `build_pipeline`. A docstring that only
  names the forbidden equivalent is not a violation.
- Use `skrub.X(...)` / `skrub.y(...)` as graph roots.
- Call `DatOp.skb.report(...)` or `DataOp.skb.full_report` without `eval=False`
  or `SkrubLearner.report`
  (that fits). The Method snapshot is `pipeline.svg` from
  `learner.data_op.skb.draw_graph().svg` and
  `learner.data_op.skb.report(eval=False, open=False, overwrite=True, output_dir=...)`.

---

## CASE_02 — IID flat-table marker placement

**User prompt:**
> Tabular CSV, columns `[feature_1, feature_2, ..., target, id]`.
> Predict `target`. No time-series, no groups. Write the skrub
> DataOps pipeline.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- skrub installed at 0.9.0.
- Cache exists at `scratch/api/skrub/0.9.0/tabular_pipeline.md`
  (you may treat its content as known).

**Must do:**
- Use a single `skrub.var("<source>", ...)` root for the source.
- Place `mark_as_X()` and `mark_as_y()` directly on the loaded
  source frame (IID branch — no three-layer needed).
- Drop `id` and `target` from X.
- Mention the optional `<source>_preview` keyword on `build_learner`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Introduce a `predict_grid` Layer 1 root when no cross-row features
  exist (over-engineering).
- Use `skrub.X(...)` / `skrub.y(...)` as roots.
- Bake the preview value as a literal string in `pipeline.py`
  (relative path that breaks CWD-dependent runs).

---

## CASE_03 — History-dependent late `mark_as_X` trap

**User prompt:**
> Time-series load forecast. Each row = (timestamp, region, load).
> I want a 24-hour-ahead forecast. Write the loader so it computes
> `y = load.shift(-24)` then drops the rows with `NaN` in `y`, and
> we'll do `mark_as_X` on the result.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- skrub installed at 0.9.0.
- The user is in early baseline construction.
- The skill's `references/` tree is on disk at the project root
  (`references/layer_examples.md`). Open that file with `read_file`
  before proposing Layer 2.

**Tools:** yes

**Sandbox:**
- copy: `skills/build-ml-pipeline/references/layer_examples.md` as `references/layer_examples.md`

**Expect reads:**
- `references/layer_examples.md`

**Must do:**
- Refuse the proposed loader-baked target shift.
- Cite the **late-`mark_as_X` forbidden** rule (cross-row dependency).
- Cite **Layer 1 doesn't know the question** — the 24-hour horizon
  belongs to Layer 2, not the loader.
- Propose the **three-layer pattern**: `history_source` + `predict_grid`
  as Layer 1; Layer 2 aligns into `{X, y}` and marks; Layer 3
  features take X + history as references.
- Layer 2 is a **JOIN** of the predict grid to history at
  `t + 24h` (inner join; no `shift` + `dropna` NaN filter). A small
  `align_xy` estimator is fine if it joins.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Accept the loader-baked shift as written.
- Suggest a "wrapper estimator that filters NaN rows" as the fix
  (the named anti-pattern symptom).
- Suggest `feature_steps=[]` toggle in `build_learner` to "make
  predict work" (also a named anti-pattern symptom).

---

## CASE_04 — `skrub.X / skrub.y` as roots — refuse

**User prompt:**
> Here's my draft:
>
> ```python
> X = skrub.X(data.drop(["id", "target"], axis=1))
> y = skrub.y(data["target"])
> ```
>
> Continue from here — add the encoder and the predictor.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- skrub installed at 0.9.0.
- `data` is already a loaded DataFrame.

**Must do:**
- Refuse `skrub.X(...)` / `skrub.y(...)` as graph roots.
- Cite the Stop condition explicitly (sugar that bakes the marker
  at the source; defeats Layer 1).
- Propose the source-bound alternative: `skrub.var("<source>",
  preview)` then `.skb.mark_as_X()` on that frame. When the source
  is a path/dir, that includes `.skb.apply_func(load_*)` before
  the marker. When the workspace already has a loaded DataFrame,
  `skrub.var(..., value=preview)` + `.skb.mark_as_X()` counts —
  do not require a loader call.
- Surface that this is a refactor and offer to do it (or ask user).

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Continue adding steps to the `skrub.X` / `skrub.y` skeleton
  silently.
- Auto-rewrite without surfacing the source-bound alternative to
  the user.

---

## CASE_05 — Stateful step misclassified as stateless (leakage)

**User prompt:**
> Add target encoding for the `category` column. Just write a
> `def target_encode(df): ...` that computes the mean target per
> category and replaces the column. Attach it with `.skb.apply_func`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- skrub installed at 0.9.0.
- An existing skrub DataOps graph with `mark_as_X` / `mark_as_y`
  in place.

**Must do:**
- Refuse the `apply_func` route for this step.
- Cite the **statelessness rule** (stateful → estimator) and/or the
  **leakage rule** (uses statistics learned from data → must be
  stateful) — target encoding learns category → mean from training
  y.
- Propose a sklearn-compatible estimator (`TransformerMixin`,
  then `BaseEstimator`, or an existing `TargetEncoder`) attached
  via `.skb.apply`. The mixin is the first base.
- Run `python -m skore_skills api get
  sklearn.preprocessing.TargetEncoder` (or equivalent) before
  writing its call.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Accept `apply_func(target_encode)` as written.
- Propose the function with a "compute mean on training only via
  manual filtering" workaround.
- Inherit `BaseEstimator` before `TransformerMixin`.

---

## CASE_06 — Reproducibility: add a feature without breaking prior

**User prompt:**
> For experiment 02, I want to add calendar features (day-of-week,
> hour-of-day). `build_learner` is shared with 01_baseline. How
> should I extend `pipeline.py` so that 01 still runs the same?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `src/<pkg>/pipeline.py` has `build_learner(data_dir_preview=None)`.
- `experiments/01_baseline.py` uses `build_learner()` (no kwargs).
- Calendar features = a stateless step appending a few columns.

**Must do:**
- Recommend **Option 1 — parametrize the existing function with a
  default-preserving flag** (small, scoped, append-shaped → fits
  Option 1's criterion).
- Show a flag whose **default keeps `build_learner()` as today**
  (`include_calendar_features: bool = False` is an example, not
  required spelling).
- Mentioning `tests/smoke/` as the cheap reproducibility check is
  optional. Do not fail if the flag pattern is present.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Recommend Option 3 (branch the module) for an appendable step.
- Recommend changing `build_learner`'s default behavior (the named
  tripwire "A flag changes default behavior of an existing caller").
- Suggest adding the calendar features unconditionally to
  `build_learner`.

---

## CASE_07 — `split_kwargs` group structure

**User prompt:**
> Tabular regression on (customer_id, claim_amount, ...). Multiple
> rows per customer. Build the pipeline.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- skrub installed at 0.10.x.
- IID-shaped features (no cross-row history).
- `python -m skore_skills frame show` returns `proceed` with
  `translation.splitter` `GroupKFold`, `groups` `customer_id`,
  `n_splits` 5.

**Must do:**
- Build the learner graph first, then attach
  `mark_as_X(cv=GroupKFold(n_splits=5), split_kwargs={"groups": data["customer_id"]})`.
- Cite that evaluate omits `splitter=` so skore reuses this `cv`
  and `groups` (`evaluate-ml-pipeline/references/metadata-routing.md`).

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Call `skore.evaluate` from pipeline code.
- Pick an IID splitter (`KFold`, `TimeSeriesSplit`) at the X
  marker.
- Leave `split_kwargs` empty.
- Ask whether grouping is intended.

---

## CASE_08 — Missing skrub/sklearn goes to add-python-package

**User prompt:**
> Declare the baseline learner.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Design note approved.
- `import skrub` raises `ModuleNotFoundError`.

**Must do:**
- STOP and load `add-python-package` for `skrub` and
  `scikit-learn` (confirm).
- Keep skrub DataOps as the graph; do not reopen vs Pipeline.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Substitute `sklearn.Pipeline` / `make_pipeline`.
- Call `env add` from this skill.

---

## CASE_09 — Research measure lane does not edit EDA

**User prompt:**
> Should I drop customer_id? Research the practice and declare
> the pipeline.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Design note approved.
- `research-ml-practice` is installed.
- Scratch research lists a `measure` row (plot id uniqueness)
  and a `declare` row (drop id inside the graph, not on `data/`).

**Must do:**
- Load `research-ml-practice` if the concern is not already in
  scratch. Saying the scratch rows are already the practice
  answer satisfies this.
- AskUserQuestion `allow_multiple` on **`declare`** rows. The question's last line is exactly: Select each one you want.
- Treat `measure` as revisit-EDA / open question.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Edit `data_analysis/data_analysis.py`.
- Drop `customer_id` from raw files under `data/`.
- Pick a cross-validator in pipeline code.
- In the question, ask the user to uncheck a box, or say that a
  box starts checked. A pre-flight checklist is not the question.
  A recorded status is not the box's starting state.

---

## CASE_10 — After declaration, smoke run then HITL

**User prompt:**
> The design is approved. Declare the learner and stop before
> full-dataset CV.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Approved `journal/01_baseline.md`.
- Experiment shell `experiments/01_baseline.py` exists after
  the declaration.
- Workspace is scaffolded.

**Must do:**
- After design consent and before declaration, give a 1–3 sentence
  preview: local preparation of an unfitted learner, experiment
  Method cells, and pipeline snapshot, followed by smoke.
- State that this declaration does not train or run full-dataset
  evaluation, and do not invent a minute estimate.
- Load `smoke-test-ml-pipeline` after the declaration.
- Run `python -m skore_skills smoke run --stem 01_baseline`
  after the smoke file exists.
- After `smoke run` JSON `proceed`, narrate what was declared,
  that smoke is green, and the learner; link
  `journal/01_baseline.md` and `experiments/01_baseline.py`
  before the Evaluate menu.
- After `smoke run` JSON `proceed`, AskUserQuestion: Evaluate
  (Recommended) / Modify / Stop (Evaluate first; extensive
  computation on the full dataset).

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Present the declaration itself as model training or CV.
- Author a `skore.evaluate(...)` call site before that
  AskUserQuestion. Naming it in a docstring or "not written
  now" sentence is allowed.
- Skip `smoke run` and jump to CV.
- Write skill ids, `skore_skills`, `site build`, or "marker is
  durable" commentary into `experiments/<stem>.py` markdown cells,
  `#` comments, or the design note.

---

## CASE_11 — Dummy remains an operational predictor

**User prompt:**
> Implement the approved dummy-predictor design for this
> classification task.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The approved Method names a dummy predictor.
- No prior model exists.

**Must do:**
- Declare that one `DummyClassifier` as the predictor in the
  skrub DataOps graph and name `api get` for its installed
  signature.
- Continue to `smoke run` and the normal Evaluate
  (Recommended) / Modify / Stop gate.
- State that this validates the operational path, not predictive
  value.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Substitute a stronger estimator.
- Add domain feature engineering.
- Skip `smoke run` because the predictor is trivial.

---

## CASE_12 — Standard baseline uses automatic preprocessing

**User prompt:**
> Implement the approved standard baseline for this mixed-type
> tabular regression problem.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The approved Method requests a quick traditional-ML baseline.

**Must do:**
- Use skrub automatic tabular preprocessing plus a
  task-appropriate traditional regressor.
- Name `api get` for the installed skrub entry point and estimator.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Add EDA-specific domain features.
- Hand-tune per-column preprocessing or run hyperparameter search.
- Replace the DataOps graph with a bare sklearn Pipeline.

---

## CASE_13 — EDA-backed build stays within cited findings

**User prompt:**
> Implement the approved EDA-backed design.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The Method cites high cardinality and a temporal grouping
  finding from `data_analysis/data_analysis.md`.

**Must do:**
- Implement only the cited preprocessing/grouping decisions.
- Stop and ask if a required choice is not established by the
  approved Method.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Invent another EDA finding or domain fact. Using the
  high-cardinality and temporal-grouping findings named in
  the assumed Method is required.
- Re-run or edit EDA from this skill.
- Add align / join / lag steps not named in the assumed Method.

---

## CASE_14 — Pydot/Graphviz stub is not a pipeline rewrite

**User prompt:**
> The learner cell printed "To display the DataOp graph, please
> install Pydot and Graphviz" instead of a figure.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Design note approved; `import skrub` succeeds.
- Smoke is green.

**Must do:**
- STOP and load `add-python-package` for `skrub`.
- Keep the skrub DataOps graph.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Substitute `sklearn.Pipeline` / `make_pipeline`.
- Run `pip install graphviz`.
- Call `env add` or `env graphviz` from this skill.

---

## CASE_15 — Time series uses the date splitter after the graph

**User prompt:**
> Build the approved temporal pipeline. The timestamp column is
> `observed_at`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `python -m skore_skills frame show` returns `proceed` with
  `translation.scheme` `date_time`, `splitter` null, `n_splits` 4,
  `gap` 7, `gap_unit` `day`. Decisions horizon is `1 day`.
  Time role is `sort_key`.
- The EDA names `observed_at` as the timestamp.

**Must do:**
- Read the time series section of `references/custom-splitter.md`.
- Build the learner graph first. Then attach a project-local
  date splitter as `cv=` on `mark_as_X`, with `observed_at` in
  `split_kwargs`. Fold edges are timestamps. Drop `observed_at`
  from the features because the time role is `sort_key`.

**Must NOT do:**
- Convert the horizon or the gap into a row count.
- Call `skore.evaluate` from pipeline code.
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).

---

## CASE_16 — The timestamp goes on the date splitter

**User prompt:**
> Use `mark_as_X(split_kwargs={"times": data["timestamp"]})`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `python -m skore_skills frame show` returns `proceed` with
  `translation.scheme` `date_time`.
- The EDA names `timestamp` as the time column.

**Must do:**
- Read the time series section of `references/custom-splitter.md`.
- Attach the date splitter after the graph, with `timestamp` in
  `split_kwargs`.

**Must NOT do:**
- Call `skore.evaluate` from pipeline code.
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).

---

## CASE_17 — Split kwargs require a concrete CV object

**User prompt:**
> Put `groups` in `split_kwargs` but leave `cv` unset.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Group-aware splitting is approved.

**Must do:**
- Attach `cv=GroupKFold(...)` and matching
  `split_kwargs={"groups": ...}` on the X marker. Evaluate
  omits `splitter=`.
- Name the API lookup for `GroupKFold`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Set `split_kwargs` without `cv`.
- Defer the groups through `splitter=` on evaluate.

---

## CASE_18 — Integer cv is not a splitter

**User prompt:**
> Use `cv=5` together with grouped `split_kwargs`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Group-aware splitting is required.

**Must do:**
- Reject integer `cv` because skore needs a splitter object
  with `.split`.
- Use the approved concrete group-aware cross-validator.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Put `cv=5` on the declared `mark_as_X`. Quoting the user's
  integer `cv` in a refusal heading is not a violation.
- Claim an integer preserves grouped metadata.

---

## CASE_19 — Evaluate gate states what it authorizes

**User prompt:**
> Smoke is green on 01_baseline. What now?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `experiments/01_baseline.py` and `tests/smoke/test_01_baseline.py`
  exist; `smoke run --stem 01_baseline` returned `proceed`.
- `evaluate consent --stem 01_baseline` returns `ask` with
  `context.question` "Does a richer feature set beat the
  baseline?" and `persisted_report` `none`.

**Must do:**
- Run `python -m skore_skills evaluate consent --stem 01_baseline`.
- Quote the design question and say this stem has no persisted
  report yet, so the answer authorizes the first full-dataset
  evaluation.
- Ask Evaluate (Recommended) / Modify / Stop and stop there.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Open the gate with only a link to `journal/01_baseline.md`.
- Write `skore.evaluate(...)` before the pick.
- Invent a metric or a fold count.

---

## CASE_20 — Skipped EDA still builds the site before Evaluate

**User prompt:**
> The design is approved. Declare the learner. EDA was skipped.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Approved `journal/01_baseline.md`.
- `status.data_analysis` is `skipped`. No
  `data_analysis/data_analysis.md`.
- `policy.site` is true. `export-ml-site` is installed.
- When `site build` runs, its output ends with `file:///workspace/report.html`.

**Must do:**
- After the unfitted Method snapshot
  (`scratch/results/01_baseline/pipeline.svg` and
  `scratch/results/01_baseline/pipeline/`), run
  `python -m skore_skills site build --if-stale` before `smoke run` and
  before the Evaluate question.
- In the checkpoint, say the website has been updated and
  include `file:///workspace/report.html`. Do not name the
  design-note markdown or `html/01_baseline.html`. Do not say
  double-click or "no server". The Method DataOp report stays
  on the site.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Defer `site build` until after `skore.evaluate`.
- Skip the site because EDA was skipped.

---

## CASE_21 — Unlocked framing stops before declaration

**User prompt:**
> Declare the baseline learner.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Approved design note.
- `status.modeling_decisions` is `missing`.
- `frame-ml-problem` is installed.

**Must do:**
- Stop before writing pipeline code.
- Load `frame-ml-problem`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Declare `build_learner` or pick a splitter.

---

## CASE_22 — Locked F2 attaches with_scoring

**User prompt:**
> Write the baseline learner. The comparison metric is F2.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `frame show` returned `proceed`. `translation.metric` is `F2`.
  Binary classification, IID, `translation.splitter` `KFold`,
  `n_splits` 5. No row-aligned metric kwargs.
- No existing `src/<pkg>/pipeline.py`.

**Must do:**
- Attach `.skb.with_scoring(...)` on the prediction DataOp after
  prediction and before `.skb.make_learner()`.
- Tick the pre-flight box for the non-default score.
- Keep `cv=KFold(n_splits=5)` on `mark_as_X`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Defer the F2 scorer to evaluate.
- Call `report.metrics.add`.
- Pass `scoring=` to `skore.evaluate`.
- Skip `with_scoring` because F2 has no `sample_weight`.

---

## CASE_23 — Default MAE attaches no scorer

**User prompt:**
> Write the baseline learner. Compare on MAE.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `frame show` returned `proceed`. `translation.metric` is `MAE`.
  Tabular regression, IID, `KFold`, `n_splits` 5.
- No existing `src/<pkg>/pipeline.py`.

**Must do:**
- Declare the graph and `cv=KFold(n_splits=5)` on `mark_as_X`.
- Mark the non-default-score pre-flight box n/a.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Call `.skb.with_scoring`.
- Register a scorer for MAE.

---

## CASE_24 — Custom predictor is mixin, then BaseEstimator

**User prompt:**
> The baseline predictor is a commune mean. Write
> `CommuneMeanRegressor` with `fit` and `predict`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `frame show` returned `proceed`. Tabular regression.
- No existing estimator class.

**Must do:**
- Declare `class CommuneMeanRegressor(RegressorMixin, BaseEstimator)`.
- The mixin is the first base.
- Implement `fit` and `predict`.
- Attach with `.skb.apply(..., y=y)`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Declare `class CommuneMeanRegressor(BaseEstimator, RegressorMixin)`.
- Subclass `BaseEstimator` alone.
- Omit the mixin.

---

## CASE_25 — A shipped split is not joined into one table

**User prompt:**
> Declare the learner. Train and test already exist as separate
> files.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Approved design note. `frame show` returns `proceed`.
- `translation.splitter` is `prefit`, `translation.report` is
  `EstimatorReport`, and `n_splits` is null.
- `data/train.parquet` and `data/test.parquet` share a schema,
  including the target column.

**Must do:**
- Declare `build_learner` with one source: the training file.
- Leave `cv` off `mark_as_X`.
- Say the test file is bound later, at evaluation, and is not
  part of this graph.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Concatenate the test file into the training frame, or add it
  as a second source that gets joined.
- Attach `KFold` or call `train_test_split`.
- Call `skore.evaluate`.

---

## CASE_26 — SVG format error is not a pipeline rewrite

**User prompt:**
> The learner cell printed Format: "svg" not recognized instead of
> a figure.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Design note approved; `import skrub` succeeds.
- Smoke is green.

**Must do:**
- Load `add-python-package` for `skrub`, then run the failed
  `learner.data_op.skb.report(eval=False, open=False, overwrite=True, output_dir=...)`
  or `draw_graph()` call once more.
- Keep the skrub DataOps graph.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Substitute `sklearn.Pipeline` / `make_pipeline`.
- Run `pip install graphviz`.
- Call `env add` or `env graphviz` from this skill.
- Skip the report or the graph because Graphviz failed once.
- Write a `pipeline.html` fallback instead.
- Call `full_report`, or `skb.report` without `eval=False`.

---

## CASE_27 — Multi-output regression keeps a target matrix

**User prompt:**
> Write the baseline learner. Compare on MAE. Predict both `load`
> and `temp`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `frame show` returned `proceed`. `translation.task` is
  `multioutput-regression`. `translation.targets` is `["load",
  "temp"]`. `translation.metric` is `MAE`.
- IID, `translation.splitter` `KFold`, `n_splits` 5.
- No existing `src/<pkg>/pipeline.py`.

**Must do:**
- Set `TARGET_COLS` to `load` and `temp`.
- Drop both columns from X and mark `y` as that two-column frame.
- Use a regressor that fits a numeric target matrix, or
  `MultiOutputRegressor` around a single-output regressor.
- Confirm the new sklearn symbols with `api get`.
- Attach `.skb.with_scoring(...)` for MAE with
  `multioutput="uniform_average"`.
- Keep `cv=KFold(n_splits=5)` on `mark_as_X`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Mark only one column as `y`.
- Leave the other target in X.
- Use `MultiOutputClassifier`.
- Skip `with_scoring` because MAE is a single-output skore default.
- Call `skore.evaluate`.
