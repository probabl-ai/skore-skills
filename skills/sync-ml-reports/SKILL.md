---
name: sync-ml-reports
description: >
  Copy skore reports between local, Hub, and MLflow, and optionally switch the
  upload destination. Trigger when the user asks to sync or migrate reports,
  switch skore mode, upload reports to Hub or MLflow, or pull Hub/MLflow
  reports onto disk. First G-SKORE-MODE pick stays evaluate-ml-pipeline.
metadata:
  modelTier: medium
---

# Sync ML Reports

Copy reports with the `skore` CLI. Switch the default destination
only when the user asked to. Do not evaluate, audit, or invent
`Project.sync` Python.

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Ask where reports live (disk, Hub, MLflow) in those words. Do not
name `G-SKORE-MODE`, skill ids, or the wrapper CLI in the
question. `skore sync` output may appear in the close as the
sync table.

## Procedure

1. Run `python -m skore_skills status`. Read `policy.skore_mode`
   and `skills`. Open `experiments/` and `audit/` for the
   `skore.Project(...)` init block: `name=`, Hub `workspace=`,
   MLflow `tracking_uri=`. Local store is always the workspace
   `reports/` directory (absolute path). Never omit
   `--from-workspace` / `--to-workspace` on a **local** endpoint.

2. If `policy.skore_mode` is unset: STOP. First pick is
   G-SKORE-MODE in `evaluate-ml-pipeline`. Do not ask local / hub
   / mlflow here. Load that skill only if
   `status.skills.evaluate-ml-pipeline` is true and the user
   asked to evaluate; else one-line skip. The close is only this
   stop: the destination is not chosen yet and is picked when a
   report is stored. Do not list local, Hub, or MLflow, a
   workspace name, or a tracking URI. Do not use the
   source-to-destination close below.

3. **AskUserQuestion** for any answer not already in the request.
   Ahead of each question, state in 2–4 lines what the answer
   authorizes — which reports move where, whether `skore_mode` and
   the Project init lines get rewritten — and the facts it rests
   on: the current mode, the discovered report count, the
   endpoint. A file link is an addition, never the context.

   - **Intent.** Switch default destination (sync, then persist
     `skore_mode` and rewrite every Project init) vs copy only
     (sync, leave policy and experiment files).
   - **Destination** — same three options as G-SKORE-MODE:
     `local` (disk, no account), `hub` (https://skore.probabl.ai),
     `mlflow` (tracking server). Hub: ask the workspace name; it
     MUST NOT contain `/`. MLflow: ask `tracking_uri`; confirm a
     bare `host:port` as `http://host:port`. Do not default the
     URI.
   - **Project name** if `name=` is missing or disagrees across
     files.
   - **Dry-run first** vs transfer now.

   If intent is **switch** and destination equals
   `policy.skore_mode`, stop in one line.

4. Destination extras: load `add-python-package` only if
   `status.skills.add-python-package` is true, for Skore at the
   **destination** mode (`env add-skore --mode <dest>`). If that
   skill is missing, name Skore for the destination and stop. Do
   not splice `pip install` / `skore[...]` here.

5. If Hub is source or destination: require `SKORE_HUB_API_KEY` in
   the environment. Missing → name it and stop. Do not open a
   browser login. Do not read `.skore` for the key.

6. Build `skore sync`. If `skore` is not on PATH, name
   `skore-cli` and stop. Do not call `skore.Project.sync` in
   Python.

   ```bash
   skore sync <project> --from=<source_mode> --to=<dest_mode>
   ```

   Source mode is `policy.skore_mode`. Add:

   | Endpoint | Flags |
   |---|---|
   | local | `--from-workspace` or `--to-workspace` = resolved `reports/` |
   | hub | `--from-workspace` or `--to-workspace` = Hub workspace name (required) |
   | mlflow | `--tracking-uri=...`; never `*-workspace` |

   `--to-project` only if the destination name differs.
   `--hub-url` only when `SKORE_HUB_URI` (or the user) names a
   non-default Hub. `--both` only if the user asked to copy
   missing reports both ways. Otherwise one-way.

   If the user picked dry-run first, run with `--dry-run`, show
   the plan, then ask to transfer. Live run omits `--dry-run`.

   Usage/auth/backend errors: name stdout/stderr and stop. Do not
   invent a Python fallback. Empty output `No reports to
   synchronize.` is success (nothing to copy; a **switch** may
   still continue).

7. **Switch intent only**, after a successful (or empty) sync:
   `python -m skore_skills policy set skore_mode <dest>`.
   Rewrite every Project init in `experiments/` and `audit/` to
   the destination form in
   `evaluate-ml-pipeline/references/g_skore_mode.md` (audit must
   match the paired experiment, byte-for-byte modulo formatting).
   If dest is **local**, `mkdir reports` (`exist_ok`); no README.
   If **hub** or **mlflow**, do not create `reports/`.
   Do not edit `JOURNAL.md`. `Project.sync` copies the objective
   and the experiment rows.

   **Copy-only:** do not `policy set`, rewrite init, mkdir, or
   edit JOURNAL.

## Stop conditions

- Do not steal first G-SKORE-MODE when `skore_mode` is unset.
- Do not silently change a recorded mode; switch requires the
  switch intent (or an explicit user request to switch).
- Do not `git commit`.
- Do not evaluate, `project.put`, or audit.
- Do not pass `*-workspace` on an MLflow endpoint.
- Do not omit `*-workspace` on a local or Hub endpoint.

## End of turn

### User-facing close

This close applies only after a sync. An unset `policy.skore_mode`
uses the step-2 stop instead.

Short story: source → destination, whether policy changed, and
the `skore sync` table or `No reports to synchronize.` Do not
dump experiment files.

Then `python -m skore_skills git end-turn --stage evaluate`
(the persist bucket for this work; this is not a CV run). If
JSON `action` is `invoke`, load `persist-ml-git` only if
`status.skills.persist-ml-git` is true and stop; that skill
returns to triage. If persist is missing, name the pending
`staged` paths and stop. Otherwise load `triage-ml-task` only if
`status.skills.triage-ml-task` is true; else stop. No `git
commit`.
