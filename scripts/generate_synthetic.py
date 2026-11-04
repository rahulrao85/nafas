"""Write the synthetic demo dataset to data/synthetic/ so it can be declared and inspected.

    python scripts/generate_synthetic.py

Output is fully determined by fixed seeds in nafas/synthetic.py; re-running gives identical files.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nafas import synthetic  # noqa: E402
from nafas.ingest import to_csv  # noqa: E402

OUT = ROOT / "data" / "synthetic"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"generator": "nafas/synthetic.py", "real_data_used": False, "personas": [], "cohort": {}}
    for pid, make in synthetic.PERSONAS.items():
        p = make()
        (OUT / f"{pid}_nights.csv").write_text(to_csv(p["nights"]), encoding="utf-8", newline="\n")
        (OUT / f"{pid}_checkins.json").write_text(
            json.dumps([c.to_dict() for c in p["checkins"]], ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
        manifest["personas"].append({
            "id": pid, "display_name": p["profile"].display_name, "nights": len(p["nights"]),
            "first": p["nights"][0].date.isoformat(), "last": p["nights"][-1].date.isoformat(),
            "story": p["story"],
        })
    users = synthetic.cohort()
    rows = []
    for u in users:
        for n in u["nights"]:
            rows.append(n)
    (OUT / "cohort_profiles.json").write_text(
        json.dumps([{"id": u["profile"].id, **u["profile"].tags} for u in users], indent=2), encoding="utf-8", newline="\n")
    manifest["cohort"] = {"people": len(users), "nights_each": len(users[0]["nights"]),
                          "file": "cohort_profiles.json (attributes only; nights regenerate from seed 7)"}
    (OUT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"Wrote {len(synthetic.PERSONAS)} personas + cohort manifest to {OUT}")


if __name__ == "__main__":
    main()
