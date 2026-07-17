# Elektron Electrum selbst kompilieren -- Schritt-für-Schritt-Anleitung

Diese Anleitung richtet sich an Leute **ohne** Entwickler-Hintergrund, die
sich ihre eigene Kopie von Elektron Electrum aus dem Quellcode bauen wollen,
statt einer fertigen Datei zu vertrauen. Das ist optional -- wer den
fertigen Download benutzen möchte, findet ihn unter
[Releases](https://github.com/kutlusoy/elektron-net-electrum/releases) und
kann diese Anleitung ignorieren.

**Warum überhaupt selbst bauen?** Damit du nicht "blind" einer
herunterladbaren `.exe`/`.apk`/`.dmg` vertrauen musst, sondern selbst
prüfen kannst, dass daraus wirklich genau das entsteht, was im Quellcode
dieses Repos steht.

Diese Datei fasst die ausführlichere, entwicklerorientierte Original-
Dokumentation (in `contrib/*/README*.md`, von Electrum übernommen) in
einfachen Schritten zusammen. Bei Problemen lohnt sich ein Blick dort hinein
-- die Links stehen jeweils am Ende des Abschnitts.

**Wichtig:** Es gibt für jedes Betriebssystem eine eigene Anleitung weiter
unten -- du brauchst nur den Abschnitt für das System, für das du bauen
willst (nicht zwingend das, auf dem du gerade sitzt, siehe Windows/Linux/
Android unten: die laufen alle über Docker auf einem Linux-Rechner).

---

## 0. Gemeinsamer erster Schritt: Quellcode herunterladen

Für **alle** Plattformen zuerst dasselbe: Git installieren (unter Linux z.B.
`sudo apt-get install git`, unter macOS via `brew install git` oder Xcode-
Tools) und den Quellcode holen:

```
git clone https://github.com/kutlusoy/elektron-net-electrum.git
cd elektron-net-electrum
git checkout elektron-net-integration
```

(`elektron-net-integration` ist der aktuelle Arbeits-Branch, bevor er in
`main` gemerged wird -- falls du diese Anleitung später liest und `main`
schon aktuell ist, kannst du den `git checkout`-Schritt weglassen.)

---

## 1. Windows (.exe) bauen

**Nicht** unter Windows selbst -- der Build läuft über Docker auf einem
Linux-Rechner (oder Windows mit WSL2 + Ubuntu), der die Windows-Version
"cross-kompiliert" (mit Wine). Das klingt ungewohnt, ist aber der offizielle
und reproduzierbare Weg.

1. **Docker installieren** (Ubuntu/Debian):
   ```
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
   sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
   sudo apt-get update
   sudo apt-get install -y docker-ce
   sudo usermod -aG docker ${USER}
   ```
   Danach einmal ab- und wieder anmelden (oder neu starten), damit die
   Gruppenmitgliedschaft wirkt. Andere Linux-Distributionen: Docker über den
   eigenen Paketmanager installieren, der Rest ist identisch.

2. **Bauen:**
   ```
   cd elektron-net-electrum/contrib/build-wine
   ./build.sh
   ```
   Das dauert beim ersten Mal am längsten (Docker-Image wird gebaut,
   danach wird es wiederverwendet).

3. **Ergebnis:** liegt in `contrib/build-wine/dist/` als
   `elektron-electrum-<version>-setup.exe` (Installer) und als portable
   `.exe`.

Details/Fehlersuche: [`contrib/build-wine/README.md`](../contrib/build-wine/README.md),
[`contrib/docker_notes.md`](../contrib/docker_notes.md).

---

## 2. Linux -- AppImage (läuft auf den meisten Linux-Distros ohne Installation)

Gleiches Prinzip wie Windows, auch über Docker:

1. Docker installieren (siehe Schritt 1 oben, falls noch nicht geschehen).

2. Bauen:
   ```
   cd elektron-net-electrum/contrib/build-linux/appimage
   ./build.sh
   ```

3. **Ergebnis:** liegt in `./dist/` als `elektron-electrum-*-x86_64.AppImage`.
   Ausführbar machen und starten:
   ```
   chmod +x dist/elektron-electrum-*-x86_64.AppImage
   ./dist/elektron-electrum-*-x86_64.AppImage
   ```

Details: [`contrib/build-linux/appimage/README.md`](../contrib/build-linux/appimage/README.md).

---

## 3. Linux -- direkt aus dem Quellcode starten (am einfachsten, kein Docker)

Wenn du Elektron Electrum nur auf deinem eigenen Linux-Rechner benutzen
willst (kein fertiges Installationspaket brauchst), ist das der schnellste
Weg -- kein Docker nötig:

1. **Abhängigkeiten installieren:**
   ```
   sudo apt-get install python3-pip python3-pyqt6 libsecp256k1-dev
   ```

2. **Installieren und starten:**
   ```
   cd elektron-net-electrum
   python3 -m pip install --user -e ".[gui,crypto]"
   ./run_electrum
   ```

Details: Haupt-[`README.md`](../README.md), Abschnitt "Development version
(git clone)".

### 3b. Linux -- Quellcode-Tarball bauen (für Weitergabe/Pakete)

Falls du stattdessen ein `.tar.gz`-Paket erzeugen willst (z.B. um es
weiterzugeben, nicht um es selbst direkt zu benutzen):

```
cd elektron-net-electrum/contrib/build-linux/sdist
./build.sh
```

Ergebnis in `./dist/`. Details:
[`contrib/build-linux/sdist/README.md`](../contrib/build-linux/sdist/README.md).

---

## 4. macOS (.dmg / .app) bauen

Das geht **nur auf einem echten Mac** (kein Docker/Cross-Build möglich).

1. **[Homebrew](https://brew.sh/) installieren** (falls noch nicht
   vorhanden) -- Anleitung auf der verlinkten Seite, ein Terminal-Befehl.

2. **Xcode-Kommandozeilentools** werden von Homebrew bei Bedarf automatisch
   mitinstalliert.

3. **Bauen:**
   ```
   cd elektron-net-electrum
   ./contrib/osx/make_osx.sh
   ```

4. **Ergebnis:** ein Ordner `Elektron Electrum.app` sowie eine `.dmg`-Datei,
   beide unsigniert (macOS zeigt beim ersten Start eine Warnung, dass die
   App von einem "nicht verifizierten Entwickler" stammt -- normal bei
   selbst gebauten, unsignierten Apps; über Rechtsklick -> "Öffnen"
   bestätigen).

Details (inkl. Codesigning/Notarisierung für Fortgeschrittene):
[`contrib/osx/README.md`](../contrib/osx/README.md),
[`contrib/osx/README_macos.md`](../contrib/osx/README_macos.md) (Variante:
direkt aus dem Quellcode starten statt eine `.app` zu bauen, analog zu
Abschnitt 3 oben).

---

## 5. Android (.apk) bauen

Auch hier: Docker auf einem Linux-Rechner, kein Android Studio nötig.

1. Docker installieren (siehe Schritt 1 oben).

2. **Bauen** (Debug-Version, zum Selbst-Testen -- am einfachsten):
   ```
   cd elektron-net-electrum/contrib/android
   ./build.sh qml arm64-v8a debug
   ```
   `arm64-v8a` passt für die allermeisten Android-Handys der letzten Jahre.
   Falls dein Handy älter/anders ist: `armeabi-v7a` oder `x86_64` statt
   `arm64-v8a` verwenden.

3. **Ergebnis:** liegt in `./dist/` als
   `ElektronElectrum-*-arm64-v8a-debug.apk`.

4. **Auf dem Handy installieren:** entweder die `.apk`-Datei manuell aufs
   Handy kopieren und dort öffnen (Einstellungen -> "Installation aus
   unbekannten Quellen erlauben" wird dafür einmalig verlangt), oder per
   USB-Kabel mit [`adb`](https://developer.android.com/tools/adb) installiert:
   ```
   adb install -r dist/ElektronElectrum-*-arm64-v8a-debug.apk
   ```

**Hinweis:** Debug-Builds sind mit einem provisorischen Schlüssel signiert.
Wer eine App aus dem Play Store o.ä. verteilen will, braucht einen eigenen,
sicher aufbewahrten Signierschlüssel (`release`-Modus) -- siehe die
Detail-Doku für den fortgeschrittenen Weg.

Details: [`contrib/android/Readme.md`](../contrib/android/Readme.md).

---

## Häufige Probleme

- **"docker: permission denied"**: Du hast dich nach `usermod -aG docker`
  noch nicht neu angemeldet/neu gestartet. Alternativ jeden Befehl mit
  `sudo` voranstellen.
- **Build bricht beim ersten Mal mit Netzwerkfehlern ab**: Die
  Build-Skripte laden beim ersten Lauf einiges herunter (Docker-Images,
  Abhängigkeiten) -- bei instabiler Verbindung einfach das Skript erneut
  ausführen, bereits heruntergeladene Sachen werden zwischengespeichert.
- **Windows/macOS zeigen eine Sicherheitswarnung beim ersten Start**: normal
  bei selbst gebauten, unsignierten/unnotarisierten Programmen -- betrifft
  nur die offiziellen Downloads unter
  [Releases](https://github.com/kutlusoy/elektron-net-electrum/releases)
  nicht (die sind signiert).
- **Ich will prüfen, ob mein selbst gebauter Build zum offiziellen Release
  passt ("reproducible build")**: möglich, aber fortgeschritten -- siehe
  die Detail-Dokus der jeweiligen Plattform (Abschnitt "Verifying
  reproducibility").

Allgemeiner Hintergrund zu Elektron Net und was in diesem Fork gegenüber
dem originalen Electrum verändert wurde: [`doc/elektron.md`](elektron.md).
