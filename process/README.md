# How this was built

Everything here comes from one Claude Code session (Claude Opus, VS Code extension, Windows).

| Artefact | What it is |
|---|---|
| [`../AGENTS.md`](../AGENTS.md) | The standing instructions written for the coding agent before any code: trust-first rules, isolation, caching, no attribution, definition of done |
| [`transcript.md`](transcript.md) | The complete session, exported with [`export_transcript.py`](export_transcript.py) (system reminders removed, e-mails/tokens redacted) |
| [`WHERE_THE_AGENT_WAS_WRONG.md`](WHERE_THE_AGENT_WAS_WRONG.md) | Every place the agent was wrong, how it was caught, and the hand checks done on real runs |

## Prompts I gave (verbatim, in order)

1. *"read this and provide task here clearly"* (with the brief PDF)
2. *"yes"* (start)
3. *"explore internet where you have doubt"*
4. *"never write any place co-authored by claude"*
5. *"as per document mentioned is this right architecture choose best skill to evalute"*
6. Answers to the design questions (below), including *"for this can we create local this files?"* and
   *"Create agent using crewai and ollama model and create mcp as well if needed"*
7. *"with ollama check all models"*
8. *"do it end to end"*
9. *"why to use flask instead of fastapi"* (it was flake8, not Flask), *"what is doing?"*

## Skills used

- `superpowers:brainstorming`: forced clarifying questions before code: stack (Python/uv),
  budget ($5-15), agents (Claude Code + Codex), demo change (AGENTS.md conventions).
- `plan-eng-review`: architecture review against the brief. It surfaced the four findings that
  shaped the tool: harness contamination, hidden-test leakage, no A/A noise floor, no crash/spend safety.

## Decisions taken in review

| # | Question | Decision |
|---|---|---|
| D1 | Isolate runs from my own harness? | Local per-run homes (HOME/USERPROFILE/CLAUDE_CONFIG_DIR/CODEX_HOME) with copied credentials, deleted after each run |
| D2 | Hidden-test leakage and test tampering | Inject hidden tests after the agent exits; restore pristine tests; report tampering |
| D3 | Prove the tool does not invent differences | `calibrate` = A/A run; its spread becomes the noise floor |
| D4 | 40+ paid runs | Content-addressed cache, resume, timeouts, `--max-cost` |
| D5 | Test the pipeline for free | CrewAI + Ollama local agent with a workspace MCP server (+ a deterministic `replay` agent for pytest) |
| D6 | Concurrency | Sequential (one 6 GB GPU; avoids rate limits) |
