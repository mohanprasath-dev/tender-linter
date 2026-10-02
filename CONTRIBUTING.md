# Contributing to Tender Linter

Thank you for contributing to Tender Linter (Team OnFocus, SIH 2026).
Before writing code, read `GEMINI.md` and `docs/PROJECT_SPEC.md`.

## Non-Negotiable Rules

1. The LLM only extracts. Verdicts come from deterministic rules over database rows.
2. No IS number, year, status, section number, link or statistic enters code, data, docs or the deck unless it exists as a source-linked row in the data layer.
3. Anything marked UNVERIFIED in the spec stays out of product and deck. Unknown fields stay NULL and trigger no claim.
4. Never store, paste, summarise or reproduce text of any Indian Standard. Metadata and links only.
5. Never write "outdated" or "withdrawn" in a message unless rule R02 fires from a verified status.
6. Report accuracy only as "X of Y on test set Z". No bare percentages.
7. The tool never approves or rejects a tender. Keep the officer review banner in the UI.
8. The repository is PUBLIC. Never commit secrets, keys, evidence screenshots, uploaded tenders, private notes, or any standard text.
9. Do not use em dashes in any copy, docs, prompts or messages.

## Conventional Commits

All commit messages must follow the Conventional Commits specification:

- `feat:` A new feature or capability
- `fix:` A bug fix
- `docs:` Documentation changes only
- `test:` Adding or updating tests
- `chore:` Maintenance, configuration, dependencies, or tool updates
- `refactor:` Code change that neither fixes a bug nor adds a feature

Format:
```
<type>: <short imperative summary in lower-case>

[optional body explaining why the change was made]
```

Examples:
- `feat: add version and health routers to api`
- `fix: exclude node_modules from em dash verification test`
- `chore: update docker compose services and ports`

## Development Setup

### Python (Backend)

- Python version: 3.12
- Pinned requirements: `apps/api/requirements.txt`
- Code formatter and linter: Ruff

Commands:
```bash
# Check code style and linting
python -m ruff check .

# Check code formatting
python -m ruff format --check .

# Auto-format code
python -m ruff format .

# Run test suite
python -m pytest -q tests
```

### TypeScript and React (Frontend)

- Node version: 22+
- TypeScript: strict mode enabled in `apps/web/tsconfig.json`
- Bundler: Vite
- Linter: ESLint with typescript-eslint

Commands:
```bash
cd apps/web
npm ci
npm run lint
npm run build
```

## Pull Request Process

1. Create a milestone or feature branch from `main`: `feat/mN-short-name`.
2. Write unit tests first before implementing functionality.
3. Ensure all tests pass (`pytest`, `npm run lint`, `npm run build`).
4. Ensure no unverified claims, secrets, or standard text are added.
5. Fill out the pull request template in `.github/pull_request_template.md`.
6. Every PR must be reviewed by a second team member before merging.
