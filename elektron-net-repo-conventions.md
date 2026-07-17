# Elektron Net — Conventions for Forked Third-Party Repos

**Status:** working notes, derived from the existing `elektron-net-*` repos
(`elektron-net-electrs` in particular, itself a fork of `romanz/electrs`) and
applied here to `elektron-net-electrum` (fork of `spesmilo/electrum`). Kept
in this file so the next fork of a third-party project in this family starts
from the same baseline instead of re-deriving it.

## 1. Chain parameters are sourced from the node, not re-derived

The single source of truth for every network constant (HRP, Base58/BIP32
version bytes, genesis hash, `pchMessageStart`, SLIP-44 coin type, block
time, pruning depth) is the `elektron-net` node itself:

- `src/kernel/chainparams.cpp` (`CMainParams`) — HRP, Base58 prefixes,
  xpub/xprv headers, genesis hash/merkle root, `pchMessageStart`, port.
- `src/wallet/walletutil.cpp` (`GenerateWalletDescriptor`) — the exact
  descriptor derivation paths (dual-track `1370'`/legacy `0'`).
- `doc-elektron/guideline-wallet-integration.md` and
  `doc-elektron/CHANGELOG-slip44-coin-type.md` — the written rationale.

Never invent or guess a value (genesis hash, checkpoint, server address)
that isn't backed by one of these. Where a fork needs data that doesn't
exist yet (e.g. real checkpoints, a running Electrum-protocol server
address), ship an empty/valid placeholder and say so explicitly in the
fork's own doc — don't fabricate plausible-looking values.

## 2. Fork identification

- The fork is **permanent and explicit**, not a temporary patch queue.
  State this up front in the README (see `elektron-net-electrs/README.md`
  for the exact tone/format to mirror): what upstream project and version
  this is based on, and a link to the design-rationale document in
  `elektron-net/doc-elektron/`.
- A dedicated `doc/elektron.md` (or `doc-elektron/` if the upstream project
  already has its own `doc/`) collects **only what is actually implemented
  in this fork** — not the full design discussion (that stays in
  `elektron-net/doc-elektron/guideline-*-integration.md`).
- Upstream's own `LICENCE`/`LICENSE`, `AUTHORS`, and copyright headers are
  **never modified or removed** — this family of forks is MIT-derived
  throughout, and MIT requires exactly that. New Elektron-specific files
  get their own copyright header; existing upstream files keep theirs.
- Upstream's `CONTRIBUTING.md` workflow is carried over unchanged unless a
  fork-specific reason exists to diverge from it.
- The underlying package/binary/module name from upstream (e.g. Python
  package `electrum`, CLI script `electrum/electrum`) stays as-is — only
  user-facing branding (display name, desktop entry, app-data folder,
  icons, about-box strings) is renamed. Renaming the internal package
  would break tooling/build scripts for no user-visible benefit — the same
  restraint `electrum-ltc` and other established forks apply.

## 3. Release automation (GitHub Actions)

Established pattern across `elektron-net` (Windows installer) and now
`elektron-net-electrum`:

- Trigger: `on: push: tags: ['v*']` (plus `workflow_dispatch` for manual
  re-runs).
- Version string is read from the fork's own version file, not
  hand-maintained in the workflow.
- Release is created with `softprops/action-gh-release`, name pattern
  `"<Product Name> <version>"`, `prerelease:` derived from the version
  string (e.g. contains `-rc`).
- Every platform build job uploads its own artifact; the release job
  collects and attaches all of them in one GitHub Release rather than
  creating one release per platform.
- Artifact filenames are versioned and product-named, e.g.
  `elektron-net-windows-v4.0.4_setup.exe` /
  `elektron-electrum-windows-v1.0.0.exe` — never bare `setup.exe`.

## 4. What this repo (`elektron-net-electrum`) does with it

See `doc/elektron.md` for the concrete, implemented differences from
upstream Electrum (chain parameters, branding, release workflow). Open
items tracked there rather than silently resolved: BOLT11 HRP (Lightning
not in scope for this milestone), automatic dual coin-type scan on restore,
testnet/regtest chain parameters (only mainnet forked so far), and the
legacy Base58 collision UI warning (§4.4 of the wallet-integration
guideline, MUST-level, tracked as follow-up work). `servers.json` now
lists one live instance, `electrs.elektron-net.org:50002`.
