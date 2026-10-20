---
name: search-ml-literature
description: >
  Search scientific and technical sources and create one experiment for the
  direction the user confirms. Comes after review, beside the backlog. Do not
  call research-ml-practice. Do not edit JOURNAL.md, idea files, or a design
  note. Do not pick a winner.
metadata:
  modelTier: medium
---

# Search ML Literature

Store a confirmed direction with
`python -m skore_skills experiment create --stem <stem> --question "<question>"`.
Do not edit `JOURNAL.md`, an idea file, or a design note. If a later step
says to write those files, skip that step and use `experiment create`.

Comes after review, beside the backlog. Source is a query, not an
artifact the user already named. Show a few directions, then write
one `journal/ideas/<slug>.md` and one Ideas row for the direction
they confirm. `manage-ml-backlog` triages that file later.

## Human-facing prose

Details: `setup-workspace` `references/human_facing_prose.md`.
Directions and the pick question are scientific options for this
project — not skill ids or the wrapper CLI.

## Procedure

1. Run `python -m skore_skills status`. Read `journal/JOURNAL.md`
   Status, the last History headline, and the EDA summary when
   `data_analysis/data_analysis.md` exists. If the query is too
   vague to search, ask once.
2. Rewrite the query as a problem class before any search. Drop
   dataset names, loader names (`sklearn.datasets`, `fetch_*`),
   and Kaggle slugs. JOURNAL and EDA are context for that
   rewrite, not search strings.
3. Search scientific and technical sources. Fetch the primary
   pages. When sources disagree, say so. Do not fill a gap from
   memory after a search has run. If search cannot run, say so
   and stop. Do not invent papers, URLs, or claims.
4. Write `scratch/research/direction-<slug>.md` when that write
   can run. Do not paste it into chat.
5. Show two to four directions. Each one: a one-line idea, why
   it might transfer here, what it would change, and the URL
   plus the claim. Do not rank a winner.
6. **AskUserQuestion**: pick one, narrow the query, or stop.
   Narrow restarts at step 2. Stop writes no idea file.
7. If this turn is not already an explicit yes, restate the
   picked direction in one short paragraph, then one
   single-choice **AskUserQuestion**: **Yes** / **No**. Do not
   also ask for a typed yes. Until Yes, that paragraph and the
   question are the whole message. "Maybe" is not Yes. No or
   Stop writes nothing.
8. On Yes — the tool answer, or an explicit yes already given
   on this or a later turn — write `journal/ideas/<slug>.md`
   and upsert its Ideas row. Do not create a design note.
   Do not edit History, Backlog, or Status. Write
   `journal/ideas/<slug>.md`:

```
# <slug>
- Experiment: <last History stem, or n/a>
- Source: literature: <url>
- Triage: open
- Question:
- Why now:
- What changes:
- Open gaps:
```

   Open gaps hold transfer risks, disagreements, and domain
   claims this dataset does not establish. A library named only
   by a source stays in Open gaps until the user asks to add it.
   Then upsert one `## Ideas` row: Question as plain text, Status
   `open`, Experiment `<last History stem, or n/a>`, Source
   `literature: <url>`. If that table is missing, insert it
   between History and Backlog. Do not rewrite the other
   sections. Return the path to the caller.

## Stop conditions

- Do not load `research-ml-practice`.
- Do not write History, Backlog, Status, or a design note.
  The Ideas table is the only `JOURNAL.md` edit.
- Do not append a `B<N>` row.
- Do not search a dataset proper name, a loader, or a Kaggle slug.
- Do not add a package or run `env add` / `pixi add`.
- Do not treat one blog as ground truth.
