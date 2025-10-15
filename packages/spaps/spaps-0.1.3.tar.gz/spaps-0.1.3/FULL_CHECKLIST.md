# Python Client Completion Checklist

## Feature Parity
- [x] Auth: email/password login & signup helpers
- [x] Auth: magic link flow
- [x] Auth: logout & token revocation
- [x] Auth: whitelist queries/mutations
- [x] Sessions: list sessions
- [x] Sessions: touch session endpoint
- [x] Sessions: delete session / revoke
- [x] Payments: usage balance/history endpoints
- [x] Payments: update payment method
- [x] Payments: Stripe checkout (existing)
- [x] Payments: Stripe payment intent (existing)
- [x] Payments: wallet deposit/status (existing)
- [x] Payments: subscription details/cancel (existing)
- [x] Payments: crypto invoices (create/get/reconcile)
- [x] Payments: crypto webhooks signature helper
- [x] Usage API: feature list/record/history wrappers
- [x] Admin: secure messages routes
- [x] Admin: whitelist management
- [x] Admin: metrics endpoints
- [ ] Docs/search/openapi utilities (if applicable)

## SDK Ergonomics
- [x] Token storage abstraction (file/memory/extensible)
- [x] Retry/backoff policy with configurable strategy
- [x] Logging hooks & structured errors
- [x] Async client variants (optional dependency)
- [x] Type hints/completion for all public APIs
- [x] Rich README with quickstart & API reference
- [ ] CHANGELOG.md with semantic version entries

## Testing & Quality
- [x] Integration smoke tests using mock server
- [x] Coverage tracking / threshold enforcement
- [x] Type checking (mypy or pyright)
- [x] Lint/format (ruff or black) configuration
- [x] Twine check in release flow
- [x] CI matrix for Python 3.9-3.12

## Documentation Sync
- [x] Update SDK_QUICKSTART with Python section
- [x] Add dedicated guide `docs/guides/python-backend.md`
- [x] Ensure API docs link to Python examples (in progress)
- [x] Update docs/manifest entries for all endpoints
- [x] Reference Python client in AGENTS documentation

## Automation & CI/CD
- [x] Add `prepush` hook entry for `npm run test:python-client`
- [x] Add npm scripts for build/release (`build:python-client`, `publish:python-client`)
- [x] GitHub Actions workflow for lint/test/build (`.github/workflows/python-client.yml`)
- [x] Release workflow with PyPI token (manual trigger)
- [ ] Dependabot/Renovate rules for Python deps (optional)
- [ ] Release checklist enforced (link in docs)

## Release Readiness
- [ ] Decide package registry (PyPI vs internal)
- [ ] Configure credentials/secrets for publishing
- [ ] Version compatibility policy with backend
- [ ] Beta release announcement plan
- [ ] Support channel / issue templates updated

## Post-Launch
- [ ] Monitor downloads/errors
- [ ] Collect feedback for next iteration
