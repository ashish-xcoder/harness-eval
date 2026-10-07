"""Suite and harness definitions, loaded from YAML, plus content hashing for the run cache."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import yaml

AGENTS = ("claude", "codex", "crewai", "replay")
_IGNORED = {"__pycache__", ".pytest_cache"}


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Task:
    id: str
    prompt: str
    hidden_tests: Path


@dataclass(frozen=True)
class Suite:
    name: str
    root: Path
    repo: Path
    tests: str
    source: str
    conventions: tuple[str, ...]
    tasks: tuple[Task, ...]

    def task_hash(self, task: Task) -> str:
        """Changes when anything the run depends on changes: repo, prompt, hidden tests."""
        h = hashlib.sha256(tree_hash(self.repo).encode())
        h.update(task.prompt.encode())
        h.update(_normalised(task.hidden_tests))
        return h.hexdigest()[:12]


@dataclass(frozen=True)
class Harness:
    """A harness is a directory: harness.yaml + files overlaid on the repo (workspace/)
    and on the agent's private home directory (home/)."""

    name: str
    root: Path
    agent: str
    model: str | None
    max_turns: int
    timeout_s: int
    extra_args: tuple[str, ...] = ()
    settings: dict = field(default_factory=dict)

    @property
    def workspace_dir(self) -> Path:
        return self.root / "workspace"

    @property
    def home_dir(self) -> Path:
        return self.root / "home"

    @property
    def hash(self) -> str:
        return tree_hash(self.root)[:12]

    def files(self) -> dict[str, str]:
        """Every harness file as text, keyed by relative path (for the report's harness diff)."""
        return {
            p.relative_to(self.root).as_posix(): _normalised(p).decode("utf-8", "replace")
            for p in sorted(self.root.rglob("*"))
            if p.is_file() and not _IGNORED.intersection(p.parts)
        }


def load_suite(path: Path) -> Suite:
    path = Path(path)
    if path.is_dir():
        path = path / "suite.yaml"
    data = _read_yaml(path)
    root = path.parent
    tasks = []
    for t in data.get("tasks") or []:
        hidden = root / t["hidden_tests"]
        if not hidden.is_file():
            raise ConfigError(f"task {t['id']}: hidden tests not found: {hidden}")
        tasks.append(Task(id=t["id"], prompt=t["prompt"].strip(), hidden_tests=hidden))
    if not tasks:
        raise ConfigError(f"{path}: suite has no tasks")
    if len({t.id for t in tasks}) != len(tasks):
        raise ConfigError(f"{path}: duplicate task ids")
    repo = root / data.get("repo", "repo")
    if not repo.is_dir():
        raise ConfigError(f"{path}: repo directory not found: {repo}")
    return Suite(
        name=data.get("name", root.name),
        root=root,
        repo=repo,
        tests=data.get("tests", "tests"),
        source=data.get("source", "."),
        conventions=tuple(data.get("conventions") or ()),
        tasks=tuple(tasks),
    )


def load_harness(path: Path) -> Harness:
    root = Path(path)
    data = _read_yaml(root / "harness.yaml")
    agent = data.get("agent")
    if agent not in AGENTS:
        raise ConfigError(f"{root}: agent must be one of {AGENTS}, got {agent!r}")
    known = {"agent", "model", "max_turns", "timeout_s", "extra_args"}
    return Harness(
        name=root.name,
        root=root,
        agent=agent,
        model=data.get("model"),
        max_turns=int(data.get("max_turns", 30)),
        timeout_s=int(data.get("timeout_s", 600)),
        extra_args=tuple(data.get("extra_args") or ()),
        settings={k: v for k, v in data.items() if k not in known},
    )


def tree_hash(root: Path) -> str:
    """Hash of every file's relative path and content. CRLF is normalised so a Windows
    checkout and a Linux checkout of the same commit hash identically."""
    h = hashlib.sha256()
    for p in sorted(Path(root).rglob("*")):
        if p.is_file() and not _IGNORED.intersection(p.parts):
            h.update(p.relative_to(root).as_posix().encode())
            h.update(b"\0")
            h.update(_normalised(p))
            h.update(b"\0")
    return h.hexdigest()


def _normalised(path: Path) -> bytes:
    return Path(path).read_bytes().replace(b"\r\n", b"\n")


def _read_yaml(path: Path) -> dict:
    if not path.is_file():
        raise ConfigError(f"not found: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: expected a mapping")
    return data
