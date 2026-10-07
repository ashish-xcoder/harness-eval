# Harness evaluation: orders-service

> **Verdict: INCONCLUSIVE** - No evidence either way at this sample size. Add tasks or trials before deciding.

Exit code 2. no metric moved beyond its confidence interval / noise floor.

## What changed

|  | A | A' |
|---|---|---|
| harness | `baseline` (7e833fd841be) | `baseline` (7e833fd841be) |
| agent / model | claude / haiku | claude / haiku |
| runs | 15 | 15 |

Harness files are identical (A/A run).

## Scorecard

5 tasks x 3 trials per arm. Delta = A' - A, averaged per task. 95% CI from a task+trial bootstrap. A metric only counts as moved when its CI excludes 0.

| metric | A | A' | delta | 95% CI | noise floor | outcome |
|---|---|---|---|---|---|---|
| Works (existing tests pass) (guardrail) | 1.00 | 1.00 | +0.00 | [0.00, 0.00] | - | no change |
| Business intent (hidden acceptance tests) (guardrail) | 1.00 | 1.00 | +0.00 | [0.00, 0.00] | - | no change |
| Team conventions | 0.83 | 0.84 | +0.01 | [-0.02, 0.07] | - | no change |
| Cost per task (USD) | $0.0838 | $0.0822 | $-0.0016 | [$-0.0212, $0.0182] | - | no change |
| Tokens per task | 245,458 | 250,706 | +5,248 | [-77,829, 116,941] | - | no change |
| Wall time per task (s) | 30 | 33 | +3 | [-6, 14] | - | no change |

## Per task

Mean per task (works / intent / conventions are 0-1, cost in USD).

| task | works | intent | conventions | cost | tampered runs |
|---|---|---|---|---|---|
| bulk-discount | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.83 | $0.0937 -> $0.0623 | 0 -> 0 |
| coupons | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.89 | $0.0954 -> $0.1234 | 0 -> 0 |
| tax | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.83 | $0.0662 -> $0.0627 | 0 -> 0 |
| reserve-stock | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.83 | $0.0989 -> $0.0953 | 0 -> 0 |
| shipping | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.83 | $0.0648 -> $0.0672 | 0 -> 0 |

## Convention violations

Runs with at least one violation of each rule (lower is better).

| rule | A | A' |
|---|---|---|
| no-print | 0/15 | 0/15 |
| domain-errors | 1/15 | 0/15 |
| decimal-money | 0/15 | 0/15 |
| type-hints | 0/15 | 0/15 |
| module-logger | 0/15 | 0/15 |
| tests-added | 14/15 | 14/15 |

## Can I trust this measurement?

| check | result |
|---|---|
| run status (A) | ok: 15 |
| run status (A') | ok: 15 |
| isolation | 30/30 Claude runs loaded no plugins, no MCP servers beyond the harness; runs execute outside the user profile after an ancestor CLAUDE.md/AGENTS.md scan |
| test tampering | 0 run(s) edited or deleted existing tests (originals are restored before scoring, so this cannot earn points) |
| hidden tests | copied in only after the agent exited; conftest/ini ignored |
| sample size | 5 tasks x 3 trials per arm (OK) |
| A/A calibration | not run - run `harness-eval calibrate` to measure the noise floor |

## Evidence

Every run is a JSON record next to the agent's diff and redacted log. Open the diff of any surprising cell before acting on the verdict.

| arm | task | trial | status | works | intent | conv | cost | record |
|---|---|---|---|---|---|---|---|---|
| A | bulk-discount | 0 | ok | 1 | 1.00 | 0.83 | $0.1313 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-0.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-0.diff) |
| A | bulk-discount | 1 | ok | 1 | 1.00 | 0.83 | $0.0870 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-1.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-1.diff) |
| A | bulk-discount | 2 | ok | 1 | 1.00 | 0.83 | $0.0627 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-2.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-2.diff) |
| A | coupons | 0 | ok | 1 | 1.00 | 0.67 | $0.0640 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-0.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-0.diff) |
| A | coupons | 1 | ok | 1 | 1.00 | 0.83 | $0.1018 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-1.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-1.diff) |
| A | coupons | 2 | ok | 1 | 1.00 | 1.00 | $0.1204 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-2.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-2.diff) |
| A | reserve-stock | 0 | ok | 1 | 1.00 | 0.83 | $0.1060 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-0.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-0.diff) |
| A | reserve-stock | 1 | ok | 1 | 1.00 | 0.83 | $0.0902 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-1.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-1.diff) |
| A | reserve-stock | 2 | ok | 1 | 1.00 | 0.83 | $0.1006 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-2.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-2.diff) |
| A | shipping | 0 | ok | 1 | 1.00 | 0.83 | $0.0643 | [json](runs/7e833fd841be/shipping-391d19718652/trial-0.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-0.diff) |
| A | shipping | 1 | ok | 1 | 1.00 | 0.83 | $0.0653 | [json](runs/7e833fd841be/shipping-391d19718652/trial-1.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-1.diff) |
| A | shipping | 2 | ok | 1 | 1.00 | 0.83 | $0.0647 | [json](runs/7e833fd841be/shipping-391d19718652/trial-2.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-2.diff) |
| A | tax | 0 | ok | 1 | 1.00 | 0.83 | $0.0617 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-0.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-0.diff) |
| A | tax | 1 | ok | 1 | 1.00 | 0.83 | $0.0689 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-1.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-1.diff) |
| A | tax | 2 | ok | 1 | 1.00 | 0.83 | $0.0679 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-2.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-2.diff) |
| A' | bulk-discount | 3 | ok | 1 | 1.00 | 0.83 | $0.0625 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-3.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-3.diff) |
| A' | bulk-discount | 4 | ok | 1 | 1.00 | 0.83 | $0.0619 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-4.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-4.diff) |
| A' | bulk-discount | 5 | ok | 1 | 1.00 | 0.83 | $0.0627 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-5.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-5.diff) |
| A' | coupons | 3 | ok | 1 | 1.00 | 1.00 | $0.1360 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-3.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-3.diff) |
| A' | coupons | 4 | ok | 1 | 1.00 | 0.83 | $0.1282 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-4.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-4.diff) |
| A' | coupons | 5 | ok | 1 | 1.00 | 0.83 | $0.1058 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-5.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-5.diff) |
| A' | reserve-stock | 3 | ok | 1 | 1.00 | 0.83 | $0.0941 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-3.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-3.diff) |
| A' | reserve-stock | 4 | ok | 1 | 1.00 | 0.83 | $0.0963 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-4.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-4.diff) |
| A' | reserve-stock | 5 | ok | 1 | 1.00 | 0.83 | $0.0957 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-5.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-5.diff) |
| A' | shipping | 3 | ok | 1 | 1.00 | 0.83 | $0.0703 | [json](runs/7e833fd841be/shipping-391d19718652/trial-3.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-3.diff) |
| A' | shipping | 4 | ok | 1 | 1.00 | 0.83 | $0.0660 | [json](runs/7e833fd841be/shipping-391d19718652/trial-4.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-4.diff) |
| A' | shipping | 5 | ok | 1 | 1.00 | 0.83 | $0.0653 | [json](runs/7e833fd841be/shipping-391d19718652/trial-5.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-5.diff) |
| A' | tax | 3 | ok | 1 | 1.00 | 0.83 | $0.0623 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-3.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-3.diff) |
| A' | tax | 4 | ok | 1 | 1.00 | 0.83 | $0.0626 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-4.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-4.diff) |
| A' | tax | 5 | ok | 1 | 1.00 | 0.83 | $0.0633 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-5.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-5.diff) |
