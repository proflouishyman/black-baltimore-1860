#!/usr/bin/env python3
"""Rebuild the house-number/cross-street anchor table from Wood's 1860
Baltimore directory "Street Directory" (printed pp. 509-529).

Why this exists: the directory prints, for every major street in the city, the
house number standing at each cross street, in Left and Right columns. That
table is the key to geocoding 1860 addresses, because it lets us place a house
number between two named intersections *in 1860 numbering* and so never touch
the 1880s renumbering at all. The directory's own worked example:

    "55 is on the N.E. corner of Charles and Saratoga-sts., hence the desired
     No. 71 will be between Saratoga and Pleasant-sts., right hand."

The flat `_djvu.txt` OCR is useless here: it serialises the sub-columns into
decoupled runs with no row alignment. So we work from `_djvu.xml`, which
carries per-word bounding boxes, and rebuild rows geometrically.

Two facts make naive fixed-x parsing fail, and drive the design:

  * Column positions are NOT constant. Different pages indent the table block
    by different amounts (p.509 puts cross-street names at x-offset ~325,
    p.513 puts them at ~455). So geometry is derived per table block from the
    printed "Left. / Right." header row rather than hardcoded.
  * Street headings are NOT reliably flush left either. They are, however,
    always ALL CAPS, while cross-street names are Title Case. Case is the
    discriminator.

State (current street, current column geometry) flows in reading order:
left book column then right book column, page after page, because a long
street's table runs across a column break without repeating its heading.

Outputs two CSVs with a stable contract:
    street_extents.csv  street, extent
    street_anchors.csv  street, seq, cross_street, left_no, right_no, page
"""

import csv
import re
import sys
from pathlib import Path

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
WORK = Path(__file__).resolve().parent.parent / "data" / "work"
XML = RAW / "wood1860.djvu.xml"

COL_SPLIT = 930      # x dividing the two book columns
ROW_TOL = 22         # y tolerance when grouping words into a visual row
HEADER_ZONE = 260    # running page head ("STREET DIRECTORY. 513") sits above this
NAME_MARGIN = 10     # gap after the Right. column before the name column starts

WORD_RE = re.compile(r'<WORD coords="(\d+),(\d+),(\d+),(\d+)"[^>]*>([^<]*)</WORD>')
# ALL-CAPS opener marks a new street entry; Title Case marks a cross street
HEAD_RE = re.compile(r"^[A-Z][A-Z'’\.]{2,}")
DIGITS_RE = re.compile(r"^(\d+)")
# things that look like headings but are not streets
NOT_STREET = re.compile(r"^(STREET|DIRECTOR|INCLUDING|AVENUES|LANES|ALLEYS|COURTS|"
                        r"WHARVES|COMPILED|EXPLANATION|ABBEE|ABBRE|ENTERED|FOR\b)", re.I)


def page_words(page_xml):
    """Words as (x0, y, x1, text), with the running page head dropped."""
    out = []
    for x0, yb, x1, _yt, txt in WORD_RE.findall(page_xml):
        t = txt.strip()
        if t and int(yb) >= HEADER_ZONE:
            out.append((int(x0), int(yb), int(x1), t))
    return out


def group_rows(words):
    """Cluster words into visual rows by y, each ordered left to right."""
    rows, cur, cur_y = [], [], None
    for w in sorted(words, key=lambda t: t[1]):
        if cur_y is not None and abs(w[1] - cur_y) > ROW_TOL:
            rows.append(sorted(cur, key=lambda t: t[0]))
            cur, cur_y = [], None
        cur.append(w)
        if cur_y is None:
            cur_y = w[1]
    if cur:
        rows.append(sorted(cur, key=lambda t: t[0]))
    return rows


def is_lr_header(row):
    """The 'Left. / Right.' row printed above each table. OCR mangles it badly
    (Lejl., Lafl., Le/t., Ei'/ht.), so match loosely on shape and initial."""
    if not 2 <= len(row) <= 3:
        return None
    toks = [w[3].strip(" .,") for w in row]
    if any(len(t) > 7 or DIGITS_RE.match(t) for t in toks):
        return None
    left = [w for w, t in zip(row, toks) if t[:1].upper() == "L"]
    right = [w for w, t in zip(row, toks) if t[:1].upper() in ("R", "E")
             or t.lower().endswith("ht")]
    if len(left) == 1 and len(right) == 1 and left[0][0] < right[0][0]:
        return left[0], right[0]
    return None


