"""Initialize and build an offline MkDocs site from workspace markdown."""

from __future__ import annotations

import hashlib
import html
import json
import posixpath
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from skore_skills.workspace import is_scaffolded, package_name

CONFIG_NAME = "mkdocs.yml"
HTML_DIR = "html"
BUILD_DIR = Path("_build")
DOCS_DIR = BUILD_DIR / "docs"
GENERATED_CONFIG = BUILD_DIR / CONFIG_NAME
BUILD_STATE = BUILD_DIR / "site-state.json"
SITE_ASSETS = Path(__file__).with_name("site_assets")
STAGED_ASSETS = Path("assets") / "skore"
GITIGNORE_LINES = (f"{BUILD_DIR.as_posix()}/", f"{HTML_DIR}/")
MISSING_MKDOCS = "mkdocs-material is required; add it with add-python-package"
ASSET_SUFFIXES = {".html", ".png", ".jpg", ".jpeg", ".svg", ".gif"}
LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)\)")
IMAGE_LINK = re.compile(
    r"(?<!!)\[([^\]]*)\]\(([^)\s]+\.(?:png|jpe?g|svg|gif))\)", re.IGNORECASE
)
RAW_IFRAME = re.compile(r'<iframe[^>]+src="([^"]+)"[^>]*>\s*</iframe>', re.IGNORECASE)
NOTEBOOKS_SECTION = re.compile(
    r"(?ms)^## Notebooks\s*\n.*?(?=^## |\Z)",
)
RESULTS_SECTION = re.compile(
    r"(?ms)^## Results\s*\n.*?(?=^## |\Z)",
)
METHOD_SECTION = re.compile(
    r"(?ms)^## Method\s*\n.*?(?=^## |\Z)",
)
DATA_UNDERSTANDING_SECTION = re.compile(
    r"(?ms)^## Data understanding\s*\n.*?(?=^## |\Z)",
)
RESULT_ITEMS = (
    ("checks", "Checks"),
    ("metrics", "Metrics"),
)
RESULT_EMBED = re.compile(r"<!--\s*results-embed:\s*([A-Za-z0-9_-]+)\s*-->")
CORE_RESULT_KINDS = {kind for kind, _heading in RESULT_ITEMS}
UNSTAGED_RESULT_HTML = CORE_RESULT_KINDS | {"report"}
RESULT_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".gif"}
EMBED_STYLESHEET = (STAGED_ASSETS / "embed.css").as_posix()
NOTEBOOK_SUFFIX = ".nb.html"
HOME_PAGE = "journal/JOURNAL.md"
STUB_HOME = "index.md"
# A ``_repr_html_`` fragment inherits its typography from whatever page
# holds it. Alone in a viewer it would inherit nothing, so wrap it in a
# document that carries the charset and the site font.
EMBED_DOCUMENT = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="{stylesheet}">
</head>
<body>
{body}</body>
</html>
"""


@dataclass(frozen=True)
class Page:
    """One Markdown report page in the generated site."""

    title: str
    source: Path
    dest_name: str
    notebook: Path | None = None
    section: str | None = None
    audit: Path | None = None


def _notebook_for(directory: Path, stem: str) -> Path | None:
    path = directory / f"{stem}{NOTEBOOK_SUFFIX}"
    return path if path.is_file() else None


def docs_path(root: Path, path: Path) -> str:
    """Return the staged path of a workspace file. The docs tree mirrors it."""
    return path.relative_to(root).as_posix()


def link_from(page: Page, target: str) -> str:
    """Return the docs path ``target`` as a link written on ``page``."""
    return posixpath.relpath(target, posixpath.dirname(page.dest_name) or ".")


def result_dest(stem: str, kind: str, suffix: str = ".html") -> str:
    """Return the staged path of a Results viewer."""
    if not suffix.startswith("."):
        suffix = f".{suffix}"
    return f"scratch/results/{stem}/{kind}{suffix}"


def result_source(
    root: Path, stem: str, kind: str, suffix: str = ".html"
) -> Path | None:
    """Return the scratch snapshot when it exists."""
    path = root / "scratch" / "results" / stem / f"{kind}{suffix}"
    return path if path.is_file() else None


def result_report_dest(stem: str, kind: str) -> str:
    """Return the staged path of a multi-page report."""
    return f"scratch/results/{stem}/{kind}/index.html"


def result_report_source(root: Path, stem: str, kind: str) -> Path | None:
    """Return ``kind/index.html`` when that report directory exists."""
    path = root / "scratch" / "results" / stem / kind / "index.html"
    return path if path.is_file() else None


def collect_pages(root: Path) -> list[Page]:
    """Return Markdown report pages; notebooks are pages of their own."""
    pages: list[Page] = []
    journal = root / "journal" / "JOURNAL.md"
    if journal.is_file():
        pages.append(Page("Home", journal, HOME_PAGE))
    analysis = root / "data_analysis" / "data_analysis.md"
    if analysis.is_file():
        pages.append(
            Page(
                "Exploratory data analysis",
                analysis,
                "data_analysis/data_analysis.md",
                _notebook_for(root / "data_analysis", "data_analysis"),
            )
        )
    notes = root / "journal"
    if notes.is_dir():
        for path in sorted(notes.glob("*.md")):
            if path.name in {"JOURNAL.md", "README.md"}:
                continue
            pages.append(
                Page(
                    path.stem,
                    path,
                    f"journal/{path.name}",
                    _notebook_for(root / "experiments", path.stem),
                    "Experiments",
                    _notebook_for(root / "audit", path.stem),
                )
            )
    return pages


LAUNCHER_NAME = "report.html"


def site_title(root: Path) -> str:
    """Return the project name used as the site title."""
    return package_name(root) or root.name


def launcher_name(root: Path) -> str:
    """Return the workspace-root HTML launcher filename."""
    del root
    return LAUNCHER_NAME


def launcher_url(root: Path) -> str:
    """Return a clickable ``file://`` URL for the root launcher."""
    return (root / launcher_name(root)).resolve().as_uri()


