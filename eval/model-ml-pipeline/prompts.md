# model-ml-pipeline eval

Unless a case says otherwise, `status.modeling_decisions` is `locked`
and `frame show` already returned `proceed` with a non-null
`translation`.

---

## CASE_01 — Approved model implementation

**User prompt:**
> The baseline design is approved. Implement and test the model.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Matching approved design note and experiment shell exist.
- Workspace is scaffolded (`has_src` and `has_journal` true).

**Must do:**
- Run `python -m skore_skills status`.
- Resume the approved stem directly; do not show the starting
  choices menu.
- Preview the broad sequence as local pipeline preparation, small
  real-data smoke fit/predict, optional full-dataset evaluation,
  then read-only audit; leave each detailed compute preview to
  its child skill and do not invent minute estimates.
- Dispatch `build-ml-pipeline` (do not load
  `smoke-test-ml-pipeline` as a sibling of evaluate).
- Treat smoke as a **step of build** that runs
  `python -m skore_skills smoke run --stem <stem>`.
- Name the post-smoke AskUserQuestion (Evaluate (Recommended) /
  Modify / Stop) before full-dataset evaluation.
- Preserve the matching experiment stem.
- Run `python -m skore_skills git end-turn --stage implement`
  after the implement loop (after Evaluate / Modify / Stop,
  evaluate, audit, and
  record-outcome — not before the Evaluate pick).
- If that command returns `invoke`, load `persist-ml-git`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Duplicate detailed build / smoke / evaluate / audit previews
  from the dispatcher.
- Load `smoke-test-ml-pipeline` as a sibling dispatcher step.
- Write `skore.evaluate` or load `evaluate-ml-pipeline` /
  `audit-ml-pipeline` before the post-smoke Evaluate question.
- Replace skrub DataOps with a bare sklearn Pipeline.
- Mark the experiment done while smoke tests fail.
- Run `git commit` in this skill or `git push`.
- Distill `scratch/research/` here instead of loading
  `build-ml-pipeline`.
- Run `python -m skore_skills model choices` for this explicit,
  already-approved stem.

---

## CASE_02 — Missing design note stops before code

**User prompt:**
> Implement experiment 02 for the selected target transform.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The Backlog choice is confirmed with stem `02_target_transform`.
- `journal/02_target_transform.md` does not exist.

**Must do:**
- Run `python -m skore_skills scaffold --journal --stem
  02_target_transform` to create the packaged design-note shell.
- Fill Question, Motivation, Method, and Risks from the selected
  target-transform proposal after that command creates the shell.
- Ask Approve / Modify / Stop. Do not ask Yes / No before the note.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Write model or experiment code before the design note is approved.
- Recreate or fill the design-note shape from memory when the CLI
  command did not run this turn.
- Run `python -m skore_skills site build` before the shell exists.

---

## CASE_03 — Site on stays a four-phase preview

**User prompt:**
> The baseline design is approved. Implement and test the model.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Matching approved design note and experiment shell exist.
- `policy.site` is true. `policy.notebooks` is false.
- `export-ml-site` is installed.

**Must do:**
- With no shell, the answer is the four-phase preview only:
  local pipeline preparation, small real-data smoke fit/predict,
  optional full-dataset evaluation, review.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Name the post-smoke Evaluate / Modify / Stop question, an
  unfitted `site build`, or `pipeline.svg` in this preview.
- Name `loop notebooks` or `notebook convert` on this preview.
  Notebooks stay off until a report exists.
- Run `git commit` in this skill or `git push`.
- Write `skore.evaluate` in this preview.

---

## CASE_04 — Notebooks stay off until a report exists

**User prompt:**
> The baseline design is approved. Implement and test the model.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Approved design note and experiment shell exist with stem
  `01_baseline`.
- `policy.notebooks` is true. `policy.site` is true.
- `export-ml-notebook` and `export-ml-site` are installed.
- `jupytext`, `nbclient`, `ipywidgets`, and `nbconvert` are installed.

**Must do:**
- With no shell, the answer is the four-phase preview only:
  local pipeline preparation, small real-data smoke fit/predict,
  optional full-dataset evaluation, review.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Name the post-smoke Evaluate / Modify / Stop question, an
  unfitted `site build`, or `pipeline.svg` in this preview.
- Name `loop notebooks` or `notebook convert` on this preview.
  Notebooks stay off until a report exists.
- Convert while there is no persisted report
  (`not_evaluated`).
- Run `git commit` in this skill or `git push`.
- Write `skore.evaluate` in this preview.

---

## CASE_05 — Smoke red or Stop does not start evaluate

**User prompt:**
> The baseline design is approved. Implement the model. Pytest
> smoke is red on row count.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Approved design and experiment script exist.
- `tests/smoke/test_01_baseline.py` fails pytest (row count).

