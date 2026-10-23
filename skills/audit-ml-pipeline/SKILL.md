---
name: audit-ml-pipeline
description: >
  Audit a persisted skore report read-only and produce a reusable digest. Do
  not execute it. Run `materialize.py` once. Never call `skore.evaluate` or
  `project.put`.

  TRIGGER when a completed run needs an audit, the user asks to audit, show,
  or re-audit an experiment, a re-run overwrote the same `put()` key, or they
  want a narrative of a past experiment without `journal/ideas/` files.

  STOP when `status.setup.pending` is non-empty (load `setup-ml-project`), or
  when there is no approved design, no report, or no agent feature: explain
  and send the user to setup, `evaluate-ml-pipeline`, or `model-ml-pipeline`.
  Also stop for raw-data exploration or sourcing a future experiment.

  HOW TO USE: confirm journal, experiment, smoke, and report; place the file
  from `templates/audit.py`; copy `templates/materialize.py` to scratch;
  execute once; derive G-AUDIT-FINDING; then the continue-or-close gate.
  Resolve skore symbols with `api get`.
metadata:
  role: helper
  modelTier: medium
---

# Audit ML Pipeline

Per-experiment, human-readable narrative of a skore report. The
`# %%` file is the human notebook and is not executed. `materialize.py`
writes the digest and the HTML viewers in one run. Read-only against
the skore Project.

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Audit markdown and `#` comments describe **this** report's findings
— not the skills framework, the CLI, or the command that produced
an output. Questions, replies, and the close narrative use the
same data-science language — not skill ids, `G-*` names, or the
wrapper CLI. Trailing locator tokens stay index strings. Do not
put API tutorials, version floors, or locator recipes in
`audit/<stem>.py`. `<!-- results-embed: … -->` is a site marker.
Authoring hints stay in this skill. `style` is ruff only.

## Next-step pointers

| Came here from… | After audit, next is… |
|---|---|
| `model-ml-pipeline` (implement loop) | → Return. This audit execution may already materialize its notebook. The caller runs `python -m skore_skills loop notebooks --stem <stem>` as a freshness gate before record-outcome, then site build and `git end-turn --stage implement`. |
| User free-text ("audit 02", "re-audit 04") | → Surface metrics, then own the close (see § End of turn) |
| Re-run of an existing experiment | → Re-execute the existing audit file; surface diff if metrics changed |

The implement loop dispatches audit **after evaluate and before
record-outcome**. The digest carries the checks summary and metrics
summary. G-AUDIT-FINDING is a separate normalized finding derived
from that digest. `manage-ml-backlog` record-outcome consumes both
and never dispatches audit back.

## Where things live — visual map

| Path | Durability | Who writes it | What it holds |
|---|---|---|---|
| `audit/<NN>_<short_name>.py` | **Durable** (in git) | This skill, once per experiment | The bare-expression cells. Source of truth. Not executed by the agent. The site notebook is this file with empty outputs |
| `scratch/audit/<stem>/audit.md` | Ephemeral (gitignored) | `materialize.py` | `repr` of the checks display and the metrics frame. `audit finding` parses this |
| `scratch/results/<stem>/materialize.py` | Ephemeral (gitignored) | Evaluate, from `evaluate-ml-pipeline/templates/materialize.py` | The only `skore.evaluate` and `project.put`. Writes `report.html`, `report.txt`, `id.txt`, `checks.html`, `metrics.html`, and the Method viewer |
| `scratch/results/<stem>/report.html` `report.txt` `locator.txt` `id.txt` `pipeline.svg` `pipeline/` | Ephemeral (gitignored) | Evaluate `materialize.py`, then the agent writes `locator.txt` from `id.txt` | Full-report viewer, text fallback, locator, DataOp graph and report |
| `scratch/audit/<stem>/materialize.py` | Ephemeral (gitignored) | This skill, from `templates/materialize.py` | Re-opens the report. Writes checks, metrics, `audit.md`, and extra viewers, plus `accessors.txt` |
| `scratch/audit/<stem>/accessors.txt` | Ephemeral (gitignored) | `materialize.py` | `help()` trees. Additional report view labels come from the `Displays` groups here, not from the notebook |
| `scratch/results/<stem>/checks.html` `metrics.html` and extra `<slug>.html` / `.png` | Ephemeral (gitignored) | `materialize.py` | Per-item viewers the site embeds under `## Results`. The digest already carries the text, so no extra `.txt` is written here |
| Execution digest | Captured from CLI output or the digest path | CLI | Streamed or written digest — the agent reads this directly |

