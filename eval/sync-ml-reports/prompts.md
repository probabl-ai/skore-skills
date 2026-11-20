# sync-ml-reports eval

---

## CASE_01 — Switch local to Hub

**User prompt:**
> Switch the default destination to Hub workspace acme-corp at
> https://skore.probabl.ai for project load-forecast. Transfer now,
> not a dry run.

**Assumed workspace state:**
- `policy.skore_mode` is `local`.
- `experiments/01_baseline.py` has `skore.Project(name="load-forecast",
  mode="local", workspace=str(PROJECT_ROOT / "reports"))`.
- `add-python-package` is installed.
- `SKORE_HUB_API_KEY` is set. `SKORE_HUB_URI` is unset.
- `skore` is on PATH.
- `persist-ml-git` and `triage-ml-task` are installed.

**Must do:**
- Run `python -m skore_skills status`.
- Load `add-python-package` for Skore at Hub mode.
- Name `skore sync load-forecast --from=local --to=hub` with
  `--from-workspace` on `reports/`, `--to-workspace=acme-corp`,
  and `--host https://skore.probabl.ai`.
- Persist `python -m skore_skills policy set skore_mode hub`.
- Rewrite the Project init to Hub form
  (`mode="hub"`, `workspace="acme-corp"`,
  `host="https://skore.probabl.ai"`, no `skore.login`).
- Run `python -m skore_skills git end-turn --stage evaluate`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Call `skore.login` or `Project.sync` in Python.
- Run `skore hub api-key generate` when `SKORE_HUB_API_KEY` is set.
- Pass `--hub-url`.
- Run `git commit` in this skill.
- Ask a first-time local / Hub / MLflow destination pick.
- Pass `--from-workspace` / `--to-workspace` as an MLflow flag.

---

## CASE_02 — Copy only, keep local mode

**User prompt:**
> Copy our local reports to Hub workspace acme-corp at
> https://skore.probabl.ai for project load-forecast. Keep
> evaluating locally. Transfer now, not a dry run.

**Assumed workspace state:**
- `policy.skore_mode` is `local`.
- Project name is `load-forecast`.
- `add-python-package` is installed.
- `SKORE_HUB_API_KEY` is set. `SKORE_HUB_URI` is unset.
- `skore` is on PATH.

**Must do:**
- Run `python -m skore_skills status`.
- Name `skore sync` from `local` to `hub` with Hub
  `--to-workspace=acme-corp` and
  `--host https://skore.probabl.ai`.
- Run `python -m skore_skills git end-turn --stage evaluate`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Persist `policy set skore_mode`.
- Rewrite Project init blocks.
- Call `skore.login` or `Project.sync` in Python.
- Run `skore hub api-key generate` when `SKORE_HUB_API_KEY` is set.
- Pass `--hub-url`.
- Run `git commit` in this skill.

---

## CASE_03 — Unset mode does not steal G-SKORE-MODE

**User prompt:**
> Upload the reports to Hub.

**Assumed workspace state:**
- `policy.skore_mode` is unset.
- `evaluate-ml-pipeline` is installed.

**Must do:**
- Run `python -m skore_skills status`.
- Stop because report destination must be chosen in the evaluate
  workflow first.
- The close is only that stop: the destination is not chosen yet
  and is picked when a report is stored. Do not list local, Hub,
  or MLflow, a workspace name, or a tracking URI.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Run `skore sync`.
- Persist `policy set skore_mode`.
- Ask local / Hub / MLflow as this skill's first destination
  pick.

---

## CASE_04 — Missing Hub API key

**User prompt:**
> Switch the default destination to Hub workspace acme-corp at
> https://skore.probabl.ai. Transfer now, not a dry run.

**Assumed workspace state:**
- `policy.skore_mode` is `local`.
- Project name is `load-forecast`.
- `add-python-package` is installed.
- `SKORE_HUB_API_KEY` is unset. `SKORE_HUB_URI` is unset.
- `skore hub api-key list` has no row for this host and workspace.
- `skore` is on PATH.

**Must do:**
- Run `python -m skore_skills status`.
- Run `skore hub api-key generate --host https://skore.probabl.ai
  --workspace acme-corp` and wait for its browser device login
  before `skore sync`.
- After that key exists, name `skore sync` from `local` to `hub`
  with `--to-workspace=acme-corp` and
  `--host https://skore.probabl.ai`.
- Persist `policy set skore_mode hub` and rewrite the Project init
  with `workspace="acme-corp"` and
  `host="https://skore.probabl.ai"`.

**Must NOT do:**
- Put catalog skill ids, HITL, `G-PKG-NAME` / `G-ENV-MGR` / `G-SKORE-MODE` / `G-TABULAR` / `G-CV-SPLITTER`, or `python -m skore_skills` / `env add` in user-facing questions or the close narrative (trailing `G-REPORT-LOCATOR` / `G-AUDIT-FINDING` and unmanaged `pixi add` / `uv add` / `pip install` lines are allowed).
- Stop only because `SKORE_HUB_API_KEY` is unset.
- Call `skore.login` or `Project.sync` in Python.
- Run `skore sync` before `skore hub api-key generate`.
- Pass `--hub-url` or `--force`.
- Read `~/.skore.hub/credentials.json` or `.skore` for the key.
