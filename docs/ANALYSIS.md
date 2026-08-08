# Black Baltimore, 1819–1868: what the numbers say

This is a first analytical pass across all seven directory years, the ward
censuses, and the geocoded points. Nothing here has been fitted to a thesis
in advance; the method for each section is described so the numbers can be
checked and re-run. Where a pattern could plausibly be an artifact of
coverage rather than history, that is said explicitly rather than folded
into the finding. Directories undercount the poor, the transient, and women
everywhere in this record, so every share below is a floor, not a census.

## Data and coverage, at a glance

| Year | Records | Occupation stated | Geocoded | Geocoded % |
|---|---:|---:|---:|---:|
| 1819 | 526 | 93.0% | 92 | 17.5% |
| 1822 | 1,061 | 97.1% | 230 | 21.7% |
| 1842 | 2,724 | 70.4% | 742 | 27.2% |
| 1845 | 2,100 | 39.2% | 1,447 | 68.9% |
| 1851 | 3,642 | 53.2% | 1,584 | 43.5% |
| 1860 | 4,251 | 62.9% | 2,939 | 69.1% |
| 1868 | 8,512 | 64.2% | 6,047 | 71.0% |

Two things follow immediately from this table and shape every section below.
First, occupation-stated rate swings from 39% to 97% across years for reasons
that are about the *source*, not the *population* — the 1819/1822 Afrigeneas
transcriptions record occupation almost universally, the printed city
directories do not. Any cross-year occupational comparison must be normalized
to the stated-occupation cohort, never to raw counts, and even then the
denominator's composition is not the same kind of sample year to year.
Second, geocoding coverage triples from 1819/1822 (17–22%) to 1845–1868
(44–71%), because the earlier records give only a cross-street/bearing
("block face") while the numbered-address method used from 1845 on recovers
far more points. **A point map of 1819 next to a point map of 1868 is not two
densities of the same phenomenon — it is 92 points against 6,047, drawn by
different methods.** Anywhere below that compares density or clustering
visually across years, that gap is the first explanation to rule out.

Geocoding confidence also varies structurally by year: 1819/1822/1842 use a
block-face method (confidence `block_face`/`corner`/`near`) with no numeric
precision at all, while 1845–1868 use house-number interpolation, tiered from
best to worst as `bracketed` (a printed ladder exists on both sides) →
`single_anchor` → `street_proportional` (only a street match, placed
proportionally) → `extrapolated`. In 1868, 67% of geocoded points
(4,053 of 6,047) are the weakest tier, `street_proportional`. This matters
directly for §7 below.

---

## 1. The long arc: concentration, not just decline

The top-line numbers are not in dispute: Baltimore's Black share of the
population fell from 23.40% in 1820 to 16.79% in 1850 to 13.13% in 1860. The
ward data answer the follow-up question — did that mean Black Baltimoreans
spread out as the city grew around them, or did they concentrate into a
smaller residential footprint while the city's growth passed them by?

The ward censuses say concentration, unambiguously, for the one comparison
that is methodologically clean (1850→1860, identical 20-ward boundary set):

| Year | Wards | Citywide Black share | Dissimilarity index (D)¹ | Std. dev. of ward Black % | Coefficient of variation |
|---|---:|---:|---:|---:|---:|
| 1820 | 12 | 23.40% | 0.082 | 4.00 pts | 0.172 |
| 1850 | 20 | 16.79% | 0.203 | 6.19 pts | 0.362 |
| 1860 | 20 | 13.13% | 0.247 | 6.41 pts | 0.462 |

¹ D is the Duncan dissimilarity index between the Black and white ward
distributions: `D = 0.5 × Σ|bᵢ/B − wᵢ/W|`, the share of either population that
would have to relocate to make ward shares proportional to the citywide
population. 0 = wards identical; 1 = complete separation.

