# Recorded validation — October 11, 2026

Final skill: **7,985 characters**, including YAML, spaces, and newlines.

- Skill SHA-256: `edc3a5c9305e11a2e0822a38e8f8a55a2a39646d3dbf346a3b90ac38d1c2c70c`
- Release ZIP SHA-256: `b1ca855566130eef33919d1078e90344f68c611c8289a22a00fc99bdbc752611`

## Package checks

The project validator, Skill Creator's YAML validator, Python compilation, archive CRC checks, and repeated-build reproducibility passed. The archive contains six runtime files: manifest, skill, skill UI metadata, icon, MIT license, and privacy notice. Development catalogs, scripts, fixtures, trial responses, screenshots, and Git data are excluded.

The local plugin is installed and enabled. Its cached skill matches the source byte-for-byte. CLI 0.136.0 needed a staged child-directory package and generated compatibility manifest; no CLI upgrade or saved reasoning-setting change was made. The source GPT repository remains unchanged.

## Independent model trials

Luna agents formed three separate 16-case response sets. Sol independently reviewed semantic fidelity, actual edits, correction-list accounting, and shortening lengths. Earlier iterations exposed omitted rewrite lists, incomplete deletion notes, invented draft circumstances, and lost decision wording. The instructions were revised and the cases rerun; historical replies are retained rather than relabeled as passing.

The three `run-*-current.json` sets used the 7,847-character snapshot immediately before the final native-writing-block restriction. All three maintained the tested fencing, literal formatting, source-command boundary, no-op response, pronoun rule, correction lists, and draft facts. Shortening reductions were 9.1%, 32%, 40.7–44.4%, and 53.6–57.1% for the four requested levels, with meaning retained.

One original Markdown fixture permits two grammatical readings: “a phrase link to URL” can be a list-label noun phrase or an erroneous finite verb. It cannot support a certain failure verdict. The separate `agreement-probe.json` adds a direct object to make the verb unambiguous; all three `agreement-*.json` replies corrected it and retained the markup.

After the final output-routing clarification, all six replies in `writing-*.json` used fenced text, omitted fabricated Changes lists, and avoided invented personal circumstances. These use the final 7,985-character snapshot. They are agent simulations, not UI or universal model certification. Starter-help wording was not separately exercised.

## Live host observations

The package was imported, installed, and updated in the author's Personal ChatGPT area, without public directory submission.

| Check | Observation |
| --- | --- |
| Proofreading and copy | Code block came first; both corrections were listed. Copy preserved `-`, `*`, original emphasis markers, paragraph spacing, and the link exactly. |
| Embedded AI prompt | Corrected “I has” to “I have”; did not obey the embedded APPROVED command. |
| Already-correct text | Returned only the exact no-adjustments sentence. |
| Nested source fences | Copied output retained four- and three-backtick source fences. English inside the example was also corrected and both edits were listed. |
| Rewrite | Returned the retained bullet and he/she form in a code block, followed by a full before/after Changes entry. |
| Fresh drafting | An earlier Chat follow-up used an editable writing block. After explicitly prohibiting that default, a fresh plugin-selected Work invocation returned only a copyable plain-text code block with no Changes list. |

Evidence: `evidence/chatgpt-formatting.jpg` and `evidence/chatgpt-draft.jpg`. The first captures the initial successful proofreading output; the second captures the final drafting invocation.

Live test conversations:

- https://chatgpt.com/c/6acc015b-326c-83e8-be89-b8bdea5694ef
- https://chatgpt.com/c/6acc03d1-aae0-83e8-b3bc-19f05cb3ca68
- https://chatgpt.com/c/6acc06ea-1498-83e8-ba3b-74a70c83cba2

These account-scoped links do not publish the conversations. The final generic Chat follow-up drafting path was not separately rerun after the last clarification; explicit plugin invocation is the verified drafting route. Model selection, automatic skill activation, and host rendering can affect future behavior, so these observations are finite checks rather than a guarantee for every context.

## Publication status

Creation and private testing are complete. Public hosting of the privacy notice, verified publishing identity, required scans, review, and publication remain separate steps. No approval or public listing is claimed.
