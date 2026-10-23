---
name: export-ml-notebook
description: >
  Write a jupytext percent file out as a notebook with empty outputs.
  `data_analysis/`, `experiments/`, and `audit/` are filled with empty
  outputs. Pass `--html` when that notebook should also become a viewer on the
  site. Kernel `notebook convert` stays for a source that is itself the
  execution. Trigger on notebook, ipynb, HTML, or executed-report requests, or
  when export-ml-project dispatches notebooks.
metadata:
  modelTier: small
---

# Export ML Notebook

Source of truth stays the `# %%` `.py`. This skill only writes
derived `.ipynb` (and optional `.nb.html`). Do not rewrite the
`.py` from the notebook. `cells run` is not a substitute.

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Tell the user the written `.ipynb` (and HTML viewer) paths. Do
not quote `notebook convert`, `--html`, or `site build` as
something they should run.

While `policy.notebooks` is true, `explore-ml-data` fills the
analysis file it wrote. `model-ml-pipeline` and
`evaluate-ml-pipeline` fill the experiment script and, when it
exists, `audit/<stem>.py`, with empty outputs.
`audit-ml-pipeline` fills `audit/<stem>.py` only on a direct
close. This skill owns on-demand fills, other sources, and
turning the flag on when it is `null` or false. A data-analysis,
experiment, or audit source uses `notebook fill`, not
`notebook convert`.

## Workflow checkpoint execution

Stage owners read policy before executing a human `# %%` source.
Only `policy.notebooks` `true` enables automatic notebook
materialization; `null` and `false` keep the stage's non-notebook
execution and do not change policy.

When true, exploratory analysis uses `materialize.py` as its
**one run**, then `notebook fill` writes the `.ipynb` with empty
outputs. Add `--html` only when `policy.site` is also true. An
experiment or audit file is the same: `notebook fill` writes the
`.ipynb` with empty outputs, and `materialize.py` is the run that
writes the digest and the HTML viewers. Do not `notebook convert`
those files and do not `cells run` them. Kernel `notebook convert`
stays only for a source that is itself the execution (the unfitted
experiment snapshot). A generated notebook records its source
fingerprint; `loop notebooks` fills or converts again only when
the source or required HTML changed.

## Lookup

Run `status` and read `policy.notebooks`. Take the first row that
matches. Fill leaves code-cell outputs empty. Do not stop after
reading the table.

| `policy.notebooks` | Request | Then |
|---|---|---|
| `null` | any | step 2, then match this table again. Do not take the convert row only because it is listed first. |
| `false` | any | step 3. Do not fill until the policy is `true`. |
| `true` | the user asked for HTML, a site viewer, or the notebook on the site | step 4 `notebook fill --html`, then step 5. `data_analysis/`, `experiments/<stem>.py`, and `audit/<stem>.py` stay `notebook fill`, not `notebook convert`. |
| `true` | the source is itself the execution (unfitted experiment snapshot, before `skore.evaluate`) and the user did not ask for HTML or a site viewer | kernel `notebook convert`, not `notebook fill` |
| `true` | notebook, ipynb, or convert, with no HTML and no site viewer | step 4 `notebook fill` only. No `--html`. No `site build`. |

## Sequence

1. `python -m skore_skills status`. Read `policy.notebooks` and
   `skills`.
2. If `policy.notebooks` is `null`: persist
   `python -m skore_skills policy set notebooks true`. Do not
   AskUserQuestion. Then load `add-python-package` for `jupytext`
   and `nbformat` (agent) and continue.
3. If `policy.notebooks` is false: say notebooks are off; offer
   to turn them on. Do not fill until the policy is true.
4. Fill the requested percent file (default `data_analysis/data_analysis.py` when
   the user did not name one):

   ```bash
   python -m skore_skills notebook fill data_analysis/data_analysis.py
   ```

   Fill does not execute the file and leaves code-cell outputs
   empty. It needs jupytext and nbformat, not nbclient,
   ipywidgets, or IPython. Do not start EDA, an evaluation, or
   an audit from this skill to produce those outputs.
   `experiments/<stem>.py` and `audit/<stem>.py` are filled the
   same way. Missing `jupytext` / `nbformat` / `nbconvert` stays
   a one-line skip.

   If the user wants the notebook on the site, load
   `add-python-package` for `nbconvert` (agent) and pass `--html`
   (writes a self-contained `<stem>.nb.html` next to the `.py`).
   The site links that file from the associated exploratory data
   analysis or design report. It opens as a page of its own.

   Optional `--out path.ipynb`. Keep `*.ipynb` gitignored unless
   the user asks `setup-git` to track them.

   Fill-only requests (notebook / ipynb / convert, no HTML or
   site viewer): run **only** that `notebook fill` line, with no
   `--html`. Tell the user the written `.ipynb` path. Do not
   mention `--html` or `site build` as an optional aside.

   Kernel `notebook convert` is only for a source that is itself
   the execution: the unfitted experiment snapshot, before
   `skore.evaluate` exists. Convert injects `%matplotlib inline`
   for that kernel run so seaborn / matplotlib last expressions
   emit `image/png`, then strips that setup cell from the written
   notebook. Do not put `%matplotlib inline` in the `.py`
   (`style` / ruff would reject it). If that convert fails
   because `ipywidgets` is missing, load `add-python-package`
   for it (agent) and convert again.
5.    After `--html`, if `policy.site` is true, `export-ml-site`
   is installed, run `python -m skore_skills site build --if-stale` so the
   viewer is packaged. Run `--html` and `site build` **only**
   when the user asked for HTML or a site viewer. Fill
   without `--html` does not rebuild the site. Skip in one line
   otherwise. If `site build` errors with `mkdocs-material is
   required`, load `add-python-package` for `mkdocs-material`
   (agent) and build once more. Do not `pixi add` / `uv add`.
   If that skill is missing, or the retry still fails, name the
   error in one line. Name a build error; do not fail the
   fill, and do not claim the website was updated. When the
   build ran, say the website has been updated and paste the
   `file://` line from that output verbatim. Do not name the
   markdown file
   or the HTML viewer path. Do not quote the CLI.

## Stop conditions

- Do not `git commit` or `git end-turn`.
- Do not run `cells run` as a substitute for fill.
- Do not `pixi add` / `uv add`; load `add-python-package`.
- Missing skill or missing source → one-line skip.
- Do not name `--html` or `python -m skore_skills site build`
  unless the user asked for HTML or a site viewer. Tell the user
  paths, not the CLI.
