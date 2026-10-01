"""Host-session clock: monotonic authority, UTC provenance, injectable suppliers."""
import math
from collections import namedtuple
Stamp = namedtuple("Stamp", "monotonic utc")


def finite(value):
    return type(value) in (int, float) and value >= 0 and not math.isnan(value) and not math.isinf(value)


def deadline(start, duration):
    if not finite(start) or not finite(duration) or duration <= 0 or not finite(start + duration):
        raise ValueError("CLOCK_STATE_INVALID")
    return start + duration


class Clock(object):
    """Owned/read by logical-owner thread. Invalid/regressing readings poison it.

    Inject both zero-argument suppliers in tests. No wall-time fallback, provider
    timestamps or persistence. IronPython uses Stopwatch; CPython monotonic.
    """
    def __init__(self, monotonic=None, utc=None):
        if (monotonic is None) != (utc is None):
            raise ValueError("CLOCK_STATE_INVALID")
        if monotonic is None:
            import sys
            if sys.platform == "cli":
                from System.Diagnostics import Stopwatch
                monotonic = lambda: float(Stopwatch.GetTimestamp()) / Stopwatch.Frequency
            else:
                import time
                monotonic = time.monotonic
            from datetime import datetime
            utc = lambda: datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self._monotonic, self._utc = monotonic, utc
        self._last, self._invalid = None, False

    def sample(self):
        try:
            if self._invalid:
                raise ValueError()
            value, utc = self._monotonic(), self._utc()
            if (not finite(value) or (self._last is not None and value < self._last) or
                    not isinstance(utc, (str, type(u""))) or not 0 < len(utc) <= 256 or
                    any(ord(ch) < 32 for ch in utc)):
                raise ValueError()
            self._last = value
            return Stamp(value, utc)
        except Exception:
            self._invalid = True
            raise ValueError("CLOCK_STATE_INVALID")
