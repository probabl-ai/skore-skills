# G-SKORE-MODE in detail

Owned by **`evaluate-ml-pipeline`**. Ask and persist
`policy.skore_mode` on first `skore.evaluate` / `Project` use, not
during workspace setup.

Full deep dive on the Skore Project mode gate. This reference is
for filling the Project init form or debugging a hub-vs-local
mismatch.

Cross-referenced from `evaluate-ml-pipeline` (gate owner),
`add-python-package` (skore extra), `audit-ml-pipeline` § Read-only
contract.

## Project init forms — concrete side-by-side

The three forms are not "swap one word" variants; the argument shape
changes per mode.

### Local mode (default)

```python
import skore

from <pkg> import PROJECT_ROOT

project = skore.Project(
    name="<project-name>",
    mode="local",
    workspace=str(PROJECT_ROOT / "reports"),
)
```

### Hub mode

```python
import skore

# Auth is an API key, not skore.login. Mint it once with
# `skore hub api-key generate --host <host> --workspace <workspace>`.
project = skore.Project(
    name="<project-name>",
    mode="hub",
    workspace="<hub-workspace>",
    host="https://skore.probabl.ai",
)
```

### MLflow mode

```python
import skore

# No login() — auth (if any) is the MLflow server's concern.
project = skore.Project(
    name="<experiment-name>",
    mode="mlflow",
    tracking_uri="<mlflow-tracking-uri>",
)
```

`name=` is the **MLflow experiment name**; reports persist as MLflow
model artifacts in runs created under that experiment. `tracking_uri=`
is an **mlflow-only** kwarg — the URI of the MLflow tracking server
(e.g. `http://127.0.0.1:5000`, `https://mlflow.acme.internal`, or a
`file:./mlruns` / `sqlite:///mlflow.db` local backend). The
`project.put("<key>", report)` `key` becomes the **run name**.
Source: https://docs.skore.probabl.ai/stable/reference/api/skore.Project.html

### Diff at a glance

| Concern | Local | Hub | MLflow |
|---|---|---|---|
| `skore.login` | not used | **gone** — do not call it | not used |
| API key | not used | `SKORE_HUB_API_KEY`, else the key from `skore hub api-key generate --host <host> --workspace <workspace>` | not used |
| `name=` argument | `name="<project-name>"` (bare) | `name="<project-name>"` (bare — the Hub project name) | `name="<experiment-name>"` (MLflow experiment name) |
| `mode=` argument | `mode="local"` | `mode="hub"` | `mode="mlflow"` |
| `workspace=` argument | **required**: `workspace=str(PROJECT_ROOT / "reports")` (on-disk dir) | **required**: `workspace="<hub-workspace>"` (the Hub workspace name) | **MUST be absent** — `tracking_uri=` is used instead |
| `host=` argument | not used | **required** unless `SKORE_HUB_URI` is already that host: `host="https://skore.probabl.ai"` | not used |
| `tracking_uri=` argument | not used | not used | **required**: the MLflow tracking server URI |
| Install command | `env add-skore --mode local --execute` | `env add-skore --mode hub --execute` | `env add-skore --mode mlflow --execute` (`mlflow>=3` required) |
| Pre-condition | `reports/` exists (create at this gate; no README) | Skore Hub account, workspace access, and an API key for that host and workspace | reachable MLflow tracking server at `<uri>` |

## The gate — AskUserQuestion shape

Fires at first evaluation, before `skore.evaluate`. Never silent,
and **always presents all three options** (`local` / `hub` /
`mlflow`) as selectable choices — even if the user has used skore
in `local` mode in prior projects, **and even if the current folder
already contains skore-hub configuration** (`SKORE_HUB_URI`,
`SKORE_HUB_API_KEY`, or a row from `skore hub api-key list`).
Detected hub config is *detection, not a decision*: it MAY set
the highlighted default, but it MUST NOT remove `mlflow` or
`local` from the list.

### Structured pick with default and follow-up

1. **Mode.** Options:
   - `local` — artifacts on disk, no account needed, recommended
     for solo work.
   - `hub` — artifacts on https://skore.probabl.ai, requires
     account + workspace access, recommended for team
     collaboration.
   - `mlflow` — artifacts pushed to an MLflow tracking server (the
     skore `skore[mlflow]` backend integration), recommended when
     the team already runs MLflow or standardizes on it for
     experiment storage.

   Default proposal: `local`.

