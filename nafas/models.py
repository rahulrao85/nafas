"""Core data types. Every source (ResMed EDF, CSV, JSON, synthetic) is normalised to `Night`."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date


@dataclass
class Night:
    """One therapy night, dated by the evening it started."""
    date: date
    usage_min: float | None = 0.0        # minutes of mask-on time; 0 = not used (None only before data checks)
    ahi: float | None = None             # apnoea-hypopnoea index, events/hour
    leak95_lpm: float | None = None      # 95th-percentile leak, L/min
    pressure95: float | None = None      # 95th-percentile pressure, cmH2O
    mask_events: int | None = None       # mask-on sessions in the night (1 = slept through)
    session_start: str | None = None     # "HH:MM" local time the first session began
    wearable_sleep_min: float | None = None  # optional: sleep a watch/ring saw, CPAP or not
    wearable_rhr: float | None = None        # optional: resting heart rate, bpm (wellness estimate)
    wearable_hrv_ms: float | None = None     # optional: overnight HRV, ms (wellness estimate)
    wearable_source: str | None = None       # which device the wearable fields came from

    def to_dict(self) -> dict:
        d = asdict(self)
        d["date"] = self.date.isoformat()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Night":
        d = dict(d)
        d["date"] = date.fromisoformat(d["date"])
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class CheckIn:
    """A one-tap self-report: what got in the way (or a note)."""
    date: date
    barrier: str
    note: str = ""

    def to_dict(self) -> dict:
        return {"date": self.date.isoformat(), "barrier": self.barrier, "note": self.note}

    @classmethod
    def from_dict(cls, d: dict) -> "CheckIn":
        return cls(date=date.fromisoformat(d["date"]), barrier=d["barrier"], note=d.get("note", ""))


@dataclass
class Profile:
    """User-controlled settings. Nothing here is shared unless `share_with_care_team` is on."""
    id: str
    display_name: str
    language: str = "en"                 # "en" | "ar"
    goal_hours: float = 4.0              # nightly goal; 4 h matches common adherence definitions
    mask_type: str = "nasal"
    max_pressure: float = 20.0
    nudges_enabled: bool = True
    nudge_hour: int = 21                 # local hour for the evening nudge
    quiet_start: int = 23
    quiet_end: int = 7
    share_with_care_team: bool = False
    use_llm: bool = True
    notes: str = ""
    tags: dict = field(default_factory=dict)  # cohort attributes for equity breakdowns

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Profile":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})
