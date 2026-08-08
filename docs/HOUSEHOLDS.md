# Households, not addresses — IPUMS complete-count household data, 1790–1840

Status: analysis complete, independently verified. 2026-08-08.

## What this data cannot do

State this before anything else, because it constrains every sentence that
follows. The IPUMS complete-count household files (`H_1790.csv` through
`H_1840.csv`) have **no name, no address, and no ward** — confirmed directly
by inspecting the columns, all ~134 of which are counts (household
composition, age bands, sex, race, enslaved status). The finest geography in
the file is the whole city. **This data cannot be mapped**, and nothing below
should be read onto a street or a ward. It answers a different question than
the directories: not *where* did Black Baltimoreans live, but *with whom*.

Two more limits apply everywhere below:

- **Category definitions change between census years**, in ways that break
  naive year-over-year comparison. 1790–1810 have no race-labeled Black
  column at all — only `nothfree`, a catch-all "other free persons except
  Indians not taxed," used here as the standard historians' proxy for free
  Black population. 1820 introduces an explicit "Colored" age-band scheme
  (under 14 / 14–26 / 26–45 / 45+). 1830–1840 switch to a differently-labeled
  "Black" scheme with different age cuts (under 10 / 10–24 / 24–36 / 36–55 /
  55–100). Any claim that crosses the 1810/1820 boundary, or compares
  age-structure percentages across 1820 versus 1830/1840, is flagged
  inline below rather than left to a footnote.
- **Every count here is a floor.** Household-level sums run 0.1–1.9% below
  the independently verified 1820 printed-census figures in most years, and
  1790 is a severe outlier (see below). Read "X households" as "at least X."

## What is genuinely new

The ward maps and directory transcriptions elsewhere in this project can show
where Black Baltimoreans lived on a street. They cannot show whose household
they lived in. This data can, for 1790–1840 — five decades entirely before
the earliest directory year this project maps in detail. Two findings stand
out.

**Free Black Baltimoreans increasingly lived in Black-only households, not
inside white households.** Household-level, mixed (free-Black-and-white)
households fell from 61–67% of all Black-present households in 1790–1800 to
46–47% by 1830–1840. Household size confirms the reading: Black-only
households averaged 3.8–5.8 free Black residents, while mixed households
averaged only 1.6–1.9 — consistent with one or two Black residents, plausibly
servants or dependents, inside a larger white household, versus a full
Black family unit in the Black-only case.

**As slaveholding contracted, it did not simply disappear — an increasing
share of the slaveholders who remained also had free Black people in the
same household.** That share rose from 8.3% of slaveholding households in
1790 to roughly a third (33–36%) from 1820 onward, and this part of the trend
survives an independent robustness check: mean household size among
slaveholders is flat across the whole period (about 9.4–9.8 people in every
year), so the rising overlap is not a mechanical side-effect of slaveholding
households simply getting bigger over time.

## Establishing the Baltimore City subset

Baltimore City is identified as `stateicp==52` (Maryland) & `county==50` &
`city==530`, found empirically (not assumed) by matching each year's
`citypop` tag against the known published city population, and confirmed
stable across all six years. The subset reconciles well in five of six
years; 1790 is a genuine exception.

| Year | Households | Free persons | Enslaved | Total (extract) | `citypop` tag | Coverage vs. known total |
|---|---|---|---|---|---|---|
| 1790 | 1,733 | 9,598 | 1,043 | 10,641 | 13,503 | **78.8% — does not reconcile** |
| 1800 | 3,907 | 23,768 | 2,752 | 26,520 | 26,514 | 100.0% |
| 1810 | 7,275 | 41,816 | 4,649 | 46,465 | 46,555 | 99.9% |
| 1820 | 9,545 | 57,861 | 4,419 | 62,280 | 62,738 | 99.3% |
| 1830 | 12,669 | 75,415 | 4,058 | 79,473 | 80,620 | 98.6% |
| 1840 | 17,118 | 99,073 | 3,152 | 102,225 | 102,313 | 99.9% |

