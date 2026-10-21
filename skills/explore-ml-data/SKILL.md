---
name: explore-ml-data
description: >
  Explore the dataset before designing any model. Place
  `data_analysis/data_analysis.py` and do not execute it. Run `materialize.py`
  once, write `data_analysis.md`, and put the short summary in the project
  objective. Never design the model, edit `src/<pkg>/`, edit JOURNAL.md, or
  modify raw data files.

  TRIGGER when the user asks to explore, profile, or understand the data;
  triage sent them here (`status.data_analysis` missing); a data source
  changed; they want to refresh a recorded EDA; or leakage or research arises
  on a recorded EDA.

  STOP when `status.setup.pending` is non-empty (load `setup-ml-project`),
  when there is no data (send to triage), the request is not raw-data
  exploration, or EDA is recorded with no refresh and no methodology concern.
  Do not invent a package root or a root `JOURNAL.md` while setup is pending.

  HOW TO USE: G-TABULAR via `add-python-package`, infer or ask the targets,
  load `plot-ml-figure` if installed, then ask the five-option continuation
  board, including Close.
metadata:
  modelTier: medium
---

# Explore ML Data

Keep writing `data_analysis/data_analysis.md`. Put the short summary in the
project with `python -m skore_skills objective set "<summary>"`. Do not edit
`JOURNAL.md`. The analysis files may live in a temporary directory.
If a later step says to edit `JOURNAL.md`, skip that step and use
`objective set`.

One project-level exploratory data analysis: a notebook the user
can open, HTML reports, a short `data_analysis.md` that embeds
them, and a JOURNAL index row.

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Notebook markdown, `data_analysis.md`, JOURNAL text, and `#`
comments describe **this** dataset — not the skills framework, the
CLI, or the command that produced an output. Questions, replies,
and the close narrative use the same data-science language — not
skill ids, `G-*` names, or the wrapper CLI.
`<!-- results-embed: … -->` is a site marker. Authoring hints stay
in this skill. `style` is ruff only.

## Artifacts

| Path | Audience |
|---|---|
| raw data (anywhere) | User-owned, **read-only** |
| `data_analysis/data_analysis.py` | Human notebook — TableReport + ML-gap cells |
| `data_analysis/data_analysis_<slug>.html` | Human — TableReport page, one per family |
| `data_analysis/*.png` | Human — figures for implications, never glance |
| `data_analysis/<slug>.html` | Human — Plotly (or other) HTML, iframe in implications |
| `data_analysis/data_analysis.md` | Human + later modelling — TableReport iframes, implications |
| `scratch/data_analysis/materialize.py` | Agent — the only run; gitignored |
| `scratch/data_analysis/<slug>.json` | Agent — `TableReport.json()` per family; gitignored |
| `scratch/data_analysis/extras.json` | Agent — `tables[]`, `targets`, leakage, png and html paths |
| JOURNAL § Data understanding | Index: status, 2–4 line summary, link |

TableReport owns dtypes, missingness, univariate distributions,
cardinality, and top pairwise associations. Extra cells cover
duplicates, each target's distribution, feature-vs-target, and
leakage candidates. Sibling targets are not features. Do not
duplicate TableReport in extra cells.

Details: `references/cell_anatomy.md`. Extra recipes:
`references/extra_analyses.md`.

## Next-step pointers

| You came here for… | → next |
|---|---|
| First EDA (triage or free-text) | → write md; then the five-option continuation board |
| Continuation pick | → pre-defined option, query, automatic exploration, or describe a plot; no end-turn yet |
| Close this stage | → fill / site / git end-turn / `triage-ml-task` if installed |
| Methodology concern while EDA is done | → skip G-DATA-ANALYSIS; Keep exploring § Automatic exploration (named concern skips the canned survey) |
| Changed data source or "also plot X" | → overwrite `data_analysis/data_analysis.*`, refresh JOURNAL |

## Stop conditions

