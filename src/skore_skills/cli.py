"""Command-line interface for ``skore_skills``."""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import click

from skore_skills import __version__
from skore_skills.api import get_symbol, package_version
from skore_skills.check import render_workspace_check
from skore_skills.design_consent import render_design_consent
from skore_skills.evaluate_consent import render_evaluate_consent
from skore_skills.frame import render_frame_show
from skore_skills.model_choices import render_model_choices
from skore_skills.policy import LOOP_STAGES
from skore_skills.review_consent import render_review_consent
from skore_skills.status import render_status


def _reexec_library_command(argv: list[str]) -> None:
    """Enter the composed project env for in-process library commands."""
    from skore_skills.env import reexec_in_dev

    code = reexec_in_dev(Path.cwd(), argv=argv)
    if code is not None:
        raise SystemExit(code)


def _emit_git(load: Callable[[], tuple[dict[str, Any], int]]) -> None:
    """Print a git command payload and exit when its code is non-zero."""
    from skore_skills.git import render_git_json

    try:
        payload, code = load()
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(render_git_json(payload), nl=False)
    if code:
        raise SystemExit(code)


@click.group()
@click.version_option(version=__version__, prog_name="skore-skills")
def cli() -> None:
    """Deterministic helpers for Probabl ML skills.

    Invoke as ``python -m skore_skills``.
    """


@cli.group("cells")
def cells_group() -> None:
    """Execute jupytext percent-format ``# %%`` files."""


@cells_group.command("run")
@click.argument("src", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument(
    "dst",
    type=click.Path(dir_okay=False, path_type=Path),
    required=False,
)
def cells_run(src: Path, dst: Path | None) -> None:
    """Stream a markdown digest of each cell to stdout.

    When ``DST`` is given, also write the digest to that path.
    """
    from skore_skills.cells import run

    forwarded = ["cells", "run", os.fspath(src)]
    if dst is not None:
        forwarded.append(os.fspath(dst))
    _reexec_library_command(forwarded)
    run(src, dst)


@cli.group("notebook")
def notebook_group() -> None:
    """Write notebooks from percent-format ``# %%`` files."""


@notebook_group.command("convert")
@click.argument("src", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "--out",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Destination .ipynb (default: same stem next to SRC).",
)
@click.option(
    "--html",
    is_flag=True,
    help="Also write <stem>.nb.html next to SRC.",
)
@click.option(
    "--digest",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Also write the executed cells as a Markdown digest.",
)
def notebook_convert(
    src: Path, out: Path | None, html: bool, digest: Path | None
) -> None:
    """Execute SRC with nbclient and write an .ipynb with outputs."""
    from skore_skills.notebook import convert

    forwarded = ["notebook", "convert", os.fspath(src)]
    if out is not None:
        forwarded.extend(["--out", os.fspath(out)])
    if html:
        forwarded.append("--html")
    if digest is not None:
        forwarded.extend(["--digest", os.fspath(digest)])
    _reexec_library_command(forwarded)
    try:
        dest = convert(src, out, html=html, digest=digest)
    except (ImportError, FileNotFoundError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(dest))


@notebook_group.command("fill")
@click.argument("src", type=click.Path(dir_okay=False, path_type=Path))
@click.option(
    "--out",
    type=click.Path(dir_okay=False, path_type=Path),
    help="Destination .ipynb (default: same stem next to SRC).",
)
@click.option(
    "--html",
    is_flag=True,
    help="Also write <stem>.nb.html next to SRC.",
)
def notebook_fill(src: Path, out: Path | None, html: bool) -> None:
    """Write an .ipynb with empty outputs. Does not execute SRC."""
    from skore_skills.notebook import fill

    forwarded = ["notebook", "fill", os.fspath(src)]
    if out is not None:
        forwarded.extend(["--out", os.fspath(out)])
    if html:
        forwarded.append("--html")
    _reexec_library_command(forwarded)
    try:
        dest = fill(src, out, html=html)
    except (ImportError, FileNotFoundError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(dest))


@cli.group("site")
def site_group() -> None:
    """Initialize and build an offline MkDocs documentation site."""


@site_group.command("init")
@click.option(
    "--force",
    is_flag=True,
    help="Accepted for compatibility; init only updates .gitignore.",
)
def site_init(force: bool) -> None:
    """Ignore _build/ and html/. Does not write a user mkdocs.yml."""
    from skore_skills.site import init_site

    forwarded = ["site", "init"]
    if force:
        forwarded.append("--force")
    _reexec_library_command(forwarded)
    try:
        dest = init_site(Path.cwd(), force=force)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(str(dest))


@site_group.command("build")
@click.option(
    "--if-stale",
    is_flag=True,
    help="Skip MkDocs when all site inputs already match the built output.",
)
def site_build(if_stale: bool) -> None:
    """Package Markdown and existing companions into ``html/``."""
    from skore_skills.site import build_site

    forwarded = ["site", "build"]
    if if_stale:
        forwarded.append("--if-stale")
    _reexec_library_command(forwarded)
    try:
        click.echo(build_site(Path.cwd(), if_stale=if_stale))
    except (ValueError, FileNotFoundError, RuntimeError) as exc:
        raise click.ClickException(str(exc)) from exc


@cli.group("api")
def api_group() -> None:
    """Look up public symbols in the running interpreter."""


@api_group.command("get")
@click.argument("symbols", nargs=-1, required=True, metavar="SYMBOL...")
def api_get(symbols: tuple[str, ...]) -> None:
    """Print signature cards and cache them under ``scratch/api/``."""
    _reexec_library_command(["api", "get", *symbols])
    try:
        for symbol in symbols:
            click.echo(get_symbol(symbol), nl=False)
    except ImportError as exc:
        raise click.ClickException(str(exc)) from exc
    except LookupError as exc:
        raise click.ClickException(str(exc)) from exc


@api_group.command("version")
@click.argument("package")
def api_version(package: str) -> None:
    """Print the installed version of ``PACKAGE``."""
    _reexec_library_command(["api", "version", package])
    try:
        click.echo(package_version(package))
    except ImportError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("status")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "text"], case_sensitive=False),
    default="json",
    show_default=True,
)
def status_cmd(fmt: str) -> None:
    """Print a read-only JSON snapshot of the current workspace."""
    click.echo(render_status(Path.cwd(), fmt.lower()), nl=False)


