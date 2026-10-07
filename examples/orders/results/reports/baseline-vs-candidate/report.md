# Harness evaluation: orders-service

> **Verdict: INCONCLUSIVE** - No evidence either way at this sample size. Add tasks or trials before deciding.

Exit code 2. no metric moved beyond its confidence interval / noise floor.

## What changed

|  | baseline | candidate |
|---|---|---|
| harness | `baseline` (7e833fd841be) | `candidate` (682bee5bbfb9) |
| agent / model | claude / haiku | claude / haiku |
| runs | 30 | 30 |

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

5 tasks x 6 trials per arm. Delta = candidate - baseline, averaged per task. 95% CI from a task+trial bootstrap. A metric only counts as moved when its CI excludes 0 and the delta beats the A/A noise floor.

| metric | baseline | candidate | delta | 95% CI | noise floor | outcome |
|---|---|---|---|---|---|---|
| Works (existing tests pass) (guardrail) | 1.00 | 1.00 | +0.00 | [0.00, 0.00] | 0.00 | no change |
| Business intent (hidden acceptance tests) (guardrail) | 1.00 | 0.99 | -0.01 | [-0.03, 0.00] | 0.00 | no change |
| Team conventions | 0.84 | 0.90 | +0.06 | [0.02, 0.11] | 0.07 | no change |
| Cost per task (USD) | $0.0830 | $0.0932 | +$0.0102 | [$-0.0009, $0.0208] | $0.0212 | no change |
| Tokens per task | 248,082 | 305,134 | +57,052 | [-19,891, 124,620] | 116,941 | no change |
| Wall time per task (s) | 31 | 36 | +4 | [-1, 10] | 14 | no change |

## Per task

Mean per task (works / intent / conventions are 0-1, cost in USD).

| task | works | intent | conventions | cost | tampered runs |
|---|---|---|---|---|---|
| bulk-discount | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.86 | $0.0780 -> $0.0843 | 0 -> 0 |
| coupons | 1.00 -> 1.00 | 1.00 -> 0.97 | 0.86 -> 0.97 | $0.1094 -> $0.1174 | 0 -> 0 |
| tax | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.92 | $0.0645 -> $0.0873 | 0 -> 0 |
| reserve-stock | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.86 | $0.0971 -> $0.0934 | 0 -> 0 |
| shipping | 1.00 -> 1.00 | 1.00 -> 1.00 | 0.83 -> 0.89 | $0.0660 -> $0.0837 | 0 -> 0 |

## Convention violations

Runs with at least one violation of each rule (lower is better).

| rule | baseline | candidate |
|---|---|---|
| no-print | 0/30 | 0/30 |
| domain-errors | 1/30 | 0/30 |
| decimal-money | 0/30 | 0/30 |
| type-hints | 0/30 | 0/30 |
| module-logger | 0/30 | 0/30 |
| tests-added | 28/30 | 18/30 |

## Can I trust this measurement?

| check | result |
|---|---|
| run status (baseline) | ok: 30 |
| run status (candidate) | ok: 30 |
| isolation | 60/60 Claude runs loaded no plugins, no MCP servers beyond the harness; runs execute outside the user profile after an ancestor CLAUDE.md/AGENTS.md scan |
| test tampering | 0 run(s) edited or deleted existing tests (originals are restored before scoring, so this cannot earn points) |
| hidden tests | copied in only after the agent exited; conftest/ini ignored |
| sample size | 5 tasks x 6 trials per arm (OK) |
| A/A calibration | baseline vs itself gave INCONCLUSIVE (5 tasks x 3 trials); its CI widths are the noise floors in the scorecard |

## Evidence

Every run is a JSON record next to the agent's diff and redacted log. Open the diff of any surprising cell before acting on the verdict.

