"""Initialize and build an offline MkDocs site from workspace markdown."""

from __future__ import annotations

import hashlib
import html
import json
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
MISSING_INDEX = "mkdocs build did not write html/index.html"
MISSING_MKDOCS = "mkdocs-material is required; add it with add-python-package"
ASSET_SUFFIXES = {".html", ".png", ".jpg", ".jpeg", ".svg", ".gif"}
MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
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
    ("report", "Report overview"),
    ("checks", "Checks"),
    ("metrics", "Metrics"),
)
RESULT_EMBED = re.compile(r"<!--\s*results-embed:\s*([A-Za-z0-9_-]+)\s*-->")
CORE_RESULT_KINDS = {kind for kind, _heading in RESULT_ITEMS}
RESULT_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".svg", ".gif"}
# Staged report pages measure themselves and post their height up, so the
# viewer fits the report exactly. Reading the document from the parent is
# blocked under ``file://``; postMessage is not. Measure the body box, not
# the root: the root stretches to the frame and would never shrink back.
# A skrub node page sizes itself with ``100vh``. Measuring that and
# resizing the frame shrinks the iframe on every click, so those pages
# ask the viewer to drop the inline height and use its own CSS height.
HEIGHT_REPORTER = """<script>
(() => {
  const post = () => {
    if (document.querySelector(".data_op-node")) {
      parent.postMessage({ type: "skore-embed-height", fill: true }, "*");
      return;
    }
    const style = getComputedStyle(document.body);
    parent.postMessage(
      {
        type: "skore-embed-height",
        height: Math.ceil(
          document.body.getBoundingClientRect().height +
            parseFloat(style.marginTop) +
            parseFloat(style.marginBottom),
        ),
      },
      "*",
    );
  };
  addEventListener("load", post);
  new ResizeObserver(post).observe(document.body);
})();
</script>
"""
EMBED_STYLESHEET = (STAGED_ASSETS / "embed.css").as_posix()
EMBED_HOST_ID = "skore-embed-host"
EMBED_TEMPLATE_ID = "skore-embed-template"
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
{body}{reporter}</body>
</html>
"""
# Fragments without a shadow root of their own get one here, so the
# baseline stylesheet and the fragment's own rules cannot collide.
EMBED_SHADOW_HOST = """<div id="{host}"></div>
<template id="{template}">
<link rel="stylesheet" href="{stylesheet}">
{fragment}</template>
<script>
(() => {{
  const host = document.getElementById("{host}");
  const template = document.getElementById("{template}");
  host.attachShadow({{ mode: "open" }}).append(template.content.cloneNode(true));
}})();
</script>
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
    path = directory / f"{stem}.nb.html"
    return path if path.is_file() else None


def notebook_dest(page: Page) -> str:
    """Return the staged file name of the notebook page for ``page``."""
    return f"{Path(page.dest_name).stem}.nb.html"


def audit_dest(page: Page) -> str:
    """Return the staged file name of the audit notebook for ``page``."""
    return f"{Path(page.dest_name).stem}.audit.nb.html"


def result_dest(stem: str, kind: str, suffix: str = ".html") -> str:
    """Return the staged file name of a Results viewer."""
    if not suffix.startswith("."):
        suffix = f".{suffix}"
    return f"{stem}.{kind}{suffix}"


def result_source(
    root: Path, stem: str, kind: str, suffix: str = ".html"
) -> Path | None:
    """Return the scratch snapshot when it exists."""
    path = root / "scratch" / "results" / stem / f"{kind}{suffix}"
    return path if path.is_file() else None


def result_report_dest(stem: str, kind: str) -> str:
    """Return the staged iframe path of a multi-page report."""
    return f"{stem}.{kind}/index.html"


def result_report_source(root: Path, stem: str, kind: str) -> Path | None:
    """Return ``kind/index.html`` when that report directory exists."""
    path = root / "scratch" / "results" / stem / kind / "index.html"
    return path if path.is_file() else None