def entry_page(root: Path) -> str:
    """Return the built page the launcher opens, relative to ``html/``."""
    if (root / HOME_PAGE).is_file():
        return Path(HOME_PAGE).with_suffix(".html").as_posix()
    return Path(STUB_HOME).with_suffix(".html").as_posix()


def render_launcher(title: str, entry: str) -> str:
    """Return a ``file://``-safe redirect into ``html/<entry>``."""
    safe = html.escape(title)
    target = html.escape(f"{HTML_DIR}/{entry}", quote=True)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "  <head>\n"
        '    <meta charset="utf-8">\n'
        f"    <title>{safe}</title>\n"
        f'    <meta http-equiv="refresh" content="0; url={target}">\n'
        f'    <script>location.replace("{target}");</script>\n'
        "  </head>\n"
        "  <body>\n"
        f'    <p><a href="{target}">Open {safe}</a></p>\n'
        "  </body>\n"
        "</html>\n"
    )


def render_mkdocs_yml(
    pages: list[Page], *, stub_home: bool = False, site_name: str, entry: str
) -> str:
    """Return generated ``mkdocs.yml`` text for ``file://`` browsing."""
    lines = [
        "# Generated by python -m skore_skills site build",
        f"site_name: {json.dumps(site_name)}",
        'site_url: ""',
        "use_directory_urls: false",
        "docs_dir: docs",
        "site_dir: ../html",
        "theme:",
        "  name: material",
        "  font: false",
        "  logo: assets/skore/skore-text.svg",
        "  favicon: assets/skore/favicon.svg",
        "markdown_extensions:",
        "  - pymdownx.arithmatex:",
        "      generic: true",
        "extra:",
        f"  homepage: {entry}",
        "  polyfills:",
        "    - assets/skore/iframe-worker.js",
        "plugins:",
        "  - search",
        "  - offline",
        "extra_css:",
        "  - assets/skore/katex/katex.min.css",
        "  - assets/skore/skore.css",
        "extra_javascript:",
        "  - assets/skore/nav-data.js",
        "  - assets/skore/skore.js",
        "  - assets/skore/katex/katex.min.js",
        "  - assets/skore/katex/contrib/auto-render.min.js",
        "  - assets/skore/katex-render.js",
        "nav:",
    ]
    if stub_home:
        lines.append(f"  - Home: {STUB_HOME}")
    if pages:
        sections: dict[str, list[Page]] = {}
        for page in pages:
            if page.section is None:
                lines.append(f"  - {page.title}: {page.dest_name}")
            else:
                sections.setdefault(page.section, []).append(page)
        for title, children in sections.items():
            lines.append(f"  - {title}:")
            lines.extend(f"      - {page.title}: {page.dest_name}" for page in children)
    lines.append("")
    return "\n".join(lines)


