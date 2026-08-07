#!/usr/bin/env python3
"""Ward-level 1860 population for Baltimore, transcribed and self-checked.

Source: "Population of the United States in 1860", Table No. 3, Population of
Cities, Towns, &c., State of Maryland, p. 214 (census volume 1860a-18.pdf).
The scan carries no text layer, so the figures are transcribed from the page
image.

Transcription is verified arithmetically rather than trusted: each column is
summed and compared against the printed "Total Baltimore" row, and every ward's
aggregate must equal white + free colored + slave. That check earned its keep,
catching a misread of ward 1's white female count (7,215 for 7,245); the exact
value is recoverable because aggregate, free colored and slave all verify, so
white total = aggregate - free colored - slave.

This is the only ward-level race breakdown available to us. IPUMS does not
distribute WARD for 1860 in its public complete count, so density by ward
cannot be computed from the microdata.

Output: data/work/ward_census_1860.csv
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORK = ROOT / "data" / "work"

# ward: (white_m, white_f, fc_m, fc_f, slave_m, slave_f, aggregate)
WARDS = {
    1:  (7300, 7245, 184, 249, 20, 34, 15032),
    2:  (4241, 4425, 298, 330, 19, 27, 9340),
    3:  (6363, 7115, 723, 1027, 25, 90, 15343),
    4:  (3073, 3480, 148, 237, 26, 46, 7010),
    5:  (2165, 2251, 362, 541, 10, 31, 5360),
    6:  (3651, 4265, 775, 1119, 19, 59, 9888),
    7:  (5276, 5708, 638, 740, 11, 32, 12405),
    8:  (6908, 6667, 361, 392, 18, 41, 14387),
    9:  (1518, 1346, 97, 91, 48, 44, 3144),
    10: (1823, 1889, 189, 364, 21, 29, 4315),
    11: (3344, 4485, 801, 1588, 101, 252, 10571),
    12: (3658, 4135, 760, 1207, 36, 75, 9871),
    13: (1742, 1949, 225, 466, 47, 44, 4473),
    14: (2689, 3055, 446, 730, 33, 109, 7062),
    15: (5123, 4978, 1169, 1618, 44, 129, 13061),
    16: (3187, 3488, 591, 891, 34, 46, 8237),
    17: (6371, 6413, 1008, 1160, 3, 0, 14955),
    18: (9443, 10394, 453, 766, 63, 212, 21331),
    19: (5600, 6344, 416, 603, 37, 57, 13057),
    20: (5138, 6275, 702, 1215, 62, 184, 13576),
}

# printed "Total Baltimore" row, used as the check
PRINTED = {"white_m": 88613, "white_f": 95907, "white": 184520,
           "fc_m": 10346, "fc_f": 15334, "fc": 25680,
           "slave": 2218, "aggregate": 212418}


def main():
    rows, totals = [], {k: 0 for k in
                        ("white_m", "white_f", "white", "fc_m", "fc_f", "fc",
                         "slave", "aggregate")}
    problems = []
    for w in sorted(WARDS):
        wm, wf, fm, ff, sm, sf, agg = WARDS[w]
        white, fc, slave = wm + wf, fm + ff, sm + sf
        black = fc + slave                      # free colored plus enslaved
        if white + fc + slave != agg:
            problems.append(f"ward {w}: {white}+{fc}+{slave} != {agg}")
        rows.append({
            "ward": w, "white": white, "free_colored": fc, "slave": slave,
            "black_total": black, "aggregate": agg,
            "black_pct": round(black / agg * 100, 2),
        })
        for k, v in (("white_m", wm), ("white_f", wf), ("white", white),
                     ("fc_m", fm), ("fc_f", ff), ("fc", fc),
                     ("slave", slave), ("aggregate", agg)):
            totals[k] += v

    for k, want in PRINTED.items():
        got = totals[k]
        flag = "OK " if got == want else "MISMATCH"
        print(f"  {flag} {k:10s} transcribed {got:>7,}  printed {want:>7,}")
        if got != want:
            problems.append(f"column {k}: {got} != {want}")

    if problems:
        raise SystemExit("TRANSCRIPTION FAILED:\n  " + "\n  ".join(problems))

    WORK.mkdir(parents=True, exist_ok=True)
    out = WORK / "ward_census_1860.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    print(f"\nall columns reconcile with the printed totals -> {out.name}")
    top = sorted(rows, key=lambda r: -r["black_pct"])[:5]
    print("\nmost heavily Black wards, 1860:")
    for r in top:
        print(f"   ward {r['ward']:2d}  {r['black_pct']:5.2f}%   "
              f"{r['black_total']:,} of {r['aggregate']:,}")
    citywide = sum(r["black_total"] for r in rows) / sum(r["aggregate"] for r in rows)
    print(f"\ncitywide Black share: {citywide*100:.2f}%")


if __name__ == "__main__":
    main()
