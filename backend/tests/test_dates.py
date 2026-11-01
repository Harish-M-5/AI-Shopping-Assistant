"""Run with:  cd backend && pytest -q"""
from datetime import date

from app.services.dates import extract_dates

TODAY = date(2026, 10, 31)


def test_labeled_numeric_dates():
    r = extract_dates("MFD: 12/03/2026 EXP: 11/03/2027", today=TODAY)
    assert r["manufacturing_date"] == "2026-03-12"
    assert r["expiry_date"] == "2027-03-11"
    assert r["status"] == "ok"


def test_month_names_and_expired():
    r = extract_dates("MFG 05 JAN 2024  BEST BEFORE 05 JUL 2024", today=TODAY)
    assert r["manufacturing_date"] == "2024-01-05"
    assert r["expiry_date"] == "2024-07-05"
    assert r["status"] == "expired"


def test_month_year_only_expiry_is_end_of_month():
    r = extract_dates("PKD 03/2026 EXP 11/2026", today=TODAY)
    assert r["expiry_date"] == "2026-11-30"
    assert r["status"] == "expiring_soon"


def test_unlabeled_two_dates():
    r = extract_dates("10-02-2026 09-02-2027", today=TODAY)
    assert r["manufacturing_date"] == "2026-02-10"
    assert r["expiry_date"] == "2027-02-09"


def test_relative_best_before():
    r = extract_dates("MFD 01/09/2026 best before 6 months from manufacture", today=TODAY)
    assert r["expiry_date"] == "2027-03-01"


def test_no_dates():
    assert extract_dates("fresh organic apples", today=TODAY)["status"] == "unknown"
