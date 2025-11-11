# Assignment 3 — Services Refactor and Payment Tests

Author: Mustafa
Date: 2025-11-10

## Purpose
This report documents the restructuring work and test additions performed to satisfy the assignment requirements:

- Move business logic into a `services/` package.
- Add payment-related functions (`pay_late_fees`, `refund_late_fee_payment`) into `services/library_service.py` and make them testable with mocks/stubs.
- Add a simulated external payment gateway implementation `services/payment_service.py` (treated as external; tests should mock it).
- Add tests that use stubs/mocks for database helpers and the payment gateway and raise coverage for `services/` to >= 80%.

## Repository changes (key files)
- `services/library_service.py` — migrated business logic and added payment functions:
  - `pay_late_fees(patron_id, book_id, payment_gateway)`
  - `refund_late_fee_payment(transaction_id, amount, payment_gateway)`
  - Other functions: `add_book_to_catalog`, `borrow_book_by_patron`, `return_book_by_patron`, `calculate_late_fee_for_book`, `search_books_in_catalog`, `get_patron_status_report`.

- `services/payment_service.py` — simulated `PaymentGateway` with `process_payment` and `refund_payment` methods. This module is intended to be mocked in unit tests (low coverage is acceptable and expected).

- `library_service.py` (root) — compatibility shim: `from services.library_service import *` (keeps existing imports working). Note: the repository currently contains a duplicate copy of business logic further down in this file; this was left intentionally to avoid changing behavior unless you request a cleanup.

- `tests/test_payment_mock_stub.py` — tests for payment functions using mocks and stubs.

- `tests/test_services_coverage.py` — additional tests exercising many branches in `services/library_service.py` to raise coverage.

- `requirements.txt` — updated test dependencies (including a working `pytest-mock` pin and `pytest-cov`).

## Why this meets the assignment
- The `services/` package contains `library_service.py` and `payment_service.py` as required.
- The two payment functions requested by the assignment exist in `services/library_service.py` and are written to accept an injected `payment_gateway` object (so tests can easily mock the gateway).
- Imports were updated: code/tests that import `library_service` at project root still work because a shim re-exports the services implementation.

## Test and coverage results (local)
All test and coverage commands below were run from the repository root with the project virtual environment activated.

Example test run (summary):

- pytest summary:
  - 48 passed, 1 xfailed, 3 xpassed

- Coverage (services):
  - `services/library_service.py`: 91%
  - `services/payment_service.py`: 22% (expected — treated as external)
  - TOTAL `services` coverage: 83% (meets the >= 80% requirement)

HTML coverage output written to: `htmlcov/` (open `htmlcov/index.html` locally to view the full report).

## How to reproduce locally
From the repo root (assuming `.a2env` virtualenv is set up):

```bash
# Activate env (example)
source .a2env/bin/activate

# Install dependencies
python -m pip install -r requirements.txt

# Run tests
PYTHONPATH=. pytest --maxfail=1 -q

# Run coverage for services and produce HTML
PYTHONPATH=. pytest --cov=services --cov-report=term --cov-report=html
```

Notes:
- `PYTHONPATH=.` is required in some environments to ensure tests import the local `services` package and the root `library_service.py` shim correctly.
- If you run tests without `PYTHONPATH=.`, pytest may fail to import `services` or `library_service` in some setups.

## Verification performed
- Ran tests and coverage locally on 2025-11-10 using Python 3.13 in `.a2env`.
- Confirmed the two payment functions exist and are importable from `services.library_service` and that the root `library_service` shim imports them.

## Remaining recommendations / next steps
- Clean up root `library_service.py` so it only contains the shim (remove the duplicate business logic) to avoid confusion. I did not remove it automatically to avoid changing files unexpectedly; say "remove duplicate" if you want me to do this and I'll run tests afterwards.

- Optionally, add a short README or developer note describing the `services/` layout and the testing approach.

## Files created/edited in this change
- Created: `A3_report.md` (this report)
- Existing files modified earlier in the session: `services/library_service.py`, `services/payment_service.py`, tests under `tests/`, `requirements.txt`, and `library_service.py` shim.

## Contact / notes
If you want this report exported as a PDF, I can generate one locally and add it to the repo (requires wkhtmltopdf or pandoc if you want a precise layout). Also tell me if you want the root `library_service.py` cleaned to a pure shim.

---
Report generated automatically from the current repository state on 2025-11-10.
