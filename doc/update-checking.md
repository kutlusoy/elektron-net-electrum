# Update checking

How "Check for updates" works in Elektron Electrum, and what's needed to make
it fully functional.

## How it works (code)

`electrum/gui/qt/update_checker.py`, class `UpdateCheck`:

1. On "Help -> Check for updates", the client does an HTTP GET against
   `UpdateCheck.url` (`https://elektron-net.org/version`) and expects a JSON
   body shaped like:
   ```json
   {
     "version": "4.0.5",
     "signatures": {
       "<some-address>": "<base64-encoded signature of the version string>"
     }
   }
   ```
2. For each `(address, signature)` pair in `signatures`, it checks whether
   `address` is one of the addresses in `UpdateCheck.VERSION_ANNOUNCEMENT_SIGNING_KEYS`,
   and if so, verifies the signature against the `version` string using
   `verify_usermessage_with_address()` (standard message-signing, the same
   mechanism used to sign arbitrary text with a wallet address).
3. If none of the signatures verify against a known key, the check fails
   with "Update check failed" -- it does **not** silently trust an
   unsigned or wrongly-signed response.
4. On success, the returned version is compared against
   `electrum.version.ELECTRUM_VERSION` (`StrictVersion` comparison) to
   decide whether to show "There is a new update available" or "Already
   up to date". The download link shown is `UpdateCheck.download_url`.

## Current state

- `url` points at `https://elektron-net.org/version` and `download_url`
  at this repo's GitHub Releases page (`.../releases`).
- `VERSION_ANNOUNCEMENT_SIGNING_KEYS` is currently an **empty tuple**.
  This is deliberate, not an oversight: upstream Electrum's keys were
  removed (this fork has nothing to do with them), and no Elektron Net
  signing key has been set up yet. With an empty key list, step 3 above
  always fails safely -- every check ends in "Update check failed"
  rather than trusting an unsigned reply or a spoofable HTTP response.
- Net effect right now: the "Check for updates" menu item is present and
  will not crash, but will always report "Update check failed" until the
  two things below are set up.

## What's needed to make it fully functional

1. **Serve `https://elektron-net.org/version`** returning the JSON shape
   above for the current release.
2. **Pick a signing key** (any address whose private key you control --
   does not need to be a funded/real wallet address) and sign the version
   string with it, e.g. via Electrum's own "Sign/verify message" tool in
   the wallet's address-details dialog, or `electrum signmessage <addr>
   <message>` on the CLI. Put the resulting `address: signature` pair into
   the `signatures` object in the JSON response.
3. **Add that address** to `UpdateCheck.VERSION_ANNOUNCEMENT_SIGNING_KEYS`
   in `electrum/gui/qt/update_checker.py` and release a build with that
   change -- from that point on, older installs *and* new ones will
   recognize announcements signed with that key. (Rotating/adding keys
   later works the same way each already-released version keeps trusting
   whatever key list it shipped with.)

There's no requirement that the version-announcement JSON is served by the
same box as anything else -- it can be a static file behind
`elektron-net.org/version`, updated by hand or by the release CI each time
a tag is cut.

## QML / mobile GUI

There is currently no update-check implementation in the QML GUI
(`electrum/gui/qml/`) at all -- it's Qt-desktop-only, same as upstream
Electrum. Not addressed here.
