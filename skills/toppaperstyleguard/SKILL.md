---
name: toppaperstyleguard
description: Top-journal academic writing revision with source-overlap safeguards. Use when an agent needs to revise abstracts, introductions, contribution paragraphs, literature-gap positioning, empirical strategy prose, or discussion sections using a TopPaperStyleGuard profile while avoiding source-like phrasing, running tpsg audit, and preserving the user's actual claims and evidence.
---

# TopPaperStyleGuard

## Overview

Use this skill to improve academic prose toward the structure and restraint of top-journal writing without copying corpus wording. Learn from `topstyle.profile.json` or `references/profile.md`; never imitate source sentences from the training corpus.

## Ground Rules

- Preserve the user's claims, evidence, identification strategy, and contribution boundaries.
- Learn rhetorical moves, not sentences.
- Do not request or reproduce protected source passages unless the user explicitly provides a short excerpt for analysis.
- Do not use synonym-swapping to disguise copied text. If overlap is flagged, rewrite from the underlying idea.
- Run `tpsg audit` before finalizing when a profile and guardpack are available.
- Do not claim overlap safety when no guardpack was used.
- Confirm the user is allowed to process the source corpus if that is unclear.
- Be explicit about uncertainty: this skill improves structure and overlap hygiene, not scientific validity.

## Inputs to Look For

- `topstyle.profile.json`: aggregate style and rhetorical move profile.
- `topstyle.guard.json`: hashed source-overlap guardpack.
- `skills/toppaperstyleguard/references/profile.md`: optional human-readable profile reference.
- Draft files such as `abstract.md`, `introduction.md`, `paper.tex`, or section snippets pasted by the user.

If a project-specific profile reference exists, read it before revising. If only JSON exists, inspect it with:

```console
tpsg inspect topstyle.profile.json
```

If expected files are not in the current directory, search common locations such as `.` , `profiles/`, `style/`, `skills/toppaperstyleguard/references/`, and the manuscript directory. If no guardpack is available, use `--style-only` and explicitly state that overlap was not checked.

If the user has a corpus and draft but no artifacts, build them first. Use `--sections introduction` only for full papers with recognizable section headings; if the corpus already contains introduction-only files, omit `--sections`.

If the draft is pasted in chat, ask to save it to a local file or create a temporary file before audit. Do not claim audit success for text that was not actually checked with `tpsg audit`.

## Revision Workflow

1. Identify the section type: abstract, introduction, contribution, literature review, empirical strategy, results, discussion, or conclusion.
2. Diagnose the current rhetorical move sequence. Typical useful moves include phenomenon, gap, question, design, finding, mechanism, contribution, limitation, and exposition.
3. Revise structure first:
   - make the research question visible;
   - locate the gap precisely;
   - connect design to credibility;
   - separate finding from interpretation;
   - bound contribution claims.
4. Revise style second:
   - prefer concrete nouns and evidence-bearing verbs;
   - reduce promotional claims;
   - use hedging when evidence is suggestive;
   - keep topic sentences functional;
   - remove generic phrases such as "fills an important gap" unless immediately specified.
5. Audit overlap:

```console
tpsg audit path/to/draft.md --profile topstyle.profile.json --guard topstyle.guard.json
```

For large corpora, prefer:

```console
tpsg audit path/to/draft.md --profile topstyle.profile.json --guard topstyle.guard.json --ignore-common-ngrams
```

6. If risk is `medium` or `high`, rewrite flagged sentences from scratch and rerun the audit. Treat common n-grams as lower priority than distinctive long spans.

## Section-Specific Guidance

### Abstract

Use a compact sequence: problem or phenomenon, gap/question, design, central finding, contribution or implication. Avoid broad claims not supported by the manuscript.

### Introduction

Make the first pages do real work: motivate stakes, name what existing work cannot yet explain, state the question, preview the design, summarize findings, and position contributions.

### Contribution Paragraph

Do not write a generic contribution list. For each contribution, specify the literature or debate, what uncertainty remains, and what the paper adds that was not already known.

### Empirical Strategy

Tie the design to the threat it addresses. Avoid overstating causality unless the design supports it. Separate identifying variation, assumptions, diagnostics, and limitations.

### Discussion

Use bounded implications. State what the evidence suggests, what remains unresolved, and what future work or policy decisions should not infer.

## Reporting Back

Return:

- the revised text or a patch;
- a short explanation of structural changes;
- the audit command used;
- risk, matched n-grams, ignored common n-grams, and max contiguous overlap;
- whether any medium/high-risk draft sentences remain;
- any sentences that still need user judgment;
- a reminder that the audit checks source-like wording, not originality of the research claim.
