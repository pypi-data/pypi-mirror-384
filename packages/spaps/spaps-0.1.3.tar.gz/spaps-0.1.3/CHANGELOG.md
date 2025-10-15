# Changelog

# Changelog

## 0.1.3 - 2025-10-14

- Add subscription listing, detail, cancellation, and plan swap helpers to match the TypeScript SDK.
- Extend checkout tooling with session lookup/list/expire plus guest session create/get/list/convert flows.
- Surface Stripe payment history summaries and payment detail fetches.
- Introduce `spaps_client.permissions` with client-side role/permission utilities.
- Refresh README examples covering the new helpers.

## 0.1.2 - 2025-10-12

- Add a convenience helper used by invoice lookups to standardize crypto invoice paths; no
  behavior changes but keeps client logs consistent.

## 0.1.1 - 2025-10-11

- Widen `httpx` dependency range to `<0.29` so downstream apps can stay on FastAPI’s default
  stack (0.28.x) without local overrides.
- No code changes—existing HTTP and auth/session tests pass against `httpx` 0.27 and 0.28.

## 0.1.0 - 2025-10-11

- First public release on PyPI under the name `spaps`.
- Adds synchronous and asynchronous clients mirroring the TypeScript SDK, including
  sessions, payments (crypto included), usage, whitelist, secure messages, and metrics helpers.
- Provides configurable retry/backoff handling, structured logging hooks, and token storage
  abstractions (in-memory & file-backed).
- Ships lint (`ruff`), type checking (`mypy`), coverage enforcement, and integration smoke
  tests wired into the release workflow.
- Updates documentation with Python quickstart examples and a dedicated backend guide.
