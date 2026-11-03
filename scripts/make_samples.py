"""Write synthetic sample files for every source Nafas reads to data/samples/ (deterministic).

    python scripts/make_samples.py

Also unpacks the sample SD card into data/samples/resmed_sd_card/, so "pick a folder" can be tried too.
"""

import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nafas.samples import build_all  # noqa: E402

OUT = ROOT / "data" / "samples"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = build_all()
    for name, data in files.items():
        (OUT / name).write_bytes(data)
    card = OUT / "resmed_sd_card"
    with zipfile.ZipFile(io.BytesIO(files["resmed_sd_card.zip"])) as z:
        for info in z.infolist():
            rel = Path(*Path(info.filename).parts[1:])        # drop the "SD CARD/" prefix
            dest = card / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(z.read(info))
    print(f"Wrote {len(files)} sample files and the resmed_sd_card/ folder to {OUT}")


if __name__ == "__main__":
    main()
