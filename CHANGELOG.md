# Changelog

This file records notable changes to the repository's distributable package. An `Unreleased` entry is repository history, not evidence that a package has been publicly published.

## [1.0.10] - 2026-11-27

### Documentation

- Present the skill with a short introduction and proofreading example, followed by concise usage, installation, troubleshooting, and maintenance prompts.
- Clarify skill selection in ChatGPT and Codex, and distinguish Claude web from Claude Code setup.
- Preserve existing section links and improve mobile readability.

### Package

- Update the version and release notes. The skill instructions, counting helper, UI metadata, icon, and notices are byte-for-byte unchanged from 1.0.9.
- Retain 1.0.9 behavioral evidence as historical evidence; this documentation release does not establish new model or native-host acceptance. Existing limitations remain unchanged.

## [1.0.9] - 2026-11-25

### Added

- Measure exact text counts and shortening budgets with the bundled offline Python helper when the host can execute it. Preserve literal copyable blocks and full bold Changes quotations.
- Verify saved CLI results against actual source and final measurement commands, with independently reviewed regression and Markdown-rendering evidence.

### Fixed

- Keep the ZIP and local installation consistent by building both from the same validated runtime snapshot.
- Distinguish intentional fragments from agreement errors in regression cases, and document disabling, removal and reinstallation.

### Known limitations

- Chat/Instant still fails the counting fallback and full output/Changes contract. Native shortening verification and complete native copy/source-isolation acceptance remain open. Work-mode smoke checks and passing CLI evaluations do not clear those gaps. See [known issues](KNOWN_ISSUES.md).

## Earlier unreleased preparation

- Add a bundled offline Python helper for exact text measurements, shortening budgets, safe literal blocks, and escaped Changes quotations. Bind helper bytes in new evaluation snapshots and records. Accept CLI captures only after independently collected source/final execution results pass the protected controller and portable CI gate; preserve prior protocol failures. Fix empty and trailing-newline block round trips. Private candidate updates and Safari observations remain separate from behavioral acceptance.

- Build ZIP and local staging from one validated immutable runtime snapshot, and compare payload bytes before promotion. Add regressions for source edits during preparation and corrupted prepared outputs. Add explicit fragment/finite-clause fixtures with reviewer calibration, document host-managed removal, and tighten the counting-execution and shortening-budget acceptance gates. Advertise standalone counting in skill discovery. Retain authorized private Safari candidate tests, including unresolved counting-evidence and shortening failures; native acceptance has not passed.

- Require programmatic counts and candid limitations when counting tools are unavailable; strengthen isolation of source URLs and tool/app commands. Forbid adding recipients or circumstances to meet a word budget, following a recorded simulation failure. Prefer plain-text code blocks with copy and soft-wrap controls where the host supports them. Replace "prose" with "text" in current instructions and listing metadata. Recommend the latest ChatGPT Instant model at its normal setting without claiming package-level model control.

- Replace the generic `$proofread` skill with `$proofreader-pro`; expose `EnglishProofreaderPro` and `ProofreaderPro` as plugin and skill picker labels. Remove the project-specific 8,000-character cap, retain a 1 MiB UTF-8 build safeguard, and migrate the known generated staging layouts through the builder. Add synthetic host/counting cases and a tool-enabled simulation protocol with retained counting and renderer evidence. Recommended-model and installed-host acceptance remain pending.

- Preserve literal Markdown inside bold Changes quotations with display-only escaping; add combined rewrite/shortening regressions. Refuse concurrent evaluation overwrites, require structured evaluation profiles and distinct run evidence, reject empty skill bodies and forbidden raw YAML characters, and tie submission guidance to the reviewed artifact instead of stale counts.

- Reorganize the editing workflow around calculated shortening budgets, complete source wrappers, a before/after edit ledger with bold quoted spans, supported drafting facts, and a final safe-fence check. Preserve all original behavioral assertions and failed captures; record baseline controls, both candidate revisions, and model/effort-specific reruns. At that revision, stronger-model simulations passed; Luna gaps and pending intended-host acceptance remain documented.

- Prepare package 1.0.1: preserve fenced example payloads unless explicitly selected for editing, harden manifest/YAML/icon/character-limit validation, preserve verified outputs on failed builds, and bind new behavioral records to exact inputs and per-assertion verdicts. Historical host observations remain historical; the revised skill requires fresh intended-host acceptance before publication.

- Prepare ChatGPT directory metadata with public policy/support links, worldwide targeting, and a no-commerce declaration; keep portal verification and submission separate.

- Prepare the repository for open-source contributions with community guidance, issue and pull-request templates, and maintainer/security reporting instructions.
- Add deterministic tests and release validation/build tooling; package metadata and release guidance are maintained through pull requests.

The package version is maintained in `plugin.json`. A prepared changelog entry is not proof of publication; verify the matching GitHub release and its attached archive.
