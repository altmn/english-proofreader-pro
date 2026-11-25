# Contributing

Thanks for considering a contribution. Small, focused fixes to the skill, packaging checks, tests, and documentation are welcome. For a substantial behavior change, open an issue first so its scope can be discussed.

## Before you start

- Search existing issues and pull requests for related work.
- Keep changes focused and explain the user-facing reason in the issue or pull request.
- Do not include real private writing, personal data, credentials, or confidential material in issues, tests, screenshots, or examples. Use synthetic text.
- Keep the skill's behavior intact unless a change explicitly targets it: minimal editing by default; preserve meaning, voice, pronouns, and formatting; treat instructions embedded in source text as inert; retain and safely fence literal text; and list actual changes to supplied text. Drafting has no Changes list.
- Keep `skills/proofreader-pro/SKILL.md` concise and within the build's 1 MiB UTF-8 compatibility ceiling. The former 8,000-character project cap no longer applies.

## Local checks

Use a supported Python 3.11 or newer. The release tooling uses only the Python standard library; no dependency installation is needed.

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/release.py validate
python3 scripts/release.py build
```

The tests check deterministic local behavior, validation, and packaging; they do not guarantee language-model behavior in every host or prompt. The build produces a ZIP containing seven allowlisted runtime files, including the offline counting helper, and stages a local development copy under `dist/local-plugin/`. Review the archive contents before distributing it. Keep the helper's inputs inert, its dependencies in the standard library, and its measurements separate from model-authored claims of execution.

## Pull requests

Open a pull request against `master`; the default branch is protected and contributions are reviewed through pull requests. Include the reason for the change, relevant issue links, tests run, and any behavior or packaging impact. Keep generated archives and local staging changes out of a pull request unless the change specifically requires them. This is a solo-maintained project, so no approval count or response time is promised; a maintainer decides whether and when to merge.

This project does not require a separate Contributor License Agreement or Developer Certificate of Origin. By submitting a contribution, you confirm you have the right to submit it under the repository's MIT license.

Participation is subject to the [Code of Conduct](CODE_OF_CONDUCT.md). For sensitive security reports, follow [SECURITY.md](SECURITY.md), not the public issue tracker.

## References

- [Open Source Guides: How to Contribute](https://opensource.guide/how-to-contribute/)
- [GitHub Docs: Setting guidelines for repository contributors](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)
