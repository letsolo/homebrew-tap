# LetSolo macOS

macOS application releases and the Homebrew tap for LetSolo products.

## Downloads and Homebrew

Signed macOS installers and update files are published in [Releases](https://github.com/letsolo/homebrew-macos/releases). Tags use `<application>-v<version>` so several products can share this repository.

Add the tap:

```bash
brew tap letsolo/macos
```

After a product cask has been added, install it with `brew install --cask letsolo/macos/<application>`. There are no application casks or binaries yet. Casks belong under `Casks/` and must reference the matching release URL and SHA-256 checksum.

## Publication flow

A private product repository builds, signs, and tests its macOS app. Its workflow calls `letsolo/github-workflows/.github/workflows/release.yml@v1` with `platform: macos` and the name of the artifact uploaded in the same workflow run. The shared workflow publishes here using a repository-scoped Vapor token. It generates `SHA256SUMS` and creates a draft release by default.

Homebrew cask updates are separate bot commits after the installer URL and checksum are known. Public delivery of a private product artifact must be intentional; only installers and update files belong here.

## Vapor authentication

All code authorship, committers, pushes, tags, and GitHub releases use `letsolo-vapor[bot]`. A new checkout must be configured before its first commit:

```bash
python3 -I scripts/bot.py --config <private-app-config> configure
```

In a configured checkout, ordinary `git commit` and `git push` use the bot. Bot-authenticated GitHub CLI commands use the local alias:

```bash
git bot-gh release list
```

```bash
python3 -I scripts/bot.py verify
```

The App is installed across the organization, while each local token is restricted to one allowed repository. Private configuration stays outside the checkout. Credential failures stop Git instead of falling back to a personal login. Local hooks are safeguards, not server-enforced access restrictions.

`Publisher identity` verifies bot authorship and the push actor. `scripts/check-repository.py` checks tracked files for credentials and personal machine paths. Actions uses variable `PUBLISHER_APP_CLIENT_ID` and encrypted secret `PUBLISHER_APP_PRIVATE_KEY`; no private values belong in this repository.
