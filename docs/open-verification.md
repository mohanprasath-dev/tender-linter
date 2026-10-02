# Open Verification Items and Decisions

Owner: team. Nothing below is a fact until a primary source is read and logged.

## A. Facts to verify
| Item | Needed from | Status |
|---|---|---|
| Final submission deadline and any extension | Portal and college SPOC | Open |
| Theme, category and problem statement ID as shown on the portal (spec says SIH26108) | Portal statement page | Open |
| Team ID 176283 | Portal | Supplied, confirm |
| Free-tier limits, models, Hindi support, data terms per provider | Run `docs/prompts/fact-gathering.md` | Open |
| IS 302-2-25: year, status, newer edition | BIS catalogue record | Open |
| IS/IEC 62368-1: catalogue status, amendments | BIS catalogue record | Open |
| IS 13252 (Part 1) amendments; CCTV listing and migration date | Gazette order text and link | Open |
| IS 302-1 | BIS catalogue record | Open |
| Cement QCO: which order is current, which IS numbers it names | Gazette entries | Open |
| Exact model name and version used for extraction | Bake-off result | Open |
| One measured impact number with working | Evaluation harness output | Open |
| Whether any procurement portal permits integration | Portal operator | Open |
| URLs for BIS Scheme II page and catalogue records used in seed rows | Team, from the pages already read | Open |
| Names of first and second verifier for each seed row | Team | Open |
| Whether SIH terms restrict the repo license or visibility | SIH guidelines or SPOC | Open |
| Certification rule rows (scheme, instrument, specified standard) for laptops, adaptors and microwave ovens; needed for R05 and R06 | BIS Scheme II page | Open |
| Catalogue title for IS/IEC 62368 Part 1 | BIS catalogue record | Open |

## B. Decisions the spec leaves open (team must decide, then add a test)
1. R01 vs R12: a one-digit typo (T10) is also "not in dataset". Proposal: R12 suppresses R01 for that citation.
2. R07 with R09: "ISI quality" with no number (T06) fires both. Proposal: allow both.
3. R03 with R11: same standard cited with two years (T09) also differs from the verified year. Proposal: allow both.
4. What counts as "mentions certification" for R06: needs a curated term list in English and Hindi (for example CRS, BIS registration). The spec does not define it.
5. R05 and R06 can both fire on one clause (T01). Confirm this is intended.
6. Freshness limit (`STALE_DAYS`) value.
7. Published threshold for labelling a language "supported".
