"""workspace MCP server: the minimal toolset a coding agent needs, jailed to one directory.

    python -m harness_eval.mcp_server --root <workspace>

Used as the CrewAI local agent's only tools, and attachable to any harness via .mcp.json,
so "we added an MCP server" is itself an evaluable harness change.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("workspace")
ROOT = Path.cwd()


def _safe(path: str) -> Path:
    p = (ROOT / path).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError(f"path escapes the workspace: {path}")
    return p


@mcp.tool()
def list_files(path: str = ".") -> str:
    """List files under a directory of the workspace (recursive, max 200 entries)."""
    base = _safe(path)
    files = [p.relative_to(ROOT).as_posix() for p in sorted(base.rglob("*"))
             if p.is_file() and ".git" not in p.parts and "__pycache__" not in p.parts]
    return "\n".join(files[:200]) or "(empty)"


@mcp.tool()
def read_file(path: str) -> str:
    """Return the full text of a workspace file."""
    return _safe(path).read_text(encoding="utf-8")


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Create or overwrite a workspace file with the given full content."""
    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return f"wrote {len(content)} chars to {path}"


@mcp.tool()
def run_tests(path: str = "") -> str:
    """Run pytest in the workspace (optionally on one path) and return the summary."""
    cmd = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *([path] if path else [])]
    try:
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return "pytest timed out after 120s"
    return (out.stdout + out.stderr)[-3000:]


def main() -> None:
    global ROOT
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    ROOT = Path(parser.parse_args().root).resolve()
    mcp.run()


if __name__ == "__main__":
    main()
