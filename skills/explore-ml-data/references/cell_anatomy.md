# Explore ML Data — Human notebook vs agent facts

`data_analysis/data_analysis.py` is for a person in Jupyter.
Agent-only blobs go under `scratch/data_analysis/`. SKILL.md is
the procedure; this file is the split.

## Human — `data_analysis/data_analysis.py`

Markdown cells describe **this dataset's analysis**, not the repo
and not the CLI. Authoring hints (which template to append, when
to omit drift, glance vs implications) stay in this file and
SKILL.md — never as HTML comments in `data_analysis.md` or as
`#` procedure in the notebook.

Last expressions are rich objects or small summary frames: the
frame (`RAW`), `skrub.TableReport(...)`, duplicate/target/leakage
tables, bivariate column lists, **and live figures**. Writing
`report.html_snippet()` to `data_analysis/data_analysis_<slug>.html`
is what `data_analysis.md` shows: the site pastes the fragment into
the page. Saved figures are PNG siblings under
`data_analysis/`, or Plotly HTML siblings (`<plot_slug>.html`, never
`data_analysis_<slug>.html`). Do not put `json()`, dict dumps of TableReport,
or analyses TableReport already covers (dtypes, missingness,
cardinality, univariate histograms, pairwise associations,
`sns.heatmap` of a correlation matrix). Do not add unique-ratio
(`nunique()/n`) or column-dict cells.

Start from `templates/data_analysis.py` if it fits, then **edit**.
The first family holds every target when any exist. Each
further family: `templates/family.py`. One target: append
`templates/target_regression.py` or
`templates/target_classification.py`. Two or more regression
targets: append `templates/target_multioutput_regression.py`
once. Several classification columns, or a mix, get no target
snippet. Append `templates/datetime.py` / `templates/drift.py`
only when those data exist (datetime per family; include the
datetime relplot only when there is exactly one numeric target;
copy the datetime block per family with `FRAME_<OTHER_SLUG>`;
drift only when two families share column names — omit on
disjoint schemas). Join coverage is Keep exploring
only (`templates/join_coverage.py`: diagnostic coverage, do not
write a joined frame or TableReport on the join). Do not leave `if TARGET` /
`if TASK` / `OTHER = None` / empty datetime loops / “skip this
cell” in the notebook. Load `plot-ml-figure` before figure cells. Save each
PNG, then leave the figure/grid as the cell output — never
`plt.close`. Prefer seaborn figure-level (`displot`, `relplot`,
`catplot`, `pairplot`); one target uses one faceted `relplot`
saved as `bivariate_grid.png`. Multi-output regression uses
`target_distributions.png` and `bivariate_targets.png`. Last
expression `g`. Do not `import matplotlib.pyplot` on the
normal path. One figure-level call per cell as the last
expression; facet with `col=` / `col_wrap` instead of looping.
A bare name inside a `for` loop is not displayed. The
multi-output leakage loop is the template's last expression,
the summary frame, not a trailing grid.

The agent does not execute this file, and does not `notebook convert`
or `cells run` it. Do not put TableReport dicts in the notebook to
feed the agent.

## Agent — `scratch/data_analysis/materialize.py`

Copy `templates/materialize.py` to
`scratch/data_analysis/materialize.py` (gitignored). This is the
only run. The matplotlib Agg backend is set before seaborn; do not
put that in the human notebook. Replace `<ANALYSIS>` with the same
loads, `TableReport.html_snippet()` writes, and figure or HTML saves as
the human file. One load per family. Bind `FAMILIES` as
`(slug, raw)` and `FRAME` to the pandas frame that contains every
target (the first family when there is no target). No
markdown cells and no bare display expressions. Leave the tail: it
does not load again and does not write the TableReport HTML again.
It builds `TableReport(..., plot_distributions=False)` on the
in-memory frame and writes `scratch/data_analysis/<slug>.json` from
`report.json()` so that snapshot has statistics, not SVG, then
`extras.json` (`tables[]`, `targets` with one entry per confirmed
column, `complete_target_rows`, `target_target_corr`, png and html
paths). A single target is a one-item `targets` list. There is no
scalar `target` or `task` field. Confirm keys with `api get`;
parse JSON files with `.get(...)`.

Author `data_analysis/data_analysis.md` from those JSON files plus
the HTML. The glance section is one iframe per family and nothing
else — no bullets restating the report. Every path in
`extras["pngs"]` and `extras["htmls"]` is embedded in Modelling
implications (`![](<name>.png)` or `<iframe src="<plot_slug>.html">`)
beside a sentence that cites numbers from those JSON files (or a
summary table from the notebook). If a figure earns no such
sentence, do not save it — no orphan files under `data_analysis/`.
Glance stays TableReport-only.

Extra cells after the user picks extras: `references/extra_analyses.md`.

## Substitutions

| Placeholder | Where |
|---|---|
| `<pkg>` | `from <pkg> import PROJECT_ROOT` |
| `<LOAD_RAW_DATA>` | first family; pandas/polars load; in-memory concat of shards; convert to pandas for seaborn cells |
| `<slug>` | Python identifier; `data_analysis_<slug>.html` and `<slug>.json` |
| `<OTHER_SLUG>` / `<LOAD_OTHER>` | `templates/family.py` for each further family |
| `<TARGET>` | `"column"` in the notebook load cell when exactly one target exists |
| `<TARGETS>` | list of column names in the multi-output notebook and in materialize.py; `[]` when there is no target |
| `<TASKS>` | list parallel to `<TARGETS>`: `classification` \| `regression` (materialize.py only) |
| `<OTHER_FRAME>` | `templates/drift.py` when two families share column names |
| `<JOIN_KEY>` | `templates/join_coverage.py` (Keep exploring only) |
