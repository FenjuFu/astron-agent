# AGENTS.md

Guidance for AI coding agents working in the **astron-agent** repository — an
enterprise-grade, commercial-friendly agentic workflow platform for building
SuperAgents.

## Project layout

This is a multi-language monorepo. A unified `Makefile` with intelligent
project detection drives the common workflows across all languages.

- `console/` — the application console.
  - `console/frontend/` — web UI (TypeScript / React).
  - `console/backend/` — console backend (Java, Spring Boot).
- `core/` — backend microservices.
  - `core/agent/` — agent execution engine (Python).
  - `core/workflow/` — workflow orchestration (Python).
  - `core/knowledge/` — knowledge base service (Python).
  - `core/memory/`, `core/plugin/` — supporting services (Python).
  - `core/common/` — shared Python libraries.
  - `core/tenant/` — tenant service (Go).
- `docker/` — Docker Compose deployment manifests.
- `helm/` — Kubernetes Helm charts.
- `makefiles/` — modular build-system components included by the root `Makefile`.
- `docs/`, `examples/`, `faq/`, `website/` — documentation and samples.

## Toolchain

- **Python 3.9+** — core services.
- **Go 1.21+** — tenant service.
- **Java 21+** — console backend.
- **Maven 3.8+** — Java project management.
- **Node.js 18+** — console frontend (TypeScript).
- **Docker & Docker Compose** — containerized services.

## Common commands

Run these from the repository root; the Makefile detects active projects
automatically. In a single-project context, run them from the corresponding
subdirectory instead.

- `make setup` — one-time environment setup (installs tools, configures git
  hooks and branch strategy).
- `make check` (alias `make lint`) — quality check including formatting and
  linters (flake8 / mypy / pylint, ESLint / tsc, golangci-lint / staticcheck,
  Checkstyle / PMD / SpotBugs). CI is check-only and does not auto-fix.
- `make format` — apply formatters (black + isort, prettier, gofmt + goimports
  + gofumpt, Spotless).
- `make test` — run tests across active projects (per-language targets such as
  `make test-java` also exist).
- `make build` — build active projects.
- `make ci` — full pipeline: check + test + build.
- `make status` / `make info` — project status and tool/dependency info.

## Testing instructions

- Run `make test` before opening a PR; add or update tests for code you change.
- Pre-commit hooks run the linters. Install them with `make setup`, and run a
  specific hook with e.g. `pre-commit run eslint-check --all-files` or
  `pre-commit run golangci-lint --all-files`.
- A change must have no linting errors or warnings and must pass strict type
  checking (TypeScript / Python).

## Running locally

The quickest way to run the full stack is Docker Compose:

```bash
cd docker/astronAgent
cp .env.example .env
# edit .env to fill in required configuration
docker compose -f docker-compose-with-auth.yaml up -d
```

- Application frontend (nginx proxy): http://localhost/
- Casdoor admin interface: http://localhost:8000

## Code style

| Language   | Format                        | Lint                              | Rules                              |
| ---------- | ----------------------------- | --------------------------------- | ---------------------------------- |
| Go         | gofmt + goimports + gofumpt   | golangci-lint + staticcheck       | Go standard format, complexity ≤10 |
| Java       | Spotless (Google Java Format) | Checkstyle + PMD + SpotBugs       | Google Java Style, complexity ≤10  |
| Python     | black + isort                 | flake8 + mypy + pylint            | PEP 8, complexity ≤10              |
| TypeScript | prettier                      | eslint + tsc                      | ESLint rules, strict typing        |

## PR instructions

- Branch naming follows the project's strategy; helpers exist, e.g.
  `make new-feature name=<short-name>`, `make new-bugfix name=<short-name>`.
- Before committing, run `make check` and `make test` and make sure pre-commit
  hooks pass.
- Follow the [Conventional Commits](https://www.conventionalcommits.org/)
  specification for commit messages and keep PRs focused.
- See `CONTRIBUTING.md` for the full contribution workflow.
