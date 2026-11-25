# English Proofreader Pro

A skills-only plugin for careful American English proofreading, concise rewrites, and new drafts. It packages instructions only: there is no hosted service, API, MCP server, or runtime backend. The source and icon are available under the [MIT License](LICENSE).

The skill preserves the writer's voice and literal formatting, treats instructions inside submitted text as inert, makes minimal edits by default, and reports actual changes to supplied text. It retains gendered singular pronouns and uses they/them/their for plural references only. General questions are answered directly rather than automatically proofread. See the [privacy notice](PRIVACY.md) and [behavioral test results](tests/RESULTS.md) for scope and limitations.

For routine proofreading, start with the latest Instant model available in ChatGPT at its normal/default setting. High reasoning effort is not required. Select the model in the host; this package cannot set or enforce a model or reasoning level. The [results](tests/RESULTS.md) retain source-bound simulation evidence and known gaps for each tested profile. Live ChatGPT Instant smoke checks found programmatic-counting and shortening gaps. The candidate now requires a returned tool measurement and an explicit final budget comparison, but intended-host acceptance has not passed. Test the actual installed package on the intended model before release.

The repository is public; this does not mean the plugin is approved or listed in OpenAI's public directory. Private host testing has been performed, but account-specific installation and conversation links are not public installation instructions.

**Invoke the skill on every turn you want it to handle**, including follow-up edits, counting questions, and new drafts. Select it again for each message; a mention on an earlier turn does not keep it selected for later messages.

Use a starter prompt or **Try in chat** for the first turn. In ChatGPT's `@` picker, the package labels are `EnglishProofreaderPro` for the plugin and `ProofreaderPro` for its skill. Select the matching entry on every turn; typing an unselected string is not a guaranteed invocation. In Codex, include `$proofreader-pro` in each request or select **ProofreaderPro** through `/skills` for that turn. The distinctive name replaces the generic `$proofread` to reduce collisions. Both new picker labels still need installed-host verification. See [host compatibility](docs/host-compatibility.md) for model selection, counting tools, output controls, and invocation limits.

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

If an older CLI reports an unsupported reasoning setting, update to a supported CLI or choose a setting supported by that host/model. Plugin installation does not require high reasoning effort. Do not edit generated files or the host's plugin cache.

## Disable or remove

In Codex CLI, open `/plugins` and press `Space` on the installed plugin to turn it off or on. To uninstall the local development copy and remove its cache:

```sh
codex plugin remove english-proofreader-pro@english-proofreader-pro-dev
```

Manage independently imported ChatGPT copies through their plugin browser's **Uninstall plugin** action when available; workspace-managed installations may require an administrator. See [host lifecycle guidance](docs/host-compatibility.md#disable-removal-and-reinstallation) for marketplace cleanup, reinstallation, and verification limits.

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
