---
name: frame-ml-problem
description: >
  Record the problem, deployment setting, metric, baseline, and fold count
  before any model code. Ask every missing decision in one turn, from `frame
  show`, and store the table with `objective set`. Does not write Python,
  hyperparameters, splitters, or JOURNAL.md.

  TRIGGER when the user asks which metric to compare on, how new rows should
  be split, which baseline to use, or says a problem constraint changed. Not
  when they ask to run evaluation or CV.

  HOW TO USE: run `python -m skore_skills frame show`. Read each reference
  named in `questions` once, ask every key in `missing` in one message, and
  write every answered value. If a key is still unanswered, ask it and stop.
  If the write fills every required decision, set Status to `locked`, say
  those choices are reused and can be changed by name, then follow `proceed`.
  Do not ask to confirm. If that command is missing, or the recorded task is
  not classification, regression, or multi-output regression, follow Fallback
  below and do not invent the closed menu.
metadata:
  modelTier: medium
---

# Frame ML Problem

Store the modeling-decisions table with
`python -m skore_skills objective set "<table>"`. Do not edit `JOURNAL.md`
or write a design note. If a later step says to edit `JOURNAL.md`, skip
that step and use `objective set`.

Write `## Modeling decisions` in `journal/JOURNAL.md`. The table
is the contract. This skill does not declare a learner and does
not evaluate one.

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Journal rows describe this dataset. Do not name the skills
framework, the CLI, or a splitter class in the table. Questions
use data-science language — not skill ids, `G-*` names, or the
wrapper CLI.

## Procedure

1. Run `python -m skore_skills status`. If `status.setup.pending`
   is non-empty and `status.skills.setup-ml-project` is true,
   load `setup-ml-project` and stop. Do not start this skill.
   When it returns, continue. Do not load it again on this turn.
   If that skill is not installed, name the pending pieces in
   one line and stop. Do not invent `git init`, scaffold, or
   `env init`. If `status.setup.env` or `status.setup.workspace`
   is `declined`, stop in one line. A declined `git` or
   `editable` is not asked again; continue. If `data_analysis` is
   `missing` and `explore-ml-data` is installed, **AskUserQuestion**:
   explore first (default) or continue from facts the user stated.
   Explore loads `explore-ml-data` and stops. Do not invent dataset
   facts. Do not ask this again once `data_analysis` is `present`
   or `skipped`.
2. Run `python -m skore_skills frame show`. When the user is
   changing a locked constraint and named one decision, do not add
   `--revise` and do not treat `proceed` as the end of the turn.
   Show this command once, in a fence. The only sentence for it
   is: That command drops that one recorded decision. Then run
   `frame show` with no `--revise`.

   ```
   python -m skore_skills frame clear --cell <key>
   ```

   Ask the replacement in this message, the way step 5 asks a
   missing decision. Do not say that `frame show` will ask it.
   When the named decision is the comparison metric and the
   message does not state the new value, say that metric role,
   prediction goal, and folds stay filled. Then name the
   experiment file from the workspace state and say it still
   uses the previous metric and is not run, and that the next
   build or evaluate rewrites it after the table is complete
   again. The last line is: The comparison
   metric is MAE. Which metric replaces it? Nothing follows that
   line. When the named decision is the prediction
   goal and the message already states the new value, write that
   value. Metric role and the comparison metric are unanswered.
   Status is `draft`. Ask those two in this message. Do not write
   Status `locked`. Otherwise, if the message already states the
   new value, write it and ask only the decisions that are still
   empty. Do not ask Modify / Keep / Stop. Do not say the new
   value waits until next turn. Do not load `model-ml-pipeline`
   or git-close on this turn. When they are changing a constraint and did not
   name a decision, **AskUserQuestion** one pick among the filled
   decisions (skip `n/a`) and stop. Do not also ask for a typed
   answer. Do not `--revise` and do not edit the journal on that
   turn. JSON `action` is authoritative. Do not invent a menu.
   If the command is missing or exits without JSON, follow
   Fallback below. Do not open another reference. Do not guess
   candidates.
3. `stop` — say the JSON `reason` and stop.
4. `ask` / `uncovered` — follow Fallback below, including the
   table written in this message and the Status rule there. Say
   the reuse and change lines, and say there is no splitter
   translation. Do not load `build-ml-pipeline`. Stop this turn.
5. `ask` / `missing_keys` — read each distinct `reference` in
   `questions` once before asking. Do not open any other file
   under `references/`. Ask every key in `missing` in one
   message. For a question that has `candidates`, those are the
   options. When `candidates` is absent, ask for the value the
   reference describes. Draw on three sources, and only what they
   actually say: the EDA report, free-form text that came with
   the data if any is present (notes, a dictionary, or a README
   beside the raw files), and facts the user stated. If none of
   that text is present, do not invent it. When one of them
   already states the fact, quote it in the question. Write every
   Value the user answered in this turn. Do not rename the
   Variable column. Do not stop after the first decision.
   When the deployment makes other rows inapplicable, set those
   rows to `n/a` in the same edit. Horizon, gap, and time role
   are `n/a` unless deployment is time. Generalize-to is `n/a`
   unless deployment is groups. A fold count of `1` is one
   train/test split drawn from a single table. When the EDA
   report, the text shipped with the data, or the user already
   names a separate training table and test table, offer using
   that split in the folds question and write `predefined` if
   they choose it. Do not offer it otherwise. Do not write
   `prefit` in the table. Do not type `Revised on`; only that
   command writes that date. If any key in `missing` is still
   unanswered, set Status to `draft` once any decision is filled,
   ask those keys, and stop. Do not invent their values. Do not
   set Status to `locked`. Do not ask to confirm the table. If
   the write fills every required decision, set Status to
   `locked` in that same edit, not `draft`. Run
   `python -m skore_skills frame show` again in this turn. On
   `proceed`, say the reuse and change lines, then follow step 8.
   On `ask` / `set`, write Status `locked` only, say those lines,
   run `frame show` again, and follow step 8. If that `frame show`
   still returns `missing_keys`, the table was not complete: ask
   those keys and stop, and leave Status `draft`.
   Reuse and change lines, quoting JSON `context` in 2–4 lines:
   these choices are reused for the rest of the experiment so
   models stay comparable, and any one of them can be changed by
   naming it (for example the comparison metric). Do not say
   "lock" in those lines. Do not AskUserQuestion.