def write_generated_config(root: Path, pages: list[Page], *, stub_home: bool) -> Path:
    """Write ``_build/mkdocs.yml`` for this build."""
    dest = root / GENERATED_CONFIG
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        render_mkdocs_yml(
            pages,
            stub_home=stub_home,
            site_name=site_title(root),
            entry=entry_page(root),
        ),
        encoding="utf-8",
    )
    return dest


def ensure_site_gitignore(root: Path) -> None:
    """Append ``_build/``, ``html/``, and the root launcher to ``.gitignore``."""
    gitignore = root / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    present = {line.strip() for line in existing.splitlines()}
    wanted = (*GITIGNORE_LINES, launcher_name(root))
    additions = [line for line in wanted if line not in present]
    if not additions:
        return
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    gitignore.write_text(
        existing + prefix + "\n".join(additions) + "\n", encoding="utf-8"
    )


def render_embed(name: str, title: str) -> str:
    """Return a fixed-height iframe with a link to open the file alone."""
    safe_name = html.escape(name, quote=True)
    safe_title = html.escape(title)
    return (
        f'<div class="skore-embed">\n'
        f'  <iframe src="{safe_name}" title="{safe_title}" loading="lazy"></iframe>\n'
        f'  <p class="skore-embed__open">{new_tab_link(name, "Open separately")}</p>\n'
        f"</div>"
    )


def new_tab_link(href: str, label: str) -> str:
    """Return a link that opens in a new tab. Markdown cannot set a target."""
    return (
        f'<a href="{html.escape(href, quote=True)}" target="_blank" '
        f'rel="noopener">{html.escape(label)}</a>'
    )


def render_inline(fragment: str) -> str:
    """Return an HTML fragment wrapped so Markdown leaves it alone."""
    return f'<div class="skore-inline">\n{fragment.strip()}\n</div>'


def render_html(name: str, source_dir: Path | None) -> str:
    """Paste a fragment file into the page; any other HTML gets an iframe."""
    if source_dir is not None and (source_dir / name).is_file():
        text = (source_dir / name).read_text(encoding="utf-8")
        if not is_document(text):
            return render_inline(text)
    return render_embed(name, "Interactive report")


def embed_assets(text: str, source_dir: Path | None = None) -> str:
    """Render asset links inline: images as images, HTML pasted or framed.

    ``source_dir`` holds the HTML files that the Markdown refers to by name.
    """
    seen = set(RAW_IFRAME.findall(text))
    text = RAW_IFRAME.sub(lambda match: render_html(match.group(1), source_dir), text)
    embedded: list[str] = []
    for line in text.splitlines():
        embedded.append(IMAGE_LINK.sub(r"![\1](\2)", line))
        for match in LINK.finditer(line):
            name = match.group(2)
            if Path(name).suffix.lower() != ".html" or name in seen:
                continue
            seen.add(name)
            embedded.extend(["", render_html(name, source_dir)])
    return "\n".join(embedded) + "\n"


def inject_notebook(text: str, page: Page, root: Path) -> str:
    """Link the paired notebooks. They open as pages of their own."""
    if page.section == "Experiments":
        links = [
            f"- {new_tab_link(link_from(page, docs_path(root, source)), heading)}"
            for source, heading in (
                (page.notebook, "Evaluation notebook"),
                (page.audit, "Audit notebook"),
            )
            if source is not None
        ]
        section = "## Notebooks\n"
        if links:
            section += "\n" + "\n".join(links) + "\n"

        if NOTEBOOKS_SECTION.search(text):
            return NOTEBOOKS_SECTION.sub(lambda _match: section, text, count=1)
        if not links:
            return text
        return f"{text.rstrip()}\n\n{section}"

    for source, heading, label in (
        (page.notebook, "Notebook", "Open the notebook"),
        (page.audit, "Audit", "Open the audit notebook"),
    ):
        if source is None:
            continue
        name = link_from(page, docs_path(root, source))
        if f'href="{name}"' in text:
            continue
        if not text.endswith("\n"):
            text += "\n"
        text = f"{text}\n## {heading}\n\n{new_tab_link(name, label)}\n"
    return text


