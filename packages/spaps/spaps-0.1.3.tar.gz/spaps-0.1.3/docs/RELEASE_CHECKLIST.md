# Python Client Release Checklist

## Pre-Release
- [ ] Update `packages/python-client/CHANGELOG.md` with new version entry
- [ ] Bump version in `packages/python-client/pyproject.toml` and `packages/python-client/src/spaps_client/__init__.py`
- [ ] Ensure dependencies are up to date and version ranges still valid
- [ ] Verify `LICENSE` file reflects current year and ownership

## Validation
- [ ] Run `npm run test:python-client`
- [ ] Run `pytest -q` from `packages/python-client` (should match script output)
- [ ] Run `python -m build` in `packages/python-client` and confirm wheel + sdist are produced
- [ ] Install built wheel into a clean virtual environment and smoke-test `AuthClient` and `SessionsClient`

## Documentation
- [ ] Update `packages/python-client/README.md` with version highlights and usage changes
- [ ] Update `docs/api/wallet-authentication.md` and `docs/api/sessions.md` if request/response shapes changed
- [ ] Sync any environment variable guidance in `.env.example`
- [ ] Ensure `docs/manifest.json` references new tests or docs as needed

## Release
- [ ] Trigger the `Publish Python Client` workflow with the appropriate bump type (prefer dry run first)
- [ ] Create git tag `python-client-vX.Y.Z`
- [ ] Publish package to PyPI (or internal index) using `python -m build` outputs
- [ ] Notify downstream teams and update relevant tickets/incidents