**Must do:**
- Stay with `build-ml-pipeline` / `smoke run` to fix topology.
- Name that JSON `stop` keeps the loop in build.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `evaluate-ml-pipeline` or write `skore.evaluate`.
  Describing the post-green sequence, and saying it is unreachable
  while smoke is red, is not starting it. Writing the call this
  turn is.
- Load `audit-ml-pipeline`.
- Loosen the smoke assertion so pytest passes.

---

## CASE_06 — First model writes the baseline note

**User prompt:**
> Let us start modeling. What can we do?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- Modeling decisions Status is `locked`. Baseline is
  `seasonal_naive`. Baseline note is `last observed week`.
- No experiment scripts or completed/running History rows.
- `status.data_analysis` is `missing`.
- Backlog is empty.
- `python -m skore_skills model choices` returns `choices` whose
  ids are `baseline` then `discuss`. The baseline reason quotes
  `seasonal_naive` and `last observed week`.

**Must do:**
- Run `python -m skore_skills status` and
  `python -m skore_skills model choices`.
- Run `python -m skore_skills scaffold --journal --stem <NN_short>`
  and fill the design note from `seasonal_naive` and
  `last observed week`.
- Ask Approve / Modify / Stop. Do not ask Yes / No before the note.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Ask Build the locked baseline or Discuss the next step.
- Mention discuss, an EDA proposal, or the backlog.
- Offer an EDA-derived proposal.
- Offer Pick from the Backlog.
- Write model code before the design note is approved.

---

## CASE_07 — Existing model with EDA and Backlog

**User prompt:**
> Start the next modeling iteration.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Modeling decisions Status is `locked`.
- `experiments/01_baseline.py` exists.
- `status.data_analysis` is `present`.
- Backlog contains B1 and B2.
- `python -m skore_skills model choices` returns `choices` whose
  ids are `eda_proposal`, `backlog`, `discuss`.

**Must do:**
- Run `python -m skore_skills model choices`.
- Ask one question with, in order: Propose a pipeline from the
  EDA; Pick from the Backlog; Discuss the next step.

**Must NOT do:**
- Offer the locked baseline.
- Offer a dummy predictor or a standard baseline.
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Silently pick B1.

---

## CASE_08 — Skipped EDA is not an EDA proposal

**User prompt:**
> What model should we build next?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Modeling decisions Status is `locked`.
- A prior experiment exists.
- `status.data_analysis` is `skipped`.
- Backlog is empty.
- `python -m skore_skills model choices` returns one choice,
  `discuss`.

**Must do:**
- Offer only Discuss the next step.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Treat skipped EDA as recorded findings.
- Offer an EDA proposal or Backlog.

---

## CASE_09 — Discussion becomes a confirmed proposal

**User prompt:**
> I want to talk through what to model next.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The user selected Discuss the next step.

**Must do:**
- Preview this route as LLM discussion over recorded project
  facts, with no model fit, smoke test, or CV before confirmation.
- Discuss what to learn, why now, and what changes.
- Once an idea is agreed, restate it, then AskUserQuestion
  Yes / No, before creating a design note.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Claim local model computation is running during the discussion.
- Force a free-text / artifact entry menu.
- Emit a proposal or model code before confirmation.
- Create the design note before that explicit yes.

---

## CASE_10 — Backlog selection consumes one real row

**User prompt:**
> Pick from the backlog.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- CLI returned B1 and B3; B2 was previously consumed.

**Must do:**
- Load `manage-ml-backlog` and present B1 and B3 in that order.
- Ask for one selection and preserve the unselected row.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Ask Yes / No before a row is picked.
- Renumber B3 to B2.
- Invent a new Backlog item.

---

## CASE_11 — Implement loop reviews before record-outcome

**User prompt:**
> Evaluate it.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `01_baseline` design note approved; smoke green.
- The user chose Evaluate at the post-smoke gate.
- `evaluate-ml-pipeline` and `review-ml-experiment` are installed.
- `review consent` returns `audit`.
- `policy.notebooks` and `policy.site` are both true.

**Must do:**
- Run evaluate, then `review consent`.
- On `audit`, load `review-ml-experiment`. Do not load
  `audit-ml-pipeline` from this dispatcher.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Run `cells run` from this dispatcher.
- Run `loop notebooks`, record-outcome, or `site build` before
  `review-ml-experiment` returns.
- Leave History `planned` in any journal excerpt you author.
- Write the journal files directly instead of dispatching.

---

## CASE_12 — Review then records the locator

**User prompt:**
> Finish the successful baseline evaluation.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Smoke is green and evaluate returned
  `[Open report](https://example.invalid/report/42) · hub · id: 42`.
