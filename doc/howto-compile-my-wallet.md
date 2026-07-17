# Compiling Elektron Electrum Yourself -- Step-by-Step Guide

This guide is for people **without** a developer background who want to
build their own copy of Elektron Electrum from source, instead of trusting
a pre-built file. This is optional -- if you just want the ready-to-use
download, grab it from
[Releases](https://github.com/kutlusoy/elektron-net-electrum/releases) and
you can skip this guide entirely.

**Why build it yourself at all?** So you don't have to "blindly" trust a
downloadable `.exe`/`.apk`/`.dmg` -- you can verify for yourself that it's
built from exactly the source code in this repository.

This file summarizes the more detailed, developer-oriented original
documentation (in `contrib/*/README*.md`, inherited from Electrum) into
simple steps. If you run into trouble, it's worth checking those out -- the
links are at the end of each section.

**Important:** There's a separate section below for each operating system
-- you only need the section for the system you want to build *for* (not
necessarily the one you're sitting at right now -- see Windows/Linux/
Android below: those all run through Docker on a Linux machine).

---

## 0. Common first step: get the source code

Same for **all** platforms first: install Git (on Linux e.g.
`sudo apt-get install git`, on macOS via `brew install git` or the Xcode
tools) and fetch the source code:

```
git clone https://github.com/kutlusoy/elektron-net-electrum.git
cd elektron-net-electrum
git checkout elektron-net-integration
```

(`elektron-net-integration` is the current working branch, before it's
merged into `main` -- if you're reading this later and `main` is already
up to date, you can skip the `git checkout` step.)

---

## 1. Building Windows (.exe)

**Not** done on Windows itself -- the build runs through Docker on a Linux
machine (or Windows with WSL2 + Ubuntu), which "cross-compiles" the Windows
version (using Wine). That sounds unusual, but it's the official and
reproducible way to do it.

1. **Install Docker** (Ubuntu/Debian):
   ```
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
   sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
   sudo apt-get update
   sudo apt-get install -y docker-ce
   sudo usermod -aG docker ${USER}
   ```
   Afterward, log out and back in (or reboot) once, so the group membership
   takes effect. On other Linux distributions: install Docker through your
   own package manager, the rest is identical.

2. **Build:**
   ```
   cd elektron-net-electrum/contrib/build-wine
   ./build.sh
   ```
   This takes the longest the first time (the Docker image gets built;
   after that it's reused).

3. **Result:** ends up in `contrib/build-wine/dist/` as
   `elektron-electrum-<version>-setup.exe` (installer) and as a portable
   `.exe`.

Details/troubleshooting: [`contrib/build-wine/README.md`](../contrib/build-wine/README.md),
[`contrib/docker_notes.md`](../contrib/docker_notes.md).

---

## 2. Linux -- AppImage (runs on most Linux distros with no installation)

Same principle as Windows, also via Docker:

1. Install Docker (see step 1 above, if you haven't already).

2. Build:
   ```
   cd elektron-net-electrum/contrib/build-linux/appimage
   ./build.sh
   ```

3. **Result:** ends up in `./dist/` as `elektron-electrum-*-x86_64.AppImage`.
   Make it executable and run it:
   ```
   chmod +x dist/elektron-electrum-*-x86_64.AppImage
   ./dist/elektron-electrum-*-x86_64.AppImage
   ```

Details: [`contrib/build-linux/appimage/README.md`](../contrib/build-linux/appimage/README.md).

---

## 3. Linux -- run directly from source (simplest, no Docker)

If you just want to use Elektron Electrum on your own Linux machine (and
don't need a packaged installer), this is the fastest route -- no Docker
needed:

1. **Install dependencies:**
   ```
   sudo apt-get install python3-pip python3-pyqt6 libsecp256k1-dev
   ```

2. **Install and run:**
   ```
   cd elektron-net-electrum
   python3 -m pip install --user -e ".[gui,crypto]"
   ./run_electrum
   ```

Details: main [`README.md`](../README.md), "Development version (git
clone)" section.

### 3b. Linux -- build a source tarball (for distribution/packaging)

If you instead want to produce a `.tar.gz` package (e.g. to hand it to
someone else, rather than run it yourself directly):

```
cd elektron-net-electrum/contrib/build-linux/sdist
./build.sh
```

Result in `./dist/`. Details:
[`contrib/build-linux/sdist/README.md`](../contrib/build-linux/sdist/README.md).

---

## 4. Building macOS (.dmg / .app)

This only works **on an actual Mac** (no Docker/cross-build possible).

1. **Install [Homebrew](https://brew.sh/)** (if not already installed) --
   instructions on the linked page, a single terminal command.

2. **Xcode command line tools** get installed automatically by Homebrew
   when needed.

3. **Build:**
   ```
   cd elektron-net-electrum
   ./contrib/osx/make_osx.sh
   ```

4. **Result:** a folder `Elektron Electrum.app` plus a `.dmg` file, both
   unsigned (macOS will show a warning on first launch that the app is from
   an "unidentified developer" -- normal for self-built, unsigned apps;
   confirm via right-click -> "Open").

Details (including codesigning/notarization for advanced users):
[`contrib/osx/README.md`](../contrib/osx/README.md),
[`contrib/osx/README_macos.md`](../contrib/osx/README_macos.md) (alternative:
run directly from source instead of building a `.app`, similar to section 3
above).

---

## 5. Building Android (.apk)

Also Docker on a Linux machine here, no Android Studio needed.

1. Install Docker (see step 1 above).

2. **Build** (debug version, for testing yourself -- the simplest option):
   ```
   cd elektron-net-electrum/contrib/android
   ./build.sh qml arm64-v8a debug
   ```
   `arm64-v8a` fits the vast majority of Android phones from the last few
   years. If your phone is older/different: use `armeabi-v7a` or `x86_64`
   instead of `arm64-v8a`.

3. **Result:** ends up in `./dist/` as
   `ElektronElectrum-*-arm64-v8a-debug.apk`.

4. **Installing on your phone:** either copy the `.apk` file to your phone
   manually and open it there (Settings -> "Allow installation from unknown
   sources" needs to be enabled once for this), or install it over a USB
   cable with [`adb`](https://developer.android.com/tools/adb):
   ```
   adb install -r dist/ElektronElectrum-*-arm64-v8a-debug.apk
   ```

**Note:** Debug builds are signed with a provisional key. If you want to
distribute an app through the Play Store or similar, you need your own,
securely stored signing key (`release` mode) -- see the detailed docs for
that advanced route.

Details: [`contrib/android/Readme.md`](../contrib/android/Readme.md).

---

## Common problems

- **"docker: permission denied"**: You haven't logged out/back in (or
  rebooted) since `usermod -aG docker` yet. Alternatively, prefix every
  command with `sudo`.
- **Build fails with network errors the first time**: The build scripts
  download a fair amount on the first run (Docker images, dependencies) --
  if your connection is unstable, just re-run the script; anything already
  downloaded gets cached.
- **Windows/macOS show a security warning on first launch**: normal for
  self-built, unsigned/unnotarized programs -- doesn't apply to the
  official downloads under
  [Releases](https://github.com/kutlusoy/elektron-net-electrum/releases)
  (those are signed).
- **I want to check whether my self-built binary matches the official
  release ("reproducible build")**: possible, but advanced -- see the
  detailed docs for each platform ("Verifying reproducibility" section).

General background on Elektron Net and what this fork changes compared to
original Electrum: [`doc/elektron.md`](elektron.md).