**Mnemonic:** `audit/` is *source* (in git); `scratch/audit/` and
stdout are *output*. Never copy `audit/<stem>.py` under
`scratch/audit/`. `materialize.py` is the gitignored agent script.
Never commit anything under `scratch/audit/`.

## Read-only contract

The central rule. Surfaced as the first Stop condition below.

**Allowed in `audit/<stem>.py`:**

- `skore.Project(...)` — open the project this experiment wrote to.
- `project.summarize()` — list `(key, id)` pairs.
- `project.get(id)` — load a specific report by id.
- Every `report.*` accessor.
- Imports from `<pkg>` (read-only inspection).

**Forbidden in `audit/<stem>.py`:**

- `skore.evaluate(...)` — duplicates the report under the same key
  and pollutes `summarize()`.
- `project.put(...)` — same.
- Snapshot writes (`write_text` of HTML, `locator.txt`,
  `report.txt`) and `help()` loops in `audit/<stem>.py`. Those
  live in `scratch/audit/<stem>/materialize.py`, which may write
  `scratch/results/<stem>/` and `accessors.txt`.
- Writes to `data/`, `reports/`, or `src/<pkg>/`. The audit
  notebook is a viewer.
- Mutation of the loaded `report` that survives the cell (e.g.
  monkey-patching skore symbols).

The runner renders every cell's source + last-expression repr +
stdout to the digest. A forbidden call surfaces in the digest (as a
`put` row in a later `summarize()` cell, or as a `**error:**`
section). The contract is *visible*, not invisible.

Sibling read-only consumers (different output shapes, same
discipline): `scratch/<ts>_*.py` probes. `review-ml-experiment`
reads the digest as text and does not open the Project. See
`evaluate-ml-pipeline` § Stop conditions for the consumer rule.

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
- **No report → STOP.** Four-way pairing is hard: run
  `python -m skore_skills design consent --stem <stem>` (`ask` /
  `stop` → do not audit) + `experiments/NN_*.py` + smoke pytest
  passed + a report under that key in the Project. If the report is
  missing, explain and stop. Do not `skore.evaluate` / `project.put`.
  Route to `evaluate-ml-pipeline` or `model-ml-pipeline`. Direct
  "audit 02" uses this same gate.
- **Read-only against the skore Project.** See § Read-only contract.
  Never `skore.evaluate(...)` or `project.put(...)` in an audit file.
- **`project.get(...)` is by id, not key.** For hub mode, read the
  id from the URL printed by `project.put()`:
  `https://…/<workspace>/<project>/<type-plural>/<N>` → id is
  `skore:report:<type-singular>:<N>` (URL segment is plural; id uses
  the singular — drop the trailing `s`, e.g. `cross-validations` →
  `cross-validation`, `estimators` → `estimator`). Hardcode
  `REPORT_ID` in the audit file — no `summarize()` traversal needed.
  For local mode, read the `"id"` column of `project.summarize()` for
  the matching key row. A `KeyError` from `get("<stem>")` means the
  lookup shape is wrong (get is by id), not that the report is
  missing.
- **Symbol from memory is forbidden.** Any `skore` / `skrub` /
  `sklearn` symbol must come from `python -m skore_skills api get` *this turn*. Cache
  hits under `scratch/api/skore/<version>/` count (Shape 0); inline
  memory does not.
- **Agent feature missing → STOP and delegate.** If `ipython` /
  `ipython` aren't importable, do NOT fabricate audit outputs by
  writing `print()` calls as a workaround. Do NOT type
  `pixi add ...` / `uv add ...` yourself — install is owned by
  `add-python-package` § Agent feature. Request via
  `agent tools (ruff / ipython / ipykernel)` (binary: install / skip); resume only when
  add-python-package returns "ready".
- **Bare expressions, not `print()`.** The runner captures each
  cell's last bare expression via `result.result` and renders its
  `repr`. Wrapping in `print(repr(...))` lands in stdout instead of
  the output section; mixed and harder to scan. Use bare
  expressions; statement-only cells (variable binding) are fine.
- **One audit file per experiment stem (four-way pairing).** No
  `audit_NN_<short_name>_v2.py`. When an experiment is re-run, the
  audit file is **overwritten in place** — same stem, same audit.
- **Executed artifacts go to `scratch/audit/<stem>/`, NOT into
  `audit/`.** Durable artifact is `audit/<stem>.py`; the rendered
  digest is ephemeral.
- **`audit/<stem>.py` does not write snapshot files.** HTML,
  `locator.txt`, and `help()` trees are `materialize.py`. No writes
  to `data/` or `reports/`.
- **Don't filter warnings in audit cells.** No
  `warnings.filterwarnings(...)` unless the user explicitly asks
  — the runner streams cell stderr into the digest and that's
  signal. See `python -m skore_skills style` § Stop conditions.
