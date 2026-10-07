# Harness evaluation: orders-service

> **Verdict: INCONCLUSIVE** - No evidence either way at this sample size. Add tasks or trials before deciding.

Exit code 2. no metric moved beyond its confidence interval / noise floor.

## What changed

|  | baseline | candidate |
|---|---|---|
| harness | `local-qwen2.5` (3a529c10c41c) | `local-qwen3.5` (65849126debc) |
| agent / model | crewai / ollama/qwen2.5-7b-16k | crewai / ollama/qwen3.5-4b-16k |
| runs | 5 | 5 |

```diff
--- local-qwen2.5/harness.yaml
+++ local-qwen3.5/harness.yaml
@@ -1,4 +1,4 @@
-# Local, free: CrewAI agent on Ollama qwen2.5:7b, workspace tools via the harness-eval MCP server.
+# Local, free: CrewAI agent on Ollama qwen3.5:4b, workspace tools via the harness-eval MCP server.
 agent: crewai
-model: ollama/qwen2.5-7b-16k
+model: ollama/qwen3.5-4b-16k
 max_turns: 25
```

## Scorecard

5 tasks x 1 trials per arm. Delta = candidate - baseline, averaged per task. 95% CI from a task+trial bootstrap. A metric only counts as moved when its CI excludes 0.

| metric | baseline | candidate | delta | 95% CI | noise floor | outcome |
|---|---|---|---|---|---|---|
| Works (existing tests pass) (guardrail) | 0.00 | 0.00 | +0.00 | [0.00, 0.00] | - | no change |
| Business intent (hidden acceptance tests) (guardrail) | 0.00 | 0.00 | +0.00 | [0.00, 0.00] | - | no change |
| Team conventions | 0.00 | 0.00 | +0.00 | [0.00, 0.00] | - | no change |
| Cost per task (USD) | $0.0000 | $0.0000 | +$0.0000 | [$0.0000, $0.0000] | - | no change |
| Tokens per task | 0 | 0 | +0 | [0, 0] | - | no change |
| Wall time per task (s) | 2 | 2 | -0 | [-0, 0] | - | no change |

## Per task

Mean per task (works / intent / conventions are 0-1, cost in USD).

| task | works | intent | conventions | cost | tampered runs |
|---|---|---|---|---|---|
| bulk-discount | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | $0.0000 -> $0.0000 | 0 -> 0 |
| coupons | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | $0.0000 -> $0.0000 | 0 -> 0 |
| tax | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | $0.0000 -> $0.0000 | 0 -> 0 |
| reserve-stock | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | $0.0000 -> $0.0000 | 0 -> 0 |
| shipping | 0.00 -> 0.00 | 0.00 -> 0.00 | 0.00 -> 0.00 | $0.0000 -> $0.0000 | 0 -> 0 |

## Convention violations

Runs with at least one violation of each rule (lower is better).

| rule | baseline | candidate |
|---|---|---|
| no-print | 0/5 | 0/5 |
| domain-errors | 0/5 | 0/5 |
| decimal-money | 0/5 | 0/5 |
| type-hints | 0/5 | 0/5 |
| module-logger | 0/5 | 0/5 |
| tests-added | 5/5 | 5/5 |

## Can I trust this measurement?

| check | result |
|---|---|
| run status (baseline) | error: 5 |
| run status (candidate) | error: 5 |
| isolation | private HOME/CODEX_HOME per run; ancestor CLAUDE.md/AGENTS.md scan |
| test tampering | 0 run(s) edited or deleted existing tests (originals are restored before scoring, so this cannot earn points) |
| hidden tests | copied in only after the agent exited; conftest/ini ignored |
| sample size | 5 tasks x 1 trials per arm (SMALL - treat as indicative) |
| A/A calibration | not run - run `harness-eval calibrate` to measure the noise floor |

## Evidence

Every run is a JSON record next to the agent's diff and redacted log. Open the diff of any surprising cell before acting on the verdict.

| arm | task | trial | status | works | intent | conv | cost | record |
|---|---|---|---|---|---|---|---|---|
| baseline | bulk-discount | 0 | error | 1 | 0.25 | 0.83 | $0.0000 | [json](runs/3a529c10c41c/bulk-discount-8231c8d52d44/trial-0.json) [diff](runs/3a529c10c41c/bulk-discount-8231c8d52d44/trial-0.diff) |
| baseline | coupons | 0 | error | 1 | 0.00 | 0.83 | $0.0000 | [json](runs/3a529c10c41c/coupons-cc47a6a3c067/trial-0.json) [diff](runs/3a529c10c41c/coupons-cc47a6a3c067/trial-0.diff) |
| baseline | reserve-stock | 0 | error | 1 | 0.75 | 0.83 | $0.0000 | [json](runs/3a529c10c41c/reserve-stock-2eabd626aece/trial-0.json) [diff](runs/3a529c10c41c/reserve-stock-2eabd626aece/trial-0.diff) |
| baseline | shipping | 0 | error | 1 | 0.00 | 0.83 | $0.0000 | [json](runs/3a529c10c41c/shipping-391d19718652/trial-0.json) [diff](runs/3a529c10c41c/shipping-391d19718652/trial-0.diff) |
| baseline | tax | 0 | error | 1 | 0.00 | 0.83 | $0.0000 | [json](runs/3a529c10c41c/tax-1af12c3c5ad1/trial-0.json) [diff](runs/3a529c10c41c/tax-1af12c3c5ad1/trial-0.diff) |
| candidate | bulk-discount | 0 | error | 1 | 0.25 | 0.83 | $0.0000 | [json](runs/65849126debc/bulk-discount-8231c8d52d44/trial-0.json) [diff](runs/65849126debc/bulk-discount-8231c8d52d44/trial-0.diff) |
| candidate | coupons | 0 | error | 1 | 0.00 | 0.83 | $0.0000 | [json](runs/65849126debc/coupons-cc47a6a3c067/trial-0.json) [diff](runs/65849126debc/coupons-cc47a6a3c067/trial-0.diff) |
| candidate | reserve-stock | 0 | error | 1 | 0.75 | 0.83 | $0.0000 | [json](runs/65849126debc/reserve-stock-2eabd626aece/trial-0.json) [diff](runs/65849126debc/reserve-stock-2eabd626aece/trial-0.diff) |
| candidate | shipping | 0 | error | 1 | 0.00 | 0.83 | $0.0000 | [json](runs/65849126debc/shipping-391d19718652/trial-0.json) [diff](runs/65849126debc/shipping-391d19718652/trial-0.diff) |
| candidate | tax | 0 | error | 1 | 0.00 | 0.83 | $0.0000 | [json](runs/65849126debc/tax-1af12c3c5ad1/trial-0.json) [diff](runs/65849126debc/tax-1af12c3c5ad1/trial-0.diff) |
