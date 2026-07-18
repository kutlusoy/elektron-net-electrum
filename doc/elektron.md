# Elektron Net Fork Notes

This repository, `elektron-net-electrum`, is a **permanently-diverged fork**
of [`spesmilo/electrum`](https://github.com/spesmilo/electrum), forked at
upstream **v4.8.0**, adapted for
[Elektron Net](https://github.com/kutlusoy/elektron-net) (ELEK). This file
documents only what is actually implemented here; the full design rationale
and phased plan live in the elektron-net repo:
[`doc-elektron/guideline-wallet-integration.md`](https://github.com/kutlusoy/elektron-net/blob/main/doc-elektron/guideline-wallet-integration.md).

The conventions applied here follow the precedent set by this family's
other third-party forks (`elektron-net-electrs` in particular): permanent,
explicitly-labeled fork with a link back to the design rationale; upstream
`LICENCE`/`AUTHORS` preserved unmodified; a `doc/elektron.md` covering only
what's actually implemented; `v*`-tag-triggered releases via
`softprops/action-gh-release`.

## Chain parameters (`electrum/constants.py`, `BitcoinMainnet`)

Values are sourced from `elektron-net`'s own `src/kernel/chainparams.cpp`
(`CMainParams`) and `src/wallet/walletutil.cpp`
(`GenerateWalletDescriptor`) -- treat those as ground truth for any future
change here, not this file.

| Parameter | Value |
|---|---|
| `SEGWIT_HRP` (Bech32) | `be` (`be1q...`/`be1p...`) |
| `WIF_PREFIX` / `ADDRTYPE_P2PKH` / `ADDRTYPE_P2SH` | `0x80` / `0` / `5` -- **intentionally identical to Bitcoin mainnet** |
| `XPRV_HEADERS['standard']` / `XPUB_HEADERS['standard']` | `0x0488ade4` / `0x0488b21e` -- also identical to Bitcoin, no change needed |
| `GENESIS` | `00000006b054338443f1a5d5534df21eab0d13232028158ae198edbb169f9dad` |
| `BIP44_COIN_TYPE` | `1370` (registered SLIP-44 coin type, symbol `ELEK`) |
| `BOLT11_HRP` | placeholder, same as `SEGWIT_HRP` -- **not a decision**, see Open Items |

**Legacy Base58 collision (guideline SS4.4):** because `WIF_PREFIX`,
`ADDRTYPE_P2PKH`, and `ADDRTYPE_P2SH` are byte-identical to Bitcoin
mainnet, a legacy Elektron Net key or address is also a valid Bitcoin
mainnet one, and vice versa. This is a MUST-level UI requirement from the
wallet-integration guideline (default to Bech32 receive addresses, warn on
legacy import) that is **not yet implemented in this fork's UI** -- tracked
as an open item below, not silently done.

**Dual coin-type scanning (guideline SS3.1, MUST):** wallets created on
`elektron-net` before 2026-07-15 derive at the legacy `0'` path, not
`1370'` (see `elektron-net`'s
`doc-elektron/CHANGELOG-slip44-coin-type.md`). This fork sets
`BIP44_COIN_TYPE = 1370` for new wallets/restores, but does **not**
automatically also scan `0'` on restore. Until that's implemented,
restoring a pre-2026-07-15 seed with its original balance requires manually
specifying the legacy derivation path (e.g. `m/84'/0'/0'`) in Electrum's
"Restore from seed" advanced options.

## Server backend (`electrum/chains/mainnet/`)

- `servers.json`: lists the one known live `elektron-net-electrs` instance,
  `electrs.elektron-net.org`, port `50002`, listed under the plaintext
  `'t'` key -- **not** `'s'` (SSL), since electrs itself never terminates
  TLS (see `elektron-net-electrs/doc/config.md`) and nothing in front of it
  currently does either. The port itself comes from `elektron-net-stack`'s
  `install-elektron-stack.sh` (`electrum_rpc_addr = "0.0.0.0:50002"` in the
  generated `electrs.toml`), not electrs' own upstream default of `50001`.
- `checkpoints.json`, `fallback_lnnodes.json`: intentionally empty (`[]` /
  `{}`). No real Elektron Net Electrum-protocol checkpoints exist yet, and
  no Lightning routing/trampoline nodes exist on the network at all (see
  Open Items). Electrum handles an empty checkpoints file correctly --
  it just does a full header sync instead of jumping ahead from a trusted
  checkpoint.

## Header-chain difficulty verification (`electrum/blockchain.py`)

Electrum SPV clients independently verify the header chain's proof-of-work
(not just trust the server), which means `blockchain.py` needs to know this
chain's real difficulty rules -- carried over from upstream, it still had
Bitcoin's own values, and header sync failed against a real Elektron Net
node as a result (confirmed live: `unexpected bad header during binary`
trying to validate height 1). Fixed:

- `MAX_TARGET`: was Bitcoin's `powLimit` (compact `0x1d00ffff`); now
  Elektron Net's own (compact `0x1f7fffff`, confirmed against a real
  height-1 header from the network -- much easier, consistent with a young,
  low-hashrate chain).
- `TARGET_TIMESPAN`: was Bitcoin's 14-day retarget window; now Elektron
  Net's 1.4 days (`nPowTargetTimespan = 2016 * 60`, from
  `elektron-net/src/kernel/chainparams.cpp`). The retarget *interval in
  blocks* (`CHUNK_SIZE = 2016`) was already correct -- only the real-time
  window differs, since Elektron Net blocks are 10x faster (60s vs 600s).
- **"Stoic Awakening"**: a temporary, Elektron-Net-specific min-difficulty
  escape, active for heights `[1, 150000)` (`STOIC_AWAKENING_START_HEIGHT`/
  `STOIC_AWAKENING_END_HEIGHT` in `blockchain.py`). Between normal 2016-block
  retarget points, if a block's timestamp is more than 120s (2x target
  spacing) after its parent's, its target drops to `MAX_TARGET` for that one
  block; otherwise the block carries forward the last non-escape block's
  bits (walking back across chained escape blocks, stopping at a retarget
  boundary regardless). This is structurally identical to Bitcoin's own
  testnet min-difficulty rule, just time-boxed on mainnet instead of
  permanent -- see `elektron-net/src/pow.cpp` (`GetNextWorkRequired`,
  `PermittedDifficultyTransition`) for the source of truth, and
  `elektron-net/doc-elektron/CHANGELOG-stoic-awakening-retirement.md` for
  why/when it retires. Because the current chain tip is still well inside
  this window, this isn't an edge case -- it affects the *majority* of
  currently-existing mainnet header history, not just early blocks.
  Implemented in `Blockchain.get_expected_target()`, used by both
  `verify_chunk()` (bulk header-chunk sync) and `can_connect()`
  (single-header sync/tip-following); tests in `tests/test_blockchain.py`
  (`TestStoicAwakeningDifficulty`).
