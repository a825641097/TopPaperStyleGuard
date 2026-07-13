# TopPaperStyleGuard

**Learn top-journal writing structure without copying top-journal text.**

[简体中文](README.zh-CN.md) | [Method](docs/method.md) | [Agent skill](docs/agent-skill.md) | [Ethics](docs/ethics.md)

TopPaperStyleGuard turns a private corpus of high-quality papers into local artifacts:

- a **style profile**: aggregate rhetorical patterns, sentence rhythm, paragraph structure, move sequences, and stance markers;
- a **guardpack**: salted hashed n-gram fingerprints used to detect drafts that drift too close to the source corpus;
- a **skill reference**: a readable profile summary that agents can load without seeing the original papers.

The design principle is simple:

> Learn rhetorical moves, not sentences.

It is built for researchers and coding agents that need to improve academic writing while avoiding accidental copying, style overfitting, or hidden reuse of protected source text.

## What It Does

- Builds a local aggregate profile from `.txt`, `.md`, or `.tex` papers.
- Avoids storing source sentences in the generated profile.
- Creates a hashed overlap guardpack for local similarity checks.
- Audits drafts for long source-like spans before submission or agent-assisted revision.
- Generates a profile reference that agents can load as a writing Skill resource.
- Ships a portable agent skill at [`skills/toppaperstyleguard`](skills/toppaperstyleguard).

## Quick Start

Install from this checkout:

```console
python -m pip install .
```

For a temporary source-tree trial without installing:

```console
PYTHONPATH=src python -m toppaperstyleguard --help
```

### Try the Included Example

If you do not have a corpus ready yet, run the bundled offline example:

```console
python -m toppaperstyleguard build examples/corpus \
  --field economics \
  --profile-out /tmp/tpsg.profile.json \
  --guard-out /tmp/tpsg.guard.json \
  --skill-reference /tmp/tpsg-profile.md \
  --common-doc-threshold 2

python -m toppaperstyleguard audit examples/drafts/introduction.md \
  --profile /tmp/tpsg.profile.json \
  --guard /tmp/tpsg.guard.json \
  --ignore-common-ngrams \
  --fail-on none

python -m toppaperstyleguard audit examples/drafts/revised-introduction.md \
  --profile /tmp/tpsg.profile.json \
  --guard /tmp/tpsg.guard.json \
  --ignore-common-ngrams \
  --fail-on none
```

Build a profile and guardpack from your local top-journal corpus:

```console
tpsg build papers/top-journal-corpus \
  --field economics \
  --profile-out topstyle.profile.json \
  --guard-out topstyle.guard.json \
  --skill-reference skills/toppaperstyleguard/references/profile.md \
  --common-doc-threshold 5
```

Corpus preparation: start with 10-30 papers or sections from the same field and genre. Use clean UTF-8 text. Remove bibliographies, appendices, tables, and OCR artifacts when possible. For style learning, section-level corpora such as introductions-only are often easier to interpret than mixed full papers.

### Real Introduction Workflow

For an introduction-focused workflow, put one top-journal introduction per file:

```text
data/top-intros/paper-01.txt
data/top-intros/paper-02.txt
drafts/my-introduction.md
```

If each corpus file already contains only an introduction, do not use `--sections`:

```console
tpsg build data/top-intros \
  --field economics \
  --profile-out topstyle.profile.json \
  --guard-out topstyle.guard.json \
  --skill-reference skills/toppaperstyleguard/references/profile.md

tpsg audit drafts/my-introduction.md \
  --profile topstyle.profile.json \
  --guard topstyle.guard.json \
  --ignore-common-ngrams \
  --fail-on medium
```

If each corpus file is a full paper with recognizable headings such as `Introduction` or `\section{Introduction}`, use:

```console
tpsg build data/top-papers \
  --field economics \
  --sections introduction \
  --profile-out topstyle.profile.json \
  --guard-out topstyle.guard.json \
  --skill-reference skills/toppaperstyleguard/references/profile.md
```

Checklist: use UTF-8 text, one paper or section per file, clean obvious OCR artifacts, and remove tables or bibliography blocks when possible. The section parser is lightweight; if headings are missing or unusual, save the target section as a standalone file and omit `--sections`.

Audit a draft:

```console
tpsg audit drafts/introduction.md \
  --profile topstyle.profile.json \
  --guard topstyle.guard.json \
  --ignore-common-ngrams \
  --fail-on none
```

Example output:

```text
TopPaperStyleGuard audit: drafts/introduction.md
Risk: medium
Matched n-grams: 9
Max contiguous overlap: 11 words

Style feedback:
- Opening move sequence: phenomenon > gap > question > design.

Recommendations:
- Rewrite flagged sentences from the underlying idea, not by local synonym substitution.
- Run the audit again after revision and keep max contiguous overlap below 10 words.
```

## Why This Is Not a Plagiarism Machine

TopPaperStyleGuard is intentionally limited:

- It does not generate papers from a corpus.
- It does not store source sentences in the profile.
- It does not make the guardpack safe to publish; guardpacks contain salted hashes and should stay local or private.
- It does not encourage paraphrasing protected paragraphs.
- It does not claim to bypass plagiarism detection.
- It flags risky overlap so the writer can move farther away from source wording.

The tool is for learning durable writing strategy: how strong papers motivate a question, introduce a gap, describe identification, bound claims, sequence contributions, and use cautious academic stance.

## Agent Skill

Copy [`skills/toppaperstyleguard`](skills/toppaperstyleguard) into a compatible agent skills directory, or point an agent at its `SKILL.md`.

Then use a prompt like:

```text
Use $toppaperstyleguard to revise my introduction toward top-journal structure.
Preserve my claims, avoid source-like wording, and run tpsg audit before finalizing.
```

See [Agent Skill](docs/agent-skill.md).

## Commands

| Command | Purpose |
| --- | --- |
| `tpsg build CORPUS` | Create a style profile and hashed guardpack |
| `tpsg audit DRAFT` | Check a draft against the profile and guardpack |
| `tpsg inspect PROFILE` | Inspect profile metadata and privacy contract |

Use `tpsg inspect topstyle.profile.json --guard topstyle.guard.json` to confirm selected sections, move sequences, n-gram size, and guardpack settings before giving the artifacts to an agent.

For larger corpora, use `--common-doc-threshold` during build and `--ignore-common-ngrams` during audit to reduce false positives from generic academic boilerplate.
The threshold must be no larger than the number of corpus documents.

Use `--fail-on none` for exploratory writing, `--fail-on medium` before sharing or submission, and `--fail-on high` for a looser CI gate. Use `--style-only` only when you intentionally want profile feedback without any overlap-safety claim.

Audit reports omit draft excerpts by default. Add `--include-excerpts` only when you are comfortable storing or sharing snippets from the draft.

## Supported Inputs

The alpha version reads UTF-8 `.txt`, `.md`, `.markdown`, and `.tex` files. For PDFs, extract text first with your preferred local PDF text tool, then run `tpsg build` on the extracted files.

## Where It Fits

TopPaperStyleGuard complements grammar checkers, prose linters, and citation tools. It focuses on a narrower problem: **agent-assisted academic style learning with overlap safeguards**.

It is useful for:

- abstract and introduction revision;
- contribution paragraph sharpening;
- literature-gap positioning;
- empirical strategy prose;
- cautious discussion and limitation sections;
- bilingual academic drafting where structure matters more than literal translation.

## License

Apache-2.0. See [LICENSE](LICENSE).
