# triage-ml-task eval

---

## CASE_01 — Ambiguous capability request

**User prompt:**
> What can you help me with on this machine learning project?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Existing scaffold with no specific task requested.
- No `.skore` file.
- `status.data_analysis` is `missing`.
- `status.skills` reports the usual entry skills `true`, including
  `review-ml-experiment` and `review-ml-choices`.

**Must do:**
- Run `python -m skore_skills status`.
- Use the `triage choices` JSON. Do not rebuild which rows are
  offered.
- AskUserQuestion with the eight installed entry rows, human
  labels only. One pick. Do not put skill ids on the labels.
- Recommend exploring the data first, using
  `recommendation_reason`; do not auto-load it.
- Do not treat the missing `.skore` as an empty project despite
  the existing scaffold.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Start designing the next experiment.
- Claim to have loaded or executed every skill.
- Auto-load a stage skill without asking.
- Ask only stay / go deeper / next stage without offering the
  entry work.
- Put `evaluate-ml-pipeline` or `audit-ml-pipeline` on the
  uncertain entry board.
- Put `shape-user-idea` or `search-ml-literature` on the
  uncertain entry board.
- Auto-load `review-ml-experiment` while `data_analysis` is
  `missing`.

---

## CASE_02 — Certain git request

**User prompt:**
> Initialize git here.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace, no `.git`.
- `status.skills.setup-git` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `setup-git` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Ask which entry skill to run.
- Invent `git init` procedure in triage instead of loading
  `setup-git`.

---

## CASE_03 — Git skill not installed

**User prompt:**
> Initialize git here.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.skills.setup-git` is `false`.

**Must do:**
- Skip in one line because `setup-git` is not installed.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Run `git init` or invent the `setup-git` procedure from memory.
- Treat the missing skill as an error that aborts the session.

---

## CASE_04 — Generic bootstrap

**User prompt:**
> Bootstrap this project for me.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Empty folder.
- `status.skills.setup-ml-project` is `true`.
- `status.skills.setup-python-env` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `setup-ml-project` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `setup-python-env` as the certain skill.
- Ask which entry skill to run.

---

## CASE_05 — Certain env manager request

**User prompt:**
> Get pixi going for this folder.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Empty folder.
- `status.skills.setup-python-env` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `setup-python-env` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `setup-ml-project` as the certain skill.
- Ask which entry skill to run.

---

## CASE_06 — Certain EDA request

**User prompt:**
> Explore the data in data/.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace with `data/` present.
- `status.skills.explore-ml-data` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `explore-ml-data` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Ask which entry skill to run.
- Start exploratory data analysis methodology in triage instead of
  loading the skill. Saying the request routes to exploration and
  that the exploration skill is loaded next turn is not starting
  the methodology. Writing profiling steps is.

---

## CASE_07 — Model request while EDA is missing

**User prompt:**
> Build the first baseline model.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.data_analysis` is `missing`.
- `status.skills.explore-ml-data` is `true`.
- `status.skills.model-ml-pipeline` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- AskUserQuestion: run exploratory data analysis first (default) vs proceed to modeling
  with user-supplied facts.
- Do not invent dataset facts.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Auto-load `model-ml-pipeline`.
- Auto-load `explore-ml-data` without asking.

---

## CASE_08 — Model request after EDA is present

**User prompt:**
> Build the first baseline model.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.data_analysis` is `present`.
- `status.skills.model-ml-pipeline` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `model-ml-pipeline` without an exploratory data analysis AskUserQuestion.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Ask which entry skill to run.
- Load `explore-ml-data` first.

---

## CASE_09 — Certain notebook request

**User prompt:**
> Give me an executed ipynb of the EDA.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.skills.export-ml-notebook` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `export-ml-notebook` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `export-ml-project` as the certain skill.
- Ask which entry skill to run.

---

## CASE_10 — Certain website request

**User prompt:**
> Build the MkDocs documentation site.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.skills.export-ml-site` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `export-ml-site` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `export-ml-project` as the certain skill.
- Ask which entry skill to run.

---

## CASE_11 — Generic export

**User prompt:**
> Export the project.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.skills.export-ml-project` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `export-ml-project` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `export-ml-notebook` as the certain skill.
- Ask which entry skill to run.

---

## CASE_12 — Certain HTML notebook request

**User prompt:**
> Give me an HTML notebook of the EDA.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.skills.export-ml-notebook` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `export-ml-notebook` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `export-ml-project` as the certain skill.
- Load `export-ml-site` as the certain skill.
- Ask which entry skill to run.

---

## CASE_13 — Certain leakage question routes to explore

**User prompt:**
> Research whether 0.97 correlation with the target is leakage.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- The question is about the table (`data_analysis` may be
  `present` or `missing`).
- `status.skills.explore-ml-data` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `explore-ml-data` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `research-ml-practice` as the certain skill.
- Put `research-ml-practice` on the uncertain entry board.
- Ask which entry skill to run.

---

## CASE_14 — Certain research during modeling routes to model

**User prompt:**
> Research whether target encoding is the right transform for
> this high-cardinality column.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- An approved design note exists; modeling is in progress.
- `status.skills.model-ml-pipeline` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `model-ml-pipeline` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `research-ml-practice` as the certain skill.
- Load `explore-ml-data` as the certain skill.
- Ask which entry skill to run.

---

## CASE_15 — Certain audit loads audit, not the meta skill

**User prompt:**
> Audit experiment 02.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.skills.audit-ml-pipeline` is `true`.
- `status.skills.model-ml-pipeline` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `audit-ml-pipeline` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `model-ml-pipeline` as the certain skill.
- Ask which entry skill to run.