- **Chunk-boundary retarget within the Stoic Awakening window: trust the
  header's own bits, don't recompute.** The classic Bitcoin-style retarget
  formula (`get_target()`, ported line-for-line from `elektron-net`'s
  `CalculateNextWorkRequired()`) was applied at every `height % CHUNK_SIZE
  == 0` boundary regardless of Stoic Awakening state, on the assumption
  (stated in `elektron-net/src/pow.cpp`, see below) that boundaries are
  always classic-retarget, unaffected. This was proven wrong against real
  network data: at height 10080 (a boundary, `10080 == 5*CHUNK_SIZE`), the
  real chain's block 10079 (last block of the old chunk) was an
  escape/min-difficulty block (`bits=0x1f7fffff`), yet the real block 10080
  had a genuinely *harder* bits value (`bits=0x1e7c9c07`) -- cross-checked
  independently via a live Elektron Net node's local header data and the
  `mempool.elektron-net.org` block explorer, both agreeing exactly (hash,
  prev_hash, timestamp, bits, nonce). Applying `CalculateNextWorkRequired()`
  with an escape-block (`bits==powLimit`) baseline can mathematically only
  ever yield `powLimit` again (any timespan ratio >= 1 gets clamped back to
  the ceiling) -- it can never predict a harder value. This means the
  deployed node's actual boundary-difficulty algorithm differs from what's
  readable in this checkout of `elektron-net/src/pow.cpp` in some way that
  couldn't be reverse-engineered from source alone (possibly a version
  difference, or logic elsewhere not yet located).

  Rather than risk being wrong again on some future boundary, chunk
  boundaries inside `[STOIC_AWAKENING_START_HEIGHT,
  STOIC_AWAKENING_END_HEIGHT)` now trust the boundary header's own claimed
  `bits` directly (same principle already used for non-boundary escape
  blocks), bounded so it can't claim to be easier than the network's own
  absolute floor (`target > MAX_TARGET` is rejected). Real proof-of-work
  against the claimed target is still enforced by `verify_header()`. This
  is a deliberate simplification, not an oversight: hash-chain linkage and
  real-PoW-effort are still fully verified; only the specific "does this
  boundary's claimed difficulty match an independently *computed* expected
  value" check is relaxed, for the window where that computation has been
  shown unreliable. Boundaries outside the window still use the classic
  `get_target()` computation unchanged. See
  `tests/test_blockchain.py::TestStoicAwakeningDifficulty` (the
  `test_stoic_boundary_*` and `test_post_stoic_boundary_*` tests) for the
  exact real-world numbers and the boundary behavior this locks in.

  `STOIC_AWAKENING_END_HEIGHT = 150000` is confirmed active on
  `elektron-net`'s `main` branch: `chainparams.cpp` sets
  `consensus.StoicAwakeningEndHeight = 150000`, gated into `pow.cpp`'s
  `GetNextWorkRequired()`/`PermittedDifficultyTransition()` via a
  `stoicAwakeningActive` check (`... && (StoicAwakeningEndHeight == -1 ||
  height < StoicAwakeningEndHeight)`). This end-height gating only affects
  *whether the min-difficulty escape applies at all* (the non-boundary
  carry-forward/escape logic, already correctly implemented and unaffected
  by this whole investigation) -- it does not change
  `CalculateNextWorkRequired()`, the classic-retarget function used at
  chunk boundaries, which is identical to what's described above. So this
  doesn't resolve or explain the height-10080 boundary discrepancy; the
  boundary-trust-the-header relaxation above is still the fix.
