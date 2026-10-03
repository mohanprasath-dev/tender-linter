# Tender Linter: Rule Catalogue

**Rule Set Version:** `0.1.0`  
**Source of Truth:** `packages/rules/rules.yaml` and `docs/PROJECT_SPEC.md` Section 6  
**Disclaimer:** *This tool flags issues for the officer to review. It does not approve or reject a tender.*

---

## 1. Overview and Core Philosophy

In Tender Linter, the LLM only extracts entities (IS numbers, years, products, and vague phrases). It never decides whether a clause passes or fails. All verdicts and findings are evaluated deterministically by the rules engine against source-linked rows in the database.

- **Evidence or silence:** Every finding includes a primary source link (BIS catalogue or Gazette) and a verified date.
- **Abstain by design:** If a product or standard is not in the dataset, rule R10 or R01 fires clearly.
- **Language neutrality:** Every rule has an English message and a verified Hindi message where available.

---

## 2. Rule Summary Table

| Code | Title | Severity | Trigger Condition | Required Evidence |
|---|---|---|---|---|
| `R01` | Unknown citation | CANNOT_VERIFY | Cited IS number is not in verified standards table | None (abstains) |
| `R02` | Superseded or withdrawn | ERROR | Standard status is Withdrawn or Superseded | BIS catalogue link, verified date |
| `R03` | Year differs | WARNING | Cited year differs from catalogue year | Catalogue link, verified date |
| `R04` | Part or section mismatch | WARNING | Cited part or section differs from catalogue | Catalogue link, verified date |
| `R05` | Differs from certification list | ERROR | Product requires standard X, but clause cites Y | Certification source link, instrument |
| `R06` | Certification not mentioned | WARNING | Mandatory certification exists but omitted in clause | Certification source link, verified date |
| `R07` | No standard cited | WARNING | Mapped product has verified standards, but none cited | Product-standard map link |
| `R08` | Allied standard absent | INFO | Verified allied link exists but not referenced | Allied links source |
| `R09` | Vague wording | INFO | Vague quality phrase used (e.g., "ISI quality") | Vague term explanation |
| `R10` | Abstain | CANNOT_VERIFY | Product unmapped or no verified rows exist | None (abstains cleanly) |
| `R11` | Internal contradiction | WARNING | Standard cited with differing years/parts in same tender | Clause offset locations |
| `R12` | Malformed citation | INFO | Citation near-matches verified standard (typo) | Suggested candidate standard |
| `R13` | Wrong product family | WARNING | Standard linked to another product family | Product mapping link |
| `R14` | Stale row | INFO | Source row verification date exceeds freshness limit | Verification date |

---

## 3. Detailed Rule Specifications

### R01: Unknown citation
- **Severity:** CANNOT_VERIFY
- **Trigger:** When an IS number cited in a tender specification does not match any entry in the database.
- **English Message:** `"This standard is not in our dataset, so we cannot check it."`
- **Hindi Message:** Placeholder pending fluent review.

### R02: Superseded or withdrawn
- **Severity:** ERROR
- **Trigger:** When the cited standard is verified as Withdrawn or Superseded in the official BIS catalogue.
- **English Message:** `"The catalogue shows this standard as {status} (verified {verified_on})."`
- **Required Evidence:** Direct link to BIS catalogue record with date.

### R03: Year differs
- **Severity:** WARNING
- **Trigger:** When the cited year differs from the catalogue publication year.
- **English Message:** `"The clause cites {cited_year}. The catalogue shows {catalogue_year} (verified {verified_on})."`
- **Required Evidence:** BIS catalogue link with verified date.

### R04: Part or section mismatch
- **Severity:** WARNING
- **Trigger:** When the cited part number or section differs from the published standard structure.
- **English Message:** `"The cited part or section differs from the catalogue record (verified {verified_on})."`
- **Required Evidence:** BIS catalogue link with verified date.

### R05: Differs from certification list
- **Severity:** ERROR
- **Trigger:** When an official order (such as CRO/QCO) mandates standard X for the detected product, but the clause cites standard Y.
- **English Message:** `"The certification list specifies {specified} for this product. This clause cites {cited}. (verified {verified_on})"`
- **Required Evidence:** Gazette notification or BIS Scheme II page link.

### R06: Certification not mentioned
- **Severity:** WARNING
- **Trigger:** When mandatory certification (e.g. BIS CRS or ISI Mark) applies to the product, but the clause fails to mention the certification scheme.
- **English Message:** `"A certification requirement is listed for this product and the clause does not mention it (verified {verified_on})."`
- **Required Evidence:** Gazette notification or BIS Scheme II page link.

### R07: No standard cited
- **Severity:** WARNING
- **Trigger:** When a known product is specified, but no Indian Standard is cited anywhere in the clause.
- **English Message:** `"No standard is cited for this product. The dataset lists {standards} (verified {verified_on})."`
- **Required Evidence:** Product-standard mapping record.

### R08: Allied standard absent
- **Severity:** INFO
- **Trigger:** When verified allied standards exist for the cited standard (e.g., testing methods or safety codes) and are absent from the tender.
- **English Message:** `"A verified link lists {allied} alongside the cited standard (verified {verified_on})."`
- **Required Evidence:** Normative reference record from primary source.

### R09: Vague wording
- **Severity:** INFO
- **Trigger:** When subjective phrases such as "ISI quality", "as per standard", or "best commercial grade" are used without an IS number.
- **English Message:** `"This wording does not name a standard: {explanation}"`
- **Required Evidence:** Curated vague term dictionary explanation.

### R10: Abstain
- **Severity:** CANNOT_VERIFY
- **Trigger:** When a product or item is not present in our curated dataset.
- **English Message:** `"No applicable standard in our dataset."`
- **Required Evidence:** None (abstains explicitly).

### R11: Internal contradiction
- **Severity:** WARNING
- **Trigger:** When the same Indian Standard is cited with conflicting years or conflicting parts across different clauses in the same document.
- **English Message:** `"This standard is cited with different years or parts at {location_a} and {location_b}."`
- **Required Evidence:** Offsets and clause locations within document.

### R12: Malformed citation
- **Severity:** INFO
- **Trigger:** When a citation appears to contain a typographical error or non-standard formatting that closely matches a verified standard.
- **English Message:** `"This citation looks close to {candidate}. Please confirm."`
- **Required Evidence:** Candidate recommendation requiring officer confirmation.

### R13: Wrong product family
- **Severity:** WARNING
- **Trigger:** When a cited standard belongs to a completely different product family than the one specified in the clause.
- **English Message:** `"The dataset links this standard to {other_product}, not this product (verified {verified_on})."`
- **Required Evidence:** Product mapping table source link.

### R14: Stale row
- **Severity:** INFO
- **Trigger:** When a database row supporting a finding was verified longer ago than the configured freshness window (`STALE_DAYS`).
- **English Message:** `"A source row used here was last verified on {verified_on}."`
- **Required Evidence:** Stale timestamp from provenance record.