As the Black share of the *city* shrank, the Black share *within wards*
spread further apart, not closer together: by 1860 the most heavily Black
ward (Ward 11, 25.94%) and the least (Ward 1, 3.24%) are eight-fold apart,
where in 1820 the range was under two-fold (17.76%–29.70%). Every measure of
dispersion — dissimilarity, standard deviation, coefficient of variation —
rises monotonically across all three years. **This is the headline finding
of the long arc: Black Baltimore did not disperse as its share of the city
fell. It held a shrinking, increasingly concentrated footprint while the
city's white population grew rapidly around and past it.**

**Caveat on the 1820 number.** The 1820 ward map has 12 wards; 1850 and 1860
have 20. Dissimilarity indices are well known to be sensitive to the number
of areal units used to compute them (more, smaller units mechanically permit
higher measured segregation), so part of the jump from D=0.082 (1820) to
D=0.203 (1850) is very likely an artifact of the finer 1850 ward grid, not
purely a change in settlement pattern. The 1850→1860 rise (D=0.203→0.247),
by contrast, uses the *same* 20 wards both years and is a clean, trustworthy
comparison: concentration genuinely intensified in that decade.

Location quotients (ward Black share ÷ citywide Black share; 1.0 = ward
matches the citywide average) show where the pull was:

| 1820 top 3 (LQ) | 1850 top 3 (LQ) | 1860 top 3 (LQ) |
|---|---|---|
| Ward 9 — 1.27 | Ward 11 — 1.56 | Ward 11 — 1.98 |
| Ward 11 — 1.17 | Ward 6 — 1.49 | Ward 15 — 1.73 |
| Ward 12 — 1.14 | Ward 17 — 1.48 | Ward 12 — 1.60 |

| 1820 bottom 3 (LQ) | 1850 bottom 3 (LQ) | 1860 bottom 3 (LQ) |
|---|---|---|
| Ward 4 — 0.76 | Ward 8 — 0.55 | Ward 1 — 0.25 |
| Ward 5 — 0.76 | Ward 18 — 0.56 | Ward 8 — 0.43 |
| Ward 1 — 0.77 | Ward 19 — 0.59 | Ward 4 — 0.50 |

Ward 11 is the standout: it is the single most Black-concentrated ward in
*both* 1850 and 1860 (1846–1860 boundaries, a legitimate same-boundary
comparison), and its concentration is still rising even as the citywide share
falls — LQ 1.56 → 1.98. A single ward becoming *more* distinctively Black
while the city's Black share overall contracts is exactly the concentration
signature the dissimilarity index is picking up.

---

## 2. Persistence and collapse across three censuses

Two comparisons are available here, and they are not equally trustworthy.

**Sound comparison: 1850 → 1860, same 20 wards.** Ward-level Black share is
strongly persistent (Pearson r = 0.925 between 1850 and 1860 percentages),
but the changes that do occur are large and one-directional — every ward's
Black share *fell* over the decade, none rose. The variation is in how much:

| Ward | Black % 1850 | Black % 1860 | Change (pts) | Aggregate pop. change |
|---:|---:|---:|---:|---:|
| 17 | 24.86 | 14.52 | **−10.34** | +5,121 |
| 4 | 13.32 | 6.52 | −6.80 | −617 |
| 3 | 17.40 | 12.16 | −5.24 | +3,522 |
| 6 | 24.95 | 19.94 | −5.01 | +873 |
| 5 | 22.44 | 17.61 | −4.83 | −352 |
| 1 | 7.98 | 3.24 | −4.74 | +379 |
| … | | | | |
| 12 | 22.29 | 21.05 | −1.24 | +588 |
| 9 | 9.96 | 8.91 | −1.05 | −1,596 |
| 14 | 18.86 | 18.66 | **−0.20** | −349 |
| 11 | 26.11 | 25.94 | **−0.17** | +1,648 |