- **Harness "no clarifying questions" hints do NOT waive
  agent tools (ruff / ipython / ipykernel).** Install gate fires regardless.
- **Post-hoc audit — required before ending the turn.** Walk every
  pre-flight row; surface unfilled Evidence cells.
- **The post-audit gate is mandatory.** After the first digest and
  every refresh, ask Additional report view / Custom query /
  Custom plot / Close audit in that exact order unless the user
  already explicitly closed the audit. The one execution may
  materialize a policy-enabled notebook and a stale-only site
  preview before this gate. No close-time conversion, git close,
  record-outcome, or dispatcher return before Close.

## Forbidden shortcuts

| Shortcut | Why it's wrong |
|---|---|
| `report = project.get(REPORT_ID); print(repr(report))` | Runner captures bare expressions via `result.result`, not stdout. `print(repr(...))` mixes stdout and output sections. Use `report` on its own line |
| `checks.frame()` instead of the bare `checks` Display | The Display `__repr__` already groups issues and tips with their codes and documentation URLs. `.frame()` flattens that into a table the agent then has to re-read, and drops the severity grouping the review mines |
| `project.get(KEY)` raised `KeyError` → re-run `evaluate` + `put` "to refresh" | Lookup shape is wrong (get is by id, not key). Hub: read the id from the URL printed by `put()`. Local: read `summary["id"]` for the matching key row. Never re-run `evaluate` + `put` to recover |
| Write `pixi add --feature agent ipython` directly from this skill | Install commands owned by `add-python-package`. This skill **requests**; it does not install |
| Dump the audit `.py` into `scratch/audit/<stem>/` | The notebook stays in `audit/`. `materialize.py` is the only `.py` that belongs under `scratch/audit/<stem>/`, and it is gitignored |
| Register a Jupyter kernel "to be safe" | Current runner is in-process; no kernel. Registering creates an orphan kernelspec |
| Add a fix-up cell that mutates `data/` or `reports/` | Audit files are read-only. State mutations belong in a `scratch/<ts>_*.py` probe or the experiment script |
| Substitute `<SKORE_PROJECT_INIT>` in `audit/<stem>.py` without reading `experiments/<stem>.py` first | Audit must open the same Project. Always Read experiments/<stem>.py this turn and copy the literal Project init block byte-identical (modulo formatting) |
| Hub mode: put `skore.login(mode="hub")` after `skore.Project(...)` | `Project(...)` constructor authenticates at init time; without prior `login`, fails. Order is fixed: login first, Project second |
| Implement-loop audit → write scratch probe first to "double-check metrics" | The audit IS the metric-extraction step. Scratch probes for metrics are the anti-pattern this dispatch replaces |
| `write_text` or a `help()` loop inside `audit/<stem>.py` | The notebook is the human view. Copy `templates/materialize.py` to `scratch/audit/<stem>/materialize.py` for HTML, the locator file, and `accessors.txt` |

## Pre-flight — emit before any audit-file write or execution

```
Pre-flight (audit-ml-pipeline):
- [ ] Experiment stem confirmed: <NN_short_name>
      Evidence: journal/NN_<short_name>.md exists AND state is approved
                | "n/a — user invoked re-audit on existing stem"
- [ ] Four-way pairing complete:
        journal/NN_<short_name>.md       — design note (state approved or done)
        experiments/NN_<short_name>.py   — script
        tests/smoke/test_NN_<short_name>.py — smoke test (passing)
        audit/NN_<short_name>.py         — about to be written / refreshed
      Evidence: ls / Glob on each path
- [ ] Report present in skore Project under key=<NN_short_name>
      Evidence: project.summarize() this turn; row with
                key == "<NN_short_name>" appears.
                "Run finished, put() landed" is NOT sufficient.
- [ ] Agent feature available:
        run `ipython -c "print(0)"` and `ipython --version`
        through the project's composed dev environment
      Evidence: tool output of each
                | JOURNAL.md Status `agent feature: installed`
                Missing → STOP, delegate to add-python-package agent tools (ruff / ipython / ipykernel)
- [ ] API CLI consulted for skore symbols used:
      Project, summarize, get, report.checks.summarize, report.metrics.summarize
      Evidence: Read scratch/api/skore/<version>/<topic>.md (this turn)
                | Write the same (this turn)
                | "n/a — cache hit, file already on disk + Read this turn"
- [ ] Template copy + substitution decided:
        <pkg> → package name from src/<pkg>/
        <NN>_<short_name> → experiment stem
        <SKORE_PROJECT_INIT> → literal block copied from experiments/<stem>.py
      Evidence: Read experiments/<stem>.py this turn for the Project init block;
                Read templates/audit.py this turn before Write audit/<stem>.py
- [ ] Read-only contract acknowledged: audit file contains
      summarize / get / report.* only — no evaluate, no put
      Evidence: explicit grep / Read confirmation of the drafted file
- [ ] Execution command shape confirmed:
        python scratch/audit/<stem>/materialize.py
        notebooks true: notebook fill audit/<stem>.py [--html]
      Evidence: command emitted in the response before running
- [ ] G-AUDIT-FINDING derived from the executed digest
      Evidence: issue/tip counts + ordered codes + optional metric
                context | explicit clean-checks value
- [ ] Post-audit gate answered: additional view | query | plot | close
- [ ] Pre-flight re-emitted with evidence before final message.
      Evidence: this checklist appears in the end-of-turn summary.
```

