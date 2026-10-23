# evaluate-ml-pipeline eval — golden prompts

Unless a case says otherwise, `status.modeling_decisions` is `locked`
and `frame show` returned `proceed` with `translation.splitter`
`KFold`, `n_splits` 5, `groups` null, and `metric` `MAE`.

Behavioural prompts. Pass = every Must do ticked, zero Must NOT
violated.

---

## CASE_01 — Standard skore.evaluate entry, IID tabular

**User prompt:**
> Wire `experiments/01_baseline.py` for the baseline. Tabular
> regression, no groups, no temporal ordering.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `journal/01_baseline.md` approved.
- `src/<pkg>/pipeline.py` exists with `build_learner` returning a
  `SkrubLearner`. The X-marker has `cv=KFold(n_splits=5)` and
  empty `split_kwargs`.
- `python -m skore_skills frame show` returns `proceed` with
  `translation.splitter` `KFold`, `n_splits` 5, `metric` `MAE`.
- `experiments/01_baseline.py` is the scaffold placeholder.
- `policy.skore_mode` is `local`.
- Cache exists at `scratch/api/sklearn/1.8.0/cv_splitters.md`
  covering `KFold` / `GroupKFold`, and at
  `scratch/api/skore/0.18.0/evaluate.md`.

**Must do:**
- After all evaluation gates and before writing/running
  `skore.evaluate`, give a 1–3 sentence preview: local
  full-dataset CV with the selected splitter, the skore checks
  computed and stored with the report, report persistence, and
  the `experiments/01_baseline.py` /
  `scratch/results/01_baseline/` outputs.
- Name the fold count when known; otherwise explain that timing
  depends on rows, folds/repeats, the learner, and the checks.
  Do not invent a minute estimate.
- Pick **`skore.evaluate(learner, data={...})`** as the entry
  point, with no `splitter=` (not `cross_val_score`, not
  `cross_validate`). The `KFold` already on the marker is reused.
- Score that one learner with one `skore.evaluate`, one
  `report.checks.summarize()` with no arguments, and one
  `project.put`.
- Name `python -m skore_skills frame show` and
  `python -m skore_skills api get` for `skore.evaluate` (or Read
  the matching caches already listed).
- Mention `data={...}` (env-dict) for `SkrubLearner`, NOT
  positional `X, y`.
- Run `python -m skore_skills git end-turn --stage evaluate` at
  the end of the turn.
- If that command returns `invoke`, load `persist-ml-git`.
- Copy `templates/materialize.py` to
  `scratch/results/01_baseline/materialize.py` and run it once.
  The `<CALL>` block is the experiment's `skore.evaluate`,
  `report.checks.summarize()`, and `project.put`. Do not execute
  `experiments/01_baseline.py`. The tail writes `report.html`
  from `report._repr_html_()`, `report.txt` from `repr(report)`,
  `checks.html`, `metrics.html`, and `id.txt`. Write
  `locator.txt` from that id. The experiment file ends at
  `report.checks.summarize()`, `project.put`, and a bare
  `report`.
- `materialize.py` writes, from `learner.data_op.skb` on the
  in-memory learner (`reports_[0].estimator_` on a CV report),
  `pipeline.svg` with `draw_graph().svg` and
  `scratch/results/01_baseline/pipeline/` with
  `report(eval=False, open=False, overwrite=True, output_dir=...)`.
  No `environment`. That does not fit.
- Run `python -m skore_skills loop locator --stem 01_baseline` and
  `python -m skore_skills loop artifacts --stem 01_baseline`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Present splitter reasoning alone as model fitting.
- Recommend `cross_val_score`, `cross_validate`,
  `classification_report`, or hand-rolled `print(mean_squared_error(...))`.
- Default to `StratifiedKFold` (forbidden — compresses across-fold
  variance, even on imbalance).
- Pass `splitter=` to `skore.evaluate`.
- Pass `fast_mode` or `ignore` to `report.checks.summarize`.
- Call `project.put` before `report.checks.summarize()`.
- Pre-pin a different metric (e.g. `scoring="neg_mean_squared_error"`).
  The locked comparison is `MAE`.
