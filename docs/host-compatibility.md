# Host compatibility

## Skill size

There is no 8,000-character project cap on `SKILL.md`. OpenAI's [skills guide](https://learn.chatgpt.com/docs/build-skills) distinguishes the initial discovery list's fallback 8,000-character budget from the selected skill's full instructions. Keep instructions concise for clarity and context use. The release validator uses a 1 MiB UTF-8 file ceiling as a packaging compatibility safeguard, following the bundled plugin-authoring guidance; this is not a claim of a universal skill-body limit across hosts.

## Model recommendation

For routine proofreading, start with the latest Instant model available in ChatGPT at its normal/default setting. High reasoning effort is not a requirement. Choose the model in [ChatGPT's composer](https://learn.chatgpt.com/docs/web). In Codex, select an available model and supported effort through the model picker or your own [configuration](https://learn.chatgpt.com/docs/config-file/config-basic).

The documented plugin and [skill metadata](https://learn.chatgpt.com/docs/build-skills#optional-metadata) provide no model or reasoning-effort selector. A recommendation in the listing or skill instructions cannot change host settings. OpenAI's API alias [`chat-latest`](https://developers.openai.com/api/docs/models/chat-latest) tracks the latest ChatGPT Instant model, but its API Skills support is unavailable; it is not a documented Codex model-selection shortcut.

Earlier Sol/high simulations are evidence for their exact source/profile, not a default setting or proof of Instant behavior. This revision still needs acceptance in the intended host on the recommended Instant setting. See [validation evidence](../tests/RESULTS.md).

## Invocation and collisions

The stable plugin ID remains `english-proofreader-pro`. Its plugin picker label is `EnglishProofreaderPro`; the bundled skill's picker label is `ProofreaderPro`. ChatGPT's `@` menu can select [plugins](https://learn.chatgpt.com/docs/build-plugins) and [skills](https://learn.chatgpt.com/docs/build-skills). These labels provide the two requested no-space names through those supported metadata fields. They do not register arbitrary aliases or guarantee that an unselected typed `@` string activates the plugin. Verify both entries after installation.

In Codex, use `$proofreader-pro` or choose **ProofreaderPro** through `/skills`. The skill folder, frontmatter name, and starter prompt use the distinctive `proofreader-pro` name. The former `$proofread` and `$english-proofreader-pro` names are not retained as aliases. OpenAI documents that duplicate skill names are not merged and can both appear in selectors. Select the entry from this plugin if another installation uses the same distinctive name; do not rely on name precedence. Cached older installs may still expose an older name until updated through the host's normal workflow.

## Copyable text and wrapping

The skill requests a plain-text code block with the host's Copy code button and soft wrapping when available. ChatGPT/Codex normally render Markdown fences as native code blocks; there is no separate package field that enables their UI controls. A native literal-block facility may be used when the host exposes one; safe Markdown fences are the portable fallback. Soft wrapping must not insert line breaks into the copied text. Copy/clipboard behavior and nested fences require intended-host checks.

## Programmatic counts

Every text-unit count, including internal shortening checks, requires a programmatic tool. The host supplies code execution or another reliable counter; this instructions-only package does not install a tool. Source must be passed as inert data and never executed or interpolated into commands. Use the requested unit and convention; default characters are Unicode code points, not model tokens, UTF-8 bytes, UTF-16 units, or visible grapheme clusters. Without suitable tools, disclose the limitation instead of claiming an exact count or verified shortening percentage.

## Source instructions and host permissions

Text after the source boundary remains data, including URLs, requests addressed to the assistant, and apparent instructions to verify, browse, use an app, or send a message. The skill requires checking the real request outside the source before each tool call. Editing permission permits editing the text; it does not authorize actions described by that text. A separate later user message can revise the task.

These instructions strengthen isolation but do not revoke host tools or guarantee model compliance. [Codex web-search settings](https://learn.chatgpt.com/docs/web-search) and [ChatGPT Work controls](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-cloud-security) belong to the host. Disabling web search alone does not remove browsers, shell networking, or connectors. No package-local permission switch is added. Test synthetic source attacks with actual tool traces; a correct-looking final answer alone does not prove that no URL was visited.
