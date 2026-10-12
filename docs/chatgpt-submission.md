# ChatGPT directory submission handoff

This guide prepares the existing skills-only plugin for possible OpenAI public-directory submission. It does not upload a ZIP, create a portal draft, submit for review, or publish. Open-source repository publication and ChatGPT directory publication are separate.

## Listing draft

Use the supported values already in `plugin.json` as the English listing draft:

| Field | Draft |
| --- | --- |
| Name | English Proofreader Pro |
| Subtitle | Careful English proofreading |
| Description | Proofread, edit, rewrite, or draft American English prose while preserving meaning and voice. Finished text appears in a copyable plain-text code block. Edits to supplied text are followed by a complete Changes list. Preserve literal Markdown, paragraph breaks, and list markers. Supports requested shortening levels and editing AI prompts without executing their embedded instructions. By default, make only necessary corrections and retain gendered singular pronouns instead of replacing them with singular they; use they, them, and their for plural references only. Already-correct text receives a no-adjustments confirmation. Follow the user's separate editing directions. |
| Category | Productivity |
| Intended publisher | Alex Allen, individual; verify this exact identity in the OpenAI Platform before submission |

The three starter prompts are:

1. `Proofread the following text, preserving its formatting.`
2. `Proofread the following text and trim the fat.`
3. `Draft a short professional email asking for a status update.`

Keep English in the base listing fields. Do not invent translations or add an `en-US` translation entry. The confirmed publication choice is all countries available in the portal, represented by `publication.countries: []`; this removes the package's country allowlist, but does not claim availability where OpenAI does not offer it. The manifest includes `review.commerce: false` and the confirmed no-payments explanation. The maintainer chose the existing icon without optional dark assets or custom colors.

## Public URLs and package checks

The listing metadata uses absolute HTTPS links that must open without a private login, identify this plugin/publisher, and serve the field's purpose. Check both reachability and page content on the reviewed `master` revision before upload. The configured URLs are:

| Listing field | URL |
| --- | --- |
| Website | `https://github.com/altmn/english-proofreader-pro` |
| Support | `https://github.com/altmn/english-proofreader-pro/issues` |
| Privacy policy | `https://github.com/altmn/english-proofreader-pro/blob/master/PRIVACY.md` |
| Terms of service | `https://github.com/altmn/english-proofreader-pro/blob/master/TERMS.md` |

These policy URLs point to `master`, not a development branch. Do not call them complete merely because files exist in a working tree or an open pull request: merge through the protected branch, then re-open the published pages and check their content. The privacy page must describe the package's actual data practices; the terms page must be reviewed by the publisher before the portal's attestations. The listing must not link to the private installation or private test conversations.

After merge, make a clean checkout of the reviewed `master`, run the repository's tests, `python3 scripts/release.py validate`, and `python3 scripts/release.py build`. Inspect the exact ZIP, not just the worktree: confirm the manifest contains the final English listing, all four checked URLs, commerce and country choices, release notes, and no invented translations; check that it contains exactly the six intended runtime files and no tests, private text, credentials, or unrelated files. Keep the 7,985-character skill and existing icon unchanged. The current OpenAI submission-error reference accepts WebP icons; verify that the referenced WebP is square, readable, within size limits, and included in the ZIP.

## Readiness snapshot and evidence

Recheck CI on the exact reviewed commit after any edits; the repository currently has 24 offline tests, not 24 live ChatGPT behavior tests. `tests/cases.json` describes synthetic behavior checks, and `tests/RESULTS.md` records prior observations and limitations; those records do not mean every fixture passed a live ChatGPT run. Existing private installation and live-host observations concern an earlier package artifact. The updated metadata artifact has not been re-imported into ChatGPT, so do not describe it as portal-validated or freshly re-tested. The skill remains below its 8,000-character limit.

Because this is skills-only, no MCP server connection, MCP review cases, recorded demo, or reviewer credentials are needed. Local deterministic packaging tests and a manual host check are useful, but they are not substitutes for the portal's required skill scan. Wait for scans on the exact uploaded draft to finish successfully before asking the authorized developer to submit it for review.

## Remaining handoff checklist

- [ ] Confirm the reviewed change is merged to protected `master` through its required signed, linear-history path, and the latest CI run passes.
- [ ] On merged `master`, open the website, support, privacy, and terms URLs in a signed-out browser. Confirm each page is public, current, identifies the plugin/publisher, and provides the promised content or contact path. Correct metadata through a pull request if needed.
- [ ] Build from a clean checkout of that merged commit. Run tests, `validate`, and `build`; inspect the ZIP inventory, metadata, skill size, icon, and archive integrity.
- [ ] In OpenAI Platform, the individual developer Alex Allen must complete identity verification and select that verified identity. The portal has not yet confirmed it.
- [ ] Upload the verified ZIP as a draft only when an authorized developer is ready. Inspect the imported listing and review/publication metadata, then wait for the exact draft's skill/security scan findings and resolve any required findings with a corrected ZIP.
- [ ] The authorized developer—not this preparation guide or an automated process—must review and affirm the current legal and policy attestations in the portal. Do not attest on anyone else's behalf.
- [ ] Submit for review only after the public pages, identity, package checks, scans, and attestations are complete. Approval is a later state; publication is a separate action after approval. A submission does not guarantee approval.
- [ ] Share a public directory link only after publication has actually completed and the listing URL is visible.

## Official references

- [Upload and submit your plugin](https://developers.openai.com/plugins/deploy/submission) — draft upload, scans, review, attestations, and publication states.
- [Plugin guidelines](https://developers.openai.com/plugins/plugin-guidelines) — listing, privacy, verification, and policy requirements.
- [Plugin submission errors](https://developers.openai.com/plugins/deploy/submission-errors) — current package/listing limits and supported image formats, including WebP.
