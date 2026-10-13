# How to publish a release

Only a maintainer should publish a release. A checked-in version or locally built ZIP is not evidence that a public release or plugin submission has occurred.

## Prepare the release pull request

1. In the feature pull request that proposes a release, update `plugin.json`'s version and release notes, and add the proposed version's entry to `CHANGELOG.md`. Make these changes before merging to `master`; do not make a release-preparation commit directly on `master` after the merge.
2. Run the test and package checks from the repository root:

   ```sh
   python3 -m unittest discover -s tests -p 'test_*.py'
   python3 scripts/release.py validate
   python3 scripts/release.py build
   ```

3. Inspect the generated `dist/english-proofreader-pro-<version>.zip`: verify it contains exactly the six runtime files, opens successfully, and excludes development materials and private data. Calculate and record the SHA-256 with `shasum -a 256 dist/english-proofreader-pro-<version>.zip` on macOS or `sha256sum dist/english-proofreader-pro-<version>.zip` on Linux.
4. Review the release notes, package contents, privacy notice, and source-bound synthetic behavior/host records using the [evaluation procedure](../tests/README.md). For a skill change, refresh three complete independent simulation runs with exact input hashes and per-assertion verdicts. Require all assertions to pass for the profile being accepted; a passing stronger-model run does not clear a failing Luna profile. Run intended-host acceptance against the exact built ZIP and record the real host version, model/effort, installation method, invocation mode, and archive checksum; historical observations are not acceptance for a new skill. Tests are not a guarantee of consistent model behavior in every host.
5. Confirm CI's `dwebp` asset-decode check passed. For local asset verification, install libwebp's decoder through your system package manager and run `dwebp assets/icon.webp -o /tmp/english-proofreader-pro-icon.png`; the archive builder itself remains standard-library-only.
6. Confirm successful CodeQL analyses for both Python and GitHub Actions on the exact reviewed commit, then review the alerts. Resolve high/critical security alerts and error-level alerts, or record the maintainer's reasoned disposition before releasing. Confirm GitHub's immutable-release setting is enabled and the `Release tag integrity` ruleset protects `refs/tags/v*` against updates and deletion with no bypass actors. These settings live on GitHub, not in the archive.

## Publish the reviewed commit

1. Start from a clean checkout of the reviewed `master` commit: confirm `git status --short` is empty and verify the commit is the one containing the merged, reviewed pull request.
2. Build and verify the package from that checkout using the commands above. Confirm `plugin.json` has the exact intended version, and compute the archive checksum.
3. Create a new version tag (for example, `v1.2.3`) at that reviewed commit and create a **draft** GitHub release from the same tag. Attach the verified ZIP and a SHA-256 checksum file, and include the checksum in the release notes. Do not tag an unreviewed or different commit. Version tags cannot be moved or deleted under the tag ruleset.
4. Check the draft's tag, commit, notes, ZIP, and checksum before publishing. Attach all assets while it is a draft: immutable releases prevent changing the tag or assets after publication. Publish only after these checks pass. GitHub creates a release attestation binding the published tag, commit, and asset digests; this attests release integrity, not an independently verified build process.
5. With a current GitHub CLI, verify the published release and the downloaded ZIP:

   ```sh
   gh release verify v1.2.3 --repo altmn/english-proofreader-pro
   gh release verify-asset v1.2.3 dist/english-proofreader-pro-1.2.3.zip --repo altmn/english-proofreader-pro
   ```

   Substitute the actual tag and the downloaded archive path, then compare its SHA-256 with the published checksum. A local build is not necessarily byte-identical to the published ZIP. Verification must pass before distributing the downloaded artifact.
6. If submitting the ZIP to a separate plugin directory, use that platform's current process. GitHub source publication and plugin-directory submission are distinct; publishing one does not automatically publish the other, and submission is not approval or listing.
7. If a release needs correction, use a new version/tag and update `CHANGELOG.md` and release metadata through a new pull request against the default branch. Do not weaken the ruleset, reuse a tag, edit `master` directly, or backfill an unverified release history.

There is no pre-existing public release history recorded in this repository's changelog.

## References

- [GitHub Docs: About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [GitHub Docs: Creating releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
- [GitHub Docs: Immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)
- [GitHub Docs: Verify release integrity](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/verify-release-integrity)
