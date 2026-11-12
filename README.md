# WildbberriesClient — GitHub Installer

This repository builds a single Windows installer, `WildbberriesInstaller.exe`. The user downloads and runs that one EXE; it downloads the latest client bundle from the public GitHub Releases page, installs the launcher and game payload, creates a desktop shortcut, and starts the launcher.

## Quick setup

Read **GITHUB-SETUP-RU.md** (Russian instructions). Before publishing, replace `YOUR_GITHUB_USERNAME/WildbberriesClient` in `bootstrapper/Program.cs` with the actual public GitHub repository owner/name.

## Release build

Push a tag such as `v1.0.0`. GitHub Actions builds:

- `WildbberriesInstaller.exe` — self-contained Windows x64 installer (the only file end users need to download).
- `WildbberriesClient-Bundle.zip` — release asset fetched automatically by the installer.

The installer places files under `%LOCALAPPDATA%\WildbberriesClient`, preserves an existing `run` folder, creates a desktop shortcut, and starts `WildbberriesClient.exe`.

## Local launcher build

On Windows with Python 3.10+, run `Build.bat`. This produces `dist\WildbberriesClient.exe`.

## Notes

- The GitHub repository must be public for the unauthenticated installer download flow.
- Minecraft may still require the Java runtime version expected by the bundled client.
- Verify that you have permission to redistribute all content in `ClientPayload.zip`.
- K5Launcher attribution and MIT notice are retained in `K5-LICENSE.txt`.
