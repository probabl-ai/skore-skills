"""Tests for ``skore_skills site init`` and ``site build``."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from skore_skills import site as site_mod
from skore_skills.cli import cli
from skore_skills.policy import empty_policy, save_policy


def _scaffold(tmp_path: Path, *, package: str = "claim_predictor") -> None:
    (tmp_path / "journal").mkdir()
    (tmp_path / "journal" / "JOURNAL.md").write_text(
        "# JOURNAL\n\n[report](../data_analysis/data_analysis.md)\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "{package}"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )


def test_site_title_uses_package_then_folder(tmp_path: Path) -> None:
    """Site title prefers ``[project].name``, then ``src/``, then the folder."""
    (tmp_path / "src").mkdir()
    assert site_mod.site_title(tmp_path) == tmp_path.name
    (tmp_path / "src" / "churnlab").mkdir()
    assert site_mod.site_title(tmp_path) == "churnlab"
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "claim_predictor"\n', encoding="utf-8"
    )
    assert site_mod.site_title(tmp_path) == "claim_predictor"


def _tab_link(href: str, label: str) -> str:
    return f'<a href="{href}" target="_blank" rel="noopener">{label}</a>'


def _ok_mkdocs(tmp_path: Path):
    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    def fake_run(argv: list[str], **kwargs: object) -> Result:
        entry = tmp_path / "html" / site_mod.entry_page(tmp_path)
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text("<html></html>\n", encoding="utf-8")
        return Result()

    return fake_run


def test_site_init_writes_gitignore(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Init ignores build dirs and does not write a user mkdocs.yml."""
    _scaffold(tmp_path)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "init"])
    assert result.exit_code == 0, result.output
    text = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert "_build/" in text
    assert "html/" in text
    assert "report.html" in text
    assert not (tmp_path / "mkdocs.yml").exists()