@cli.group("model")
def model_group() -> None:
    """Inspect deterministic model-workflow choices."""


@model_group.command("choices")
def model_choices_cmd() -> None:
    """Print the available model-entry choices as JSON."""
    click.echo(render_model_choices(Path.cwd()), nl=False)


@cli.group("evaluate")
def evaluate_group() -> None:
    """Inspect deterministic evaluate-workflow gates."""


@evaluate_group.command("consent")
@click.option("--stem", required=True, help="Experiment stem, e.g. 05_new_model.")
def evaluate_consent_cmd(stem: str) -> None:
    """Print whether first-eval HITL is required as JSON."""
    try:
        click.echo(render_evaluate_consent(Path.cwd(), stem), nl=False)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc


@cli.group("review")
def review_group() -> None:
    """Inspect deterministic review-workflow gates."""


@review_group.command("choices")
def review_choices_cmd() -> None:
    """Print the stored-choice board as JSON. Does not write."""
    from skore_skills.review_choices import render_review_choices

    try:
        click.echo(render_review_choices(Path.cwd()), nl=False)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc


@review_group.command("consent")
@click.option("--stem", required=True, help="Experiment stem, e.g. 01_baseline.")
def review_consent_cmd(stem: str) -> None:
    """Print whether to audit this stem, as JSON."""
    try:
        click.echo(render_review_consent(Path.cwd(), stem), nl=False)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc


@cli.group("frame")
def frame_group() -> None:
    """Inspect the modeling-decisions gate."""


@frame_group.command("show")
@click.option(
    "--revise",
    is_flag=True,
    help="Ask to edit a locked block instead of proceeding.",
)
def frame_show_cmd(revise: bool) -> None:
    """Print the next modeling-decisions gate as JSON."""
    click.echo(render_frame_show(Path.cwd(), revise=revise), nl=False)


@frame_group.command("clear")
@click.option("--cell", required=True, help="Framing cell key to blank, e.g. metric.")
def frame_clear_cmd(cell: str) -> None:
    """Blank one framing cell and its dependents, then print JSON."""
    from skore_skills.frame import render_frame_clear

    try:
        click.echo(render_frame_clear(Path.cwd(), cell), nl=False)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc


@cli.group("design")
def design_group() -> None:
    """Inspect deterministic design-note gates."""


@design_group.command("consent")
@click.option("--stem", required=True, help="Experiment stem, e.g. 05_new_model.")
def design_consent_cmd(stem: str) -> None:
    """Print whether design approval is required as JSON."""
    try:
        click.echo(render_design_consent(Path.cwd(), stem), nl=False)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc


