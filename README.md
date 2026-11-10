# LetSolo Homebrew tap

The universal macOS cask catalog for LetSolo products. Application installers and update feeds belong in each product's own public release repository; this tap does not host application releases.

## Install

```bash
brew tap letsolo/tap
```

Once the first signed and notarized LBV macOS release and its cask are published:

```bash
brew install --cask letsolo/tap/lbv
```

No LBV cask is advertised before real installers exist. The private publisher creates `Casks/lbv.rb` only after verifying public downloads in `letsolo/lbv`, with Apple Silicon/Intel-specific checksums and the `鹊桥VPN.app` bundle. Future products add their own casks to this same tap.

## Migration

This repository was renamed from `homebrew-macos`. GitHub preserves its history and redirects; new integrations should use `letsolo/homebrew-tap`. Existing users can switch their tap explicitly when the first real cask is available. The former platform release repositories are not the product update source.

## Publication and privacy

Vapor (`letsolo-vapor[bot]`) authors and commits all cask changes with a token scoped to this repository. Private central CI owns builds, signing, and notarization. Do not add source-repository references, private metadata, personal account information, credentials, build receipts, or local paths here.

Configure a new checkout using external private App metadata:

```bash
python3 -I scripts/bot.py --config <private-app-config> configure
```

A configured checkout uses the bot for `git commit`, `git push`, and `git bot-gh`. Credential errors stop operations without personal-account fallback. `Publisher identity` validates new commit authorship, the push actor, and repository privacy. Local hooks are safeguards rather than server-enforced access restrictions.
