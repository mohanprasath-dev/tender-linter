# Data Dictionary

Source: `PROJECT_SPEC.md` section 3. Every row in every table needs source URL, verified date, verifier and evidence reference. Unknown stays NULL.

## standards
| Field | Type | Notes |
|---|---|---|
| id | integer | primary key |
| is_number | text | normalised, e.g. `IS 302-2-25` |
| part | text, nullable | |
| title | text | as shown in the BIS catalogue |
| publication_year | integer, nullable | NULL if not verified |
| status | Active / Withdrawn / Superseded / UNKNOWN | UNKNOWN triggers no status claim |
| superseded_by_id | integer, nullable | foreign key |
| amendments | text, nullable | as shown in catalogue; NULL if not verified |
| catalogue_url | text | official catalogue record |
| verified_on | date | |
| verified_by | text | person |
| second_checked_by | text | second person; must differ from verified_by |
| evidence_ref | text | screenshot or PDF in object store |

## products
id, canonical_name, synonyms_en, synonyms_hi, synonyms_other (JSON arrays, curated by hand), family.

## product_standard_map
product_id, standard_id, relation (PRIMARY / NORMATIVE / TEST_METHOD / TERMINOLOGY / INSTALLATION / RELATED), source_url, verified_on, verified_by, second_checked_by, evidence_ref.

## certification_rules
product_id, scheme (CRS / BIS_MARK / QCO / HALLMARKING / NONE_FOUND), specified_standard_id, instrument, source_url, verified_on, verified_by, second_checked_by, evidence_ref, effective_from (nullable), transition_until (nullable). Dates only from a read source text.

## allied_links
from_standard_id, to_standard_id, relation, plus the same provenance fields. Only rows read from an official source.

## vague_terms
phrase, language, explanation. Curated by hand.

## audit_log, user
Append-only audit log with before and after values. Roles: Reviewer, Curator, Verifier, Admin. Verifier cannot be the Curator of the same row.

## Note on `second_checked_by`
The spec requires two-person sign-off (section 3.3 step 4). This field records the second person so the database can enforce it. The CSV seed files use the same column.
