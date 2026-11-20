# Audit ML Pipeline — failure modes and recovery

Load this reference when an audit-ml-pipeline action fails and you
need to know how to recover. The SKILL.md body links here from its
"Failure modes" section.

## `project.get(key)` raises `KeyError` / `TypeError`

Lookup shape is wrong: `get` is by id, not by key.

- **Hub mode**: the id comes from the URL printed by `project.put()`:
  `https://…/<workspace>/<project>/<type-plural>/<N>` → id is
  `skore:report:<type-singular>:<N>` (URL segment is plural; id is
  singular — drop the trailing `s`, e.g. `cross-validations` →
  `cross-validation`, `estimators` → `estimator`). If the audit
  file's `REPORT_ID` is wrong, update it from the correct URL.
- **Local mode**: `summarize()` is a Display. Bind
  `frame = summary.frame()`, then
  `frame.loc[frame["key"] == "<NN>_<short_name>", "id"].iloc[0]`
  and set it as `REPORT_ID`. The core template leaves `summary`
  as the last expression so the digest shows the Display;
  `.frame()` is for lookup, not for replacing that last line.

Never substitute by re-running `evaluate` + `put`. See `python -m skore_skills api get`
§ "Lookup failure ≠ artifact missing".

## `cells run` exits with `ModuleNotFoundError: No module named 'IPython'`

Agent feature not installed in the env the runner is invoked from.
**Delegate to `add-python-package` § "Agent feature" via
`agent tools (ruff / ipython / ipykernel)`.** Do not type install commands from this skill.
`python -m skore_skills env init` prints the full plan;
`env init --execute` installs and verifies it.

## Cell renders as `<Display object at 0x…>` in the digest

Current skore Displays render themselves as text, so the bare
expression is normally enough. Seeing the object-at-address means
this skore predates that, and the runner has nothing to capture.
Chain `.frame()` on the affected cell only:

```python
report.metrics.summarize().frame(verbose_name=True, flat_index=False)
report.checks.summarize().frame()
```

## Digest contains `**error:** AttributeError: 'X' object has no attribute 'Y'` for a `report.*` accessor

Symbol drift between skore versions OR symbol-from-memory in the
audit file. Consult `python -m skore_skills api get` against the installed skore version,
update the cell, re-run the runner.

## Digest contains `**error:**` for the `project.get(REPORT_ID)` cell

`project.get(REPORT_ID)` raised — the id doesn't match any report in
this Project. Most likely cause: the audit's `<SKORE_PROJECT_INIT>`
block points to a different Project than the experiment wrote to (wrong
hub workspace name, wrong mode, wrong project name). Verify it matches
`experiments/<stem>.py` exactly. For hub mode, also confirm `REPORT_ID`
was copied from the correct `put()` URL output.

## Report differs between runs even when source code didn't change

Most often: the experiment was re-run with a different data slice,
or a non-deterministic step (RNG seed) shifted. Not a bug in this
skill; surface to the user before assuming the audit changed.

## Hub mode: `RuntimeError: No API key found for this workspace`

No key for this host and workspace, and `SKORE_HUB_API_KEY` is
unset. Surface the error. Run
`skore hub api-key generate --host <host> --workspace <workspace>`
with the host and workspace already in `experiments/<stem>.py`.
Do not insert `skore.login`. Do not read
`~/.skore.hub/credentials.json` or `.skore`. Re-run the audit
runner after the key is stored.

## Hub mode: `ValueError` — host missing

`Project(...)` was opened without `host=` and `SKORE_HUB_URI` is
unset. Copy `host=` and `workspace=` from `experiments/<stem>.py`.
Hub requires both. Do not drop `workspace=` to "fix" the call.

## Hub mode: report appears missing in `summarize()` but the experiment script reported a successful `put()`

Two possibilities:

1. **Different hub workspace or host.** The audit is opening a
   different hub workspace or host than the experiment wrote to.
   Verify `workspace=` and `host=` match `experiments/<stem>.py`.
2. **No read access.** The user's credentials don't have read access
   to the workspace they wrote to (rare). Surface the access issue
   to the user; do not silently fall back to local mode.