- Run `git commit` in this skill or `git push`.
- Put `write_text` of `report.html`, `report.txt`, `locator.txt`,
  or `pipeline.svg`, or `skb.report(...)`, in
  `experiments/01_baseline.py`. Those writes belong in
  `scratch/results/01_baseline/materialize.py`.
- Execute `experiments/01_baseline.py` or `notebook convert` it.
- Call `skb.report` or `full_report` without `eval=False`.

---

## CASE_02 — Time series cv is missing on the DataOp

**User prompt:**
> Wire `experiments/02_load_forecast.py` for the 24h-ahead load
> forecast experiment. Pick the splitter.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `journal/02_load_forecast.md` approved.
- `pipeline.py` X-marker has no `cv=`.
- `python -m skore_skills frame show` returns `proceed` with
  `translation.scheme` `date_time`, `n_splits` 4, `gap` 7,
  `gap_unit` `day`.
- Matching smoke pytest is green.

**Must do:**
- Name `python -m skore_skills frame show`.
- Go back to build because the locked date splitter is not on
  the marker. This skill was entered directly, so go through
  `model-ml-pipeline`, which resumes the approved design. Do not
  write `skore.evaluate` yet.

**Must NOT do:**
- Write `skore.evaluate` in this turn.
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).

---

## CASE_03 — `split_kwargs={"groups": ...}` → GroupKFold

**User prompt:**
> Wire `experiments/NN_*.py` for a tabular regression where rows
> are grouped by customer.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `status.modeling_decisions` is `locked`.
- `frame show` `translation.groups` is `customer_id` and
  `translation.splitter` is `GroupKFold`.
- `pipeline.py` X-marker has
  `cv=GroupKFold(n_splits=5)` and
  `split_kwargs={"groups": data["customer_id"]}`.
- `python -m skore_skills frame show` returns `proceed` with
  `translation.splitter` `GroupKFold` and `groups` `customer_id`.
- No temporal structure.

**Must do:**
- Name `python -m skore_skills frame show`. Reuse the `GroupKFold`
  already on the marker. Do not withhold that name.
- Call `skore.evaluate(learner, data={...})` **without**
  `splitter=` so skore reuses the DataOp `cv` and `groups`
  (`references/metadata-routing.md`).
- `python -m skore_skills api get` for the *signature* may be named
  as the next live turn. Do not fail if signature lookup is BLOCKED
  as long as `GroupKFold` is named.
- Show the `data={...}` env-dict form for a `SkrubLearner`.
- Do NOT use `StratifiedGroupKFold` (forbidden by Stop conditions).

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Use `StratifiedGroupKFold`.
- Use `LeaveOneGroupOut` (forbidden — per-fold variance too high).
- Pick `KFold` ignoring the group structure.
- Pass `splitter=GroupKFold()` (or any `splitter=`) to `evaluate`
  — that drops `split_kwargs` and `groups` becomes None.

---

## CASE_04 — Empty `split_kwargs` BUT possible group structure

**User prompt:**
> Wire `experiments/NN_*.py`. The data has a `region` column. Not
> sure if we should treat it as a group.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `pipeline.py` X-marker has empty `split_kwargs`.
- `status.modeling_decisions` is `locked`.
- `frame show` `translation.groups` is `region`.

**Must do:**
- **Refuse to default** to `KFold` silently.
- Send the fix back to build (NOT this skill) to wire
  `split_kwargs` for `region` first, through `model-ml-pipeline`
  since this skill was entered directly.
- Cite the stop: `translation.groups` is set and `split_kwargs`
  is empty → back to build.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Default to `KFold` and proceed.
- Auto-wire `split_kwargs={"groups": data["region"]}` from this
  skill (that's `build-ml-pipeline`'s job).
- Ask whether `region` should be a group.
- Pick `StratifiedKFold` because "stratified is safer".

---

## CASE_05 — Refuse `cross_val_score` / hand-rolled prints

**User prompt:**
> Just use `cross_val_score(learner, X, y, cv=5)` for the baseline
> evaluation and `print(mean_squared_error(...))` for the metric.
> Quick and simple.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `pipeline.py` returns a `SkrubLearner`.
- skore is installed.