## Before execution

After the four-way pairing, report lookup, agent feature, and API
checks are satisfied, emit 1–3 natural sentences immediately
before writing or running `audit/<stem>.py`. Say that this is
**local read-only report materialization**, not retraining: it
opens the persisted Skore report, renders checks / metrics /
available views, and writes the digest under
`scratch/audit/<stem>/` plus HTML viewers under
`scratch/results/<stem>/`. Name the exact policy-matched
execution command.

Describe cost from facts: report loading and requested view
rendering, not model fits or full CV. Unless an observed duration
is already available, say timing depends on report size and
selected views and do not invent minutes. Emit this preview once
for the initial audit; refresh it only when Additional report
view / Custom query / Custom plot materially changes the work.
The run pauses at the existing post-audit gate before close.

Questions about what the report means are **LLM narrative work**
over the digest. For a fired check, read its documentation URL
and apply that page's recommendation. They do not call
`evaluate` or `put`. If any
mandatory gate is pending, preview the possible audit but do not
write or execute it.

## Audit file contract — overview

The audit file is **jupytext percent format** (`# %%`). Filename:
`audit/NN_<short_name>.py` — stem matches the experiment exactly.
Template: `templates/audit.py`.

### Substitutions

| Placeholder | Replaced with |
|---|---|
| `<pkg>` | The importable package name (from `src/<pkg>/`) |
| `<NN>_<short_name>` | The experiment stem (e.g. `02_target_transform`) |
| `<SKORE_PROJECT_INIT>` | The full Project init block (including any preceding `skore.login(...)` call for hub mode), copied **byte-identical** from `experiments/<stem>.py` |
| `<project-name>` | The `name=` argument from `experiments/<stem>.py` (read it; don't invent) |
| `<hub-workspace>` | Hub-mode only. Copy from the `workspace=` argument in `experiments/<stem>.py` |
| `<REPORT_LOCATOR>` | The normalized post-put locator handed off by evaluate. If absent, derive it from the selected id and backend rules below; never guess a URL |

`<SKORE_PROJECT_INIT>` and `<project-name>` are the most error-prone
substitutions: the audit must open the same Project the experiment
wrote to. **Always `Read experiments/<stem>.py` this turn** to lift
the literal init block; never reconstruct from memory of the
`skore mode:` decision alone.

### Cell sequence (what each cell does)

Brief outline; full anatomy with concrete examples →
`references/cell_anatomy.md`.

1. **Module docstring (markdown cell)** — what this file is, the
   read-only rule.
2. **Imports (code cell)** — `import skore`, `from <pkg> import ...`.
3. **Open the Project (bare-expression cell)** — `project =
   skore.Project(...)`; then `project` on its own line.
4. **List reports** — `summary = project.summarize()`; then `summary`.
5. **Load the report** — set `REPORT_ID` from the URL printed by
   `project.put()` (hub: `"skore:report:<type-singular>:<N>"` — URL
   path segment is plural, id uses singular, e.g. `cross-validations`
   → `cross-validation`, `estimators` → `estimator`; local **and
   mlflow**: read `summary["id"]` for the matching key row), then
   `report = project.get(REPORT_ID)`, then `report` as the last
   expression. Do not write HTML or `locator.txt` in this cell.
   `materialize.py` does that (confirm `_repr_html_` with `api get`).
6. **Persisted report** — substitute the exact normalized locator
   from evaluate. For a direct audit, use the selected `REPORT_ID`
   and `policy.skore_mode`: local links `../reports/`; Hub uses the
   exact saved `put` URL (or a clearly labeled project link);
   MLflow uses an emitted run URL or records tracking URI +
   experiment id + run id. If no authoritative locator exists,
   write `n/a — backend did not expose a locator`. Do not call
   `put`, inspect private storage, or invent a frontend URL.
7. **Checks summary** — `checks = report.checks.summarize()`, then
   `checks` as the last expression. `materialize.py` writes
   `checks.html`. Its repr groups the walk by severity; every
   `issue` / `tip` line ends with the documentation URL. Read that
   page and apply its recommendation (custom `CSTM*` checks may
   have none).
8. **Metrics summary** —
   `metrics = report.metrics.summarize().frame(verbose_name=True, flat_index=False)`,
   then `metrics` last. `materialize.py` writes `metrics.html` from
   that frame. That frame is the only metrics table. Do not also
   paste its values into the design note.
9. **Available report accessors** — not a notebook cell. Copy
   `templates/materialize.py` to `scratch/audit/<stem>/materialize.py`
   and run it. It calls `help()` on `report.metrics`,
   `report.checks`, and any other namespace that exists
   (`inspection`, `data`, …) and writes the trees to
   `accessors.txt`. `help()` prints its tree and returns `None`.
   Skip a namespace that is absent. Do not call plot accessors
   here. Do not put the loop in `audit/<stem>.py`.

That's the core template. Leave checks as a bare Display: editors
render `_repr_html_`, the runner records the `repr`, and
`.frame()` drops the severity grouping. Metrics are the frame
above, not that Display and not a second markdown table. Extra
Display cells are appended only after the user picks Additional
report view. Details: → `references/cell_anatomy.md`.

### The digest is the review's canonical source

The rendered digest at `scratch/audit/<stem>/audit.md` is the
**single source of truth** that `review-ml-experiment` reads to
write `journal/ideas/<stem>-<slug>.md` and one Ideas row in
`journal/JOURNAL.md`. That skill reads the digest as text, walks
`Issues:` then `Tips:` in `## Checks summary`, and does not
re-open the Project, call `report.*`, or write
`scratch/<ts>_*.py` probes for metric extraction.
`manage-ml-backlog` later triages those files. A promoted idea
leaves the Ideas table and becomes a Backlog row.

The contract stays narrow: persisted-report locator + checks +
metrics summary. The review must not walk extra Display headings.
Do not
put ROC / confusion-matrix / importance cells in the core
template. After Close-audit extras, those cells use their own
`## <title>` headings. If the user explicitly asks for a custom
figure that `accessors.txt` did **not** list, load
`plot-ml-figure` if installed **before writing the cell**; never
replace a skore Display. Save PNG (or HTML) and leave the figure
visible; never `plt.close` in the audit notebook.

## G-AUDIT-FINDING

After every successful audit execution, run
`python -m skore_skills audit finding --stem <stem>` (or pass the
digest path). Paste JSON `finding` **verbatim**. Do not rewrite
codes, counts, or the metric clause. Missing digest → JSON
`finding` is `n/a — audit digest unavailable`.

Extra Display cells do not change G-AUDIT-FINDING (re-run the
command; it still reads only checks + metrics).

Return G-AUDIT-FINDING verbatim with the digest and
G-REPORT-LOCATOR from `python -m skore_skills loop locator --stem
<stem>`. `manage-ml-backlog` writes the finding to the design
note's Status block. Recompute it after every added view, query,
or plot because the digest is overwritten.

## Continue auditing

After the initial digest and every successful refresh, unless the
user already said to close, **AskUserQuestion** with one pick in
this exact order. None is recommended or preselected.

**Gate context.** Ahead of the question, state in 2–4 lines what
the answer authorizes and the facts it rests on — echoed inline
from this turn's digest (the checks and metrics just read, the
Display names in `accessors.txt`) — plus what each option
does. A file link is an addition, never the context.