Wards 11 and 14 are essentially flat — Baltimore's most stable Black wards
across the decade. Ward 17 collapsed hardest, losing over 10 points of Black
share while its total population grew by more than 5,000: a textbook case of
the city literally growing around and diluting an existing Black
neighborhood, rather than Black residents leaving. Ward 4 is the opposite
pattern — its Black share fell nearly as much (−6.80 pts) while its *total*
population also shrank (−617), which looks more like displacement than
dilution.

**Approximate comparison: 1820 → 1850/1860, different boundaries.** The 1820
ward map (12 wards, 1818–1831 boundaries) cannot be joined to the 1850/1860
map (20 wards, 1846–1860 boundaries) by ward number — they are different
polygons. To compare them at all, I areally interpolated the 1820 ward
populations onto the 1846–1860 ward footprint: for each 1846–1860 ward, I
took the 1820 wards it overlaps and allocated their Black/aggregate
population proportional to the overlapping area, **assuming population was
distributed uniformly within each 1820 ward** — an assumption that is
certainly wrong at the block level but is the best available without
digitizing intersection-level 1820 addresses. The allocation reproduces the
citywide 1820 totals almost exactly (14,680 of 14,683 Black; 62,727 of 62,738
aggregate — the small shortfall is 43 sliver geometries dropped at the
overlay step), which is a reasonable sanity check on the method, not proof
that the uniform-density assumption holds locally.

| 1846–60 ward | Black % implied by 1820 (interpolated) | Black % 1850 (actual) | Black % 1860 (actual) |
|---:|---:|---:|---:|
| 11 | 24.05 | 26.11 | 25.94 |
| 6 | 23.83 | 24.95 | 19.94 |
| 20 | 27.26 | 17.77 | 15.93 |
| 19 | 26.70 | 9.90 | 8.52 |
| 18 | 26.70 | 9.38 | 7.00 |
| 8 | 19.99 | 9.25 | 5.64 |
| 1 | 17.91 | 7.98 | 3.24 |

Read cautiously, this table tells a consistent story with §1: the ward that
holds the *highest* Black share throughout (Ward 11: ~24% interpolated 1820 →
26.1% in 1850 → 25.9% in 1860) is nearly flat across the full 40-year span,
while several wards that were comparably or more Black in 1820 (Wards 18, 19,
20, 8, 1 — all above 18% on the interpolated figure) fell to single digits or
low teens by 1850 and fell further by 1860. **The same handful of wards
(11, and to a lesser extent 6) anchor Black Baltimore across all three
censuses; the wards that "diluted" hardest did so mostly in the 1820s–1840s,
before the 1850 census baseline, not afterward.** This is presented as a
directional finding, not a precise one — the areal-interpolation numbers in
the first column should not be quoted as if they were as solid as the actual
1850/1860 census figures next to them.

---

## 3. Occupational change across seven directories

