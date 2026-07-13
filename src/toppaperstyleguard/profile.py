"""Aggregate profile construction."""

from __future__ import annotations

import json
import statistics
from collections import Counter
from pathlib import Path
from typing import Any

from .moves import classify_sentence, move_sequence, stance_counts, transition_counts
from .text import detect_sections, read_documents, split_paragraphs, split_sentences, words

SCHEMA_VERSION = "0.1"


def _summary(values: list[int]) -> dict[str, float]:
    if not values:
        return {"count": 0, "mean": 0, "median": 0, "p25": 0, "p75": 0}
    values = sorted(values)
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "p25": float(values[len(values) // 4]),
        "p75": float(values[(len(values) * 3) // 4]),
    }


def _top(counter: Counter[str], limit: int = 12) -> list[dict[str, Any]]:
    return [{"item": item, "count": count} for item, count in counter.most_common(limit) if count]


def build_profile(
    corpus: Path,
    field: str = "general",
    sections: set[str] | None = None,
) -> dict[str, Any]:
    requested_sections = sections
    documents = read_documents(corpus, sections=requested_sections)
    if not documents:
        if requested_sections:
            wanted = ", ".join(sorted(requested_sections))
            raise ValueError(f"No matching sections found in {corpus}: {wanted}")
        raise ValueError(f"No supported text files found in {corpus}")

    sentence_lengths: list[int] = []
    paragraph_sentence_counts: list[int] = []
    detected_sections: Counter[str] = Counter()
    moves: Counter[str] = Counter()
    transitions: Counter[str] = Counter()
    abstract_sequences: Counter[str] = Counter()
    total_words = 0
    total_sentences = 0
    stance = Counter()

    for doc in documents:
        doc_words = words(doc.text)
        total_words += len(doc_words)
        stance.update(stance_counts(doc_words))
        detected_sections.update(detect_sections(doc.text))
        transitions.update(transition_counts(doc.text))

        paragraphs = split_paragraphs(doc.text)
        for paragraph in paragraphs:
            sentences = split_sentences(paragraph)
            if not sentences:
                continue
            paragraph_sentence_counts.append(len(sentences))
            for sentence in sentences:
                tokens = words(sentence)
                if tokens:
                    sentence_lengths.append(len(tokens))
                    moves[classify_sentence(sentence)] += 1
                    total_sentences += 1
        sequence = " > ".join(move_sequence(split_sentences(doc.text), limit=10))
        if sequence:
            abstract_sequences[sequence] += 1

    return {
        "schema_version": SCHEMA_VERSION,
        "created_by": "TopPaperStyleGuard",
        "field": field,
        "privacy": {
            "stores_source_text": False,
            "stores_source_sentences": False,
            "stores_aggregate_statistics": True,
            "note": "This profile is designed to learn rhetorical structure, not reusable source wording.",
        },
        "corpus": {
            "document_count": len(documents),
            "word_count": total_words,
            "sentence_count": total_sentences,
            "selected_sections": sorted(requested_sections) if requested_sections else [],
        },
        "style": {
            "sentence_words": _summary(sentence_lengths),
            "paragraph_sentences": _summary(paragraph_sentence_counts),
            "hedge_to_booster_ratio": round(
                stance["hedges"] / max(1, stance["boosters"]), 2
            ),
            "top_transitions": _top(transitions),
        },
        "rhetorical_moves": {
            "counts": dict(moves),
            "top_sequences": _top(abstract_sequences, limit=8),
        },
        "sections": dict(detected_sections),
        "guidance": [
            "Learn move order, evidentiary restraint, and paragraph function; do not reuse source phrasing.",
            "Prefer concrete research questions, identification logic, bounded claims, and explicit contribution targets.",
            "After any AI rewrite, run an overlap audit against the guardpack before using the text.",
        ],
    }


def write_profile(profile: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_profile(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
