# Seed data (DRAFT)

These CSVs hold only what the spec lists as verified on 2 Oct 2026. Source URLs, verifier names, evidence references and second checks are empty on purpose: they were not supplied, and nothing here may be invented.

Fill them from the official pages, then run:
```
python .agents/skills/provenance-row-check/scripts/check_provenance.py packages/data/seed/*.csv
```
Empty cells for year, status, amendments mean "not verified". Do not load UNVERIFIED items listed in `docs/curator-handbook.md`.
Certification rules and allied links are not seeded: the spec does not give verified rows for them yet.
