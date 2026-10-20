---
name: review-ml-experiment
description: >
  Read the stored report, then write one idea file and one Ideas row per
  candidate. Load it with `project.get` and create each issue or tip with
  `experiment create`. Do not edit JOURNAL.md, idea files, or design notes.
metadata:
  modelTier: medium
---

# Review ML Experiment

The project is the only store. Load the report with `project.get(experiment_id)`.
Create each issue or tip with
`python -m skore_skills experiment create --stem <stem> --question "<question>" --source-id <id> --check-code <code>`.
Read the journal with `python -m skore_skills journal show`. Do not edit
`JOURNAL.md`, `journal/ideas/`, or a design note. Scripts used to inspect the
report may live in a temporary directory and are deleted after the turn.
If a later step says to edit `JOURNAL.md`, an idea file, or a design note,
skip that step and use the commands above.

Optional loop step after evaluate. Record-outcome stays with the
caller. This skill writes idea files and their Ideas rows. The
stem is whichever experiment was reviewed. Check results were
stored with the report, so the audit reads them.

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Idea files describe this report and the follow-up — not skill
ids, `cells run`, or the wrapper CLI.

## Procedure

1. Run `python -m skore_skills status` and
   `python -m skore_skills review consent --stem <stem>`. Treat
   JSON `action` as authoritative.
   - `stop` — no `scratch/results/<stem>/report.html`. Name that
     file and stop. Do not audit. Do not record-outcome.
   - `audit` — report exists, digest does not. Load
     `audit-ml-pipeline` when installed. That skill runs
     `materialize.py` once and does not execute the audit file.
   - `proceed` — digest already on disk. Do not re-run
     `materialize.py` unless the user asked to re-audit. A
     re-audit loads `audit-ml-pipeline`; that skill runs
     `materialize.py` once.
     Otherwise refresh idea files from the existing digest.
2. Missing audit skill → one-line skip. Return
   `n/a — audit not run` and write no idea files. Do not open
   the Project or call `report.*` here.
3. Read the design note, the EDA summary, the last History row,
   and the digest. One candidate per `Issues:` / `Tips:` line.
   A methodological gap the design note named and this run did
   not test is another candidate. A user idea or a literature
   query is not a candidate here: after this skill returns,
   `shape-user-idea` or `search-ml-literature` writes that file
   and its Ideas row when the user asks. Load `research-ml-practice` only if
   `status.skills.research-ml-practice` is true and an audit or
   design candidate needs sources; otherwise one-line skip. Do
   not invent papers, metrics, or a winner.
4. Write one file per candidate at
   `journal/ideas/<stem>-<slug>.md` with Experiment, Source
   (`audit:<stem>:checks.<code>` or `design:<stem>`), Triage
   `open`, Question, Why now, What changes, Open gaps. No
   acceptance criteria. For a check candidate, read the
   documentation URL on that line and apply that page's
   recommendation in What changes. On a refresh, keep an existing file's
   `Triage` value and the matching Ideas status. A new candidate
   is `open`.
5. Upsert one `## Ideas` row per file in `journal/JOURNAL.md`.
   If that table is missing, insert it between History and
   Backlog. Columns: Question, Status, Experiment, Source.
   Question is the file's Question as plain text, not a link.
   Status is `open`, `discarded`, or `aside`, matching `Triage`.
   A `promoted` file has no Ideas row. Experiment is this run's
   stem. Source is copied verbatim. Edit only that table.
6. Return the digest, JSON `finding` from
   `python -m skore_skills audit finding --stem <stem>`, the
   locator from `python -m skore_skills loop locator --stem <stem>`,
   and the idea paths.

## Stop conditions

- On `proceed`, do not re-run `materialize.py` unless the user
  asked to re-audit.
- Do not write History, Backlog, Status, or a design note.
  The Ideas table is the only `JOURNAL.md` edit.
- Do not call `skore.evaluate` or `project.put`.
- Do not pick a winning idea.
- Do not invent a missing child's procedure.