**Must do:**
- Refuse `cross_val_score` and the hand-rolled metric print.
- Cite that `skore.evaluate` is the canonical entry point in this
  stack.
- Cite that `SkrubLearner` does NOT implement sklearn's
  `fit(X, y)` signature — `cross_val_score` will raise.
- Propose `skore.evaluate(learner, data={...})` with no
  `splitter=`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Write `cross_val_score(...)` in `experiments/NN_*.py`.
- Use `print(mean_squared_error(...))` instead of the report
  object.
- Allow the substitution as a "just for now" workaround.

---

## CASE_06 — CV is necessary but not sufficient for history-dep

**User prompt:**
> 02_load_forecast has lag features. CV passes clean — RMSE looks
> fine. Mark it `done` in `JOURNAL.md`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `02_load_forecast` ran; CV report is clean.
- `tests/smoke/test_02_load_forecast.py` exists but has NOT been
  run this turn / is currently red on row-count.

**Must do:**
- Refuse to mark `done` without the smoke test passing.
- Cite the Stop condition: "CV is necessary but not sufficient for
  any pipeline with history-dependent features."
- Mention that `skore.evaluate` materializes the graph once with
  one env-dict; the smoke test exercises a fresh env-dict at
  predict time, which is what catches cold-start row drops.
- State that a passing smoke test is still required before the
  caller may flip the status.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Edit `journal/02_load_forecast.md` Status to `done`.
- Edit `journal/JOURNAL.md` History row to `done`.
- Treat clean CV as sufficient for a history-dependent pipeline.
- Write `skore.evaluate` while pytest smoke is red.

---

## CASE_07 — A scratch probe must not re-run evaluate

**User prompt:**
> Add a scratch probe that re-runs `skore.evaluate(learner, ...)` to
> see the updated metrics, then `project.put("02_text_encoder",
> report)` to refresh the cache.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `experiments/02_text_encoder.py` already produced a report.
- The user wants a "refreshed" version.

**Must do:**
- Refuse the scratch re-run.
- Cite that the human experiment file contains
  `skore.evaluate(...)` and `project.put(...)` and is not
  executed. The only run is
  `scratch/results/<stem>/materialize.py`, so `project.put`
  happens once.
- Recommend `project.summarize()` then `project.get(id)` to read
  a stored report. `get(key)` raises `KeyError`.
- If a fresh report is needed, update that human call and re-run
  `materialize.py` once. Do not execute the experiment file.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Approve a scratch probe that calls `skore.evaluate` and
  `project.put`.
- Say the experiment file is executed to store the report.

---

## CASE_08 — G-SKORE-MODE unset at first evaluate

**User prompt:**
> Wire `experiments/01_baseline.py` for the baseline.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `journal/01_baseline.md` approved.
- `src/<pkg>/pipeline.py` has `build_learner`.
- `policy.skore_mode` is unset. `import skore` may fail.
- `add-python-package` is installed.

**Must do:**
- AskUserQuestion where to store reports (local recommended /
  Hub / MLflow) before writing `skore.evaluate`.
- Persist `policy set skore_mode` after the user answers.
- If the answer is **local**, create `reports/` (`mkdir`, exist_ok)
  with no README. If **hub** or **mlflow**, do not create
  `reports/`.
- Load `add-python-package` and name
  `env add-skore --mode <mode> --execute`; do not construct the
  manager-specific requirement in this skill.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Silent-default `mode="local"` without asking.
- Drop back to `cross_val_score` because skore is missing.
- Re-ask pandas vs polars.
- Send `skore[hub]` / `skore[mlflow]` directly to pixi or conda.
- Write `reports/README.md`.

---

## CASE_09 — Recorded skore mode is not re-asked

**User prompt:**
> Wire `experiments/01_baseline.py` for the baseline.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Same as CASE_01.
- `policy.skore_mode` is `local`.
- `skore` imports.

**Must do:**
- Use local mode; do not re-ask where to store reports.
- Pick `skore.evaluate` as the entry point.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Re-open local vs hub vs mlflow.

---

