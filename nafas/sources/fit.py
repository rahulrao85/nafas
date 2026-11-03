"""Garmin FIT files: sleep stages, overnight HRV and resting heart rate.

Decoded with `fitdecode`. Fields are matched by their FIT message/field *numbers*, so files from devices
newer than the library's profile still parse. The `file_id` message (which holds the watch serial) is
never read. All values are consumer wellness estimates.

FIT messages used (FIT SDK numbering):
  275 sleep_level            253 timestamp, 0 sleep_level (0 unmeasurable, 1 awake, 2 light, 3 deep, 4 rem)
  370 hrv_status_summary     253 timestamp, 1 last_night_average (uint16, /128 → ms)
  211 monitoring_hr_data     253 timestamp, 0 resting_heart_rate, 1 current_day_resting_heart_rate (bpm)
  162 timestamp_correlation  253 timestamp, 3 local_timestamp (gives the device's UTC offset)
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

FIT_EPOCH = datetime(1989, 12, 31, tzinfo=timezone.utc)
ASLEEP = {2, 3, 4}
GAP_SPLIT = timedelta(hours=3)


def is_fit(head: bytes) -> bool:
    return len(head) >= 12 and head[8:12] == b".FIT"


def _ts(raw) -> datetime | None:
    return FIT_EPOCH + timedelta(seconds=int(raw)) if isinstance(raw, int) and raw > 0 else None


def _fields(frame) -> dict[int, object]:
    return {f.def_num: f.raw_value for f in frame.fields}


def night_of(local: datetime):
    """The night a moment belongs to: the evening date (noon-to-noon day)."""
    return (local - timedelta(hours=12)).date()


def parse(data: bytes, tz_offset_min: int = 0) -> dict:
    """Return {"sleep": {night: minutes}, "hrv": {night: ms}, "rhr": {night: bpm}}."""
    import fitdecode

    levels: list[tuple[datetime, int]] = []
    hrv: list[tuple[datetime, float]] = []
    rhr: list[tuple[datetime, float]] = []
    offset = None
    with fitdecode.FitReader(io.BytesIO(data), check_crc=fitdecode.CrcCheck.RAISE) as fr:
        for frame in fr:
            if frame.frame_type != fitdecode.FIT_FRAME_DATA:
                continue
            num, f = frame.global_mesg_num, _fields(frame)
            ts = _ts(f.get(253))
            if num == 162 and ts and isinstance(f.get(3), int):
                offset = timedelta(seconds=int(f[3])) - timedelta(seconds=int(f[253]))
            elif num == 275 and ts and isinstance(f.get(0), int):
                levels.append((ts, f[0]))
            elif num == 370 and ts and isinstance(f.get(1), int) and f[1] not in (0, 0xFFFF):
                hrv.append((ts, f[1] / 128.0))
            elif num == 211 and ts:
                v = f.get(1) if isinstance(f.get(1), int) and f.get(1) not in (0, 0xFF) else f.get(0)
                if isinstance(v, int) and 0 < v < 0xFF:
                    rhr.append((ts, float(v)))

    off = offset if offset is not None else timedelta(minutes=tz_offset_min)
    out = {"sleep": {}, "hrv": {}, "rhr": {}}
    levels.sort()
    block_night = None
    for i, (ts, lvl) in enumerate(levels):
        nxt = levels[i + 1][0] if i + 1 < len(levels) else ts + timedelta(seconds=60)
        dur = nxt - ts
        if dur > GAP_SPLIT or dur.total_seconds() <= 0:     # gap: this sample closes its block
            dur = timedelta(seconds=60)
        if block_night is None or (i and ts - levels[i - 1][0] > GAP_SPLIT):
            block_night = night_of(ts + off)
        if lvl in ASLEEP:
            out["sleep"][block_night] = out["sleep"].get(block_night, 0.0) + dur.total_seconds() / 60
    for ts, v in hrv:
        out["hrv"][night_of(ts + off)] = round(v, 1)
    for ts, v in rhr:
        out["rhr"][night_of(ts + off)] = v
    out["sleep"] = {k: round(v) for k, v in out["sleep"].items()}
    return out