- **Setup first.** Run `python -m skore_skills status`. If
  `status.setup.pending` is non-empty and
  `status.skills.setup-ml-project` is true, load
  `setup-ml-project` and stop. Do not start this skill. When it
  returns, continue. Do not load it again on this turn. If that
  skill is not installed, name the pending pieces in one line
  and stop. Do not invent `git init`, scaffold, or `env init`.
  If `status.setup.env` or `status.setup.workspace` is
  `declined`, stop in one line. A declined `git` or `editable`
  is not asked again; continue. Do not define `PROJECT_ROOT` by
  hand or write a root `JOURNAL.md` while workspace setup is
  pending.
- **Read-only raw data.** Never clean, rewrite, or re-save the
  user's files. Never tell the user to drop a column or file
  (“drop it”). Leakage stays Open questions / a `measure`
  board. Cleaning belongs in `build-ml-pipeline`.
- **Deliverables under `data_analysis/`.** Raw load may point
  anywhere.
- **Every ask carries its context.** Before any AskUserQuestion in
  this skill, state in 2–4 lines what the answer authorizes, the
  facts it rests on — echoed inline, e.g. the file names, the
  candidate columns, the proposed family slugs — and what each
  option does. A file link is an addition, never the context.
- **G-DATA-ANALYSIS run | skip.** AskUserQuestion. "Go fast" does
  not skip. Skip →
  `python -m skore_skills eda stamp --status skipped`
  and stop. Do not type the date.
  Skip is valid only when `data_analysis/data_analysis.md` is
  absent (`status.data_analysis` `missing` or `skipped`). If
  status is `present`, do not write `skipped`. Say the written
  analysis stays, and offer to run exploration again (overwrites
  `data_analysis/data_analysis.*`) or keep it. Do not overwrite
  until the user accepts the re-run. A named methodology concern
  while EDA is done still skips this gate. Do not run `site
  build` on skip. The unfitted snapshot build in
  `build-ml-pipeline` still runs before Evaluate.
- **G-TABULAR before `data_analysis/data_analysis.py`.**
  `status.policy.tabular`; else `choose-python-library` (recommend
  pandas) then `add-python-package` for that lib **and** `skrub`,
  `matplotlib`, and `seaborn`. No silent default. A Graphviz
  repair diagnostic from that `skrub` install does not discard
  this analysis. Quote it in one line and continue. The unfitted
  snapshot in `build-ml-pipeline` is what requires a renderable
  graph. If G-TABULAR,
  targets, or families are unanswered, **stop after the asks** —
  no default-path notebook, even as a “Deliverable A assuming
  pandas.” Do not install sklearn / skore / pytest unless the
  user picked an extra that needs them.