- **Not fixed / known follow-up:** `chainwork_of_header_at_height()` /
  `get_chainwork()` (used to pick between competing valid header chains on a
  reorg, not for header validation itself) still assume uniform difficulty
  across a whole 2016-block chunk, which undercounts/overcounts real work
  for chunks inside the Stoic Awakening window. Doesn't affect normal
  single-chain sync; only matters if this client ever needs to resolve a
  fork/reorg while still inside the window.
- **This is not Electrum-specific.** Any wallet doing independent SPV
  header verification for Elektron Net needs this same logic, most notably
  the Stoic Awakening escape, which has no equivalent in stock Bitcoin
  Core-derived difficulty code. Documented for other wallet implementers in
  `elektron-net/doc-elektron/guideline-spv-header-difficulty-verification.md`.

## Branding

Display name is "Elektron Electrum" throughout (window titles, About
dialog, desktop entry, AppStream metainfo, Windows installer
`PRODUCT_NAME`, Android `title`/`package.name`/`package.domain`, macOS
`.app` bundle name). Following this fork family's convention, the
**underlying Python package (`electrum`), CLI script (`electrum/electrum`),
and `bitcoin:`/`lightning:` URI scheme handlers are unchanged** -- renaming
those would be a much larger, riskier change (URI parsing, packaging
tooling) for no user-visible benefit at this stage; tracked as a possible
follow-up, not done silently.

The app-data directory is `~/.elektron-electrum` (POSIX) /
`%APPDATA%\Elektron Electrum` (Windows) -- deliberately distinct from
upstream Electrum's `~/.electrum` / `%APPDATA%\Electrum`, so both can be
installed side-by-side on the same machine without sharing wallet files.
`$ELECTRUMDIR` still overrides this, unchanged from upstream.

Icons are regenerated from Elektron Net's own logo
(`electrum/gui/icons/elektron_electrum_logo.svg`, the same mark used across
`elektron-net-pool-ui`/`elektron-net-ppool-ui`/the `*-startos` repos) at
every size upstream's build tooling expects (`.ico`, `.icns`, Android
adaptive-icon foreground/background, presplash, tray icons). The
`electrum_text.png` wordmark next to the round logo on the terms-of-use
screen was regenerated as a plain rendered label ("Elektron Electrum",
DejaVu Sans) rather than a designed wordmark -- fine for now, but a real
designer pass would look better.

## Release automation

`v*`-tag releases follow this fork family's release convention: version is
read from `electrum/version.py` (`ELECTRUM_VERSION`, set to `4.0.4` for this
initial release rather than continuing upstream Electrum's `4.8.0` -- chosen
to match `elektron-net`'s own version at the time of this release, marking
the node version this wallet is known compatible with; the two lineages are
expected to diverge from here on, this is a starting marker, not a promise
to track each other going forward), and
`softprops/action-gh-release` attaches every platform build (Windows,
Android, AppImage, source tarball) to one GitHub Release per tag.

## Open items (not silently resolved)

- **Bech32-default + legacy-import warning (guideline SS4.4, MUST):** not yet
  implemented in the wallet UI. Chain parameters make legacy addresses
  valid on both Elektron Net and Bitcoin mainnet; the UI does not yet
  warn about this.
- **Automatic dual coin-type scan on restore (guideline SS3.1, MUST):**
  restoring a pre-SLIP-44 wallet by seed currently requires manually
  entering the legacy `m/.../0'/...` derivation path; no automatic
  fallback scan exists yet.
