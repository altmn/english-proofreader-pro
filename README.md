<p align="center"><img src="assets/icon.webp" width="72" height="72" alt=""></p>

# English Proofreader Pro

Polish emails, documents, and everyday messages in American English while keeping your voice. Correct a draft, make it shorter, or write something new.

[Try it](#try-it) · [Get started](#get-started) · [Get help](#get-help) · [Update or remove](#update-or-remove) · [Technical details](#technical-details)

```diff
- The reports is ready.
+ The reports are ready.
```

*An illustrative edit using made-up text. Edits to your text come with a list of what changed; already-correct text is left alone.*

## Try it

Once installed, select the skill for **each message** you want it to handle, including follow-up edits.

| Where you are writing | How to select it |
| --- | --- |
| ChatGPT in your browser, or the **ChatGPT tab** in the desktop app | Type `@` and choose the available **EnglishProofreaderPro** plugin or **ProofreaderPro** skill entry. |
| The **Codex tab**, Codex app, or Codex CLI | Include `$proofreader-pro`, or choose **ProofreaderPro** in the skill picker (`/skills` in the CLI). |

Choose the matching menu entry rather than just typing its name. If it does not appear, start with [setup help](#get-started). The new picker labels still need installed-host verification; see [where it works](#where-it-works).

**In ChatGPT:** select the entry through `@`, then paste:

```text
Proofread this email in American English. Keep my tone and formatting,
make only necessary corrections, and show what changed.

Text:
Hi Morgan,

The reports is ready for your review. Please let me know if you have any
questions before Friday.

Thanks,
Alex
```

**In Codex:** use `$proofreader-pro` followed by the same request.

<details>
<summary>More prompts: shorten a message or write a new draft</summary>

Select the skill again for each request. In Codex, add `$proofreader-pro` at the beginning.

```text
Make this message shorter and easier to read while keeping the meaning
and a friendly tone.

Text:
I am writing to let you know that we have now finished reviewing the
proposal, and we would like to arrange a time to discuss the next steps.
```

```text
Write a friendly, concise email asking a colleague for an update on a
proposal. We expected it yesterday and need it before tomorrow's meeting.
```

</details>

<a id="build-and-install"></a>

## Get started

Ask an AI assistant to help with setup, or follow the [installation guide](docs/getting-started.md) yourself. No terminal knowledge is needed to ask for help.

**Ask ChatGPT to guide you — paste into a chat at [chatgpt.com](https://chatgpt.com/):**

```text
I want to use English Proofreader Pro:
https://github.com/altmn/english-proofreader-pro

I'm using ChatGPT in my browser and would like setup help without a
terminal. Read the project's current instructions and OpenAI's guidance.
Help me check which supported installation route my account offers, then
guide me one step at a time. If I need the desktop app or an administrator,
explain the next step. Finish by helping me select it and try a short email.
```

**Ask a coding agent to set it up — paste into Codex or another agent with local tools:**

```text
Help me install English Proofreader Pro for this AI tool:
https://github.com/altmn/english-proofreader-pro

Read its current installation instructions, check what is already installed,
and use the supported route for this tool. Ask which installation scope I
want if needed. Preserve existing personal changes, verify the skill appears
in a fresh session, and give me a short first-use example.
```

**Current availability:** this project is open source and has a [published plugin ZIP and checksum](https://github.com/altmn/english-proofreader-pro/releases/latest), but does not claim an approved OpenAI directory listing. A browser chat can guide setup; it cannot create an unavailable import option. Use a route your account offers, or the documented [local Codex route](docs/getting-started.md#install-in-codex-from-source). See the [manual steps](docs/getting-started.md) for package choices.

## Get help

If the skill is missing, check installation and the picker first. If a follow-up is handled unexpectedly, select the skill again for that message. For other problems, ask your assistant:

```text
Help me troubleshoot English Proofreader Pro:
https://github.com/altmn/english-proofreader-pro

I'm using [ChatGPT web / the ChatGPT tab in the desktop app / Codex].
I expected [result], but got [actual result or short error].
Help me check installation, selection for this message, and whether the task
works in my environment. Ask only for the details needed for the next step,
and use a short made-up example to check the result.
```

[Get support](SUPPORT.md) or [report a problem](https://github.com/altmn/english-proofreader-pro/issues/new/choose) with a small synthetic example. Keep private writing out of public reports. Report vulnerabilities through the [security policy](SECURITY.md).

<a id="disable-or-remove"></a>

## Update or remove

**Ask the AI tool where you use the skill:**

```text
Help me check whether English Proofreader Pro is up to date:
https://github.com/altmn/english-proofreader-pro

I use it in [ChatGPT web / ChatGPT desktop / Codex]. Help me find the installed
version, compare it with the latest published release, and follow the update
process for that installation. Preserve personal changes and help me select
the skill and try a short example afterward.
```

```text
Help me temporarily disable or uninstall English Proofreader Pro from
[the AI tool where I use it]. Identify my installation method, follow the
project's removal instructions, keep my writing and unrelated settings,
and help me confirm the result in a new chat or session.
```

Prefer direct steps? See [updating, disabling, and uninstalling](docs/getting-started.md#update-disable-or-remove).

## Where it works

- **ChatGPT:** use a supported plugin installation available to your account. Select through `@` in the browser or ChatGPT tab; public directory approval is not claimed. Current picker labels and exact-release behavior still need intended-host acceptance.
- **Codex:** the source checkout provides a local development marketplace. Select through `$proofreader-pro` or the skill picker; installation and selection are separate steps.
- **Counts and shortening targets:** verified counts and length budgets need a host that can execute the bundled counting tool. Without a successful measurement, the skill reports that limitation. Ordinary proofreading should not be mistaken for a verified count.

For routine proofreading, start with the latest Instant model available in ChatGPT at its normal setting. See [host compatibility](docs/host-compatibility.md) for model choice, counting requirements, and verification limits. [Test results](tests/RESULTS.md) and [known issues](KNOWN_ISSUES.md) retain observed failures and pending acceptance; source-bound simulations do not establish universal host behavior.

## Technical details

The plugin contains editing instructions and an offline Python counting helper. The host supplies the model and execution tools; there is no publisher-hosted service or API. Manual builds use Git and Python 3.11+, without third-party Python packages. No publisher account or API key is needed to build.

| I want to… | Read this |
| --- | --- |
| Download, build, or install | [Getting started](docs/getting-started.md) |
| Understand models, selection, or counting tools | [Host compatibility](docs/host-compatibility.md) |
| Understand behavior and package contents | [Architecture](docs/architecture.md) |
| Inspect checks and their limits | [Testing](tests/README.md) · [Results](tests/RESULTS.md) · [Known issues](KNOWN_ISSUES.md) |
| Understand data handling | [Privacy](PRIVACY.md) · [Terms](TERMS.md) |

<a id="contribute-and-get-help"></a>

## Contribute

Improvements to documentation, synthetic examples, packaging, and tests are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md); changes use feature branches and pull requests against `master`.

<a id="openai-directory-publication"></a>

Maintainers can find [release instructions](docs/releasing.md), [directory submission preparation](docs/chatgpt-submission.md), [open-source readiness](docs/open-source-readiness.md), and the [presentation guide](docs/presentation.md). OpenAI submission, review, and directory publication remain separate steps.

<a id="license-and-author"></a>

Maintained by [Alex Allen (@altmn)](https://github.com/altmn). [MIT license](LICENSE) · [Notices](NOTICE.md) · [Code of conduct](CODE_OF_CONDUCT.md). This independent project is not an official OpenAI product.
