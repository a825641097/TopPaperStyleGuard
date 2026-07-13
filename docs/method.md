# Method

TopPaperLearn separates style learning from text reuse.

## Corpus Ingestion

The current release reads local `.txt`, `.md`, `.markdown`, and `.tex` files. It performs lightweight normalization of citations, comments, whitespace, and simple TeX commands before segmentation.

PDF text extraction is intentionally left to external local tools in the alpha release. This keeps the package dependency-free and makes the ingestion step easier to audit. Remove bibliographies, appendices, tables, and OCR artifacts when possible.

## Style Profile

The profile stores aggregate signals:

- document, word, and sentence counts;
- sentence length distribution;
- paragraph sentence distribution;
- section heading counts;
- rhetorical move counts;
- common opening move sequences;
- hedge-to-booster ratio;
- whitelisted transition marker counts.

It does not store source sentences.

## Rhetorical Moves

The built-in classifier is deterministic and transparent. It detects broad moves such as:

- phenomenon;
- gap;
- question;
- design;
- finding;
- mechanism;
- contribution;
- limitation;
- exposition.

The classifier is not a scientific writing judge. It gives agents a stable scaffold for revision and audit.

## Guardpack

The guardpack stores salted SHA-256 hashes of normalized source n-grams. During audit, draft n-grams are hashed with the same salt and compared to the guardpack.

This detects exact normalized word-order overlap without storing original source text. It does not detect every possible paraphrase, synonym substitution, sentence reordering, or semantic similarity, so human judgment remains necessary.

Guardpacks are sensitive. They do not contain raw source sentences, but if shared publicly they can still help an attacker test guessed phrases against the corpus. Keep guardpacks local or private.

For larger corpora, the guardpack can mark n-grams that appear across many source documents as common. Audits can ignore these common hashes with `--ignore-common-ngrams`, which reduces false positives from ordinary academic boilerplate while still flagging distinctive source-like spans.

`--common-doc-threshold` must be no larger than the number of corpus documents. For small examples, use `2`; for larger field-specific corpora, values such as `5` or `10` are usually more meaningful.

## Risk Levels

- `not_checked`: no guardpack was used, so overlap hygiene was not evaluated.
- `clear`: no guardpack overlap detected.
- `low`: some hashed n-gram overlap, usually short or isolated.
- `medium`: enough overlap to require revision before sharing.
- `high`: long contiguous source-like span or many repeated matches.

The default recommendation is to keep the maximum contiguous overlap below 10 words.

Recommended action:

- `clear`: acceptable for overlap hygiene; still review claims manually.
- `low`: inspect the flagged draft sentence and revise if it contains distinctive phrasing.
- `medium`: revise before sharing with collaborators or submitting.
- `high`: do not use the draft as-is; rewrite the flagged sentences from the underlying idea and rerun audit.
- `not_checked`: do not claim overlap safety; rerun with `--guard`.
