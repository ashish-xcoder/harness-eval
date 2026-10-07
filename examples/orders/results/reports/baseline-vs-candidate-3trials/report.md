# Harness evaluation: orders-service

> **Verdict: INCONCLUSIVE** - No evidence either way at this sample size. Add tasks or trials before deciding.

Exit code 2. no metric moved beyond its confidence interval / noise floor.

## What changed

|  | baseline | candidate |
|---|---|---|
| harness | `baseline` (7e833fd841be) | `candidate` (682bee5bbfb9) |
| agent / model | claude / haiku | claude / haiku |
| runs | 15 | 15 |

```diff
--- baseline/harness.yaml
+++ candidate/harness.yaml
@@ -1,2 +1,3 @@
-# Baseline: today's harness. Claude Code on Haiku, a bare AGENTS.md.
+# Candidate: same agent and model, AGENTS.md now spells out the team conventions
+# and a "run the tests before you finish" rule. This is the change under evaluation.
 agent: claude
--- baseline/workspace/AGENTS.md
+++ candidate/workspace/AGENTS.md
@@ -4,2 +4,12 @@
 
-Run the tests with `python -m pytest -q`.
+## Team conventions (mandatory)
+- Money is always `decimal.Decimal`. Never use `float` values or `float()` for amounts or rates.
+- Errors: raise a subclass of `app.errors.OrderError`. Add a new subclass in `app/errors.py`
+  when none fits. Never raise built-in exceptions such as `ValueError` or `KeyError`.
+- Logging: use the module logger `logger = logging.getLogger(__name__)`. No `print()`,
+  no root-logger calls like `logging.info(...)`.
+- Every public function and method has full type hints, including the return type.
+- Every behaviour change ships with tests in `tests/`. Never edit or delete existing tests.
+
+## Before you finish
+Run `python -m pytest -q` and make sure everything passes.
```

## Scorecard

5 tasks x 3 trials per arm. Delta = candidate - baseline, averaged per task. 95% CI from a task+trial bootstrap. A metric only counts as moved when its CI excludes 0 and the delta beats the A/A noise floor.

| metric | baseline | candidate | delta | 95% CI | noise floor | outcome |
|---|---|---|---|---|---|---|
| Works (existing tests pass) (guardrail) | 1.00 | 1.00 | +0.00 | [0.00, 0.00] | 0.00 | no change |
| Business intent (hidden acceptance tests) (guardrail) | 1.00 | 1.00 | +0.00 | [0.00, 0.00] | 0.00 | no change |
| Team conventions | 0.83 | 0.90 | +0.07 | [0.01, 0.13] | 0.07 | no change |
| Cost per task (USD) | $0.0838 | $0.0935 | +$0.0097 | [$-0.0092, $0.0250] | $0.0212 | no change |
| Tokens per task | 245,458 | 305,137 | +59,679 | [-26,921, 144,583] | 116,941 | no change |
| Wall time per task (s) | 30 | 37 | +7 | [-1, 14] | 14 | no change |

## Per task

Mean per task (works / intent / conventions are 0-1, cost in USD).

| task | works | intent | conventions | cost | tampered runs |
|---|---|---|---|---|---|
| bulk-discount | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.83 | $0.0937 -> $0.0788 | 0 -> 0 |
| coupons | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.94 | $0.0954 -> $0.1195 | 0 -> 0 |
| tax | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.94 | $0.0662 -> $0.0880 | 0 -> 0 |
| reserve-stock | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.89 | $0.0989 -> $0.0972 | 0 -> 0 |
| shipping | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.89 | $0.0648 -> $0.0841 | 0 -> 0 |

## Convention violations

Runs with at least one violation of each rule (lower is better).

| rule | baseline | candidate |
|---|---|---|
| no-print | 0/15 | 0/15 |
| domain-errors | 1/15 | 0/15 |
| decimal-money | 0/15 | 0/15 |
| type-hints | 0/15 | 0/15 |
| module-logger | 0/15 | 0/15 |
| tests-added | 14/15 | 9/15 |

## Can I trust this measurement?

| check | result |
|---|---|
| run status (baseline) | ok: 15 |
| run status (candidate) | ok: 15 |
| isolation | 30/30 Claude runs loaded no plugins, no MCP servers beyond the harness; runs execute outside the user profile after an ancestor CLAUDE.md/AGENTS.md scan |
| test tampering | 0 run(s) edited or deleted existing tests (originals are restored before scoring, so this cannot earn points) |
| hidden tests | copied in only after the agent exited; conftest/ini ignored |
| sample size | 5 tasks x 3 trials per arm (OK) |
| A/A calibration | baseline vs itself gave INCONCLUSIVE (5 tasks x 3 trials); its CI widths are the noise floors in the scorecard |

## Evidence

Every run is a JSON record next to the agent's diff and redacted log. Open the diff of any surprising cell before acting on the verdict.

