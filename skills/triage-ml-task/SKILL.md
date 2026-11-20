---
name: triage-ml-task
description: >
  Session owner: list installed entry skills and ask which to run.
  Load a skill without asking only when the request is certain to
  be that skill. Trigger on an ambiguous request, a finished stage,
  a workspace-open session, or "what should we do next".
metadata:
  role: entry
  modelTier: medium
---

# Triage ML Task

This is the session owner. Stage skills do the work; you only
route and ask. Do not execute another skill's methodology.

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Questions and replies describe the **work** (explore the data,
build a model) — not skill ids, `G-*` names, or the wrapper CLI.
Run `python -m skore_skills …` yourself; do not quote it.

Every question here carries its own context: 2–4 lines on what the
answer authorizes, the workspace facts it rests on — echoed inline
from `status` (scaffold, `data_analysis`, `loop_stage`) — and what
each option leads to. A file link is an addition, never the
context.

## Procedure

1. Run `python -m skore_skills status`. Read `skills`, `data_analysis`,
   `loop_stage`, `setup.pending`, and the filesystem snapshot. If `.skore` is
   missing, that is expected. Do not treat a missing file as an
   empty project when `src/` or `journal/` exist.
2. **Certain request** — load that skill, after the setup gate
   below. Tell the user the work
   you are starting, not the catalog id. Do not list the catalog.
   `status.skills` is a per-id dict. Load the mapped skill only if
   `status.skills.<id>` is true; else one-line skip and do not
   invent that skill's steps:

   **Setup gate for a lifecycle skill.** Before loading
   `explore-ml-data`, `frame-ml-problem`, `model-ml-pipeline`,
   `build-ml-pipeline`, `evaluate-ml-pipeline`,
   `smoke-test-ml-pipeline`, or `audit-ml-pipeline`, read
   `status.setup.pending`. If it is non-empty and
   `status.skills.setup-ml-project` is true, load
   `setup-ml-project` and stop. Tell the user the requested work
   waits on those pieces. Do not show the entry menu. After setup
   returns, load the certain lifecycle skill. Do not load setup
   again on this turn. If `setup.env` or `setup.workspace` is
   `declined`, stop in one line. A declined `git` or `editable`
   does not block. If `setup-ml-project` is not installed, name
   the pending pieces in one line and stop. Do not invent
   `git init`, scaffold, or `env init`. Uncertain sessions skip
   this gate.

   | User intent | Skill |
   |---|---|
   | env / pixi / uv / python environment | `setup-python-env` |
   | scaffold / layout / package folders | `setup-workspace` |
   | git init / first commit / ignore | `setup-git` |
   | add or install a named package | `add-python-package` |
   | exploratory data analysis / explore the data | `explore-ml-data` |
   | evaluate / metrics / CV / run `skore.evaluate` | `evaluate-ml-pipeline` (child gate may STOP) |
   | audit / open / narrate an existing report | `audit-ml-pipeline` (child gate may STOP) |
   | build / model a pipeline | `model-ml-pipeline` |
   | smoke / pytest row-count / why is smoke failing | `smoke-test-ml-pipeline` (debug; does not start evaluate) |
   | backlog / history / record the run / what next | `manage-ml-backlog` |
   | review this stem / review the last experiment | `review-ml-experiment` |
   | I want to try X / here is an idea / what if we / a pasted URL or issue | `shape-user-idea` |
   | papers / literature / what do people do for (no design note in progress) | `search-ml-literature` |
   | notebook / ipynb | `export-ml-notebook` |
   | notebook viewer on the site / executed report | `export-ml-notebook` (`--html`) |
   | website / mkdocs / documentation site | `export-ml-site` |
   | export (generic) | `export-ml-project` |
   | sync / migrate reports / switch skore mode / upload reports to hub or mlflow | `sync-ml-reports` |
   | set up / bootstrap this project (generic) | `setup-ml-project` |
   | “is this leakage” on the table | `explore-ml-data` (even if `data_analysis` is present). Do not load `research-ml-practice`. |
   | research / literature on a modeling design (design note exists or modeling in progress) | `model-ml-pipeline`. Do not load `research-ml-practice`. |
   | which comparison metric / how new rows should be split / which baseline / a problem constraint changed | `frame-ml-problem`. Not a request to run evaluation. |
   | what did we decide / show stored choices / change a stored project choice | `review-ml-choices` |

   An explicit sync, generic export, or changed modeling
   constraint still uses those rows. Do not send them through
   `review-ml-choices`.

   A git init, first commit, or ignore request loads `setup-git`
   and stops. Do not write `git init`, a `.gitignore`, or a commit
   plan. With no shell, the whole answer is that `setup-git` is
   loaded. Do not describe the commands that skill will run.

   "What should we try next?" while `loop_stage` is `backlog` and
   `manage-ml-backlog` is installed loads that skill and stops.
   Do not ask the user to choose explore, build, review, or export.

   Certain EDA: run `python -m skore_skills status`. If
   `status.setup.pending` is non-empty, load `setup-ml-project`
   (setup gate above) and stop. Otherwise load
   `explore-ml-data` and stop. Do not inventory `data/`, list
   missingness or distributions, or start EDA methodology.

   Certain generic export: run `python -m skore_skills status`,
   then load `export-ml-project`. Do not list notebook / `--html`
   / site as sibling options.

   **Modeling while `status.data_analysis` is `missing`:** if the certain
   skill is `model-ml-pipeline` (or the user asked to build the
   first experiment) **and** `status.skills.explore-ml-data` is
   true, do not load modeling yet. **AskUserQuestion** two options:
   run exploratory data analysis first (default) vs proceed to
   modeling with user-supplied facts. Do not invent dataset facts
   here. If `data_analysis` is `present` or `skipped`, load
   `model-ml-pipeline` with no extra gate (still only if that id
   is true).

