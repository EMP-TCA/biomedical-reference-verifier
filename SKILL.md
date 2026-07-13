---
name: biomedical-reference-verifier
description: "Verify or normalize biomedical and life-science reference lists, when the task is about AI-caused reference errors. Makes your reference bibliography more reliable and convincing.. 生物医学/生命科学参考文献真实性验证skill，可以对参考文献列表（引文列表）进行多轮核查和错误修复，附带引文格式整理功能，能统一规范化所有引文为AMA、APA、GB/T 7714等格式。"
version: 1.1.3
metadata:
  openclaw:
    requires:
      bins:
        - python3
    envVars:
      - name: NCBI_API_KEY
        required: false
        description: Optional NCBI API key for higher PubMed E-utilities rate limits.
      - name: OPENALEX_API_KEY
        required: false
        description: Optional OpenAlex API key for authenticated metadata lookups.
---

# Biomedical Reference Verifier

Use this skill only for reference-list authenticity checking, AI-caused reference cleanup, and citation-format normalization. Do not use it to judge whether papers are relevant, suitable, or correctly used in the manuscript body unless the user explicitly asks for reference authenticity plus body cleanup.

## Core Rule

Always reduce the task to this sequence:

1. Build or read `biomedical-reference-verifier.records.v1`.
2. Choose the lightest pipeline.
3. Run the script.
4. Report result files and retained process files.
5. Ask before expensive manual recovery or process-file deletion.

Load `references/verification_policy.md` before classifying authenticity errors, changing severe items, or explaining network/query policy.

## Pipeline Choice

- **Format only**: use when the user only asks to convert or unify citation style. Run `--pipeline format-only`. Do not query Crossref/PubMed/OpenAlex.
- **Verify**: use when the user asks whether references are real, fake, wrong, AI-generated, DOI/PMID-mismatched, or metadata-corrupted. Run the default `verify` pipeline.
- **Verify then format**: use when the user asks both to check authenticity and standardize style. Run `verify` with the requested `--citation-style`; the fixed copy is generated after verification.

## Execution Mode

- **Fast** (`--mode fast`): use for quick scans and large routine lists. Stop after primary DOI evidence when available.
- **Balanced** (`--mode balanced`): default for ordinary authenticity checks. Auxiliary evidence lines receive a short 2.5-second grace period after the first line completes.
- **Strict** (`--mode strict`): use for final or pre-submission checks. Wait for every enabled evidence line to complete or fail explicitly.

Do not invent a local confidence score. For DOI-bearing references, resolve the DOI and directly compare returned title, authors, journal, year, DOI, and PMID with source fields. Keep the existing classification policy. Severe items are reported and retained; never auto-delete them.

Do not run AI-assisted per-paper web searching by default. Stop after batch verification and title recovery, then ask the user whether to continue.

## Machine Input

Prefer `biomedical-reference-verifier.records.v1` JSON/JSONL. If the source is free text, convert it to records first using only values present in the user source. Do not fill missing source fields from Crossref, PubMed, OpenAlex, memory, or plausible guesses.

Minimal record:

```json
{
  "schema": "biomedical-reference-verifier.records.v1",
  "records": [
    {
      "index": 1,
      "source": {
        "original_text": "exact source reference",
        "title": "title from source, or empty string",
        "authors": ["First Author"],
        "year": "2024",
        "journal": "Journal from source",
        "identifiers": {"doi": "10.xxxx/example", "pmid": "", "urls": []},
        "source_lines": [12],
        "context": ""
      }
    }
  ]
}
```

Use `--input-mode records` for standardized JSON/JSONL. Use Markdown worksheet and `doi-context` modes only for compatibility.

## Commands

Run from this skill directory:

```bash
python3 scripts/verify_references.py refs.md --output-dir /tmp/reference-audit --citation-style ama
```

Common variants:

```bash
python3 scripts/verify_references.py refs.md --pipeline format-only --citation-style ama
python3 scripts/verify_references.py records.json --input-mode records --citation-style ama
python3 scripts/verify_references.py records.json --input-mode records --mode fast
python3 scripts/verify_references.py records.json --input-mode records --mode strict
python3 scripts/verify_references.py records.json --input-mode records --reuse-results previous/reference-audit.json
python3 scripts/verify_references.py records.json --input-mode records --write-index
python3 scripts/convert_reference_artifact.py previous/reference-audit.json --to index --output reference-index.json
python3 scripts/convert_reference_artifact.py reference-index.json --to audit --output restored-reference-audit.json
python3 scripts/verify_references.py refs.md --pubmed-mode off --openalex-mode off
python3 scripts/verify_references.py refs.md --doi-output append
python3 scripts/verify_references.py refs.md --keep-process-json
python3 scripts/verify_references.py refs.md --cleanup-process-files all
python3 scripts/verify_references.py refs.md --cleanup-process-files normalized_input,extracted_references
```

## Output Contract

Result files:

- `reference-audit-summary.md`: concise chat-ready summary.
- `reference-audit-detail.md`: detailed report with evidence links.
- `references.auto-fixed.md` or `document.auto-fixed.md`: fixed/formatted copy; never overwrites the source.

Process files retained by default:

- `reference-normalized-records.json`: machine-readable records.
- `reference-normalized-input.md`: human-readable parser inspection table.
- `references.extracted.md`: raw references extracted before verification.

Process files skipped by default:

- `reference-audit.json`: write only with `--keep-process-json`.

There is no hidden persistent cache. `--reuse-results` accepts either `reference-audit.json` or schema `biomedical-reference-verifier.index.v1`. The converter supports audit-to-index and index-to-audit round trips; the `results` array must remain identical after a round trip. In a conversation, ask about reuse once when such an artifact is available; do not repeatedly ask after the user decides.

User-edited prior artifacts are handled conservatively: malformed JSON is rejected with one concise error; invalid individual rows are skipped and rechecked; valid rows remain reusable. Do not guess repairs for damaged structured fields.

Prior-result reuse tolerates punctuation changes only when strict bibliographic fields still agree: DOI+title+year, or title+first author+year+journal. Temporary network failures receive one bounded retry; permanent 4xx failures do not. PubMed DOI batches split only when a batch fails. Early DOI recovery uses Crossref first, then OpenAlex and PubMed outside Fast mode.

`--write-index` optionally writes `reference-index.json`; it is off by default. Network request events and phase timings are stored in `reference-audit.json` when `--keep-process-json` is used.

Never delete user-requested result files. Delete only process files generated by the script in the selected output directory, and only when the user chooses deletion or `--cleanup-process-files` is explicit.

## Closeout

After running:

1. Paste or summarize `reference-audit-summary.md`.
2. Link result files and retained process files.
3. State which process files were cleaned or skipped.
4. Ask whether to delete retained process files:
   - A. delete all retained process files
   - B. keep selected process files
   - C. keep all process files for now
5. If severe items exist, ask whether to continue AI-assisted recovery, delete, keep with warning notes, or stop with the report.
6. Ask whether recovered DOI values should be appended when DOI output is optional.
