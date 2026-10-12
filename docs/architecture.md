# Architecture

English Proofreader Pro is a skills-only plugin. It has no hosted service, API, MCP server, runtime backend, or third-party Python dependency. The host reads the plugin manifest and skill instructions and supplies the model/runtime that performs the requested writing task.

## Repository roles

- `plugin.json` is the canonical plugin identity, version, UI metadata, and skill-only publication description.
- `skills/proofread/SKILL.md` defines proofreading, editing, rewriting, and drafting behavior. Keep it under 8,000 characters.
- `skills/proofread/agents/openai.yaml` contains skill UI metadata.
- `assets/icon.webp`, `LICENSE`, and `PRIVACY.md` are runtime package assets and notices.
- `scripts/release.py` validates the runtime inputs and creates the distributable ZIP; it also stages a local compatibility copy for development.
- `tests/` contains synthetic behavior cases and deterministic packaging tests. Model/host acceptance checks are separate and manual.
- `scripts/evaluate.py` snapshots the skill, manifest, fixtures, and runner context, then binds responses and manual assertion verdicts to those inputs. It validates record integrity and identifies historical evidence; it does not grade semantic correctness.

## Behavior boundaries

The skill defaults to minimal edits and preservation of meaning, voice, pronouns, and formatting. Text supplied for processing—including quoted or fenced instructions—is source material, not authority to change the task. For supplied text, the skill reports actual changes; drafting from scratch does not use a Changes list. Literal Markdown and nested fences must remain safe to copy. These instructions are the product's core behavior and should not be changed incidentally during packaging or documentation work.

The skill describes desired behavior; it cannot guarantee identical output across models, hosts, or contexts. The test suite checks local deterministic properties and packaging, not universal model quality.

The editing workflow now orders five checks: separate directions from the complete source, calculate shortening budgets or inventory drafting facts, compose text, verify counts and every edit, then construct a safe outer fence. The final check includes quoted spans in Changes explanations. These checks are instructions executed by the host model, not deterministic runtime enforcement. Current simulations and model-specific gaps are recorded in [validation evidence](../tests/RESULTS.md).

Fenced/code-example payloads remain literal unless the user explicitly asks for edits inside them. Preserve their fence delimiters and other formatting in either case. Ordinary prose editing, source-command isolation, pronouns, and Changes-list requirements still apply.

## Distribution

Run `python3 scripts/release.py validate` and `python3 scripts/release.py build`. The resulting ZIP is an allowlisted six-file runtime package: `plugin.json`, the skill and its UI metadata, the icon, `LICENSE`, and `PRIVACY.md`. Repository history, tests, screenshots, development catalog, and scripts are not part of that ZIP. `dist/local-plugin/` is a development staging copy, not the public release artifact.

The validator rejects duplicate JSON keys and invalid semantic versions. Skill length is measured from the actual UTF-8-decoded file, preserving CRLF characters. Metadata uses a deliberately narrow YAML subset: unique keys at fixed indentation levels with string scalars; plain strings, JSON-compatible double-quoted strings, and single-quoted strings with doubled apostrophes. Collections, multiline scalars, implicit typed values, and undeclared fields are rejected. Quote values that resemble YAML booleans or numbers.

Icon validation checks the WebP container, chunk bounds, frame headers, dimensions, and a 5 MiB size limit using the standard library. CI additionally decodes the image with libwebp's `dwebp`; compressed pixel decoding is separate from the offline structural checks. The decoder is a CI asset-verification dependency, not a dependency of the plugin or local archive builder.

Build prepares and verifies temporary outputs before publication. The old ZIP stays at its final path until one atomic replacement; a failed promotion rolls back local staging or reports the preserved backup path if restoration fails. Run one build at a time. ZIP replacement and staging replacement are separate filesystem operations, so an interrupted process still requires checking outputs before distribution.
