# Secure Packaging Guide

This guide captures the steps for producing a hardened binary of the Nocturnal Archive CLI before shipping it to private beta testers.

## 1. Overview
- **Goal:** reduce easy reverse engineering of the Python source and avoid exposing API keys embedded in the build.
- **Approach:** compile the CLI with [Nuitka](https://nuitka.net/) into a single-file executable, optionally layering bytecode/constant obfuscation (commercial feature) and platform-specific signing.
- **Output:** platform-specific binaries stored under `dist/secure/` with versioned filenames.

## 2. Install toolchain
```bash
python -m pip install --upgrade nuitka zstandard ordered-set
```

Platform-specific prerequisites:
- **macOS:** Xcode Command Line Tools (`xcode-select --install`) and an Apple Developer cert for codesign.
- **Windows:** MSVC Build Tools or Visual Studio 2022, plus `signtool.exe` for Authenticode signatures.
- **Linux:** GCC/Clang, `patchelf`, `libfuse` for AppImage wrapping if desired.

## 3. Build the hardened binary
```bash
./tools/packaging/build_secure_cli.sh
```

Environment flags:
- `PYTHON_BIN=/path/to/python` to use a specific interpreter.
- `NUITKA_ENCRYPTION_KEY=secret` to enable Nuitka commercial obfuscation features (requires a licensed build).
- Pass `--clean` to wipe previous secure build artifacts.

The script emits a single binary such as `dist/secure/nocturnal-0.9.0b1-macos`.

## 4. Sign & notarize
- **macOS:**
  ```bash
  codesign --deep --force --options runtime --entitlements deploy/macos/entitlements.plist \
    --sign "Developer ID Application: Nocturnal Archive" dist/secure/nocturnal-0.9.0b1-macos
  xcrun notarytool submit dist/secure/nocturnal-0.9.0b1-macos --keychain-profile nocturnal-notary --wait
  ```
- **Windows:**
  ```powershell
  signtool sign /tr http://timestamp.digicert.com /td sha256 /fd sha256 \
    /a dist\secure\nocturnal-0.9.0b1-windows.exe
  ```
- **Linux:** include the binary inside a `.deb`, `.rpm`, or AppImage and sign the package using GPG (`dpkg-sig`, `rpm --addsign`, or `gpg --detach-sign`).

## 5. Generate checksums
```bash
(cd dist/secure && sha256sum nocturnal-0.9.0b1-* > nocturnal-0.9.0b1.sha256)
```
Publish the checksum alongside download links.

When sharing the shell/PowerShell bootstrap scripts, distribute the matching SHA-256 string and instruct testers to export it via the `NOCTURNAL_PACKAGE_SHA256` environment variable. The installer now verifies the downloaded artifact before installation and aborts if the hash deviates.

## 6. Test the artifact
```bash
./dist/secure/nocturnal-0.9.0b1-macos --version
./dist/secure/nocturnal-0.9.0b1-macos --tips
```
Run a short interactive session to confirm the CLI behaves the same as the pure Python build.

## 7. Distribution checklist
- [ ] Hardened binaries built for macOS, Windows, and Linux
- [ ] Platform-specific signatures applied (codesign, Authenticode, GPG)
- [ ] SHA-256 checksums generated and stored next to artifacts
- [ ] Smoke tests documented with pass/fail results
- [ ] Links added to distribution email and docs (see `docs/USER_GETTING_STARTED.md`)

Following this guide fulfills the “Optionally obfuscate/distribute core agent via PyArmor/Nuitka bundles” and “Generate checksums for installers” bullet points in the beta launch checklist. Supplement with PyArmor or additional packers if deeper obfuscation is required.