| Label | Contract |
|---|---|
| Additional report view | Menu labels are **exactly** the names under the `Displays` group of this turn's `help()` trees in `scratch/audit/<stem>/accessors.txt`. Confirm the picked name with `python -m skore_skills api get`. The list is task-dependent — a regression report has no `roc`. Omit anything the trees do not list; never show remembered Display names. Ask one pick before editing. |
| Custom query | Wait for one concrete read-only question about the loaded report. Append only the minimal accessor cells needed to answer it, in `audit/<stem>.py` and in the materialize `<CALL>` block. Prefer a name from the trees when it answers the question. |
| Custom plot | Only when the trees have no Display for this chart. Load `plot-ml-figure` only if `status.skills.plot-ml-figure` is true; else one-line skip and return to this gate. Append the read-only plot to both files. `materialize.py` saves the figure under `scratch/results/<stem>/`. |
| Close audit | Continue to the existing dispatched or direct close. |

Additional report view / Custom query / Custom plot all edit the
same durable `audit/<stem>.py`, **below** `## Core audit complete`,
and the `<CALL>` block of `materialize.py`. After an edit: run
`style`, re-run `materialize.py` once, `notebook fill` when
notebooks are on, derive
G-AUDIT-FINDING again
with `python -m skore_skills audit finding --stem <stem>`
(from checks + metrics only), then run `site build --if-stale`
when site policy is true and re-present this same gate. Do not
run the close-time `loop notebooks`, run `git end-turn`,
record-outcome, or return to the dispatcher before Close audit.
The audit remains read-only: no `evaluate`, no `put`, and no
workspace-data mutation.