---

## CASE_16 — Certain report sync loads sync-ml-reports

**User prompt:**
> Push our skore reports to Hub.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.skills.sync-ml-reports` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `sync-ml-reports` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `evaluate-ml-pipeline` as the certain skill.
- Load `review-ml-choices`.
- Ask which entry skill to run.

---

## CASE_17 — Certain next-experiment request loads the backlog

**User prompt:**
> What should we try next?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `status.data_analysis` is `present`.
- `loop_stage` is `backlog`.
- `status.skills.manage-ml-backlog` is `true`.
- `journal/ideas/` has one idea file.

**Must do:**
- Run `python -m skore_skills status`.
- Load `manage-ml-backlog` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `review-ml-experiment` or `audit-ml-pipeline`.
- Design the next experiment in triage. Restating the user's
  request, or saying the backlog will turn the existing idea
  into the next step, is not that design.
- Ask which entry skill to run.

---

## CASE_18 — Backlog stage recommends the backlog skill

**User prompt:**
> What can you help me with on this machine learning project?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `status.data_analysis` is `present`.
- `loop_stage` is `backlog`.
- `status.skills.manage-ml-backlog` is `true`.
- The usual entry skills are `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Use the `triage choices` JSON. Do not rebuild which rows are
  offered.
- AskUserQuestion with the installed entry rows, including
  Record / decide what next and Review the last experiment. One
  pick.
- Recommend recording the run / deciding what next, using
  `recommendation_reason`. Do not auto-load it.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Auto-load `manage-ml-backlog`.
- Put `audit-ml-pipeline` on the uncertain entry board.
- Start designing the next experiment.

---

## CASE_19 — Missing backlog skill still offers the other entries

**User prompt:**
> What should we try next?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `loop_stage` is `backlog`.
- `status.skills.manage-ml-backlog` is `false`.
- The other usual entry skills are `true`.

**Must do:**
- Use the `triage choices` JSON. Do not rebuild which rows are
  offered.
- Say in one line that `manage-ml-backlog` is not installed.
- Offer the other installed entry points, each with a short
  description.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Invent idea-file triage (promote / discard / set aside).
- Load `review-ml-experiment` from memory. A one-sentence
  description of review, build, or explore is not loading that
  skill. Writing the review steps as this turn's work still is.

---

## CASE_20 — Certain review request loads review

**User prompt:**
> Review experiment 02.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `status.skills.review-ml-experiment` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `review-ml-experiment` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `audit-ml-pipeline` from triage.
- Ask which entry skill to run.
- Write a design note in triage.

---

## CASE_21 — Certain idea loads shape-user-idea

**User prompt:**
> I want to try a monotonic constraint on the target.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `status.skills.shape-user-idea` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `shape-user-idea` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `search-ml-literature`.
- Ask which entry skill to run.
- Write a design note in triage.

---

## CASE_22 — Certain literature query loads literature search

**User prompt:**
> What do people do for censored regression?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- No design note is in progress.
- `status.skills.search-ml-literature` is `true`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `search-ml-literature` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `research-ml-practice`.
- Load `model-ml-pipeline` as the certain skill.
- Invent papers in triage.

---

## CASE_23 — Certain stored-choice request loads the board

**User prompt:**
> What did we decide for this project?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffolded workspace.
- `status.skills.review-ml-choices` is `true`.
- `policy.skore_mode` is `local`.

**Must do:**
- Run `python -m skore_skills status`.
- Load `review-ml-choices` without listing the catalog menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `sync-ml-reports` as the certain skill.
- Ask which entry skill to run.

---

## CASE_24 — Certain EDA on a fresh folder

**User prompt:**
> Explore the data in data/.

**Assumed workspace state:**
- The folder contains only `data/` (one CSV). No `src/`, no
  `journal/`, no `.git`, and no env manifest.
- `status.setup.pending` is `env`, `workspace`, `git`.
- `status.setup.env` and `status.setup.workspace` are `missing`,
  not `declined`.
- `status.skills.explore-ml-data` is true.
- `status.skills.setup-ml-project` is true.

**Must do:**
- Run `python -m skore_skills status`.
- Load `setup-ml-project` and stop. Tell the user exploration
  waits on those pieces.
- Do not show the entry menu.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `explore-ml-data` before setup returns.
- Start exploratory data analysis methodology.
- Ask which entry skill to run.

---

## CASE_25 — Loop pack leaves the setup row off the board

**User prompt:**
> What can you help me with on this machine learning project?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Existing scaffold with no specific task requested.
- `status.data_analysis` is `missing`.
- The `loop` workflow pack is installed: `triage choices` returns
  `choices` for Explore the data, Build a model, Review the last
  experiment, Record / decide what next, Export, Sync reports,
  and Review choices.
- `status.skills.setup-ml-project` is `false`; `not_offered`
  carries that row as "setup-ml-project not installed".

**Must do:**
- Run `python -m skore_skills status`.
- Use the `triage choices` JSON. Do not rebuild which rows are
  offered.
- AskUserQuestion with exactly the seven installed entry rows.
  One pick. Do not put skill ids on the labels.
- Recommend exploring the data first, using
  `recommendation_reason`; do not auto-load it.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Offer "Set up the project" or load `setup-ml-project`.
- Load a skill the board left out.
- Auto-load a stage skill without asking.
