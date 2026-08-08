#!/usr/bin/env python3
"""Ward-level new construction in Baltimore, 1869, transcribed and self-checked.

Source: "Mayor's Message and Reports of the City Officers", Baltimore, 1869,
report of Thomas Gifford, Assessor, to the Judges of the Appeal Tax Court. The
table records dwellings and improvements assessed during 1869, by ward, with
their cash value.

Why this matters to the project. Every other ward series we have is about who
lived where. This one is about where the city was putting its money, in the
same years. Set against the 1868 directory map it asks a question the dot maps
cannot: was capital flowing into the wards where Black Baltimoreans lived, or
around them?

IMPORTANT - ward geometry. These are the 1861-1882 wards, NOT the 1846-1860
wards used for the 1850 and 1860 census tables. Ward 7 in 1869 is not ward 7 in
1860. This series therefore joins to the 1861-1882 boundary file and pairs with
the 1868 directory cohort, which uses the same boundaries. Do not join it to
the 1850/1860 census by ward number.

Transcription is verified by summing every column against the printed total row
($6,615,275 / 2,836 dwellings / 696 improvements), exactly as for the census
tables. All three reconcile.

Output: data/work/ward_valuation_1869.csv
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"

# ward: (cash value of assessments, dwellings, improvements)
WARDS = {
    1:  (544300, 388, 24),   2:  (151725, 60, 56),
    3:  (54750, 28, 43),     4:  (54300, 17, 12),
    5:  (39900, 39, 43),     6:  (268450, 190, 54),
    7:  (468900, 270, 52),   8:  (216950, 158, 20),
    9:  (377050, 36, 27),    10: (399150, 32, 60),
    11: (376650, 56, 32),    12: (825050, 156, 26),
    13: (95700, 54, 39),     14: (51400, 28, 37),
    15: (163050, 47, 23),    16: (179350, 130, 37),
    17: (218450, 200, 14),   18: (681200, 392, 50),
    19: (807050, 285, 17),   20: (641900, 270, 30),
}
PRINTED = {"value": 6615275, "dwellings": 2836, "improvements": 696}


def main():
    rows = []
    tot = {"value": 0, "dwellings": 0, "improvements": 0}
    for w in sorted(WARDS):
        v, d, i = WARDS[w]
        rows.append({"ward": w, "value": v, "dwellings": d, "improvements": i,
                     "value_per_dwelling": round(v / d) if d else 0})
        tot["value"] += v
        tot["dwellings"] += d
        tot["improvements"] += i

    problems = []
    for k, want in PRINTED.items():
        got = tot[k]
        print(f"  {'OK ' if got == want else 'MISMATCH'} {k:13s} "
              f"transcribed {got:>10,}  printed {want:>10,}")
        if got != want:
            problems.append(f"{k}: {got} != {want}")
    if problems:
        raise SystemExit("TRANSCRIPTION FAILED:\n  " + "\n  ".join(problems))

    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / "ward_valuation_1869.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"\nall columns reconcile -> {out.name}")
    print("\nmost new construction value, 1869:")
    for r in sorted(rows, key=lambda r: -r["value"])[:5]:
        print(f"   ward {r['ward']:2d}  ${r['value']:>9,}  {r['dwellings']:3d} dwellings")
    print("\nleast:")
    for r in sorted(rows, key=lambda r: r["value"])[:5]:
        print(f"   ward {r['ward']:2d}  ${r['value']:>9,}  {r['dwellings']:3d} dwellings")


if __name__ == "__main__":
    main()