- `review consent` returned `proceed`.
- `review-ml-experiment` returned that locator and
  G-AUDIT-FINDING `0 issues, 0 tips — automated checks surfaced no actionable finding`.
- `policy.site` is not true.

**Must do:**
- Name this order. A no-tools turn that lists each command
  satisfies the step. Do not reorder it.
- Name `python -m skore_skills loop notebooks --stem <stem>`
  first. It continues only on `skip`. `record` is not this gate.
- On `convert`, name `notebook fill` for every `experiments/`
  or `audit/` source (`--html` when `html` is true). Do not
  `notebook convert` those files. Fill does not `put`. Then
  `loop notebooks` again until `skip`.
- Name record-outcome next, with the exact locator
  `[Open report](https://example.invalid/report/42) · hub · id: 42`
  and that G-AUDIT-FINDING, before site build.
- Write 2–6 sentences of the result. Do not name
  `journal/<stem>.md`. Do not claim the website has been
  updated, because this workspace does not set `policy.site`.
- Include that locator in the user-facing close (first among
  tokens).
- Name `git end-turn --stage implement` last. Do not name
  `site build`: `policy.site` is not true here.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Record G-AUDIT-FINDING `n/a — audit not run`.
- Write the journal files directly instead of record-outcome.
- Drop the locator.
- Invent a headline metric.
- Open idea triage.

---

## CASE_13 — Planned design note uses one approval gate

**User prompt:**
> The design note is written. Approve it and implement.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `journal/02_target_transform.md` exists with State `planned`.
- Question, Motivation, Method, and Risks are filled.
- `design consent` returns `ask` with choices approve, modify, stop.

**Must do:**
- Ask one AskUserQuestion, in order: Approve / Modify / Stop.
- On Approve, run `design approve --stem 02_target_transform`.
  Do not type the date. Then require `design consent` `proceed`
  before code.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Also ask in chat whether the note looks right.
- Treat "Approve it and implement" as approval before the gate.
- Write model code while State is still `planned`.
- Invent a calendar date for Approved by user on.

---

## CASE_14 — Skipped EDA still site-builds before Evaluate

**User prompt:**
> The baseline design is approved. Implement and test the model.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Matching approved design note and experiment shell exist.
- `status.data_analysis` is `skipped`. No
  `data_analysis/data_analysis.md`.
- `policy.site` is true. `export-ml-site` is installed.
- `build-ml-pipeline` is installed.
- Each time `site build` runs, its output ends with `file:///workspace/report.html`.

**Must do:**
- Dispatch `build-ml-pipeline`.
- Require `python -m skore_skills site build` after the unfitted
  Method snapshot (`pipeline.svg` and `pipeline/`) and before
  the Evaluate question, inside that build.
- Keep the post-loop `site build` for the same unevaluated report.
- Say the website has been updated and include
  `file:///workspace/report.html` when each site build runs. Do
  not name the design-note markdown or `html/<stem>.html`. Do
  not say double-click or "no server".

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Defer the first `site build` until after `skore.evaluate`.
- Skip the pre-Evaluate site build because EDA was skipped.
- Point the user at the design-note markdown or
  `html/<stem>.html` instead of `report.html` after a site
  build.
- Say double-click or "no server".

---

## CASE_15 — Design approval states the note's facts inline

**User prompt:**
> Build a dummy predictor to check the pipeline runs.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace; no prior experiment.
- `journal/01_dummy.md` exists with State `planned`, question
  "Does the loading and fit/predict path work end to end?",
  Files touched `src/pkg/pipeline.py`, change "first pipeline; a
  DummyClassifier inside the skrub DataOps declaration", and the
  risk "the dummy adds no predictive value; it only proves the
  path".
- `python -m skore_skills design consent --stem 01_dummy` returns
  `action` `ask` with those facts in its JSON `context`.

**Must do:**
- Run `python -m skore_skills design consent --stem 01_dummy`.
- State the design question, the planned change and files touched,
  and the recorded risk in the approval message itself.
- Ask Approve / Modify / Stop and stop there.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Ask for approval by only pointing at `journal/01_dummy.md`
  without stating what the note says.
- Write model, experiment, or pytest code before approval.
- Invent a question, method, or risk the note does not state.

---

## CASE_16 — Unpopulated design note is not ready for approval

**User prompt:**
> The note for 02_target_transform is created. Approve and build it.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `journal/02_target_transform.md` is the scaffolded shell: State
  `planned`, every content section still a template comment.
- `design consent --stem 02_target_transform` returns `ask` with
  every `context` field empty.

**Must do:**
- Say the note states no question, method change, or risk yet, so
  it is not ready for approval.
