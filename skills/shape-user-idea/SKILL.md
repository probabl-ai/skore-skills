---
name: shape-user-idea
description: >
  Shape a user idea or a named artifact into one idea file and one Ideas row
  after they confirm. Store it with `experiment create`. A topic with no
  artifact belongs to search-ml-literature. Do not edit JOURNAL.md or pick a
  backlog row.
metadata:
  role: helper
  modelTier: medium
---

# Shape User Idea

Store a confirmed idea with
`python -m skore_skills experiment create --stem <stem> --question "<question>"`.
Leave `--plan` unset so the row stays an idea, and omit `--source-id` for a
user idea. Do not edit `JOURNAL.md`, `journal/ideas/`, or a design note.
If a later step says to write those files, skip that step and use
`experiment create`.

Comes after review, beside the backlog. The user already has an
idea, a question, or an artifact. This skill writes
`journal/ideas/<slug>.md` and one Ideas row only after they
confirm. The backlog triages that file later.

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Questions and the confirmation paragraph describe this idea in
data-science terms — not skill ids or the wrapper CLI.

## Procedure

1. Run `python -m skore_skills status`. Read `journal/JOURNAL.md`
   Status and History, and `data_analysis/data_analysis.md` when it
   exists.
2. If the entry is not already a concrete idea, question, or
   artifact, **AskUserQuestion**: free-text or artifact. A URL,
   issue, path, or stated idea skips that menu.
3. A question about this project is answered from those files.
   Leave an unknown metric as `n/a`. Write no idea file and
   return to the caller.
4. A topic with no artifact ("what do people do for …") loads
   `search-ml-literature` only if
   `status.skills.search-ml-literature` is true. Otherwise
   one-line skip. Do not `WebSearch` for a paper from here.
5. An artifact is read, not reconstructed. Paper or doc URL:
   `WebFetch` the page. GitHub issue: `gh auth status` first;
   if unauthenticated, ask the user to run `gh auth login` or
   paste the body. Then `gh issue view`. Resolution: explicit
   URL, then `org/repo#N`, then bare `#N` only in the current
   `gh` repo — otherwise ask. Spec or notes file: read that
   file only.
6. Walk three questions. Do not fabricate a missing answer.
   - What are we trying to learn?
   - Why now? Quote the user or the artifact.
   - What changes versus the last experiment, in prose?
7. If the idea changes the project goal in `journal/JOURNAL.md`
   Status, ask before writing the file. A library the source names and
   the user has not agreed to add stays in Open gaps. A domain
   claim this dataset does not establish stays in Open gaps.
8. Restate the idea in one short paragraph, then one
   single-choice **AskUserQuestion**: **Yes** / **No**. Do not
   also ask for a typed yes. Put that question in the message
   before any idea file. "Maybe" is not Yes. No or Stop writes
   nothing. A Yes from the tool, or an explicit yes the user
   already gave, authorizes the write only after that question
   is in the message.
9. On Yes, write `journal/ideas/<slug>.md` and upsert its Ideas
   row. Do not create a design note. Do not edit History,
   Backlog, or Status. Write `journal/ideas/<slug>.md`:

```
# <slug>
- Experiment: <last History stem, or n/a>
- Source: user
- Triage: open
- Question:
- Why now:
- What changes:
- Open gaps:
```

   Why now carries the quote, URL, or path. No acceptance
   criteria. Then upsert one `## Ideas` row: Question as plain
   text, Status `open`, Experiment `<last History stem, or n/a>`,
   Source `user`. If that table is missing, insert it between
   History and Backlog. Do not rewrite the other sections.
   Return the path to the caller (`manage-ml-backlog` or
   `triage-ml-task`).

## Stop conditions

- Do not write History, Backlog, Status, or a design note.
  The Ideas table is the only `JOURNAL.md` edit.
- Do not append a `B<N>` row. The backlog triages the file.
- Do not invent source content from a title.
- Do not `WebSearch` for a topic with no artifact.
- The entry question and the Yes / No confirmation are
  required gates.
- If the user already asked to add a named library, put it in
  What changes and load `add-python-package` when that skill
  is installed. Do not `pixi add` from here.
