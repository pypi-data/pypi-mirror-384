---
id: spaps-python-sdk
title: Sweet Potato Python Client
category: sdk
tags:
  - sdk
  - python
  - client
ai_summary: |
  Explains installation, configuration, and usage patterns for the spaps Python
  SDK, including environment setup, async support, and integration guidance for
  backend services.
last_updated: 2025-10-14
---

# Sweet Potato Python Client

> Python SDK for the Sweet Potato Authentication & Payment Service (SPAPS).

This package is under active development. The sections below outline the supported
surface area, test coverage, and release checks we use to keep the client aligned with
the SPAPS API.

## Installation

Install from PyPI:

```bash
pip install spaps
```

For local development inside this repository:

```bash
pip install -e .[dev]
```

## Development

Source for the Python client lives in `src/spaps_client/`. Tests are split between
`tests/unit/` (feature coverage) and `tests/integration/` (build/install guards).
Use `pytest` directly during local TDD, or run the npm script `npm run test:python-client`
from the repo root if you need the full harness. The repository npm scripts automatically
install the dev extras (`pip install -e .[dev]`) before linting, typing, or testing so you
do not have to manage that bootstrap step manually.

```bash
pytest
```

### Quality Checks

Before opening a PR or publishing, run the standard gates:

- `npm run lint:python-client` – ensures the `ruff` configuration passes
- `npm run typecheck:python-client` – validates mypy typing coverage
- `npm run test:python-client` – executes the pytest suite with `respx` mocks
- `npm run build:python-client` – builds wheel/sdist and performs a `twine check`
- `npm run docs:validate-all` – keeps the docs manifest in sync across SDKs
- `npm run publish:python-client` – builds and uploads via `twine` (requires `PYPI_TOKEN`)

### Available clients

- `AuthClient` – wallet, email/password, and magic link flows
- `SessionsClient` – current session, validation, listing, revocation
- `PaymentsClient` – checkout sessions, wallet deposits, crypto invoices
- `UsageClient` – feature usage snapshots, recording, aggregated history
- `SecureMessagesClient` – encrypted message creation and retrieval
- `MetricsClient` – health and metrics convenience helpers

### Quickstart

```python
from spaps_client import SpapsClient

spaps = SpapsClient(base_url="http://localhost:3300", api_key="test_key_local_dev_only")

# Authenticate (tokens are persisted automatically)
spaps.auth.sign_in_with_password(email="user@example.com", password="Secret123!")

# Call downstream services using the stored access token
current = spaps.sessions.get_current_session()
print(current.session_id)

checkout = spaps.payments.create_checkout_session(
    price_id="price_123",
    mode="subscription",
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
)
print(checkout.checkout_url)

spaps.close()
```

Configure retry/backoff and structured logging when constructing the client:

```python
from spaps_client import SpapsClient, RetryConfig, default_logging_hooks

spaps = SpapsClient(
    base_url="http://localhost:3300",
    api_key="test_key_local_dev_only",
    retry_config=RetryConfig(max_attempts=4, backoff_factor=0.2),
    logging_hooks=default_logging_hooks(),
)
```

### Magic Link & Wallet Authentication

```python
# Send a sign-in email
spaps.auth.send_magic_link(email="user@example.com")

# Later, exchange the token from the link for session tokens (persisted automatically)
magic_result = spaps.auth.verify_magic_link(token="token-from-email")
print(magic_result.user.email)

# Wallet flow (Solana/Ethereum)
nonce = spaps.auth.request_nonce(wallet_address="0xabc...", chain="ethereum")
signature = sign_message_with_wallet(nonce.message)  # your wallet integration
wallet_tokens = spaps.auth.verify_wallet(
    wallet_address="0xabc...",
    signature=signature,
    message=nonce.message,
    chain="ethereum",
)
print(wallet_tokens.user.wallet_address)
```

### Current User Profile

```python
profile = spaps.auth.get_current_user()
print(profile.id, profile.email, profile.tier)
```

### Password Reset

```python
spaps.auth.request_password_reset(email="user@example.com")

spaps.auth.confirm_password_reset(
    token="reset-token-from-email",
    new_password="Sup3rStrong!",
)
```

### Product Catalog

```python
catalog = spaps.payments.list_products(category="subscription", active=True, limit=10)
for product in catalog.products:
    print(product.name, product.default_price)

detail = spaps.payments.get_product("prod_123")
print(detail.prices[0].nickname)
```

### Subscription & Billing Helpers

```python
# Fetch active subscriptions for the current user
subs = spaps.payments.list_subscriptions(status="active")
print(subs.subscriptions[0].status)

# Inspect a specific subscription and switch to a new price
detail = spaps.payments.get_subscription(subscription_id="sub_123")
print(detail.plan.interval)

spaps.payments.update_subscription(subscription_id="sub_123", price_id="price_plus")

# Cancel immediately (versus at period end)
spaps.payments.cancel_subscription(subscription_id="sub_123", immediately=True)
```

### Checkout Session Management

```python
# Lookup previously created checkout sessions
session = spaps.payments.get_checkout_session(session_id="cs_test_123")
print(session.payment_status)

sessions = spaps.payments.list_checkout_sessions(limit=5)
print(len(sessions.sessions))

# Force-expire a stale session
spaps.payments.expire_checkout_session(session_id="cs_test_123")
```

```python
# API-key-only guest checkout helpers
guest = spaps.payments.create_guest_checkout_session(
    customer_email="guest@example.com",
    mode="payment",
    line_items=[{"price_id": "price_basic", "quantity": 1}],
    success_url="https://example.com/success",
    cancel_url="https://example.com/cancel",
)

guest_detail = spaps.payments.get_guest_checkout_session(session_id=guest.id)
print(guest_detail.payment_status)

guest_sessions = spaps.payments.list_guest_checkout_sessions(limit=10)
print(guest_sessions.sessions[0].session_id)
```

### Payment History

```python
history = spaps.payments.list_payment_history(limit=20, status="succeeded")
for charge in history.payments:
    print(charge.id, charge.amount, charge.status)

detail = spaps.payments.get_payment_detail(payment_id="pi_123")
print(detail.metadata)
```

### Async Quickstart

```python
import asyncio
from spaps_client import AsyncSpapsClient

async def main():
    client = AsyncSpapsClient(base_url="http://localhost:3300", api_key="test_key_local_dev_only")
    try:
        await client.auth.sign_in_with_password(email="user@example.com", password="Secret123!")
        current = await client.sessions.list_sessions()
        print(len(current.sessions))
    finally:
        await client.aclose()

asyncio.run(main())
```

Async helpers mirror the synchronous API:

```python
nonce = await client.auth.request_nonce(wallet_address="0xabc...", chain="solana")
signature = await sign_message_async(nonce.message)
await client.auth.verify_wallet(
    wallet_address="0xabc...",
    signature=signature,
    message=nonce.message,
    chain="solana",
)
```

```python
profile = await client.auth.get_current_user()
print(profile.username)
```

### Permission Utilities

```python
from spaps_client import PermissionChecker

checker = PermissionChecker(customAdmins=["founder@example.com"])
role = checker.getRole("user@example.com")
if checker.requiresAdmin({"email": "user@example.com"}):
    raise PermissionError(checker.getErrorMessage("admin", role, action="change billing settings"))
```

### Documentation Notes

Additional API references under `docs/api/` include Python usage snippets for sessions,
payments, usage, whitelist, and secure messages. Those guides ship with the repository;
clone the project if you need the full documentation set.
