# Project guidance

Read [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md), and the [architecture](docs/architecture.md) before changing the project. There is no separate CLAUDE.md.

## Git and scope

- The default branch is `master`, not `main`. Work on a new feature branch (use `codex/` for Codex-created branches) and open a pull request against `master`.
- Never commit or push directly to `master`. Do not reuse a branch after its changes have been committed, pushed, and merged, except for a deployment fix caused by those changes.
- Preserve unrelated local changes. Do not rewrite public history or force-push without explicit maintainer authorization.
- Source preparation does not authorize installing, updating the live plugin, or publishing an OpenAI directory listing.

## Product invariants

- Keep `skills/proofread/SKILL.md` under 8,000 Unicode characters, including frontmatter, spaces, and newlines.
- Preserve minimal editing/no-op behavior, literal formatting, the existing pronoun rule, source-instruction isolation, copyable fenced output, and complete truthful Changes lists for edited supplied text. Fresh drafts do not get fictional correction lists.
- Do not change these instructions incidentally during repository, packaging, or documentation work.
- Root `plugin.json` is canonical. The legacy manifest in `dist/local-plugin/` is generated; never edit the host's cache or generated staging files by hand.
- Never add credentials, private chat links, real user writing, or account screenshots. Use synthetic fixtures. Ignoring a file does not remove it from existing Git history.

## Verify

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/release.py validate
python3 scripts/release.py build
git diff --check
```

The build uses the standard library and an explicit six-file runtime allowlist. Behavioral acceptance checks require the intended host; deterministic package tests are not a guarantee of model behavior. See [testing](tests/README.md) and [release instructions](docs/releasing.md).