### Extra Display cells

Slug = the accessor name `accessors.txt` listed under `Displays`.
Do not invent slugs from docs memory.

1. Markdown cell `## <human title>` — not `## Checks summary` or
   `## Metrics summary`.
2. Code cell: call the accessor; confirm `_repr_html_` with
   `api get` on the returned Display. Last expression: the bare
   Display.
3. In `materialize.py` only, append that accessor to `EXTRA`. It
   writes `scratch/results/<stem>/<slug>.html` from
   `_repr_html_()` when it exists. Only when it does not, save
   `<slug>.png` so the site can still embed a figure. Re-run
   `materialize.py`.
4. Failed or inapplicable accessors stay in `scratch/` probes.
   Do not add a Results subsection for them.

`manage-ml-backlog` turns each extra `<slug>` viewer (other than
`report`, `checks`, `metrics`) into a `###` Results heading with
`<!-- results-embed: <slug> -->`, summarizing it from the digest
cell that produced it.

## Execution contract — one execution

Before the first execution for a stem, run
`python -m skore_skills review consent --stem <stem>`.
- `stop` — name the missing `report.html` and stop.
- `audit` — write `audit/<stem>.py` and execute it once.
  Check results were stored with the report; this read uses them.
- `proceed` — digest exists. Do not execute unless the user
  explicitly asked to re-audit. A re-audit repeats the one
  policy-matched execution.

Copy `templates/materialize.py` to `scratch/audit/<stem>/materialize.py`,
substitute the Project init, report id, and locator, and run it
once with the composed-dev Python from `env verify`. That run
writes the HTML viewers, `accessors.txt`, and `audit.md`. Do not
`cells run` the audit file and do not `notebook convert` it.
When `policy.notebooks` is `true`, then run:
```bash
python -m skore_skills notebook fill audit/<stem>.py [--html]
```
Add `--html` only when site is also `true`. Fill writes an
output-free notebook and does not write the digest. When
notebooks is `null` or `false`, do not change policy and do not
fill. Then run:
```bash
python -m skore_skills audit finding --stem <stem>
```

The notebook does not contain the materialize writes. If site
policy is `true` and `export-ml-site` is installed, run
`python -m skore_skills site build --if-stale` after materialize
and before that gate. When the build ran, say the website has
been updated and paste the `file://` line from that output
verbatim. Do
not name the design-note markdown or `html/<stem>.html`.

Paste JSON `finding` verbatim. Read `audit.md`; do not derive it
from the notebook.

### Executed notebook

When notebook policy is true, `notebook fill` above owns the
output-free notebook on direct and dispatched paths. The caller
runs `python -m skore_skills loop notebooks --stem <stem>`
and obeys `convert` by filling, not by kernel-executing. Naming
`notebook fill` is not that close. A current source fingerprint
makes that gate skip; a changed source fills again as a safety
net.

On a direct close, run the notebook gate in § End of turn before
record-outcome. The audit has no page of its own. Site build
embeds `audit/<stem>.nb.html` under the design note's
`## Notebooks` section, after the evaluation notebook, whenever
that file exists. Do not add `<!-- results-embed: audit -->`. A
marker does not create the viewer, and a missing `.nb.html`
omits it.

### Re-execution semantics

- Re-running an experiment (overwriting `put()` under the same key)
  → re-execute the matching audit file. `manage-ml-backlog` § 4
  fires this on every record-outcome.
- Editing the audit file's source (adding a metric accessor) →
  re-execute. The digest is regenerable.
- `scratch/audit/<stem>/` is **overwritten on every execution**. No
  version history; the source `.py` + git history is the audit trail.

## Four-way stem-pairing rule

Extends `setup-workspace`'s pairing rule from three artifacts
to four:

```
journal/NN_<short_name>.md           — design note
experiments/NN_<short_name>.py       — script
tests/smoke/test_NN_<short_name>.py  — smoke test
audit/NN_<short_name>.py             — audit  ← this skill
```

Identical stems, 1:1. By the time the experiment shows `done` in
`journal/JOURNAL.md`, all four exist.

