# November 25, 2026 audit fixes

These source repairs address the four findings from the skill-project audit of commit `ca6b3bd5ba6e4a06b7802364c5fadd94c45ce155`. They do not install or update a live plugin, publish a directory listing, or turn simulation evidence into intended-host acceptance.

| Finding | Source change and verification | Status |
| --- | --- | --- |
| EPP-001: Instant counting/shortening acceptance | A verified count now requires a returned tool measurement for the exact current text. Shortening requires comparing the result with the computed budget before acceptance. Three fresh CLI simulations each shortened the known 25-word less-wordy input to 18 words; calculation traces and complete responses are retained. | Candidate remediation implemented; native acceptance remains blocked pending a signed-in host and exact-artifact testing. |
| EPP-002: Build input drift | Capture six immutable byte payloads, validate that snapshot, build both outputs from it, and compare every prepared payload before promotion. Both drift regressions failed before the fix and pass afterward; corruption tests preserve previous outputs. | Resolved for the validated-snapshot contract. Sequential capture and two-output interruption limits remain. |
| EPP-003: Ambiguous fragment grading | Add explicit noun-fragment, finite-clause, and article-only cases, a versioned rubric, and six calibration examples. An independent reviewer committed all six judgments before comparison with gold labels, then reviewed all three new captures. | Resolved for the new grading panel. Historical ambiguous responses and verdicts remain unchanged and qualified. |
| EPP-004: Missing removal instructions | Document host-managed disable/removal, separate development marketplace cleanup, reinstallation, and fresh-session verification. Syntax checked against Codex CLI 0.170.0 and current official guidance. | Documentation resolved; actual installed-host removal was not exercised. |

The candidate skill is **11,390 UTF-8 bytes**, SHA-256 `4988f2bdbf4b336604906b6ad08562a94ec4a17b94732c9e3ce463ffbc863207`. Its six-file ZIP is SHA-256 `e803ad70cfaa447b98be0ad5f4a3ecad491b89fb5250c1c767ed21cbb7d95729`; all payloads match the stable reviewed source and local staging. These identify the candidate, not a published release.

## Regression evidence

Three fresh ephemeral **Codex CLI 0.170.0 / gpt-6.1-sol / high** runs received frozen skill instructions and raw prompts only. Each generated 25 cases: 18 original, four Markdown, and three fragment-calibration cases. Original expectations and historical answers were withheld. Separate reviewers graded the frozen outputs; no response was edited after capture. All **411 named assertions** passed: 249 original, 111 Markdown, and 51 fragment assertions. This is the configured CI simulation profile, not ChatGPT Instant or a held-out comparison.

The [attempt register](../tests/trials/audit-fixes-cli-attempts-2026-11-25.json) retains all seven attempts. Four transport preflights are excluded from the three-run panel: the CLI pre-created `responses.json` for its final-message output while generators were told to create that artifact exclusively. Two reached the deadline, and available raw outputs and tool logs are preserved. The corrected transport separates generator-owned `capture.json` from CLI-owned `completion.txt`. This correction preceded semantic grading; there was no best-answer selection or silent semantic retry.

[Source-bound calculation evidence](../tests/trials/audit-fixes-cli-counting-provenance-2026-11-25.json) retains actual command events, counting traces, and response hashes. The [GFM proof](../tests/trials/audit-fixes-markdown-render-2026-11-25.json) renders all twelve actual Markdown responses, with independently checked literal code text and full bold quotations. [Calibration results](../tests/trials/audit-fixes-fragment-calibration-result-2026-11-25.json) bind the committed judgments to rubric version 1.0. [Judgment application](../tests/trials/audit-fixes-judgment-application-2026-11-25.json) maps the reviewers' pre-grade inputs to graded records without changing any response or expectation.

CI now requires all three current suites and keeps the former `host-facts` captures as historical evidence. Current-source unit tests also verify retained trace, calibration, and renderer bindings. Hashes and declared profile checks do not independently attest model execution order, hidden actions, or broad reliability. No clean no-skill benefit, latency, cost, or automatic-routing claim is made.

The [local verification receipt](../tests/trials/audit-fixes-local-checks-2026-11-25.json) records **82 passing unit tests, zero skips**, all 46 current/historical record-integrity checks, all three current suite gates, validation, build, a byte-identical repeat build, exact ZIP/source/staging comparisons, and whitespace checks. The [build regression receipt](../tests/trials/audit-fixes-build-regressions-2026-11-25.json) retains the before-fix failures and the intermediate test adaptation; neither was discarded.

## Remaining native gate

The available ChatGPT browser surface was logged out during repair. No native trial, live installation, or account update was performed. The separate [native acceptance protocol](../tests/host-acceptance-runner.txt) requires exact candidate identity, real per-turn selection, returned counter results or an honest unavailable-tool branch, copied literal output, and source-action traces. Keep unknown web-build or activated-byte identity explicit. A code example or later admission cannot replace an execution trace; GFM HTML cannot replace native clipboard observation.

The November 16 Instant failures in [validation evidence](../tests/RESULTS.md) remain open until those checks are completed on the candidate. Passing the offline suite does not close EPP-001.