## CASE_10 — Smoke not green stops before skore.evaluate

**User prompt:**
> Wire evaluate for the 24h-ahead load forecast. Run CV now.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `journal/02_load_forecast.md` approved.
- `experiments/02_load_forecast.py` exists.
- Pipeline has lag features (history-dependent).
- `tests/smoke/test_02_load_forecast.py` is missing, or pytest is red.

**Must do:**
- Run `python -m skore_skills status`.
- STOP. Go back to build for the pytest smoke, through
  `model-ml-pipeline` since this skill was entered directly.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Author `skore.evaluate` / `project.put` call sites this turn
  (naming them in a STOP sentence is allowed).
- Say CV can still be produced while smoke is failing.
  Explaining why CV must not run while smoke is red, including
  naming `skore.evaluate` in that STOP sentence, is allowed.

---

## CASE_11 — Direct evaluate owns convert and site build

**User prompt:**
> Evaluate the baseline.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `journal/01_baseline.md` is approved.
  `experiments/01_baseline.py` exists. Smoke is green. No
  history-dependent step.
- `frame show` is `proceed`. `translation.splitter` is `KFold`,
  `n_splits` 5, `metric` `MAE`.
- `evaluate consent --stem 01_baseline` is `proceed`.
- `policy.skore_mode` is `local`. The `skore.evaluate` API cache
  is a hit.
- `project.put("01_baseline", report)` already succeeded.
  `scratch/results/01_baseline/report.txt` says the locked MAE
  is 12.4.
- `loop artifacts --stem 01_baseline` is `record`. No audit ran.
  `audit/01_baseline.py` does not exist.
- `loop notebooks --stem 01_baseline` is `convert`, `html` true,
  `sources` `experiments/01_baseline.py`. After that convert,
  the same command is `skip`.
- The post-convert `loop locator --stem 01_baseline` is
  `local workspace: [reports/](../reports/) · id: local-report-id`.
- `model-ml-pipeline` did not dispatch this turn.
- `policy.notebooks` and `policy.site` are both true.
- `export-ml-notebook` and `export-ml-site` are installed.
- `jupytext`, `nbclient`, `ipywidgets`, and `nbconvert` are
  installed.
- These results are already known. Name the close from them.
  Do not stop for another lookup, and do not invent a second
  metric.
- When `site build` runs, its output ends with `file:///workspace/report.html`.

**Must do:**
- Write 2–6 sentences of the evaluation result.
- Say the website has been updated and include
  `file:///workspace/report.html`, because `policy.site` is
  true. Do not name the design-note markdown or
  `html/01_baseline.html`. Do not say double-click or "no
  server".
- Include the G-REPORT-LOCATOR value (or
  `n/a — backend did not expose a locator`) in the user-facing
  close (first among tokens, after the narrative). When the
  experiment script was converted, that locator is the one from
  the post-convert `loop locator`.
- Name this order. A no-tools turn that lists each command
  satisfies the step. Saying the command was not executed does
  not fail it.
- Name `loop artifacts`, then `python -m skore_skills loop
  notebooks`. A placeholder stem is enough. The notebook gate
  continues only on `skip`. `record` is the artifacts action,
  not this gate.
- On `convert`, name `notebook fill` for every `experiments/`
  or `audit/` source with `--html`. Do not `notebook convert`
  those files. Fill does not `put`.
- Name record-outcome next, after the notebook gate is `skip`,
  since no audit ran this turn, and hand it that locator.
- Name `python -m skore_skills site build --if-stale` after record-outcome.
- Name `python -m skore_skills git end-turn --stage evaluate`
  last. If it returns `invoke`, name `persist-ml-git`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Name record-outcome, `site build`, or `git end-turn` without
  the locator (or the explicit n/a string).
- End the turn, or name only the audit file, while `action` is
  `convert`.
- Name `site build` before record-outcome.
- Write `journal/JOURNAL.md` or the design note directly.
- Run `git commit` in this skill.
- Convert `audit/01_baseline.py`: no audit file exists this turn.

---

## CASE_12 — Dispatched evaluate returns instead of closing

