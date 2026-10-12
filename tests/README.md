# Evaluation cases and acceptance checks

`cases.json` is a compact set of synthetic prompts for checking task selection and output properties. It intentionally uses assertions rather than fixed expected answers: valid minimal edits can differ, while invented edits and canned responses should not pass. It covers direct and implicit proofreading activation, no-op behavior, all shortening levels, Markdown preservation, literal fenced payloads and an explicit request to edit one, embedded instruction handling, the pronoun constraint, rewriting, new drafting, missing input, starter help, direct questions, and unrelated negative activation.

`agreement-probe.json` disambiguates the original list label "phrase link to URL" by adding a direct object. Test it separately: intentional list fragments are allowed, so the original label should not automatically be graded as an agreement error.

## Local package checks

From the repository root, run:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/release.py validate
python3 scripts/release.py build
```

The offline unit tests exercise package validation, URL safety, character limits, allowlisting, symlink rejection, staging preservation, and repeatable ZIP output. CI runs them on Python 3.11 and the latest stable Python. These tests do not call a model or require credentials.

## Model evaluation records

Use fresh sessions for each model run and retain the exact runner context, prompt, response, and source identity. The evaluation tool snapshots the current skill, manifest, runner context, and fixture prompts before responses are recorded. Snapshots cannot be overwritten; a changed skill or fixture set needs a new snapshot. The record command refuses to overwrite an existing file; edit the resulting record to grade assertions. The validator checks hashes, prompt and fixture coverage, and source binding; a human must judge semantic assertions. `not_run` is an allowed status until each assertion is reviewed, and every `fail` needs a note.

Create a snapshot:

```sh
python3 scripts/evaluate.py snapshot --id <slug> --runner-context <file>
```

Create a response record from the snapshot and a response bundle shaped as `{"responses":[{"id":"fixture-id","prompt":"exact fixture prompt","response":"model response"}]}`:

```sh
python3 scripts/evaluate.py record --snapshot <path> --responses <path> --model <name> --host <name> --host-version <version-or-unknown> --invocation-mode <description> --date YYYY-MM-DD --source <description> --reviewer <name-or-role> --reviewer-context <description> [--install-method <text> --build-sha256 <sha256>] --out <path>
python3 scripts/evaluate.py validate <record.json> [--require-current] [--require-complete] [--require-pass]
```

Every record also needs reviewer metadata. An intended-host record must set `--invocation-mode intended-host` and include the exact host version, `--install-method`, and `--build-sha256`; simulation records may use `unknown` for `--host-version` only when `--invocation-mode` identifies the run as a simulation.

The validator can require that evidence bind to current skill, manifest, and fixture files, that all assertions are graded, or that all graded assertions pass. Runner context stays bound to the exact text captured in the snapshot; changing a runner file does not alter a recorded run. New snapshots embed the original fixture text for historical verification. Older snapshots without it can be verified only while their fixture hash matches the current fixture. The older response files in `trials/` predate this record format and have unknown provenance; they remain historical evidence and are not converted into current records.

CI checks that the selected current records are completely graded and additionally requires passing assertions for all three current `gpt-6.1-sol` high-effort runs. Luna failures remain in the records and block acceptance for that profile; a green CI result does not certify Luna or an installed host. Behavioral acceptance additionally requires intended-host checks. When changing bound source inputs, capture new runs and update CI's record paths; keep prior responses historical.

The original `cases.json` and Luna `evaluation-runner.txt` remain byte-for-byte unchanged during behavioral remediation. `behavior-runner.txt` provides an otherwise equivalent model-neutral simulation protocol, with the actual model and reasoning effort in each record's metadata. Each generator receives only frozen skill and raw prompts/context; an independent reviewer receives the expectations after generation. Batched simulation runs are not installed-host conversations. Baseline controls help distinguish instruction changes from model differences; all attempted runs remain evidence, including failed candidates.

`supplemental-facts.json` separately preregisters the known fresh-draft gap: watering plants does not establish that the writer was away. Supplemental records bind the rubric, source snapshot, graded response record, and response hashes. They add a check without replacing or changing any of the original 83 assertions. This is a known-case regression check, not a holdout evaluation.

Confirm the generated ZIP contains the intended skill-only package and that no user writing, credentials, or unrelated files were bundled. Install from the local marketplace catalog and refresh/reinstall after changing package files; a cached install does not track the working tree.

## Behavioral and host acceptance

Use fresh, independent sessions for three complete runs of the fixture suite. Do not reuse one conversation's prior answers or expectations. Capture a snapshot before the runs and a separate complete response record for each run; unchanged inputs may share a snapshot. Check the response against each fixture's observable assertions and record pass/fail/not-run status with concise gap notes for every run. Compare behavior, not exact wording.

Then install the built package in the intended host and manually verify rendered and copied output: proofread text appears first, the outer fence safely contains source backticks, Markdown/list indentation survives copy-paste, change notes are outside the fence and enumerate only real supplied-text edits, and no-op output is exactly the specified sentence. Also check a new draft has no change list and an unrelated question is answered normally. Record the host/version, install method, checks, and any gaps; fix and rerun failures before release.

These are local acceptance checks, not claims that a public submission was scanned, reviewed, or approved. For the current OpenAI plugin upload and review steps, see [Upload and submit your plugin](https://developers.openai.com/plugins/deploy/submission).
