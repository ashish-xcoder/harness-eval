"""Isolated run directories.

Each run gets a fresh directory outside the user's profile:

    <runs_root>/<run-id>/
        workspace/   task repo copy + harness workspace/ overlay, committed as git baseline
        home/        HOME / USERPROFILE / CLAUDE_CONFIG_DIR / CODEX_HOME for the agent;
                     harness home/ overlay + a *copy* of the login credentials

Why outside the profile: Claude Code collects CLAUDE.md from every parent directory of its
cwd, so a workspace under C:\\Users\\me\\ silently inherits C:\\Users\\me\\CLAUDE.md. The
ancestor scan below turns that into a hard failure instead of a contaminated result.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from harness_eval.config import Harness, Suite

# Files an agent may pick up from an ancestor directory and treat as instructions.
INSTRUCTION_NAMES = (
    "CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", "AGENTS.override.md", ".claude", ".codex",
)

# Login state copied into the private home so subscription logins keep working.
CREDENTIALS = {
    "claude": (
        Path.home() / ".claude" / ".credentials.json",
        Path(".claude") / ".credentials.json",
    ),
    "codex": (Path.home() / ".codex" / "auth.json", Path(".codex") / "auth.json"),
}

GIT_ENV = {
    "GIT_AUTHOR_NAME": "harness-eval",
    "GIT_AUTHOR_EMAIL": "harness-eval@localhost",
    "GIT_COMMITTER_NAME": "harness-eval",
    "GIT_COMMITTER_EMAIL": "harness-eval@localhost",
}


class IsolationError(Exception):
    pass


@dataclass(frozen=True)
class RunDirs:
    root: Path
    workspace: Path
    home: Path


def runs_root() -> Path:
    """Where run directories live. Override with HARNESS_EVAL_WORKDIR.

    Default is deliberately not the system temp dir: on Windows that sits inside the user
    profile, whose CLAUDE.md files would leak into every run.
    """
    if env := os.environ.get("HARNESS_EVAL_WORKDIR"):
        return Path(env)
    if sys.platform == "win32":
        return Path(Path.cwd().anchor) / ".harness-eval-runs"
    return Path(tempfile.gettempdir()) / "harness-eval-runs"


def leaked_ancestors(path: Path) -> list[Path]:
    """Instruction files in any ancestor of `path` (they would be inherited by the agent)."""
    found = []
    for parent in Path(path).resolve().parents:
        found += [parent / n for n in INSTRUCTION_NAMES if (parent / n).exists()]
    return found


def check_isolation(root: Path | None = None) -> None:
    root = root or runs_root()
    if leaks := leaked_ancestors(root / "probe"):
        listing = "\n  ".join(str(p) for p in leaks)
        raise IsolationError(
            f"agent runs under {root} would inherit instruction files from parent directories:\n"
            f"  {listing}\nSet HARNESS_EVAL_WORKDIR to a directory with no such ancestors."
        )


@contextmanager
def prepared_run(suite: Suite, harness: Harness, root: Path | None = None) -> Iterator[RunDirs]:
    """Create workspace + home for one run; always removes credentials and the directory."""
    root = (root or runs_root()) / uuid.uuid4().hex[:12]
    dirs = RunDirs(root=root, workspace=root / "workspace", home=root / "home")
    try:
        ignore = shutil.ignore_patterns("__pycache__", ".pytest_cache")
        shutil.copytree(suite.repo, dirs.workspace, ignore=ignore)
        if harness.workspace_dir.is_dir():
            shutil.copytree(harness.workspace_dir, dirs.workspace, dirs_exist_ok=True)
        dirs.home.mkdir(parents=True)
        if harness.home_dir.is_dir():
            shutil.copytree(harness.home_dir, dirs.home, dirs_exist_ok=True)
        _copy_credentials(harness.agent, dirs.home)
        git(dirs.workspace, "init", "-q")
        git(dirs.workspace, "add", "-A")
        git(dirs.workspace, "commit", "-q", "-m", "baseline")
        yield dirs
    finally:
        remove_credentials(dirs.home)
        try:
            rmtree(root)
        except OSError:  # a straggling agent process still holds a file; credentials are gone
            pass


def _copy_credentials(agent: str, home: Path) -> None:
    if agent not in CREDENTIALS:
        return
    src, rel = CREDENTIALS[agent]
    if src.is_file():  # API-key users have no file; the env var is passed through instead
        (home / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, home / rel)


def remove_credentials(home: Path) -> None:
    for _, rel in CREDENTIALS.values():
        (home / rel).unlink(missing_ok=True)


def agent_env(home: Path) -> dict[str, str]:
    """Environment for the agent process: private home, our interpreter first on PATH
    (so `python -m pytest` works inside the workspace even without a system Python)."""
    env = dict(os.environ)
    for var in ("HOME", "USERPROFILE"):
        env[var] = str(home)
    env["CLAUDE_CONFIG_DIR"] = str(home / ".claude")
    env["CODEX_HOME"] = str(home / ".codex")
    (home / ".codex").mkdir(exist_ok=True)  # codex requires CODEX_HOME to exist
    env["PATH"] = str(Path(sys.executable).parent) + os.pathsep + env.get("PATH", "")
    env.pop("VIRTUAL_ENV", None)
    env.pop("CLAUDECODE", None)  # we may be launched from inside a Claude Code session
    env.update(GIT_ENV)
    return env


def git(cwd: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "-c", "core.safecrlf=false", *args],
        cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, **GIT_ENV},
    )
    if out.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {out.stderr.strip()}")
    return out.stdout


def capture_diff(workspace: Path) -> str:
    """Everything the agent changed relative to the baseline commit, new files included."""
    git(workspace, "add", "-A")
    return git(workspace, "diff", "--cached", "HEAD", "--", ".", ":(exclude)**/__pycache__/**")


def changed_files(workspace: Path) -> dict[str, str]:
    """{path: status} with status A(dded), M(odified), D(eleted) vs the baseline commit."""
    git(workspace, "add", "-A")
    out = git(workspace, "diff", "--cached", "--name-status", "--no-renames", "HEAD")
    result = {}
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if "__pycache__" not in path:
            result[path] = status[:1]
    return result


def rmtree(path: Path) -> None:
    """rmtree that copes with read-only files (git objects on Windows)."""

    def _retry(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    if Path(path).exists():
        shutil.rmtree(path, onexc=_retry)