- Offer to populate Question / Motivation / Method / Risks first.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Treat "approve and build it" as design approval.
- Fill the note's sections from memory as if they were recorded.
- Write model or experiment code.
- Run `python -m skore_skills site build` on an empty shell.

---

## CASE_17 — Site on rebuilds before design approval

**User prompt:**
> Build a dummy predictor to check the pipeline runs.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace; no prior experiment.
- `journal/01_dummy.md` was just populated (State `planned`) with
  question, files touched, planned change, and a recorded risk.
- `python -m skore_skills design consent --stem 01_dummy` returns
  `action` `ask` with those facts in its JSON `context`.
- `policy.site` is true.
- `export-ml-site` is installed.
- When `site build` runs, its output ends with `file:///workspace/report.html`.

**Must do:**
- Run `python -m skore_skills site build --if-stale` after the
  note is populated and before Approve / Modify / Stop.
- Say the website has been updated and include
  `file:///workspace/report.html`. Do not name
  `journal/01_dummy.md` or `html/01_dummy.html`. Do not say
  double-click or "no server".
- State the design question, planned change, and recorded risk
  inline, then ask Approve / Modify / Stop and stop there.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Write model, experiment, or pytest code before approval.
- Open only `journal/01_dummy.md` or `html/01_dummy.html` and
  omit `report.html`.
- Run `notebook convert` or `git end-turn` on this preview rebuild.
- Fail the approval gate if site build errors; name the error.

---

## CASE_18 — Unlocked framing stops before modeling

**User prompt:**
> Let us start modeling. What can we do?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.modeling_decisions` is `draft`.
- `frame-ml-problem` is installed.

**Must do:**
- Run `python -m skore_skills status`.
- Load `frame-ml-problem` and stop.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Run `python -m skore_skills model choices`.
- Write a design note or model code.

---

## CASE_19 — A null translation does not start model code

**User prompt:**
> The modeling decisions are locked. Build the first model.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.modeling_decisions` is `locked`.
- `python -m skore_skills frame show` returns `proceed` with
  `translation` null.

**Must do:**
- Run `python -m skore_skills frame show`.
- Say the lock has no splitter translation and stop.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Offer model choices or dispatch `build-ml-pipeline`.

---

## CASE_20 — Pending setup loads project setup

**User prompt:**
> Build the first baseline model.

**Assumed workspace state:**
- No `src/` and no `journal/`.
- `status.setup.pending` is `env`, `workspace`, `git`.
- `status.setup.env` and `status.setup.workspace` are `missing`,
  not `declined`.
- `status.skills.setup-ml-project` is true.

**Must do:**
- Load `setup-ml-project` and stop.
- Do not write a design note or dispatch `build-ml-pipeline`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Run `python -m skore_skills model choices`.
- Start model code.

---

## CASE_21 — Discuss does not write the baseline note

**User prompt:**
> Discuss the next step.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Modeling decisions Status is `locked`. Baseline is
  `seasonal_naive`.
- No experiment scripts.
- `python -m skore_skills model choices` returns `choices` whose
  ids are `baseline` then `discuss`.

**Must do:**
- Discuss what to learn, why now, and what changes.
- Once an idea is agreed, restate it, then AskUserQuestion
  Yes / No, before creating a design note.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Write the locked-baseline design note.
- Ask Build the locked baseline.
- Write model code.

---

## CASE_22 — A picked backlog row writes the note

**User prompt:**
> Take B1. Robust scaling applies to the numeric columns.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `experiments/01_baseline.py` exists.
- B1 Item is "try robust scaling", Source is `user`. B3 remains.
- The missing shaping fact is already in the prompt: numeric
  columns.

**Must do:**
- Fill the next design note from that Item, Source, and the
  numeric-columns fact.
- Ask Approve / Modify / Stop.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Ask Yes / No before the note.
- Ask which columns again.
- Add an estimator or a procedure the row and the fact do not state.
- Renumber B3.
- Write model code before the design note is approved.

---

## CASE_23 — Results are published before the close message

**User prompt:**
> Finish the evaluated baseline.

**Assumed workspace state:**
- Review returned a digest, locator, and finding.
- `manage-ml-backlog` record-outcome just updated JOURNAL and
  `journal/01_baseline.md`.
- `policy.site` is true and `export-ml-site` is installed.

**Must do:**
- Run `python -m skore_skills site build --if-stale` after
  record-outcome and before the user-facing close.
- Say the website has been updated and show the absolute
  `file://` URL of the freshly built `report.html` that `site
  build` printed. Do not name `journal/01_baseline.md` or
  `html/01_baseline.html`. Do not say double-click or "no
  server".

**Must NOT do:**
- Send the site link before the Results Markdown is published.
- Re-execute a source-current experiment notebook at Close.