@design_group.command("approve")
@click.option("--stem", required=True, help="Experiment stem, e.g. 05_new_model.")
def design_approve_cmd(stem: str) -> None:
    """Stamp State approved and Approved by user on, then print JSON."""
    from skore_skills.design_consent import render_design_approve

    try:
        click.echo(render_design_approve(Path.cwd(), stem), nl=False)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc


@cli.group("eda")
def eda_group() -> None:
    """Stamp the data-understanding status date."""


@eda_group.command("stamp")
@click.option(
    "--status",
    required=True,
    type=click.Choice(["done", "skipped"]),
    help="Data-understanding status to record.",
)
def eda_stamp_cmd(status: str) -> None:
    """Write the data-understanding Status date, then print JSON."""
    from skore_skills.eda import render_eda_stamp

    try:
        click.echo(render_eda_stamp(Path.cwd(), status), nl=False)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc


@cli.group("smoke")
def smoke_group() -> None:
    """Run the per-stem smoke pytest gate."""


@smoke_group.command("run")
@click.option("--stem", required=True, help="Experiment stem, e.g. 01_baseline.")
def smoke_run_cmd(stem: str) -> None:
    """Stream pytest for ``tests/smoke/test_<stem>.py``, then print JSON."""
    from skore_skills.smoke import render_smoke, run_smoke

    forwarded = ["smoke", "run", "--stem", stem]
    _reexec_library_command(forwarded)
    try:
        payload, code = run_smoke(Path.cwd(), stem)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc
    click.echo(render_smoke(payload), nl=False)
    if code:
        raise SystemExit(code)


@cli.group("audit")
def audit_group() -> None:
    """Deterministic audit-digest helpers."""


@audit_group.command("finding")
@click.argument(
    "digest",
    required=False,
    type=click.Path(dir_okay=False, path_type=Path),
)
@click.option(
    "--stem", help="Use scratch/audit/<stem>/audit.md when DIGEST is omitted."
)
def audit_finding_cmd(digest: Path | None, stem: str | None) -> None:
    """Print G-AUDIT-FINDING JSON from a digest. Does not open the Project."""
    from skore_skills.audit_finding import (
        audit_finding,
        default_digest,
        render_audit_finding,
    )

    if digest is not None:
        path = digest
    elif not stem:
        raise click.UsageError("provide DIGEST or --stem")
    else:
        path = default_digest(Path.cwd(), stem.strip())
    click.echo(render_audit_finding(audit_finding(path)), nl=False)
    if not path.is_file():
        raise SystemExit(1)


@cli.group("loop")
def loop_group() -> None:
    """Filesystem close-gates for evaluate, audit, and notebooks."""


@loop_group.command("artifacts")
@click.option("--stem", required=True, help="Experiment stem, e.g. 01_baseline.")
def loop_artifacts_cmd(stem: str) -> None:
    """Print which close step is due from files on disk."""
    from skore_skills.loop import loop_artifacts, render_loop

    try:
        payload = loop_artifacts(Path.cwd(), stem)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc
    click.echo(render_loop(payload), nl=False)
    if payload["action"] == "stop":
        raise SystemExit(1)


@loop_group.command("locator")
@click.option("--stem", required=True, help="Experiment stem, e.g. 01_baseline.")
def loop_locator_cmd(stem: str) -> None:
    """Print the persisted-report locator from scratch or the audit file."""
    from skore_skills.loop import loop_locator, render_loop

    try:
        payload = loop_locator(Path.cwd(), stem)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc
    click.echo(render_loop(payload), nl=False)


@loop_group.command("notebooks")
@click.option("--stem", required=True, help="Experiment stem, e.g. 01_baseline.")
def loop_notebooks_cmd(stem: str) -> None:
    """Print whether notebook convert is still due for ``stem``."""
    from skore_skills.loop import loop_notebooks, render_loop

    try:
        payload = loop_notebooks(Path.cwd(), stem)
    except ValueError as exc:
        raise click.UsageError(str(exc)) from exc
    click.echo(render_loop(payload), nl=False)


@cli.group("check")
def check_group() -> None:
    """Yes/no checks over workspace facts."""


@check_group.command("workspace")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "text"], case_sensitive=False),
    default="json",
    show_default=True,
)
def check_workspace(fmt: str) -> None:
    """Exit 1 if the tree is not scaffolded (no ``src/`` and no ``journal/``)."""
    text, code = render_workspace_check(Path.cwd(), fmt.lower())
    click.echo(text, nl=False)
    if code:
        raise SystemExit(code)


