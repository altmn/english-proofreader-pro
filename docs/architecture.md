# Architecture

English Proofreader Pro is a skills-only plugin. It has no hosted service, API, MCP server, runtime backend, or third-party Python dependency. The host reads the plugin manifest and skill instructions and supplies the model/runtime that performs the requested writing task.

## Repository roles

- `plugin.json` is the canonical plugin identity, version, UI metadata, and skill-only publication description.
- `skills/english-proofreader-pro/SKILL.md` defines proofreading, editing, rewriting, and drafting behavior. Keep it concise; the validator uses a 1 MiB UTF-8 compatibility ceiling, not the former 8,000-character project cap.
- `skills/english-proofreader-pro/agents/openai.yaml` contains skill UI metadata. The canonical skill name is `english-proofreader-pro`; the picker label is `ProofreaderPro`. The plugin label is `EnglishProofreaderPro`.
- `assets/icon.webp`, `LICENSE`, and `PRIVACY.md` are runtime package assets and notices.
- `scripts/release.py` validates the runtime inputs and creates the distributable ZIP; it also stages a local compatibility copy for development.
- `tests/` contains synthetic behavior cases and deterministic packaging tests. Model/host acceptance checks are separate and manual.
- `scripts/evaluate.py` snapshots the skill, manifest, selected fixtures, and runner context, then binds responses and manual assertion verdicts to those inputs. Exclusive creation protects existing evidence from concurrent writers. New records include structured model effort and run identity; suite validation checks the declared profile, repeated inputs, minimum run count, and obvious duplicate captures. Schema-1 historical records remain individually verifiable. These checks do not attest independent execution or grade semantic correctness.

## Behavior boundaries

The skill defaults to minimal edits and preservation of meaning, voice, pronouns, and formatting. Text supplied for processing—including quoted or fenced instructions—is source material, not authority to change the task. For supplied text, the skill reports actual changes; drafting from scratch does not use a Changes list. Literal Markdown and nested fences must remain safe to copy. These instructions are the product's core behavior and should not be changed incidentally during packaging or documentation work.

The skill describes desired behavior; it cannot guarantee identical output across models, hosts, or contexts. The test suite checks local deterministic properties and packaging, not universal model quality.

The editing workflow orders five checks: separate directions from the complete source, calculate shortening budgets or inventory drafting facts, compose text, verify counts and every edit, then construct a safe copyable block. All counting requires programmatic tools, including internal shortening checks. Source may be passed to those tools only as inert data, never executed or used to authorize browsing or app actions. Changes quotations use display-only Markdown escaping inside their outer bold markers so literal source syntax remains visible; those escapes never belong in the copyable text or edit ledger. The final check includes quoted spans in Changes explanations. These are instructions executed by the host model; the package does not supply a runtime tool sandbox or force code-block controls. Historical simulations and pending acceptance are recorded in [validation evidence](../tests/RESULTS.md).

Fenced/code-example payloads remain literal unless the user explicitly asks for edits inside them. Preserve their fence delimiters and other formatting in either case. Ordinary text editing, source-command isolation, pronouns, and Changes-list requirements still apply. See [host compatibility](host-compatibility.md) for model recommendations and capability boundaries.

## Distribution

Run `python3 scripts/release.py validate` and `python3 scripts/release.py build`. The resulting ZIP is an allowlisted six-file runtime package: `plugin.json`, the skill and its UI metadata, the icon, `LICENSE`, and `PRIVACY.md`. Repository history, tests, screenshots, development catalog, and scripts are not part of that ZIP. `dist/local-plugin/` is a development staging copy, not the public release artifact.

The validator rejects duplicate JSON keys, invalid semantic versions, and empty skill bodies. The file ceiling is measured in actual UTF-8 bytes, including physical CRLF bytes; metadata retains its character limits. Metadata uses a deliberately narrow YAML subset: unique keys at fixed indentation levels with string scalars; plain strings, JSON-compatible double-quoted strings, and single-quoted strings with doubled apostrophes. Raw YAML source must use the printable character range, including comments and ignored lines; supported quoted escape sequences are parsed separately. Collections, multiline scalars, implicit typed values, and undeclared fields are rejected. Quote values that resemble YAML booleans or numbers.

Icon validation checks the WebP container, chunk bounds, frame headers, dimensions, and a 5 MiB size limit using the standard library. CI additionally decodes the image with libwebp's `dwebp`; compressed pixel decoding is separate from the offline structural checks. The decoder is a CI asset-verification dependency, not a dependency of the plugin or local archive builder.

Build prepares and verifies temporary outputs before publication. The old ZIP stays at its final path until one atomic replacement; a failed promotion rolls back local staging or reports the preserved backup path if restoration fails. Run one build at a time. ZIP replacement and staging replacement are separate filesystem operations, so an interrupted process still requires checking outputs before distribution.

Preflight recognizes only the two known runtime files under the retired `skills/proofread/` staging path so a previous generated build can be replaced. Unknown files, symlinks, and non-regular entries there still block replacement. Newly prepared staging trees and ZIPs use only the current six-file allowlist; the retired skill is never bundled as an alias.
