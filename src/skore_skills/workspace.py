"""Read-only filesystem snapshot of an ML workspace.

Detection uses root manifests only. Ambient PATH managers are ignored.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

from skore_skills.frame import modeling_decisions_state
from skore_skills.installed_skills import installed_skills
from skore_skills.policy import (
    AUTOCOMMIT_VALUES,
    SETUP_PIECES,
    infer_loop_stage,
    load_policy,
)

MANAGER_ORDER = ("pixi", "uv", "poetry", "hatch", "conda", "pip-venv")

STATUS_KEYS = (
    "package",
    "env_manager",
    "managers",
    "evidence",
    "ambiguous",
    "mismatch",
    "has_src",
    "has_experiments",
    "has_journal",
    "has_tests",
    "data_analysis",
    "modeling_decisions",
    "ruff_toml",
    "git",
    "last_history_stem",
    "policy",
    "setup",
    "loop_stage",
    "skills",
    "workspace",
)


def load_pyproject(root: Path) -> dict[str, Any]:
    """Parse ``pyproject.toml`` if present."""
    path = root / "pyproject.toml"
    if not path.is_file():
        return {}
    return tomllib.loads(path.read_text(encoding="utf-8"))


def manager_evidence(root: Path) -> dict[str, list[str]]:
    """Return visible env-manager signals at ``root``.

    Parameters
    ----------
    root : pathlib.Path
        Project root.

    Returns
    -------
    dict
        Mapping of manager name to evidence filenames / sections.
    """
    evidence: dict[str, list[str]] = {}
    pixi_files = [
        name for name in ("pixi.toml", "pixi.lock") if (root / name).is_file()
    ]
    if pixi_files:
        evidence["pixi"] = pixi_files
    pyproject = load_pyproject(root)
    tools = pyproject.get("tool", {}) if isinstance(pyproject.get("tool"), dict) else {}
    if "pixi" in tools and "pixi" not in evidence:
        evidence["pixi"] = ["pyproject.toml:[tool.pixi]"]

    uv_bits: list[str] = []
    if (root / "uv.lock").is_file():
        uv_bits.append("uv.lock")
    if "uv" in tools:
        uv_bits.append("pyproject.toml:[tool.uv]")
    if uv_bits:
        evidence["uv"] = uv_bits

    poetry_bits: list[str] = []
    if (root / "poetry.lock").is_file():
        poetry_bits.append("poetry.lock")
    if "poetry" in tools:
        poetry_bits.append("pyproject.toml:[tool.poetry]")
    if poetry_bits:
        evidence["poetry"] = poetry_bits

    hatch_bits: list[str] = []
    if (root / "hatch.toml").is_file():
        hatch_bits.append("hatch.toml")
    hatch_tool = tools.get("hatch")
    if isinstance(hatch_tool, dict) and "envs" in hatch_tool:
        hatch_bits.append("pyproject.toml:[tool.hatch.envs]")
    if hatch_bits:
        evidence["hatch"] = hatch_bits

    conda_files = [
        name
        for name in ("environment.yml", "environment.yaml")
        if (root / name).is_file()
    ]
    if conda_files:
        evidence["conda"] = conda_files

    venv_dir = None
    for name in (".venv", "venv"):
        if (root / name).is_dir():
            venv_dir = name
            break
    if (root / "requirements.txt").is_file() and venv_dir is not None:
        evidence["pip-venv"] = ["requirements.txt", venv_dir]

    return evidence


def first_manager(evidence: dict[str, list[str]]) -> str:
    """Return the first manager in table order, or ``none``."""
    for name in MANAGER_ORDER:
        if name in evidence:
            return name
    return "none"


def manager_detection(root: Path) -> dict[str, Any]:
    """Return manifest-based manager facts shared by status and env detect."""
    evidence = manager_evidence(root)
    managers = [name for name in MANAGER_ORDER if name in evidence]
    ambiguous = len(managers) > 1
    env_manager: str | None
    if ambiguous:
        env_manager = None
    elif managers:
        env_manager = managers[0]
    else:
        env_manager = "none"
    recorded = load_policy(root).get("env_manager")
    mismatch = (
        recorded in MANAGER_ORDER and len(managers) == 1 and managers[0] != recorded
    )
    return {
        "env_manager": env_manager,
        "managers": managers,
        "evidence": evidence,
        "ambiguous": ambiguous,
        "mismatch": mismatch,
    }


def package_name(root: Path) -> str | None:
    """Return ``[project].name`` or the first ``src/`` package directory."""
    pyproject = load_pyproject(root)
    project = pyproject.get("project")
    if isinstance(project, dict):
        name = project.get("name")
        if isinstance(name, str) and name:
            return name
    src = root / "src"
    if src.is_dir():
        dirs = sorted(path.name for path in src.iterdir() if path.is_dir())
        if dirs:
            return dirs[0]
    return None


def last_history_stem(root: Path) -> str | None:
    """Stem of the last ``journal/*.md`` note, excluding ``JOURNAL.md``."""
    journal = root / "journal"
    if not journal.is_dir():
        return None
    notes = sorted(
        path
        for path in journal.glob("*.md")
        if path.name != "JOURNAL.md" and path.is_file()
    )
    if not notes:
        return None
    return notes[-1].stem


_DATA_ANALYSIS_SECTION = re.compile(
    r"^## Data understanding\s*\n(.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)
_DATA_ANALYSIS_SKIPPED = re.compile(r"(?im)^\s*\|\s*Status\s*\|\s*skipped\b")


def data_analysis_state(root: Path) -> str:
    """Return ``present``, ``skipped``, or ``missing`` for data analysis."""
    if (root / "data_analysis" / "data_analysis.md").is_file():
        return "present"
    journal = root / "journal" / "JOURNAL.md"
    if journal.is_file():
        match = _DATA_ANALYSIS_SECTION.search(journal.read_text(encoding="utf-8"))
        if match and _DATA_ANALYSIS_SKIPPED.search(match.group(1)):
            return "skipped"
    return "missing"


def ruff_is_configured(root: Path) -> bool:
    """Return True if ``ruff.toml`` or ``[tool.ruff]`` is present."""
    if (root / "ruff.toml").is_file():
        return True
    pyproject = load_pyproject(root)
    tool = pyproject.get("tool")
    return isinstance(tool, dict) and "ruff" in tool


def setup_status(
    policy: dict[str, Any],
    *,
    env_manager: str | None,
    ambiguous: bool,
    has_src: bool,
    has_journal: bool,
    git: bool,
) -> dict[str, Any]:
    """Return each setup piece as ``done``, ``declined``, or ``missing``.

    ``pending`` lists ``missing`` pieces in pipeline order. Editable is
    pending only after the workspace piece is ``done``. A stored
    ``declined`` wins over filesystem inference.
    """
    recorded = policy.get("setup")
    if not isinstance(recorded, dict):
        recorded = {}
    states: dict[str, str] = {}
    for piece in SETUP_PIECES:
        stored = recorded.get(piece)
        if stored == "declined":
            states[piece] = "declined"
            continue
        inferred = _setup_inferred(
            piece,
            policy,
            env_manager=env_manager,
            ambiguous=ambiguous,
            has_src=has_src,
            has_journal=has_journal,
            git=git,
        )
        if stored == "done" or inferred:
            states[piece] = "done"
            continue
        states[piece] = "missing"
    pending = [
        piece
        for piece in SETUP_PIECES
        if states[piece] == "missing"
        and not (piece == "editable" and states["workspace"] != "done")
    ]
    return {**states, "pending": pending}


def _setup_inferred(
    piece: str,
    policy: dict[str, Any],
    *,
    env_manager: str | None,
    ambiguous: bool,
    has_src: bool,
    has_journal: bool,
    git: bool,
) -> bool:
    """Return True when the workspace already proves this piece is done."""
    if piece == "env":
        recorded = policy.get("env_manager")
        managed = policy.get("env", {}).get("managed")
        if recorded not in MANAGER_ORDER:
            return False
        if managed is not True and managed is not False:
            return False
        if managed is False:
            return True
        return not ambiguous and env_manager == recorded
    if piece == "workspace":
        return has_src or has_journal
    if piece == "git":
        autocommit = policy.get("git", {}).get("autocommit")
        return git and autocommit in AUTOCOMMIT_VALUES
    return False


def is_scaffolded(root: Path) -> bool:
    """Return True if ``src/`` or ``journal/`` exists.

    Fail closed when both are missing (empty / unorganized tree).
    """
    return (root / "src").is_dir() or (root / "journal").is_dir()


def snapshot(root: Path) -> dict[str, Any]:
    """Return the frozen ``status`` mapping for ``root``."""
    manager = manager_detection(root)
    payload: dict[str, Any] = {
        "package": package_name(root),
        **manager,
        "has_src": (root / "src").is_dir(),
        "has_experiments": (root / "experiments").is_dir(),
        "has_journal": (root / "journal").is_dir(),
        "has_tests": (root / "tests").is_dir(),
        "data_analysis": data_analysis_state(root),
        "modeling_decisions": modeling_decisions_state(root),
        "ruff_toml": ruff_is_configured(root),
        "git": (root / ".git").exists(),
        "last_history_stem": last_history_stem(root),
    }
    policy = load_policy(root)
    payload["policy"] = policy
    payload["setup"] = setup_status(
        policy,
        env_manager=payload["env_manager"],
        ambiguous=payload["ambiguous"],
        has_src=payload["has_src"],
        has_journal=payload["has_journal"],
        git=payload["git"],
    )
    payload["loop_stage"] = infer_loop_stage(root, policy, payload)
    payload["skills"] = installed_skills(root)
    temporary = (root / ".skore-temporary").is_file()
    payload["workspace"] = "temporary" if temporary else "durable"
    if temporary:
        payload["setup"]["workspace"] = "done"
        payload["setup"]["pending"] = [
            piece
            for piece in payload["setup"]["pending"]
            if piece != "workspace"
        ]
    return payload


def format_status_text(payload: dict[str, Any]) -> str:
    """Render ``payload`` as one key: value line per frozen key."""
    lines = [f"{key}: {payload[key]}" for key in STATUS_KEYS]
    return "\n".join(lines) + "\n"
