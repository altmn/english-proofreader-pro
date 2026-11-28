# Project guidance

Read [README.md](README.md), [CONTRIBUTING.md](CONTRIBUTING.md), and the [architecture](docs/architecture.md) before changing the project. There is no separate CLAUDE.md.

## Git and scope

- The default branch is `master`, not `main`. Work on a new feature branch (use `codex/` for Codex-created branches) and open a pull request against `master`.
- Never commit or push directly to `master`. Do not reuse a branch after its changes have been committed, pushed, and merged, except for a deployment fix caused by those changes.
- Preserve unrelated local changes. Do not rewrite public history or force-push without explicit maintainer authorization.
- Source-only preparation does not authorize live installation or publication. Production requests include release publication and updates to existing installations as defined below; OpenAI directory submission still requires an explicit request.

## Getting to production

A request to "get to production", or a clearly equivalent request to ship or deploy this project, authorizes the complete workflow below. Do not ask for confirmation again for steps already covered by that request. Honor any explicit narrower scope.

1. Prepare a new version, changelog entry, and release notes on a fresh feature branch, including for README-only or other documentation-only changes. Preserve project behavior unless the requested change explicitly changes it, and synchronize canonical and generated release metadata.
2. Commit, push, open a pull request, complete the required checks, and merge through the project's protected-branch workflow.
3. Build from the clean, reviewed merged revision. Inspect the package contents, publish a new GitHub release with the required installable assets and checksums, and verify the published version and artifact integrity using this project's release procedure.
4. Discover and update the project's existing installed copies through supported host mechanisms, including Codex and any other known installed hosts. For an existing ChatGPT cloud plugin, update that same plugin once and verify availability and selection in Chrome and Safari when those browsers are in use. Preserve installation scope, local modifications, unrelated files, ownership, and sharing; do not create duplicate installations or edit host caches by hand.
5. Verify and report the GitHub release and each installed target separately, using installed versions or file identities and actual skill discovery or selection. A merged PR, local build, or unchanged runtime is not completion of a production request. Discovery alone is not behavioral acceptance.

If a required step is blocked, complete independent work and report the exact blocker. Request only the missing input or manual action needed to proceed, rather than asking for authorization again.

Source-only edits, reviews, and local package preparation do not by themselves trigger this workflow. New installations, changes to sharing, and public plugin-directory submission remain outside it unless requested. Follow [the release instructions](docs/releasing.md) and retain all required validation and evidence checks.

## Product invariants

- Keep `skills/proofreader-pro/SKILL.md` concise. The build's compatibility ceiling is 1 MiB of UTF-8 bytes; there is no project-specific 8,000-character cap.
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

The build uses the standard library and an explicit seven-file runtime allowlist, including the offline counting helper. Behavioral acceptance checks require the intended host; deterministic package tests are not a guarantee of model behavior. See [testing](tests/README.md) and [release instructions](docs/releasing.md).
