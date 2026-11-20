"""Fake-harness tests for the integration scenario runner."""

from __future__ import annotations

import json
import os
import stat
import sys
from contextlib import suppress
from pathlib import Path

import pytest

from tools import integration_harness, integration_scenario
from tools.integration_harness import (
    EXIT_INTERRUPT,
    EXIT_MISSING,
    EXIT_TIMEOUT,
    INITIAL_PROMPT,
    PI_DEFAULT_MODEL,
    PI_DEFAULT_PROVIDER,
    HarnessError,
    PreparedLaunch,
    _wait,
    build_launch,
    execute_launch,
)
from tools.integration_scenario import (
    ensure_workspace,
    materialize,
    run_scenario,
    stage_workflow_skills,
)


def _driver(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "SCENARIO.md"
    path.write_text("authorized choices\n", encoding="utf-8")
    return path


def _fake_which(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        integration_harness.shutil,
        "which",
        lambda name: f"/fake/{name}",
    )


def _launch(
    directory: Path,
    *,
    interactive: bool,
    model: str | None,
    extra_args: list[str] | None = None,
    skill_paths: list[Path] | None = None,
):
    return build_launch(
        workspace=directory,
        driver=_driver(directory),
        interactive=interactive,
        model=model,
        extra_args=extra_args,
        skill_paths=skill_paths,
    )


def test_pi_commands(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_which(monkeypatch)
    headless = _launch(tmp_path / "pi", interactive=False, model="pair")
    assert headless.argv[:4] == [
        "/fake/pi",
        "--append-system-prompt",
        str(tmp_path / "pi" / "SCENARIO.md"),
        "--approve",
    ]
    assert headless.argv[4:6] == ["--mode", "json"]
    assert "--print" not in headless.argv
    assert headless.argv[headless.argv.index("--provider") + 1] == PI_DEFAULT_PROVIDER
    assert headless.argv[headless.argv.index("--model") + 1] == "pair"
    assert PI_DEFAULT_MODEL not in headless.argv
    interactive = _launch(tmp_path / "tty", interactive=True, model=None)
    assert "--mode" not in interactive.argv
    assert interactive.argv[-1] == INITIAL_PROMPT


def test_pi_defaults_and_harness_args(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fake_which(monkeypatch)
    default = _launch(tmp_path / "default", interactive=True, model=None)
    assert default.argv[default.argv.index("--provider") + 1] == PI_DEFAULT_PROVIDER
    assert default.argv[default.argv.index("--model") + 1] == PI_DEFAULT_MODEL
    overridden = _launch(
        tmp_path / "extra",
        interactive=False,
        model=None,
        extra_args=["--provider", "other", "--model", "custom", "--thinking", "high"],
    )
    assert overridden.argv.count("--provider") == 1
    assert overridden.argv.count("--model") == 1
    assert overridden.argv[overridden.argv.index("--provider") + 1] == "other"
    assert overridden.argv[overridden.argv.index("--model") + 1] == "custom"
    assert "--thinking" in overridden.argv
    assert overridden.argv[-1] == INITIAL_PROMPT


def test_pi_loads_skills_before_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fake_which(monkeypatch)
    skills = [tmp_path / "source-a", tmp_path / "source-b"]
    launch = _launch(
        tmp_path / "workspace",
        interactive=False,
        model=None,
        skill_paths=skills,
    )
    assert launch.argv.count("--skill") == 2
    for source in skills:
        index = launch.argv.index(str(source))
        assert launch.argv[index - 1] == "--skill"
        assert index < len(launch.argv) - 1
    assert launch.argv[-1] == INITIAL_PROMPT


def test_launch_prepends_checkout_to_pythonpath(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _fake_which(monkeypatch)
    monkeypatch.setenv("PYTHONPATH", "existing")
    launch = _launch(tmp_path, interactive=True, model=None)
    entries = launch.env["PYTHONPATH"].split(os.pathsep)
    expected = Path(integration_harness.__file__).resolve().parent.parent / "src"
    assert entries == [str(expected), "existing"]


def test_missing_pi(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(integration_harness.shutil, "which", lambda _name: None)
    with pytest.raises(HarnessError, match="pi is not installed") as missing:
        _launch(tmp_path, interactive=True, model=None)
    assert missing.value.code == EXIT_MISSING


def test_headless_streams_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    launch = PreparedLaunch(
        argv=[
            sys.executable,
            "-c",
            "import sys; print('hello-out'); print('hello-err', file=sys.stderr)",
        ],
        cwd=tmp_path,
        env=os.environ.copy(),
        cleanup=lambda: None,
    )
    stdout_path = tmp_path / "logs" / "stdout.txt"
    stderr_path = tmp_path / "logs" / "stderr.txt"
    status = execute_launch(
        launch,
        interactive=False,
        timeout=5,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
    )
    captured = capsys.readouterr()
    assert status == 0
    assert stdout_path.read_text(encoding="utf-8") == "hello-out\n"
    assert stderr_path.read_text(encoding="utf-8") == "hello-err\n"
    assert "hello-out" in captured.out
    assert "hello-err" in captured.err


def test_timeout_kills_the_process_group(tmp_path: Path) -> None:
    pids: list[int] = []

    def popen(argv, **kwargs):
        import subprocess

        process = subprocess.Popen(argv, **kwargs)
        pids.append(process.pid)
        return process

    launch = PreparedLaunch(
        argv=[sys.executable, "-c", "import time; time.sleep(60)"],
        cwd=tmp_path,
        env=os.environ.copy(),
        cleanup=lambda: None,
    )
    try:
        status = execute_launch(
            launch,
            interactive=False,
            timeout=0.2,
            stdout_path=tmp_path / "logs" / "stdout.txt",
            stderr_path=tmp_path / "logs" / "stderr.txt",
            popen=popen,
        )
        assert status == EXIT_TIMEOUT
        with pytest.raises(OSError):
            os.kill(pids[0], 0)
    finally:
        for pid in pids:
            with suppress(OSError):
                os.kill(pid, 9)


@pytest.mark.skipif(os.name == "nt", reason="Windows uses taskkill, not killpg")
def test_timeout_kills_the_pid_when_killpg_is_denied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pids: list[int] = []

    def deny_group(pid: int, sig: int) -> None:
        raise PermissionError(1, "Operation not permitted")

    def popen(argv, **kwargs):
        import subprocess

        process = subprocess.Popen(argv, **kwargs)
        pids.append(process.pid)
        return process

    monkeypatch.setattr(integration_harness.os, "killpg", deny_group)
    launch = PreparedLaunch(
        argv=[sys.executable, "-c", "import time; time.sleep(60)"],
        cwd=tmp_path,
        env=os.environ.copy(),
        cleanup=lambda: None,
    )
    try:
        status = execute_launch(
            launch,
            interactive=False,
            timeout=0.2,
            stdout_path=tmp_path / "logs" / "stdout.txt",
            stderr_path=tmp_path / "logs" / "stderr.txt",
            popen=popen,
        )
        assert status == EXIT_TIMEOUT
        with pytest.raises(OSError):
            os.kill(pids[0], 0)
    finally:
        for pid in pids:
            with suppress(OSError):
                os.kill(pid, 9)


def test_interrupt_returns_130() -> None:
    killed: list[int] = []

    class _Stop(_Ready):
        def wait(self, timeout: float | None = None) -> int:
            self.calls += 1
            if self.calls == 1:
                raise KeyboardInterrupt
            return 0

    status = _wait(_Stop(), timeout=5, terminate=killed.append)
    assert status == EXIT_INTERRUPT
    assert killed == [7]


def test_materialize_copies_driver(tmp_path: Path) -> None:
    dest = tmp_path / "housing"
    materialize("california-housing", dest, force=False)
    text = (dest / "SCENARIO.md").read_text(encoding="utf-8")
    assert "California housing" in text
    assert "{{SKILLS_REPO}}" not in text
    assert "{{SKILLS_REPO_URI}}" not in text
    repo = integration_scenario.CHECKOUT_ROOT.resolve()
    assert str(repo) in text
    assert repo.as_uri() in text
    assert 'skill("setup-ml-project")' in text
    assert "record the outcome" in text
    assert "Run the data analysis" in text
    assert "close this stage" in text
    assert "/reload" not in text
    assert "Symlink each" not in text
    assert (dest / "DATA.md").is_file()
    housing = dest / "data" / "raw" / "housing.csv"
    rows = housing.read_text(encoding="utf-8").splitlines()
    assert len(rows) - 1 >= 5000


def test_stage_workflow_skills_before_launch(tmp_path: Path) -> None:
    paths = stage_workflow_skills("ml-experimentation", tmp_path)
    catalog = json.loads(
        (tmp_path / ".agents" / "skills" / ".catalog.json").read_text(encoding="utf-8")
    )
    included = catalog["workflows"][0]["includes"]
    assert included
    assert len(paths) == len(included)
    assert {path.name for path in paths} == set(included)
    for skill_id in included:
        sidecar = tmp_path / ".agents" / "skills" / skill_id / ".skore-skill.json"
        assert json.loads(sidecar.read_text(encoding="utf-8")) == {"id": skill_id}


def test_reuse_workspace_rules(tmp_path: Path) -> None:
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "keep.txt").write_text("keep\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="reuse-workspace"):
        ensure_workspace("california-housing", occupied, reuse=False)
    ensure_workspace("california-housing", occupied, reuse=True)
    assert (occupied / "keep.txt").is_file()
    assert (occupied / "SCENARIO.md").is_file()
    assert not (occupied / "DATA.md").exists()


def test_run_records_check_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _script(tmp_path / "bin" / "pi", code=0)
    monkeypatch.setenv("PATH", f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(integration_scenario, "REPO_ROOT", tmp_path)
    workspace = tmp_path / "housing"
    status = run_scenario(
        "california-housing",
        workspace=workspace,
        interactive=False,
        model=None,
        timeout=5,
        reuse=False,
    )
    result = _result(tmp_path)
    assert status == 1
    assert result["exit_status"] == 1
    assert result["harness"] == "pi"
    assert result["mode"] == "headless"
    assert result["check_errors"]
    assert (workspace / "SCENARIO.md").is_file()


def test_run_skips_check_when_harness_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = tmp_path / "record.txt"
    _script(tmp_path / "bin" / "pi", code=3, record=record)
    monkeypatch.setenv("PATH", f"{tmp_path / 'bin'}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setattr(integration_scenario, "REPO_ROOT", tmp_path)
    status = run_scenario(
        "california-housing",
        workspace=tmp_path / "housing",
        interactive=False,
        model=None,
        timeout=5,
        reuse=False,
    )
    result = _result(tmp_path)
    recorded = record.read_text(encoding="utf-8")
    assert status == 3
    assert result["check_errors"] == []
    assert "--approve" in recorded
    assert "--mode" in recorded
    assert "json" in recorded


def test_run_reports_missing_pi(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PATH", str(tmp_path))
    monkeypatch.setattr(integration_scenario, "REPO_ROOT", tmp_path)
    status = run_scenario(
        "california-housing",
        workspace=tmp_path / "housing",
        interactive=False,
        model=None,
        timeout=5,
        reuse=False,
    )
    result = _result(tmp_path)
    assert status == EXIT_MISSING
    assert result["exit_status"] == EXIT_MISSING


def test_run_refuses_nonempty_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "housing"
    workspace.mkdir()
    (workspace / "keep.txt").write_text("keep\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="reuse-workspace"):
        run_scenario(
            "california-housing",
            workspace=workspace,
            interactive=False,
            model=None,
            timeout=5,
            reuse=False,
        )


class _Ready:
    def __init__(self) -> None:
        self.pid = 7
        self.calls = 0

    def wait(self, timeout: float | None = None) -> int:
        self.calls += 1
        return 0


def _script(path: Path, *, code: int, record: Path | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["import sys", "from pathlib import Path"]
    if record is not None:
        lines.append(
            f"Path({str(record)!r}).write_text('\\n'.join(sys.argv[1:]) + '\\n')"
        )
    lines.append(f"raise SystemExit({code})")
    program = "\n".join(lines) + "\n"
    if os.name == "nt":
        source = path.with_suffix(".py")
        source.write_text(program, encoding="utf-8")
        path.with_suffix(".cmd").write_text(
            f'@echo off\r\n"{sys.executable}" "{source}" %*\r\n',
            encoding="utf-8",
        )
        return
    path.write_text(f"#!{sys.executable}\n{program}", encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _result(root: Path) -> dict[str, object]:
    paths = list((root / ".transcripts").rglob("result.json"))
    assert len(paths) == 1
    return json.loads(paths[0].read_text(encoding="utf-8"))
