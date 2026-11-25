# Known issues and to-do list

Updated November 25, 2026. Current private candidate: **1.0.9**. The user retained this candidate and then requested shipping through CI. This list records the pre-release verification checkpoint; use the linked pull request, CI runs, and published release for subsequent landing status. Native failures remain open.

## Known failures and capability gaps

- [ ] **P1 — Chat/Instant bypasses the counting gate.** The original letter-count question still returns an exact number while saying the verification script was unavailable. It must either execute the helper on the exact input or return only the specified no-count limitation. An explicitly worded helper request obtained the honest fallback, but the ordinary question did not. See the [1.0.9 Instant observations](tests/trials/resource-counting-safari-1.0.9-2026-11-25.json).
- [ ] **P1 — Chat/Instant misses the output and Changes contract.** Shortening still uses an editable writing block instead of a plain-text code block. Changes quotes only fragments instead of complete original/revised sentences or paragraphs. The latest quoted fragments are bold, and single-line payload copy worked; those successes do not resolve the remaining failures.
- [ ] **P2 — Chat/Instant shortening targets remain unverified.** The current less-wordy fixture produced 15 words from 25; its measured point target is 18. It correctly disclosed that programmatic verification was unavailable, so this was a qualitative fallback, not a verified target result. Verify both source and final measurements for all four shortening levels before claiming quantitative support in that mode.

The original **EPP-001 remains open for Chat/Instant**. The user has not adopted Work mode as a replacement acceptance target. The maintainer authorized releasing 1.0.9 with these documented native failures and incomplete acceptance checks; that decision does not turn them into passes.

## Finish verification and integration

- [x] **Complete independent grading of the V4 CLI captures.** All three retained captures pass 411/411 assertions: 249 original, 111 Markdown, 51 fragments. Exact responses/source bindings remain unchanged; judgment and application files retain reviewer/calibration limits.
- [x] **Render and review the actual V4 Markdown responses.** All twelve exact responses passed actual GitHub GFM rendering and literal/bold-quotation review. [Render evidence](tests/trials/resource-execution-v4-markdown-render-2026-11-25.json).
- [x] **Create and validate the V4 portable execution panel.** The [three-capture panel](tests/trials/resource-execution-v4-panel-2026-11-25.json) passes the portable checker against exact accepted outputs, real events, runtime receipts and graded records.
- [ ] **Verify hosted CI on the final candidate.** The workflow now references V4 suites and panel. Local profile/execution checks pass; hosted final-commit CI must pass before merge.
- [ ] **Finish intended-host acceptance.** Exercise nested fences, literal Markdown/URLs and indentation, longer wrapping/copy behavior, no-op/minimal edits, pronouns, draft facts, and source URL/app-command isolation with actual native observations and available traces. Keep unknown web-build, model-snapshot, and loaded-byte identity explicit.
- [ ] **Decide the supported native target before another repair iteration.** Current evidence separates failing Chat/Instant behavior from bounded Work-mode successes. If Chat/Instant remains required, establish a supported counting execution path and address its instruction-following failures; further wording changes alone are not established fixes.
- [ ] **Exercise removal/reinstallation only when specifically authorized.** The instructions are documented and syntax checked; the actual installed-host lifecycle was not tested.
- [ ] **Review the CLI startup-cache warning.** One V4 startup reported a failed system-skill installation because a directory was not empty. Required execution still passed, and the warning is retained in the harvest evidence. Its effect on the harness has not been established; do not edit the host cache by hand.
- [ ] **Review, commit, and push the continuation.** Land the continuation through PR [#8](https://github.com/altmn/english-proofreader-pro/pull/8) and require passing final-commit CI before merge. Recheck its state before committing; use a new branch if it has merged. Keep native acceptance and any pending CI gates visible in the PR. Repository landing and public directory publication are separate actions.

## What is already fixed or verified

- **EPP-002 — Build input drift:** both generated outputs use the same validated immutable snapshot; the explicit allowlist now contains seven runtime files, including the counter. Drift/corruption and preservation regressions pass.
- **EPP-003 — Fragment grading:** explicit noun-fragment/finite-clause cases and the versioned six-example calibration rubric are in place. Historical ambiguous grades remain preserved and qualified.
- **EPP-004 — Removal documentation:** supported disable, uninstall, marketplace cleanup, reinstall, and fresh-session checks are documented. Actual removal remains a separate unchecked lifecycle task above.
- **Offline helper and evidence gates:** exact counts, rounded budgets, safe fences, and escaped quote fields have deterministic coverage. Empty/trailing-line-ending block round trips were repaired. Resource-aware snapshots/records bind helper bytes; current local validation and build passed.
- **Local tests:** the latest completed full run passed **160 tests**. This does not substitute for current behavioral grading, CI, or native acceptance.
- **CLI execution:** all **three V4 captures passed** actual source/final execution, with direct helper calls, no command failures or guard denials, and no remaining owned CLI processes. Earlier V2 launch failures and the V3 guard denial remain retained. V3's two accepted captures passed 274 independent assertions and eight actual GFM renders; they use a different frozen runner and do not fill the V4 three-run panel.
- **Safari Work-mode smoke checks:** GPT-6.2 Sol Light / 2 of 6 showed calculation-command activity, a correct count, and the 25-to-18-word shortening result in a code block with full bold Changes. Native copy preserved that single-line payload. The inspected UI exposed command titles rather than raw command bodies/returned helper JSON, so exact execution identity and full host acceptance remain unverified. See [Work observations](tests/trials/resource-counting-safari-work-1.0.9-2026-11-25.json).
- **Private plugin:** 1.0.9 is saved in the same private plugin; source read-back matched the uploaded runtime text, and audience, identity, prompts, and retained files were preserved. No publisher backend was added.
- **Approved setting change:** the separate BuildWebApps plugin was disabled as requested so the SessionStart security audit could pass. Other configuration bytes and permissions were verified unchanged; security hooks remain active.

Package 1.0.9 ZIP SHA-256: `2d4c2accbe42dcf27dda066690a48df629e6a3519c1f664c5f3a775d0e55b6b1`.
