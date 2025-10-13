# CISC327 Assignment 2 — Library Management System

**Repository:** [https://github.com/Musdaf-Hirsi/cisc327-library-management-a2-6847](https://github.com/Musdaf-Hirsi/cisc327-library-management-a2-6847)

[![Tests](https://github.com/Musdaf-Hirsi/cisc327-library-management-a2-6847/actions/workflows/python-app.yml/badge.svg)](https://github.com/Musdaf-Hirsi/cisc327-library-management-a2-6847/actions)

This repository contains my completed implementation for **Assignment 2: Library Management System** in **CISC 327 (Software Quality Assurance)**.

---

## Project Structure

- `library_service.py` – main business logic (R1–R7)
- `database.py` – SQLite helper functions and sample data
- `tests/` – pytest test suite (instructor + added cases)
- `.github/workflows/python-app.yml` – CI workflow for automated testing
- `requirements.txt` – dependencies

---

## ▶Run Tests Locally

```bash
# 1. Create and activate the virtual environment
python3 -m venv .a2env
source .a2env/bin/activate

# 2. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Run all tests
python -m pytest -q