@cli.command("scaffold")
@click.option(
    "--package", "package_name", help="Snake-case import name for a full scaffold."
)
@click.option(
    "--journal",
    is_flag=True,
    help="Initialize JOURNAL.md instead of the full workspace.",
)
@click.option(
    "--stem",
    help="With --journal, also create journal/NN_short_name.md.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite files owned by the selected scaffold mode.",
)
def scaffold_cmd(
    package_name: str | None,
    journal: bool,
    stem: str | None,
    force: bool,
) -> None:
    """Copy full-workspace or journal templates into the current directory."""
    from skore_skills.scaffold import scaffold, scaffold_journal

    if (package_name is None) == (not journal):
        raise click.UsageError("choose exactly one of --package or --journal")
    if stem is not None and not journal:
        raise click.UsageError("--stem requires --journal")

    try:
        if journal:
            written = scaffold_journal(Path.cwd(), stem=stem, force=force)
        else:
            assert package_name is not None
            written = scaffold(Path.cwd(), package_name, force=force)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    for path in written:
        click.echo(str(path))


@cli.command("style")
@click.argument(
    "paths",
    nargs=-1,
    type=click.Path(path_type=Path),
)
@click.option(
    "--init",
    "initialize",
    is_flag=True,
    help="Write [tool.ruff] into pyproject.toml when it is missing.",
)
def style_cmd(paths: tuple[Path, ...], initialize: bool) -> None:
    """Run ruff check --fix then format on defaults or PATHS.

    Default globs: ``src/``, ``experiments/``, ``audit/``, ``data_analysis/``,
    top-level ``*.py``. ``--init`` without PATHS only writes ``[tool.ruff]``.
    """
    from skore_skills.style import initialize_style, run_style

    forwarded = ["style"]
    if initialize:
        forwarded.append("--init")
    forwarded.extend(os.fspath(path) for path in paths)
    _reexec_library_command(forwarded)
    if initialize:
        created = initialize_style(Path.cwd())
        click.echo(
            "wrote [tool.ruff] in pyproject.toml"
            if created
            else "ruff already configured"
        )
        if not paths:
            return

    def warn(message: str) -> None:
        click.echo(message, err=True)

    try:
        code = run_style(Path.cwd(), paths, warn=warn)
    except FileNotFoundError as exc:
        raise click.ClickException(str(exc)) from exc
    if code:
        raise SystemExit(code)


@cli.group("env")
def env_group() -> None:
    """Detect the env manager and print install commands."""


@env_group.command("detect")
def env_detect() -> None:
    """Print JSON evidence; exit non-zero when two managers are visible."""
    import json

    from skore_skills.env import detect

    payload = detect(Path.cwd())
    click.echo(json.dumps(payload, indent=2))
    if payload["ambiguous"]:
        raise SystemExit(1)


@env_group.command("add")
@click.argument("packages", nargs=-1, required=False)
@click.option(
    "--execute",
    is_flag=True,
    help="Run the install command instead of printing it.",
)
@click.option(
    "--feature",
    "--group",
    "feature",
    help="Manager feature/group (pixi --feature, uv/poetry --group).",
)
@click.option(
    "--editable",
    is_flag=True,
    help="Editable install of the workspace package (src/).",
)
def env_add(
    packages: tuple[str, ...],
    execute: bool,
    feature: str | None,
    editable: bool,
) -> None:
    """Print (or run) the manager-specific add command."""
    from skore_skills.env import add_packages

    text, code = add_packages(
        Path.cwd(),
        list(packages),
        execute=execute,
        feature=feature,
        editable=editable,
    )
    click.echo(text, nl=False)
    if code:
        raise SystemExit(code)


@env_group.command("add-skore")
@click.option(
    "--mode",
    type=click.Choice(["local", "hub", "mlflow"], case_sensitive=True),
    help="Override the recorded destination. Omit to follow it.",
)
@click.option(
    "--execute",
    is_flag=True,
    help="Run the install command instead of printing it.",
)
def env_add_skore(mode: str | None, execute: bool) -> None:
    """Print or run the manager-aware Skore install command."""
    from skore_skills.env import add_skore, resolve_add_skore_mode

    try:
        resolved = resolve_add_skore_mode(Path.cwd(), mode)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    text, code = add_skore(Path.cwd(), resolved, execute=execute)
    click.echo(text, nl=False)
    if code:
        raise SystemExit(code)


