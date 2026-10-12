# Validation evidence

## Current source — October 12, 2026

Proposed package: **1.0.1**. Skill: **7,990 Unicode characters**, including frontmatter, spaces, and physical newlines; SHA-256 `9c2134334e6c4ce33c4780c03d39ecc6f26793ef1d4e2bf733f246572c4a34ee`.

The [frozen input snapshot](trials/engineering-fixes-2026-10-12-snapshot.json) binds the exact skill, manifest, fixture hash and case projections, and [runner context](evaluation-runner.txt). This first snapshot predates embedded fixture text; its complete 18-case projection is verified against the matching current fixture. It was captured before generation and remains unchanged. Later snapshots also embed the original fixture for self-contained historical checks.

Three fresh `gpt-6-luna` subagents, each with no inherited conversation, generated all 18 prompts in a single batched turn per run. They received the skill and raw prompts/context; fixture expectations and prior trial answers were withheld. A separate `gpt-6-sol` reviewer manually graded every fixture assertion against the captured responses and the shared output contract. These are independent-agent simulations, not installed-plugin or ChatGPT UI runs. Exact host build version is unavailable and is recorded as `unknown`.

| Record | Passed assertions | Failed assertions | Aggregate |
| --- | ---: | ---: | --- |
| [Run 1](trials/engineering-fixes-2026-10-12-run-1.json) | 69 | 14 | fail |
| [Run 2](trials/engineering-fixes-2026-10-12-run-2.json) | 70 | 13 | fail |
| [Run 3](trials/engineering-fixes-2026-10-12-run-3.json) | 68 | 15 | fail |

All **249 assertions** have explicit verdicts and notes. All three records pass provenance/current-source and complete-grading validation. None passes behavioral acceptance (`--require-pass`), and failed responses have not been edited or relabeled as successes.

The main gaps are excessive shortening, quoted explanation spans without bold formatting in Changes lists, and explicit fenced-payload editing. Default nested-example payload preservation passed all three runs. For the explicit-edit exception, runs 1 and 3 lose source delimiters; run 2 includes the user's editing directive in the returned source. Runs 1 and 2 also invent "while I was away" in a fresh draft: that violates the public skill even though the fixture's length/tone assertion passes. The reviewer records this additional rule gap in its notes; passing selected fixture assertions does not certify all skill rules.

The standard-library package checks pass, and the verified six-file ZIP has SHA-256 `aabcb183716fbe75ae0421fbb8077eca974a9042939239fface921e82b821aff`. Its members equal the current source bytes, and the generated local compatibility manifest mirrors version and presentation. The icon decoded successfully with libwebp `dwebp` 1.6.0 at 1024×1024. Offline package checks and successful pixel decoding do not resolve the semantic failures above.

**Intended-host acceptance remains pending.** No live plugin was installed or updated for this source change. Before publication, test the exact built ZIP in the intended host and record the actual host version, installation method, invocation mode, build checksum, copied/rendered output, and per-case gaps. Historical observations below are not acceptance for this new skill.

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
