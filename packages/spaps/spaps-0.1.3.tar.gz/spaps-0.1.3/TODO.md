# Python Client TODO


## Ongoing
- [ ] Keep changelog up to date (`packages/python-client/CHANGELOG.md`)
- [ ] Wire pytest command into repo scripts/CI
- [ ] Align SDK and Python docs for every new feature
- [x] Ensure the docs on PyPI don't have broken links to docs in a private repo (README now self-contained)

## Parity Gaps (from TypeScript SDK)
- [x] Implement auth recovery flows (password reset request/confirm).
- [x] Add auth profile helper for `/api/auth/user` parity.
- [x] Add Stripe catalog read helpers (product listings/details for user-facing flows).
- [x] Add Stripe subscription helpers (list subscriptions, fetch subscription detail).
- [x] Add Stripe payment history helpers (list history, fetch individual payment detail).
- [x] Extend checkout helpers (lookup/list/expire sessions, guest checkout create/get/list/convert).
- [x] Provide client-side permission helpers and token persistence conveniences similar to the TypeScript SDK.

## On Hold (Crypto / Web3)
- [ ] Add wallet utility endpoints (Solana/Ethereum link, verify, network info, typed-data, balance/contract checks).
- [ ] Provide wallet validation and detection helpers comparable to the TypeScript SDK.
- [ ] Stripe admin/catalog management (product CRUD, price creation, product sync, customer portal session).