def collect_pages(root: Path) -> list[Page]:
    """Return Markdown report pages; notebooks are pages of their own."""
    from skore_skills.journal_api import render_if_project_has_content

    render_if_project_has_content(root)
    pages: list[Page] = []
    journal = root / "journal" / "JOURNAL.md"
    if journal.is_file():
        pages.append(Page("Home", journal, "index.md"))
    analysis = root / "data_analysis" / "data_analysis.md"
    if analysis.is_file():
        pages.append(
            Page(
                "Exploratory data analysis",
                analysis,
                "data_analysis.md",
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
                    path.name,
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


def render_launcher(title: str) -> str:
    """Return a ``file://``-safe redirect into ``html/index.html``."""
    safe = html.escape(title)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "  <head>\n"
        '    <meta charset="utf-8">\n'
        f"    <title>{safe}</title>\n"
        '    <meta http-equiv="refresh" content="0; url=html/index.html">\n'
        '    <script>location.replace("html/index.html");</script>\n'
        "  </head>\n"
        "  <body>\n"
        f'    <p><a href="html/index.html">Open {safe}</a></p>\n'
        "  </body>\n"
        "</html>\n"
    )


def render_mkdocs_yml(
    pages: list[Page], *, stub_home: bool = False, site_name: str
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
    if stub_home and not any(page.dest_name == "index.md" for page in pages):
        lines.append("  - Home: index.md")
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
    elif not stub_home:
        lines.append("  - Home: index.md")
    lines.append("")
    return "\n".join(lines)


def write_generated_config(root: Path, pages: list[Page], *, stub_home: bool) -> Path:
    """Write ``_build/mkdocs.yml`` for this build."""
    dest = root / GENERATED_CONFIG
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        render_mkdocs_yml(pages, stub_home=stub_home, site_name=site_title(root)),
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


def rewrite_markdown_links(text: str, dest_names: set[str]) -> str:
    """Point Markdown links at files that exist in the flattened docs tree."""

    def replace(match: re.Match[str]) -> str:
        label, url = match.group(1), match.group(2)
        if url.startswith(("#", "http:", "https:", "mailto:")):
            return match.group(0)
        path, sep, rest = url.partition("#")
        if not path:
            return match.group(0)
        path, qsep, query = path.partition("?")
        name = Path(path).name
        if name in dest_names or Path(name).suffix.lower() in ASSET_SUFFIXES:
            return f"[{label}]({name}{qsep}{query}{sep}{rest})"
        return match.group(0)

    return MD_LINK.sub(replace, text)


def render_embed(name: str, title: str, *, autosize: bool = False) -> str:
    """Return an accessible, fullscreen-capable HTML viewer."""
    safe_name = html.escape(name, quote=True)
    safe_title = html.escape(title)
    sizing = " data-skore-autosize" if autosize else ""
    return (
        f'<div class="skore-embed" data-skore-embed>\n'
        f'  <div class="skore-embed__toolbar">\n'
        f'    <span class="skore-embed__title">{safe_title}</span>\n'
        f'    <div class="skore-embed__actions">\n'
        f'      <a class="skore-button" href="{safe_name}" target="_blank" '
        f'rel="noopener">Open separately</a>\n'
        f'      <button class="skore-button" type="button" '
        f'data-skore-fullscreen aria-pressed="false">\n'
        f'        <svg viewBox="0 0 24 24" aria-hidden="true">'
        f'<path d="M7 3H3v4h2V5h2V3zm12 4h2V3h-4v2h2v2zM5 17H3v4h4v-2H5v-2z'
        f'm14 2h-2v2h4v-4h-2v2z"/></svg>\n'
        f'        <span class="skore-button__label">Full screen</span>\n'
        f"      </button>\n"
        f"    </div>\n"
        f"  </div>\n"
        f'  <iframe src="{safe_name}" title="{safe_title}" '
        f'loading="lazy"{sizing}></iframe>\n'
        f"</div>"
    )


def embed_assets(text: str) -> str:
    """Render asset links inline: images as embeds, HTML in viewers."""
    seen = set(RAW_IFRAME.findall(text))
    text = RAW_IFRAME.sub(
        lambda match: render_embed(match.group(1), "Interactive report", autosize=True),
        text,
    )
    embedded: list[str] = []
    for line in text.splitlines():
        embedded.append(IMAGE_LINK.sub(r"![\1](\2)", line))
        for match in LINK.finditer(line):
            name = match.group(2)
            if Path(name).suffix.lower() != ".html" or name in seen:
                continue
            seen.add(name)
            embedded.extend(
                ["", render_embed(name, "Interactive report", autosize=True)]
            )
    return "\n".join(embedded) + "\n"


def inject_notebook(text: str, page: Page) -> str:
    """Insert paired experiment viewers or append one analysis viewer."""
    if page.section == "Experiments":
        viewers: list[str] = []
        for source, heading, name in (
            (page.notebook, "Evaluation notebook", notebook_dest(page)),
            (page.audit, "Audit notebook", audit_dest(page)),
        ):
            if source is None:
                continue
            embed = render_embed(name, f"{page.title} {heading.lower()}")
            viewers.append(f"### {heading}\n\n{embed}")

        section = "## Notebooks\n"
        if viewers:
            section += "\n" + "\n\n".join(viewers) + "\n"

        if NOTEBOOKS_SECTION.search(text):
            return NOTEBOOKS_SECTION.sub(section, text, count=1)
        if not viewers:
            return text
        return f"{text.rstrip()}\n\n{section}"

    for source, heading, name in (
        (page.notebook, "Notebook", notebook_dest(page)),
        (page.audit, "Audit", audit_dest(page)),
    ):
        if source is None or f'src="{name}"' in text:
            continue
        if not text.endswith("\n"):
            text += "\n"
        embed = render_embed(name, f"{page.title} {heading.lower()}")
        text = f"{text}\n## {heading}\n\n{embed}\n"
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


def _result_embed(root: Path, stem: str, slug: str, title: str) -> str | None:
    """Return an HTML or image embed for a scratch snapshot."""
    if result_report_source(root, stem, slug) is not None:
        return render_embed(result_report_dest(stem, slug), title, autosize=True)
    html = result_source(root, stem, slug, ".html")
    if html is not None:
        name = result_dest(stem, slug, ".html")
        return render_embed(name, title, autosize=True)
    for suffix in RESULT_IMAGE_SUFFIXES:
        image = result_source(root, stem, slug, suffix)
        if image is not None:
            name = result_dest(stem, slug, suffix)
            return f"![{title}]({name})"
    return None


def _inject_marked_embeds(section: str, root: Path, stem: str, title: str) -> str:
    """Append scratch snapshots after ``results-embed`` comments in ``section``."""
    for slug in RESULT_EMBED.findall(section):
        if slug in CORE_RESULT_KINDS:
            continue
        embed = _result_embed(root, stem, slug, f"{title} {slug}")
        if embed is None:
            continue
        names = [
            result_report_dest(stem, slug),
            result_dest(stem, slug, ".html"),
            *(result_dest(stem, slug, suffix) for suffix in RESULT_IMAGE_SUFFIXES),
        ]
        if any(f'src="{name}"' in section or f"]({name})" in section for name in names):
            continue
        section = _append_after_embed_marker(section, slug, embed)
    return section


def inject_results(text: str, page: Page, root: Path) -> str:
    """Embed scratch snapshots under Method and Results on experiment pages."""
    if page.section != "Experiments":
        return text
    stem = Path(page.dest_name).stem
    method = METHOD_SECTION.search(text)
    if method is not None:
        section = _inject_marked_embeds(method.group(0), root, stem, page.title)
        text = text[: method.start()] + section + text[method.end() :]
    match = RESULTS_SECTION.search(text)
    if match is None:
        return text
    section = match.group(0)
    for kind, heading in RESULT_ITEMS:
        embed = _result_embed(root, stem, kind, f"{page.title} {heading.lower()}")
        if embed is None:
            continue
        name = (
            result_report_dest(stem, kind)
            if result_report_source(root, stem, kind) is not None
            else result_dest(stem, kind)
        )
        if f'src="{name}"' in section:
            continue
        section = _append_under_heading(section, heading, embed)
    section = _inject_marked_embeds(section, root, stem, page.title)
    return text[: match.start()] + section + text[match.end() :]


def with_height_reporter(text: str) -> str:
    """Return report HTML that posts its content height to the viewer."""
    index = text.lower().rfind("</body>")
    if index == -1:
        return text + HEIGHT_REPORTER
    return text[:index] + HEIGHT_REPORTER + text[index:]


def is_document(text: str) -> bool:
    """Whether ``text`` is a whole HTML document rather than a fragment.

    ``<body>`` is not a marker: ``estimator_html_repr`` emits one in the
    middle of its fragment.
    """
    head = text[:2048].lower()
    return "<!doctype" in head or "<html" in head


def carries_shadow_host(text: str) -> bool:
    """Whether ``text`` already attaches a shadow root of its own.

    skore report and checks reprs ship a ``<template>`` holding their
    styles plus the ``skoreInit`` call that hosts it.
    """
    return "<template id=" in text and "skoreInit" in text


def as_embed_document(text: str) -> str:
    """Return ``text`` as a self-contained document sized for its viewer.

    A fragment that neither hosts its own shadow root nor runs scripts is
    moved into one. The rest stay in the light DOM: skore and sklearn
    resolve their containers through ``document``, which a shadow root
    would hide from them, and scripts cloned out of a ``<template>`` never
    run at all.
    """
    if is_document(text):
        return with_height_reporter(text)
    body = text if text.endswith("\n") else f"{text}\n"
    if not carries_shadow_host(text) and "<script" not in text:
        body = EMBED_SHADOW_HOST.format(
            host=EMBED_HOST_ID,
            template=EMBED_TEMPLATE_ID,
            stylesheet=EMBED_STYLESHEET,
            fragment=body,
        )
    return EMBED_DOCUMENT.format(
        stylesheet=EMBED_STYLESHEET, body=body, reporter=HEIGHT_REPORTER
    )


def _copy_data_analysis_assets(root: Path, docs: Path) -> None:
    analysis = root / "data_analysis"
    if not analysis.is_dir():
        return
    for path in analysis.iterdir():
        if path.name.endswith(".nb.html") or not path.is_file():
            continue
        if path.suffix.lower() == ".html":
            (docs / path.name).write_text(
                as_embed_document(path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )
        elif path.suffix.lower() in ASSET_SUFFIXES:
            shutil.copy2(path, docs / path.name)


def _copy_result_html(root: Path, docs: Path, page: Page) -> None:
    if page.section != "Experiments":
        return
    stem = Path(page.dest_name).stem
    directory = root / "scratch" / "results" / stem
    if not directory.is_dir():
        return
    for path in directory.iterdir():
        if path.is_dir() and (path / "index.html").is_file():
            dest_dir = docs / f"{stem}.{path.name}"
            for item in path.rglob("*"):
                if not item.is_file():
                    continue
                target = dest_dir / item.relative_to(path)
                target.parent.mkdir(parents=True, exist_ok=True)
                if item.suffix.lower() == ".html":
                    target.write_text(
                        as_embed_document(item.read_text(encoding="utf-8")),
                        encoding="utf-8",
                    )
                else:
                    shutil.copy2(item, target)
            continue
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        dest = docs / f"{stem}.{path.stem}{suffix}"
        if suffix == ".html":
            dest.write_text(
                as_embed_document(path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )
        elif suffix in RESULT_IMAGE_SUFFIXES:
            shutil.copy2(path, dest)


def _write_stub_index(docs: Path) -> bool:
    dest = docs / "index.md"
    if dest.is_file():
        return False
    dest.write_text("# Report\n", encoding="utf-8")
    return True


def _copy_notebook(src: Path, dest: Path) -> None:
    shutil.copy2(src, dest)


def _copy_site_assets(docs: Path) -> None:
    shutil.copytree(SITE_ASSETS, docs / STAGED_ASSETS)


def write_nav_data(docs: Path, pages: list[Page], *, stub_home: bool) -> Path:
    """Write top-navigation data as JavaScript that works under ``file://``."""
    items: list[dict[str, object]] = []
    if stub_home and not any(page.dest_name == "index.md" for page in pages):
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
    dest_names = {page.dest_name for page in pages}
    dest_names.add("index.md")
    analysis_exists = (root / "data_analysis" / "data_analysis.md").is_file()
    for page in pages:
        text = page.source.read_text(encoding="utf-8")
        if (
            page.dest_name == "index.md"
            and page.source.name == "JOURNAL.md"
            and not analysis_exists
        ):
            text = DATA_UNDERSTANDING_SECTION.sub("", text, count=1)
        text = rewrite_markdown_links(text, dest_names)
        text = inject_results(inject_notebook(embed_assets(text), page), page, root)
        (docs / page.dest_name).write_text(text, encoding="utf-8")
        if page.notebook is not None:
            _copy_notebook(page.notebook, docs / notebook_dest(page))
        if page.audit is not None:
            _copy_notebook(page.audit, docs / audit_dest(page))
        _copy_result_html(root, docs, page)
    _copy_data_analysis_assets(root, docs)
    _copy_site_assets(docs)
    stub_home = _write_stub_index(docs)
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
        "data_analysis/*.html",
        "data_analysis/*.png",
        "data_analysis/*.jpg",
        "data_analysis/*.jpeg",
        "data_analysis/*.svg",
        "data_analysis/*.gif",
        "experiments/*.nb.html",
        "audit/*.nb.html",
    ):
        paths.extend(path for path in root.glob(pattern) if path.is_file())
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
        and (root / HTML_DIR / "index.html").is_file()
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
        When ``mkdocs`` is missing, the build fails, or ``index.html`` is missing.
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
    index = root / HTML_DIR / "index.html"
    if not index.is_file():
        raise RuntimeError(MISSING_INDEX)
    launcher = root / launcher_name(root)
    launcher.write_text(render_launcher(site_title(root)), encoding="utf-8")
    state = root / BUILD_STATE
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({"fingerprint": fingerprint}) + "\n", encoding="utf-8")
    extra = (completed.stdout or "").strip()
    url = launcher_url(root)
    if extra:
        return f"{extra}\n{url}"
    return url