def clean_street(s):
    s = s.replace("—", " ").replace("’", "'")
    s = re.sub(r"\s+", " ", s).strip(" .,-")
    return s


def split_heading(text):
    """'CHARLES (N.) going north from 228 W Baltimore' -> name, extent.
    The name is the leading run of ALL-CAPS (plus parenthetical) tokens."""
    toks = text.split()
    name = []
    for t in toks:
        core = t.strip("—-.,")
        if core.isupper() or re.match(r"^\(?[NSEW]\.?\)?[,.]?$", core) or core in ("AL", "LA", "CT", "AV"):
            name.append(t)
        else:
            break
    n = clean_street(" ".join(name))
    ext = clean_street(" ".join(toks[len(name):]))
    return n, ext


def main():
    if not XML.exists():
        sys.exit(f"missing {XML}: download the _djvu.xml first")
    pages = open(XML, encoding="utf8", errors="ignore").read().split("<OBJECT ")

    # locate the section: title page through the ward-boundary page that follows
    start = end = None
    for i, p in enumerate(pages):
        if not p:
            continue
        up = " ".join(t for _, _, _, t in page_words(p)).upper()
        if start is None and "STREET" in up and "DIRECTORY" in up and "ALLEYS" in up:
            start = i
        elif start is not None and re.search(r"BOUND[AE]", up) and "WARDS" in up:
            end = i
            break
    end = end or (start + 21)
    print(f"street directory: scan pages {start}..{end}")

    extents, anchors = [], []
    street, geom, seq = None, None, 0

    # reading order: left column then right column, page after page
    for pno in range(start, end):
        words = page_words(pages[pno])
        if not words:
            continue
        for lo, hi in ((0, COL_SPLIT), (COL_SPLIT, 10 ** 6)):
            col = [w for w in words if lo <= w[0] < hi]
            for row in group_rows(col):
                if not row:
                    continue

                lr = is_lr_header(row)
                if lr:
                    lhdr, rhdr = lr
                    geom = (lhdr[0], rhdr[0], rhdr[2] + NAME_MARGIN)
                    continue

                first = row[0][3]
                if HEAD_RE.match(first) and not NOT_STREET.match(first):
                    name, ext = split_heading(" ".join(w[3] for w in row))
                    if name:
                        street, seq = name, 0
                        extents.append({"street": street, "extent": ext})
                        continue

                # heading continuation: lowercase fragment, no digits, no geom hit
                if street and not geom:
                    continue
                if street and extents and not any(DIGITS_RE.match(w[3]) for w in row) \
                        and all(w[0] < geom[2] for w in row):
                    extents[-1]["extent"] = clean_street(
                        extents[-1]["extent"] + " " + " ".join(w[3] for w in row))
                    continue

                if street is None or geom is None:
                    continue

                left_x, right_x, name_x = geom
                left_no = right_no = ""
                name_parts = []
                for x0, _y, _x1, tok in row:
                    if x0 >= name_x:
                        name_parts.append(tok)
                        continue
                    m = DIGITS_RE.match(tok)
                    if not m:
                        continue
                    # nearer the Left. header or the Right. header?
                    if abs(x0 - left_x) <= abs(x0 - right_x):
                        left_no = left_no or m.group(1)
                    else:
                        right_no = right_no or m.group(1)

                cross = clean_street(" ".join(name_parts))
                if not cross or DIGITS_RE.match(cross):
                    continue
                seq += 1
                anchors.append({"street": street, "seq": seq, "cross_street": cross,
                                "left_no": left_no, "right_no": right_no, "page": pno})

    WORK.mkdir(parents=True, exist_ok=True)
    with (WORK / "street_extents.csv").open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=["street", "extent"])
        w.writeheader()
        w.writerows(extents)
    with (WORK / "street_anchors.csv").open("w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=["street", "seq", "cross_street",
                                           "left_no", "right_no", "page"])
        w.writeheader()
        w.writerows(anchors)

    numbered = [a for a in anchors if a["left_no"] or a["right_no"]]
    print(f"streets with extents : {len({e['street'] for e in extents})}")
    print(f"streets with anchors : {len({a['street'] for a in anchors})}")
    print(f"anchor rows          : {len(anchors)}  ({len(numbered)} carry a house number)")


if __name__ == "__main__":
    main()