3. **Uncertain** (open session, “what can you do”, finished stage,
   mixed intent) — run `python -m skore_skills triage choices`.
   Its `choices` array is the board: installed entry work only.
   **AskUserQuestion** with exactly those rows, in order, each
   row's `label` as the option and its `skill` as the load target.
   Do not rebuild the board from memory, add a row, or offer a
   `not_offered` row. One pick, then load that row's `skill` and
   stop.

   When `recommended` is set, say its `recommendation_reason` and
   recommend that row first. Do not auto-load it. When `choices`
   is empty, say in one line that no entry skill is installed (or
   that the install status is unknown) and do not invent a menu.

   The board never includes evaluate, audit, shaping an idea,
   literature search, or internals (`build-ml-pipeline`,
   `smoke-test-ml-pipeline`, `frame-ml-problem`,
   `choose-python-library`, `research-ml-practice`,
   `plot-ml-figure`, stack refs). Certain requests still load
   those.

## Stop conditions

- Do not design experiments, write pipelines, or run exploratory
  data analysis yourself. Certain EDA with `setup.pending` empty
  loads `explore-ml-data` only — no data inventory and no EDA
  checklist. Pending setup loads `setup-ml-project` first.
- Do not load every skill.
- Do not invent workspace facts when status is unavailable.
- Do not treat a missing `.skore` as an empty project when `src/`
  or `journal/` exist.
- Do not invent a missing skill's steps from memory.
- Do not put `evaluate-ml-pipeline` or `audit-ml-pipeline` on the
  uncertain entry board (certain requests still load them).
- Do not offer an entry row that `triage choices` left out of
  `choices`, and do not rebuild the board by hand.
- A missing review, backlog, user-idea, or literature skill is
  a one-line skip. Do not invent that skill's procedure.
- Do not put `shape-user-idea` or `search-ml-literature` on the
  uncertain entry board.
- Do not put `frame-ml-problem` on the uncertain entry board
  (a certain metric, split, baseline, or changed-constraint
  request still loads it).
- Certain generic export: run `python -m skore_skills status`,
  load `export-ml-project` only — no sibling-skill menu.

End of every other skill's turn returns here when this skill is
installed.