| arm | task | trial | status | works | intent | conv | cost | record |
|---|---|---|---|---|---|---|---|---|
| baseline | bulk-discount | 0 | ok | 1 | 1.00 | 0.83 | $0.1313 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-0.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-0.diff) |
| baseline | bulk-discount | 1 | ok | 1 | 1.00 | 0.83 | $0.0870 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-1.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-1.diff) |
| baseline | bulk-discount | 2 | ok | 1 | 1.00 | 0.83 | $0.0627 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-2.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-2.diff) |
| baseline | bulk-discount | 3 | ok | 1 | 1.00 | 0.83 | $0.0625 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-3.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-3.diff) |
| baseline | bulk-discount | 4 | ok | 1 | 1.00 | 0.83 | $0.0619 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-4.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-4.diff) |
| baseline | bulk-discount | 5 | ok | 1 | 1.00 | 0.83 | $0.0627 | [json](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-5.json) [diff](runs/7e833fd841be/bulk-discount-8231c8d52d44/trial-5.diff) |
| baseline | coupons | 0 | ok | 1 | 1.00 | 0.67 | $0.0640 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-0.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-0.diff) |
| baseline | coupons | 1 | ok | 1 | 1.00 | 0.83 | $0.1018 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-1.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-1.diff) |
| baseline | coupons | 2 | ok | 1 | 1.00 | 1.00 | $0.1204 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-2.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-2.diff) |
| baseline | coupons | 3 | ok | 1 | 1.00 | 1.00 | $0.1360 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-3.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-3.diff) |
| baseline | coupons | 4 | ok | 1 | 1.00 | 0.83 | $0.1282 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-4.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-4.diff) |
| baseline | coupons | 5 | ok | 1 | 1.00 | 0.83 | $0.1058 | [json](runs/7e833fd841be/coupons-cc47a6a3c067/trial-5.json) [diff](runs/7e833fd841be/coupons-cc47a6a3c067/trial-5.diff) |
| baseline | reserve-stock | 0 | ok | 1 | 1.00 | 0.83 | $0.1060 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-0.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-0.diff) |
| baseline | reserve-stock | 1 | ok | 1 | 1.00 | 0.83 | $0.0902 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-1.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-1.diff) |
| baseline | reserve-stock | 2 | ok | 1 | 1.00 | 0.83 | $0.1006 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-2.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-2.diff) |
| baseline | reserve-stock | 3 | ok | 1 | 1.00 | 0.83 | $0.0941 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-3.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-3.diff) |
| baseline | reserve-stock | 4 | ok | 1 | 1.00 | 0.83 | $0.0963 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-4.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-4.diff) |
| baseline | reserve-stock | 5 | ok | 1 | 1.00 | 0.83 | $0.0957 | [json](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-5.json) [diff](runs/7e833fd841be/reserve-stock-2eabd626aece/trial-5.diff) |
| baseline | shipping | 0 | ok | 1 | 1.00 | 0.83 | $0.0643 | [json](runs/7e833fd841be/shipping-391d19718652/trial-0.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-0.diff) |
| baseline | shipping | 1 | ok | 1 | 1.00 | 0.83 | $0.0653 | [json](runs/7e833fd841be/shipping-391d19718652/trial-1.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-1.diff) |
| baseline | shipping | 2 | ok | 1 | 1.00 | 0.83 | $0.0647 | [json](runs/7e833fd841be/shipping-391d19718652/trial-2.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-2.diff) |
| baseline | shipping | 3 | ok | 1 | 1.00 | 0.83 | $0.0703 | [json](runs/7e833fd841be/shipping-391d19718652/trial-3.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-3.diff) |
| baseline | shipping | 4 | ok | 1 | 1.00 | 0.83 | $0.0660 | [json](runs/7e833fd841be/shipping-391d19718652/trial-4.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-4.diff) |
| baseline | shipping | 5 | ok | 1 | 1.00 | 0.83 | $0.0653 | [json](runs/7e833fd841be/shipping-391d19718652/trial-5.json) [diff](runs/7e833fd841be/shipping-391d19718652/trial-5.diff) |
| baseline | tax | 0 | ok | 1 | 1.00 | 0.83 | $0.0617 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-0.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-0.diff) |
| baseline | tax | 1 | ok | 1 | 1.00 | 0.83 | $0.0689 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-1.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-1.diff) |
| baseline | tax | 2 | ok | 1 | 1.00 | 0.83 | $0.0679 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-2.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-2.diff) |
| baseline | tax | 3 | ok | 1 | 1.00 | 0.83 | $0.0623 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-3.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-3.diff) |
| baseline | tax | 4 | ok | 1 | 1.00 | 0.83 | $0.0626 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-4.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-4.diff) |
| baseline | tax | 5 | ok | 1 | 1.00 | 0.83 | $0.0633 | [json](runs/7e833fd841be/tax-1af12c3c5ad1/trial-5.json) [diff](runs/7e833fd841be/tax-1af12c3c5ad1/trial-5.diff) |
| candidate | bulk-discount | 0 | ok | 1 | 1.00 | 0.83 | $0.0690 | [json](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-0.json) [diff](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-0.diff) |
| candidate | bulk-discount | 1 | ok | 1 | 1.00 | 0.83 | $0.0932 | [json](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-1.json) [diff](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-1.diff) |
| candidate | bulk-discount | 2 | ok | 1 | 1.00 | 0.83 | $0.0743 | [json](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-2.json) [diff](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-2.diff) |
| candidate | bulk-discount | 3 | ok | 1 | 1.00 | 1.00 | $0.0945 | [json](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-3.json) [diff](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-3.diff) |
| candidate | bulk-discount | 4 | ok | 1 | 1.00 | 0.83 | $0.0898 | [json](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-4.json) [diff](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-4.diff) |
| candidate | bulk-discount | 5 | ok | 1 | 1.00 | 0.83 | $0.0852 | [json](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-5.json) [diff](runs/682bee5bbfb9/bulk-discount-8231c8d52d44/trial-5.diff) |
| candidate | coupons | 0 | ok | 1 | 1.00 | 1.00 | $0.1323 | [json](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-0.json) [diff](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-0.diff) |
| candidate | coupons | 1 | ok | 1 | 1.00 | 0.83 | $0.1007 | [json](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-1.json) [diff](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-1.diff) |
| candidate | coupons | 2 | ok | 1 | 1.00 | 1.00 | $0.1256 | [json](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-2.json) [diff](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-2.diff) |
| candidate | coupons | 3 | ok | 1 | 0.80 | 1.00 | $0.0968 | [json](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-3.json) [diff](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-3.diff) |
| candidate | coupons | 4 | ok | 1 | 1.00 | 1.00 | $0.1357 | [json](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-4.json) [diff](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-4.diff) |
| candidate | coupons | 5 | ok | 1 | 1.00 | 1.00 | $0.1135 | [json](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-5.json) [diff](runs/682bee5bbfb9/coupons-cc47a6a3c067/trial-5.diff) |
| candidate | reserve-stock | 0 | ok | 1 | 1.00 | 0.83 | $0.0994 | [json](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-0.json) [diff](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-0.diff) |
| candidate | reserve-stock | 1 | ok | 1 | 1.00 | 0.83 | $0.0863 | [json](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-1.json) [diff](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-1.diff) |
| candidate | reserve-stock | 2 | ok | 1 | 1.00 | 1.00 | $0.1058 | [json](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-2.json) [diff](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-2.diff) |
| candidate | reserve-stock | 3 | ok | 1 | 1.00 | 0.83 | $0.1045 | [json](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-3.json) [diff](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-3.diff) |
| candidate | reserve-stock | 4 | ok | 1 | 1.00 | 0.83 | $0.0780 | [json](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-4.json) [diff](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-4.diff) |
| candidate | reserve-stock | 5 | ok | 1 | 1.00 | 0.83 | $0.0866 | [json](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-5.json) [diff](runs/682bee5bbfb9/reserve-stock-2eabd626aece/trial-5.diff) |
| candidate | shipping | 0 | ok | 1 | 1.00 | 1.00 | $0.1011 | [json](runs/682bee5bbfb9/shipping-391d19718652/trial-0.json) [diff](runs/682bee5bbfb9/shipping-391d19718652/trial-0.diff) |
| candidate | shipping | 1 | ok | 1 | 1.00 | 0.83 | $0.0764 | [json](runs/682bee5bbfb9/shipping-391d19718652/trial-1.json) [diff](runs/682bee5bbfb9/shipping-391d19718652/trial-1.diff) |
| candidate | shipping | 2 | ok | 1 | 1.00 | 0.83 | $0.0746 | [json](runs/682bee5bbfb9/shipping-391d19718652/trial-2.json) [diff](runs/682bee5bbfb9/shipping-391d19718652/trial-2.diff) |
| candidate | shipping | 3 | ok | 1 | 1.00 | 0.83 | $0.0693 | [json](runs/682bee5bbfb9/shipping-391d19718652/trial-3.json) [diff](runs/682bee5bbfb9/shipping-391d19718652/trial-3.diff) |
| candidate | shipping | 4 | ok | 1 | 1.00 | 1.00 | $0.1085 | [json](runs/682bee5bbfb9/shipping-391d19718652/trial-4.json) [diff](runs/682bee5bbfb9/shipping-391d19718652/trial-4.diff) |
| candidate | shipping | 5 | ok | 1 | 1.00 | 0.83 | $0.0722 | [json](runs/682bee5bbfb9/shipping-391d19718652/trial-5.json) [diff](runs/682bee5bbfb9/shipping-391d19718652/trial-5.diff) |
| candidate | tax | 0 | ok | 1 | 1.00 | 1.00 | $0.0947 | [json](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-0.json) [diff](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-0.diff) |
| candidate | tax | 1 | ok | 1 | 1.00 | 1.00 | $0.0962 | [json](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-1.json) [diff](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-1.diff) |
| candidate | tax | 2 | ok | 1 | 1.00 | 0.83 | $0.0730 | [json](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-2.json) [diff](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-2.diff) |
| candidate | tax | 3 | ok | 1 | 1.00 | 0.83 | $0.0900 | [json](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-3.json) [diff](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-3.diff) |
| candidate | tax | 4 | ok | 1 | 1.00 | 0.83 | $0.0757 | [json](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-4.json) [diff](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-4.diff) |
| candidate | tax | 5 | ok | 1 | 1.00 | 1.00 | $0.0940 | [json](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-5.json) [diff](runs/682bee5bbfb9/tax-1af12c3c5ad1/trial-5.diff) |
