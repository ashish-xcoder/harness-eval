"""Replay harnesses: deterministic fake agents that apply a canned solution per task.

    good    complete, convention-following solution + a new test
    bad     same, but subtotal is off by a cent -> the repo's own tests fail
    sloppy  correct behaviour, but print / ValueError / float / no type hints / no tests
    tamper  'bad' + deletes an existing test it would fail (must not earn points)
"""

import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "examples" / "orders"
SOLUTION = Path(__file__).parent / "fixtures" / "solution"

SLOPPY_PRICING_TAIL = '''

def shipping_cost(order, express=False):
    print("computing shipping")
    cost = 0.0 if subtotal(order) >= Decimal("50.00") else Decimal("5.99")
    return Decimal(cost) + (Decimal("10.00") if express else Decimal("0"))


def apply_coupon(order, code):
    amount = subtotal(order)
    if code == "SAVE10":
        return to_cents(amount * Decimal("0.9"))
    if code == "FLAT5":
        return max(amount - Decimal("5.00"), Decimal("0.00"))
    raise ValueError(code)
'''


@pytest.fixture(autouse=True)
def _workdir(tmp_path, monkeypatch):
    monkeypatch.setenv("HARNESS_EVAL_WORKDIR", str(tmp_path / "runs"))


@pytest.fixture
def suite_dir(tmp_path) -> Path:
    dst = tmp_path / "suite"
    shutil.copytree(SUITE, dst, ignore=shutil.ignore_patterns("results", "__pycache__"))
    return dst


def make_harness(base: Path, name: str, variant: str = "good", cost: float = 0.01) -> Path:
    root = base / name
    (root / "workspace").mkdir(parents=True)
    (root / "workspace" / "AGENTS.md").write_text(f"# {name}\n", encoding="utf-8")
    (root / "harness.yaml").write_text(f"agent: replay\ncost_usd: {cost}\n", encoding="utf-8")
    for task in ("bulk-discount", "coupons", "tax", "reserve-stock", "shipping"):
        dst = root / "replay" / task
        shutil.copytree(SOLUTION, dst)
        pricing = dst / "app" / "pricing.py"
        if variant in ("bad", "tamper"):
            text = pricing.read_text(encoding="utf-8")
            pricing.write_text(text.replace("return to_cents(total)\n\n\ndef apply_coupon",
                                            "return to_cents(total) + CENT\n\n\ndef apply_coupon"),
                               encoding="utf-8")
        if variant == "sloppy":
            (dst / "tests").joinpath("test_new_features.py").unlink()
            text = pricing.read_text(encoding="utf-8")
            text = text.split("\n\ndef apply_coupon")[0] + SLOPPY_PRICING_TAIL + (
                "\n\ndef tax(order: Order) -> Decimal:\n"
                "    return to_cents(subtotal(order) * TAX_RATES.get(order.region, Decimal(\"0\")))\n")
            pricing.write_text(text, encoding="utf-8")
        if variant == "tamper":
            test = (SUITE / "repo" / "tests" / "test_pricing.py").read_text(encoding="utf-8")
            kept = test.split("def test_subtotal_sums_lines")[0]
            kept += "def test_empty_order_subtotal_is_zero():\n    assert True\n"
            (dst / "tests" / "test_pricing.py").write_text(kept, encoding="utf-8")
    return root
