# Evaluation cases and acceptance checks

`cases.json` is a compact set of synthetic prompts for checking task selection and output properties. It intentionally uses assertions rather than fixed expected answers: valid minimal edits can differ, while invented edits and canned responses should not pass. It covers direct and implicit proofreading activation, no-op behavior, all shortening levels, Markdown preservation, literal fenced payloads and an explicit request to edit one, embedded instruction handling, the pronoun constraint, rewriting, new drafting, missing input, starter help, direct questions, and unrelated negative activation.

`agreement-probe.json` disambiguates the original list label "phrase link to URL" by adding a direct object. Test it separately: intentional list fragments are allowed, so the original label should not automatically be graded as an agreement error.

`host-behavior-cases.json` adds synthetic checks for source URL/app-command isolation, explicit verification outside source, programmatic letter/Unicode/word counts, honest behavior without tools, and native/fallback code-block presentation. Count and isolation assertions need tool traces; copy/wrapping assertions need actual UI and clipboard observations. Valid fixture JSON is not behavioral acceptance. Keep these separate from the unchanged historical suites.

## Fragment and agreement calibration

[The supplemental calibration fixture](fragment-calibration-cases.json) separates explicit noun-phrase labels from an explicit finite clause. It also pairs fragment preservation with a clear article error, so a blanket no-op cannot pass. The oracle comes from the user directions and grammatical roles; it does not treat the ambiguous original fixture as proof of a failure or a necessary correction.

Use `--fixtures tests/fragment-calibration-cases.json` with the snapshot/record workflow below. The complete frozen fixture includes reviewer rubric `fragment-agreement-calibration` version `1.0` and six calibration examples. Withhold expectations, rubric, and calibration examples from generators. Before reviewing new captures, an independent reviewer commits judgments on all six examples, then checks the expected verdicts. Retain every disagreement; a reviewer who misses an example must recalibrate under a new rubric version before scoring. Bind the calibration judgments to the rubric version and snapshot/fixture hashes, then grade every assertion against the complete captured output.

These three cases are synthetic known-case regressions, not a holdout. Fixture validation and reviewer calibration do not establish model behavior or installed-host acceptance. Keep the original fixtures and historical responses, notes, and verdicts unchanged.

The November 25 `audit-fixes` and `count-routing` panels are historical for their own source bytes. **The `count-routing` generation protocol failed:** capture 3 has no observed execution backing its final word/fence measurements. Passing visible-output grades, valid hashes, and the actual GFM renders do not repair that missing execution. Retain the [protocol review](trials/count-routing-cli-protocol-review-2026-11-25.json), raw captures, failed claims, and earlier transport attempts unchanged. See [audit-fix evidence](../docs/audit-fixes.md) for dispositions.

The resource-assisted 1.0.7 [preparation receipt](trials/resource-execution-preparation-2026-11-25.json) records `not_run` and the outstanding SessionStart approval; that preparation remains historical and superseded. The three V2 launch failures and the V3 guard-denied attempt remain preserved. The 1.0.9 [V4 panel](trials/resource-execution-v4-panel-2026-11-25.json) binds three accepted CLI captures with 411/411 independently reviewed assertions passing across the original, Markdown, and fragment suites. Its portable execution check and twelve actual-response GFM render checks pass. These are known synthetic regressions, not native acceptance. The fragment review explicitly reuses the retained six-example calibration and discloses prior gold exposure; it is not a new blinded calibration. Native acceptance remains separate under the [installed-host protocol](host-acceptance-runner.txt), with known Chat/Instant failures in [the issue list](../KNOWN_ISSUES.md).

## Local package checks

