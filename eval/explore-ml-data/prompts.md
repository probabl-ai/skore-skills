# explore-ml-data eval

---

## CASE_01 — End of turn uses git hook

**User prompt:**
> EDA is done. Close the turn.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `data_analysis/data_analysis.md` was just written.

**Must do:**
- Write 2–6 sentences of EDA findings (shape / target /
  leakage or duplicates that shape modelling).
- Do not name `data_analysis/data_analysis.md`. Do not claim
  the website has been updated.
- Run `python -m skore_skills git end-turn --stage data_analysis`.
- If that command returns `invoke`, load `persist-ml-git`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Paste the full `data_analysis.md` into chat.
- Run `git commit` in this skill.
- Run `git push`.

---

## CASE_02 — G-TABULAR before first EDA script

**User prompt:**
> Explore the dataset before we design a model.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists (`has_src`, `journal/JOURNAL.md`).
- Raw data path is known.
- `policy.tabular` is unset.
- `choose-python-library` and `add-python-package` are installed.

**Must do:**
- Read `status.policy.tabular` and ask pandas vs polars
  (recommend pandas) via `choose-python-library` or ask here if
  that skill is missing.
- Persist `policy set tabular` after confirmation.
- Load `add-python-package` for the chosen frame library,
  `skrub`, `matplotlib`, and `seaborn`.
- Do not place `data_analysis/data_analysis.py` before the library
  choice is confirmed.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Silent-default pandas and write `data_analysis.py` first.
- Install sklearn, skore, or pytest in this turn.
- Call `env add` from this skill instead of `add-python-package`.

---

## CASE_03 — Skip G-DATA-ANALYSIS

**User prompt:**
> Skip the EDA. I already know the data.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists (`has_src`, `journal/JOURNAL.md`).
- `status.data_analysis` is `missing`.
- No `data_analysis/data_analysis.md`.

**Must do:**
- Run `eda stamp --status skipped`. Do not type the date.
- Stop without placing `data_analysis/data_analysis.py`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Run `python -m skore_skills cells run`.
- Write `data_analysis/data_analysis.py` or `data_analysis/data_analysis.md`.
- Invent a calendar date for the data-understanding Status.
- Pick a package name or start modeling.
- Run `python -m skore_skills site build`.

---

## CASE_04 — EDA already present, no refresh

**User prompt:**
> Explore the dataset.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `data_analysis/data_analysis.md` exists.
- JOURNAL § Data understanding records `Status: done`.
- The user did not ask to re-run or refresh EDA.

**Must do:**
- Detect exploratory data analysis already recorded (`status.data_analysis` present).
- Say the written analysis stays and offer to run it again or
  keep it.
- Do not overwrite `data_analysis/data_analysis.py` or
  `data_analysis/data_analysis.md` until the user accepts a
  re-run.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Write a JOURNAL Data understanding Status of `skipped`.
- Re-run `cells run` or rewrite the report before the user
  accepts a re-run.
- Design a model in this skill.
- Treat a methodology concern (“is this leakage”) as this stop
  (see CASE_18).

---

## CASE_05 — Human notebook vs agent scratch

