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

# ---------------------------------------------------------------------------
# 1850: Seventh Census, Table II, Population of Cities and Towns, Maryland
# report p.221. This PDF does carry a text layer, but pdftotext interleaves the
# columns across ward rows, so only the three columns that self-check are taken
# directly - free colored, slave, aggregate - and white is derived as
# aggregate - free colored - slave. Wards 1846-1860 are the same polygons as
# 1860, so the two years are directly comparable on one boundary set.
#
# ward: (free_colored, slave, aggregate)
WARDS_1850 = {
    1:  (1091, 79, 14653),   2:  (917, 85, 9492),
    3:  (1862, 195, 11821),  4:  (766, 250, 7627),
    5:  (1198, 84, 5712),    6:  (2145, 104, 9015),
    7:  (1013, 57, 7660),    8:  (750, 78, 8953),
    9:  (333, 139, 4740),    10: (596, 241, 5033),
    11: (2078, 252, 8923),   12: (1911, 158, 9283),
    13: (807, 264, 5566),    14: (1221, 177, 7411),
    15: (2242, 307, 10302),  16: (1189, 134, 5878),
    17: (2400, 45, 9834),    18: (934, 168, 11746),
    19: (717, 63, 7875),
    # ward 20's slave count reads as 99 in the scrambled text layer, but
    # aggregate minus total-free gives 66, and only 66 makes the column sum to
    # the printed 2,946. The arithmetic check is the authority here.
    20: (1272, 66, 7530),
}
PRINTED_1850 = {"fc": 25442, "slave": 2946, "aggregate": 169054, "white": 140666}

# ---------------------------------------------------------------------------
# 1820: Fourth Census, "AGGREGATE amount of each description of persons within
# the DISTRICT OF MARYLAND", printed p.97 of 1820a-02.pdf. City of Baltimore is
# broken into its twelve wards, thirty years before the 1850 table.
#
# This page was nearly missed. The PDF is a pure image scan with no text layer,
# so grep and pdftotext both return nothing and the obvious conclusion is that
# the data does not exist. It does. Old volumes have to be paged through, not
# searched.
#
# The census bands by age, so slaves and free colored each arrive as eight
# columns (four male, four female). Stored summed. The transcription is
# confirmed by three independent twelve-number sums landing exactly on the
# known city totals: 4,357 enslaved, 10,326 free colored, 62,738 aggregate.
#
# ward: (slave_total, free_colored_total, aggregate)
WARDS_1820 = {
    1:  (267, 535, 4477),    2:  (288, 1430, 7512),
    3:  (362, 1204, 6548),   4:  (371, 809, 6645),
    5:  (313, 240, 3091),    6:  (459, 258, 3469),
    7:  (468, 450, 3460),    8:  (227, 626, 3592),
    9:  (268, 795, 3579),    10: (407, 1066, 6119),
    11: (334, 1273, 5882),   12: (593, 1640, 8364),
}
PRINTED_1820 = {"fc": 10326, "slave": 4357, "aggregate": 62738}


def main_1820():
    rows, tot = [], {"fc": 0, "slave": 0, "aggregate": 0}
    for w in sorted(WARDS_1820):
        sl, fc, agg = WARDS_1820[w]
        black = sl + fc
        rows.append({"ward": w, "white": agg - black, "free_colored": fc,
                     "slave": sl, "black_total": black, "aggregate": agg,
                     "black_pct": round(black / agg * 100, 2)})
        tot["fc"] += fc; tot["slave"] += sl; tot["aggregate"] += agg
    problems = []
    for k, want in PRINTED_1820.items():
        got = tot[k]
        print(f"  {'OK ' if got == want else 'MISMATCH'} {k:10s} "
              f"transcribed {got:>7,}  known {want:>7,}")
        if got != want:
            problems.append(f"{k}: {got} != {want}")
    if problems:
        raise SystemExit("1820 TRANSCRIPTION FAILED:\n  " + "\n  ".join(problems))
    out = WORK / "ward_census_1820.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    share = sum(r["black_total"] for r in rows) / sum(r["aggregate"] for r in rows)
    print(f"\n1820 reconciles -> {out.name}")
    print(f"citywide Black share 1820: {share*100:.2f}%")
    return rows


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


def main_1850():
    rows, tot = [], {"fc": 0, "slave": 0, "aggregate": 0, "white": 0}
    problems = []
    for w in sorted(WARDS_1850):
        fc, slave, agg = WARDS_1850[w]
        white = agg - fc - slave
        black = fc + slave
        rows.append({"ward": w, "white": white, "free_colored": fc,
                     "slave": slave, "black_total": black, "aggregate": agg,
                     "black_pct": round(black / agg * 100, 2)})
        tot["fc"] += fc; tot["slave"] += slave
        tot["aggregate"] += agg; tot["white"] += white

    for k, want in PRINTED_1850.items():
        got = tot[k]
        print(f"  {'OK ' if got == want else 'MISMATCH'} {k:10s} "
              f"transcribed {got:>7,}  printed {want:>7,}")
        if got != want:
            problems.append(f"{k}: {got} != {want}")
    if problems:
        raise SystemExit("1850 TRANSCRIPTION FAILED:\n  " + "\n  ".join(problems))

    out = WORK / "ward_census_1850.csv"
    with out.open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    share = sum(r["black_total"] for r in rows) / sum(r["aggregate"] for r in rows)
    print(f"\n1850 reconciles -> {out.name}")
    print(f"citywide Black share 1850: {share*100:.2f}%")
    for r in sorted(rows, key=lambda r: -r["black_pct"])[:4]:
        print(f"   ward {r['ward']:2d}  {r['black_pct']:5.2f}%")
    return rows


if __name__ == "__main__":
    print("=== 1860 ===")
    main()
    print("\n=== 1850 ===")
    main_1850()
    print("\n=== 1820 ===")
    main_1820()
