# Evaluation cases and acceptance checks

`cases.json` is a compact set of synthetic prompts for checking task selection and output properties. It intentionally uses assertions rather than fixed expected answers: valid minimal edits can differ, while invented edits and canned responses should not pass. It covers direct and implicit proofreading activation, no-op behavior, all shortening levels, Markdown preservation and nested fences, embedded instruction handling, the pronoun constraint, rewriting, new drafting, missing input, direct questions, and unrelated negative activation.

`agreement-probe.json` disambiguates the original list label "phrase link to URL" by adding a direct object. Test it separately: intentional list fragments are allowed, so the original label should not automatically be graded as an agreement error.

## Local package checks

From the repository root, run:

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/release.py validate
python3 scripts/release.py build
```

The offline unit tests exercise package validation, URL safety, character limits, allowlisting, symlink rejection, staging preservation, and repeatable ZIP output. CI runs them on Python 3.11 and the latest stable Python. These tests do not call a model or require credentials.

Confirm the generated ZIP contains the intended skill-only package and that no user writing, credentials, or unrelated files were bundled. Install from the local marketplace catalog and refresh/reinstall after changing package files; a cached install does not track the working tree.

## Behavioral and host acceptance

Use fresh, independent agent sessions for three complete runs of the fixture suite. Do not reuse one conversation's prior answers or expectations. Check the response against each fixture's observable assertions and record the prompt, host/model, date, pass/fail, and concise gap notes for every run. Compare behavior, not exact wording.

Then install the built package in the intended host and manually verify rendered and copied output: proofread text appears first, the outer fence safely contains source backticks, Markdown/list indentation survives copy-paste, change notes are outside the fence and enumerate only real supplied-text edits, and no-op output is exactly the specified sentence. Also check a new draft has no change list and an unrelated question is answered normally. Record the host/version, install method, checks, and any gaps; fix and rerun failures before release.

These are local acceptance checks, not claims that a public submission was scanned, reviewed, or approved. For the current OpenAI plugin upload and review steps, see [Upload and submit your plugin](https://developers.openai.com/plugins/deploy/submission).