@env_group.command("sync")
@click.option(
    "--execute",
    is_flag=True,
    help="Run the sync command instead of printing it.",
)
def env_sync(execute: bool) -> None:
    """Print (or run) the post-init install/sync command."""
    from skore_skills.env import sync_environment

    text, code = sync_environment(Path.cwd(), execute=execute)
    click.echo(text, nl=False)
    if code:
        raise SystemExit(code)


@env_group.command("route")
@click.argument("package")
def env_route(package: str) -> None:
    """Print JSON scope for a package (default, agent, ask, or refuse)."""
    import json

    from skore_skills.env import route_package

    payload = route_package(package)
    if payload["scope"] == "refuse":
        click.echo(payload["message"])
        raise SystemExit(1)
    click.echo(json.dumps(payload, indent=2))


@env_group.command("stack")
def env_stack() -> None:
    """Print the packaged canonical-package policy as JSON."""
    import json

    from skore_skills.env import load_stack_policy

    click.echo(json.dumps(load_stack_policy(), indent=2))


@env_group.command("graphviz")
@click.option(
    "--execute",
    is_flag=True,
    help="Install conda Graphviz when possible and verify SVG rendering.",
)
def env_graphviz(execute: bool) -> None:
    """Print JSON for Graphviz; optionally install and verify it with pydot."""
    from skore_skills.env import ensure_graphviz

    text, code = ensure_graphviz(Path.cwd(), execute=execute)
    click.echo(text, nl=False)
    if code:
        raise SystemExit(code)


@env_group.command("verify")
@click.argument("packages", nargs=-1, required=False)
@click.option(
    "--execute",
    is_flag=True,
    help="Run the import check instead of printing JSON only.",
)
def env_verify(packages: tuple[str, ...], execute: bool) -> None:
    """Print (or run) an agent-env import check."""
    import json

    from skore_skills.env import verify_environment

    payload, code = verify_environment(
        Path.cwd(), list(packages) if packages else None, execute=execute
    )
    click.echo(json.dumps(payload, indent=2))
    if code:
        raise SystemExit(code)


@env_group.command("init")
@click.option(
    "--manager",
    required=True,
    type=click.Choice(
        ["pixi", "uv", "poetry", "hatch", "conda", "pip-venv"],
        case_sensitive=True,
    ),
)
@click.option(
    "--force",
    is_flag=True,
    help="Replace conda environment files if they already exist.",
)
def env_init(manager: str, force: bool) -> None:
    """Write manager and agent tables into pyproject.toml (or conda YAML)."""
    from skore_skills.env import init_environment

    text, code = init_environment(Path.cwd(), manager, force=force)
    click.echo(text, nl=False)
    if code:
        raise SystemExit(code)


@cli.group("policy")
def policy_group() -> None:
    """Read and write the ``workspace`` section of ``.skore``."""


@policy_group.command("set")
@click.argument("key")
@click.argument("value")
def policy_set(key: str, value: str) -> None:
    """Set one dotted workspace policy key and print the section JSON."""
    import json

    from skore_skills.policy import set_policy_value

    try:
        payload = set_policy_value(Path.cwd(), key, value)
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(json.dumps(payload, indent=2))


@cli.group("git")
def git_group() -> None:
    """Merge ignore rules, classify review paths, and print the end-turn hook."""


@git_group.command("ignore-merge")
@click.option(
    "--keep",
    "keep_paths",
    multiple=True,
    help="Force-track a hidden path after the user decides to keep it.",
)
@click.option(
    "--decide",
    is_flag=True,
    help="Record this as the hidden-path answer: --keep tracked, the rest ignored.",
)
def git_ignore_merge_cmd(keep_paths: tuple[str, ...], decide: bool) -> None:
    """Union packaged ignore rules into ``.gitignore``. No git commands."""
    from skore_skills.git import run_ignore_merge

    _emit_git(lambda: run_ignore_merge(Path.cwd(), keep=keep_paths, decide=decide))


@git_group.command("end-turn")
@click.option(
    "--stage",
    required=True,
    type=click.Choice(LOOP_STAGES, case_sensitive=True),
    help="Loop stage that just finished.",
)
def git_end_turn_cmd(stage: str) -> None:
    """Print whether to load ``persist-ml-git``. Never commits."""
    from skore_skills.git import run_end_turn

    _emit_git(lambda: run_end_turn(Path.cwd(), stage))