2. **Hub workspace name and host** (only when mode is `hub`).
   The workspace is a free-form org/team identifier. The agent
   cannot infer it; the user must know it. If the user picks
   `hub` without a workspace name, surface that they need to
   create or join one at https://skore.probabl.ai first.

   **Validation**: the workspace name MUST NOT contain `/`. The
   `workspace=` value is a single Hub workspace identifier passed as
   its own kwarg (e.g. `workspace="acme-corp"`), not a path and not a
   `<workspace>/<project>` join — a `/` is not a valid Hub workspace
   name. If the user types `acme/datasci`, ask whether `acme` was the
   intended workspace and `datasci` is part of the project name. Do
   not silently accept slashes — that produces an invalid workspace
   identifier at runtime.

   The host is the Hub address passed as `host=` (for example
   `https://skore.probabl.ai`). Propose that URL. Confirm a bare
   host as `https://<host>`. If `SKORE_HUB_URI` is already set,
   use it and do not re-ask. There is no built-in default: omitting
   `host=` with `SKORE_HUB_URI` unset raises `ValueError`.

   **API key**, before any Hub `Project(...)`. Do not call
   `skore.login`. `SKORE_HUB_API_KEY`, when set, wins and is
   enough; it is bound to one workspace. Otherwise run
   `skore hub api-key list`. A row for this host and workspace
   is enough. If that row is missing, run
   `skore hub api-key generate --host <host> --workspace <workspace>`
   and wait for the browser device login. Do not pass `--force`
   unless the user asked to replace a key. Do not read
   `~/.skore.hub/credentials.json` or `.skore` for the secret.

3. **MLflow tracking URI** (only when mode is `mlflow`). Free-form
   string — the `tracking_uri=` passed to `skore.Project(...)`.
   The agent **cannot** infer the server address; the user must
   supply it. Accept the forms MLflow itself accepts:
   - an HTTP(S) tracking server — `http://127.0.0.1:5000`,
     `https://mlflow.acme.internal`;
   - a database backend — `sqlite:///mlflow.db`,
     `postgresql://…`;
   - a local file store — `file:./mlruns` or an absolute `file:`
     path.

   If the user picks `mlflow` without knowing the URI, surface that
   they need a running tracking server (or a local backend path)
   before reports can be pushed — do NOT default the URI silently.
   A bare host:port without a scheme (e.g. `localhost:5000`) should
   be confirmed as `http://localhost:5000` rather than passed
   verbatim.

### Free-text resolution

- Explicit naming of `local` / `hub` / `mlflow` resolves
  immediately.
- "use the cloud one" / "store remotely" → `hub`.
- "store locally" / "no account" → `local`.
- "push to mlflow" / "our mlflow server" / "track in mlflow" →
  `mlflow` (then ask for the tracking URI).
- Urgency phrasing ("quick" / "you pick") does NOT resolve — falls
  through to the structured ask.

## What the gate determines

The recorded `skore mode:` decision drives three downstream
artifacts:

| Downstream artifact | local-mode shape | hub-mode shape | mlflow-mode shape |
|---|---|---|---|
| `<SKORE_PROJECT_INIT>` in `experiments/NN_*.py` and `audit/NN_*.py` | `skore.Project(name="<project-name>", mode="local", workspace=str(PROJECT_ROOT / "reports"))` | `skore.Project(name="<project-name>", mode="hub", workspace="<hub-workspace>", host="<hub-host>")` | `skore.Project(name="<experiment-name>", mode="mlflow", tracking_uri="<mlflow-tracking-uri>")` |
| Skore install (via `add-python-package`) | `env add-skore --mode local --execute` | `env add-skore --mode hub --execute` | `env add-skore --mode mlflow --execute` (the `mlflow>=3` pin is encoded) |
| `policy.skore_mode` (`.skore`) | `local` | `hub` | `mlflow` |

`name=` is a bare project name in **all three** modes — local uses it
directly, hub uses it as the Hub project name, mlflow uses it as the
MLflow experiment name. What changes is the **companion kwarg**:
`workspace=` is required by local (an on-disk directory `Path`) and by
hub (the Hub workspace identifier `str`). Hub also takes `host=`
unless `SKORE_HUB_URI` is already that host. MLflow takes
`tracking_uri=` instead and rejects `workspace=`. These are not "swap
one word" differences; the substitution marker exists precisely
because the companion kwargs change.

## Persistence

Record the mode with `python -m skore_skills policy set
skore_mode <local | hub | mlflow>`. If **local**, create
`reports/` if missing (`mkdir`, exist_ok) and do not write a
README. If **hub** or **mlflow**, do not create `reports/` —
that directory is the on-disk Project store only. Hub workspace
names, Hub hosts, and MLflow tracking URIs live in the experiment's
`<SKORE_PROJECT_INIT>` block, not in JOURNAL. On later sessions,
read `status.policy.skore_mode` and skip re-asking.

## Post-put report locator

`Project.put(key, report)` returns `None` in every mode. After it
succeeds, preserve stdout and use the newest matching-key row from
`project.summarize().frame()` as the source of the report id. Store
one normalized Markdown locator in the design note and JOURNAL:

