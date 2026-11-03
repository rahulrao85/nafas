"""Safe handling of uploaded files and zip archives, all in memory (nothing is written to disk).

Guards: a byte budget per upload, per-member size cap, compression-ratio check (zip bombs), member
count cap, nested-zip depth cap, no encrypted members, and no absolute or `..` paths.
"""

from __future__ import annotations

import io
import posixpath
import zipfile
from dataclasses import dataclass
from typing import Callable, Iterator

MAX_TOTAL_BYTES = 1024 * 1024 * 1024     # decompressed bytes read per upload
MAX_MEMBER_BYTES = 512 * 1024 * 1024     # one file (an Apple Health export.xml can be large)
MAX_MEMBERS = 20000
MAX_RATIO = 200                          # uncompressed / compressed, for members over 10 MB
MAX_DEPTH = 2                            # a zip inside a zip inside the upload


class BudgetExceeded(Exception):
    pass


class Budget:
    def __init__(self, limit: int | None = None):
        self.limit, self.used = (limit if limit is not None else MAX_TOTAL_BYTES), 0

    def take(self, n: int) -> None:
        self.used += n
        if self.used > self.limit:
            raise BudgetExceeded("This upload unpacks to more than 1 GB; split it into smaller parts.")


@dataclass
class Entry:
    path: str                        # display path, e.g. "card.zip/STR.edf"
    size: int
    _open: Callable[[], io.BufferedIOBase]
    depth: int = 0

    @property
    def name(self) -> str:
        return posixpath.basename(self.path.replace("\\", "/"))

    def open(self):
        return self._open()

    def read(self, budget: Budget, limit: int = MAX_MEMBER_BYTES) -> bytes:
        with self.open() as f:
            out = bytearray()
            while True:
                chunk = f.read(1 << 20)
                if not chunk:
                    break
                out += chunk
                budget.take(len(chunk))
                if len(out) > limit:
                    raise BudgetExceeded(f"{self.name} is larger than {limit // (1024 * 1024)} MB.")
        return bytes(out)

    def head(self, n: int = 64) -> bytes:
        with self.open() as f:
            return f.read(n)


def from_bytes(path: str, data: bytes) -> Entry:
    return Entry(path, len(data), lambda: io.BytesIO(data))


def safe_member_path(name: str) -> str | None:
    p = name.replace("\\", "/")
    if p.startswith("/") or (len(p) > 1 and p[1] == ":"):
        return None
    norm = posixpath.normpath(p)
    if norm.startswith("..") or "/../" in f"/{norm}/":
        return None
    return norm


def is_zip(entry: Entry) -> bool:
    return entry.name.lower().endswith(".zip") or entry.head(4) == b"PK\x03\x04"


def expand(entry: Entry, budget: Budget, skipped: list) -> Iterator[Entry]:
    """Yield the entry, or, for a zip, its safe members (recursively, up to MAX_DEPTH)."""
    if not is_zip(entry):
        yield entry
        return
    if entry.depth >= MAX_DEPTH:
        skipped.append({"file": entry.path, "reason": "zip_nested"})
        return
    try:
        data = entry.read(budget)
        zf = zipfile.ZipFile(io.BytesIO(data))
        infos = zf.infolist()
    except (zipfile.BadZipFile, BudgetExceeded) as e:
        skipped.append({"file": entry.path, "reason": "zip_bad", "detail": str(e)[:120]})
        return
    if len(infos) > MAX_MEMBERS:
        skipped.append({"file": entry.path, "reason": "zip_too_many"})
        return
    for info in infos:
        if info.is_dir():
            continue
        shown = f"{entry.path}/{info.filename}"
        safe = safe_member_path(info.filename)
        if safe is None:
            skipped.append({"file": shown, "reason": "unsafe_path"})
            continue
        if info.flag_bits & 0x1:
            skipped.append({"file": shown, "reason": "encrypted"})
            continue
        if info.file_size > MAX_MEMBER_BYTES:
            skipped.append({"file": shown, "reason": "too_large"})
            continue
        if info.file_size > 10 * 1024 * 1024 and info.file_size > MAX_RATIO * max(info.compress_size, 1):
            skipped.append({"file": shown, "reason": "zip_bomb"})
            continue
        child = Entry(f"{entry.path}/{safe}", info.file_size,
                      (lambda i=info: zf.open(i)), depth=entry.depth + 1)
        yield from expand(child, budget, skipped)
