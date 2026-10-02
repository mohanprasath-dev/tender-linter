# Security, Privacy and Legal Checklist (M14 sign-off)

- [ ] Roles enforced and tested: Reviewer, Curator, Verifier, Admin
- [ ] Verifier cannot be the Curator of the same row (test exists)
- [ ] Passwords hashed; optional SSO documented
- [ ] Encryption in transit; uploads encrypted at rest
- [ ] Default retention short; one-click deletion works
- [ ] Only clause text needed is sent to a hosted model
- [ ] Provider data-use terms read and recorded; until then only synthetic or public text is sent
- [ ] Local-model option documented
- [ ] Every stored evidence image reviewed for standard text
- [ ] No standard text anywhere in repo, database or exports
- [ ] Rate limits, input size limits, upload scanning in place
- [ ] Dependency scan and secret scan pass in CI
- [ ] Audit log append-only
- [ ] Disclaimer banner on every screen and in every export
- [ ] Wording and disclaimers reviewed by a qualified person
- [ ] Repo is public from day one: secret scanning and push protection on, history scanned before each release, no evidence files or private notes committed