| Mode | Locator |
|---|---|
| local | `local workspace: [reports/](../reports/) · id: <id>`; the user-facing message also gives the resolved absolute `reports/` path |
| hub | Exact `Consult your report at …` URL printed by `put`, plus the id. If older Skore prints no report URL, link the Hub project landing page and label it as a project link |
| mlflow | Exact emitted `View run …` URL when available; otherwise the standard run URL only for HTTP(S) tracking. Non-HTTP or nonstandard tracking records URI + experiment id + run id as text |

Do not synthesize Hub report URLs: the frontend URL is backend
owned. Do not link local serialized report files: their layout is
private. Do not turn `file:`, `sqlite:`, or `databricks` tracking
URIs into guessed browser URLs. A missing locator is
`n/a — backend did not expose a locator`, never an invented URL.

## Switching mid-project

Do not silently change a recorded mode. If the user asks to
switch destination or migrate existing reports, load
**`sync-ml-reports`** when that skill is installed (it runs
`skore sync`, then — on switch intent — `policy set`, Project
init rewrite, extras, and a JOURNAL History divider). If that
skill is missing, one-line skip; do not invent `skore sync` or
`Project.sync` from this reference.

## Anatomy of the substitution

The `<SKORE_PROJECT_INIT>` marker is a **comment line** inside the
template that signals the start of the Project init block. The
substitution replaces the comment AND the block that follows it
(up to the next blank line) with the mode-appropriate code. The
marker comment itself **is removed** in the substituted file —
it's not a permanent anchor, it's a scaffold-time signal.

### Authoritative experiment skeleton before substitution

Use the experiment call shapes in
`evaluate-ml-pipeline/references/skrub_interop.md`; there is no
packaged `templates/experiment.py` file. The relevant Project-init
block starts as:

```python
# %%
# <SKORE_PROJECT_INIT>
project = skore.Project(
    name="<project-name>",
    mode="local",
    workspace=str(PROJECT_ROOT / "reports"),
)
```

### After substitution — local mode

Replacing `<project-name>`, keeping the rest:

```python
# %%
project = skore.Project(
    name="load-forecast",
    mode="local",
    workspace=str(PROJECT_ROOT / "reports"),
)
```

### After substitution — hub mode

The whole block (including the `# %%` cell marker) is rewritten to
the Hub `Project` shape. There is no `login` call:

```python
# %%
project = skore.Project(
    name="load-forecast",
    mode="hub",
    workspace="acme-corp",
    host="https://skore.probabl.ai",
)
```

Note that in the hub form:

- `workspace=` is **kept**, but carries the **Hub workspace name**
  (`"acme-corp"`), not an on-disk directory.
- `host=` is the Hub address. Write it in the file so a later run
  does not depend on `SKORE_HUB_URI` in the shell.
- `name=` stays the bare project name (no slash join).
- Do not call `skore.login`. The key comes from
  `skore hub api-key generate` or `SKORE_HUB_API_KEY`.

### After substitution — mlflow mode

The block is rewritten to drop `workspace=` and add the
`tracking_uri=` recorded at G-SKORE-MODE. No `login(...)`:

```python
# %%
project = skore.Project(
    name="load-forecast",
    mode="mlflow",
    tracking_uri="http://127.0.0.1:5000",
)
```

Note that in the mlflow form:

- `workspace=` is **gone** — `tracking_uri=` replaces it.
- `name=` is the **MLflow experiment name** (bare, no slash join).
- no `login(...)` — authentication, if any, is the MLflow server's
  concern, handled out-of-band (env vars / server config), not by
  skore.
- `project.put("<stem>", report)` creates a run named `<stem>`
  under the experiment.

### Audit-file copy rule

For `audit/<stem>.py`: the same substitution rule applies, but with
one extra constraint — the substituted block must match what
`experiments/<stem>.py` actually contains, byte-for-byte (modulo
formatting). Read the experiment file first, copy its Project init
block, paste into the audit's substitution marker.

**Do not re-derive from the `skore mode:` decision alone** — a typo
or formatting drift would silently open a different Project. See
the `audit-ml-pipeline` Forbidden shortcuts row "Substituting
`<SKORE_PROJECT_INIT>` in audit independently of the experiment".

## Out of scope

- **Running / provisioning the MLflow server.** When the user picks
  `mlflow`, the gate captures the `tracking_uri=` but does NOT
  stand up the tracking server, create the backing database, or
  configure object storage. A reachable server (or a local
  `file:`/`sqlite:` backend) at the supplied URI is the user's
  responsibility — surface that pre-condition rather than spinning
  one up.

- **Provisioning the MLflow backing store for `delete`.**
  `skore.Project.delete(name=..., mode="mlflow", tracking_uri=...)`
  is supported (it removes the matching MLflow experiment), but it
  raises `LookupError` if no experiment exists at the given
  `tracking_uri`. This skill does not stand up or seed that server;
  a reachable tracking store is the user's responsibility.

- **Skore Hub account creation.** The gate assumes the user has an
  account when they pick `hub`. Sign-up is a probabl.ai concern
  (https://probabl.ai/skore); this skill won't drive the user
  through it.
