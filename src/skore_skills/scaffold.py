"""Copy setup-workspace templates into a project tree."""

from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path

ALREADY_SCAFFOLDED = (
    "refusing to overwrite an existing layout; pass --force to replace files"
)
INVALID_PACKAGE = "package name must be a Python identifier (snake_case)"
MISSING_TEMPLATE = "packaged scaffold templates are missing"
INVALID_STEM = "journal stem must look like NN_short_name"

# Root files an env manager may already own (``pixi init`` writes
# ``pyproject.toml`` and ``.gitignore``). Kept unless ``--force``.
PRESERVED_ROOT_FILES = frozenset({Path("pyproject.toml"), Path(".gitignore")})

SRC_TEMPLATES = {
    "src___init__.py": "__init__.py",
    "src_data.py": "data.py",
    "src_features.py": "features.py",
    "src_pipeline.py": "pipeline.py",
    "src_evaluate.py": "evaluate.py",
}

# Directory README.md files (cookiecutter). ``tests/smoke`` is nested.
LAYOUT_READMES = (
    ("readme_src.md", Path("src") / "README.md"),
    ("readme_experiments.md", Path("experiments") / "README.md"),
    ("readme_journal.md", Path("journal") / "README.md"),
    ("readme_data_analysis.md", Path("data_analysis") / "README.md"),
    ("readme_data.md", Path("data") / "README.md"),
    ("readme_audit.md", Path("audit") / "README.md"),
    ("readme_tests_smoke.md", Path("tests") / "smoke" / "README.md"),
    ("readme_scratch.md", Path("scratch") / "README.md"),
)


def template_root() -> Path:
    """Return the packaged copy of setup-workspace templates."""
    return Path(str(files("skore_skills").joinpath("templates")))


def render_template(text: str, package: str, *, pyproject: bool = False) -> str:
    """Substitute ``<pkg>`` and related placeholders."""
    kebab = package.replace("_", "-")
    if pyproject:
        text = text.replace('name = "<pkg>"', f'name = "{kebab}"')
    return text.replace("<pkg>", package).replace("<project-name>", kebab)


ENV_SKELETON_NAME = 'name = "workspace"'
ENV_SKELETON_DESCRIPTION = 'description = "ML experimentation workspace."'
ENV_SKELETON_HATCH_PACKAGES = '[tool.hatch.build.targets.wheel]\npackages = ["src"]'


def specialize_env_skeleton(path: Path, package: str) -> bool:
    """Rewrite env-init Hatch metadata once the import name is known.

    Only the generic ``env init`` skeleton is touched. Custom
    manager-only ``pyproject.toml`` files stay as they are.
    """
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8")
    if (
        ENV_SKELETON_NAME not in text
        or ENV_SKELETON_DESCRIPTION not in text
        or ENV_SKELETON_HATCH_PACKAGES not in text
    ):
        return False
    kebab = package.replace("_", "-")
    text = text.replace(ENV_SKELETON_NAME, f'name = "{kebab}"', 1)
    text = text.replace(
        ENV_SKELETON_DESCRIPTION,
        f'description = "Workspace package for the {package} ML experiments."',
        1,
    )
    text = text.replace(
        ENV_SKELETON_HATCH_PACKAGES,
        f'[tool.hatch.build.targets.wheel]\npackages = ["src/{package}"]',
        1,
    )
    path.write_text(text, encoding="utf-8")
    return True


def layout_exists(root: Path) -> bool:
    """Return True if a scaffolded layout is already present.

    A manager-only root (``pixi.toml`` / ``pyproject.toml`` from
    ``pixi init``) is not a finished layout.
    """
    return (root / "src").exists() or (root / "journal").exists()


def scaffold(root: Path, package: str, *, force: bool = False) -> list[Path]:
    """Write the template tree under ``root``.

    Parameters
    ----------
    root : pathlib.Path
        Destination workspace.
    package : str
        Snake-case import name (``src/<package>/``).
    force : bool, optional
        Replace files when a layout already exists.

    Returns
    -------
    list of pathlib.Path
        Paths written, relative to ``root``.

    Raises
    ------
    ValueError
        Invalid package name, existing layout without ``force``, or
        missing packaged templates.
    """
    if not package.isidentifier():
        raise ValueError(INVALID_PACKAGE)
    if layout_exists(root) and not force:
        raise ValueError(ALREADY_SCAFFOLDED)
    templates = template_root()
    if not templates.is_dir():
        raise ValueError(MISSING_TEMPLATE)

    written: list[Path] = []

    def write(rel: Path, body: str) -> None:
        dest = root / rel
        if rel in PRESERVED_ROOT_FILES and dest.is_file() and not force:
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(body, encoding="utf-8")
        written.append(rel)

    for src_name, dest_name in SRC_TEMPLATES.items():
        raw = (templates / src_name).read_text(encoding="utf-8")
        write(Path("src") / package / dest_name, render_template(raw, package))

    for name, dest in (
        ("pyproject.toml.template", Path("pyproject.toml")),
        (".gitignore", Path(".gitignore")),
    ):
        raw = (templates / name).read_text(encoding="utf-8")
        write(
            dest, render_template(raw, package, pyproject=name.startswith("pyproject"))
        )

    for name, dest in LAYOUT_READMES:
        raw = (templates / name).read_text(encoding="utf-8")
        write(dest, render_template(raw, package))

    from skore_skills.style import ensure_ruff_in_pyproject

    pyproject_path = root / "pyproject.toml"
    if specialize_env_skeleton(pyproject_path, package):
        rel = Path("pyproject.toml")
        if rel not in written:
            written.append(rel)
    if pyproject_path.is_file() and ensure_ruff_in_pyproject(pyproject_path):
        rel = Path("pyproject.toml")
        if rel not in written:
            written.append(rel)
    return written


def scaffold_journal(
    root: Path,
    *,
    stem: str | None = None,
    force: bool = False,
) -> list[Path]:
    """Journal files are rendered from the project. Nothing is authored here."""
    del root, force
    if stem is not None and re.fullmatch(r"\d{2}_[a-z0-9][a-z0-9_]*", stem) is None:
        raise ValueError(INVALID_STEM)
    return []
