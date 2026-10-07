# Where the agent was wrong, and what I checked by hand

Log kept during the build session (see `transcript.md` for the full session). Each entry: what
the agent (Claude Code) claimed or built, how it was caught, what changed.

| # | Agent was wrong about | Caught by | Fix |
|---|---|---|---|
| 1 | "The Ollama server wasn't running" — it was; the first `ollama list` just hung, and `ollama serve` then failed with *port already bound* | reading the error instead of trusting the summary | used the running server; noted that a hung CLI ≠ a dead service |
| 2 | Assumed `CLAUDE_CONFIG_DIR` + private `HOME` isolates a Claude Code run | **hand check**: asked an isolated agent whether it had instructions mentioning RTK/CodeGraph (terms only in my global CLAUDE.md). It said yes | Claude Code also reads `CLAUDE.md` from every **parent** dir; workspaces under `C:\Users\me\...` inherited `C:\Users\me\CLAUDE.md`. Runs moved outside the profile + a deterministic ancestor scan that refuses to run. Re-checked: `global=no` |
| 3 | First `Runner.collect` keyed results by harness hash | re-reading before writing tests | A/A calibration uses the *same* harness for both arms, so both arms would have merged into one. Keyed by arm label instead |
| 4 | Left a dead duplicate `BUILTIN_EXCEPTIONS` definition in `scorers.py` | IDE diagnostics + review | removed, single definition from `builtins` |
| 5 | Local agent: 15 minutes, zero tool calls | **hand check** of MCP server log (`CallToolRequest` count = 0) and `ollama ps` (context 4096) | Ollama's default 4k context truncated CrewAI's prompt + tool schemas |
| 6 | Proposed fix for #5: pass `num_ctx` to CrewAI's `LLM` (and switch to `ollama_chat/`) | it crashed: CrewAI 1.15 calls Ollama through an OpenAI-compatible client that rejects `num_ctx` | baked `num_ctx 16384` into `*-16k` Ollama model variants via Modelfile |
| 7 | Codex spike left a process holding the workspace open after the shell timed out | `rm` failed with *Device or resource busy* | adapters kill the whole process tree on timeout (`taskkill /T` on Windows) |
| 8 | Declared the local agent working after a smoke test, but that test ran **without** the private HOME the real runner uses | first real local runs all `error` in 2 s: `com_error` from `appdirs` -> `SHGetFolderPath` (no AppData under the private profile) | private `APPDATA`/`LOCALAPPDATA` for CrewAI runs; deleted the 10 bug-caused records so the cache could not replay them. Lesson: smoke-test through the real code path |
| 9 | One-pager chart: drew the noise-floor line at x=217 on a scale where +0.067 is x=188, and claimed "75 runs" (there are 60 unique records) | re-deriving the coordinates and counting records before rendering | fixed both; the corrected chart shows the 3-trial estimate sitting exactly on the floor, which is the point |

## A result I did not trust

Baseline vs candidate at 3 trials: **INCONCLUSIVE**, decided by a tie with the A/A noise floor
(+0.067 vs 0.067) although the rule-level evidence (tests-added 14/15 -> 9/15) looked real.
I did not relax the verdict rule after seeing the data. I extended to 6 trials instead ($1.39,
because calibration had cached baseline trials 3-5). Still INCONCLUSIVE: +0.06, CI [0.02, 0.11].
Both reports are kept: `examples/orders/results/reports/baseline-vs-candidate-3trials/` and
`.../baseline-vs-candidate/` (6 trials).

## Hand checks on the real tool (not just on unit tests)

- **First 18 tests passed on the first run** — distrusted that, generated a report from replay
  harnesses and read it: violations attributed to the right rules and lines, guardrails flat,
  conventions +0.83. Only then moved on.
- **First real Claude Code runs ($0.40, capped at $0.30 + one in-flight run)**: opened the run records and traced
  the tool calls in the raw logs: agents actually ran `python -m pytest` in the workspace via
  our interpreter on PATH; baseline coupons raised `ValueError` (a real convention violation, line 33);
  candidate obeyed the new "run tests before you finish" rule (two pytest runs, fixed its own
  failing test); tamper detection correctly reported nothing because only the agent's *own new*
  test was edited.
- Isolation: every Claude run's `init` event shows `plugins: []`, `mcp_servers: []`.