Reading occupation shares requires normalizing to the stated-occupation
cohort each year (see coverage table above — the denominator ranges from 39%
to 97% of the year's records) and merging obvious spelling/dialect variants
(`labourer`/`laborer`, `laundress`/`washerwoman`, `mariner`/`seaman`). With
that done, the top occupations as a share of the stated-occupation cohort:

| Occupation | 1819 | 1822 | 1842 | 1845 | 1851 | 1860 | 1868 |
|---|---:|---:|---:|---:|---:|---:|---:|
| laborer | 32.9% | 36.3% | 21.9% | 21.2% | 25.0% | 20.6% | 23.6% |
| laundress/washerwoman | 22.7% | 17.1% | 20.3% | 12.3% | 11.8% | 9.6% | **21.5%** |
| waiter | 1.4% | 2.1% | 2.9% | 2.4% | 3.8% | 7.8% | 6.6% |
| porter | 1.6% | — | 3.3% | 3.0% | 3.2% | 7.0% | 4.1% |
| drayman | 0.6% | 4.6% | 5.6% | 5.5% | 6.4% | 8.3% | 4.0% |
| cook | — | 0.4% | 1.0% | 0.6% | 1.3% | 2.1% | 3.9% |
| seaman/mariner | 2.7% | 0.1% | 2.9% | 2.7% | 1.3% | 2.6% | 2.3% |
| hod carrier | — | — | — | — | — | 1.0% | 1.9% |
| brickmaker | 1.2% | 0.1% | 0.8% | 2.1% | 0.6% | 3.3% | 1.7% |
| barber | 4.1% | 2.5% | 2.1% | 2.2% | 2.1% | 2.8% | 1.3% |
| carter | 5.3% | 4.0% | 4.1% | 2.7% | 3.7% | 3.3% | 1.0% |
| caulker | 2.9% | 2.4% | 2.2% | 1.9% | 2.7% | 2.2% | 1.0% |

The single largest movement anywhere in the table is **laundress/washerwoman,
which more than doubles its share of stated occupations from 9.6% in 1860 to
21.5% in 1868** — the biggest occupational shift across emancipation in
either direction. Set against it, a cluster of dock- and transport-adjacent
male trades all contract as a share of the stated-occupation cohort from
1860 to 1868: drayman (−4.3 pts), porter (−2.9), carter (−2.2), brickmaker
(−1.6), barber (−1.5), caulker (−1.2), waiter (−1.1), sailor (−0.9). Laborer
rises modestly (+3.1 pts). Read together with §4 below, this looks less like
a shift in what *men's* work was available and more like a much larger,
much more fully documented female labor force entering the recorded
occupational structure after emancipation, which mechanically compresses
every other category's share of the total.

**Caveat.** The pre-1850 years carry a specific data-quality wrinkle: OCR
noise in the 1842/1845/1851 sources sometimes merges the occupation into the
`given`-name field (e.g. a raw line like "Ackwood Wm. sawyer" was parsed with
`given="Wm. sawyer"`, `occupation=NaN`). That means the `occupation`-stated
rate for 1842/1845/1851 in the coverage table understates true occupational
recording in those years, and any occupation-share comparison involving them
should be read as a floor. It does not affect the 1860→1868 comparison
above, which is the cleanest pair in the set (both from the same publisher,
Wood's directory, using the same conventions).

---

## 4. Women's work

There is no sex field in this data. Gender was inferred two ways, combined:
(1) an explicit list of occupation terms that are unambiguously gendered in
this period (female: laundress, washerwoman, seamstress, dressmaker,
huckstress, nurse, chambermaid, tailoress, midwife; male: laborer, drayman,
waiter, porter, mariner, brickmaker, barber, coachman, carter, caulker,
stevedore, sailor, sawyer, blacksmith, carpenter, and similar trades never
held by women in this record), applied to both the `occupation` field and,
as a fallback, the `given` field (to catch the OCR-merged cases described
above); (2) for anyone not resolved by occupation, a curated list of ~90
forenames common in this corpus, classified by conventional gender. Both are
heuristics and will misclassify unusual or unisex names; unresolved records
are reported as unknown rather than guessed.

| Year | N | Female (% of all) | Female (% of gender-resolved) | Unresolved |
|---|---:|---:|---:|---:|
| 1819 | 526 | 22.2% | 24.0% | 7.2% |
| 1822 | 1,061 | 19.9% | 20.6% | 3.6% |
| 1842 | 2,724 | 26.0% | 27.3% | 4.6% |
| 1845 | 2,100 | 18.6% | 20.1% | 7.4% |
| 1851 | 3,642 | 17.5% | 18.8% | 7.2% |
| 1860 | 4,251 | 20.6% | 21.7% | 4.9% |
| 1868 | 8,512 | 27.3% | 28.7% | 5.1% |

Women are a minority of every year's listing, consistent with directories
being built around household heads and wage earners, which in this period
skews male even within the free Black community. But the female share jumps
from 20.6% in 1860 to 27.3% in 1868 — the highest of any year — and the shift
is not just in *how many* women appear but in *how visible their work is* to
the directory:

| Year | Occupation stated, female-coded records | Occupation stated, male-coded records |
|---|---:|---:|
| 1860 | 41.8% | 71.2% |
| 1868 | **72.4%** | 62.3% |

In 1860, fewer than half of women in the listing have any occupation
recorded at all — most appear as a name and address only. By 1868, nearly
three-quarters do, a rate that has overtaken the male rate (which itself
fell, from 71.2% to 62.3%, likely reflecting a much larger and more marginal
male cohort entering the postwar directory alongside the same core of
established tradesmen). Put together with §3, the emancipation-era jump in
laundress/washerwoman's share of the whole cohort's stated occupations is not
simply more women being listed — it is more women being listed *as workers*,
where before they were, disproportionately, listed as dependents. That is a
genuinely new form of visibility, and probably reflects real change (a freed
woman supporting herself needs an income and a directory listing that
records it), though the directory's own compilation habits could also be
shifting in step with it — we cannot fully separate "more women worked for
wages" from "the compiler was now more willing to write down what women did."

Within the female-coded, occupation-stated group, laundry/wash work is
overwhelming (55–96% of female stated occupations, depending on year) — but
this figure should be read with real caution, since laundress/washerwoman
was itself one of the primary markers used to *classify* gender in the first
place. The non-circular, trustworthy number is the one in §3: laundress and
washerwoman rose from 9.6% to 21.5% of the *entire* stated-occupation cohort
(men and women together) between 1860 and 1868, which is not an artifact of
the classifier.

---

## 5. Business and institutional geography

`record_categories.csv` classifies 701 business records and 19 institutions
across the seven years (residents are the unlabeled remainder):

| Year | Businesses | Institutions |
|---|---:|---:|
| 1819 | 39 | 0 |
| 1822 | 52 | 0 |
| 1842 | 117 | 1 |
| 1845 | 65 | 1 |
| 1851 | 97 | 1 |
| 1860 | 167 | 7 |
| 1868 | 164 | 9 |

Institutions and businesses geocode at a much lower rate than residents,
because many are listed by name or corner rather than a numbered address
(churches especially): of 1860's 167 businesses and 7 institutions, only 118
businesses and 2 institutions land on the map at all; of 1868's 164 and 9,
only 122 and 2. Anything below about institutions in particular is a
two-or-three-point sample and should be read as illustrative, not as a
distribution.

**Alley vs. named street.** Businesses sit on alleys distinctly less often
than the resident population around them:

| Year | Business on alley | Resident on alley |
|---|---:|---:|
| 1860 | 14.4% | 19.7% |
| 1868 | 8.2% | 21.1% |

That is consistent with an intuitive read: commerce needs street frontage
and foot traffic that a residential alley doesn't offer, so even within the
same community, Black-run business gravitates toward named streets while a
larger share of the general population lives on alleys behind them.

**Do businesses track residents at the ward level?** Yes, broadly, but
imperfectly. Comparing each ward's share of geocoded businesses to its share
of geocoded residents gives a correlation of r = 0.79 (1860, 1846–1860
wards) and r = 0.81 (1868, 1861–1882 wards) — a strong but not one-to-one
relationship. The clearest 1860 exception is Ward 11, the single most
Black-concentrated ward in the city by census and directory alike (§1):
it holds 4.7% of geocoded residents but only 2.5% of geocoded businesses
(under-represented by roughly half), while Wards 1 and 5 — modest residential
wards — carry 2–3 times their resident share in businesses. **The densest
Black residential ward was not proportionally the densest Black business
ward**, which is at least consistent with Black commerce clustering on
through-streets that cut across residential concentration rather than
strictly inside it — though with only ~120 geocoded businesses this pattern
should be treated as suggestive, not conclusive. Note that 1860 and 1868 use
different ward boundary sets (1846–1860 vs. 1861–1882), so "Ward 11" in each
year is not necessarily the same polygon and the two years' ward patterns are
not compared to each other here.

**A weaker, secondary cross-check for 1868**: joining the 1868 geocoded
points to the 1861–1882 wards and then to `ward_valuation_1869` (new
construction that year) gives a *negative* correlation (r = −0.28) between a
ward's share of the Black directory population and its share of the city's
new dwelling construction. Wards 3 and 15 alone hold 7.8% and 13.8% of the
1868 directory population but only 1.0% and 1.7% of new dwellings that year;
Ward 1 has 13.7% of new construction but just 0.6% of the directory
population. This is a single-year snapshot with a weak correlation and
should not be over-read, but it points the same direction as the alley data
in §6: Black Baltimoreans in 1868 were concentrated in wards where the
building boom was passing them by, not wards being newly built up.

---

## 6. Alley living

Baltimore's Black population lived disproportionately on alleys — streets
named for a lane, court, or alley rather than a major thoroughfare — and that
share declines over the seven directories:

| Year | % on alley (of records with a street) |
|---|---:|
| 1819 | 37.3% |
| 1822 | 31.3% |
| 1842 | 30.6% |
| 1845 | 28.1% |
| 1851 | 22.0% |
| 1860 | 25.6% |
| 1868 | 21.6% |

(Method: the raw `street` field matched against `\b(al|aly|alley|ct|court)\b`
as a whole word, so "Central" or "Courtland" are not miscounted as alleys.)

The decline from 37.3% (1819) to 21.6% (1868) is close to a halving, and is
fairly steady apart from an uptick at 1860. Read as housing quality, this
would suggest real improvement in where Black Baltimoreans lived over the
half-century — but it should not be reported as settled fact, because the
sources compiling these numbers changed alongside the numbers themselves:
the 1819/1822 years come from hand-transcribed indices (Afrigeneas), while
1842–1868 are printed city directories with different canvassing practices,
and a directory that canvasses named streets more thoroughly than back
alleys would produce exactly this kind of decline in *measured* alley share
without any change in where people actually lived. The direction is
plausible and worth taking seriously; the magnitude is not.

---

## 7. Geography vs. the census — the directory's blind spot

This is the most methodologically important result in this analysis, because
it is the one place we can directly measure who the directory missed, rather
than infer it.

For 1860, every geocoded directory record carries a `Ward_Num` (1846–1860
boundaries), letting us compare the directory's ward distribution to the
ward census's actual Black population distribution. First, scale: the 2,939
geocoded 1860 directory records are just **10.5% of the 27,898 people the
1860 census counted as Black in Baltimore** — directories record household
heads and wage earners, not every man, woman and child, so this ratio alone
is not surprising. What is informative is *where* that 10.5% comes from,
relative to where the census says the population actually was:

| Ward | Directory share of geocoded 1860 records | Census share of Black population | Representation index¹ |
|---:|---:|---:|---:|
| 3 | 13.1% | 6.7% | **1.96** |
| 4 | 2.9% | 1.6% | 1.79 |
| 2 | 4.2% | 2.4% | 1.73 |
| 8 | 5.0% | 2.9% | 1.71 |
| 15 | 14.5% | 10.6% | 1.37 |
| … | | | |
| 16 | 3.9% | 5.6% | 0.69 |
| 10 | 1.5% | 2.2% | 0.68 |
| 6 | 3.5% | 7.1% | 0.50 |
| 5 | 1.6% | 3.4% | 0.48 |
| **11** | **4.6%** | **9.8%** | **0.47** |

¹ Representation index = directory share ÷ census share. 1.0 = the directory
represents the ward exactly in proportion to its actual Black population;
above 1 = over-represented; below 1 = missed.

**Ward 11 — the single most Black ward in the city, holding 9.8% of the
city's entire census-counted Black population (§1) — is the most
under-represented ward in the directory, captured at less than half its fair
share.** Wards 5 and 6, also above-average Black wards, are similarly
under-represented (0.48, 0.50). Meanwhile Wards 3, 4, 2, and 8 — all
comparatively modest Black wards by census share — are over-represented by
70–96%. **The directory did not miss Black Baltimoreans at random. It missed
them concentrated exactly where the Black population itself was most
concentrated**, which is close to the worst-case bias a source like this
could carry: the neighborhoods most central to Black Baltimore's actual
geography are the ones this dataset sees least clearly.

**A necessary caveat that keeps this from being a clean finding.** This
pattern is entangled with, and cannot be fully separated from, a second
effect: geocoding quality is not uniform by ward, and it is worst exactly in
Ward 11. Of Ward 11's 134 geocoded points, **zero** carry the best-quality
`bracketed` confidence tier — all are `single_anchor` or the weakest tier,
`street_proportional` — while Ward 3, the most over-represented ward above,
is 95% `bracketed`. The list of streets that failed to geocode at all in
1860 (`unmatched_streets_1860.csv`) is dominated by alley names — Lerew's
alley, Chesnut alley, Carpenter's alley, Eutaw court, Cecil alley, Gillingham
alley — and alleys are exactly where the densest Black wards housed people
(per the geocoding pipeline's own documentation in `scripts/geocode_1860.py`,
modern street data "still carries the alleys" only in part). So Ward 11's
apparent under-representation could be some mixture of two distinct things
this dataset cannot cleanly separate: (a) the 1860 directory itself under-
listing the densest, poorest, most alley-heavy Black blocks — the historical
finding the method was designed to detect — and (b) modern street geometry
failing to carry forward exactly the alley names that would place points in
Ward 11, an artifact of the geocoding pipeline rather than of 1860 Baltimore.
Both effects plausibly point the same direction and could be compounding
each other. Given this project's standing preference for false negatives
over false positives: **report the under-representation of Ward 11 as real
and worth investigating further (e.g. by re-examining Ward 11's specific
unmatched streets, or by tallying the *raw, ungeocoded* 1860 records by
street name against known Ward 11 streets), but do not treat the exact
magnitude (0.47×) as a precise measure of directory bias alone.**

---

## Confidence summary

**High confidence** (directly computed from clean, matching-boundary data,
robust to the caveats noted):
- Citywide Black share fell 1820→1850→1860, and ward-level dispersion of
  Black share rose over the same period (§1, using the clean 1850→1860 pair
  especially).
- Ward 11 is the most Black-concentrated ward in both 1850 and 1860 and its
  concentration is rising, not falling (§1, §2).
- Ward-level persistence 1850→1860 is strong (r=0.925) and every ward's
  Black share fell, with Ward 17 collapsing hardest amid citywide growth and
  Wards 11/14 essentially flat (§2).
- Laundress/washerwoman's share of all stated occupations more than doubled
  from 1860 to 1868 (9.6%→21.5%), the largest occupational shift in the
  dataset (§3).
- Women's occupation-stated rate rose sharply from 1860 to 1868 (41.8%→
  72.4%), outpacing men (§4).
- Alley living rate and business-vs-resident alley rates are cleanly computed
  from the raw address strings (§5, §6).
- The 1860 directory's ward coverage is skewed relative to the census, with
  Ward 11 most under-represented (§7) — the *direction* of this finding is
  solid.

**Provisional / directional only, flagged accordingly in text:**
- The 1820→1850/1860 areal-interpolation comparison (§2), which rests on a
  uniform-density assumption within 1820 wards.
- The precise *magnitude* of Ward 11's under-representation in §7, which is
  confounded with that ward's unusually poor geocoding confidence.
- The declining alley-living trend as evidence of improving housing quality
  (§6), which could partly reflect changing directory canvassing practices.
- The ward-level business/resident correlation and the 1868
  construction-valuation cross-check (§5), both based on small geocoded
  business/institution samples.
- Gender classification (§4) is a name-and-occupation heuristic with 4–7%
  unresolved records per year, not a ground-truth field.
