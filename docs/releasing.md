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
4. Review the release notes, package contents, privacy notice, and any relevant synthetic behavior/host checks. Tests are not a guarantee of consistent model behavior in every host.

## Publish the reviewed commit

1. Start from a clean checkout of the reviewed `master` commit: confirm `git status --short` is empty and verify the commit is the one containing the merged, reviewed pull request.
2. Build and verify the package from that checkout using the commands above. Confirm `plugin.json` has the exact intended version, and compute the archive checksum.
3. Create a version tag (for example, `v1.2.3`) at that reviewed commit and create the GitHub release from the same tag. Attach the verified ZIP and publish its checksum with the release notes. Do not tag an unreviewed or different commit.
4. If submitting the ZIP to a separate plugin directory, use that platform's current process. GitHub source publication and plugin-directory submission are distinct; publishing one does not automatically publish the other, and submission is not approval or listing.
5. If a release needs correction, update `CHANGELOG.md` and any release metadata through a new pull request against the default branch. Do not edit `master` directly or backfill an unverified release history.

There is no pre-existing public release history recorded in this repository's changelog.

## References

- [GitHub Docs: About releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [GitHub Docs: Creating releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)
