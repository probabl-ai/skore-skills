# Known at predict and generalize-to

**Known at predict** lists columns that are present on a new row.
A group mean is only a baseline for one of those columns. If
there is no such column, write `n/a`.

**Generalize to** is a different row. It is the column whose ids
will be new when the model is used. Those ids must stay entirely
out of the fit that is scored, so that column's mean is not a
baseline. Ask it only when it is in `missing`, which is after
deployment is `groups`. On an i.i.d. or time deployment it is
`n/a` and is not a question. Do not ask it from this note.