## Dispatching in and out

### Called from

| Caller | When |
|---|---|
| `review-ml-experiment` | When review consent is `audit`, before idea files |
| `model-ml-pipeline` | Does not load this skill; it loads `review-ml-experiment` |
| `evaluate-ml-pipeline` | Standalone evaluate may run audit before its close |
| User free-text | "audit experiment 02", "show me what 03", "re-audit 04" — resolves directly |

### Calls into

| Callee | Why |
|---|---|
| `python -m skore_skills audit finding` | After audit execution. Paste JSON `finding` verbatim |
| `python -m skore_skills loop locator` | G-REPORT-LOCATOR from `locator.txt` or the audit file |
| `python -m skore_skills loop artifacts` | Direct-audit close: `record` before the notebook gate |
| `python -m skore_skills loop notebooks` | Before record-outcome. Obey `convert`; `skip` continues |
| `add-python-package` | When `ipython` is missing |
| `manage-ml-backlog` (record-outcome mode) | End of turn on a direct free-text audit — hands over the digest so the History row and design-note Status block get written |
| `python -m skore_skills style` | After writing / editing `audit/<stem>.py` — bundled `ruff.toml` carries `audit/**` per-file ignores. Ruff only; it does not rewrite comments. Do not write workflow/process prose in the audit file |

## End of turn

**Dispatched** (`model-ml-pipeline`, `evaluate-ml-pipeline`, or
`manage-ml-backlog` this turn), after **Close audit**: run
`python -m skore_skills audit finding --stem <stem>` and
`python -m skore_skills loop locator --stem <stem>`. Return the
digest, JSON `finding`, JSON `locator`, and an optional
headline to that caller. Stop. Do not run record-outcome,
the close-time `loop notebooks`, another site build,
`git end-turn`, or triage here. The live execution/preview above
is not repeated. When the caller is
`model-ml-pipeline` or `evaluate-ml-pipeline`, tell it to run
`python -m skore_skills loop notebooks --stem <stem>` and obey
`convert` with `notebook fill` before record-outcome. That gate
continues on `skip`. `record` is `loop artifacts`, not the
notebook gate. Then `site build` and that caller's
`git end-turn` (`--stage implement` from model, `--stage
evaluate` from evaluate). Naming the fill commands is not the
close. Filling only the audit file does not finish that close. Do
not paste the direct-audit close as a preview of what the
dispatcher will run.

**Direct free-text audit, after Close audit:** this skill owns the close. Do not start it before Close audit. Run
`python -m skore_skills loop artifacts --stem <stem>` first
(`record` expected). `record` is that command's action, not the
notebook gate. Then this order. Do not reorder it.
`loop notebooks` continues only on `skip`.

1. `python -m skore_skills loop notebooks --stem <stem>`. Treat
   JSON `action` as authoritative. Do not record-outcome,
   `site build`, or `git end-turn` while `action` is `convert`.
   `not_evaluated` does not convert.
2. On `convert`, run `notebook fill` for every `experiments/`
   or `audit/` source, with `--html` when `html` is true. Do
   not `notebook convert` those files. Fill does not `put`.
   Re-run the matching `materialize.py` first only when that
   human call changed since the run that wrote the current
   artifacts. Re-run step 1 until `action` is `skip`. Missing
   jupytext / nbformat → one-line skip naming
   `add-python-package`; do not fail the audit, do not
   `pixi add`.
3. Load `manage-ml-backlog` in **record-outcome mode** only
   if `status.skills.manage-ml-backlog` is true and hand it the
   digest, G-AUDIT-FINDING, and that locator. Missing skill →
   one-line skip; do not write History here. That mode records
   and returns; it does not re-dispatch this skill. Never mark
   `done` while smoke is red.
4. `site build` only when `policy.site` is true and
   `export-ml-site` is installed:
   `python -m skore_skills site build --if-stale`. If it errors with
   `mkdocs-material is required`, load `add-python-package` for
   `mkdocs-material` (agent) and build once more. Do not
   `pixi add` / `uv add`. Name a build error; do not fail the
   audit.
5. User-facing close. The message is 2–6 sentences from Checks +
   Metrics. Do not invent a metric or paste the digest. When
   step 4 succeeded, say the website has been updated and paste
   the `file://` line from that output verbatim. Do not name
   `html/<stem>.html` or
   `journal/<stem>.md`. When the site was not built, do not
   claim it was updated and do not name the markdown. Then JSON
   `locator` from step 2 verbatim (local: also the absolute
   `reports/` path), then G-AUDIT-FINDING. Index strings, not
   the narrative.
   Dispatched audit never writes this message.