- **`BIP44_COIN_TYPE` is not used by the default "new wallet" flow
  (deliberate, not a bug):** `keystore.from_seed()` derives Electrum-native
  (non-BIP39) seeds at the hardcoded, coin-type-independent path `m/0'`
  (single-sig segwit) / `m/1'` (multisig segwit) -- this is upstream
  Electrum's own historical scheme and predates BIP44 entirely;
  `BIP44_COIN_TYPE = 1370` is only actually used by `bip44_derivation()` /
  `purpose48_derivation()`, i.e. the BIP39-seed and custom-derivation paths
  (where it *does* apply, so those are unaffected by this). Practical
  effect: the "create new wallet" flow using a native Electrum seed
  currently produces a wallet at the *same* derivation path Bitcoin-mainnet
  upstream Electrum would use for the same seed words; combined with
  `WIF_PREFIX`/`XPRV`/`XPUB` headers being byte-identical to Bitcoin
  mainnet (see above), the same seed phrase used in both this fork and real
  upstream Electrum derives the *same* private keys.
  A fork-specific fix (anchoring `m/0'`/`m/1'` on `1370` instead) was tried
  and reverted: it touched ~100 test fixtures across the suite for a
  collision that in practice only occurs if a user deliberately reuses the
  exact same seed phrase across this wallet and a real Bitcoin wallet.
  Checked how other long-running Electrum forks with a registered SLIP-44
  coin type handle this: Electrum-LTC and Electrum-GRS both left `m/0'`/
  `m/1'` completely unmodified (Electrum-LTC even kept Bitcoin's xprv/xpub
  version bytes instead of its own Ltub/Ltpv -- see
  `pooler/electrum-ltc#52`, open since 2018). Decision: match that
  precedent and leave this alone.
- **BOLT11 HRP / Lightning (guideline SS3.3, Phase 3):** undecided upstream;
  `BOLT11_HRP` here is a placeholder equal to `SEGWIT_HRP`. No Lightning
  routing/trampoline nodes exist on Elektron Net yet, so this is out of
  scope for this milestone regardless.
- **`TRAMPOLINE_NODES_MAINNET` (`electrum/trampoline.py`) is intentionally
  empty**, for the same reason as `fallback_lnnodes.json`: upstream's
  hardcoded entries (ACINQ, `lightning.electrum.org`, hodlisterco) are all
  real Bitcoin mainnet nodes with a different `chain_hash`. Leaving them in
  caused a confirmed live failure -- opening a channel auto-suggested
  `lightning.electrum.org`, which correctly rejected the connection with
  "no common chain found with remote" (the node is doing its job; it's
  genuinely a different chain). `suggest_peer()` (`lnworker.py`) was made
  to return `None` when the hardcoded list is empty, rather than crash on
  `random.choice([])`. **When a real Elektron Net trampoline/routing node
  exists, add it as a new entry to `TRAMPOLINE_NODES_MAINNET`** (same
  `LNPeerAddr(host=..., port=..., pubkey=...)` shape upstream uses) --
  don't assume there will only ever be one; the dict already supports
  multiple entries (see the real Bitcoin-mainnet dict this replaced, which
  had three).
- **Testnet/regtest/signet chain parameters:** only `BitcoinMainnet` has
  been forked so far; `BitcoinTestnet` and friends still carry real Bitcoin
  testnet parameters. Selecting `--testnet` today produces a client that
  behaves like genuine Bitcoin testnet Electrum, not an Elektron Net
  testnet client.
- **Checkpoints:** `chains/mainnet/checkpoints.json` is empty. Electrum
  works correctly without checkpoints (full header sync instead of
  jump-starting from a trusted point); populating it with real Elektron Net
  checkpoints is a possible future optimization, not a correctness
  requirement.
- **`electrum/currencies.json` is stale (bundled cache, upstream data):**
  `electrum/exchange_rate.py`'s fiat-rate providers were repointed from BTC
  to ELEK trading pairs (none of these real third-party exchanges actually
  list ELEK, so this mostly just means "return nothing" instead of "return
  a real Bitcoin price mislabeled as an ELEK price" -- see the comment at
  the top of that file). `currencies.json` is a pre-generated cache of
  which fiat currencies each provider supports, built from real upstream
  Bitcoin listings; it wasn't regenerated (would require live network
  calls to ~20 exchanges) so it's now out of sync with the new queries --
  the currency dropdown may offer currencies that then return no rate.
  Not dangerous (no wrong price shown), just a minor UI inconsistency
  until it's regenerated or cleared.