1820 additionally checks against the project's own independently verified
printed-census figures: 4,419 enslaved computed here versus a verified 4,357
(+1.4%), 10,132 free colored versus a verified 10,326 (−1.9%), Black share
23.37% versus a verified 23.40%. This is the single external anchor available
in the whole file, and the whole-pipeline error at that anchor is under two
percent, which is the basis for trusting the same method in years without an
independent check.

**1790 does not reconcile and should not be used for any population-level
claim without this flag.** The `citypop` tag itself is correct (it matches
the known figure and is the correct Baltimore City code, confirmed by
checking every `(county, city, citypop)` group in that year, not just the
largest), but the underlying household rows sum to only 10,641 people against
a tagged population of 13,503 — a 21% shortfall in the rows themselves, not a
filter error. Independent verification reproduced this exact gap and
confirmed it is not an artifact of double-counting or a wrong code. Treat
every 1790 figure below as a floor with materially lower confidence than
1800–1840, not as a peer to the other five years.

## Free Black households versus mixed households, 1790–1840

"Race" here is inferred from household composition — zero free white members
versus zero free Black members — because **no head-of-household race field
exists in this file.** A Black-only household was almost certainly
Black-headed (antebellum schedules recorded one head per household, and an
all-Black household's head was necessarily Black). A mixed household's head
cannot be determined from this data alone; reading mixed households as
usually white-headed follows other scholarship on Black domestics and
dependents inside white households, but this file cannot prove headship for
any specific household.

| Year | Black-only HH (people) | Mixed HH (people) | % of Black-present HH that are mixed | % of free Black people living in a mixed HH |
|---|---|---|---|---|
| 1790 | 44 (168) | 69 (113) | 61.1% | 40.2% |
| 1800 | 273 (1,574) | 541 (1,040) | 66.5% | 39.8% |
| 1810 | 942 (3,998) | 1,043 (1,660) | 52.5% | 29.3% |
| 1820 | 1,488 (6,913) | 1,652 (3,219) | 52.6% | 31.8% |
| 1830 | 2,344 (10,595) | 2,110 (3,769) | 47.4% | 26.2% |
| 1840 | 2,932 (13,641) | 2,531 (4,317) | 46.3% | 24.0% |

The people-level share (right-hand column) does not fall smoothly: it dips at
1810 (29.3%) and partly rebounds at 1820 (31.8%), and that specific wiggle
lands exactly on the year the underlying measure switches from the
`nothfree` proxy to explicit age-banded race columns — read it as a possible
category-boundary artifact, not a real reversal in how Black Baltimoreans
were living. The larger 1790-to-1840 direction, and the household-level
series in the fourth column, both move the same way across the whole period
and are not affected by that single-year wiggle.

## Slaveholding, 1790–1840

Slaveholding households fell from a peak share of 26.0% of all Baltimore
households in 1800 to 9.9% by 1840, even as the absolute number of
slaveholding households rose through 1830 (397 in 1790 to 2,005 in 1830)
because the city itself was growing roughly tenfold over the period. Holding
size shrank throughout: the median enslaved-person count per slaveholding
household fell from 2 to 1 between 1820 and 1830, and mean holding size fell
from 2.63 (1790) to 1.86 (1840).

| Year | All HH | Slaveholding HH | % of all HH | Mean holding size | Median | Enslaved (total) |
|---|---|---|---|---|---|---|
| 1790 | 1,733 | 397 | 22.9% | 2.63 | 2 | 1,043 |
| 1800 | 3,907 | 1,017 | 26.0% | 2.71 | 2 | 2,752 |
| 1810 | 7,275 | 1,755 | 24.1% | 2.65 | 2 | 4,649 (peak) |
| 1820 | 9,545 | 1,876 | 19.7% | 2.36 | 2 | 4,419 |
| 1830 | 12,669 | 2,005 | 15.8% | 2.02 | 1 | 4,058 |
| 1840 | 17,118 | 1,692 | 9.9% | 1.86 | 1 | 3,152 |

The overlap between slaveholding and free Black presence in the same
household is the more interesting number: 33-192-389-669-670-588 households
held both, decade by decade, which is 8.3% of slaveholding households in
1790 and 33–36% in every year from 1820 on. The rise from 8.3% (1790) to
22.2% (1810) is measured on a single consistent proxy (`nothfree`) and is a
clean, real trend. The further jump to ~35% at 1820 crosses the same
category boundary flagged above and is somewhat less clean, though the
overall direction — a shrinking population of slaveholders that overlapped
increasingly, not decreasingly, with free Black households — holds either
way.

**Caution on comparing Baltimore to other cities on this point.** An earlier
draft of this analysis claimed Baltimore was the only one of six major
port cities (with New York, Philadelphia, Washington, Charleston, and New
Orleans) where the enslaved population fell in absolute terms across
1810–1840. **Independent verification found this false on the analysis's own
numbers**: New York's enslaved population also fell every decade over the
same window, and more sharply in relative terms (1,705 in 1810 to 3 in 1840,
a 99.8% decline, versus Baltimore's 4,649 to 3,152, a 32% decline).
Philadelphia's fell on net as well. The defensible distinction is not that
Baltimore was unique in falling, but that Baltimore's decline happened while
slavery remained fully legal in Maryland — no state abolition statute in this
period, unlike New York's 1799/1817/1827 acts or Pennsylvania's 1780 act —
and while the enslaved population stayed numerically substantial (several
thousand people) throughout, rather than an already-small population being
legislated toward zero. Washington DC, Charleston, and New Orleans show no
absolute decline at all in this window; their enslaved populations only grew.

## Household size and sex ratio, free Black versus white, 1820–1840

This question is only answerable for 1820, 1830, and 1840 — 1790–1810 have no
age or sex breakdown for free Black residents at all, only the lump
`nothfree` count. "Free Black household" and "White household" here mean a
household with free residents of only that race present (mixed households
and the small enslaved-only-no-free-residents category, 0.2–0.9% per year,
are excluded from both).

| Year | Black HH mean size / median | White HH mean size / median | Black sex ratio (M per 100 F) | White sex ratio |
|---|---|---|---|---|
| 1820 | 4.65 / 4.0 | 5.74 / 5.0 | 79.1 | 96.8 |
| 1830 | 4.52 / 4.0 | 5.72 / 5.0 | 81.9 | 92.0 |
| 1840 | 4.65 / 4.0 | 5.44 / 5.0 | 80.8 | 89.7 |

Both patterns are stable and legitimate to compare across these three years,
because household size and sex ratio only require summing age/sex bands, not
interpreting where a specific age boundary falls. Free Black households ran
about one person smaller than white households in every year measured, and
consistently female-skewed — roughly four men to five women — while white
households sat close to sex parity throughout. **Age-structure percentages
within these same years are not chainable across 1820 versus 1830/1840**: the
age bands themselves moved (Black: 14/26/45 in 1820 to 10/24/36/55/100 in
1830–1840; white bands changed similarly), so only within-year Black-versus-
white comparisons are valid, not a cross-year age trend line.

## What was independently checked and corrected

Four of the five original findings were independently reproduced from the
raw files and confirmed exactly, including every household count, share,
and mean reported above. One number changed on verification: a secondary
1840 white age-structure figure originally reported as "60+ 4.4%" is
**3.3%** on independent recomputation (2,085 of 63,209 white persons); this
does not touch household size, sex ratio, or any headline claim, and if
anything strengthens rather than weakens the point that free Black
households show a larger elderly share than white households. The
cross-city slaveholding-decline claim above was also corrected on
verification, as described in that section.

## Bottom line

This data extends the project's history five decades earlier than any
directory the project maps, but only in a demographic register: household
composition, not location. Its value here is establishing that Black
Baltimoreans built independent household lives at increasing rates through
1840, and that the shrinking slaveholding population and the growing free
Black population were not two separate stories happening in different
houses — they increasingly overlapped inside the same ones.