**User prompt:**
> Explore the dataset. Write the TableReport HTML next to the EDA
> script.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`. Skrub, IPython,
  matplotlib, and seaborn are installed.
- JOURNAL names target `MedHouseVal` (regression).
- Raw data path is known.
- User chose **run** for G-DATA-ANALYSIS.

**Must do:**
- Before writing or running the notebook, give a 1–3 sentence
  preview: local full-table profiling plus duplicate / target /
  bivariate / leakage work; name the `data_analysis/` and
  `scratch/data_analysis/` outputs.
- Say timing depends on table size, family count, and requested
  plots; do not invent a minute estimate.
- Write `data_analysis/data_analysis_<slug>.html` (not under `data/`).
- End overview cells on `TableReport` (or the frame), not on a
  json/dict digest.
- Include duplicate, target-distribution, bivariate-vs-target, and
  leakage cells (not TableReport dtypes/histograms/associations).
- Embed or link that HTML from `data_analysis/data_analysis.md`.
- Embed every saved PNG/HTML from extras in Modelling
  implications, each with a sentence citing extras/JSON numbers.
- Put `TableReport.json()` under `scratch/data_analysis/<slug>.json`
  and extras under `scratch/data_analysis/extras.json`.
- Run `scratch/data_analysis/materialize.py` once. That run writes
  the TableReport HTML, the figures, and those JSON files. Do not
  execute `data_analysis/data_analysis.py`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Describe this EDA execution as model training or smoke testing.
- Put unique-ratio / column-dict / `report.json()` cells in
  `data_analysis/data_analysis.py`.
- Write HTML under `data/`.
- Modify the user's raw data files.
- Train/test split or install sklearn unless extras were requested.
- Leave a saved figure unembedded in `data_analysis.md`.
- `notebook convert` or `cells run` `data_analysis/data_analysis.py`.

---

## CASE_06 — Missing IPython does not block the run

**User prompt:**
> Run the EDA now.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. User chose **run**.
- `ipython` is not importable in the project env.
- `add-python-package` is installed.

**Must do:**
- Run `scratch/data_analysis/materialize.py`. Do not block on
  IPython and do not skip the analysis.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Load `add-python-package` for `ipython` before the run.
- Run `pixi add ipython` / `uv add ipython` from this skill.
- Hand-write expected exploratory data analysis output.
- Skip the analysis because IPython is missing.

---

## CASE_07 — Notebook and site on after EDA

**User prompt:**
> EDA is done. Close the turn.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `data_analysis/data_analysis.md` was just written.
- `policy.notebooks` is true. `policy.site` is true.
- `export-ml-notebook` and `export-ml-site` are installed.
- `jupytext`, `nbformat`, and `nbconvert` are installed.
- The completed `materialize.py` run already wrote the artifacts,
  and fill already wrote a source-current `.ipynb` and `.nb.html`.
- When `site build` runs, its output ends with `file:///workspace/report.html`.

**Must do:**
- Write 2–6 sentences of EDA findings.
- Say the website has been updated and include
  `file:///workspace/report.html`. Do not name
  `data_analysis/data_analysis.md` or `html/data_analysis.html`.
  Do not say double-click or "no server".
- Do not execute `data_analysis.py` again on Close.
- Run `python -m skore_skills site build --if-stale` before git
  end-turn; it may report that the site is current.
- Run `python -m skore_skills git end-turn --stage data_analysis`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Paste the full `data_analysis.md` into chat.
- Name `site build` or `--if-stale` in the user-facing close.
  Housekeeping may name the command.
- Fail the data-analysis turn if site build errors; name the error.
- Run `cells run` or `notebook convert` on
  `data_analysis/data_analysis.py`.
- Re-run `notebook fill` for the source-current notebook.
- Re-run `materialize.py` when the artifacts are already from
  this human file.
- Run `git commit` in this skill.

---

## CASE_08 — Site off skips rebuild

**User prompt:**
> EDA is done. Close the turn.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `data_analysis/data_analysis.md` was just written.
- `policy.site` is false.

**Must do:**
- Write 2–6 sentences of EDA findings. Do not name
  `data_analysis/data_analysis.md`. Do not claim the website
  has been updated.
- Skip site build in one line.
- Run `python -m skore_skills git end-turn --stage data_analysis`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Name `report.html` or `html/data_analysis.html` as if the
  site was built.
- Run `python -m skore_skills site build`.

---

## CASE_09 — Notebooks on, site off fills without HTML

**User prompt:**
> EDA is done. Close the turn.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `data_analysis/data_analysis.md` was just written.
- `policy.notebooks` is true. `policy.site` is false.
- `export-ml-notebook` is installed.
- `jupytext` and `nbformat` are installed.
- No source-current `.ipynb` yet.

**Must do:**
- Run `python -m skore_skills notebook fill
  data_analysis/data_analysis.py`.
