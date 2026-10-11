# English Proofreader Pro

A skills-only plugin for careful American English proofreading, concise rewrites, and new drafts. It packages instructions only: there is no hosted service, API, MCP server, or runtime backend.

The skill is adapted from the author's English Proofreader instructions. It preserves the author's voice and formatting, treats instructions inside submitted text as inert, applies the requested editing level, and reports every actual change. General questions—including questions about editing—are answered directly rather than automatically proofread. See [`PRIVACY.md`](PRIVACY.md) for the package's data-handling scope.

The plugin is installed locally and in the author's Personal ChatGPT area for private testing: [open the private plugin](https://chatgpt.com/plugins/Plugin_6ab6023d0ed88191ae329f0aa15bf7a1). This account-scoped installation is separate from public directory publication.

Use a starter prompt, **Try in chat**, or an explicit `@English Proofreader Pro` mention to invoke it. Explicit invocation is the verified route for starting a new drafting task; do not assume the host's ordinary writing behavior always uses this skill.

## Local validation and build

From the repository root, run:

```sh
python3 scripts/release.py validate
python3 scripts/release.py build
```

The build creates a distributable ZIP; use the path printed by the script. To test the local marketplace catalog, add the absolute path to this repository, then install the catalog entry:

```sh
codex plugin marketplace add /absolute/path/to/english-proofreader-pro
codex plugin add english-proofreader-pro@english-proofreader-pro-dev
```

The local catalog is `.agents/plugins/marketplace.json` and is named `english-proofreader-pro-dev`; its source points to `./dist/local-plugin`. The build stages a test copy there, including a generated Codex compatibility manifest. This avoids the marketplace-root path bug in older clients while keeping root `plugin.json` canonical. Marketplace installs use a cache copy, not a live link. Rebuild and reinstall after changing files; editing the repository alone does not update the installed copy.

On the development machine, CLI 0.136.0 also cannot parse the existing `ultra` reasoning setting. Add `-c 'model_reasoning_effort="high"'` to the two `codex` commands above when using that CLI. This overrides only those invocations and does not change the saved reasoning preference.

## Public submission

OpenAI supports plugins made from packaged skills without an MCP server. For the current package and submission flow, see [Package your plugin](https://developers.openai.com/plugins/build/plugins), [Build skills](https://developers.openai.com/plugins/build/skills), and [Upload and submit your plugin](https://developers.openai.com/plugins/deploy/submission).

Before public submission, host a clear, published privacy policy that describes the plugin's data practices; the policy must be ready for users to review before installing. This repository's [`PRIVACY.md`](PRIVACY.md) is not yet hosted as a public notice. When the package is ready, upload its ZIP in the OpenAI Platform submission portal (choose **Upload new or existing plugin**), select the verified developer identity, review and resolve skill scan findings, then submit the draft for review. Approval and publication are separate steps: publish only after approval. No public directory submission or publication has been performed. Identity verification, public privacy notice, automated checks, review, and approval remain future steps.

This is a skills-only package. It does not need an MCP service or MCP test credentials, a server walkthrough video, or hosted runtime infrastructure. Do not infer that submission has been approved or that the plugin is listed publicly.

## Evaluation

[`tests/cases.json`](tests/cases.json) contains synthetic cases and observable behavioral requirements, not canned answer strings. See [`tests/README.md`](tests/README.md) for local checks and host acceptance testing, and [`tests/RESULTS.md`](tests/RESULTS.md) for recorded observations and limitations.

## License and author

English Proofreader Pro is by Alex Allen and is distributed under the MIT License; see [`LICENSE`](LICENSE).