- **Targets.** Infer from JOURNAL Status / the user prompt when
  the columns are obvious, including every named output. Otherwise
  AskUserQuestion `allow_multiple` (column names plus "no target
  yet") and **stop** — write no notebook yet. "no target yet" is
  exclusive. Do not list feature-vs-target / leakage as always-on
  next steps. A numeric column with many distinct values is
  regression. A column with few labels, or non-numeric labels, is
  classification. One column → that one target snippet. Two or
  more regression columns are one multi-output regression: append
  `templates/target_multioutput_regression.py` once. Several
  classification columns, or a mix of classification and
  regression, are not a joint model skore can report: record each
  column and its task, and do not append that snippet. After
  “no target yet” or Decline → `TARGETS=[]`. TableReport +
  duplicates only. Do not persist a policy key.
- **No train/test split.** The modeling-decisions lock owns that
  choice later. Do not split during EDA. If the files already
  are a training table and a test table, name both in the
  summary and do not concatenate them. Exploration does not
  choose the evaluation.
  Leakage cells are qualitative flags on the raw family that
  holds every target. Further families use `templates/family.py`
  only (TableReport + duplicates) — no leakage / target /
  bivariate cells on a family that does not hold the targets.
  Do not persist a joined modeling table.
- **Families before the notebook.** More than one data file →
  AskUserQuestion grouping (none recommended): Use a proposed
  grouping / Profile every file separately / I will describe
  the   grouping. Propose clusters from extension, name pattern,
  or a header/schema peek; generic slugs (`family_a`). Inventing
  families means writing them before the answer, not proposing
  those slugs in the ask. One file → skip this ask.
- **`api get` this turn** for symbols used (cache hits count).
  `TableReport.json()` keys drift — `.get(...)`.
- **One `data_analysis/data_analysis.py`.** Repeat the
  TableReport cell per confirmed family (or per file if the
  user picked that). Re-run overwrites in place. Default
  notebook = those templates only (plus the matching target
  snippet). Do not add extra histograms, `sns.heatmap` /
  association matrices, unique-ratio (`nunique()/n`),
  column-dicts, or `report.json()` cells. The duplicate cell
  prints the duplicate count only, not a uniqueness percentage
  and not `nunique()/n`. Leakage is the
  template table, not a comment. One target: seaborn `displot`
  inside `templates/target_regression.py` /
  `target_classification.py` (describe + one target figure) and
  one faceted `relplot` → `bivariate_grid.png`. Several
  regression targets: `templates/target_multioutput_regression.py`
  once (`target_distributions.png`, `bivariate_targets.png`).
  Do not copy a single-target snippet beside it, and do not
  invent another target histogram next to `TableReport`. Last
  expression `g`. Do not `import matplotlib.pyplot` on the
  default path.
- **Do not design the model.** Implications in
  `data_analysis.md` only.
- Do not gitignore `data_analysis/`. Ignore specific raw patterns
  via `setup-git` if the user asks (default: don't).

## Pre-flight

```
- [ ] Setup: pending empty | load setup-ml-project and stop
- [ ] Detect: status.data_analysis present|skipped|missing
- [ ] G-DATA-ANALYSIS: run | skip when the analysis file is absent (skip → JOURNAL only, STOP). present → keep or re-run; never write skipped
- [ ] G-TABULAR + add frame lib + skrub + matplotlib + seaborn
- [ ] Targets: inferred | AskUserQuestion | none
- [ ] Families: one file | AskUserQuestion grouping
- [ ] Load plot-ml-figure if installed; place
      data_analysis/data_analysis.py from the template (edit to
      the live path); do not execute it
- [ ] scratch/data_analysis/materialize.py once → HTML, figures,
      <slug>.json per family, extras.json
- [ ] notebook fill when policy.notebooks is true
- [ ] Author data_analysis.md + JOURNAL
- [ ] Preview `site build` if `policy.site` (skip on G-DATA-ANALYSIS skip)
- [ ] AskUserQuestion five options, including Close (skip if user
      already closed the turn)
```

Tick, then run the matching step. Re-emit the checklist with
evidence. End of turn only after Close.

## Before execution

After G-DATA-ANALYSIS, G-TABULAR, targets, and families are
resolved, emit 1–3 natural sentences immediately before the
first write. Say that this is **local
computation**: it profiles the confirmed full table family or
families, runs duplicate / target / bivariate / leakage analyses
that apply, and writes `data_analysis/` HTML / figures plus
`scratch/data_analysis/` JSON facts. Name the data scope and the
report paths; do not dump Pre-flight as the explanation.

Describe cost from facts, not guesses. TableReport and requested
plots scale with table size and number of families; unless a
measured duration is already available, say timing depends on
those inputs and do not invent minutes. Emit this preview once,
not before every edit; refresh it only when a newly
selected extra materially changes the work.

Automatic exploration / a methodology discussion is **LLM
research**, not model fitting or testing: say that it will reason
over the recorded EDA, may write a scratch research note, and
will stop at a measurement-choice board before local analysis.
If a mandatory gate is pending, preview the possible work but do
not write or execute the notebook.

## Procedure (run path)

1. Resolve `TARGETS` and one task per column (`classification`
   | `regression`) first. An empty list is no target. Two or
   more regression columns are multi-output regression. Resolve
   families (stop condition above). Copy
   `templates/data_analysis.py` if it fits, then **edit**
   — do not paste unused branches. The first family is the one
   that contains every target when any exist; substitute
   `<pkg>`, `<LOAD_RAW_DATA>` (in-memory concat of that family's
   shards; optional `_source_file`), `<slug>` (Python
   identifier). Each further family → `templates/family.py` (`<OTHER_SLUG>`,
   `<LOAD_OTHER>`). One target → append
   `templates/target_regression.py` **or**
   `templates/target_classification.py` and set `TARGET` in the
   first-family load cell. Two or more regression targets →
   append `templates/target_multioutput_regression.py` once and
   set `TARGETS` to that list. No target, several classification
   columns, or a mix → none of those snippets and no `TARGET` /
   `TARGETS` assignment. Datetime columns on a family →
   `templates/datetime.py` for that family (drop the relplot
   cell unless there is exactly one numeric target). Two
   families that share column names → `templates/drift.py` with
   `<OTHER_FRAME>`. Disjoint schemas → no drift on the default
   pass. Do not append join-coverage cells here. Generated
   notebook must not contain `if TARGET`, `if TASK`,
   `OTHER = None`, empty datetime loops, or “skip this cell”.
   Load `plot-ml-figure` if installed **before** writing figure
   cells (including this first write). Markdown is about
   **this** analysis. `python -m skore_skills style` after the
   write. Do not execute this file.
2. Copy `templates/materialize.py` to
   `scratch/data_analysis/materialize.py`. Substitute `<pkg>`,
   `<TARGETS>`, `<TASKS>`, and the `<ANALYSIS>` block: the same
   loads, `TableReport.write_html` calls, and figure or HTML
   saves as the human file. `<TARGETS>` is a list of column
   names (`[]` when there is no target). `<TASKS>` is the
   parallel list of `classification` | `regression`, including
   columns that have no joint snippet. One load per family.
   Bind `FAMILIES` as `(slug, raw)` and `FRAME` to the pandas
   frame that contains every target. Leave the tail. Run that
   file once.
   It writes the TableReport HTML, figures, `<slug>.json`, and
   `extras.json`. Do not execute
   `data_analysis/data_analysis.py`. Do not `notebook convert`
   it and do not `cells run` it. Read `<slug>.json` and
   `extras.json`.
3. Read `status.policy.notebooks` and `status.policy.site`.
   When notebooks is `true`, run
   `python -m skore_skills notebook fill
   data_analysis/data_analysis.py`, adding `--html` only when
   site is also `true`. Fill does not execute the file. It
   needs jupytext and nbformat, not nbclient, ipywidgets, or
   IPython. When notebooks is `null` or `false`, do not change
   policy and do not fill. `materialize.py` is still the only
   run.
4. Write `data_analysis/data_analysis.md` from
   `templates/data_analysis.md`: glance (one iframe per family
   and nothing else), modelling implications (include
   feature-engineering *candidates*), open questions. Reports
   and figures are embedded, not linked; `![](<name>.png)` or an
   HTML iframe (`<iframe src="<slug>.html" …>`) sits beside the
   implication it supports, never in the glance. Glance stays
   TableReport-only. Every `extras["pngs"]` and `extras["htmls"]`
   path is embedded, each with a sentence citing numbers from
   those JSON files (or a notebook summary table). Do not save a
   figure that earns no such sentence.
   Ground claims in both JSON files and the HTML. Do not invent
   columns.
5. JOURNAL § Data understanding table: run
   `python -m skore_skills eda stamp --status done` for the Status
   cell. Do not type the date. Write the short summary (shape,
   each target's balance or skew, one or two findings that shape
   modelling)
   and Report
   `[data_analysis/data_analysis.md](../data_analysis/data_analysis.md)`.
   Skip path: `eda stamp --status skipped` only. Do not fill or
   `git end-turn` on skip.
6. **Continuation board** — unless the user already closed
   the turn (“EDA is done”, “close the turn”): if `policy.site`
   is true and `export-ml-site` is installed, run
   `python -m skore_skills site build --if-stale` first. Skip in one line
   otherwise. If `site build` errors with `mkdocs-material is
   required`, load `add-python-package` for `mkdocs-material`
   (agent) and build once more. Do not `pixi add` / `uv add`.
   If that skill is missing, or the retry still fails, name the
   error in one line. Name a build error; do not fail the gate.
   When the build ran or reported the site current, say the
   website has been updated and paste the `file://` line from
   that output verbatim. Do not name `data_analysis.md` or
   `html/data_analysis.html`. Do not
   `notebook fill` or `git end-turn` on this preview. Then
   **AskUserQuestion** one pick. None is recommended or
   preselected. After the first md, always ask (including
   when triage sent you here). Do not say “extra-analyses” or
   “standard extra analysis” on this board.

   | Label | Subtitle |
   |---|---|
   | Choose additional pre-defined option | Name only items that apply: interactions / pairplot, PCA, hypothesis tests, subgroup, time-series, text or geo, join keys / coverage (2+ families) |
   | Provide a query to extend the exploration | Describe an analysis to add to the notebook (table, test, or plot) |
   | Automatic exploration related to the data and problem | Do in-depth research related to the problem and data that we are exploring |
   | Describe a plot | You name a chart and I add cells for it |
   | Close | End this stage. Do not add another analysis. |

   Close → End of turn (User-facing close). Do not rewrite
   `data_analysis.md` on Close. The other four picks go to
   **Keep exploring** and do not ask this board again for the
   same pick. Duplicate / target / leakage stay in Modelling
   implications, not only Open questions.

If the original prompt already named extras (e.g. PCA), include
those cells in step 1 and do not re-ask that extra.

Import failures → `add-python-package`, do not work around.

Refresh (already `done`, user asks for more plots): edit the
human file and the `<ANALYSIS>` block, run `materialize.py`
once, fill when notebooks are on, then steps 4–6. Do not re-ask
G-DATA-ANALYSIS.

Methodology concern while `status.data_analysis` is present
(leakage / “research this”): skip G-DATA-ANALYSIS; do not
overwrite the notebook; go to **Keep exploring** § Automatic
exploration with that named concern (skip the canned
extra-analysis survey).

Always load `plot-ml-figure` if installed before writing or
rewriting figure cells. The template is not a license to skip
the plotting worker. Missing skill → one-line skip and still
follow that tree (seaborn statistical, pandas simple chart,
matplotlib last). Never `plt.close` in notebook cells: save PNG
then leave the figure/grid as the cell output.

## Keep exploring

No separate export pass and no `git end-turn`. Editing the human
file also edits `<ANALYSIS>`, then `materialize.py` runs once
and fill runs when notebooks are on. Do not run a **second**
site build until the md is rewritten. Do not say “extra-analyses”
or “standard extra analysis” **anywhere this turn** (chat,
checklists, or the board). The file
`references/extra_analyses.md` may be named as a path only.
The continuation board was already asked. Handle the picked
label. Do not ask keep-versus-close, and do not repeat the
board for this pick.

1. **Pre-defined option** — the recipe file
   `references/extra_analyses.md` (path only; do not say
   “extra-analyses” in chat). Its own `allow_multiple` board.
   The question's last line is exactly: Select each one you want.
   Write nothing after that line. Load
   `plot-ml-figure` if installed before figure cells.
2. **Query** — wait for the user’s analysis request. Append
   cells (load `plot-ml-figure` if a figure). Not the canned
   research survey. Then the refresh step.
3. **Automatic exploration** — load `research-ml-practice`
   if installed with stage `data_analysis` and the canned
   survey concern below. Missing skill → one-line skip and
   re-ask the five-option board without another `site build`.
   Do not ask intake. Pass JOURNAL,
   `data_analysis.md` (implications + open questions), and
   `scratch/data_analysis/extras.json` as **context**. The
   worker abstracts the **problem class** (no dataset proper
   name) before searching. Canned question:

   > Given the kind of problem in JOURNAL (domain, task,
   > constraints) and the kinds of structure already seen in
   > EDA (not the dataset’s proper name), what extra
   > measurements on a raw table like this are still worth
   > doing?

   Read `scratch/research/survey-<slug>.md`. Summarize in
   chat; do not dump the note. If tools did not run, two
   sentences on the **named concern** (for leakage:
   provenance / scoring-time availability) plus the
   `measure` board — do not claim a scratch file was read.
   Do not say to drop a raw column. **AskUserQuestion**
   `allow_multiple` on **only** sourced **`measure`** extras
   that are not already in the notebook. No option starts
   selected. The question's last line is exactly: Select each
   one you want. That line ends the message: no checklist
   after it.
   Map onto extra_analyses when a recipe exists; else a
   custom cell. `declare` / `evaluate` / `confirm` stay off
   this board → Open questions as advice, not findings. Do
   not copy Open questions onto the board unless the survey
   note listed them with a source.

   A user-named methodology concern (leakage / “research
   this”) skips the canned survey: pass that concern for
   **depth**, then the same **`measure`** board. Summarize
   as above if tools did not run; do not say to drop a raw
   column.
4. **Describe a plot** — load `plot-ml-figure` if installed;
   append cells.
5. Picks that change the `.py`: `style`, edit the `<ANALYSIS>`
   block to match, run `materialize.py` once, then `notebook fill`
   when notebooks is `true` (`--html` only when site is also
   true). Rewrite `data_analysis.md` from JSON/PNGs/HTML
   (implications from **results**). Then preview `site build` if
   `policy.site` and re-ask the five-option board (run path
   step 6). Do not invent domain checklists.

## Dispatch

Called from `triage-ml-task` (explore-the-data intent, or
explore-first on a modeling request while `data_analysis` is
missing) and user free-text.

Calls: `add-python-package`, `api get`, `choose-python-library` /
stack for G-TABULAR, `research-ml-practice` if installed when the
user wants extra-analysis research or a named methodology
concern, `plot-ml-figure` if installed before **any** figure
cells (default notebook, extras, free-text, research-`measure`),
`style` after `data_analysis.py`.

Need a package? Load `add-python-package` if installed; else name
it and stop. Do not `env add` here.

## End of turn

Run this block **only after Close** (or when the user already
closed the turn). Keep exploring never reaches here. Do not
rewrite `data_analysis.md` in this block.

### User-facing close

The user-facing message is a short story plus links. It is not
Pre-flight, not a dump of markdown, and not JOURNAL table cells
alone. Do not name `site build`, `--if-stale`, or other wrapper
commands in that message.

1. **Narrative first** — 2–6 sentences of findings for this
   stage, grounded in Modelling implications / the JSON facts
   (shape, targets, leakage or duplicates that shape modelling).
   Do not invent columns. Do not paste `data_analysis.md`.
2. **Open these** — when `site build` ran or reported the site
   current, say the website has been updated and paste the
   `file://` line from that output verbatim. Do not name the
   markdown or
   `html/data_analysis.html`. When the site was not built, do
   not claim it was updated and do not name the markdown.
   No Skore locator on this stage.
3. **Normalized tokens second** — none for EDA (no
   G-REPORT-LOCATOR / G-AUDIT-FINDING).

This skill owns the close. Keep exploring stays a 1–2 sentence
summary (when a build ran: the website has been updated and
the pasted `file://` line); it never reaches fill /
`git end-turn`.

If `policy.notebooks` is true, `export-ml-notebook` is installed,
and this run did not already write a current notebook, run
`python -m skore_skills notebook fill
data_analysis/data_analysis.py`, with `--html` when `policy.site`
is also true. A notebook produced by run-path step 3 is current:
do not fill it again merely because the user picked Close.
Do not re-run `materialize.py` when the artifacts are already
from this human file. Skip in one line otherwise. Missing
jupytext / nbformat / nbconvert → one-line skip naming
`add-python-package`; do not fail the turn, do not `pixi add`.

Then, if `policy.site` is true, `export-ml-site` is installed, run
`python -m skore_skills site build --if-stale` after durable files are on
disk. Skip in one line otherwise. If `site build` errors with
`mkdocs-material is required`, load `add-python-package` for
`mkdocs-material` (agent) and build once more. Do not
`pixi add` / `uv add`. If that skill is missing, or the retry
still fails, name the error in one line. Name a build error;
do not fail the data-analysis turn. When the build ran, say
the website has been updated and paste the `file://` line from
that output verbatim. Do not name the markdown or
`html/data_analysis.html`.

`python -m skore_skills git end-turn --stage data_analysis`. If
JSON `action` is `invoke`, load `persist-ml-git` only if
`status.skills.persist-ml-git` is true and stop; that skill
returns to triage. If persist is missing, name the pending
`staged` paths and stop. Otherwise load `triage-ml-task` only if
`status.skills.triage-ml-task` is true; else stop. No `git
commit`.
