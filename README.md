# English Proofreader Pro

A skills-only plugin for careful American English proofreading, concise rewrites, and new drafts. It packages instructions only: there is no hosted service, API, MCP server, or runtime backend. The source and icon are available under the [MIT License](LICENSE).

The skill preserves the writer's voice and literal formatting, treats instructions inside submitted text as inert, makes minimal edits by default, and reports actual changes to supplied text. It retains gendered singular pronouns and uses they/them/their for plural references only. General questions are answered directly rather than automatically proofread. See the [privacy notice](PRIVACY.md) and [behavioral test results](tests/RESULTS.md) for scope and limitations.

The host's model and reasoning settings affect these guarantees. The current source passes three complete independent simulations on `gpt-6.1-sol` at high reasoning effort; Luna still has documented failures. This package cannot select or enforce a host model. Validate the actual model and installed package in your intended host before relying on acceptance results from another profile.

The repository is public; this does not mean the plugin is approved or listed in OpenAI's public directory. Private host testing has been performed, but account-specific installation and conversation links are not public installation instructions.

Use a starter prompt, **Try in chat**, or an explicit `@English Proofreader Pro` mention to invoke it. Explicit invocation is the verified route for starting a new drafting task; do not assume the host's ordinary writing behavior always uses this skill.

## Build and install

You need Git and a supported Python 3.11 or newer. No Python packages, API keys, or publisher account are required to build the archive.

```sh
git clone https://github.com/altmn/english-proofreader-pro.git
cd english-proofreader-pro
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/release.py validate
python3 scripts/release.py build
```

The build prints the path to `dist/english-proofreader-pro-<version>.zip` and creates a local staging copy. Upload the ZIP using your compatible host's personal plugin import flow, if available. This creates your own installation, not a public directory listing. See [OpenAI's package documentation](https://developers.openai.com/plugins/build/plugins).

For local Codex testing, install the Codex CLI, then run these commands from the repository root after building:

```sh
codex plugin marketplace add "$PWD"
codex plugin add english-proofreader-pro@english-proofreader-pro-dev
```

The catalog points to `dist/local-plugin/`, including a generated legacy manifest for older clients. Root `plugin.json` stays canonical. Marketplace installs are cached copies: rebuild and reinstall after changing source. See [architecture](docs/architecture.md) for package contents.

If an older CLI reports an unsupported reasoning setting, use a current supported CLI or override that invocation with a supported value, for example `codex -c 'model_reasoning_effort="high"' plugin marketplace add "$PWD"`. Do not edit generated files or the host's plugin cache.

## Contribute and get help

The default branch is `master`. Changes go through feature branches and pull requests. Contributions to instructions, synthetic test cases, packaging, and documentation are welcome; start with [CONTRIBUTING.md](CONTRIBUTING.md).

- [Support](SUPPORT.md) and [issue tracker](https://github.com/altmn/english-proofreader-pro/issues): use synthetic examples, not private writing.
- [Security policy](SECURITY.md): report vulnerabilities privately.
- [Code of conduct](CODE_OF_CONDUCT.md): expectations for participation.
- [Testing](tests/README.md): automated package checks and manual host acceptance.
- [How to publish a release](docs/releasing.md): versioning, verification, and distribution.
- [ChatGPT submission preparation](docs/chatgpt-submission.md): listing, policy links, metadata, and remaining portal steps.
- [Open-source preparation and references](docs/open-source-readiness.md): research and repository safeguards.

## OpenAI directory publication

Open-sourcing this repository and publishing a plugin listing are separate processes. The manifest links the [privacy notice](PRIVACY.md), [usage terms](TERMS.md), and public support path. Publication metadata uses Alex Allen's individual identity, declares no publisher commerce, and removes geographic restrictions (subject to OpenAI's availability). A verified publishing identity, skill scans, review, approval, and publication must still be completed before claiming a public listing. Follow the [preparation checklist](docs/chatgpt-submission.md) and [OpenAI's submission instructions](https://developers.openai.com/plugins/deploy/submission). Skills-only packages do not need a publisher-hosted MCP service or API credentials.

No public directory approval or listing is claimed by this repository.

## License and author

English Proofreader Pro is maintained by [Alex Allen (@altmn)](https://github.com/altmn). See [LICENSE](LICENSE) and [asset and document notices](NOTICE.md). This independent project is not an official OpenAI product.
