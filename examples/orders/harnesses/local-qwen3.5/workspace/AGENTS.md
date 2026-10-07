# orders-service

Small Python library for order pricing and inventory.

## Team conventions (mandatory)
- Money is always `decimal.Decimal`. Never use `float` values or `float()` for amounts or rates.
- Errors: raise a subclass of `app.errors.OrderError`. Add a new subclass in `app/errors.py`
  when none fits. Never raise built-in exceptions such as `ValueError` or `KeyError`.
- Logging: use the module logger `logger = logging.getLogger(__name__)`. No `print()`,
  no root-logger calls like `logging.info(...)`.
- Every public function and method has full type hints, including the return type.
- Every behaviour change ships with tests in `tests/`. Never edit or delete existing tests.

## Before you finish
Run `python -m pytest -q` and make sure everything passes.
