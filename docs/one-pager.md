# harness-eval: one page

**Question it answers:** "is the coding agent producing better code after this harness change?",
with evidence a maintainer can trust *before* rolling the change out to every engineer.

## Concepts I defined, and why
- **Harness = a directory** (`harness.yaml` + files overlaid on the repo + files for the agent's private home). One shape covers AGENTS.md, skills, MCP, hooks, model swaps and agent swaps (Claude Code / Codex / CrewAI).
- **Suite = real tasks with hidden acceptance tests.** The prompt is a business request; the tests encode what the business asked and are injected only after the agent exits.
- **Four dimensions, two of them guardrails.** *Works* (repo's own tests, restored pristine) and *intent* (hidden tests) can veto a change; *conventions* (deterministic AST rules from the team's AGENTS.md) and *cost* (USD, tokens, time) cannot.
- **Paired task delta + bootstrap CI.** The unit is the task (difficulty cancels); resampling tasks *and* trials covers both "which tasks we picked" and agent randomness.
- **Noise floor (A/A).** `calibrate` runs the baseline against itself. The tool must say INCONCLUSIVE there, and the spread it measures is a bar every real delta must clear.
- **Verdict with an exit code:** IMPROVEMENT 0, REGRESSION 1, INCONCLUSIVE 2, TRADE-OFF 3. TRADE-OFF exists so the tool never invents a weighting between quality and cost.

## The five hardest decisions
1. **No LLM judge.** Every score comes from tests or AST rules. A judge would cover more conventions but brings back "an opinion formed by reading outputs", the thing the brief wants replaced. The cost is coverage: only rules I can encode are checked.
2. **Failed runs count as zero.** A timeout or crash is part of the harness's behaviour; dropping it would make a flaky harness look better.
3. **Guardrails veto, no weighted score.** Any detected drop in works/intent = REGRESSION. Mixed outcomes become TRADE-OFF for a human, instead of a made-up weighting.
4. **Isolation from my own harness.** A hand check showed my global `~/.claude/CLAUDE.md` leaking into "isolated" runs through Claude Code's parent-directory lookup. Runs now execute outside the user profile with private HOME/config dirs; an ancestor scan and a per-run plugin/MCP check abort the evaluation on contamination.
5. **The A/A noise floor as an extra bar on top of the CI.** It is deliberately conservative (it partly double-counts noise): a false "ship it" reaches every engineer, a missed improvement costs one more run.

## What I cut, and why
LLM-judged quality (see 1) · parallel runs (one GPU, API rate limits; arms are interleaved instead) · a Codex demo (adapter + isolation spike done, no full run, to stay in budget) · non-Python convention rules · suites mined from real PRs/issues (the 5 tasks are hand-written) · power analysis ("how many trials do I need") · history/dashboards across many changes.

## One result I did not trust, and what I did
Baseline (bare AGENTS.md) vs candidate (AGENTS.md with team conventions), Claude Code on Haiku, 5 tasks x 3 trials:
**INCONCLUSIVE.** But the evidence underneath was not empty: conventions rose 0.83 to 0.90 with a 95% CI of [0.01, 0.13], on 4 of 5 tasks; runs with no tests added fell 14/15 to 9/15. The verdict was decided by a tie with the A/A noise floor (+0.067 vs 0.067).
I did **not** relax the rule after seeing the data, because that is how a tool learns to say what you want. I bought more data instead: 6 trials per arm. The 3 extra baseline trials were already cached from calibration, so this cost 15 runs (about $1.50).
**Result at 6 trials: still INCONCLUSIVE.** Conventions +0.06, CI [0.02, 0.11]. It is real but small, and below the 0.067 floor. "No tests added" fell from 28/30 to 18/30 runs, so the new rule is followed only 40% of the time. Cost +12% (CI includes 0). The only hidden-test failure in 60 runs was a candidate run (coupon rounding). My call as maintainer: the change helps conventions a little and is not proven, so don't roll it out on this evidence. Make the tests rule enforceable (a hook that runs pytest) and re-run. Total spend for the whole demo: $5.28.
A second thing I distrust: the baseline passed **every** hidden test (intent = 1.00, noise floor 0). This suite cannot show a harness change hurting correctness unless it hurts a lot. The next investment is harder tasks, not more statistics.
