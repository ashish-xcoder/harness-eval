"""Turn a Claude Code session .jsonl into a readable Markdown transcript.

    uv run python process/export_transcript.py <session.jsonl> process/transcript.md

Keeps: user messages, assistant text, every tool call (name + key input) and a short excerpt of
each tool result. Drops: system reminders and hook noise. Redacts: e-mail addresses and
anything that looks like a token.
"""

import json
import re
import sys
from pathlib import Path

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
TOKEN = re.compile(r"\b(sk-[A-Za-z0-9_-]{16,}|eyJ[A-Za-z0-9_-]{20,}|[A-Fa-f0-9]{40,})\b")
REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)


def clean(text: str) -> str:
    text = REMINDER.sub("", text)
    text = EMAIL.sub("[email]", text)
    return TOKEN.sub("[redacted]", text).strip()


def tool_summary(block: dict) -> str:
    inp = block.get("input") or {}
    key = next((inp[k] for k in ("command", "file_path", "pattern", "query", "skill", "url",
                                 "description") if k in inp), "")
    if block["name"] in ("Write", "Edit") and "file_path" in inp:
        size = len(inp.get("content") or inp.get("new_string") or "")
        return f"**{block['name']}** `{inp['file_path']}` ({size} chars)"
    if block["name"] == "AskUserQuestion":
        qs = "; ".join(q["question"] for q in inp.get("questions", []))
        return f"**AskUserQuestion**: {qs}"
    return f"**{block['name']}** `{str(key)[:300]}`"


def result_excerpt(block: dict, limit: int = 600) -> str:
    content = block.get("content")
    if isinstance(content, list):
        content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    text = clean(str(content or ""))
    return text if len(text) <= limit else text[:limit] + f" ... [{len(text) - limit} chars cut]"


def main(src: str, dst: str) -> None:
    out = ["# Build session transcript", "",
           "Exported from the Claude Code session that built this repository. "
           "Tool results are truncated; system reminders removed; e-mails/tokens redacted.", ""]
    for line in Path(src).read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = e.get("message") or {}
        content = msg.get("content")
        if e.get("type") == "user":
            if isinstance(content, str):
                if (text := clean(content)) and not text.startswith("<"):
                    out += ["---", "", "### USER", "", text, ""]
            elif isinstance(content, list):
                for c in content:
                    if c.get("type") == "text" and (text := clean(c["text"])) and not text.startswith("<"):
                        out += ["---", "", "### USER", "", text, ""]
                    elif c.get("type") == "tool_result":
                        out += [f"> result: {result_excerpt(c)}".replace("\n", "\n> "), ""]
        elif e.get("type") == "assistant" and isinstance(content, list):
            for c in content:
                if c.get("type") == "text" and (text := clean(c["text"])):
                    out += ["### ASSISTANT", "", text, ""]
                elif c.get("type") == "tool_use":
                    out += [f"- {tool_summary(c)}", ""]
    Path(dst).write_text("\n".join(out), encoding="utf-8")
    print(f"wrote {dst}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
