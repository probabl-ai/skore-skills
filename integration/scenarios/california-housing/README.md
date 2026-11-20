# California housing

Manual spine: set up a project, explore the housing table, lock a
small California housing regression, build one baseline, promote one
follow-up into the backlog, then start that item and stop before its
evaluation.

Install the `ml-experimentation` pack in the harness first. The seed is
only the project. Open the materialized folder as the harness workspace.
Paste one reply, wait until the agent stops, then check that turn before
pasting the next reply.

```bash
python tools/integration_scenario.py materialize california-housing --dest ../housing
python tools/integration_scenario.py prompt california-housing --turn setup-open
python tools/integration_scenario.py check california-housing --workspace ../housing --turn setup-open
```

`prompt` prints the reply on stdout. When a turn is a checkpoint, copy
the workspace before replaying a fork from it.

If a question arrives alone, paste only the matching line and check that
turn once the agent has stopped again. `baseline-approve` and
`iterate-approve` are the design-note approval. Check after the smoke
test. After `eda-run`, if the continuation board is still on screen,
paste `Close. Do not add another analysis.` The `eda-run` check still
applies. After `baseline-evaluate`, the result is recorded and the
continuation board is on screen; `baseline-move-on` leaves it for triage.

## Spine

| Turn | Checkpoint | What this reply does |
| --- | --- | --- |
| `setup-open` | | Ask to set up the housing project. |
| `setup-pieces` | | Keep environment, workspace, editable install, and Git. |
| `setup-manager` | | Use pixi. |
| `setup-managed` | | Manage the Python environment. |
| `setup-package` | | Import name `housing`. |
| `setup-autocommit` | yes | Automatic commits off. Scaffold lands here. |
| `eda-run` | yes | Run and close the data analysis. No design note yet. |
| `frame-open` | | Frame from `DATA.md` and the written analysis. |
| `frame-fill` | yes | Answer the frame questions. The table locks and the baseline design note stays `planned`. |
| `baseline-approve` | | Approve, build, and smoke-test. No report yet. |
| `baseline-evaluate` | | Evaluate, keep the report local, record the outcome, and materialize the audit. The continuation board is on screen. |
| `baseline-move-on` | yes | Move on. Triage opens with the idea files already written. |
| `backlog-promote` | yes | Promote the first idea to `B1`. |
| `iterate-choose` | | Take that backlog item. `02_*` stays `planned`. No experiment file. |
| `iterate-approve` | | Approve and smoke-test `02_*`. No second report. |
| `iterate-stop` | | Stop before evaluating `02_*`. |

The filled modeling cells are the closed-menu values: prediction goal
`point_predictions`, deployment `iid`, metric role `point_error`, metric
`RMSE`, baseline `dummy`, folds `2`. Scaffold placeholders such as
`<missing | draft | locked>` do not satisfy `| Status | locked |`.

## Forks

Copy the workspace after the turn in **After**, open that copy, and paste
the fork reply instead of continuing the spine.

| Fork | After | Reply | Check |
| --- | --- | --- | --- |
| `decline-workspace` | `setup-open` | Do not select the workspace layout. Select the Python environment, the editable install, and Git. | No `src/` or `journal/`. |
| `decline-git` | `setup-open` | Do not select Git. Select the Python environment, the workspace layout, and the editable install. | `.skore` records Git declined. No scaffold yet. |
| `you-pick-name` | `setup-managed` | You pick the import name. | No `src/housing/`. |
| `skip-eda` | `setup-autocommit` | Skip the data analysis. | Data understanding is `skipped`. No analysis file and no design note. |
| `lock-same-turn` | `frame-open` | The `frame-fill` values, then `Lock these decisions.` | Status is `locked`. The baseline design note stays `planned`. |
| `discuss-baseline` | `frame-fill` | Discuss the next step. | Decisions stay locked. The design note stays `planned`. No experiment script. |
| `stop-design` | `frame-fill` | Stop. | Design note stays `planned`. No experiment script. |
| `modify-design` | `frame-fill` | Modify the method, then ask me again. | State stays `planned`. |
| `stop-after-smoke` | `baseline-approve` | Stop. | Smoke files exist. No `report.html`. |
| `discard-ideas` | `baseline-close-audit` | Discard every open idea. | An idea file says `Triage: discarded`. No `02_*`. |
| `discuss-iterate` | `backlog-promote` | Discuss what to try instead. | `B1` remains. No `02_*`. |

```bash
python tools/integration_scenario.py prompt california-housing --fork decline-workspace
python tools/integration_scenario.py check california-housing --workspace ../housing-fork --fork decline-workspace
```

## Unattended spine

`SCENARIO.md` is the authorized spine. `run` copies it into the workspace,
starts one harness, and checks `iterate-stop` after a zero exit. Forks
stay manual.

```bash
python tools/integration_scenario.py run california-housing --workspace ../housing
python tools/integration_scenario.py run california-housing \
  --workspace ../housing --interactive
```

`run` launches Pi. Add `--interactive` to show the TUI and interrupt it
from the terminal. The default runs headless, streams the output, and
writes logs under `.transcripts/integration/<run-id>/`. Pi must already
be authenticated. This command does not install it.

Pi is started with `--approve`, which trusts project-local files; Pi
does not ask before each tool call. It defaults to `--provider openrouter`
and `--model ~deepseek/deepseek-flash-latest`. Pass `--model` to choose
another model, or repeat `--harness-arg` for any other flag. Install the
required extension once with `pi install npm:@probabl/pi-skore`.

Before Pi starts, the runner stages every workflow sidecar and passes its
checkout directory with `--skill`. It also supplies the checkout
CLI on `PYTHONPATH`. The agent must enter every stage through
`skill("<id>")`, never by reading `SKILL.md`, and adds the checkout as an
editable pixi dependency after pixi initialization. No reload is needed.
The journey may run `pixi`. A non-empty workspace is refused unless
`--reuse-workspace` is set.
