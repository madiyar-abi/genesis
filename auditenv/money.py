"""Money, FX and time helpers. Money is int minor units, rates are Decimal. See CONTRACT §1."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal

EXPONENT = {"USD": 2, "EUR": 2, "GBP": 2, "CHF": 2, "KZT": 2, "JPY": 0}


def convert(amount_minor: int, src: str, tgt: str, rate: Decimal | str) -> int:
    """Convert minor units of `src` to minor units of `tgt`; `rate` = tgt per 1 src (major)."""
    if src == tgt:
        return int(amount_minor)
    value = Decimal(int(amount_minor)).scaleb(-EXPONENT[src]) * Decimal(rate)
    return int(value.scaleb(EXPONENT[tgt]).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def rate_str(value: float) -> str:
    """Format a positive rate as a plain decimal string with 6 significant digits."""
    d = Decimal(repr(value))
    q = Decimal(1).scaleb(d.adjusted() - 5)
    return format(d.quantize(q, rounding=ROUND_HALF_UP), "f")


def parse_offset(offset: str) -> timezone:
    """'+05:00' -> timezone(timedelta(hours=5))."""
    sign = -1 if offset[0] == "-" else 1
    hours, minutes = int(offset[1:3]), int(offset[4:6])
    return timezone(sign * timedelta(hours=hours, minutes=minutes))


def offset_str(minutes: int) -> str:
    sign = "-" if minutes < 0 else "+"
    m = abs(minutes)
    return f"{sign}{m // 60:02d}:{m % 60:02d}"


def iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def parse_ts(ts: str) -> datetime:
    return datetime.fromisoformat(ts)


def local_date(ts: str | datetime, tz: timezone) -> date:
    dt = parse_ts(ts) if isinstance(ts, str) else ts
    return dt.astimezone(tz).date()
