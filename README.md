# Tender Linter

Evidence-linked auditor for Indian Standards citations in draft tender specifications.
Team OnFocus | Team ID 176283 | Smart India Hackathon 2026

> This tool flags issues for the officer to review. It does not approve or reject a tender.

## What it does
Reads a draft tender clause, extracts the standards and products it mentions, checks them against a curated and source-linked dataset, and reports line-level findings with evidence. If the dataset has nothing verified, it says so ("No applicable standard in our dataset") instead of guessing.

## Principles (non-negotiable)
1. The LLM never decides. It extracts. Rules decide.
2. Evidence or silence. No source link and verified date, no finding.
3. Abstain by design. "Not in our dataset" is a valid output.
4. Metadata, not text. We never store or reproduce standard text.
5. Say what was measured. Results are "X of Y on test set Z".
6. The officer stays in charge.

## Status
Scaffold only. Nothing is claimed as built until its milestone passes its "done when" check.
See `docs/PROJECT_SPEC.md` section 16 for milestones M0 to M16.

## Repository layout
```
apps/web/            React + TypeScript reviewer UI
apps/api/            FastAPI app
packages/data/       schema, migrations, seed CSVs, loaders
packages/rules/      rules.yaml, evaluators, message templates
packages/extraction/ provider adapter, prompts, regex, mapping
eval/                corpus, runner, reports
docs/                spec, agent story, handbooks, checklists, prompts
infra/               docker-compose, deployment files
.agents/skills/      Antigravity skills
.agents/workflows/   Antigravity workflows
GEMINI.md            always-on rules for the coding agent
```

## Quick start
```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up
```
- Web health dashboard: [http://localhost:3000](http://localhost:3000) (or [http://localhost:5173](http://localhost:5173))
- API health endpoint: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- API version endpoint: [http://localhost:8000/api/v1/version](http://localhost:8000/api/v1/version)

## Run the skill script tests now
```
pip install pytest ruff pyyaml
pytest -q tests
```

## Key documents
- `docs/PROJECT_SPEC.md` project document (source of truth)
- `docs/agent-story.md` agent story
- `docs/prompts/` all prompts
- `.agents/skills/` skills
- `docs/open-verification.md` facts still to verify from primary sources

## Public repository notice
This repo is public. It contains code, metadata and links only. No secrets, no uploaded tenders, no standard text.

## License
MIT. See `LICENSE`. Standard text is never included; metadata and links only.