- Run `python -m skore_skills git end-turn --stage data_analysis`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Pass `--html` when the site gate is off.
- Run `python -m skore_skills site build`.
- `notebook convert` or `cells run`
  `data_analysis/data_analysis.py`.

---

## CASE_10 — Missing fill toolchain skips in one line

**User prompt:**
> EDA is done. Close the turn.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `data_analysis/data_analysis.md` was just written.
- `policy.notebooks` is true. `policy.site` is false.
- `export-ml-notebook` is installed.
- `jupytext` and `nbformat` are not importable; `notebook fill`
  fails with that ImportError.

**Must do:**
- Skip the fill in one line, naming `add-python-package` for
  `jupytext` and `nbformat`.
- Run `python -m skore_skills git end-turn --stage data_analysis`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Fail the data-analysis turn because fill failed.
- Run `pixi add` / `uv add` from this skill.

---

## CASE_11 — Default run adds ML-gap cells

**User prompt:**
> Explore the California housing CSV. Target is MedHouseVal.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`.
- `add-python-package` is installed.
- User chose **run** for G-DATA-ANALYSIS.
- IPython is available.

**Must do:**
- Load `plot-ml-figure` if installed before writing figure cells.
- Load `add-python-package` for `matplotlib` and `seaborn` (and
  skrub / pandas if missing).
- Write duplicate, target-distribution, bivariate-vs-target, and
  leakage cells in `data_analysis/data_analysis.py` for
  **regression only**.
- Use seaborn figure-level plots (`displot` / `relplot`); save
  PNGs and leave figures as cell output. Feature-vs-target is
  one faceted `relplot` (`bivariate_grid.png`), last expression
  `g`.
- After `data_analysis.md`, AskUserQuestion one pick, none
  recommended: Choose additional pre-defined option; Provide a
  query to extend the exploration; Automatic exploration related
  to the data and problem; Describe a plot; Close.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Re-plot TableReport univariate histograms or the association
  matrix in extra cells.
- Add a **second** target histogram / extra `displot` besides
  the one regression snippet. Copying
  `templates/target_regression.py` into
  `data_analysis/data_analysis.py` (that file's `displot`) is
  required, not a violation.
- Install sklearn, skore, pytest, or plotly on the default path.
- Train/test split the raw table.
- Run `git end-turn` before the user picks Close.
- Leave classification / no-target branches (`if TASK`,
  `if TARGET is None`) in the notebook.
- Write skill ids, `skore_skills`, `cells run`, or "generated from
  …" process notes into `data_analysis/data_analysis.py` /
  `data_analysis.md` markdown or `#` comments.
- Call `plt.close` or `import matplotlib.pyplot` for these
  figures.
- Loop over columns with a trailing `g` (that is not displayed).
- Ask the user how to group files when only one data file is in
  play. A checklist line that says the grouping question was
  skipped is not a grouping question.

---

## CASE_12 — Unspecified target asks, does not guess

**User prompt:**
> Explore the dataset.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. User chose **run**.
- JOURNAL Goal does not name a column.
- Column names are `A`, `B`, `C`.

