# LetSolo repository rules

- Author, commit, tag, push, and publish code using `letsolo-vapor[bot]` and a GitHub App installation token. Do not use an administrator's personal token or commit identity.
- Keep each token scoped to the repository needed by that operation. Store private App configuration outside the checkout.
- Configure a new checkout with `python3 -I scripts/bot.py --config <private-config> configure`. An already configured checkout can use `git bot-gh` for bot-authenticated GitHub CLI operations.
- Do not commit personal GitHub account details, personal email addresses, machine-specific paths, private keys, signing material, or store credentials. Use generic placeholders in documentation.
- Run `python3 -I scripts/check-repository.py`, appropriate tests, and workflow validation before pushing.
- Product repositories own source and tests. Private central CI owns desktop builds/signing and publication; source repositories dispatch exact commits through the API. Public repositories contain only release data and the universal Homebrew tap. Never publish from pull-request events.
- Document public interfaces in English. Keep examples under `examples/`; they must not run as active publishing workflows in this repository.
- TestFlight and Google Play delivery require product-owned signing and store credentials. Never fabricate a successful store upload or an application release.
