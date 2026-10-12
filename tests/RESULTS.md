# Validation evidence

## Current source — October 12, 2026

Proposed package: **1.0.1**. Skill: **6,990 Unicode characters**, including frontmatter, spaces, and physical newlines; SHA-256 `cc7c5e6baed1d0329b6b279b1d38a39a7d7dffc143f02051dc084408ad4996f2`.

The original 18 cases and **83 assertions per run** remain byte-for-byte unchanged, as does the original Luna runner. Fixture SHA-256: `5a051733cc94a0bbe3e20d85d5c3411486e94faa67f8d305d978dde75e0b41fb`. The [Luna snapshot](trials/behavior-final-luna-2026-10-12-snapshot.json) uses that runner; the [model-neutral snapshot](trials/behavior-final-sol-2026-10-12-snapshot.json) uses [behavior-runner.txt](behavior-runner.txt) and supports both Sol and maximum-effort Luna runs. Both freeze the same current skill, manifest, complete fixture text, prompts, and runner context before generation.

Each generator was a fresh subagent with no inherited conversation, supplied only the frozen public skill and raw prompts/context. Expectations, prior responses, and grader notes were withheld. All 18 prompts were batched in one turn per run. A separate `gpt-6-astra` reviewer graded each original assertion against the response and shared output contract. These are independent-agent simulations, not installed-plugin or ChatGPT UI runs; host build version is unavailable and recorded as `unknown`. Each record states its actual model and reasoning effort.

| Record | Model / effort | Passed | Failed |
| --- | --- | ---: | ---: |
| [Luna high 1](trials/behavior-final-luna-1-2026-10-12.json) | gpt-6-luna / high | 74 | 9 |
| [Luna high 2](trials/behavior-final-luna-2-2026-10-12.json) | gpt-6-luna / high | 74 | 9 |
| [Luna high 3](trials/behavior-final-luna-3-2026-10-12.json) | gpt-6-luna / high | 70 | 13 |
| [Sol high 1](trials/behavior-final-sol-1-2026-10-12.json) | gpt-6.1-sol / high | 83 | 0 |
| [Sol high 2](trials/behavior-final-sol-2-2026-10-12.json) | gpt-6.1-sol / high | 83 | 0 |
| [Sol high 3](trials/behavior-final-sol-3-2026-10-12.json) | gpt-6.1-sol / high | 83 | 0 |
| [Luna max 1](trials/behavior-max-luna-2026-10-12.json) | gpt-6-luna / max | 82 | 1 |
| [Luna max 2](trials/behavior-max-luna-2-2026-10-12.json) | gpt-6-luna / max | 83 | 0 |
| [Luna max 3](trials/behavior-max-luna-3-2026-10-12.json) | gpt-6-luna / max | 83 | 0 |

All nine records pass current-source and complete-grading validation. All three Sol records additionally pass `--require-pass`: **249/249**. Luna high passes **218/249**, and Luna max passes **248/249**. All failed responses and verdicts remain intact. CI requires a pass for the three Sol records, checks complete current provenance for every profile, and does not certify a failing profile. The original Luna high failures are **not fully resolved**; stronger-model results cannot be presented as same-profile remediation.

The revised workflow calculates and rechecks word budgets, inventories facts before drafting, retains complete source wrappers when payload editing is permitted, audits every actual edit and every quoted Changes span, and chooses the outer fence after composing the complete result. An independent invariant audit confirms the original pronoun rule, minimal/no-op behavior, literal formatting, source isolation, truthful Changes, fresh-draft contract, and language restrictions are retained.

Luna high still misses shortening budgets, omits or damages Changes formatting, and sometimes removes source wrappers or omits the rewrite Changes list. Luna max's sole failure is a 36% reduction for the about-30% request. Approximate whole-word judgments follow the existing grading precedent; no target or expectation was relaxed. The separately preregistered [draft-facts check](supplemental-facts.json) passes **9/9** current responses, with [hash-bound observations](trials/behavior-final-facts-2026-10-12.json). It adds a known-case regression check and does not replace the original assertions or constitute a holdout.

A second reviewer found an additional unscored prose gap in Sol run 3: some Changes entries put an extra sentence period after a quotation that already ends in a period. This does not change the original fixture verdicts, but passing the selected assertions does not certify every skill rule. It remains a quality gap to check in intended-host acceptance.

