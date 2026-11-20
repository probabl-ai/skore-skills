# audit-ml-pipeline eval

---

## CASE_01 — Audit is read-only and returns a digest

**User prompt:**
> Audit experiment 02 after evaluation.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The design is approved, smoke is green, and the persisted report exists.
- `review consent` returns `audit`.

**Must do:**
- Run `python -m skore_skills review consent --stem <stem>` before
  the first `materialize.py` run.
- On `audit`, write `audit/<stem>.py` and run
  `scratch/audit/<stem>/materialize.py` once. Do not execute
  `audit/<stem>.py`.
- Confirm the report with `project.summarize()` and load it with
  `project.get(id)`.
- Render checks and metrics into the audit digest.
- Copy `templates/materialize.py` to
  `scratch/audit/<stem>/materialize.py` and run it. It writes
  `scratch/results/<stem>/{report,checks,metrics}.html`. Leave
  the bare Display last on checks in `audit/<stem>.py`. Metrics
  last is `summarize().frame(verbose_name=True, flat_index=False)`,
  and `metrics.html` is that frame's `_repr_html_()`. No second
  text snapshot of the table.
- Write a `help()` tree per namespace to
  `scratch/audit/<stem>/accessors.txt` for the later dig-deeper
  menu. Do not put that loop in the audit notebook.
- Derive G-AUDIT-FINDING by running
  `python -m skore_skills audit finding --stem <stem>` and pasting
  JSON `finding` verbatim.
- Return the digest, JSON `finding`, and `loop locator` JSON. On a
  direct invocation, record the outcome and publish the website
  first, and ask Additional report view / Custom query / Custom
  plot / Move on only after that result is presented.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Describe audit as model training or full CV.
- Call `skore.evaluate` or `project.put`.
- Require the experiment to be `done` before audit.
- Dispatch record-outcome before producing the digest.
- Write the journal directly.
- Write skill ids, `skore_skills`, `cells run`, or API-tutorial
  prose (version floors, `summarize(ignore=…)`, hub locator
  recipes) into `audit/<stem>.py` markdown cells or `#` comments.
- Put snapshot `write_text` calls or the `help()` loop in
  `audit/<stem>.py`. Those belong in
  `scratch/audit/<stem>/materialize.py`.

---

## CASE_02 — Direct audit owns the close

**User prompt:**
> Re-audit experiment 03.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- This is a direct free-text invocation.
- The report exists and smoke is green.

**Must do:**
- Re-run `scratch/audit/<stem>/materialize.py` for the re-audit.
  Do not execute `audit/<stem>.py`.
- Run the direct close (record-outcome, site build, close
  narrative) after the digest, and ask the continuation question
  only after that result is presented.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Paste `scratch/audit/<stem>/audit.md` wholesale into chat.
- Run `loop notebooks` before the digest.
- Call record-outcome before the digest.
- Run `git commit`.

---

## CASE_03 — Dispatched audit returns without a second close

**User prompt:**
> Continue the model loop and audit the evaluated baseline.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `model-ml-pipeline` dispatched `review-ml-experiment`, which
  loaded this audit.
- `materialize.py` already wrote the digest.
- The digest is ready; the user has not seen the result yet.
- Normalized locator is
  `local workspace: [reports/](../reports/) · id: local-report-id`.

**Must do:**
- Return to `model-ml-pipeline`. Naming `audit finding` and
  `loop locator`, plus the digest path, counts when the digest
  body is not in the prompt. Do not invent Checks or Metrics.
- State that the dispatcher owns record-outcome, the notebook
  gate, site, the user-facing close, and git close, and asks the
  continuation question after that.
- Tell the caller to run `python -m skore_skills loop notebooks
  --stem <stem>` and obey `convert` with `notebook fill` before
  record-outcome, then the caller's `git end-turn` (`--stage
  implement` from model, `--stage evaluate` from evaluate).
  Naming `notebook fill` is not that close.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Write the User-facing close (narrative + Open these) here;
  the dispatcher owns it.
- Ask Additional report view / Custom query / Custom plot /
  Move on here.
- Run `git end-turn` or `persist-ml-git` from this skill (naming
  them as the **dispatcher's** close is allowed).
- Load `triage-ml-task` from this skill.
- Dispatch `manage-ml-backlog` from this skill.
- Run `loop notebooks` or `notebook convert` here.
- Treat naming `notebook fill` as finishing the close.
- Treat the close as finished after filling only
  `audit/<stem>.py`.
- Add `<!-- results-embed: audit -->`.

---

## CASE_04 — Missing report stops without fabrication

**User prompt:**
> Audit experiment 04.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The design is approved and smoke is green.
- `project.summarize()` has no row for experiment 04.

**Must do:**
- Stop and report that the persisted report is missing.
- Route recovery to evaluation.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Re-run `skore.evaluate` from audit.
- Invent a report id, URL, metrics, or digest.
- Mark the experiment done.

---

## CASE_05 — Additional audit work loops after the close

**User prompt:**
> Add another audit view.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- The caller already recorded the outcome and published the
  website.
- The initial audit digest exists. `help()` trees are in
  `scratch/audit/<stem>/accessors.txt`, not in the notebook.
- A tree's `Displays` group lists one extra view; `api get` confirms
  that method.
- `policy.notebooks` and `policy.site` are true.

**Must do:**
- Refresh the execution preview for the selected view because it
  materially changes report rendering; do not repeat it before
  every style / execution command.
- Present Additional report view / Custom query / Custom plot /
  Move on in that exact order.
- Offer only accessor names from this turn's `Displays` groups — not
  a remembered Display catalog.
- Confirm the selected accessor with `api get`, append it below
  `## Core audit complete` on the same `audit/<stem>.py` as a bare
  Display, append it to `EXTRA` in `materialize.py`, run style,
  re-run `materialize.py` once, then
  `notebook fill audit/<stem>.py --html`.
- Recompute G-AUDIT-FINDING with `audit finding --stem <stem>`.
- Run `site build --if-stale`, then present the same question
  again; do not record-outcome again.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Guess an accessor or show unavailable disabled choices.
- Run `cells run` or `notebook convert` on `audit/<stem>.py`.
- Run git end-turn or record-outcome from this skill; the
  caller already recorded the outcome.
- Call `evaluate` or `put`.
- Name ROC / confusion_matrix / permutation_importance from docs
  memory when they are absent from this turn's `accessors.txt`
  trees.
- Put the extra-view `write_text` in `audit/<stem>.py`.

---

## CASE_06 — Fired-check advice follows its docs

**User prompt:**
> What should we do about this check?

**Assumed workspace state:**
- The audit digest exists.
- One `Issues:` line is `SKD004`, with a documentation URL.
- That page recommends tuning the decision threshold. It does not
  recommend class weighting or resampling.

**Must do:**
- Read that documentation URL and apply its recommendation:
  tune the decision threshold.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Recommend class weighting or resampling.
- Call `skore.evaluate` or `project.put`.
