# Install and manage English Proofreader Pro

For an AI-guided route, use the [setup prompts](../README.md#get-started). This guide contains the direct steps. Choose your AI tool before choosing a package or command.

## Choose a route

| Route | What to use | What to expect |
| --- | --- | --- |
| ChatGPT with a supported personal/workspace plugin installation | The installable plugin ZIP from [Releases](https://github.com/altmn/english-proofreader-pro/releases/latest), where the host offers that import route | Account/host-dependent; no public directory listing or universal browser ZIP importer is claimed. |
| Codex with local plugin support | Build and register the local marketplace below | A cached local development installation; keep the checkout for updates. |
| Inspect or develop the project | Clone the repository | Source, tests, and docs; the automatic source ZIP is not the installable plugin ZIP. |

The release includes a plugin ZIP and detached SHA-256 checksum. Check package/version and checksum before import. Source changes after a release are not automatically included in it. An ordinary ChatGPT chat can explain the route; pasting a prompt does not install a plugin. Do not use the publisher submission portal as a personal installation workflow. See [OpenAI's plugin guidance](https://learn.chatgpt.com/docs/plugins).

## Install in Codex from source

You need Git, Python 3.11+, and a current Codex CLI with `codex plugin` support. No third-party Python packages or API keys are needed to build.

```sh
git clone https://github.com/altmn/english-proofreader-pro.git
cd english-proofreader-pro
python3 -m unittest discover -s tests -p 'test_*.py'
python3 scripts/release.py validate
python3 scripts/release.py build
codex plugin marketplace add "$PWD"
codex plugin add english-proofreader-pro@english-proofreader-pro-dev
```

The build prints `dist/english-proofreader-pro-<version>.zip` and stages `dist/local-plugin/`. The marketplace reads that staging copy, including its generated compatibility manifest. Root `plugin.json` is canonical; do not hand-edit staging or host caches. Keep the clone for updates. These commands register the development marketplace with your Codex installation; choose other project/user scope only through the host's supported mechanism.

If the CLI rejects a reasoning setting, choose a supported setting or update the CLI. High reasoning effort is not required to install or proofread.

## Verify first use

1. Start a fresh chat/session if discovery has not refreshed.
2. In ChatGPT, type `@` and select the available **EnglishProofreaderPro** plugin or **ProofreaderPro** skill. In Codex, use `$proofreader-pro` or its skill picker (`/skills` in the CLI).
3. Try the [email example](../README.md#try-it). Expect revised text and actual changes for edited supplied text; already-correct text is left alone. New drafts do not receive fictional correction lists.
4. Select the skill again for every message you want it to handle, including follow-ups.

The new picker labels require installed-host verification. Discovery does not establish successful execution of a release. See [compatibility](host-compatibility.md) and [results](../tests/RESULTS.md).

## Update, disable, or remove

### Update

Compare your version with [Releases](https://github.com/altmn/english-proofreader-pro/releases). For source-based Codex copies, review the desired revision, preserve local changes, rerun validation/build, and refresh through supported plugin commands. Cached installs do not automatically use edited source. Verify in a fresh session. For independently imported ChatGPT copies, use that host's supported controls.

### Disable temporarily

In Codex CLI, open `/plugins`, choose the entry, and press `Space` to toggle it. This is a plugin-browser action; a feature-flag option is not a plugin-disable command.

### Uninstall the documented local copy

```sh
codex plugin remove english-proofreader-pro@english-proofreader-pro-dev
```

If retiring the marketplace too, remove its registration after its plugins:

```sh
codex plugin marketplace remove english-proofreader-pro-dev
```

Keep registration if you plan to reinstall. Do not manually delete shared caches. This covers the local copy, not independently imported installations.

In ChatGPT, use **Uninstall plugin** in the supported plugin browser when available. Managed installations may require an administrator. Verify availability in a new session; removal does not erase instructions loaded into an existing conversation.

See [detailed lifecycle guidance](host-compatibility.md#disable-removal-and-reinstallation) for verification limits and [maintenance prompts](../README.md#update-or-remove) for assistance.