**User prompt:**
> Evaluate the baseline.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Same as CASE_01; smoke is green.
- `model-ml-pipeline` dispatched this turn and owns the close.
- `policy.notebooks` and `policy.site` are both true.

**Must do:**
- Include the G-REPORT-LOCATOR value (or
  `n/a — backend did not expose a locator`) in the return to the
  dispatcher.
- Return to `model-ml-pipeline` after the evaluation.
- State that the dispatcher owns record-outcome, the close-time
  notebook gate, and `git end-turn`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Drop the locator because the dispatcher owns convert.
- Write the User-facing close (narrative + Open these) here;
  the dispatcher owns it.
- Run `notebook convert`, the close-time `loop notebooks`, or
  `git end-turn` here.
- Load `manage-ml-backlog` here.
- Load `triage-ml-task` directly.

---

## CASE_13 — Local put records workspace locator

**User prompt:**
> Evaluate and save 01_baseline locally.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Smoke is green and `policy.skore_mode` is `local`.
- `project.put("01_baseline", report)` succeeds.
- The newest matching summary row has id `local-report-id`.

**Must do:**
- Read `project.summarize().frame()` after the successful put and
  select the newest matching-key row.
- Include `local workspace: [reports/](../reports/) · id:
  local-report-id` and the resolved absolute `reports/` path in
  the End of turn close (G-REPORT-LOCATOR).
- Pass that locator to audit / record-outcome.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Treat the return from `put` as the report id.
- Link an internal serialized report file.
- Announce a locator when `put` has not succeeded, or invent
  an id. Using `local-report-id` from assumed workspace state
  after a successful `put` is required, not a violation. Saying
  the live shell did not re-run `put` this turn is not a
  violation. A Pre-flight line that records that assumed locator
  source is not an announcement.
- Convert, site-build, or `git end-turn` without the locator.

---

## CASE_14 — Hub put preserves its exact report URL

**User prompt:**
> Evaluate and upload 02_encoder to Skore Hub.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Smoke is green and `policy.skore_mode` is `hub`.
- Successful `put` stdout contains
  `Consult your report at https://hub.example/direct-report`.
- The matching report id is
  `skore:report:cross-validation:42`.

**Must do:**
- Preserve the exact stdout URL.
- Include `[Open report](https://hub.example/direct-report) · hub
  · id: skore:report:cross-validation:42` in the End of turn close
  (G-REPORT-LOCATOR).
- Pass that exact Markdown locator downstream.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Construct a Hub report URL from workspace/project/type.
- Drop the report id.
- Convert, site-build, or `git end-turn` without the locator.

---

## CASE_15 — MLflow non-HTTP locator is not a browser URL

**User prompt:**
> Evaluate 03_features into our file-backed MLflow project.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Smoke is green and `policy.skore_mode` is `mlflow`.
- `tracking_uri` is `file:./mlruns`; put emits no run URL.
- Summary identifies experiment `7` and run `abc123`.

**Must do:**
- Include `mlflow · tracking: file:./mlruns · experiment: 7 · run:
  abc123` in the End of turn close (G-REPORT-LOCATOR).
- Pass that locator downstream.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Invent an HTTP URL for the file store.
- Treat `file:./mlruns` as a clickable run page.
- Convert, site-build, or `git end-turn` without the locator.

---

## CASE_16 — Do not pass `splitter=` when groups are on the DataOp

**User prompt:**
> Groups are already on `mark_as_X`. Call `skore.evaluate` with
> `splitter=GroupKFold()` so the gate is visible.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- X marker has `cv=GroupKFold()` and
  `split_kwargs={"groups": data["customer_id"]}`.
- Smoke is green.

**Must do:**
- Cite `references/metadata-routing.md`: omit `splitter=` so
  skore reuses DataOp `cv` and `groups`.
- Write `skore.evaluate(learner, data={...})` with no `splitter=`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Pass `splitter=GroupKFold()` (or any `splitter=`) — that drops
  `split_kwargs` and `groups` becomes None.

---

## CASE_17 — Standalone evaluate close is ordered

