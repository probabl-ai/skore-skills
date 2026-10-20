"""Filesystem gates for evaluate / audit close and the persisted locator."""

from __future__ import annotations

import json
import re
from contextlib import suppress
from pathlib import Path
from typing import Any

from skore_skills.notebook import source_fingerprint
from skore_skills.policy import load_policy

MISSING_LOCATOR = "n/a — backend did not expose a locator"
_PERSISTED = re.compile(
    r"^# %% \[markdown\]\s*\n# ## Persisted report\s*\n#\s*\n# (.+)$",
    re.MULTILINE,
)


def _results_dir(root: Path, stem: str) -> Path:
    return root / "scratch" / "results" / stem


def _exists(path: Path) -> bool:
    return path.is_file()


def loop_artifacts(root: Path, stem: str) -> dict[str, Any]:
    """Return which close step is due for ``stem``."""
    cleaned = stem.strip()
    if not cleaned:
        raise ValueError("stem is required")
    from skore_skills.project_api import experiment_by_stem

    experiment = experiment_by_stem(root, cleaned)
    if experiment is not None:
        report_stored = False
        try:
            report_stored = experiment._project.get(experiment.id) is not None
        except Exception:
            report_stored = False
        if experiment.status == "history" and report_stored:
            action, reason = "record", "report_stored"
        elif experiment.status == "backlog":
            action, reason = "evaluate_incomplete", "ready_to_run"
        else:
            action, reason = "stop", f"status_{experiment.status}"
        return {
            "stem": cleaned,
            "action": action,
            "reason": reason,
            "files": {"report": report_stored},
        }
    results = _results_dir(root, cleaned)
    smoke = root / "tests" / "smoke" / f"test_{cleaned}.py"
    experiment = root / "experiments" / f"{cleaned}.py"
    digest = root / "scratch" / "audit" / cleaned / "audit.md"
    report_html = results / "report.html"
    files = {
        "smoke": _exists(smoke),
        "experiment": _exists(experiment),
        "report_html": _exists(report_html),
        "report_txt": _exists(results / "report.txt"),
        "checks_html": _exists(results / "checks.html"),
        "metrics_html": _exists(results / "metrics.html"),
        "digest": _exists(digest),
        "locator": _exists(results / "locator.txt"),
    }
    if not files["smoke"]:
        action, reason = "stop", "smoke_missing"
    elif not files["report_html"]:
        action, reason = "evaluate_incomplete", "report_html_missing"
    elif not files["digest"]:
        action, reason = "audit", "digest_missing"
    else:
        action, reason = "record", "digest_present"
    return {
        "stem": cleaned,
        "action": action,
        "reason": reason,
        "files": files,
    }


def _scrape_audit_locator(root: Path, stem: str) -> str | None:
    path = root / "audit" / f"{stem}.py"
    if not path.is_file():
        return None
    match = _PERSISTED.search(path.read_text(encoding="utf-8"))
    if match is None:
        return None
    text = match.group(1).strip()
    if not text or text.startswith("<"):
        return None
    return text


def loop_locator(root: Path, stem: str) -> dict[str, Any]:
    """Return the persisted-report locator without opening the Project."""
    cleaned = stem.strip()
    if not cleaned:
        raise ValueError("stem is required")
    from skore_skills.project_api import experiment_by_stem

    experiment = experiment_by_stem(root, cleaned)
    if experiment is not None and experiment.status == "history":
        return {
            "stem": cleaned,
            "action": "proceed",
            "reason": "experiment",
            "locator": experiment.id,
        }
    path = _results_dir(root, cleaned) / "locator.txt"
    if path.is_file():
        text = path.read_text(encoding="utf-8").strip()
        if text:
            return {
                "stem": cleaned,
                "action": "proceed",
                "reason": "file",
                "locator": text,
            }
    scraped = _scrape_audit_locator(root, cleaned)
    if scraped is not None:
        return {
            "stem": cleaned,
            "action": "proceed",
            "reason": "audit",
            "locator": scraped,
        }
    return {
        "stem": cleaned,
        "action": "proceed",
        "reason": "missing",
        "locator": MISSING_LOCATOR,
    }


def _notebook_is_current(src: Path, notebook: Path) -> bool:
    if not notebook.is_file():
        return False
    with suppress(json.JSONDecodeError, OSError, TypeError):
        payload = json.loads(notebook.read_text(encoding="utf-8"))
        recorded = (
            payload.get("metadata", {}).get("skore_skills", {}).get("source_sha256")
        )
        if recorded is not None:
            return recorded == source_fingerprint(src)
    return notebook.stat().st_mtime_ns >= src.stat().st_mtime_ns


def _missing_notebook_sources(root: Path, stem: str, *, html: bool) -> list[str]:
    sources: list[str] = []
    for folder in ("experiments", "audit"):
        src = root / folder / f"{stem}.py"
        if not src.is_file():
            continue
        ipynb = src.with_suffix(".ipynb")
        nb_html = src.with_name(f"{stem}.nb.html")
        notebook_current = _notebook_is_current(src, ipynb)
        html_current = (
            nb_html.is_file()
            and ipynb.is_file()
            and nb_html.stat().st_mtime_ns >= ipynb.stat().st_mtime_ns
        )
        if not notebook_current or (html and not html_current):
            sources.append(f"{folder}/{stem}.py")
    return sources


def loop_notebooks(root: Path, stem: str) -> dict[str, Any]:
    """Return whether ``stem`` still needs ``notebook convert``.

    ``policy.notebooks`` must be true and a persisted report must exist.
    Unevaluated scripts stay ``.py`` only. ``sources`` lists repo-relative
    percent files whose ``.ipynb`` (and ``.nb.html`` when ``policy.site``
    is true) is missing.
    """
    cleaned = stem.strip()
    if not cleaned:
        raise ValueError("stem is required")
    policy = load_policy(root)
    html = policy.get("site") is True
    payload: dict[str, Any] = {
        "stem": cleaned,
        "html": html,
        "sources": [],
    }
    if policy.get("notebooks") is not True:
        payload["action"] = "skip"
        payload["reason"] = "policy_off"
        return payload
    if not (_results_dir(root, cleaned) / "report.html").is_file():
        payload["action"] = "skip"
        payload["reason"] = "not_evaluated"
        return payload
    sources = _missing_notebook_sources(root, cleaned, html=html)
    if sources:
        payload["action"] = "convert"
        payload["reason"] = "notebook_missing"
        payload["sources"] = sources
        return payload
    payload["action"] = "skip"
    payload["reason"] = "already_present"
    return payload


def render_loop(payload: dict[str, Any]) -> str:
    """Serialize a loop-gate payload."""
    return json.dumps(payload, indent=2) + "\n"
