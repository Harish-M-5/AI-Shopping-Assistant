"""Parse Manufacturing / Expiry dates out of raw OCR text.

Handles labels such as MFD, MFG, PKD, "Manufactured on", EXP, "Use by",
"Best before" and formats like 12/03/2026, 12-03-26, 12 MAR 2026, MAR 2026,
03/2026. Day-first ordering (DD/MM/YYYY) is assumed when ambiguous.
Pure Python - no heavy dependencies, so it is easy to unit-test.
"""
import calendar
import re
from datetime import date, timedelta
from typing import Optional

MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}

MFG_KEYS = r"(?:mfd|mfg|mfr|manufactur\w*|pkd|packed(?:\s+on)?|packaging\s+date|prod(?:uction)?\.?\s*date|made\s+on)"
EXP_KEYS = r"(?:exp\w*|use\s*by|best\s*before|best\s*by|bb|bbe)"
KEY_RE = re.compile(rf"(?P<mfg>{MFG_KEYS})|(?P<exp>{EXP_KEYS})", re.I)

# Ordered from most to least specific. Each yields d/m/y groups.
DATE_PATTERNS = [
    re.compile(r"(?P<d>\d{1,2})[\s./\-]{1,3}(?P<m>\d{1,2})[\s./\-]{1,3}(?P<y>\d{4}|\d{2})\b"),
    re.compile(r"(?P<d>\d{1,2})\s*[ ./\-]?\s*(?P<mon>[A-Za-z]{3,9})\.?[ ./,\-]*(?P<y>\d{4}|\d{2})\b"),
    re.compile(r"\b(?P<mon>[A-Za-z]{3,9})\.?[ ./,\-]*(?P<y>\d{4})\b"),
    re.compile(r"\b(?P<m>\d{1,2})\s*[/\-.]\s*(?P<y>\d{4})\b"),
]
DURATION_RE = re.compile(r"(\d{1,2})\s*(day|week|month|year)s?", re.I)


def _year(y: str) -> int:
    return int(y) if len(y) == 4 else 2000 + int(y)


def _to_date(g: dict, end_of_month: bool) -> Optional[date]:
    """Convert regex groups into a date, or None if invalid."""
    try:
        y = _year(g["y"])
        if g.get("mon"):
            m = MONTHS.get(g["mon"][:3].lower())
            if not m:
                return None
        else:
            m = int(g["m"])
        d = int(g["d"]) if g.get("d") else None
        if d is not None and m > 12 >= d:  # looks like MM/DD -> swap
            d, m = m, d
        if not 1 <= m <= 12 or not 2000 <= y <= 2100:
            return None
        if d is None:
            d = calendar.monthrange(y, m)[1] if end_of_month else 1
        return date(y, m, d)
    except (ValueError, KeyError):
        return None


def _find_dates(text: str) -> list[tuple[int, int, dict]]:
    """Return non-overlapping (start, end, groups) matches, most specific first."""
    taken: list[tuple[int, int, dict]] = []
    for pat in DATE_PATTERNS:
        for m in pat.finditer(text):
            s, e = m.span()
            if any(s < te and e > ts for ts, te, _ in taken):
                continue
            g = m.groupdict()
            if g.get("mon") and g["mon"][:3].lower() not in MONTHS:
                continue
            taken.append((s, e, g))
    return sorted(taken, key=lambda t: t[0])


def _add_duration(start: date, n: int, unit: str) -> date:
    unit = unit.lower()
    if unit == "day":
        return start + timedelta(days=n)
    if unit == "week":
        return start + timedelta(weeks=n)
    months = n * (12 if unit == "year" else 1)
    idx = start.month - 1 + months
    y, m = start.year + idx // 12, idx % 12 + 1
    return date(y, m, min(start.day, calendar.monthrange(y, m)[1]))


def extract_dates(text: str, today: Optional[date] = None) -> dict:
    """Return manufacturing/expiry dates (ISO strings) plus an expiry status."""
    today = today or date.today()
    mfg: Optional[date] = None
    exp: Optional[date] = None
    unlabeled: list[date] = []

    for start, _end, g in _find_dates(text):
        # Label = the keyword closest *before* the date (within 30 chars).
        window = text[max(0, start - 30):start]
        keys = list(KEY_RE.finditer(window))
        kind = None
        if keys:
            kind = "mfg" if keys[-1].group("mfg") else "exp"
        d = _to_date(g, end_of_month=(kind != "mfg"))
        if d is None:
            continue
        if kind == "mfg" and mfg is None:
            mfg = d
        elif kind == "exp" and exp is None:
            exp = d
        elif kind is None:
            unlabeled.append(d)

    # No labels at all: earliest = manufacturing, latest = expiry.
    if mfg is None and exp is None and len(unlabeled) >= 2:
        unlabeled.sort()
        mfg, exp, unlabeled = unlabeled[0], unlabeled[-1], unlabeled[1:-1]

    # "Best before 6 months from manufacture" style relative expiry.
    if exp is None and mfg is not None:
        rel = re.search(rf"(?:{EXP_KEYS})[^0-9]{{0,25}}{DURATION_RE.pattern}", text, re.I)
        if rel:
            n, unit = int(rel.group(1)), rel.group(2)
            exp = _add_duration(mfg, n, unit)

    status, days_left = "unknown", None
    if exp:
        days_left = (exp - today).days
        status = "expired" if days_left < 0 else "expiring_soon" if days_left <= 30 else "ok"

    return {
        "manufacturing_date": mfg.isoformat() if mfg else None,
        "expiry_date": exp.isoformat() if exp else None,
        "unlabeled_dates": [d.isoformat() for d in unlabeled],
        "status": status,
        "days_left": days_left,
    }