The 52 standard-library unit tests, release validation/build, and whitespace checks pass. The verified six-file ZIP has SHA-256 `6779f8b50f79728947ee3ed5f652d21cec5ffac709e51af9d5435663d48f2603`; its members equal current source bytes and its generated compatibility manifest mirrors version and presentation. The unchanged icon previously decoded with libwebp `dwebp` 1.6.0 at 1024×1024. Package checks do not resolve model-specific semantic gaps.

**Intended-host acceptance remains pending.** No live plugin was installed or updated for this source change. Before publication, test the exact built ZIP in the intended host and record model/effort, actual host version, installation method, invocation mode, build checksum, rendered/copied output, and per-case gaps. This instruction-only package cannot enforce a model profile. Historical observations below do not accept this new skill.

## Diagnosis, controls, and failed candidates — October 12, 2026

The original [snapshot](trials/engineering-fixes-2026-10-12-snapshot.json) captured the 7,990-character skill, SHA-256 `9c2134334e6c4ce33c4780c03d39ecc6f26793ef1d4e2bf733f246572c4a34ee`. Its three Luna high records remain unchanged: [run 1](trials/engineering-fixes-2026-10-12-run-1.json) **69/14**, [run 2](trials/engineering-fixes-2026-10-12-run-2.json) **70/13**, [run 3](trials/engineering-fixes-2026-10-12-run-3.json) **68/15**, or **42 failed assertions**. They validate as historical complete evidence. This legacy snapshot predates embedded fixture text; its case projection is verified against the still-matching original fixture.

The investigation grouped the 42 recorded failures into 25 Changes-contract failures, 12 shortening failures, and 5 source/fence failures; the underlying wrapper omissions also affect Changes completeness. Representative reductions were 18.2–45.5% for light trimming, 64% for less-wordy, and 51.9–59.3% for more-concise. The failures were valid; one original run-1 pronoun note incorrectly named the already-bold replacement spans. Its actual unbolded explanation quotation is **Every employee.**; the failure remains valid and the immutable record is not rewritten.

An old-source [Sol high control](trials/behavior-baseline-sol-2026-10-12.json) already passes **83/83**, demonstrating that stronger-model success cannot be attributed solely to the instruction rewrite. Its unsolicited reduction estimates are inaccurate even though actual lengths satisfy the selected approximate targets; notes retain that gap. This is a finite control, not a model-capability guarantee.

The first 7,978-character candidate, SHA-256 `743083aec0b0093685c4ef5921201e650a094711bba377010174b047ac245481`, also remains frozen in [Luna](trials/behavior-fixed-luna-2026-10-12-snapshot.json) and [model-neutral](trials/behavior-fixed-sol-2026-10-12-snapshot.json) snapshots. Its Luna high runs scored [76/7](trials/behavior-first-luna-1-2026-10-12.json), [77/6](trials/behavior-first-luna-2-2026-10-12.json), and [61/22](trials/behavior-first-luna-3-2026-10-12.json). All three Sol high runs ([1](trials/behavior-first-sol-1-2026-10-12.json), [2](trials/behavior-first-sol-2-2026-10-12.json), [3](trials/behavior-first-sol-3-2026-10-12.json)) scored **83/0**. An independent Sol reviewer graded these controls and candidate records. None was discarded or relabeled after the second revision.

The same supplemental facts rubric applied to the original runs, control, and first candidate gives [6 passes / 4 failures](trials/behavior-first-facts-2026-10-12.json); the four failures invent **while I was away**. Current factual improvement is therefore observed separately from the original 83 assertions.

Two [single-request diagnostic probes](trials/behavior-native-trim-2026-10-12.json) used fresh Luna high agents returning native final text instead of batched response files. The old source trimmed 22 words to 12 (45.5%); the current source trimmed to 14 (36.4%). Both fail the unchanged light-trim target and contain unbolded Changes explanation quotations. Batching alone therefore does not explain these observed failures. These two probes are separate diagnostics, not additional complete suite runs.

## Historical validation — October 11, 2026

