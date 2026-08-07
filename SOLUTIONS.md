# SOLUTIONS

## [2026-08-07] - Directory entry parser dropped nearly all 1860 and 1842 records

### Problem
`scripts/parse_directory.py` returned 17 records for Wood's 1860 and 2 for
Matchett's 1842, against thousands of visible entries. 1822 parsed fine at 386.

### Root Cause
Two independent faults.

1. The line-rejoining rule required a comma immediately after the first word
   (`Ailand, Harriot,` - Keenan's 1822 style). Wood's and Matchett's put the
   comma after the *full* name (`Adams Benjamin,`), so every entry looked like
   a continuation of the previous one and the whole section collapsed into a
   handful of giant strings.
2. Section bounds for 1842 assumed `COLORED HOUSEHOLDERS` was a running page
   head, as it is in 1860. In Matchett's it appears only on the section title
   page, so first-to-last-occurrence spanned about 9 lines instead of ~5,000.

### Solution
Rejoin rule is now "starts with a capitalised word AND contains a comma",
which admits both name styles while still rejecting real continuations
(lowercase fragments like `atoga, dw 214 Montgomery`, or bare capitalised
street names like `Chesnut` that carry no comma). Section extraction gained an
optional `end` terminator regex, set to `APPENDIX` for 1842. Also added
hyphen-aware joining so `Sar-` + `atoga` becomes `Saratoga`.

Result: 4,251 / 2,724 / 414 records for 1860 / 1842 / 1822.

### Notes
1822 output is still unreliable - the Keenan OCR is much poorer and occupation
text bleeds into the address field. Needs separate work or re-OCR.

---

## [2026-08-07] - Street anchor table missed the largest streets

### Problem
`scripts/extract_anchors.py` recovered anchor tables for only 84 streets, and
the covered set had conspicuous alphabetical holes: no CHARLES, CALVERT,
BALTIMORE, GAY or EUTAW - precisely the busiest streets, where most addresses
are. It also invented street names like `DIRECTORY. 513` carrying 290 rows.

### Root Cause
Three faults, all from assuming the page layout is uniform.

1. **Column x-positions are not constant.** The table block is indented
   differently on different pages: cross-street names sit at x-offset ~325 on
   printed p.509 but ~455 on p.513. Fixed x bands therefore read the *name*
   column of some pages as the *number* column, so those streets produced no
   usable rows.
2. **Street headings are not reliably flush left.** The heading test used
   `x-offset < 60`, true on p.509 but false on p.513 where headings start at
   offset ~126. Those headings were missed, so their tables were attributed to
   whatever street was last seen.
3. The running page head (`STREET DIRECTORY. 513`) is ALL CAPS at the top of
   every page and parsed as a street heading. Section end detection also
   overshot into the appendix because it matched literal `BOUNDARIES` while the
   OCR reads `BOUNDAEIES`, pulling in an unrelated school table.

### Solution
Geometry is now derived per table block from the printed `Left. / Right.`
header row (matched loosely, since OCR renders it `Lejl.`, `Lafl.`, `Ei'/ht.`),
and house numbers are assigned to the left or right column by proximity to
those two header positions. Street headings are detected by **case** rather
than position - headings are ALL CAPS, cross-street names are Title Case.
Words above y=260 are dropped to remove the running head, and the terminator
regex was relaxed to `BOUND[AE]`.

Parser state (current street, current column geometry) now flows in true
reading order - left book column, then right book column, page after page -
because a long street's table continues across a column break without
repeating its heading.

Result: 214 streets, 1,520 anchor rows, 1,145 carrying a house number.

### Notes
Verified against the directory's own worked example: it states that 55 stands
on the N.E. corner of Charles and Saratoga, and that No. 71 therefore falls
between Saratoga and Pleasant on the right hand. The extracted CHARLES table
gives right-side 55 at Saratoga and 85 at Pleasant, so 71 does fall between
them. This is the regression test to re-run after any change here.

---

## [2026-08-07] - geopandas unusable in the anaconda base environment

### Problem
`import geopandas` fails with "A module that was compiled using NumPy 1.x
cannot be run in NumPy 2.4.6".

### Root Cause
Binary ABI break. The anaconda base env has NumPy 2.4.6 installed, but pandas
and its `_libs` extensions there were compiled against NumPy 1.x.

### Solution
Created a project-local `.venv` (system python3) with geopandas 1.0.1, shapely
2.0.7, pyproj 3.6.1, pyogrio and rapidfuzz. Deliberately did **not** repair the
anaconda base env, since many other projects under `~/coding` depend on it and
a numpy pin there could break them.

### Notes
Run project scripts with `./.venv/bin/python`, not `python3`.