**User prompt:**
> Evaluate the approved, smoke-green experiment and finish the turn.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- This is a standalone evaluate invocation.
- Notebooks and site are enabled.
- When `site build` runs, its output ends with `file:///workspace/report.html`.

**Must do:**
- After `put`, write a 2–6 sentence narrative, then surface
  G-REPORT-LOCATOR first among tokens. Say the website has been
  updated and include `file:///workspace/report.html`, because
  the site is enabled. Do not name the design-note markdown or
  `html/<stem>.html`. Do not say double-click or "no server".
- Name this order. A no-tools turn that lists each command
  satisfies the step. Saying the command was not executed does
  not fail it. `loop notebooks` continues only on `skip`.
  `record` is `loop artifacts`, not this gate.
- Name `python -m skore_skills loop notebooks --stem <stem>`
  before record-outcome. On `convert`, name `notebook fill`
  on every `experiments/` or `audit/` source (`--html` when
  `html` is true), including `experiments/<stem>.py` and
  `audit/<stem>.py` when that file exists. Do not `notebook
  convert` those files. Do not add `<!-- results-embed: audit -->`.
- Name audit when available, then record-outcome with that
  locator, then the close-time `site build --if-stale`, then
  `git end-turn --stage evaluate`. A post-materialize
  `site build --if-stale` may also run earlier so the result
  viewers are visible; it does not replace this close build.
- If git returns `invoke`, name `persist-ml-git` and stop,
  because it returns to triage.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Record before the locator exists.
- End the turn, or fill only the audit file, while `action`
  is `convert`.
- `notebook convert` `experiments/<stem>.py` because the script
  contains `skore.evaluate`.
- Treat the post-materialize preview as the finished close, or
  skip the close-time `site build --if-stale` after
  record-outcome.
- Load triage a second time after `persist-ml-git`.

---

## CASE_18 — Direct first evaluation still requires post-smoke consent

**User prompt:**
> Run evaluation for 05_new_model.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The design is approved and smoke is green.
- This experiment has never been evaluated.
- The user has not yet chosen Evaluate at the post-smoke gate.

**Must do:**
- Preview the possible full-dataset CV and its cost drivers, but
  state that no local evaluation starts until the gate is answered.
- Present Evaluate (Recommended) / Modify / Stop before the first
  evaluation.
- Explain that an explicit re-evaluation request for an existing
  persisted report can proceed directly.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Treat the first-run request as re-evaluation.
- Write or execute `skore.evaluate` before the gate answer.

---

## CASE_19 — F2 with beta goes through with_scoring

**User prompt:**
> Evaluate 06_classifier with an F2 score using beta=2, show it,
> and save the report.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The post-smoke answer was Evaluate in this turn.
- The learner is a SkrubLearner. `pipeline.py` has no
  `with_scoring`.
- `python -m skore_skills api get` confirmed the installed
  `with_scoring`, `make_scorer`, and `skore.evaluate` signatures.

**Must do:**
- Load `references/custom-metrics.md`.
- Route back through build and attach
  `.skb.with_scoring(...)` before `.skb.make_learner()`, with a
  named scorer from `make_scorer(..., beta=2)`.
- After that attachment, call `skore.evaluate(learner, data={...})`
  and read the F2 row from `report.metrics.summarize().frame()`
  before `project.put(...)`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Call `report.metrics.add`.
- Pass `scoring=` to `skore.evaluate`.
- Use a lambda for the persisted scorer.

---

## CASE_20 — Route weighted Skrub scoring through the DataOp

**User prompt:**
> Evaluate 07_grouped with weighted MAE. Customer groups must stay
> disjoint and `sample_weight` is a column in the input table.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The post-smoke answer was Evaluate in this turn.
- The learner is a SkrubLearner whose X marker already has
  `cv=GroupKFold()` and
  `split_kwargs={"groups": data["customer_id"]}`.
- `python -m skore_skills api get` confirmed the installed
  `with_scoring`, `make_scorer`, and `skore.evaluate` signatures.

**Must do:**
- Route back through build to derive `sample_weight` from the
  marked/aligned X DataOp and attach
  `.skb.with_scoring(..., kwargs={"sample_weight": ...})` after
  prediction and before `.skb.make_learner()`.
