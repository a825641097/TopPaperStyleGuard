"""Draft audit against a style profile and guardpack."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .guard import sentence_fingerprints_with_salt
from .moves import classify_sentence, move_sequence
from .profile import load_profile
from .text import split_paragraphs, split_sentences, words


def _fingerprint_meta(known: dict[str, Any], digest: str) -> tuple[int, int]:
    meta = known[digest]
    if isinstance(meta, dict):
        return int(meta.get("count", 1)), int(meta.get("document_count", 1))
    # Backward compatibility for early alpha guardpacks that stored occurrence rows.
    doc_ids = {str(match[0]) for match in meta if match}
    return len(meta), len(doc_ids)


def _risk_from_span(max_span_words: int, total_matches: int) -> str:
    if max_span_words >= 14 or total_matches >= 18:
        return "high"
    if max_span_words >= 10 or total_matches >= 8:
        return "medium"
    if max_span_words >= 8 or total_matches > 0:
        return "low"
    return "clear"


def _max_run(indices: list[int], ngram: int) -> int:
    if not indices:
        return 0
    best = run = 1
    previous = indices[0]
    for index in indices[1:]:
        if index == previous + 1:
            run += 1
        else:
            best = max(best, run)
            run = 1
        previous = index
    return ngram + max(best, run) - 1


def audit_draft(
    draft: Path,
    profile: dict[str, Any] | None = None,
    guardpack: dict[str, Any] | None = None,
    ignore_common_ngrams: bool = False,
    include_excerpts: bool = False,
) -> dict[str, Any]:
    text = draft.read_text(encoding="utf-8", errors="replace")
    sentences = split_sentences(text)
    paragraphs = split_paragraphs(text)
    draft_moves = [classify_sentence(sentence) for sentence in sentences]

    overlap_findings: list[dict[str, Any]] = []
    total_matches = 0
    max_span_words = 0
    ignored_common_matches = 0
    overlap_checked = bool(guardpack)
    if guardpack:
        ngram = int(guardpack["ngram"])
        salt = str(guardpack.get("salt", "toppaperlearn-v1"))
        known = guardpack["fingerprints"]
        common = set(guardpack.get("common_fingerprints", [])) if ignore_common_ngrams else set()
        for sentence_index, sentence in enumerate(sentences):
            hits = []
            source_document_count = 0
            source_match_count = 0
            for token_index, digest in sentence_fingerprints_with_salt(sentence, ngram, salt):
                if digest in common:
                    ignored_common_matches += 1
                    continue
                if digest in known:
                    hits.append(token_index)
                    count, doc_count = _fingerprint_meta(known, digest)
                    source_match_count += count
                    source_document_count = max(source_document_count, doc_count)
            if hits:
                span = _max_run(sorted(hits), ngram)
                max_span_words = max(max_span_words, span)
                total_matches += len(hits)
                overlap_findings.append(
                    {
                        "sentence_index": sentence_index + 1,
                        "matched_ngrams": len(hits),
                        "max_contiguous_span_words": span,
                        "source_document_count": source_document_count,
                        "source_match_count": source_match_count,
                    }
                )
                if include_excerpts:
                    overlap_findings[-1]["draft_excerpt"] = sentence[:220]

    style_feedback: list[str] = []
    if profile:
        target = profile.get("style", {}).get("sentence_words", {})
        draft_lengths = [len(words(sentence)) for sentence in sentences if words(sentence)]
        if draft_lengths and target:
            mean = sum(draft_lengths) / len(draft_lengths)
            p25 = float(target.get("p25", 0))
            p75 = float(target.get("p75", 0))
            if p75 and mean > p75 * 1.4:
                style_feedback.append("Average sentence length is much longer than the profile; split overloaded claims.")
            if p25 and mean < max(8, p25 * 0.65):
                style_feedback.append("Average sentence length is much shorter than the profile; combine choppy exposition where useful.")

        top_sequences = profile.get("rhetorical_moves", {}).get("top_sequences", [])
        if top_sequences and sentences:
            current_sequence = " > ".join(move_sequence(sentences, limit=10))
            style_feedback.append(f"Opening move sequence: {current_sequence or 'not detected'}.")

    risk = _risk_from_span(max_span_words, total_matches) if overlap_checked else "not_checked"
    recommendations = []
    if not overlap_checked:
        recommendations.append("No guardpack was provided; overlap safety was not checked.")
    if risk in {"medium", "high"}:
        recommendations.append("Rewrite flagged sentences from the underlying idea, not by local synonym substitution.")
        recommendations.append("Run the audit again after revision and keep max contiguous overlap below 10 words.")
    if not style_feedback:
        style_feedback.append("No major deterministic style drift detected by the current profile.")

    return {
        "draft": str(draft),
        "risk": risk,
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "move_counts": {move: draft_moves.count(move) for move in sorted(set(draft_moves))},
        "overlap": {
            "checked": overlap_checked,
            "total_matched_ngrams": total_matches,
            "max_contiguous_span_words": max_span_words,
            "ignored_common_ngrams": ignored_common_matches,
            "findings": overlap_findings,
        },
        "style_feedback": style_feedback,
        "recommendations": recommendations,
    }


def load_profile_optional(path: Path | None) -> dict[str, Any] | None:
    return load_profile(path) if path else None


def audit_to_json(audit: dict[str, Any]) -> str:
    return json.dumps(audit, indent=2, sort_keys=True)


def audit_to_text(audit: dict[str, Any]) -> str:
    lines = [
        f"TopPaperLearn audit: {audit['draft']}",
        f"Risk: {audit['risk']}",
        f"Matched n-grams: {audit['overlap']['total_matched_ngrams']}",
        f"Ignored common n-grams: {audit['overlap'].get('ignored_common_ngrams', 0)}",
        f"Max contiguous overlap: {audit['overlap']['max_contiguous_span_words']} words",
        "",
        "Style feedback:",
    ]
    lines.extend(f"- {item}" for item in audit["style_feedback"])
    if audit["overlap"]["findings"]:
        lines.append("")
        lines.append("Overlap findings:")
        for finding in audit["overlap"]["findings"][:12]:
            lines.append(
                f"- sentence {finding['sentence_index']}: "
                f"{finding['matched_ngrams']} n-grams, "
                f"{finding['max_contiguous_span_words']} word span, "
                f"{finding.get('source_document_count', 0)} source docs"
            )
            if "draft_excerpt" in finding:
                lines.append(f"  excerpt: {finding['draft_excerpt']}")
    if audit["recommendations"]:
        lines.append("")
        lines.append("Recommendations:")
        lines.extend(f"- {item}" for item in audit["recommendations"])
    return "\n".join(lines) + "\n"


def audit_to_markdown(audit: dict[str, Any]) -> str:
    lines = [
        f"# TopPaperLearn Audit",
        "",
        f"- Draft: `{audit['draft']}`",
        f"- Risk: **{audit['risk']}**",
        f"- Matched n-grams: `{audit['overlap']['total_matched_ngrams']}`",
        f"- Ignored common n-grams: `{audit['overlap'].get('ignored_common_ngrams', 0)}`",
        f"- Max contiguous overlap: `{audit['overlap']['max_contiguous_span_words']}` words",
        "",
        "## Style Feedback",
        "",
    ]
    lines.extend(f"- {item}" for item in audit["style_feedback"])
    if audit["overlap"]["findings"]:
        lines.extend(
            [
                "",
                "## Overlap Findings",
                "",
                "| Sentence | Matched n-grams | Max span | Source docs |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for finding in audit["overlap"]["findings"][:20]:
            lines.append(
                f"| {finding['sentence_index']} | "
                f"{finding['matched_ngrams']} | "
                f"{finding['max_contiguous_span_words']} | "
                f"{finding.get('source_document_count', 0)} |"
            )
        excerpt_findings = [
            finding for finding in audit["overlap"]["findings"][:20] if "draft_excerpt" in finding
        ]
        if excerpt_findings:
            lines.extend(["", "### Draft Excerpts", ""])
            for finding in excerpt_findings:
                lines.append(f"- Sentence {finding['sentence_index']}: {finding['draft_excerpt']}")
    if audit["recommendations"]:
        lines.extend(["", "## Recommendations", ""])
        lines.extend(f"- {item}" for item in audit["recommendations"])
    lines.append("")
    return "\n".join(lines)
