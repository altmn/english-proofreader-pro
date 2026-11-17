# Evaluation cases and acceptance checks

`cases.json` is a compact set of synthetic prompts for checking task selection and output properties. It intentionally uses assertions rather than fixed expected answers: valid minimal edits can differ, while invented edits and canned responses should not pass. It covers direct and implicit proofreading activation, no-op behavior, all shortening levels, Markdown preservation, literal fenced payloads and an explicit request to edit one, embedded instruction handling, the pronoun constraint, rewriting, new drafting, missing input, starter help, direct questions, and unrelated negative activation.

`agreement-probe.json` disambiguates the original list label "phrase link to URL" by adding a direct object. Test it separately: intentional list fragments are allowed, so the original label should not automatically be graded as an agreement error.

`host-behavior-cases.json` adds synthetic checks for source URL/app-command isolation, explicit verification outside source, programmatic letter/Unicode/word counts, honest behavior without tools, and native/fallback code-block presentation. Count and isolation assertions need tool traces; copy/wrapping assertions need actual UI and clipboard observations. Valid fixture JSON is not behavioral acceptance. Keep these separate from the unchanged historical suites.

## Local package checks

From the repository root, run:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/release.py validate
python3 scripts/release.py build
```

The offline unit tests exercise package validation, URL safety, metadata character limits, the skill's UTF-8 byte ceiling, allowlisting, symlink rejection, staging preservation/migration, and repeatable ZIP output. CI runs them on Python 3.11 and the latest stable Python. These tests do not call a model or require credentials.

## Model evaluation records

Use fresh sessions for each model run and retain the exact runner context, prompt, response, and source identity. The evaluation tool snapshots the current skill, manifest, runner context, and fixture prompts before responses are recorded. Snapshots cannot be overwritten; a changed skill or fixture set needs a new snapshot. The record command refuses to overwrite an existing file; edit the resulting record to grade assertions. The validator checks hashes, prompt and fixture coverage, and source binding; a human must judge semantic assertions. `not_run` is an allowed status until each assertion is reviewed, and every `fail` needs a note.

Create a snapshot:

```sh
python3 scripts/evaluate.py snapshot --id <slug> --runner-context <file> [--fixtures <repository-relative-file>]
```

Create a response record from the snapshot and a response bundle shaped as `{"responses":[{"id":"fixture-id","prompt":"exact fixture prompt","response":"model response"}]}`:

```sh
python3 scripts/evaluate.py record --snapshot <path> --responses <path> --model <name> --reasoning-effort <setting> --run-id <unique-slug> --host <name> --host-version <version-or-unknown> --invocation-mode <description> --date YYYY-MM-DD --source <description> --reviewer <name-or-role> --reviewer-context <description> [--install-method <text> --build-sha256 <sha256>] --out <path>
python3 scripts/evaluate.py validate <record.json> [--require-current] [--require-complete] [--require-pass]
python3 scripts/evaluate.py validate-suite <record.json> <record.json> <record.json> --fixtures tests/cases.json --model gpt-6.1-sol --reasoning-effort high --invocation-mode independent-agent-simulation --min-runs 3 --require-current --require-complete --require-pass
```

Every new schema-2 record also needs structured reasoning effort, a unique run ID, and reviewer metadata. An intended-host record must set `--invocation-mode intended-host` and include the exact host version, `--install-method`, and `--build-sha256`; simulation records may use `unknown` for `--host-version` only when `--invocation-mode` identifies the run as a simulation. Snapshot and record creation use exclusive writes, so simultaneous writers cannot replace an existing artifact. Grade a record only after its creation finishes.

The validator can require that evidence bind to current skill, manifest, and fixture files, that all assertions are graded, or that all graded assertions pass. Runner context stays bound to the exact text captured in the snapshot; changing a runner file does not alter a recorded run. New snapshots embed the original fixture text for historical verification. Older snapshots without it can be verified only while their fixture hash matches the current fixture. The older response files in `trials/` predate this record format and have unknown provenance; they remain historical evidence and are not converted into current records.

CI requires three passing current `gpt-6.1-sol` high-effort agent simulation records for both the original suite and the supplemental Markdown cases. That is a regression profile, not the recommended proofreading setting. CI references the tool-enabled `host-facts` captures and retains historical evidence, including the preceding `host-behavior` failure. Recommended Instant/default and installed-host acceptance remain pending. The suite gate enforces the expected fixture path (default `tests/cases.json`), complete frozen fixture bytes, exact model, effort, and invocation metadata, and unique run IDs. It rejects identical complete response sets by default; matching answers alone do not prove reused execution. After verifying distinct capture identities, an evaluator may explicitly acknowledge deterministic identical answers with `--identical-responses-note <review-explanation>`, which is echoed in the command output. Never edit responses or discard attempts to seek output variation. The checks verify declared provenance and flag obvious reuse, but cannot attest actual execution or independence. Historical schema-1 records remain valid individually without inventing structured metadata and cannot satisfy this gate. Luna failures remain historical evidence; a green CI result does not certify Luna or an installed host. Behavioral acceptance additionally requires intended-host checks. When changing bound source inputs, capture new runs and update CI's record paths; keep prior responses historical.

The original `cases.json` and Luna `evaluation-runner.txt` remain byte-for-byte unchanged during behavioral remediation. `behavior-runner.txt` and `engineering-review-runner.txt` retain the previous collaboration-agent protocols. The current `tool-enabled-runner.txt` permits programmatic counting and local checks and requires retaining the actual calculation code and output. Each generator receives only frozen skill and raw prompts/context; independent reviewers receive expectations after generation. Batched simulation runs are not installed-host conversations. All attempted runs remain evidence, including failed candidates. `host-counting-provenance-2026-11-16.json` binds each retained trace to its source snapshots and exact response hashes; offline integrity checks do not attest execution timing or semantic correctness.

`changes-markdown-cases.json` adds rewrites and shortening with emphasis, links, inline code, backslashes, tags, entities, and tildes. Grade both literal fenced output and rendered Changes: display escapes must preserve the visible source characters inside uninterrupted bold quotations and must never leak into the copyable result or count as edits. These supplemental cases have their own snapshots and source binding; `--fixtures` defaults to the original suite and permits only repository-relative paths. A rendered Markdown check is still separate from intended-host rendering and clipboard acceptance.

The current [GFM render proof](trials/host-facts-markdown-render-2026-11-16.json) retains exact HTML for all twelve final supplemental responses. The preceding [candidate proof](trials/host-behavior-markdown-render-2026-11-16.json) and [earlier proof](trials/review-markdown-render-2026-11-16.json) remain intact. `test_render_evidence.py` checks all three proofs' response and HTML hashes, complete case coverage, literal fenced content, and decoded full quotations inside bold. This is an offline integrity/regression check of retained renderer evidence, not a fresh rendering-service call or host acceptance. New captures need their own render evidence; never substitute synthetic ideal quotations for the actual generated responses.

`supplemental-facts.json` separately preregisters the known fresh-draft gap: watering plants does not establish that the writer was away. Supplemental records bind the rubric, source snapshot, graded response record, and response hashes. They add a check without replacing or changing any of the original 83 assertions. This is a known-case regression check, not a holdout evaluation.

Confirm the generated ZIP contains the intended skill-only package and that no user writing, credentials, or unrelated files were bundled. Install from the local marketplace catalog and refresh/reinstall after changing package files; a cached install does not track the working tree.

## Behavioral and host acceptance

Explicitly invoke the plugin or skill for **every test turn**, including follow-up prompts. In ChatGPT, select the plugin from the `@` picker each time; in Codex, include `$proofreader-pro` or select it through `/skills` for that turn. An earlier mention does not establish activation for a later message. Record the invocation actually used; an unmentioned response may use the host's ordinary writing workflow and cannot establish explicit-plugin behavior.

Use fresh, independent sessions for three complete runs of the fixture suite. Do not reuse one conversation's prior answers or expectations. Capture a snapshot before the runs and a separate complete response record for each run; unchanged inputs may share a snapshot. Check the response against each fixture's observable assertions and record pass/fail/not-run status with concise gap notes for every run. Compare behavior, not exact wording.

Then install the built package in the intended host and manually verify rendered and copied output: proofread text appears first, the outer fence safely contains source backticks, Markdown/list indentation survives copy-paste, change notes are outside the fence and enumerate only real supplied-text edits, and no-op output is exactly the specified sentence. Also check a new draft has no change list and an unrelated question is answered normally. Record the host/version, install method, checks, and any gaps; fix and rerun failures before release.

For this revision, also verify both no-space `@` picker labels, the distinctive Codex skill name, the recommended latest Instant setting, tool-backed counts, absence of source-authorized browsing/app actions in traces, and host-supported Copy code/soft wrapping without new copied line breaks. The older engineering runner forbids tools for solving cases; current simulations use the tool-enabled protocol and retain calculation traces. Those traces do not replace installed-host observation. No live installation or update is authorized by source preparation alone.

These are local acceptance checks, not claims that a public submission was scanned, reviewed, or approved. For the current OpenAI plugin upload and review steps, see [Upload and submit your plugin](https://developers.openai.com/plugins/deploy/submission).
