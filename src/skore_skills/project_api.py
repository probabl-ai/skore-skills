"""Open the local skore project that stores the experiment loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skore_skills.workspace import package_name


def workspace_dir(root: Path) -> Path:
    """Return the skore workspace directory for ``root``."""
    return root / ".skore"


def project_ready(root: Path) -> bool:
    """Return whether a skore workspace has already been created."""
    return (workspace_dir(root) / ".SKORE_WORKSPACE").is_file()


def open_project(root: Path) -> Any:
    """Open or create the local project for ``root``."""
    import skore

    name = package_name(root) or root.name or "ml"
    return skore.Project(name, mode="local", workspace=workspace_dir(root))


def experiment_by_stem(root: Path, stem: str) -> Any | None:
    """Return the experiment handle for ``stem``, without creating a project."""
    if not project_ready(root):
        return None
    frame = open_project(root).experiments.frame
    if frame.empty:
        return None
    matched = frame.loc[frame["stem"].astype(str) == stem]
    if matched.empty:
        return None
    return open_project(root).experiments.get(str(matched.iloc[0]["id"]))