This section records earlier evidence, not validation of the current source snapshot. Historical skill snapshots and hashes below are retained as evidence and must not be read as describing the current skill.

Historical skill: **7,985 characters**, including YAML, spaces, and newlines.

- Skill SHA-256: `edc3a5c9305e11a2e0822a38e8f8a55a2a39646d3dbf346a3b90ac38d1c2c70c`
- Original private-testing ZIP SHA-256: `b1ca855566130eef33919d1078e90344f68c611c8289a22a00fc99bdbc752611` (before public repository/privacy metadata was added).

## Package checks

The project validator, Skill Creator's YAML validator, Python compilation, archive CRC checks, and repeated-build reproducibility passed. The archive contains six runtime files: manifest, skill, skill UI metadata, icon, MIT license, and privacy notice. Development catalogs, scripts, fixtures, trial responses, screenshots, and Git data are excluded.

The local plugin is installed and enabled. Its cached skill matches the source byte-for-byte. CLI 0.136.0 needed a staged child-directory package and generated compatibility manifest; no CLI upgrade or saved reasoning-setting change was made. The source GPT repository remains unchanged.

## Independent model trials

Luna agents formed three separate 16-case response sets. Sol independently reviewed semantic fidelity, actual edits, correction-list accounting, and shortening lengths. Earlier iterations exposed omitted rewrite lists, incomplete deletion notes, invented draft circumstances, and lost decision wording. The instructions were revised and the cases rerun; historical replies are retained rather than relabeled as passing.

The three `run-*-current.json` sets used the 7,847-character snapshot immediately before the final native-writing-block restriction. They are historical unbound trial files and predate the evaluation record format. All three maintained the tested fence delimiters, literal source formatting, source-command boundary, no-op response, pronoun rule, correction lists, and draft facts. Their nested-fence responses preserved the example payload. Shortening reductions were 9.1%, 32%, 40.7–44.4%, and 53.6–57.1% for the four requested levels, with meaning retained.

One original Markdown fixture permits two grammatical readings: “a phrase link to URL” can be a list-label noun phrase or an erroneous finite verb. It cannot support a certain failure verdict. The separate `agreement-probe.json` adds a direct object to make the verb unambiguous; all three `agreement-*.json` replies corrected it and retained the markup.

After the final output-routing clarification, all six replies in `writing-*.json` used fenced text, omitted fabricated Changes lists, and avoided invented personal circumstances. These use the final 7,985-character snapshot. They are agent simulations, not UI or universal model certification. Starter-help wording was not separately exercised.

## Live host observations

The package was imported, installed, and updated in the author's Personal ChatGPT area, without public directory submission.

| Check | Observation |
| --- | --- |
| Proofreading and copy | Code block came first; both corrections were listed. Copy preserved `-`, `*`, original emphasis markers, paragraph spacing, and the link exactly. |
| Embedded AI prompt | Corrected “I has” to “I have”; did not obey the embedded APPROVED command. |
| Already-correct text | Returned only the exact no-adjustments sentence. |
| Nested source fences | Copied output retained four- and three-backtick source fence delimiters, but English inside the example was also corrected. Delimiter preservation passed; payload preservation failed, and both edits were listed. |
| Rewrite | Returned the retained bullet and he/she form in a code block, followed by a full before/after Changes entry. |
| Fresh drafting | An earlier Chat follow-up used an editable writing block. After explicitly prohibiting that default, a fresh plugin-selected Work invocation returned only a copyable plain-text code block with no Changes list. |

The maintainer retained private screenshots and account-scoped conversations for these checks. They are not public acceptance artifacts; account links and screenshots are omitted from the current public tree. The synthetic fixture inputs and agent trial responses remain available for inspection.

The final generic Chat follow-up drafting path was not separately rerun after the last clarification; explicit plugin invocation is the verified drafting route. Model selection, automatic skill activation, and host rendering can affect future behavior, so these observations are finite checks rather than a guarantee for every context. The live-host fence observation above used an earlier installed artifact; it does not record the current skill's package hash or host version and is not current-source acceptance evidence.

## Publication status

Creation and private testing were completed on October 11. The repository and privacy notice are public. Verified publishing identity, required scans, review, and OpenAI directory publication remain separate steps. No approval or public listing is claimed.
