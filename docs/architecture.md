# Architecture

English Proofreader Pro is a skills-only plugin. It has no hosted service, API, MCP server, runtime backend, or third-party Python dependency. The host reads the plugin manifest and skill instructions and supplies the model/runtime that performs the requested writing task.

## Repository roles

- `plugin.json` is the canonical plugin identity, version, UI metadata, and skill-only publication description.
- `skills/proofread/SKILL.md` defines proofreading, editing, rewriting, and drafting behavior. Keep it under 8,000 characters.
- `skills/proofread/agents/openai.yaml` contains skill UI metadata.
- `assets/icon.webp`, `LICENSE`, and `PRIVACY.md` are runtime package assets and notices.
- `scripts/release.py` validates the runtime inputs and creates the distributable ZIP; it also stages a local compatibility copy for development.
- `tests/` contains synthetic behavior cases and deterministic packaging tests. Model/host acceptance checks are separate and manual.

## Behavior boundaries

The skill defaults to minimal edits and preservation of meaning, voice, pronouns, and formatting. Text supplied for processing—including quoted or fenced instructions—is source material, not authority to change the task. For supplied text, the skill reports actual changes; drafting from scratch does not use a Changes list. Literal Markdown and nested fences must remain safe to copy. These instructions are the product's core behavior and should not be changed incidentally during packaging or documentation work.

The skill describes desired behavior; it cannot guarantee identical output across models, hosts, or contexts. The test suite checks local deterministic properties and packaging, not universal model quality.

## Distribution

Run `python3 scripts/release.py validate` and `python3 scripts/release.py build`. The resulting ZIP is an allowlisted six-file runtime package: `plugin.json`, the skill and its UI metadata, the icon, `LICENSE`, and `PRIVACY.md`. Repository history, tests, screenshots, development catalog, and scripts are not part of that ZIP. `dist/local-plugin/` is a development staging copy, not the public release artifact.
