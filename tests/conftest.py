import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from nafas.models import Night, Profile  # noqa: E402

START = date(2026, 1, 1)


def make_nights(usages, start=START, **kw):
    """usages: list of minutes per night (0 = not used). Extra per-night fields via kw lists."""
    out = []
    for i, u in enumerate(usages):
        fields = {k: v[i] for k, v in kw.items()}
        used = u > 0
        out.append(Night(date=start + timedelta(days=i), usage_min=u,
                         ahi=fields.pop("ahi", 1.0 if used else None),
                         leak95_lpm=fields.pop("leak95_lpm", 2.0 if used else None),
                         pressure95=fields.pop("pressure95", 12.0 if used else None),
                         mask_events=fields.pop("mask_events", 1 if used else 0),
                         session_start=fields.pop("session_start", "23:00" if used else None),
                         **fields))
    return out


@pytest.fixture
def profile():
    return Profile(id="t", display_name="Test Person", language="en", goal_hours=4)