- Call `skore.evaluate(learner, data={...})` without
  `splitter=`.
- Read the attached name from `report.metrics.summarize().frame()`,
  then call `project.put(...)`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Call `report.metrics.add`.
- Pass `scoring=` to `skore.evaluate`.
- Put `sample_weight` in `mark_as_X(..., split_kwargs=...)`.
- Derive scoring weights from the unsplit raw frame.

---

## CASE_21 — Register a custom check before persistence

**User prompt:**
> Evaluate 08_wide_table and add a custom check that flags when
> the test set has more than 50 features, then save the report.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The post-smoke answer was Evaluate in this turn.
- This is a sklearn-style estimator, not a SkrubLearner.
- `python -m skore_skills api get` confirmed the installed
  `skore.evaluate`, `skore.Check`, `CheckNotApplicable`, and
  `checks.add` signatures.

**Must do:**
- Load `references/custom-checks.md`.
- Define a named module-level `Check` subclass (not a lambda).
- Order the implementation as `skore.evaluate(...)`, then
  `report.checks.add(...)`, then
  `report.checks.summarize(...)`, then `project.put(...)`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Call `project.put` before registering the custom check.
- Replace or disable built-in SKD checks.
- Use a lambda or nested class for the persisted check.
- Register the check from `audit/` instead of
  `experiments/NN_*.py`.

---

## CASE_22 — Do not invent a custom check

**User prompt:**
> Wire `experiments/01_baseline.py` for the baseline. Tabular
> regression, no groups, no temporal ordering.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `journal/01_baseline.md` approved.
- `src/<pkg>/pipeline.py` exists with `build_learner` returning a
  `SkrubLearner`. The X-marker has empty `split_kwargs`.
- Matching smoke pytest is green.
- The post-smoke answer was Evaluate in this turn.
- The user did not ask for a custom metric or custom check.

**Must do:**
- Pick `skore.evaluate(learner, data={...})` with no
  `splitter=`. The `KFold` already on the marker is reused.
- Call `report.checks.summarize()` with no arguments after
  `evaluate` and before `project.put`.
- Trust skore metric and SKD-check defaults.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Define a `Check` subclass or call `report.checks.add`.
- Pass `fast_mode` or `ignore` to `report.checks.summarize`.
- Call `project.put` before `report.checks.summarize()`.
- Pass `scoring=` to `skore.evaluate`.
- Call `report.metrics.add`.

---

## CASE_23 — Unlocked framing does not choose a splitter

**User prompt:**
> Evaluate the baseline.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Approved design, green smoke, declared learner.
- `status.modeling_decisions` is `draft`.
- `model-ml-pipeline` is installed.

**Must do:**
- Stop before choosing a splitter or writing `skore.evaluate`.
- Return to `model-ml-pipeline`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Ask for a cross-validator.
- Write a `skore.evaluate` call. Naming it in a STOP sentence
  is allowed.

---

## CASE_24 — Missing locked F2 returns to build

**User prompt:**
> Evaluate 09_classifier. The locked comparison metric is F2.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The post-smoke answer was Evaluate in this turn.
- The learner is a SkrubLearner. `pipeline.py` has no
  `with_scoring`.
- `frame show` returned `proceed` with `translation.metric` `F2`.
- Binary classification. The X marker has `cv=KFold(n_splits=5)`.

**Must do:**
- Return to build before `skore.evaluate` so F2 is attached with
  `.skb.with_scoring(...)` before `.skb.make_learner()`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Call `skore.evaluate` while the locked scorer is missing.
- Cover the locked F2 with `report.metrics.add`.
- Pass `scoring=` to `skore.evaluate`.

---

## CASE_25 — Attached F2 is a summarize row

**User prompt:**
> Evaluate 09_classifier. The locked comparison metric is F2.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The post-smoke answer was Evaluate in this turn.
- The learner is a SkrubLearner. The prediction DataOp already
  has `.skb.with_scoring(...)` for F2, before `make_learner`.
- `frame show` returned `proceed` with `translation.metric` `F2`.
- Binary classification. The X marker has `cv=KFold(n_splits=5)`.
- `policy.skore_mode` is `local`.