| arm | task | trial | status | works | intent | conv | cost | record |
|---|---|---|---|---|---|---|---|---|
| baseline | bulk-discount | 0 | ok | 1 | 1.00 | 0.83 | $0.1313 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-0.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-0.diff) |
| baseline | bulk-discount | 1 | ok | 1 | 1.00 | 0.83 | $0.0870 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-1.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-1.diff) |
| baseline | bulk-discount | 2 | ok | 1 | 1.00 | 0.83 | $0.0627 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-2.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-2.diff) |
| baseline | coupons | 0 | ok | 1 | 1.00 | 0.67 | $0.0640 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-0.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-0.diff) |
| baseline | coupons | 1 | ok | 1 | 1.00 | 0.83 | $0.1018 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-1.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-1.diff) |
| baseline | coupons | 2 | ok | 1 | 1.00 | 1.00 | $0.1204 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-2.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-2.diff) |
| baseline | reserve-stock | 0 | ok | 1 | 1.00 | 0.83 | $0.1060 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-0.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-0.diff) |
| baseline | reserve-stock | 1 | ok | 1 | 1.00 | 0.83 | $0.0902 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-1.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-1.diff) |
| baseline | reserve-stock | 2 | ok | 1 | 1.00 | 0.83 | $0.1006 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-2.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-2.diff) |
| baseline | shipping | 0 | ok | 1 | 1.00 | 0.83 | $0.0643 | [json](runs/7e833fd841be/shipping-391d19718652/trial-0.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-0.diff) |
| baseline | shipping | 1 | ok | 1 | 1.00 | 0.83 | $0.0653 | [json](runs/7e833fd841be/shipping-391d19718652/trial-1.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-1.diff) |
| baseline | shipping | 2 | ok | 1 | 1.00 | 0.83 | $0.0647 | [json](runs/7e833fd841be/shipping-391d19718652/trial-2.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-2.diff) |
| baseline | tax | 0 | ok | 1 | 1.00 | 0.83 | $0.0617 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-0.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-0.diff) |
| baseline | tax | 1 | ok | 1 | 1.00 | 0.83 | $0.0689 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-1.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-1.diff) |
| baseline | tax | 2 | ok | 1 | 1.00 | 0.83 | $0.0679 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-2.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-2.diff) |
| candidate | bulk-discount | 0 | ok | 1 | 1.00 | 0.83 | $0.0690 | [json](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-0.json) [diff](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-0.diff) |
| candidate | bulk-discount | 1 | ok | 1 | 1.00 | 0.83 | $0.0932 | [json](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-1.json) [diff](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-1.diff) |
| candidate | bulk-discount | 2 | ok | 1 | 1.00 | 0.83 | $0.0743 | [json](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-2.json) [diff](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-2.diff) |
| candidate | coupons | 0 | ok | 1 | 1.00 | 1.00 | $0.1323 | [json](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-0.json) [diff](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-0.diff) |
| candidate | coupons | 1 | ok | 1 | 1.00 | 0.83 | $0.1007 | [json](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-1.json) [diff](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-1.diff) |
| candidate | coupons | 2 | ok | 1 | 1.00 | 1.00 | $0.1256 | [json](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-2.json) [diff](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-2.diff) |
| candidate | reserve-stock | 0 | ok | 1 | 1.00 | 0.83 | $0.0994 | [json](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-0.json) [diff](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-0.diff) |
| candidate | reserve-stock | 1 | ok | 1 | 1.00 | 0.83 | $0.0863 | [json](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-1.json) [diff](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-1.diff) |
| candidate | reserve-stock | 2 | ok | 1 | 1.00 | 1.00 | $0.1058 | [json](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-2.json) [diff](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-2.diff) |
| candidate | shipping | 0 | ok | 1 | 1.00 | 1.00 | $0.1011 | [json](runs/682bee5bbfb9/shipping-391d19718652/trial-0.json) [diff](runs/682bee5bbfb9/shipping-391d19718652/trial-0.diff) |
| candidate | shipping | 1 | ok | 1 | 1.00 | 0.83 | $0.0764 | [json](runs/682bee5bbfb9/shipping-391d19718652/trial-1.json) [diff](runs/682bee5bbfb9/shipping-391d19718652/trial-1.diff) |
| candidate | shipping | 2 | ok | 1 | 1.00 | 0.83 | $0.0746 | [json](runs/682bee5bbfb9/shipping-391d19718652/trial-2.json) [diff](runs/682bee5bbfb9/shipping-391d19718652/trial-2.diff) |
| candidate | tax | 0 | ok | 1 | 1.00 | 1.00 | $0.0947 | [json](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-0.json) [diff](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-0.diff) |
| candidate | tax | 1 | ok | 1 | 1.00 | 1.00 | $0.0962 | [json](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-1.json) [diff](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-1.diff) |
| candidate | tax | 2 | ok | 1 | 1.00 | 0.83 | $0.0730 | [json](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-2.json) [diff](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-2.diff) |
