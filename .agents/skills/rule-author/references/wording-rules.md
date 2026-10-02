# Wording rules (spec 6.3)

- Never say "outdated" or "withdrawn" unless R02 fires from a verified status.
- R05 message: "The certification list specifies [standard] for this product. This clause cites [other]." No claim about the cited standard's catalogue status.
- Every message states the verified date and links the source.
- CANNOT_VERIFY findings are shown in a separate, visually quiet group.
- Severities: ERROR (conflicts with a verified source), WARNING (probable omission), INFO (style or clarity), CANNOT_VERIFY (data missing, no claim).
- Conflict: when two verified sources disagree, flag the row CONFLICT and downgrade dependent findings to CANNOT_VERIFY.