def _append_under_heading(section: str, heading: str, embed: str) -> str:
    """Append an embed after the prose of one Results subsection."""
    pattern = re.compile(
        rf"(?ms)^(### {re.escape(heading)}\n.*?)(?=^### |\Z)",
    )
    match = pattern.search(section)
    if match is None:
        return section
    body = match.group(1).rstrip() + f"\n\n{embed}\n\n"
    return section[: match.start()] + body + section[match.end() :]


def _append_after_embed_marker(section: str, slug: str, embed: str) -> str:
    """Append an embed in the subsection that marks ``slug``."""
    marker = f"<!-- results-embed: {slug} -->"
    pattern = re.compile(r"(?ms)^(### .+\n.*?)(?=^### |\Z)")
    match = next(
        (item for item in pattern.finditer(section) if marker in item.group(1)),
        None,
    )
    if match is not None:
        body = match.group(1).rstrip() + f"\n\n{embed}\n\n"
        return section[: match.start()] + body + section[match.end() :]
    if marker not in section:
        return section
    return section.replace(marker, f"{marker}\n\n{embed}\n", 1)


def _result_embed(root: Path, page: Page, slug: str, title: str) -> str | None:
    """Return what the page shows for a scratch snapshot.

    Checks and metrics are HTML fragments pasted into the page. An image
    is shown as is. A report directory is a link that opens in a new tab.
    Other HTML sits in an iframe.
    """
    stem = Path(page.dest_name).stem
    parts: list[str] = []
    for suffix in sorted(RESULT_IMAGE_SUFFIXES):
        if result_source(root, stem, slug, suffix) is not None:
            name = link_from(page, result_dest(stem, slug, suffix))
            parts.append(f"![{title}]({name})")
            break
    if result_report_source(root, stem, slug) is not None:
        name = link_from(page, result_report_dest(stem, slug))
        parts.append(new_tab_link(name, f"Open the full {slug} report"))
        return "\n\n".join(parts)
    source = result_source(root, stem, slug, ".html")
    if source is not None and slug in CORE_RESULT_KINDS:
        parts.append(render_inline(source.read_text(encoding="utf-8")))
    elif source is not None:
        name = link_from(page, result_dest(stem, slug))
        parts.append(render_embed(name, title))
    return "\n\n".join(parts) or None


def _inject_marked_embeds(section: str, root: Path, page: Page) -> str:
    """Append scratch snapshots after ``results-embed`` comments in ``section``."""
    stem = Path(page.dest_name).stem
    for slug in RESULT_EMBED.findall(section):
        if slug in UNSTAGED_RESULT_HTML:
            continue
        embed = _result_embed(root, page, slug, f"{page.title} {slug}")
        if embed is None:
            continue
        names = [
            link_from(page, result_report_dest(stem, slug)),
            link_from(page, result_dest(stem, slug, ".html")),
            *(
                link_from(page, result_dest(stem, slug, suffix))
                for suffix in RESULT_IMAGE_SUFFIXES
            ),
        ]
        if any(
            f'src="{name}"' in section
            or f'href="{name}"' in section
            or f"]({name})" in section
            for name in names
        ):
            continue
        section = _append_after_embed_marker(section, slug, embed)
    return section


def inject_results(text: str, page: Page, root: Path) -> str:
    """Embed scratch snapshots under Method and Results on experiment pages."""
    if page.section != "Experiments":
        return text
    method = METHOD_SECTION.search(text)
    if method is not None:
        section = _inject_marked_embeds(method.group(0), root, page)
        text = text[: method.start()] + section + text[method.end() :]
    match = RESULTS_SECTION.search(text)
    if match is None:
        return text
    section = match.group(0)
    for kind, heading in RESULT_ITEMS:
        embed = _result_embed(root, page, kind, f"{page.title} {heading.lower()}")
        if embed is None or embed in section:
            continue
        section = _append_under_heading(section, heading, embed)
    section = _inject_marked_embeds(section, root, page)
    return text[: match.start()] + section + text[match.end() :]


def is_document(text: str) -> bool:
    """Whether ``text`` is a whole HTML document rather than a fragment.

    ``<body>`` is not a marker: ``estimator_html_repr`` emits one in the
    middle of its fragment.
    """
    head = text[:2048].lower()
    return "<!doctype" in head or "<html" in head