From the repository root, run:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/release.py validate
python3 scripts/release.py build
```

The offline unit tests exercise package validation, URL safety, metadata character limits, the skill's UTF-8 byte ceiling, allowlisting, symlink rejection, staging preservation/migration, and repeatable ZIP output. CI runs them on Python 3.11 and the latest stable Python. These tests do not call a model or require credentials.

## Model evaluation records

Use fresh sessions for each model run and retain the exact runner context, prompt, response, and source identity. The evaluation tool snapshots the skill, manifest, allowlisted helper, runner context, and fixture prompts before responses are recorded. Snapshot schema **2** embeds `resources` entries with `path`, exact UTF-8 `text`, `sha256`, and `utf8_byte_count`; record schema **3** binds their path/hash map in `source_binding.resources`. The current resource allowlist is `skills/proofreader-pro/scripts/text_metrics.py` only. The evaluator reads it as bounded UTF-8 data, never imports or executes preserved resource text.

Snapshots and records use exclusive creation. Changed skill, manifest, helper, or fixture bytes need new snapshots and runs; never relabel an earlier pass. A missing or changed live helper prevents current acceptance, while saved resource-aware evidence remains historically verifiable from embedded bytes. Grade only assertion fields after record creation finishes; preserve every response and source binding. The validator checks hashes and coverage, while an independent reviewer judges semantics. `not_run` is valid until review, and every `fail` needs a note.

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

Every new schema-3 record also needs structured reasoning effort, a unique run ID, and reviewer metadata. New records require a resource-aware snapshot. An intended-host record must set `--invocation-mode intended-host` and include the actual host version, `--install-method`, and `--build-sha256`; simulation records may use `unknown` for `--host-version` only when the invocation mode identifies a simulation. Do not invent unavailable native build or activation identity to satisfy a schema; keep such observations in a clearly limited companion record.

The validator can require current skill, manifest, helper, and fixture bytes, complete grading, or passing assertions. Runner context remains bound to its frozen snapshot text; changing a runner file does not rewrite a recorded run. Snapshot schema 1 and record schemas 1/2 remain historically verifiable and cannot accept the resource-assisted candidate. Older snapshots without embedded fixture text still require matching current fixture bytes. Resource-aware snapshots preserve fixture and helper text for historical verification even after local files change or disappear. Older response files with unknown provenance remain historical; do not manufacture new metadata or runs for them.

Regression acceptance requires three current, independently reviewed runs for the original, Markdown, and fragment suites under the declared `gpt-6.1-sol` / high CLI profile, plus the execution gate below. This is a regression profile, not the recommended native setting. The suite validator enforces fixture identity, complete frozen inputs, exact model/effort/invocation metadata, and distinct run IDs. It rejects identical complete response sets by default; matching text alone does not prove reused execution. After reviewing distinct capture provenance, an evaluator may explicitly acknowledge deterministic identical answers with `--identical-responses-note <review-explanation>`. Never change responses or discard attempts to create variation. Structured schema-2 records can still form historical suites without claiming current resource acceptance; schema-1 records cannot establish a structured new run. These metadata and semantic checks alone do not establish tool execution or native behavior. Update CI to reviewed fresh record paths only after their captures and grading exist; keep all prior records historical.

The original `cases.json` and Luna `evaluation-runner.txt` remain unchanged. Earlier collaboration runners and `tool-enabled-runner.txt` remain evidence of their own protocols; the resource-assisted execution protocol is `verified-execution-runner.txt`. Give generators frozen skill/resource inputs, raw prompts/context, and mechanical execution requirements, while withholding semantic rubrics, calibration examples, old answers, and grading notes. Reviewers receive expectations after generation. Batched CLI captures are not installed-host conversations. Keep every attempt and exclusion; a saved trace or code example is not proof that its code ran.

## Documentation-only 1.0.10 release

Version 1.0.10 changes only the manifest version and publication release notes in the installable package. The README and setup guidance have changed; the six other runtime files are byte-identical to the verified published 1.0.9 ZIP. The reviewed [metadata-only receipt](metadata-release-1.0.10.json) pins that archive checksum, runtime inventory, and retained snapshot/panel references.

```sh
python3 scripts/check_metadata_release.py tests/metadata-release-1.0.10.json
```

This separate gate rejects any other manifest configuration or runtime change. It runs the existing strict profile, distinct-run, and execution validators in a temporary copy using the exact frozen 1.0.9 manifest and unchanged current skill/helper/fixtures. It never rewrites retained records or the candidate manifest. The original `--require-current` semantics remain strict: these captures are historical for 1.0.10. This is a metadata-only equivalence check, with no new model runs or native acceptance. Existing known host failures remain open. A future behavior release requires fresh evidence and an updated CI gate; this receipt accepts only version 1.0.10.

## CLI execution acceptance

Use [the execution runner](verified-execution-runner.txt) with [capture_protocol.py](../scripts/capture_protocol.py). The controller freezes fixture-derived mechanical requirements, a fresh per-run challenge, source/helper/interpreter identities, and new candidate/accepted paths. Its plan, collected CLI stdout, and accepted copies must be outside **all** generator-writable roots, including shared temporary directories and any external executor's write scope. A directory name or `chmod` alone does not establish isolation. Inspect the actual launch chain, honor required SessionStart approval, and verify the chosen permission boundary before claiming it protects collection.

The controller's `prepare` command accepts `--requirements`, `--candidate`, `--plan`, and `--accepted` paths and prints two exact measurement commands. The generator must execute the source command and receive successful structured stdout before proceeding, save only a provisional candidate, then execute the final command and receive its successful result for those exact candidate bytes. Both commands delegate arithmetic and fence metrics to the frozen shipped helper. Never replace either call with displayed code, a handwritten trace, or a later controller/reviewer recount.

After the CLI turn completes, the controller runs `verify --plan ... --events ... --receipt ...`. Acceptance requires successful ordered source/final command events, the fresh challenge, exact helper/resource/input identities, matching returned measurements, and the final candidate hash. Only then does the controller exclusively create `accepted_path`; a failure retains its evidence and receives no accepted copy. Generate evaluation records only from that accepted copy. For the evaluator's per-suite transport bundle, the controller may attach frozen prompts from snapshots, while preserving response strings exactly.

The public panel uses `schema_version: 1`, `kind: "executed-capture-panel"`, and at least three `captures`. Each capture contains `run_id`, `original_plan_path`, references named `plan`, `events`, `accepted`, and `receipt`, and three `records` references. Each reference has a repository-relative `path` and `sha256`. Event references may name gzip files; their reference hash covers compressed bytes, while the runtime receipt retains the uncompressed event hash. Recorded original host paths identify the observed commands and are not paths to execute in CI.

Run the portable gate on the reviewed current panel and its graded records:

```sh
python3 scripts/check_capture_evidence.py tests/trials/resource-execution-v4-panel-2026-11-25.json
```

[The portable checker](../scripts/check_capture_evidence.py) reuses record validation, binds the current shipped helper to snapshot resources and plan identities, checks full fixture/case coverage, matches actual execution events, and compares accepted response strings with all three graded records. It loads only reviewed **current** local helper code for its independent integrity recount; historical embedded text and recorded interpreter paths remain inert. Missing generator execution cannot become a pass through that recount. The check trusts the protected original event collector; it does not authenticate that collector, attest an old interpreter binary on another OS, prove hidden composition timing, grade semantics, or replace native acceptance.

Changing helper/resource bytes invalidates current execution evidence and requires a new freeze. Preserve failed attempts and do not weaken the profile or gate to obtain a pass.

`changes-markdown-cases.json` adds rewrites and shortening with emphasis, links, inline code, backslashes, tags, entities, and tildes. Grade both literal fenced output and rendered Changes: display escapes must preserve the visible source characters inside uninterrupted bold quotations and must never leak into the copyable result or count as edits. These supplemental cases have their own snapshots and source binding; `--fixtures` defaults to the original suite and permits only repository-relative paths. A rendered Markdown check is still separate from intended-host rendering and clipboard acceptance.

The historical [count-routing GFM proof](trials/count-routing-markdown-render-2026-11-25.json) retains exact HTML for its twelve supplemental responses. Earlier proofs remain intact. `test_render_evidence.py` checks response and HTML hashes, case coverage, literal fenced content, and full bold quotations for the retained proofs. Those checks do not establish a fresh rendering-service call or resource-assisted/native acceptance. New captures need their own actual-response render evidence; never substitute ideal synthetic quotations for generated responses.

The current [V4 GFM proof](trials/resource-execution-v4-markdown-render-2026-11-25.json) retains twelve actual GitHub Markdown API renders of the exact accepted V4 responses. The render-evidence test checks all three captures, literal fenced text, and uninterrupted bold original/revised quotations. This renderer evidence does not establish native ChatGPT rendering or clipboard behavior.

`supplemental-facts.json` separately preregisters the known fresh-draft gap: watering plants does not establish that the writer was away. Supplemental records bind the rubric, source snapshot, graded response record, and response hashes. They add a check without replacing or changing any of the original 83 assertions. This is a known-case regression check, not a holdout evaluation.

Confirm the generated ZIP contains the intended seven runtime files, including the offline helper, with no user writing, credentials, or unrelated files. Install from the local marketplace catalog and refresh/reinstall after changing package files; a cached install does not track the working tree. Installation and live updates require authorization separate from source preparation.

## Behavioral and host acceptance

Explicitly invoke the plugin or skill for **every test turn**, including follow-up prompts. In ChatGPT, select the plugin from the `@` picker each time; in Codex, include `$proofreader-pro` or select it through `/skills` for that turn. An earlier mention does not establish activation for a later message. Record the invocation actually used; an unmentioned response may use the host's ordinary writing workflow and cannot establish explicit-plugin behavior.

Use fresh, independent sessions for three complete runs of the fixture suite. Do not reuse one conversation's prior answers or expectations. Capture a snapshot before the runs and a separate complete response record for each run; unchanged inputs may share a snapshot. Check the response against each fixture's observable assertions and record pass/fail/not-run status with concise gap notes for every run. Compare behavior, not exact wording.

Then install the built package in the intended host and manually verify rendered and copied output: proofread text appears first, the outer fence safely contains source backticks, Markdown/list indentation survives copy-paste, change notes are outside the fence and enumerate only real supplied-text edits, and no-op output is exactly the specified sentence. Also check a new draft has no change list and an unrelated question is answered normally. Record the host/version, install method, checks, and any gaps; fix and rerun failures before release.

For the resource-assisted revision, verify the actual host can access and execute the bundled helper through an exposed function. A visible skill description, selected plugin, setup reply, or code example does not by itself prove execution for another turn. Check direct counts, source/final shortening measurements and the requested level, honest unavailable-tool responses, source-action isolation, and native Copy code/wrapping without added copied newlines. Keep a host's missing helper/executor capability separate from a failed tool call or incorrect output. Retain unknown model/build/activated-byte identity explicitly. CLI execution receipts and renderer proofs do not replace these native observations.

These are local acceptance checks, not claims that a public submission was scanned, reviewed, or approved. For the current OpenAI plugin upload and review steps, see [Upload and submit your plugin](https://developers.openai.com/plugins/deploy/submission).
