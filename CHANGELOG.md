# Changelog

## 2.1.0 — 2026-09-14

The previous implementation identified itself as 2.0 in HTTP requests; it had no formal release-version field. This release establishes 2.1.0 in SKILL.md and the CLI.

- Reject duplicate reference indices before verification or writing outputs, preventing silent loss or duplication of results.
- Reject output paths that alias the source, an explicitly reused artifact, or another output, including symlinks and hardlinks.
- Keep failed title queries distinguishable from completed searches with no match. Failed queries leave unresolved references unusable; successful empty searches retain the existing classification policy.
- Do not cache failed title searches as successful empty results. Detect malformed search responses and incomplete PubMed record retrieval.
- Include formatted-only entries in the Markdown detail report.
- Update the verification policy version to 2026-09-14.1 so older evidence is rechecked.
- Add 10 offline regression tests for these boundaries.
- Add the MIT-0 license and exclude Python caches and macOS metadata from publication.