def as_embed_document(text: str, dest_dir: str = "") -> str:
    """Return ``text`` as a whole HTML document, wrapping a fragment.

    ``dest_dir`` is the docs folder the file is written to; the baseline
    stylesheet is linked from there.
    """
    if is_document(text):
        return text
    body = text if text.endswith("\n") else f"{text}\n"
    stylesheet = posixpath.relpath(EMBED_STYLESHEET, dest_dir or ".")
    return EMBED_DOCUMENT.format(stylesheet=stylesheet, body=body)


def _copy_file(source: Path, dest: Path, dest_dir: str) -> None:
    """Copy one staged file. HTML fragments become whole documents."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if source.suffix.lower() == ".html":
        dest.write_text(
            as_embed_document(source.read_text(encoding="utf-8"), dest_dir),
            encoding="utf-8",
        )
    else:
        shutil.copy2(source, dest)


def _copy_folder_assets(root: Path, docs: Path, folder: str) -> None:
    """Copy the figures and HTML next to the Markdown, keeping their paths."""
    for path in sorted((root / folder).rglob("*")):
        if (
            path.is_file()
            and path.suffix.lower() in ASSET_SUFFIXES
            and not path.name.endswith(NOTEBOOK_SUFFIX)
        ):
            name = docs_path(root, path)
            _copy_file(path, docs / name, posixpath.dirname(name))


def _copy_notebooks(root: Path, docs: Path, page: Page) -> None:
    for source in (page.notebook, page.audit):
        if source is not None:
            dest = docs / docs_path(root, source)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest)


def _copy_result_html(root: Path, docs: Path, page: Page) -> None:
    if page.section != "Experiments":
        return
    stem = Path(page.dest_name).stem
    directory = root / "scratch" / "results" / stem
    if not directory.is_dir():
        return
    for path in sorted(directory.iterdir()):
        name = docs_path(root, path)
        if path.is_dir() and (path / "index.html").is_file():
            shutil.copytree(path, docs / name, dirs_exist_ok=True)
            continue
        suffix = path.suffix.lower()
        if not path.is_file() or (
            suffix == ".html" and path.stem in UNSTAGED_RESULT_HTML
        ):
            continue
        if suffix == ".html" or suffix in RESULT_IMAGE_SUFFIXES:
            _copy_file(path, docs / name, posixpath.dirname(name))


def _write_stub_index(docs: Path, pages: list[Page]) -> bool:
    if any(page.dest_name == HOME_PAGE for page in pages):
        return False
    (docs / STUB_HOME).write_text("# Report\n", encoding="utf-8")
    return True


def _copy_site_assets(docs: Path) -> None:
    shutil.copytree(SITE_ASSETS, docs / STAGED_ASSETS)


def write_nav_data(docs: Path, pages: list[Page], *, stub_home: bool) -> Path:
    """Write top-navigation data as JavaScript that works under ``file://``."""
    items: list[dict[str, object]] = []
    if stub_home:
        items.append({"label": "Home", "href": "index.html"})
    sections: dict[str, list[dict[str, object]]] = {}
    for page in pages:
        item: dict[str, object] = {
            "label": page.title,
            "href": Path(page.dest_name).with_suffix(".html").as_posix(),
        }
        if page.section is None:
            items.append(item)
        else:
            sections.setdefault(page.section, []).append(item)
    items.extend(
        {"label": title, "children": children} for title, children in sections.items()
    )
    dest = docs / STAGED_ASSETS / "nav-data.js"
    dest.write_text(
        f"window.__SKORE_NAV__ = {json.dumps(items, ensure_ascii=False)};\n",
        encoding="utf-8",
    )
    return dest


def stage_docs(root: Path) -> tuple[Path, list[Page], bool]:
    """Copy report Markdown, assets, and existing companions into ``_build/docs``.

    The docs tree mirrors the workspace, so a link written between source files
    resolves between the staged ones and no link is rewritten.

    Returns
    -------
    tuple
        Staging directory, collected pages, and whether a stub home was written.
    """
    docs = root / DOCS_DIR
    if docs.exists():
        shutil.rmtree(docs)
    docs.mkdir(parents=True)
    pages = collect_pages(root)
    analysis_exists = (root / "data_analysis" / "data_analysis.md").is_file()
    for page in pages:
        text = page.source.read_text(encoding="utf-8")
        if page.dest_name == HOME_PAGE and not analysis_exists:
            text = DATA_UNDERSTANDING_SECTION.sub("", text, count=1)
        text = embed_assets(text, page.source.parent)
        text = inject_results(inject_notebook(text, page, root), page, root)
        dest = docs / page.dest_name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        _copy_notebooks(root, docs, page)
        _copy_result_html(root, docs, page)
    for folder in ("journal", "data_analysis"):
        _copy_folder_assets(root, docs, folder)
    _copy_site_assets(docs)
    stub_home = _write_stub_index(docs, pages)
    write_nav_data(docs, pages, stub_home=stub_home)
    return docs, pages, stub_home