**Must do:**
- AskUserQuestion for the target (column list plus "no target
  yet") before writing target-aware cells.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Guess a target column silently.
- Skip the duplicate-row cell when the user picks "no target yet".
- Write target-distribution / bivariate / leakage cells when the
  user picks "no target yet".

---

## CASE_13 — Prompt already asked for PCA

**User prompt:**
> Explore the data and add a PCA plot of the numeric columns.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. User chose **run**. Target is known.
- `add-python-package` is installed.

**Must do:**
- Load `add-python-package` for `scikit-learn`.
- Append a PCA cell from `references/extra_analyses.md`.
- Do not re-ask PCA on the pre-defined-option board.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Treat PCA as a pipeline preprocessor in this skill.
- Run `pixi add scikit-learn` from this skill.

---

## CASE_14 — Close after default pass keeps sklearn off

**User prompt:**
> Explore the dataset. Target is MedHouseVal.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Default notebook, extras.json, and `data_analysis.md` are on
  disk.
- User picks **Close** on the five-option continuation board.

**Must do:**
- AskUserQuestion one pick, none recommended: Choose additional
  pre-defined option; Provide a query to extend the exploration;
  Automatic exploration related to the data and problem;
  Describe a plot; Close.
- After Close, write 2–6 sentences of findings. Do not name
  `data_analysis/data_analysis.md`. Do not claim the website
  has been updated.
- Run `python -m skore_skills git end-turn --stage data_analysis`
  after Close.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Paste the full `data_analysis.md` into chat.
- Load `add-python-package` for sklearn / scipy / statsmodels.

---

## CASE_15 — A continuation pick does not end the turn

**User prompt:**
> Explore the dataset. Target is MedHouseVal.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `data_analysis/data_analysis.md` was just written.
- `policy.site` is true.
- `export-ml-site` is installed.
- The user has not picked Close.
- When `site build` runs, its output ends with `file:///workspace/report.html`.

**Must do:**
- Run `python -m skore_skills site build --if-stale` after the md and
  before the continuation board.
- Say the website has been updated and include
  `file:///workspace/report.html`. Do not name `data_analysis.md`
  or `html/data_analysis.html`. Do not say double-click or "no
  server".
- AskUserQuestion one pick, none recommended: Choose additional
  pre-defined option; Provide a query to extend the exploration;
  Automatic exploration related to the data and problem;
  Describe a plot; Close.
- Choosing one of the four continuations does not run
  `git end-turn`.
- Stay in `explore-ml-data`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Run `python -m skore_skills git end-turn`.
- Invent a domain-specific checklist skill or `references/domains/`.
- Run `python -m skore_skills site build` again on the
  continuation board.
- Run a second notebook execution after the checkpoint.
- Ask keep-exploring versus close as its own question, instead
  of the five-option board.
- Say “extra-analyses” or “standard extra analysis” on that
  board.

---

## CASE_16 — Keep exploring then research

**User prompt:**
> Is 0.97 correlation with the target leakage?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- EDA markdown exists. User picked **Automatic exploration
  related to the data and problem**. The prompt already names a
  leakage concern.
- `status.skills.research-ml-practice` is true.

**Must do:**
- Preview Automatic exploration as LLM research over the recorded
  EDA that may write a scratch note, with no model fitting or
  testing before the measurement-choice board.
- Load `research-ml-practice` with the named leakage concern
  (skip the canned extra-analysis survey).
- Summarize the scratch note in chat (what is happening + why
  it matters here).
- AskUserQuestion `allow_multiple` on `measure` rows only. The question's last line is exactly: Select each one you want.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Drop the correlated column from the raw data.
- Run `git end-turn` in this keep-exploring pass.
- Copy literature into modelling implications as if it were
  measured.
- Append a `declare` or `evaluate` row as an EDA cell.
- In the question, ask the user to uncheck a box, or say that a
  box starts checked. A recorded status is not the box's starting
  state.

---

## CASE_17 — Research skill missing is a one-line skip

**User prompt:**
> Is 0.97 correlation with the target leakage?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- EDA markdown exists. User picked **Automatic exploration
  related to the data and problem**.
- `status.skills.research-ml-practice` is false or absent.

**Must do:**
- One-line skip that `research-ml-practice` is not installed.
- Re-ask the five-option continuation board, including Close.
  Do not say “extra-analyses” on that board.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Invent papers or leakage thresholds from memory.
- Run `git end-turn` in this keep-exploring pass.

---

## CASE_18 — Leakage question while EDA is already done

**User prompt:**
> Is 0.97 correlation with the target leakage?

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `data_analysis/data_analysis.md` exists.
- JOURNAL § Data understanding records `Status: done`.
- `status.data_analysis` is present.
- The user did not pick a continuation option first.
- `status.skills.research-ml-practice` is true.

**Must do:**
- Do not overwrite `data_analysis/data_analysis.py`.
- Load `research-ml-practice` (Keep exploring § Automatic
  exploration; named concern — skip the canned extra-analysis
  survey).
- Summarize the scratch note in chat.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Stop as CASE_04 (EDA already recorded, no refresh).
- Run `git end-turn` in this pass.
- Re-run `cells run` or rewrite the default notebook.

---

## CASE_19 — No target omits target-aware cells

**User prompt:**
> Explore the dataset.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. User chose **run**.
- User picked **no target yet** on the target AskUserQuestion.
- `plot-ml-figure` is installed.

**Must do:**
- Write TableReport and duplicate-row cells.
- Omit `templates/target_regression.py` and
  `templates/target_classification.py`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Write `if TARGET is None` / `if TASK` branches for unused
  tasks.
- Call `plt.close`.

---

## CASE_20 — Automatic exploration uses the problem class

**User prompt:**
> Keep exploring. Research extra analyses for this table.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `data_analysis/data_analysis.md` exists with Open questions.
- JOURNAL names California housing / MedHouseVal.
- User picked **Automatic exploration related to the data and
  problem**.
- `status.skills.research-ml-practice` is true.

**Must do:**
- Load `research-ml-practice` with the canned JOURNAL+EDA
  extra-measurement question (problem class, not the dataset
  proper name).
- Read `scratch/research/survey-<slug>.md` when tools ran. A
  message that says tools did not run, and does not claim the
  survey was read, satisfies this.
- AskUserQuestion `allow_multiple` on **only** sourced
  **`measure`** extras from that note. The question's last line is exactly: Select each one you want.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Search `california_housing`, `sklearn.datasets`, or a
  sklearn fetcher name.
- Offer pipeline / learner / `GridSearch` extras on the EDA
  board.
- Copy Open questions onto the board without a source.
- Write a ranked pipeline action table in the survey note.
- Run `git end-turn` in this pass.
- Name `Close` as recommended on the continuation board.
- In the question, ask the user to uncheck a box, or say that a
  box starts checked. A pre-flight checklist is not the question.
  A recorded status is not the box's starting state.

---

## CASE_21 — Multiple files ask grouping before the notebook

**User prompt:**
> Explore the data. Target is y.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`.
- User chose **run** for G-DATA-ANALYSIS.
- IPython is available. `add-python-package` is installed.
- Raw files: `data/a_1.csv`, `data/a_2.csv`, `data/b.parquet`.
- Families are not yet confirmed.

**Must do:**
- AskUserQuestion grouping (none recommended): Use a proposed
  grouping / Profile every file separately / I will describe
  the grouping — before placing `data_analysis/data_analysis.py`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Place `data_analysis/data_analysis.py` or concat shards on
  disk before the user answers the grouping ask. Do not treat
  `family_a` / `family_b` as confirmed until that pick. Proposing
  those slugs and an in-memory concat **inside** "Use the
  proposed grouping" is required, not a violation.
- Write a joined frame to disk.
- Append join-coverage cells on the default pass.

---

## CASE_22 — Two confirmed families, default pass

**User prompt:**
> Explore the data. Target is y.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`.
- User chose **run** for G-DATA-ANALYSIS.
- IPython is available. `plot-ml-figure` is installed.
- Raw files: `data/a_1.csv`, `data/a_2.csv`, `data/b.parquet`.
- User confirmed families: `family_a` is `data/a_1.csv` and
  `data/a_2.csv` (columns `id`, `y`); `family_b` is
  `data/b.parquet` (columns `id`, `z`).

**Must do:**
- Write a TableReport cell and HTML per family from
  `report.html_snippet()` (`data_analysis_family_a.html`,
  `data_analysis_family_b.html`).
- Embed one glance iframe per family in
  `data_analysis/data_analysis.md`.
- Put target-distribution, bivariate, and leakage cells only on
  `family_a`.
- Append `templates/drift.py` (shared column names).
- Write `scratch/data_analysis/family_a.json`,
  `scratch/data_analysis/family_b.json`, and `extras.json` with
  `tables[]`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Append join-coverage cells on the default pass.
- Install sklearn, skore, or pytest.
- Write a joined frame to disk.
- Put target/bivariate/leakage cells on `family_b`.

---

## CASE_23 — Keep exploring join keys / coverage

**User prompt:**
> Keep exploring. Add join keys / coverage.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Two families are already in `data_analysis/data_analysis.py`
  (`family_a` with `id`, `y`; `family_b` with `id`, `z`).
- `data_analysis/data_analysis.md` exists.
- User picked **Choose additional pre-defined option**, then
  **Join keys / coverage**.

**Must do:**
- Append `templates/join_coverage.py` (shared columns and
  unmatched counts on `id`).
- Refresh facts and rewrite `data_analysis.md` from results.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Write a joined frame to disk.
- Replace `FRAME` with the merge or add a TableReport on the
  join.
- Run `git end-turn` in this keep-exploring pass.

---

## CASE_24 — Single file skips grouping

**User prompt:**
> Explore the data. Target is y.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`.
- User chose **run** for G-DATA-ANALYSIS.
- IPython is available.
- One raw file: `data/a.csv` (columns `id`, `y`).

**Must do:**
- Write `data_analysis/data_analysis.py` without an AskUserQuestion
  grouping board.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- AskUserQuestion grouping (Use a proposed grouping / Profile
  every file separately / I will describe the grouping).
- Append join-coverage cells.

---

## CASE_25 — Site on rebuilds before the continuation board

**User prompt:**
> Explore the California housing CSV. Target is MedHouseVal.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`.
- User chose **run** for G-DATA-ANALYSIS.
- IPython is available.
- `policy.site` is true.
- `export-ml-site` is installed.
- When `site build` runs, its output ends with `file:///workspace/report.html`.

**Must do:**
- After `data_analysis.md` and JOURNAL, name
  `python -m skore_skills site build --if-stale`.
- Say the website has been updated and include
  `file:///workspace/report.html`. Do not name `data_analysis.md`
  or `html/data_analysis.html`. Do not say double-click or "no
  server".
- Then AskUserQuestion one pick, none recommended: Choose
  additional pre-defined option; Provide a query to extend the
  exploration; Automatic exploration related to the data and
  problem; Describe a plot; Close.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Run `notebook fill` or `git end-turn` before the user picks
  Close.
- Fail the continuation board if site build errors; name the
  error.

---

## CASE_26 — Present analysis cannot be marked skipped

**User prompt:**
> Skip the data analysis. We already wrote it.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- `data_analysis/data_analysis.md` exists.
- `status.data_analysis` is `present`.

**Must do:**
- Say the written analysis stays.
- Offer to run exploration again (overwrite
  `data_analysis/data_analysis.*`) or keep it.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Write a JOURNAL Data understanding Status of `skipped`.
- Overwrite `data_analysis/data_analysis.md` before the user
  accepts a re-run.

---

## CASE_27 — Pending setup loads project setup

**User prompt:**
> Explore the dataset.

**Assumed workspace state:**
- No `src/` and no `journal/`. `data/` has one CSV.
- `status.setup.pending` is `env`, `workspace`, `git`.
- `status.setup.env` and `status.setup.workspace` are `missing`,
  not `declined`.
- `status.skills.setup-ml-project` is true.
- `status.data_analysis` is `missing`.

**Must do:**
- Load `setup-ml-project` and stop.
- Do not place `data_analysis/data_analysis.py`.
- Do not invent `PROJECT_ROOT` or write a root `JOURNAL.md`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Run `python -m skore_skills cells run`.
- Ask the tabular-library question before setup returns.

---

## CASE_28 — A shipped train and test pair is not joined

**User prompt:**
> Explore the files in `data/`. Target is y.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`.
- User chose **run** for G-DATA-ANALYSIS.
- IPython is available.
- Raw files: `data/train.csv` and `data/test.csv`, same columns,
  including `y`.

**Must do:**
- Name both files in the summary as a training table and a test
  table.
- Leave the evaluation choice for later. Do not concatenate the
  two files.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Persist a joined modeling table.
- Split rows again during exploration.
- Lock a fold count or write `predefined` into the journal.

---

## CASE_29 — Missing mkdocs-material retries before the continuation board

**User prompt:**
> Explore the California housing CSV. Target is MedHouseVal.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`.
- User chose **run** for G-DATA-ANALYSIS.
- IPython is available.
- `policy.site` is true.
- `export-ml-site` is installed.
- `add-python-package` is installed.
- `python -m skore_skills site build --if-stale` printed
  `mkdocs-material is required; add it with add-python-package`.
- When the retry succeeds, its output ends with `file:///workspace/report.html`.

**Must do:**
- After `data_analysis.md` and JOURNAL, load `add-python-package`
  for `mkdocs-material` and run `python -m skore_skills site build --if-stale`
  again.
- After that retry succeeds, say the website has been updated
  and include `file:///workspace/report.html`. Do not name
  `data_analysis.md` or `html/data_analysis.html`. Do not say
  double-click or "no server".
- Then AskUserQuestion one pick, none recommended: Choose
  additional pre-defined option; Provide a query to extend the
  exploration; Automatic exploration related to the data and
  problem; Describe a plot; Close.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Run `pixi add` or `uv add`.
- Skip the continuation board.
- Run `notebook fill` or `git end-turn` before the user picks
  Close.

---

## CASE_30 — Two regression targets are one multi-output analysis

**User prompt:**
> Explore `data/energy.csv`. Predict both `load` and `temp`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`.
- User chose **run** for G-DATA-ANALYSIS.
- IPython is available.
- `load` and `temp` are numeric columns with many distinct values.
  Other columns are features.

**Must do:**
- Append `templates/target_multioutput_regression.py` once and set
  `TARGETS` to `load` and `temp`.
- Save `target_distributions.png` and `bivariate_targets.png`.
- Keep both targets out of the feature list and the leakage flags.
- Report target-vs-target correlation and the count of rows where
  every target is present.
- Write `extras.json` `targets` with one entry per column, plus
  `complete_target_rows` and `target_target_corr`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Copy `templates/target_regression.py` once per column or beside
  the multi-output snippet.
- Treat `temp` as a feature of `load`, or the reverse.
- Choose one column as the only target.
- Leave `if TARGET` or `if TASK` in the notebook.
- Write a scalar `target` or `task` field in `extras.json`.

---

## CASE_31 — Mixed targets are recorded, not jointly modeled

**User prompt:**
> Explore `data/claims.csv`. The outputs are `amount` and `fraud`.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`.
- User chose **run** for G-DATA-ANALYSIS.
- `amount` is numeric with many distinct values. `fraud` is binary.

**Must do:**
- Record both columns in materialize `<TARGETS>` and `<TASKS>`:
  `amount` regression, `fraud` classification.
- Leave the notebook without a target snippet.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Append `templates/target_multioutput_regression.py`.
- Drop one output and explore the other as the only target.
- Write a scalar `target` or `task` field in `extras.json`.

---

## CASE_32 — Graphviz diagnostic does not discard EDA

**User prompt:**
> Explore the California housing CSV. Target is MedHouseVal.

**Assumed workspace state:**
- `status.setup.pending` is empty.
- Scaffold exists. G-TABULAR is `pandas`.
- User chose **run** for G-DATA-ANALYSIS.
- `add-python-package` is installed. Loading it for `skrub`
  returns the Graphviz repair diagnostic and ends that install
  sequence.

**Must do:**
- Load `add-python-package` for `skrub` (and matplotlib / seaborn
  if missing).
- Quote the Graphviz diagnostic in one line and continue the
  analysis. Write `data_analysis/data_analysis.py`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- End the turn because Graphviz SVG rendering failed.
- Prescribe `dot -c` or a Homebrew Graphviz install from this skill.
- Discard the analysis that was already underway.