6. When the user named one decision and Status is `draft`, do not
   treat `set` as accepting the table. Show the same fenced
   command for that decision and stop. Do not write the new
   value. Do not say any other decision was dropped. The
   command's JSON list of dropped keys is the record. Status
   stays `draft`. That command stamps `Revised on`; do not type
   that date. The next `frame show` asks only keys that are still
   empty or invalid.
7. `ask` / `set` — the table was already complete and Status is
   still `draft`. Write Status `locked` only. Say the reuse and
   change lines from step 5. Run `frame show` again and follow
   step 8. Do not AskUserQuestion. The user sentence that opened
   this screen is not a choice.
   `ask` / `revise` is not a user question. Do not present
   Modify / Keep / Stop. Ignore those `choices`. Drop the named
   decision and ask the replacement, as in step 2.
8. `proceed` — the table is locked, and the user is not changing
   a named decision. If they are, step 2 already handled it. If
   `translation` is null, say
   that this lock has no splitter translation. Do not load
   `build-ml-pipeline` and do not return to `model-ml-pipeline`.
   Stop. If `model-ml-pipeline` dispatched this turn, return to
   that coordinator and stop. Do not start build, write a design
   note, or run the git close from here. If no experiment script
   exists and History has no running, done, or abandoned model
   row, and `status.skills.model-ml-pipeline` is true, load that
   skill and stop. Do not write a design note here. Do not
   `git end-turn`. Otherwise run
   `python -m skore_skills git end-turn --stage implement`. If
   JSON `action` is `invoke`, load `persist-ml-git` only if
   `status.skills.persist-ml-git` is true and stop. Otherwise
   load `triage-ml-task` only if that skill is installed.

## Live preview

After any turn that changes `journal/JOURNAL.md` (filled
decisions, Status, that command, or lock), coalesce all edits,
then, when `policy.site` is `true` and `export-ml-site` is
installed, run `python -m skore_skills site build --if-stale`
before the next question or stop. In that message, say the
website has been updated and paste the `file://` line from
that output verbatim. Do not name
`journal/JOURNAL.md`. `policy.site`
`null` or `false` does not enable or build the site. A
read-only `frame show` with no Markdown change does not build.

## Stop conditions

- Do not write Python, a pipeline, a test, or a design note.
- Do not put a class name or a constructor argument in the journal.
  `TimeSeriesSplit`, `KFold`, `GroupKFold`, and `gap=` stay out of
  the table.
- Do not re-ask a key that is absent from `missing`.
- Do not add an option that is absent from `candidates`.
- Do not open a reference the JSON did not name. When the
  command is missing, follow Fallback below instead of opening
  a file.
- A recorded decision changes when that command drops it, then
  filling it like any missing one. A complete fill sets Status
  to `locked` again. Do not ask Modify / Keep / Stop.
- That command is the only journal edit that drops a recorded
  decision, and only for the decision the user named. It stamps
  `Revised on`; do not type that date. Do not rewrite
  `experiments/`, `audit/`, or a report in this skill.
- After that decision is dropped, do not run an existing
  experiment script. Say that it still uses the previous splitter
  and metric. Show the command once, in a fence. The next build
  or evaluate rewrites it after the table is complete again.

## Fallback

Use this when `frame show` is missing, or when the problem is not
classification, regression, or multi-output regression. Do not
open any other file under `references/`. Do not invent the closed
candidate menu.

Tell the user, in a few lines, that the closed menu does not cover
this case, so the comparison has to be written in words. Ask one
question: what would count as a better result, and what is an honest
baseline. Draw on the EDA report, free-form text that came with
the data if any is present, and facts they stated. Quote a fact
those sources already give. If that text is absent, do not invent it.

Write the table in this same message:

- Prediction goal: `uncovered`
- Metric: the comparison, in their words, or empty if they did
  not state it
- Baseline note: the baseline, in their words, or empty if they
  did not state it
- Every other decision row: `n/a`, unless they already stated a value

Do not use placeholders. Do not leave the table for a later
message. Status is `locked` only when both the comparison and the
baseline are already stated. Otherwise Status is `draft`. The
words lock, modify, and stop stay out of the message.

Do not name a splitter class or write code. Say these choices are
reused for the rest of the experiment so models stay comparable,
and that any one of them can be changed by naming it. There is no
splitter translation.

If they say it is actually classification or regression, write that
goal instead of `uncovered` and stop. Do not set Status to `locked`.
The next `frame show` uses the closed menu.

If the command is missing, there is no JSON. The same write uses
the same lines. There is no splitter translation.