def init_site(root: Path, *, force: bool = False) -> Path:
    """Ignore site build directories. Does not write a user ``mkdocs.yml``.

    Parameters
    ----------
    root : pathlib.Path
        Workspace root.
    force : bool, optional
        Unused; kept so existing ``--force`` callers stay valid.

    Raises
    ------
    ValueError
        When the workspace is not scaffolded.
    """
    del force
    if not is_scaffolded(root):
        raise ValueError("workspace is not scaffolded")
    ensure_site_gitignore(root)
    gitignore = root / ".gitignore"
    gitignore.touch()
    return gitignore


def _site_input_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        paths.append(pyproject)
    for pattern in (
        "journal/*.md",
        "data_analysis/*.md",
        f"experiments/*{NOTEBOOK_SUFFIX}",
        f"audit/*{NOTEBOOK_SUFFIX}",
    ):
        paths.extend(path for path in root.glob(pattern) if path.is_file())
    for folder in ("journal", "data_analysis"):
        paths.extend(
            path
            for path in (root / folder).rglob("*")
            if path.is_file() and path.suffix.lower() in ASSET_SUFFIXES
        )
    results = root / "scratch" / "results"
    if results.is_dir():
        paths.extend(path for path in results.rglob("*") if path.is_file())
    paths.extend(path for path in SITE_ASSETS.rglob("*") if path.is_file())
    return sorted(set(paths), key=lambda path: path.as_posix())


def site_fingerprint(root: Path) -> str:
    """Return a content fingerprint for every input copied into the site."""
    digest = hashlib.sha256(root.name.encode())
    for path in _site_input_paths(root):
        try:
            name = path.relative_to(root).as_posix()
        except ValueError:
            name = f"bundled/{path.relative_to(SITE_ASSETS).as_posix()}"
        digest.update(name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _site_is_current(root: Path, fingerprint: str) -> bool:
    state = root / BUILD_STATE
    if not (
        state.is_file()
        and (root / HTML_DIR / entry_page(root)).is_file()
        and (root / launcher_name(root)).is_file()
    ):
        return False
    try:
        payload = json.loads(state.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return payload.get("fingerprint") == fingerprint


def build_site(root: Path, *, if_stale: bool = False) -> str:
    """Stage sources, write ``_build/mkdocs.yml``, and run ``mkdocs build``.

    Raises
    ------
    ValueError
        When the workspace is not scaffolded.
    RuntimeError
        When ``mkdocs`` is missing, the build fails, or the entry page is missing.
    """
    if not is_scaffolded(root):
        raise ValueError("workspace is not scaffolded")
    fingerprint = site_fingerprint(root)
    if if_stale and _site_is_current(root, fingerprint):
        return f"site is current: {launcher_url(root)}"
    ensure_site_gitignore(root)
    _docs, pages, stub_home = stage_docs(root)
    write_generated_config(root, pages, stub_home=stub_home)
    try:
        completed = subprocess.run(
            ["mkdocs", "build", "--config-file", GENERATED_CONFIG.as_posix()],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(MISSING_MKDOCS) from exc
    if completed.returncode:
        detail = (completed.stderr or completed.stdout or "mkdocs build failed").strip()
        raise RuntimeError(detail)
    entry = entry_page(root)
    if not (root / HTML_DIR / entry).is_file():
        raise RuntimeError(f"mkdocs build did not write {HTML_DIR}/{entry}")
    launcher = root / launcher_name(root)
    launcher.write_text(render_launcher(site_title(root), entry), encoding="utf-8")
    state = root / BUILD_STATE
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"fingerprint": fingerprint}) + "\n", encoding="utf-8")
    broken = [
        line.strip()
        for line in (completed.stderr or "").splitlines()
        if "contains a link" in line
    ]
    extra = "\n".join([(completed.stdout or "").strip(), *broken]).strip()
    url = launcher_url(root)
    if extra:
        return f"{extra}\n{url}"
    return url
