# Releasing Elektron Electrum

How tagging and the automated release build work in this repository.

## TL;DR: cutting a release

1. Bump `ELECTRUM_VERSION` in [`electrum/version.py`](../electrum/version.py),
   commit it.
2. Tag that commit with a `v`-prefixed version, matching the version you
   just set, and push the tag. Use an **annotated** tag (`-a` with a `-m`
   message), not a lightweight one -- a release pointer is exactly the
   case annotated tags are for: it becomes its own Git object with a
   tagger, date, and message, instead of just a bare ref:
   ```
   git tag -a v4.0.4 -m "Release v4.0.4"
   git push origin v4.0.4
   
   Entfenen
   git tag -d v4.0.4 && git push origin :v4.0.4 
  
   ```
   (The build scripts call `git describe --tags`, which resolves either
   kind of tag fine -- the `-a` is about having a real, documented
   release object, not a build requirement.)
3. That's it -- pushing a tag matching `v*` automatically triggers the
   [`builds`](workflows/builds.yml) workflow, which builds every platform
   and publishes a GitHub Release with all of them attached.

## What gets built automatically

A `v*` tag push builds and attaches to one GitHub Release:

| Artifact | Platform | Notes |
|---|---|---|
| `elektron-electrum-<version>-setup.exe` + portable `.exe` | Windows | cross-built via Wine/Docker |
| `ElektronElectrum-<version>-arm64-v8a-debug.apk` | Android | only `arm64-v8a` is built automatically; other architectures need a manual `workflow_dispatch` run |
| `elektron-electrum-<version>-x86_64.AppImage` | Linux | |
| `Elektron-Electrum-<version>.tar.gz` + `Elektron-Electrum-sourceonly-<version>.tar.gz` | source | full tarball and a source-only variant for distro packagers |

**macOS is not built by this workflow.** Electrum's macOS build can only be
done on an actual Mac (no cross-compilation), so a `.dmg` has to be built
and uploaded manually if one is wanted for a given release -- see
[`contrib/osx/README.md`](../contrib/osx/README.md) or the beginner-friendly
[`doc/howto-compile-my-wallet.md`](../doc/howto-compile-my-wallet.md).

## How the release is put together

- Trigger: `on: push: tags: ['v*']` in
  [`.github/workflows/builds.yml`](workflows/builds.yml). The same workflow
  also runs nightly (`schedule`) and on manual `workflow_dispatch` for
  testing individual platforms, but the `release` job at the end only runs
  when the ref is an actual `v*` tag.
- The `release` job waits for the Windows/Android/AppImage/tarball jobs to
  finish, downloads all of their artifacts, and publishes them together as
  one GitHub Release via `softprops/action-gh-release`.
- **Prerelease detection:** if the tag name contains `-rc` (e.g.
  `v4.0.5-rc1`), the release is marked as a GitHub prerelease automatically.
  A plain `v4.0.5` is published as a normal release.
- The release title is `"Elektron Electrum <tag>"`.

## Versioning note

`ELECTRUM_VERSION` in `electrum/version.py` is this fork's own version
number -- it does **not** track upstream Electrum's version. The initial
release was set to `4.0.4` to match `elektron-net`'s own version at fork
time (marking a known-compatible starting point), but the two are expected
to diverge afterward -- there's no requirement to keep bumping them
together. See [`doc/elektron.md`](../doc/elektron.md) for the full picture
of what differs from upstream Electrum.

## Manual/partial builds

To test a single platform without cutting a release, run the `builds`
workflow manually (Actions tab -> "builds" -> "Run workflow") and pick a
`target` (`windows`, `android`, `appimage`, or `tarball`) instead of `all`.
This does not create a GitHub Release -- it only uploads the build as a
workflow artifact for download/inspection.