@git_group.command("review")
def git_review_cmd() -> None:
    """Print dirty paths that need a keep-or-ignore decision."""
    from skore_skills.git import run_review

    _emit_git(lambda: run_review(Path.cwd()))


@git_group.command("snapshot")
def git_snapshot_cmd() -> None:
    """Print whether to commit the tree before setup writes. Never commits."""
    from skore_skills.git import run_snapshot

    _emit_git(lambda: run_snapshot(Path.cwd()))


@git_group.command("review-decide")
@click.option(
    "--keep",
    "keep_paths",
    multiple=True,
    help="Track a review path the user chose to keep.",
)
@click.option(
    "--ignore",
    "ignore_paths",
    multiple=True,
    help="Ignore a review path the user chose not to keep.",
)
def git_review_decide_cmd(
    keep_paths: tuple[str, ...], ignore_paths: tuple[str, ...]
) -> None:
    """Record review choices in ``.gitignore``. No git add or commit."""
    from skore_skills.git import run_review_decide

    _emit_git(
        lambda: run_review_decide(Path.cwd(), keep=keep_paths, ignore=ignore_paths)
    )


@cli.group("experiment")
def experiment_group() -> None:
    """Create and update experiments in the skore project."""


@experiment_group.command("create")
@click.option("--stem", required=True)
@click.option("--question", required=True)
@click.option("--plan", default=None)
@click.option("--source-id", default=None)
@click.option("--check-code", default=None)
def experiment_create(
    stem: str,
    question: str,
    plan: str | None,
    source_id: str | None,
    check_code: str | None,
) -> None:
    """Create an idea, or a backlog row when ``--plan`` is set."""
    from skore.agent import create_experiment

    from skore_skills.project_api import open_project

    experiment = create_experiment(
        open_project(Path.cwd()),
        stem=stem,
        question=question,
        plan=plan,
        source_id=source_id,
        check_code=check_code,
    )
    click.echo(experiment.id)


@experiment_group.command("decide")
@click.argument("experiment_id")
@click.argument("status", type=click.Choice(["idea", "aside", "discarded"]))
def experiment_decide(experiment_id: str, status: str) -> None:
    """Move an idea among idea, aside, and discarded."""
    from skore_skills.project_api import open_project

    experiment = open_project(Path.cwd()).experiments.get(experiment_id)
    experiment.decide(status)
    click.echo(experiment.id)


@experiment_group.command("promote")
@click.argument("experiment_id")
@click.option("--plan", required=True)
def experiment_promote(experiment_id: str, plan: str) -> None:
    """Move an idea to the backlog and store its plan."""
    from skore_skills.project_api import open_project

    experiment = open_project(Path.cwd()).experiments.get(experiment_id)
    experiment.promote(plan)
    click.echo(experiment.id)


@experiment_group.command("list")
@click.option("--status", default=None)
def experiment_list(status: str | None) -> None:
    """Print the experiments frame as JSON."""
    from skore_skills.project_api import open_project

    frame = open_project(Path.cwd()).experiments.frame
    if status:
        frame = frame.loc[frame["status"].astype(str) == status]
    click.echo(frame.to_json(orient="records"))


@cli.group("objective")
def objective_group() -> None:
    """Read and replace the project objective."""


@objective_group.command("set")
@click.argument("text")
def objective_set(text: str) -> None:
    """Replace the project objective."""
    from skore_skills.project_api import open_project

    project = open_project(Path.cwd())
    project.objective = text
    click.echo(project.objective)


@objective_group.command("show")
def objective_show() -> None:
    """Print the project objective."""
    from skore_skills.project_api import open_project

    click.echo(open_project(Path.cwd()).objective)


@cli.group("journal")
def journal_group() -> None:
    """Render and import the journal. Do not edit the generated files."""


@journal_group.command("show")
def journal_show() -> None:
    """Print the journal rendered from the project."""
    from skore_skills.journal_api import show_journal

    click.echo(show_journal(Path.cwd()), nl=False)


@journal_group.command("render")
def journal_render() -> None:
    """Write generated journal files. They are not the store."""
    from skore_skills.journal_api import render_journal

    for path in render_journal(Path.cwd()):
        click.echo(path)


@journal_group.command("import")
def journal_import() -> None:
    """Import an existing JOURNAL.md once."""
    from skore_skills.journal_api import import_journal

    try:
        created = import_journal(Path.cwd())
    except ValueError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(created)


def main() -> None:
    """Run the CLI (``python -m skore_skills`` / console script)."""
    cli()
