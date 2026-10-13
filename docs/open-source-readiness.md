# Open-source preparation

The project uses a permissive MIT license, a public GitHub repository, and the `master` default branch. Open-source availability is separate from approval or publication in OpenAI's plugin directory.

## Practices selected for this project

- Keep the approved MIT license and document the source of the instructions and icon in [NOTICE.md](../NOTICE.md).
- Give newcomers a working clone/build/install path in the [README](../README.md), with separate [contributor](../CONTRIBUTING.md), [architecture](architecture.md), and [release](releasing.md) guides.
- Provide an explicit [code of conduct](../CODE_OF_CONDUCT.md), [support path](../SUPPORT.md), [security policy](../SECURITY.md), and issue/PR templates. Do not promise a support or disclosure deadline the maintainer has not agreed to.
- Run offline standard-library tests and package validation in CI on supported Python 3.11 and the latest stable version. Pin Actions to verified full commit hashes, enforce that requirement in GitHub's settings, keep workflow permissions read-only, and use Dependabot for action-update proposals.
- Enable CodeQL default setup for Python and GitHub Actions with the extended query suite and weekly scans while the repository is active. Review the analysis results for the exact commit being released. Default setup does not analyze pull requests from forks; a required CodeQL merge rule needs an analysis path for those contributions before it is enabled.
- Keep Dependabot alerts and automatic security updates enabled, alongside the monthly Action-update proposals. Apply a seven-day cooldown to routine Action updates; security-update PRs remain exempt.
- Preserve the existing signed-commit, linear-history, deletion, and force-push restrictions. Add pull-request and passing `Validate and test` requirements for `master`; allow a solo maintainer to merge without a second person's approval.
- Publish only the allowlisted runtime ZIP, not a checkout containing tests, raw evidence, development configuration, or Git data. A source version and CI artifact are not an approved store listing or a published release.
- Protect `v*` release tags against updates and deletion with an active tag ruleset and no bypass actors. Allow new tags to be created at reviewed commits. Enable immutable releases; prepare a draft, attach all reviewed assets, and then publish. Verify the release attestation and downloaded ZIP as described in [releasing](releasing.md).
- Use GitHub private vulnerability reporting for security reports. Keep source code secret scanning and push protection enabled. Do not use that security channel for ordinary support or conduct concerns.
- Use a repository-local GitHub noreply commit email for new work. Keep private host conversations and screenshots out of the current public tree, and use synthetic test material.

## Historical privacy limits

The initial commit was already public before this preparation. It contained account-scoped private test links, account screenshots, and a direct commit email. They were not identified as authentication credentials. Current-tree cleanup does not erase older commits, cached copies, or forks. No public history rewrite was performed. Any history cleanup requires an explicit maintainer decision and coordination; real leaked credentials would also require revocation, not only deletion.

## Research

The following primary sources informed the choices above:

- [Open Source Guides: Starting a project](https://opensource.guide/starting-a-project/): license, README, contribution guide, community expectations, and launch hygiene.
- [Choose a License: MIT](https://choosealicense.com/licenses/mit/): permissive reuse with license/copyright retention and warranty disclaimer.
- [GitHub: Secure use of Actions](https://docs.github.com/en/actions/reference/security/secure-use): immutable action pins and least-privilege workflow permissions.
- [Python 3.10 final release notice](https://www.python.org/downloads/release/python-31022/): Python 3.10 reached end of life on October 1, 2026, so it is not the supported minimum.
- [GitHub: Available ruleset rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets): pull-request, signature, linear-history, and status-check protections.
- [GitHub: Code scanning setup types](https://docs.github.com/en/code-security/concepts/code-scanning/setup-types): default setup, supported events, and fork pull-request limits.
- [GitHub: Immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases): release-tag and asset integrity, and automatic release attestations.
- [GitHub: Private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/report-privately): confidential security reports for participating public repositories.
- [GitHub: Removing sensitive repository data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository): limits and coordination costs of rewriting public history.
- [OpenAI: Package your plugin](https://developers.openai.com/plugins/build/plugins): portable source/license/homepage metadata and OpenAI-specific listing URLs.

Repository settings are external state, not enforced by this document. Maintainers should verify GitHub's live settings when changing the release process.
