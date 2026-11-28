<p align="center"><img src="assets/icon.webp" width="72" height="72" alt=""></p>

# English Proofreader Pro

Polish an email, a document, or an everyday message in American English while preserving your voice. Refine a draft or write something from scratch.

```diff
- A software issue at a single company can put on hold all US real estate market on hold.
+ A software issue at a single company can put the entire U.S. real estate market on hold.
```

[Try it](#try-it) · [Get started](#get-started) · [Get help](#get-help) · [Update or remove](#update-disable-or-remove) · [Technical details](#technical-details)

---

## Try it

### Invoke in each prompt 
Once installed, select the skill at the beginning of **each message** you want it to handle, including follow-up edits.

### How to invoke
Choose the matching menu entry rather than just typing its name. If it does not appear, start with [setup help](#get-started).
| Where you are writing | How to select it |
| --- | --- |
| ChatGPT in your browser, or the **ChatGPT tab** in the desktop app | Type `@` and choose the available **EnglishProofreaderPro** plugin or **ProofreaderPro** skill entry. |
| The **Codex tab**, Codex app, or Codex CLI | Include `$proofreader-pro`, or choose **ProofreaderPro** in the skill picker (`/skills` in the CLI). |

### Proofreading prompt examples

**In ChatGPT web or desktop app:** select the entry through `@`, type `Proofread:`, then paste the text to proofread. For example:

```text
@EnglishProofreaderPro Proofread:

Hi Morgan,

The paperwork has been signed with no issues. 
Scans are uploaded to the portal. 
Documents have been shipped for a delivery tomorrow.

Please let me know if there are any questions 
before noon tomorrow, as I'm taking the afternoon off.

Thank you and have a great day,
Jennifer
```

**In Codex:** use `$proofreader-pro` to envoke the skill in the beginning of the prompt, type `Proofread:`, then paste the text to proofread. For example:

```text
$proofreader-pro Proofread:

Hi Morgan,

The paperwork has been signed with no issues. 
Scans are uploaded to the portal. 
Documents have been shipped for a delivery tomorrow.

Please let me know if there are any questions 
before noon tomorrow, as I'm taking the afternoon off.

Thank you and have a great day,
Jennifer
```


<details>
<summary>More prompt examples</summary>

An example of a ChatGPT prompt to make the message sound official:
```text
@EnglishProofreaderPro 

Make this message sound more official while keeping the meaning and a friendly tone:

I'm writing to let you know that we have now finished reviewing 
your proposal, and we would like to set up a time 
for an online call to discuss the next steps.
```

An example of a Codex prompt to write an email to a colleague from scratch:
```text
$proofreader-pro 

Write a friendly, concise email asking my colleague Mary for an update on a proposal 
I had sent her two weeks ago. We expected it yesterday and need it before tomorrow's meeting.
```
</details>

---

<a id="build-and-install"></a>

## Get started

Ask your AI assistant to help with setup, or follow the [installation guide](docs/getting-started.md) yourself. No terminal knowledge is needed to ask for help.

**Paste into a chat in ChatGPT or Claude:**

ChatGPT:
```text
Guide me on how to install the English Proofreader Pro skill in my ChatGPT web account: https://github.com/altmn/english-proofreader-pro
```

Claude:
```text
Guide me on how to install the English Proofreader Pro skill in my Claude web account: https://github.com/altmn/english-proofreader-pro
```

**Ask your coding agent to set it up on your machine:**

Codex:
```text
Install the English Proofreader Pro skill for Codex globally: https://github.com/altmn/english-proofreader-pro
```

Claude:
```text
Install the English Proofreader Pro skill for Claude globally: https://github.com/altmn/english-proofreader-pro
```


**Current availability** 

This project is open source and has a [published plugin ZIP and checksum](https://github.com/altmn/english-proofreader-pro/releases/latest). It is not yet an approved OpenAI or Anthropic directory listing. 

A browser chat can guide setup; it cannot create an unavailable import option. Use a route your account offers, or the documented [local Codex route](docs/getting-started.md#install-in-codex-from-source). See the [manual steps](docs/getting-started.md) for package choices.

---

## Get help

If the skill is missing, check installation and the picker first. If a follow-up request is handled unexpectedly, select the skill again for that message. For other problems, ask your AI assistant.

An example of a troubleshooting prompt (replace `[...]` with your information):
```text
Help me troubleshoot English Proofreader Pro (https://github.com/altmn/english-proofreader-pro).

I'm using [ChatGPT web/ChatGPT tab in the desktop app/Codex, or similar Claude options]. 
I expected [result], but got [actual result or short error].
Investigate the issue.
```

### Nothing helps or found a bug
[Get support](SUPPORT.md) or [report a problem](https://github.com/altmn/english-proofreader-pro/issues/new/choose) with a small synthetic example. Remember to keep private writing and information out of public reports. Report vulnerabilities through the [security policy](SECURITY.md).

---

<a id="disable-or-remove"></a>

## Update, disable, or remove

What to update, disable, or remove the skill? Just ask your AI tool.

To update:
```text
Update English Proofreader Pro: https://github.com/altmn/english-proofreader-pro 
```

To disable:
```text
Temporarily disable English Proofreader Pro: https://github.com/altmn/english-proofreader-pro.
```

To uninstall:
```text
Uninstall English Proofreader Pro: https://github.com/altmn/english-proofreader-pro.
```

### Prefer direct steps?

See [updating, disabling, and uninstalling](docs/getting-started.md#update-disable-or-remove).

---

## Where it works

- **ChatGPT/Claude:** use a supported plugin installation available to your account. Select through `@` in the browser or ChatGPT tab.
- **Codex/Claude Code:** the source checkout provides a local development marketplace. Select through `$proofreader-pro` or the skill picker.

### What model to choose

For routine proofreading, start with the latest Instant model available in ChatGPT/Claude at its normal setting. 

See [host compatibility](docs/host-compatibility.md), [test results](tests/RESULTS.md), and [known issues](KNOWN_ISSUES.md) for more.

---

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

---

## Contribute

Improvements to documentation, synthetic examples, packaging, and tests are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md); changes use feature branches and pull requests against `master`.

<a id="openai-directory-publication"></a>

Maintainers can find [release instructions](docs/releasing.md), [directory submission preparation](docs/chatgpt-submission.md), [open-source readiness](docs/open-source-readiness.md), and the [presentation guide](docs/presentation.md).

<a id="license-and-author"></a>

Maintained by [Alex Allen (@altmn)](https://github.com/altmn).

This is an independent project. It is not endorced by OpenAI, Anthropic, or any other AI company.

[MIT license](LICENSE) · [Notices](NOTICE.md) · [Code of conduct](CODE_OF_CONDUCT.md). 