**Must do:**
- Call `skore.evaluate(learner, data={...})` without `splitter=`.
- Read the F2 row from `report.metrics.summarize().frame()`, then
  `project.put(...)`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Send the learner back to build.
- Call `report.metrics.add`.
- Pass `scoring=` to `skore.evaluate`.

---

## CASE_26 — Attached metric missing because the mixin is absent

**User prompt:**
> `within_10pct` is on the learner with `with_scoring`, but
> `summarize()` has no such row. The predictor is
> `class CommuneMeanRegressor(BaseEstimator)`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The prediction DataOp already has
  `.skb.with_scoring(...)` for `within_10pct`, before
  `make_learner`.
- `CommuneMeanRegressor` subclasses `BaseEstimator` only.
  It implements `fit` and `predict`.
- `frame show` returned `proceed`. Tabular regression.

**Must do:**
- Return to build before treating the report as complete.
- Change the bases to `RegressorMixin, BaseEstimator`.
- The mixin is the first base.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Leave the class as `BaseEstimator` only.
- Write `class CommuneMeanRegressor(BaseEstimator, RegressorMixin)`.
- Call `report.metrics.add`.
- Drop `with_scoring` as if the scorer were missing.

---

## CASE_27 — A shipped test table uses a prefitted learner

**User prompt:**
> Score the baseline on the test table that shipped with the data.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Approved design, green smoke, declared `build_learner`. The
  marker has no `cv`. The graph loads one table.
- `frame show` returns `proceed` with `translation.splitter`
  `prefit`, `translation.report` `EstimatorReport`, and
  `n_splits` null.
- `policy.skore_mode` is `local`. Evaluate consent is `proceed`.
- `data/train.parquet` and `data/test.parquet` share a schema,
  including the target.

**Must do:**
- Fit the learner on the training table only.
- Write `skore.evaluate` in `experiments/NN_*.py` with
  `splitter="prefit"` and `data` bound only to the test table.
- Say that omitting `splitter=` would draw a new 80/20 split.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Omit `splitter=` or pass the training table into `evaluate`.
- Concatenate the two tables before the call.
- Pass positional `X, y` for a `SkrubLearner`.

---

## CASE_28 — Notebook-enabled evaluation executes once

**User prompt:**
> Evaluate the approved baseline.

**Assumed workspace state:**
- Evaluate consent is `proceed`; smoke is green.
- `policy.notebooks` and `policy.site` are true.
- Notebook and site export skills are installed.

**Must do:**
- Run `scratch/results/01_baseline/materialize.py` once. Do not
  execute `experiments/01_baseline.py`.
- Run `python -m skore_skills notebook fill
  experiments/01_baseline.py --html`.
- After materialize and the locator, run
  `python -m skore_skills site build --if-stale` before the next
  review or user gate.

**Must NOT do:**
- Run `notebook convert` on the experiment script.
- `project.put` a second time to build the notebook.
- Wait for final close to expose the completed evaluation.
- Enable either policy when its value is null or false.

---

## CASE_29 — Multi-output metrics stay per output

**User prompt:**
> Evaluate `04_energy`. The locked comparison is MAE, and the
> outputs are `load` and `temp`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The post-smoke answer was Evaluate in this turn.
- The learner is a SkrubLearner. The prediction DataOp already
  has `.skb.with_scoring(...)` for the MAE aggregate, before
  `make_learner`.
- `frame show` returned `proceed`. `translation.task` is
  `multioutput-regression`. `translation.targets` is `["load",
  "temp"]`. `translation.metric` is `MAE`.
- The X marker has `cv=KFold(n_splits=5)`.
- `policy.skore_mode` is `local`.

**Must do:**
- Call `skore.evaluate(learner, data={...})` without `splitter=`.
- Read `report.metrics.summarize().frame()` and keep the
  per-output rows. The close may quote the aggregate MAE.
- Call `project.put(...)`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Average the per-output rows in the experiment file and drop them.
- Call `report.metrics.add`.
- Return the learner to build.
- Pass `scoring=` to `skore.evaluate`.
