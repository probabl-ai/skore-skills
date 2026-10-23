# Probabl Skills

A set of skills to steer your AI-assisted machine learning experiments.
The skills help you:

- build your machine learning pipeline with core data science libraries
  (e.g. scikit-learn, skrub, skore, pandas, polars) while ensuring
  your agent follows correct methodologies
- evaluate and store your results so you can easily audit and get insights from them
- connect your agent to [Skore Hub](https://skore.probabl.ai/) to get a comprehensive view of
  your experiments and results
- iterate on your next experiments from a Skore audit digest (a
  separate backlog turn) and from your own feedback
- organize your workspace according to best practices for data science projects
  (e.g. cookiecutter template)

Probabl skills let you focus on the science while AI agents handle the implementation,
guided by two important ingredients: core data science libraries for maintainability  and
methodological best practices for running your machine learning experiments properly.

In practice, from a prompt such as:

```text
╭────────────────────────────────────────────────────────────────────────╮
│ > Given the context in the file `data/README.md` and the data located  │
│   in `data/`, let's build a first machine learning pipeline that will  │
│   serve as baseline for the next experiments that we are going to run  │
│   together.                                                            │
╰────────────────────────────────────────────────────────────────────────╯
```

you can expect your agent to start experimenting with you. The skills work well with
models such as Claude Opus and Sonnet and produce great results with smaller models such
as Qwen 3.7 Flash or DeepSeek v4.1 Flash. Each skill declares `metadata.modelTier`
(`small`, `medium`, or `big`). The eval maps those tiers to Qwen3.8 27B,
DeepSeek v4.1 Flash, and Qwen3.8 Max. A skill may also declare `metadata.role`
(`entry` or `helper`) when its caller continues after it loads. A helper runs on at
most its caller's tier, so a skill never loads a helper of a higher tier;
`tools/validate_catalog.py` enforces it.

As for agent harnesses, we tested them with Claude Code, OpenCode, Cursor, and GitHub
Copilot and found no significant difference in terms of skill invocation.

## Install

The skills installer is the `skore` command, included in the [`skore`](https://github.com/probabl-ai/skore)
package on PyPI and conda-forge.

```bash
# with pip
pip install skore
# with uv
uv tool install skore
# with pixi
pixi global install skore
# with conda
conda install conda-forge::skore
```

`skore skills install` with no arguments opens a picker for the source, the
skills, the agent, and the project or user directory. Without a terminal, that
same command prints the catalog.

Install a workflow pack by id when you do not need every skill:

```bash
skore skills install setup  # workspace, environment, git, export
skore skills install data_analysis  # data exploration
skore skills install model  # frame, build, smoke-test, evaluate, audit
skore skills install loop   # triage, explore, model, review, backlog, export
skore skills install export  # notebooks and documentation site
```

`skore skills install ml-experimentation` and `skore skills install all`
(or `--all`) install every skill in the catalog.

You can use `uvx` or `pixi exec` to install `skore` and run the installer in
an isolated environment:

```bash
uvx --from skore skore skills install
```

or

```bash
pixi exec --spec skore skore skills install
```

If you prefer `npx`, then you can use:

```bash
npx skills add probabl-ai/skore-skills
```

### Alternative — Claude Code plugin marketplace

If you only use Claude Code and prefer the native plugin flow, this repo is
also a [Claude Code plugin marketplace](https://docs.claude.com/en/docs/claude-code/plugin-marketplaces):

```bash
/plugin marketplace add probabl-ai/skore-skills
```

```bash
/plugin install probabl-skills@probabl-skills
```

`/plugin update` pulls new releases.

## Skills in detail

### Meta and setup actions

| Skill | Description |
| --- | --- |
| [triage-ml-task](skills/triage-ml-task/SKILL.md) | Session owner: list installed entry skills and ask which to run. |
| [review-ml-choices](skills/review-ml-choices/SKILL.md) | Show stored project choices and re-enter the skill that can change one. |
| [review-ml-experiment](skills/review-ml-experiment/SKILL.md) | Read the stored report, then write one idea file and one Ideas row per candidate. |
| [setup-ml-project](skills/setup-ml-project/SKILL.md) | Ask only the pending setup pieces. When Git is selected, commit the current files before setup writes only if that check finds files to preserve. |
| [setup-workspace](skills/setup-workspace/SKILL.md) | Detect or scaffold the standard ML workspace layout. |
| [setup-python-env](skills/setup-python-env/SKILL.md) | Detect the env manager and bootstrap the runtime, agent-tools, and composed development environments. |
| [setup-git](skills/setup-git/SKILL.md) | Initialize safe version control, including an optional commit of the tree before setup changes it. |
| [persist-ml-git](skills/persist-ml-git/SKILL.md) | Commit the current loop stage when the end-turn hook says invoke. |
| [model-ml-pipeline](skills/model-ml-pipeline/SKILL.md) | Require locked problem framing, write the first baseline design note for approval, then coordinate later choices, build, smoke testing, evaluation, and audit. |
| [export-ml-project](skills/export-ml-project/SKILL.md) | Coordinate executed notebooks and an offline MkDocs documentation site. |
| [sync-ml-reports](skills/sync-ml-reports/SKILL.md) | Copy skore reports between local, Hub, and MLflow, and optionally switch the upload destination. |

### ML pipeline lifecycle

| Skill | Description |
| --- | --- |
| [explore-ml-data](skills/explore-ml-data/SKILL.md) | Explore the dataset before designing any model. |
| [frame-ml-problem](skills/frame-ml-problem/SKILL.md) | Record the problem, deployment setting, metric, baseline, and fold count before any model code. |
| [research-ml-practice](skills/research-ml-practice/SKILL.md) | Literature research for an ML methodology concern. |
| [build-ml-pipeline](skills/build-ml-pipeline/SKILL.md) | Declare a skrub DataOps graph from the data source to the predictor after framing is locked. |
| [evaluate-ml-pipeline](skills/evaluate-ml-pipeline/SKILL.md) | Evaluate one sklearn-compatible learner with the locked validation scheme and persist structured skore reports. |
| [smoke-test-ml-pipeline](skills/smoke-test-ml-pipeline/SKILL.md) | Structural pytest: prediction count must match the predict-grid row count. |
| [audit-ml-pipeline](skills/audit-ml-pipeline/SKILL.md) | Audit a persisted skore report read-only and produce a reusable digest. |

### Ideas and backlog

| Skill | Description |
| --- | --- |
| [manage-ml-backlog](skills/manage-ml-backlog/SKILL.md) | Record experiment outcomes and triage idea files. A promoted idea moves from the Ideas table into a Backlog row. |
| [shape-user-idea](skills/shape-user-idea/SKILL.md) | Shape a user idea or a named artifact into one idea file and one Ideas row after they confirm. |
| [search-ml-literature](skills/search-ml-literature/SKILL.md) | Search scientific and technical sources and write one idea file and one Ideas row for the direction the user confirms. |

### Workspace and tooling

| Skill | Description |
| --- | --- |
| [add-python-package](skills/add-python-package/SKILL.md) | Add a dependency through the project env manager, or ask the user when the environment is user-managed. |
| [choose-python-library](skills/choose-python-library/SKILL.md) | Resolve a library choice and add the selected dependency. |
| [plot-ml-figure](skills/plot-ml-figure/SKILL.md) | Pick pandas, seaborn, plotly, or matplotlib before writing figure code. |
| [export-ml-notebook](skills/export-ml-notebook/SKILL.md) | Write a jupytext percent file out as a notebook with empty outputs. |
| [export-ml-site](skills/export-ml-site/SKILL.md) | Package workspace markdown and existing notebook HTML into an offline MkDocs site. |

Canonical package policy lives in the CLI; print it with `skore skills tools env stack` (the same command as `python -m skore_skills env stack`). `choose-python-library` resolves competing libraries.

When executed notebooks or the documentation site are enabled in a
workspace, workflow stages publish them at completed checkpoints before
the next user decision. Python percent files execute once: that run can
write the notebook, optional notebook HTML, and audit digest together.
Site checkpoints rebuild only when Markdown, notebook HTML, figures,
or result files changed. Unset or disabled notebook/site policies do
not enable these artifacts automatically.

## Website

The getting-started page lives in `site/` and is published at
<https://probabl-ai.github.io/skore-skills/>.

Build it with the `site` Pixi environment, which provides Node.js:

```bash
pixi run -e site site-build
```

Pull requests that change `site/`, `.catalog.json`, or the Pixi manifest build
the site in CI. GitHub Pages builds it from `main` when those same paths change.
A repo admin turns this on once: Settings → Pages → Source **GitHub Actions**.
If Pages is enabled after that workflow is already on `main`, run the **Pages**
workflow with **Run workflow**. Catalog edits still go through `pixi run check`.