def test_site_init_force_is_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``--force`` is accepted and does not write root mkdocs.yml."""
    (tmp_path / "src").mkdir()
    (tmp_path / "mkdocs.yml").write_text("hand-written\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "init", "--force"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "mkdocs.yml").read_text(encoding="utf-8") == "hand-written\n"


def test_site_init_refuses_unscaffolded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Empty trees cannot init a site."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "init"])
    assert result.exit_code != 0
    assert "not scaffolded" in result.output


def test_site_build_runs_mkdocs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Build stages docs then invokes mkdocs with the generated config."""
    _scaffold(tmp_path)
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        "# eda\n\nThe score is $R^2$.\n\n$$\\frac{1}{2}$$\n",
        encoding="utf-8",
    )
    (tmp_path / "mkdocs.yml").write_text("hand-written\n", encoding="utf-8")
    seen: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: object) -> object:
        seen.append(list(argv))
        return _ok_mkdocs(tmp_path)(argv)

    monkeypatch.setattr(site_mod.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    assert seen == [
        ["mkdocs", "build", "--config-file", site_mod.GENERATED_CONFIG.as_posix()]
    ]
    assert (tmp_path / "mkdocs.yml").read_text(encoding="utf-8") == "hand-written\n"
    generated = (tmp_path / "_build" / "mkdocs.yml").read_text(encoding="utf-8")
    assert 'site_name: "claim_predictor"' in generated
    assert "  homepage: journal/JOURNAL.html\n" in generated
    assert "Home: journal/JOURNAL.md" in generated
    assert "index.md" not in generated
    assert "font: false" in generated
    assert (
        "markdown_extensions:\n  - pymdownx.arithmatex:\n      generic: true\n"
    ) in generated
    assert (
        "extra_css:\n  - assets/skore/katex/katex.min.css\n  - assets/skore/skore.css\n"
    ) in generated
    assert "assets/skore/skore.js" in generated
    assert "assets/skore/iframe-worker.js" in generated
    assert generated.index("assets/skore/nav-data.js") < generated.index(
        "assets/skore/skore.js"
    )
    assert (
        "  - assets/skore/skore.js\n"
        "  - assets/skore/katex/katex.min.js\n"
        "  - assets/skore/katex/contrib/auto-render.min.js\n"
        "  - assets/skore/katex-render.js\n"
    ) in generated
    assert (tmp_path / "_build" / "docs" / "journal" / "JOURNAL.md").is_file()
    assert not (tmp_path / "_build" / "docs" / "index.md").exists()
    assets = tmp_path / "_build" / "docs" / "assets" / "skore"
    assert (assets / "skore.css").is_file()
    assert (assets / "skore.js").is_file()
    assert (assets / "nav-data.js").is_file()
    assert (assets / "skore-text.svg").is_file()
    assert (assets / "iframe-worker.js").is_file()
    assert (assets / "iframe-worker.LICENSE").is_file()
    assert (assets / "fonts" / "GeistVF.woff2").is_file()
    assert (assets / "katex-render.js").is_file()
    assert (assets / "katex" / "katex.min.js").is_file()
    assert (assets / "katex" / "katex.min.css").is_file()
    assert (assets / "katex" / "LICENSE").is_file()
    assert (assets / "katex" / "contrib" / "auto-render.min.js").is_file()
    assert any((assets / "katex" / "fonts").glob("*.woff2"))
    icons = assets / "icons"
    assert (icons / "square-caret-left-regular.svg").is_file()
    assert (icons / "square-caret-right-regular.svg").is_file()
    assert (icons / "FONT-AWESOME-NOTICE.txt").is_file()
    journal = (tmp_path / "_build" / "docs" / "journal" / "JOURNAL.md").read_text(
        encoding="utf-8"
    )
    assert "](../data_analysis/data_analysis.md)" in journal
    analysis = (
        tmp_path / "_build" / "docs" / "data_analysis" / "data_analysis.md"
    ).read_text(encoding="utf-8")
    assert "$R^2$" in analysis
    assert "$$\\frac{1}{2}$$" in analysis
    assert (tmp_path / "html" / "journal" / "JOURNAL.html").is_file()
    launcher = tmp_path / "report.html"
    assert launcher.is_file()
    assert "url=html/journal/JOURNAL.html" in launcher.read_text(encoding="utf-8")
    assert site_mod.launcher_url(tmp_path) in result.output
    assert site_mod.launcher_url(tmp_path).startswith("file://")
    assert "report.html" in (tmp_path / ".gitignore").read_text(encoding="utf-8")


def test_site_build_if_stale_skips_until_an_input_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Checkpoint builds are cheap when their staged inputs are unchanged."""
    _scaffold(tmp_path)
    calls = 0

    def fake_run(argv: list[str], **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        return _ok_mkdocs(tmp_path)(argv)

    monkeypatch.setattr(site_mod.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)
    first = CliRunner().invoke(cli, ["site", "build", "--if-stale"])
    second = CliRunner().invoke(cli, ["site", "build", "--if-stale"])
    assert first.exit_code == 0, first.output
    assert second.exit_code == 0, second.output
    assert f"site is current: {site_mod.launcher_url(tmp_path)}" in second.output
    assert calls == 1

    asset = tmp_path / "scratch" / "results" / "01_baseline" / "pipeline" / "app.css"
    asset.parent.mkdir(parents=True)
    asset.write_text("body {}\n", encoding="utf-8")
    asset_refresh = CliRunner().invoke(cli, ["site", "build", "--if-stale"])
    assert asset_refresh.exit_code == 0, asset_refresh.output
    assert calls == 2

    journal = tmp_path / "journal" / "JOURNAL.md"
    journal.write_text("# JOURNAL\n\nChanged\n", encoding="utf-8")
    refreshed = CliRunner().invoke(cli, ["site", "build", "--if-stale"])
    assert refreshed.exit_code == 0, refreshed.output
    assert calls == 3


def test_site_build_if_stale_rebuilds_when_state_is_corrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A broken freshness record does not skip the build."""
    _scaffold(tmp_path)
    calls = 0

    def fake_run(argv: list[str], **kwargs: object) -> object:
        nonlocal calls
        calls += 1
        return _ok_mkdocs(tmp_path)(argv)

    monkeypatch.setattr(site_mod.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)
    first = CliRunner().invoke(cli, ["site", "build", "--if-stale"])
    assert first.exit_code == 0, first.output
    state = tmp_path / "_build" / "site-state.json"
    state.write_text("{", encoding="utf-8")
    again = CliRunner().invoke(cli, ["site", "build", "--if-stale"])
    assert again.exit_code == 0, again.output
    assert "site is current" not in again.output
    assert calls == 2


def test_site_build_omits_data_understanding_without_eda(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing analysis report drops Data understanding from the home page."""
    _scaffold(tmp_path)
    journal = (
        "# JOURNAL\n\n"
        "## Status\n\n"
        "| Variable | Value |\n"
        "|---|---|\n"
        "| Goal | predict |\n\n"
        "## Data understanding\n\n"
        "| Variable | Value |\n"
        "|---|---|\n"
        "| Status | skipped — 2026-09-24 |\n"
        "| Report | [data_analysis/data_analysis.md]"
        "(../data_analysis/data_analysis.md) |\n\n"
        "## History\n\n"
        "| Stem | Intent |\n"
        "|---|---|\n"
    )
    source = tmp_path / "journal" / "JOURNAL.md"
    source.write_text(journal, encoding="utf-8")
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    staged = (tmp_path / "_build" / "docs" / "journal" / "JOURNAL.md").read_text(
        encoding="utf-8"
    )
    assert "## Data understanding" not in staged
    assert "data_analysis.md" not in staged
    assert "## History" in staged
    assert "## Status" in staged
    assert source.read_text(encoding="utf-8") == journal


def test_site_build_groups_experiments_and_writes_top_nav(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Experiments form one ordered dropdown in desktop and mobile nav."""
    _scaffold(tmp_path)
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        "# eda\n", encoding="utf-8"
    )
    for name in ("01_baseline.md", "02_tuning.md"):
        (tmp_path / "journal" / name).write_text(f"# {name}\n", encoding="utf-8")
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    generated = (tmp_path / "_build" / "mkdocs.yml").read_text(encoding="utf-8")
    assert (
        "  - Experiments:\n"
        "      - 01_baseline: journal/01_baseline.md\n"
        "      - 02_tuning: journal/02_tuning.md\n"
    ) in generated
    script = (
        tmp_path / "_build" / "docs" / "assets" / "skore" / "nav-data.js"
    ).read_text(encoding="utf-8")
    payload = script.removeprefix("window.__SKORE_NAV__ = ").removesuffix(";\n")
    assert json.loads(payload) == [
        {"label": "Home", "href": "journal/JOURNAL.html"},
        {
            "label": "Exploratory data analysis",
            "href": "data_analysis/data_analysis.html",
        },
        {
            "label": "Experiments",
            "children": [
                {"label": "01_baseline", "href": "journal/01_baseline.html"},
                {"label": "02_tuning", "href": "journal/02_tuning.html"},
            ],
        },
    ]


def test_site_theme_has_trainhard_layout_contract() -> None:
    """Packaged CSS and JS keep the desktop shell accessibility contract."""
    css = (site_mod.SITE_ASSETS / "skore.css").read_text(encoding="utf-8")
    javascript = (site_mod.SITE_ASSETS / "skore.js").read_text(encoding="utf-8")
    assert "--skore-content-max: 1200px" in css
    assert "--skore-toc-width: 256px" in css
    assert "--skore-toc-rail-width: var(--numbers-48)" in css
    assert "font-size: 18px" in css
    assert (".md-typeset table:not([class]) {\n  font-size: inherit;\n") in css
    assert "max-height: calc(5 * var(--numbers-40))" in css
    assert "grid-template-columns: var(--skore-toc-width)" in css
    assert ".md-sidebar--secondary .md-nav__title {\n    display: none;" in css
    assert 'trigger.setAttribute("aria-haspopup", "menu")' in javascript
    assert 'button.setAttribute("aria-controls", sidebar.id)' in javascript
    assert 'document.createElement("img")' in javascript
    assert "button.append(icon, label)" in javascript
    assert "square-caret-left-regular.svg" in javascript
    assert "square-caret-right-regular.svg" in javascript
    assert 'event.key !== "Escape"' in javascript
    assert 'script[src$="assets/skore/skore.js"]' in javascript
    assert "const siteUrl = (path) => new URL(path, siteRoot).href;" in javascript
    assert "link.href = siteUrl(item.href)" in javascript
    assert 'siteUrl("assets/skore/icons/square-caret-right-regular.svg")' in javascript


def test_site_assets_do_not_script_the_embedded_frames() -> None:
    """Frames are sized by CSS alone: no height messages, no fullscreen."""
    css = (site_mod.SITE_ASSETS / "skore.css").read_text(encoding="utf-8")
    javascript = (site_mod.SITE_ASSETS / "skore.js").read_text(encoding="utf-8")
    assert "height: min(72vh, 52rem)" in css
    assert ".skore-inline table.dataframe" in css
    for name in ("message", "postMessage", "fullscreen", "iframe"):
        assert name not in javascript


def test_site_theme_uses_hub_sizing_scale() -> None:
    """Chrome sizing comes from the skore-hub ``--numbers-*`` scale."""
    css = (site_mod.SITE_ASSETS / "skore.css").read_text(encoding="utf-8")
    for token, value in (
        ("--numbers-4", "0.25rem"),
        ("--numbers-8", "0.5rem"),
        ("--numbers-12", "0.75rem"),
        ("--numbers-14", "0.875rem"),
        ("--numbers-40", "2.5rem"),
        ("--numbers-48", "3rem"),
        ("--numbers-56", "3.5rem"),
    ):
        assert f"{token}: {value};" in css
    assert "--stroke-width-md: 1px" in css
    assert "height: var(--numbers-40)" in css
    assert "border-radius: var(--numbers-8)" in css
    assert "border-radius: var(--numbers-12)" in css


def test_site_theme_flattens_and_numbers_contents() -> None:
    """Contents rows sit flush and use hierarchical numbered tiles."""
    css = (site_mod.SITE_ASSETS / "skore.css").read_text(encoding="utf-8")
    javascript = (site_mod.SITE_ASSETS / "skore.js").read_text(encoding="utf-8")
    assert "[dir] .md-sidebar--secondary .md-nav__list" in css
    assert "[dir] .md-sidebar--secondary .md-nav__item > .md-nav__link" in css
    assert "counter-reset: skore-toc" in css
    assert "counter-increment: skore-toc" in css
    # Panel padding belongs to the root nav; applying it to nested navs adds
    # extra vertical space around subsection rows.
    assert ".md-sidebar--secondary .md-sidebar__inner > .md-nav {" in css
    assert "\n  .md-sidebar--secondary .md-nav {\n" not in css
    assert ".md-nav__item > .md-nav {\n    margin: 0;" in css
    # A fixed-width, left-aligned column lines up single- and multi-level numbers.
    assert (
        ".md-sidebar--secondary .md-nav__link::before {\n"
        "    flex: 0 0 var(--numbers-24);\n"
        '    content: counters(skore-toc, ".");\n'
        "    text-align: left;\n"
        "    font-variant-numeric: tabular-nums;"
    ) in css
    assert "flex: 0 0 var(--numbers-20);\n  opacity: 0.8;" in css
    assert "body.skore-toc-collapsed .skore-toc-label {\n    display: none;" in css
    assert "width: var(--numbers-40)" in css
    # Rows, tiles, and the collapse control all keep the compact row height.
    assert "min-height: var(--numbers-28)" in css
    assert "height: var(--numbers-28)" in css
    assert "heading-solid" not in css
    # The panel hugs its rows so the collapse control follows the last one.
    assert "flex: 0 1 auto" in css
    assert (
        "body.skore-toc-collapsed .md-sidebar--secondary .md-nav__item {\n"
        "    display: flex;\n"
        "    flex-direction: column;\n"
        "    align-items: center;"
    ) in css
    assert (
        "body.skore-toc-collapsed .md-sidebar--secondary .md-nav__link::before {\n"
        "    flex: 0 0 auto;\n"
        "    text-align: center;"
    ) in css
    assert (
        "body.skore-toc-collapsed .skore-toc-footer {\n    padding: var(--numbers-6) 0;"
        in css
    )
    assert 'label.className = "skore-toc-label"' in javascript
    assert "link.title = label.textContent" in javascript


def test_site_theme_uses_trainhard_motion() -> None:
    """Transitions reuse trainhard timings and stay off until first paint."""
    css = (site_mod.SITE_ASSETS / "skore.css").read_text(encoding="utf-8")
    javascript = (site_mod.SITE_ASSETS / "skore.js").read_text(encoding="utf-8")
    assert "--skore-collapse-duration: 0.2s" in css
    assert "--skore-collapse-easing: ease-in-out" in css
    assert "--skore-hover-duration: 0.12s" in css
    assert "--skore-menu-duration: 0.15s" in css
    assert "transition: grid-template-columns var(--skore-collapse-duration)" in css
    assert "transform: translateY(-0.35rem)" in css
    assert "transform: rotate(180deg)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert "display: none" not in css.split(".skore-topnav__menu {")[1].split("}")[0]
    assert 'classList.add("skore-motion-ready")' in javascript
    assert 'caret.className = "skore-topnav__caret"' in javascript


def test_site_build_mkdocs_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A missing mkdocs executable is a clear error."""
    _scaffold(tmp_path)

    def fake_run(*args: object, **kwargs: object) -> object:
        raise FileNotFoundError("mkdocs")

    monkeypatch.setattr(site_mod.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code != 0
    assert "mkdocs-material" in result.output


def test_site_build_nonzero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-zero mkdocs build is reported."""
    (tmp_path / "src").mkdir()

    class Result:
        returncode = 1
        stdout = ""
        stderr = "nav error\n"

    monkeypatch.setattr(site_mod.subprocess, "run", lambda *args, **kwargs: Result())
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code != 0
    assert "nav error" in result.output


def test_site_build_copies_data_analysis_html(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TableReport HTML next to data_analysis.md is copied into the staged docs."""
    (tmp_path / "src").mkdir()
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        "# report\n", encoding="utf-8"
    )
    (tmp_path / "data_analysis" / "data_analysis_adult.html").write_text(
        "<html><body>report</body></html>\n", encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    staged = (
        tmp_path / "_build" / "docs" / "data_analysis" / "data_analysis_adult.html"
    ).read_text(encoding="utf-8")
    assert staged == "<html><body>report</body></html>\n"


def test_as_embed_document_wraps_a_bare_fragment() -> None:
    """A pandas table carries no styles, so give it a charset and the baseline."""
    staged = site_mod.as_embed_document(
        '<table class="dataframe"><tr><th>R²</th></tr></table>'
    )
    assert staged.startswith("<!DOCTYPE html>")
    assert '<meta charset="utf-8">' in staged
    assert 'href="assets/skore/embed.css"' in staged
    assert '<table class="dataframe">' in staged
    assert "<script" not in staged
    assert "<template" not in staged


def test_as_embed_document_keeps_a_scripted_fragment_verbatim() -> None:
    """``estimator_html_repr`` resolves its container through ``document``."""
    fragment = (
        "<style>.sk-global {}</style><body>"
        '<div id="sk-container-id-1">tree</div>'
        "<script>forceTheme('sk-container-id-1');</script>\n"
    )
    staged = site_mod.as_embed_document(fragment)
    assert staged.count("<!DOCTYPE html>") == 1
    assert fragment in staged
    assert "attachShadow" not in staged


def test_as_embed_document_leaves_a_whole_document_alone() -> None:
    """skrub ``write_html`` output already is a document."""
    document = "<!doctype html>\n<html><body>report</body></html>\n"
    assert site_mod.as_embed_document(document) == document


def test_site_build_inlines_checks_and_metrics_fragments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Checks and metrics are pasted into the page, not staged as files."""
    _scaffold(tmp_path)
    (tmp_path / "journal" / "01_x.md").write_text(
        "# design\n\n## Results\n\n### Checks\n\nOne issue.\n\n"
        "### Metrics\n\nMAE 3421.\n\n## Notebooks\n",
        encoding="utf-8",
    )
    results = tmp_path / "scratch" / "results" / "01_x"
    results.mkdir(parents=True)
    (results / "checks.html").write_text(
        '<div id="checks-1">\n\n<p>R² check</p>\n</div>\n', encoding="utf-8"
    )
    (results / "metrics.html").write_text(
        '<table class="dataframe"><tr><th>R²</th></tr></table>\n', encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    staged = (docs / "journal" / "01_x.md").read_text(encoding="utf-8")
    assert '<div id="checks-1">\n\n<p>R² check</p>\n</div>' in staged
    assert '<table class="dataframe"><tr><th>R²</th></tr></table>' in staged
    assert staged.index("One issue.") < staged.index('<div id="checks-1">')
    assert staged.index("MAE 3421.") < staged.index("<table")
    assert "<iframe" not in staged
    assert not (docs / "scratch" / "results" / "01_x" / "checks.html").exists()
    assert not (docs / "scratch" / "results" / "01_x" / "metrics.html").exists()


def test_site_build_wraps_fragment_data_analysis_html(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Plot HTML next to ``data_analysis.md`` goes through the same shell."""
    (tmp_path / "src").mkdir()
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        "# report\n", encoding="utf-8"
    )
    (tmp_path / "data_analysis" / "target_distribution.html").write_text(
        '<div class="plotly-graph-div"></div>', encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    staged = (
        tmp_path / "_build" / "docs" / "data_analysis" / "target_distribution.html"
    ).read_text(encoding="utf-8")
    assert staged.startswith("<!DOCTYPE html>")
    assert '<meta charset="utf-8">' in staged
    assert 'href="../assets/skore/embed.css"' in staged


def test_site_build_links_notebook_and_sizes_report_with_css(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """HTML reports sit in plain iframes; the notebook is a link."""
    _scaffold(tmp_path)
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        '<iframe src="data_analysis_adult.html" width="100%" height="640"></iframe>\n',
        encoding="utf-8",
    )
    (tmp_path / "data_analysis" / "data_analysis_adult.html").write_text(
        "<html><body>report</body></html>\n", encoding="utf-8"
    )
    (tmp_path / "data_analysis" / "data_analysis.nb.html").write_text(
        "<html><body>notebook</body></html>\n", encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    staged = (docs / "data_analysis" / "data_analysis.md").read_text(encoding="utf-8")
    assert (
        '<iframe src="data_analysis_adult.html" title="Interactive report" '
        'loading="lazy"></iframe>' in staged
    )
    assert _tab_link("data_analysis.nb.html", "Open the notebook") in staged
    assert '<iframe src="data_analysis.nb.html"' not in staged
    assert "data-skore" not in staged
    assert (docs / "data_analysis" / "data_analysis.nb.html").read_text(
        encoding="utf-8"
    ) == ("<html><body>notebook</body></html>\n")


def test_site_build_missing_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A successful mkdocs process without index.html is still an error."""
    (tmp_path / "journal").mkdir()

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr(site_mod.subprocess, "run", lambda *args, **kwargs: Result())
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code != 0
    assert "index.html" in result.output
    assert not (tmp_path / f"{tmp_path.name}.html").exists()


def test_site_build_does_not_convert(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Site build never executes paired scripts, even if notebooks are on."""
    _scaffold(tmp_path)
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        "# eda\n", encoding="utf-8"
    )
    (tmp_path / "data_analysis" / "data_analysis.py").write_text(
        "# %%\n1\n", encoding="utf-8"
    )
    policy = empty_policy()
    policy["notebooks"] = True
    save_policy(tmp_path, policy)
    called: list[str] = []

    def fake_convert(*args: object, **kwargs: object) -> Path:
        called.append("convert")
        raise AssertionError("site build must not convert")

    monkeypatch.setattr(site_mod, "convert", fake_convert, raising=False)
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    assert called == []
    staged = (
        tmp_path / "_build" / "docs" / "data_analysis" / "data_analysis.md"
    ).read_text(encoding="utf-8")
    assert "## Notebook" not in staged
    assert not (tmp_path / "_build" / "docs" / "data_analysis.py").exists()
    assert not (
        tmp_path / "_build" / "docs" / "data_analysis" / "data_analysis.nb.html"
    ).exists()


def test_site_build_embeds_notebook_in_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """data_analysis.nb.html is linked from data_analysis.md, not a nav page."""
    _scaffold(tmp_path)
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        "# report\n", encoding="utf-8"
    )
    (tmp_path / "data_analysis" / "data_analysis.nb.html").write_text(
        "<html>notebook</html>\n", encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    assert (docs / "data_analysis" / "data_analysis.nb.html").read_text(
        encoding="utf-8"
    ) == ("<html>notebook</html>\n")
    staged = (docs / "data_analysis" / "data_analysis.md").read_text(encoding="utf-8")
    assert "## Notebook" in staged
    assert _tab_link("data_analysis.nb.html", "Open the notebook") in staged
    assert "<iframe" not in staged
    nav = (tmp_path / "_build" / "mkdocs.yml").read_text(encoding="utf-8")
    assert "Exploratory data analysis notebook" not in nav


def test_site_build_pairs_experiment_notebook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """journal/NN.md links experiments/NN.nb.html when it exists."""
    _scaffold(tmp_path)
    (tmp_path / "journal" / "01_x.md").write_text("# design\n", encoding="utf-8")
    (tmp_path / "experiments").mkdir()
    (tmp_path / "experiments" / "01_x.nb.html").write_text(
        "<html>run</html>\n", encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    assert (docs / "experiments" / "01_x.nb.html").is_file()
    staged = (docs / "journal" / "01_x.md").read_text(encoding="utf-8")
    assert staged.count("## Notebooks") == 1
    assert (
        "- " + _tab_link("../experiments/01_x.nb.html", "Evaluation notebook")
    ) in staged
    assert "Audit notebook" not in staged
    assert "<iframe" not in staged
    nav = (tmp_path / "_build" / "mkdocs.yml").read_text(encoding="utf-8")
    assert "01_x notebook" not in nav


def test_site_build_appends_audit_after_experiment_notebook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """audit/NN.nb.html continues the experiment notebook on the same page."""
    _scaffold(tmp_path)
    (tmp_path / "journal" / "01_x.md").write_text("# design\n", encoding="utf-8")
    (tmp_path / "experiments").mkdir()
    (tmp_path / "experiments" / "01_x.nb.html").write_text(
        "<html>run</html>\n", encoding="utf-8"
    )
    (tmp_path / "audit").mkdir()
    (tmp_path / "audit" / "01_x.nb.html").write_text(
        "<html>audit</html>\n", encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    assert (docs / "audit" / "01_x.nb.html").read_text(encoding="utf-8") == (
        "<html>audit</html>\n"
    )
    staged = (docs / "journal" / "01_x.md").read_text(encoding="utf-8")
    assert staged.count("## Notebooks") == 1
    assert staged.index('href="../experiments/01_x.nb.html"') < staged.index(
        'href="../audit/01_x.nb.html"'
    )
    assert staged.index("Evaluation notebook") < staged.index("Audit notebook")
    nav = (tmp_path / "_build" / "mkdocs.yml").read_text(encoding="utf-8")
    assert "01_x audit" not in nav


def test_site_build_without_audit_has_no_audit_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No ``audit/NN.nb.html`` leaves the experiment page unchanged."""
    _scaffold(tmp_path)
    (tmp_path / "journal" / "01_x.md").write_text("# design\n", encoding="utf-8")
    (tmp_path / "experiments").mkdir()
    (tmp_path / "experiments" / "01_x.nb.html").write_text(
        "<html>run</html>\n", encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    assert not (docs / "audit" / "01_x.nb.html").exists()
    staged = (docs / "journal" / "01_x.md").read_text(encoding="utf-8")
    assert "Audit notebook" not in staged


def test_site_build_audit_without_experiment_notebook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An audit notebook is linked even when the experiment has none."""
    _scaffold(tmp_path)
    (tmp_path / "journal" / "01_x.md").write_text("# design\n", encoding="utf-8")
    (tmp_path / "audit").mkdir()
    (tmp_path / "audit" / "01_x.nb.html").write_text(
        "<html>audit</html>\n", encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    staged = (docs / "journal" / "01_x.md").read_text(encoding="utf-8")
    assert "- " + _tab_link("../audit/01_x.nb.html", "Audit notebook") in staged
    assert staged.count("## Notebooks") == 1
    assert "Evaluation notebook" not in staged


def test_inject_notebooks_reuses_authored_section_and_is_idempotent(
    tmp_path: Path,
) -> None:
    """Authored notebook placeholders become one generated link section."""
    experiment = tmp_path / "experiments" / "01_x.nb.html"
    audit = tmp_path / "audit" / "01_x.nb.html"
    page = site_mod.Page(
        "01_x",
        tmp_path / "01_x.md",
        "journal/01_x.md",
        experiment,
        "Experiments",
        audit,
    )
    source = (
        "# design\n\n## Notebooks\n\n### Evaluation notebook\n\n### Audit notebook\n"
    )

    once = site_mod.inject_notebook(source, page, tmp_path)
    twice = site_mod.inject_notebook(once, page, tmp_path)

    assert twice == once
    assert once.count("## Notebooks") == 1
    assert (
        once.count(_tab_link("../experiments/01_x.nb.html", "Evaluation notebook")) == 1
    )
    assert once.count(_tab_link("../audit/01_x.nb.html", "Audit notebook")) == 1
    assert once.index("Evaluation notebook") < once.index("Audit notebook")


def test_inject_results_appends_fragments_after_prose_and_is_idempotent(
    tmp_path: Path,
) -> None:
    """Authored Results prose is kept; fragments are inserted once."""
    stem = "01_x"
    results = tmp_path / "scratch" / "results" / stem
    results.mkdir(parents=True)
    (results / "report.html").write_text("<html>report</html>\n", encoding="utf-8")
    (results / "checks.html").write_text("<div>checks</div>\n", encoding="utf-8")
    (results / "metrics.html").write_text("<div>metrics</div>\n", encoding="utf-8")
    page = site_mod.Page(
        stem,
        tmp_path / f"{stem}.md",
        f"journal/{stem}.md",
        None,
        "Experiments",
        None,
    )
    source = (
        "# design\n\n## Results\n\n"
        "### Report overview\n\nThe CV report for Ridge.\n\n"
        "### Checks\n\nOne issue (SKD003).\n\n"
        "### Metrics\n\nMAE 3421.\n\n"
        "## Notebooks\n"
    )

    once = site_mod.inject_results(source, page, tmp_path)
    twice = site_mod.inject_results(once, page, tmp_path)

    assert twice == once
    assert "The CV report for Ridge." in once
    assert "report.html" not in once
    assert once.index("One issue (SKD003).") < once.index("<div>checks</div>")
    assert once.index("<div>checks</div>") < once.index("### Metrics")
    assert once.index("MAE 3421.") < once.index("<div>metrics</div>")
    assert once.count("<div>checks</div>") == 1
    assert "<iframe" not in once


def test_inject_results_skips_missing_section_and_missing_html(
    tmp_path: Path,
) -> None:
    """No Results heading stays unchanged; missing HTML leaves prose."""
    page = site_mod.Page(
        "01_x",
        tmp_path / "01_x.md",
        "journal/01_x.md",
        None,
        "Experiments",
        None,
    )
    no_section = "# design\n\n## Notebooks\n"
    assert site_mod.inject_results(no_section, page, tmp_path) == no_section

    (tmp_path / "scratch" / "results" / "01_x").mkdir(parents=True)
    (tmp_path / "scratch" / "results" / "01_x" / "metrics.html").write_text(
        "<div>metrics</div>\n", encoding="utf-8"
    )
    source = (
        "# design\n\n## Results\n\n"
        "### Checks\n\nOne issue.\n\n"
        "### Metrics\n\nMAE 3421.\n\n"
        "## Notebooks\n"
    )
    injected = site_mod.inject_results(source, page, tmp_path)
    assert "<div>metrics</div>" in injected
    assert injected.count("<div>") == 1
    assert "One issue." in injected


def test_inject_results_shows_pipeline_graph_under_method(tmp_path: Path) -> None:
    """Method ``results-embed: pipeline`` shows the graph image, no report link."""
    stem = "01_x"
    results = tmp_path / "scratch" / "results" / stem
    results.mkdir(parents=True)
    (results / "pipeline.svg").write_bytes(b"<svg/>")
    page = site_mod.Page(
        stem,
        tmp_path / f"{stem}.md",
        f"journal/{stem}.md",
        None,
        "Experiments",
        None,
    )
    source = (
        "# design\n\n## Method\n\n"
        "Ridge on the skrub graph.\n"
        "<!-- results-embed: pipeline -->\n\n"
        "## Risks\n\nLeakage.\n"
    )
    once = site_mod.inject_results(source, page, tmp_path)
    twice = site_mod.inject_results(once, page, tmp_path)
    assert twice == once
    assert "Ridge on the skrub graph." in once
    assert once.index("Ridge on the skrub graph.") < once.index("pipeline.svg")
    assert once.count("![01_x pipeline](../scratch/results/01_x/pipeline.svg)") == 1
    assert "Open the full" not in once
    assert "<iframe" not in once
    assert "## Risks" in once


def test_inject_results_shows_pipeline_graph_and_links_report_directory(
    tmp_path: Path,
) -> None:
    """The graph is an image; the DataOp report is a link to its own pages."""
    stem = "01_x"
    results = tmp_path / "scratch" / "results" / stem
    report = results / "pipeline"
    report.mkdir(parents=True)
    (report / "index.html").write_text(
        '<!DOCTYPE html><html><body><a href="node_0.html">step</a></body></html>\n',
        encoding="utf-8",
    )
    (report / "node_0.html").write_text(
        '<!DOCTYPE html><html><body><a href="index.html">top</a></body></html>\n',
        encoding="utf-8",
    )
    (report / "assets").mkdir()
    (report / "assets" / "mark.svg").write_bytes(b"<svg/>")
    (results / "pipeline.svg").write_bytes(b"<svg/>")
    page = site_mod.Page(
        stem,
        tmp_path / f"{stem}.md",
        f"journal/{stem}.md",
        None,
        "Experiments",
        None,
    )
    source = (
        "# design\n\n## Method\n\n"
        "Ridge on the skrub graph.\n"
        "<!-- results-embed: pipeline -->\n\n"
        "## Risks\n\nLeakage.\n"
    )
    once = site_mod.inject_results(source, page, tmp_path)
    twice = site_mod.inject_results(once, page, tmp_path)
    assert twice == once
    assert "![01_x pipeline](../scratch/results/01_x/pipeline.svg)" in once
    assert "[![" not in once
    assert (
        '<a href="../scratch/results/01_x/pipeline/index.html" target="_blank" '
        'rel="noopener">Open the full pipeline report</a>'
    ) in once
    assert once.index("pipeline.svg") < once.index("pipeline/index.html")
    assert "<iframe" not in once
    docs = tmp_path / "docs"
    docs.mkdir()
    site_mod._copy_result_html(tmp_path, docs, page)
    staged = docs / "scratch" / "results" / "01_x"
    index = (staged / "pipeline" / "index.html").read_text(encoding="utf-8")
    node = (staged / "pipeline" / "node_0.html").read_text(encoding="utf-8")
    assert 'href="node_0.html"' in index
    assert 'href="index.html"' in node
    assert "<script" not in index
    assert (staged / "pipeline" / "assets" / "mark.svg").read_bytes() == b"<svg/>"
    assert (staged / "pipeline.svg").read_bytes() == b"<svg/>"


def test_inject_results_skips_method_without_pipeline_marker(
    tmp_path: Path,
) -> None:
    """A pipeline.svg file is not injected into Method without the marker."""
    stem = "01_x"
    results = tmp_path / "scratch" / "results" / stem
    results.mkdir(parents=True)
    (results / "pipeline.svg").write_bytes(b"<svg/>")
    page = site_mod.Page(
        stem,
        tmp_path / f"{stem}.md",
        f"journal/{stem}.md",
        None,
        "Experiments",
        None,
    )
    source = "# design\n\n## Method\n\nRidge.\n\n## Risks\n\nLeakage.\n"
    assert site_mod.inject_results(source, page, tmp_path) == source


def test_inject_results_embeds_extra_slug_from_comment(
    tmp_path: Path,
) -> None:
    """Extra Display HTML lands after the results-embed marker."""
    stem = "01_x"
    results = tmp_path / "scratch" / "results" / stem
    results.mkdir(parents=True)
    (results / "roc.html").write_text("<html>roc</html>\n", encoding="utf-8")
    page = site_mod.Page(
        stem,
        tmp_path / f"{stem}.md",
        f"journal/{stem}.md",
        None,
        "Experiments",
        None,
    )
    source = (
        "# design\n\n## Results\n\n"
        "### Report overview\n\nThe CV report.\n\n"
        "### ROC curve\n<!-- results-embed: roc -->\n\n"
        "Fold 3 is weak.\n\n"
        "## Notebooks\n"
    )
    once = site_mod.inject_results(source, page, tmp_path)
    twice = site_mod.inject_results(once, page, tmp_path)
    assert twice == once
    assert "Fold 3 is weak." in once
    frame = '<iframe src="../scratch/results/01_x/roc.html"'
    assert once.index("Fold 3 is weak.") < once.index(frame)
    assert once.count(frame) == 1
    assert "data-skore" not in once


def test_inject_results_embeds_extra_slug_png(
    tmp_path: Path,
) -> None:
    """A matplotlib-style Display snapshot becomes a markdown image."""
    stem = "01_x"
    results = tmp_path / "scratch" / "results" / stem
    results.mkdir(parents=True)
    (results / "prediction_error.png").write_bytes(b"png")
    page = site_mod.Page(
        stem,
        tmp_path / f"{stem}.md",
        f"journal/{stem}.md",
        None,
        "Experiments",
        None,
    )
    source = (
        "# design\n\n## Results\n\n"
        "### Prediction error\n<!-- results-embed: prediction_error -->\n\n"
        "Residuals fan out.\n\n"
        "## Notebooks\n"
    )
    injected = site_mod.inject_results(source, page, tmp_path)
    assert (
        "![01_x prediction_error](../scratch/results/01_x/prediction_error.png)"
    ) in injected
    assert "[![" not in injected
    assert injected.index("Residuals fan out.") < injected.index("prediction_error.png")


def test_inject_results_copies_unmarked_slug_without_injecting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Scratch HTML without a results-embed comment is not injected."""
    _scaffold(tmp_path)
    (tmp_path / "journal" / "01_x.md").write_text(
        "# design\n\n## Results\n\n### Checks\n\nNo issues.\n\n## Notebooks\n",
        encoding="utf-8",
    )
    results = tmp_path / "scratch" / "results" / "01_x"
    results.mkdir(parents=True)
    (results / "checks.html").write_text("<div>checks</div>\n", encoding="utf-8")
    (results / "roc.html").write_text("<html>roc</html>\n", encoding="utf-8")
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    staged = (docs / "journal" / "01_x.md").read_text(encoding="utf-8")
    assert "<div>checks</div>" in staged
    assert '<iframe src="01_x.roc.html"' not in staged
    assert (docs / "scratch" / "results" / "01_x" / "roc.html").is_file()


def test_site_build_does_not_publish_the_skore_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The report widget is redundant with checks and metrics: no page, no file."""
    _scaffold(tmp_path)
    (tmp_path / "journal" / "01_x.md").write_text(
        "# design\n\n## Results\n\n"
        "### Report overview\n\nRidge CV report.\n\n"
        "## Notebooks\n",
        encoding="utf-8",
    )
    results = tmp_path / "scratch" / "results" / "01_x"
    results.mkdir(parents=True)
    (results / "report.html").write_text("<html>report</html>\n", encoding="utf-8")
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    staged = (docs / "journal" / "01_x.md").read_text(encoding="utf-8")
    assert "Ridge CV report." in staged
    assert "<iframe" not in staged
    assert "### Checks" not in staged
    assert "### Metrics" not in staged
    assert not (docs / "scratch" / "results" / "01_x" / "report.html").exists()


def test_site_build_embeds_audit_results_in_order(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Checks then metrics follow the report overview prose."""
    _scaffold(tmp_path)
    (tmp_path / "journal" / "01_x.md").write_text(
        "# design\n\n## Results\n\n"
        "### Report overview\n\nRidge CV report.\n\n"
        "### Checks\n\nOne issue (SKD003).\n\n"
        "### Metrics\n\nMAE 3421.\n\n"
        "## Notebooks\n",
        encoding="utf-8",
    )
    results = tmp_path / "scratch" / "results" / "01_x"
    results.mkdir(parents=True)
    (results / "checks.html").write_text("<div>checks</div>\n", encoding="utf-8")
    (results / "metrics.html").write_text("<div>metrics</div>\n", encoding="utf-8")
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    staged = (tmp_path / "_build" / "docs" / "journal" / "01_x.md").read_text(
        encoding="utf-8"
    )
    assert staged.index("### Report overview") < staged.index("### Checks")
    assert staged.index("### Checks") < staged.index("### Metrics")
    assert staged.index("One issue (SKD003).") < staged.index("<div>checks</div>")
    assert staged.index("<div>checks</div>") < staged.index("### Metrics")
    assert staged.index("MAE 3421.") < staged.index("<div>metrics</div>")


def test_site_build_without_results_section_skips_scratch_html(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Template notes without Results do not gain a Results heading."""
    _scaffold(tmp_path)
    (tmp_path / "journal" / "01_x.md").write_text(
        "# design\n\n## Notebooks\n", encoding="utf-8"
    )
    results = tmp_path / "scratch" / "results" / "01_x"
    results.mkdir(parents=True)
    (results / "roc.html").write_text("<html>roc</html>\n", encoding="utf-8")
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    staged = (tmp_path / "_build" / "docs" / "journal" / "01_x.md").read_text(
        encoding="utf-8"
    )
    assert "## Results" not in staged
    assert "<iframe" not in staged
    assert (
        tmp_path / "_build" / "docs" / "scratch" / "results" / "01_x" / "roc.html"
    ).is_file()


def test_site_build_embeds_assets(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Figures render inline and each report HTML gets one iframe."""
    _scaffold(tmp_path)
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        "- Report: [data_analysis_adult.html](data_analysis_adult.html)\n"
        "- Views: [spatial](plot.png) - [again](plot.png)\n",
        encoding="utf-8",
    )
    (tmp_path / "data_analysis" / "data_analysis_adult.html").write_text(
        "<html></html>\n", encoding="utf-8"
    )
    (tmp_path / "data_analysis" / "plot.png").write_bytes(b"png")
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    staged = (
        tmp_path / "_build" / "docs" / "data_analysis" / "data_analysis.md"
    ).read_text(encoding="utf-8")
    assert "![spatial](plot.png)" in staged
    assert "![again](plot.png)" in staged
    assert staged.count('<iframe src="data_analysis_adult.html"') == 1
    assert "[data_analysis_adult.html](data_analysis_adult.html)" in staged
    assert 'class="skore-embed"' in staged


def test_site_build_inlines_fragment_html_and_frames_documents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A TableReport snippet is pasted in; a whole document keeps its iframe."""
    _scaffold(tmp_path)
    analysis = tmp_path / "data_analysis"
    analysis.mkdir()
    (analysis / "data_analysis.md").write_text(
        '<iframe src="data_analysis_adult.html" width="100%" height="640"></iframe>\n\n'
        "[Open the report](data_analysis_adult.html)\n\n"
        "- Plot: [scatter](scatter.html)\n"
        "- Gone: [absent](absent.html)\n",
        encoding="utf-8",
    )
    snippet = (
        '<div id="report-1">\n\n<skrub-table-report></skrub-table-report>\n</div>\n'
    )
    (analysis / "data_analysis_adult.html").write_text(snippet, encoding="utf-8")
    (analysis / "scatter.html").write_text(
        "<!DOCTYPE html><html><body>plot</body></html>\n", encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    staged = (docs / "data_analysis" / "data_analysis.md").read_text(encoding="utf-8")
    assert staged.count(snippet.strip()) == 1
    assert 'class="skore-inline"' in staged
    assert '<iframe src="data_analysis_adult.html"' not in staged
    assert "[Open the report](data_analysis_adult.html)" in staged
    assert '<iframe src="scatter.html"' in staged
    assert '<iframe src="absent.html"' in staged
    assert "skrub-table-report" in (
        docs / "data_analysis" / "data_analysis_adult.html"
    ).read_text(encoding="utf-8")


def test_site_build_keeps_authored_iframe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An authored iframe is upgraded to one styled viewer."""
    _scaffold(tmp_path)
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        '<iframe src="data_analysis_adult.html" width="100%" height="640"></iframe>\n\n'
        "[Open the report](data_analysis_adult.html)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    staged = (
        tmp_path / "_build" / "docs" / "data_analysis" / "data_analysis.md"
    ).read_text(encoding="utf-8")
    assert staged.count('src="data_analysis_adult.html"') == 1
    assert 'class="skore-embed"' in staged


def test_site_build_stub_index_in_nav(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When JOURNAL is missing, stub index.md is listed in nav."""
    (tmp_path / "src").mkdir()
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        "# eda\n", encoding="utf-8"
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    nav = (tmp_path / "_build" / "mkdocs.yml").read_text(encoding="utf-8")
    assert "Home: index.md" in nav
    assert "Exploratory data analysis: data_analysis/data_analysis.md" in nav
    assert (tmp_path / "_build" / "docs" / "index.md").is_file()
    assert "  homepage: index.html\n" in nav
    launcher = (tmp_path / "report.html").read_text(encoding="utf-8")
    assert "url=html/index.html" in launcher


def test_site_build_unscaffolded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Empty trees cannot build a site."""
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code != 0
    assert "not scaffolded" in result.output


def test_site_helpers_cover_link_suffix_and_empty_nav(tmp_path: Path) -> None:
    """Bare suffixes and an empty nav stay stable."""
    assert site_mod.result_dest("01_x", "plot", "png") == (
        "scratch/results/01_x/plot.png"
    )
    rendered = site_mod.render_mkdocs_yml(
        [], stub_home=True, site_name="demo", entry="index.html"
    )
    assert rendered.rstrip().endswith("- Home: index.md")
    _scaffold(tmp_path)
    site_mod.ensure_site_gitignore(tmp_path)
    first = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    site_mod.ensure_site_gitignore(tmp_path)
    assert (tmp_path / ".gitignore").read_text(encoding="utf-8") == first


def test_stage_docs_replaces_a_previous_staging_dir(tmp_path: Path) -> None:
    """A second stage deletes files left from the previous build."""
    _scaffold(tmp_path)
    site_mod.stage_docs(tmp_path)
    stale = tmp_path / "_build" / "docs" / "stale.md"
    stale.write_text("gone\n", encoding="utf-8")
    site_mod.stage_docs(tmp_path)
    assert not stale.exists()


def test_site_build_includes_mkdocs_stdout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Non-empty mkdocs stdout is kept ahead of the launcher path."""
    _scaffold(tmp_path)

    class Result:
        returncode = 0
        stdout = "Documentation built in 1.00 seconds\n"
        stderr = ""

    def fake_run(argv: list[str], **kwargs: object) -> Result:
        entry = tmp_path / "html" / site_mod.entry_page(tmp_path)
        entry.parent.mkdir(parents=True, exist_ok=True)
        entry.write_text("<html></html>\n", encoding="utf-8")
        return Result()

    monkeypatch.setattr(site_mod.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    assert result.output.startswith("Documentation built in 1.00 seconds\n")
    assert result.output.endswith(f"{site_mod.launcher_url(tmp_path)}\n")


def test_inject_skips_missing_heading_and_loose_markers(tmp_path: Path) -> None:
    """Snapshots without a subsection, and loose markers, stay unembedded."""
    stem = "01_x"
    results = tmp_path / "scratch" / "results" / stem
    results.mkdir(parents=True)
    (results / "metrics.html").write_text("<p>metrics</p>\n", encoding="utf-8")
    (results / "curves.html").write_text("<p>curves</p>\n", encoding="utf-8")
    (results / "nested").mkdir()
    (results / "plot.png").write_bytes(b"\x89PNG")
    (results / "report.txt").write_text("repr\n", encoding="utf-8")
    page = site_mod.Page(
        "Trial", tmp_path / "trial.md", f"journal/{stem}.md", section="Experiments"
    )
    text = "## Results\n\nProse without a metrics heading.\n"
    assert site_mod.inject_results(text, page, tmp_path) == text

    core = "## Method\n\n<!-- results-embed: report -->\n"
    assert site_mod._inject_marked_embeds(core, tmp_path, page) == core
    missing = "## Method\n\n<!-- results-embed: absent -->\n"
    assert site_mod._inject_marked_embeds(missing, tmp_path, page) == missing
    loose = "## Method\n\n<!--  results-embed: curves -->\n"
    assert site_mod._inject_marked_embeds(loose, tmp_path, page) == loose

    docs = tmp_path / "docs"
    docs.mkdir()
    site_mod._copy_result_html(tmp_path, docs, page)
    staged = docs / "scratch" / "results" / "01_x"
    assert (staged / "plot.png").is_file()
    assert not (staged / "nested").exists()
    assert not (staged / "report.txt").exists()


def test_inject_notebook_adds_a_trailing_newline() -> None:
    """A page that does not end in a newline still gets a notebook section."""
    page = site_mod.Page(
        "Trial",
        Path("trial.md"),
        "data_analysis/data_analysis.md",
        notebook=Path("/work/data_analysis/data_analysis.nb.html"),
    )
    text = site_mod.inject_notebook("hello", page, Path("/work"))
    assert text.startswith("hello\n")
    assert _tab_link("data_analysis.nb.html", "Open the notebook") in text
    assert site_mod.inject_notebook(text, page, Path("/work")) == text


def test_as_embed_document_links_the_stylesheet_from_its_folder() -> None:
    """A fragment staged in a subfolder reaches the shared baseline CSS."""
    deep = site_mod.as_embed_document("<p>x</p>", "scratch/results/01_x")
    assert 'href="../../../assets/skore/embed.css"' in deep
    assert 'href="assets/skore/embed.css"' in site_mod.as_embed_document("<p>x</p>")


def test_site_build_mirrors_the_workspace_so_authored_links_resolve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Links written between source files keep working between staged files."""
    _scaffold(tmp_path)
    (tmp_path / "data_analysis").mkdir()
    (tmp_path / "data_analysis" / "data_analysis.md").write_text(
        "# eda\n\n![plot](plot.png)\n", encoding="utf-8"
    )
    (tmp_path / "data_analysis" / "plot.png").write_bytes(b"eda")
    (tmp_path / "journal" / "figures").mkdir()
    (tmp_path / "journal" / "figures" / "roc.png").write_bytes(b"roc")
    (tmp_path / "journal" / "plot.png").write_bytes(b"journal")
    (tmp_path / "journal" / "JOURNAL.md").write_text(
        "# journal\n\n[eda](../data_analysis/data_analysis.md) "
        "[note](01_x.md) ![roc](figures/roc.png)\n",
        encoding="utf-8",
    )
    (tmp_path / "journal" / "01_x.md").write_text(
        "# design\n\n[eda](../data_analysis/data_analysis.md) "
        "![eda plot](../data_analysis/plot.png) ![roc](figures/roc.png) "
        "[home](JOURNAL.md)\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(site_mod.subprocess, "run", _ok_mkdocs(tmp_path))
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    docs = tmp_path / "_build" / "docs"
    home = (docs / "journal" / "JOURNAL.md").read_text(encoding="utf-8")
    assert "[eda](../data_analysis/data_analysis.md)" in home
    assert "[note](01_x.md)" in home
    assert "![roc](figures/roc.png)" in home
    note = (docs / "journal" / "01_x.md").read_text(encoding="utf-8")
    assert "[eda](../data_analysis/data_analysis.md)" in note
    assert "![eda plot](../data_analysis/plot.png)" in note
    for staged in (
        "journal/figures/roc.png",
        "journal/plot.png",
        "data_analysis/plot.png",
    ):
        assert (docs / staged).is_file(), staged
    assert (docs / "data_analysis" / "plot.png").read_bytes() == b"eda"
    assert (docs / "journal" / "plot.png").read_bytes() == b"journal"


def test_site_build_reports_broken_links_from_mkdocs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """MkDocs checks every link; the ones it cannot resolve reach the output."""
    _scaffold(tmp_path)

    def fake_run(argv: list[str], **kwargs: object) -> object:
        completed = _ok_mkdocs(tmp_path)(argv)
        completed.stderr = (
            "INFO    -  Building documentation\n"
            "WARNING -  Doc file 'journal/01_x.md' contains a link "
            "'../figures/roc.png', but the target is not found.\n"
        )
        return completed

    monkeypatch.setattr(site_mod.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(cli, ["site", "build"])
    assert result.exit_code == 0, result.output
    assert "contains a link '../figures/roc.png'" in result.output
    assert "Building documentation" not in result.output
    assert result.output.endswith(f"{site_mod.launcher_url(tmp_path)}\n")


def test_site_build_if_stale_rebuilds_when_a_journal_figure_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A figure next to a journal note is a site input like any other."""
    _scaffold(tmp_path)
    figure = tmp_path / "journal" / "roc.png"
    figure.write_bytes(b"one")
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **kwargs: object) -> object:
        calls.append(argv)
        return _ok_mkdocs(tmp_path)(argv)

    monkeypatch.setattr(site_mod.subprocess, "run", fake_run)
    monkeypatch.chdir(tmp_path)
    assert CliRunner().invoke(cli, ["site", "build", "--if-stale"]).exit_code == 0
    assert CliRunner().invoke(cli, ["site", "build", "--if-stale"]).exit_code == 0
    assert len(calls) == 1
    figure.write_bytes(b"two")
    assert CliRunner().invoke(cli, ["site", "build", "--if-stale"]).exit_code == 0
    assert len(calls) == 2
