---
name: export-ml-site
description: >
  Package workspace markdown and existing notebook HTML into an offline MkDocs
  site. Embeds existing notebook HTML companions in their associated reports.
  Never executes Python. Trigger when the user asks for a website, mkdocs, or
  documentation site.
metadata:
  modelTier: small
---

# Export ML Site

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Tell the user the website has been updated and paste the
`file://` line from that output verbatim, so a click opens the
browser. Do not describe the line. Do not link a
workspace-relative path. Do not say double-click or
"no server". Do not name the markdown file that was edited. Do
not quote `site init` / `site build` as something they should run.

The site is a derived index of files other skills already write.
The staged docs mirror the workspace folders (`journal/`,
`data_analysis/`, `experiments/`, `audit/`, `scratch/results/`), so
a relative link written between two source files also works on the
site. MkDocs warns about a link it cannot resolve and `site build`
prints that warning: fix the link, do not hide the warning.
Markdown is the report: its figures are shown inline and an
HTML file it refers to by name is pasted into the page when it is
a fragment (TableReport `html_snippet()`). A whole HTML document
(Plotly) sits in a fixed-height iframe with an open-separately
link. Existing converted notebooks
(`<stem>.nb.html`, written only by `export-ml-notebook` with
`notebook convert --html`) are links that open a page of their own.
Each experiment design note has one `## Notebooks` section:
evaluation first, then audit. The audit notebook is
`audit/<stem>.nb.html` from `notebook convert --html`. A missing
file is omitted. Do not use `<!-- results-embed: audit -->`.
Derived HTML and PNG files under `scratch/results/<stem>/`
(checks, metrics, plus extra Display slugs) may be copied into the
staged docs. Core Results headings are Report overview / Checks /
Metrics. `### Report overview` is prose only: the skore report
(`report.html`) is not published. `checks.html` and `metrics.html`
are pasted into the page under their headings; the scores are that
table, not a second markdown table.
Extra slugs use `<!-- results-embed: <slug> -->` under
`## Results` **or** `## Method`. `pipeline` is the graph image
`pipeline.svg` shown on the page plus a link to the DataOp report
`pipeline/index.html`.
Only Markdown and already-generated notebook/HTML files are
exported. The gitignored serialized Skore `reports/` directory is
private runtime state and is never copied into the site.
On desktop, site pages are in the top bar (experiments in a
scrollable dropdown) and the page contents are in a collapsible
left rail beside a 1200px report column. Mobile uses a drawer.

Workflow stages publish at completed checkpoints, after their
Python execution and final durable Markdown batch and before the
next user decision. They call `site build --if-stale`: unchanged
inputs skip MkDocs. This is coalescing, not a file-save hook; do
not build between related Markdown edits. Only `policy.site`
`true` enables these automatic builds. `null` and `false` do not
change policy. A direct user request to rebuild uses `site build`
without `--if-stale`.

## Lookup

Run `status` and read `policy.site`. Take the first row that
matches. `site build` writes the site. Do not stop after reading
the table.

| `policy.site` | Turn | Then |
|---|---|---|
| `null` | direct request | step 2: persist `true`, install `mkdocs-material`, `site init`, then build |
| `false` | direct request | step 3. Do not init or build until it is `true`. |
| `true` | direct request, and `site build` reports `mkdocs-material is required` | load `add-python-package` for `mkdocs-material`, then build once more. Do not `site init` again. |
| `true` | direct request, first site turn | step 4 `site init`, then step 5 `site build` |
| `true` | direct request, later turn (`site init` already ran) | step 5 `site build` only. Do not `site init`. |
| `true` | workflow checkpoint, not a direct request to build | `site build --if-stale` (preview section, including its one retry). Unchanged inputs skip MkDocs. |

## Sequence

1. `python -m skore_skills status`. Read `policy.site`.
2. If `policy.site` is `null`: persist
   `python -m skore_skills policy set site true`. Do not
   AskUserQuestion. Then load `add-python-package` for
   `mkdocs-material` (agent) then
   `python -m skore_skills site init`. Continue to build.
3. If `policy.site` is false: say the documentation site is
   off; offer to turn it on. Do not init or build until it is
   true.
4. If this is the first site turn, run `site init` (gitignore
   only). Later turns only `site build`.
5. `python -m skore_skills site build`. Do not run
   `notebook convert`. If `site build` errors with
   `mkdocs-material is required`, load `add-python-package`
   for `mkdocs-material` (agent) and build once more. Do not
   `pixi add` / `uv add`. If that skill is missing, or the
   retry still fails, name the error in one line. Name a build
   error; the markdown sources remain the record. Do not claim
   the website was updated. When the build succeeds, tell the
   user the website has been updated and paste the `file://`
   line from that output verbatim. Do not say double-click or
   "no server". Do not name the markdown file or a stage
   page (`html/data_analysis/data_analysis.html`, `html/journal/<stem>.html`). Stage
   owners that just ran `site build` say that same line in the
   User-facing close.

## Preview before markdown-review gates

Stage owners that just wrote durable markdown and will ask the
user to approve or continue must rebuild the site **before**
that AskUserQuestion / consent stop — not only at End of turn.

1. If `policy.site` is true and this skill is installed, run
   `python -m skore_skills site build --if-stale`. Skip in one line
   otherwise. If `site build` errors with `mkdocs-material is
   required`, load `add-python-package` for `mkdocs-material`
   (agent) and build once more. Do not `pixi add` / `uv add`.
   If that skill is missing, or the retry still fails, name the
   error in one line. Name a build error; do not fail the gate.
2. In the same message as the gate, when the build ran or
   reported the site current: the website has been updated, and
   paste the `file://` line from that output verbatim. Do not
   name the `.md` path
   or the stage page. A file link is an addition, never the
   context. If the build failed, name the error in one line and
   do not claim the website was updated.
3. Do **not** `notebook convert`, `git end-turn`, or `git commit`
   on this preview rebuild. Do not re-run `site init`.
4. Close-time conversion and build remain a freshness safety
   gate. Current notebooks and site inputs skip execution/build;
   changed or missing outputs are refreshed.

## Stop conditions

- Do not assemble the site by hand. `site build` writes the site.
- Do not `git commit` or `git end-turn`.
- Do not `pixi add` / `uv add`; load `add-python-package`.
- Do not convert or execute `# %%` scripts.
- Do not copy or link serialized files from gitignored `reports/`.
- Skip in one line if this skill is not installed.