6. `python -m skore_skills git end-turn --stage evaluate`. The
   audit continues the evaluate stage; there is no `audit` stage.
   If JSON `action` is `invoke`, load `persist-ml-git` only if
   `status.skills.persist-ml-git` is true and stop; that skill
   returns to triage. If persist is missing, name the pending
   `staged` paths and stop. Otherwise load `triage-ml-task` only
   if `status.skills.triage-ml-task` is true; else stop. Do not
   run `git commit` in this skill.

## Failure modes and recovery

Quick lookup; detailed recovery steps in `references/failure_modes.md`.

| Symptom | Cause | Fix |
|---|---|---|
| `project.get(key)` raises `KeyError` / `TypeError` | Lookup by key, not id; local vs hub shape differs | → `references/failure_modes.md` § "`project.get(key)` raises" |
| `ModuleNotFoundError: No module named 'IPython'` | Agent feature not installed | Delegate to `add-python-package`; never `pip install` here |
| Cell renders as `<Display object at 0x…>` | skore too old to give the Display a text repr | Add `.frame()` to that cell only; leave the rest bare |
| `AttributeError` for a `report.*` accessor | Symbol from memory; skore version drift | → `references/failure_modes.md` § "AttributeError" |
| `RuntimeError: No report under key=...` | `put()` landed in a different Project | → `references/failure_modes.md` § "wrong Project" |
| Report differs across runs with unchanged source | Non-deterministic step / different data slice | Not a bug here; surface to user |
| Hub mode: `skore.login()` auth error | Token expired / first-time login | → `references/failure_modes.md` § "skore.login fails" |
| Hub mode: `TypeError: workspace` kwarg | Hub form left local-mode kwarg | → `references/failure_modes.md` § "TypeError workspace" |
| Hub mode: report missing in `summarize()` after `put()` | Wrong hub workspace OR no read access | → `references/failure_modes.md` § "report missing" |

## What this skill does NOT do

- Open or write the skore Project's reports (`evaluate-ml-pipeline`).
- Install `ipython` (`add-python-package` owns).
- Write `journal/ideas/` files or Ideas rows
  (`review-ml-experiment` owns both).
- Write or edit `journal/NN_*.md` or `journal/JOURNAL.md` directly. At end
  of turn, dispatch `manage-ml-backlog` record-outcome mode
  instead — that skill owns every journal write.
- Run pytest / smoke tests (`smoke-test-ml-pipeline`).
- Render commits or PRs.
- Decide *which* metrics matter — the cells are filled per task,
  but judgment about what matters is the user's, in the design note.

## Companion skills

| Skill | Relationship |
|---|---|
| `manage-ml-backlog` | Downstream record-outcome consumer; never dispatches audit from record-outcome mode |
| `review-ml-experiment` | Loop caller. Parses the digest as text and writes one idea file and one Ideas row per candidate. Never opens the Project |
| `evaluate-ml-pipeline` | Producer side. The experiment file holds the call; `materialize.py` is the only run |
| `setup-workspace` | Workspace layout; four-way stem pairing |
| `add-python-package` | Agent feature install (agent tools (ruff / ipython / ipykernel)). This skill requests; that skill installs |
| `python -m skore_skills api get` | skore symbol lookups, including `help` and extra Display methods. Cache hits first |
| `plot-ml-figure` | Custom plot gate only when `accessors.txt` has no Display |
| `python -m skore_skills style` | ruff after writing/editing `audit/<stem>.py` |
| `choose-python-library` / `python -m skore_skills env stack` | Agent tools (`ipython`, `ipykernel`) live under the agent feature |

## Templates and assets

- `templates/audit.py` — per-experiment audit file skeleton. Copy
  + substitute; don't rewrite from memory. Bare displays only.
- `templates/materialize.py` — the only audit run. Copy to
  `scratch/audit/<stem>/materialize.py`. Writes the HTML
  viewers, `accessors.txt`, and `audit.md`.


## Need a package?

When an import is missing, load `add-python-package` if
`status.skills.add-python-package` is true. That skill owns
`env add` and the unmanaged ask. Do not run `env add` here.
If the skill is not installed, name the package and stop.

## References (load on demand)

- `references/cell_anatomy.md` — concrete cell examples (right /
  wrong shapes), core sequence, why checks stay a bare Display
  and metrics use `frame(verbose_name=True, flat_index=False)`,
  extra Display snapshot contract, bare-expression rules.
- `references/runner_internals.md` — leftover runner internals
  (IPython, Agg). Prefer `--help` / the package docstring.
- `references/failure_modes.md` — detailed recovery for every
  symptom in § Failure modes.
