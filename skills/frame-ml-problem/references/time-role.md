# Time role

On a time deployment, record what the time column is for.

- `sort_key` — the column only orders rows.
- `covariate` — the model may use the column as a feature.

That choice is not a splitter setting. Ask this only when it
is in `missing`. On an i.i.d. or group deployment the row is
`n/a`. Do not say the column is a feature in that case.
