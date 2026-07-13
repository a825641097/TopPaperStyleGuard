"""Rhetorical move classification for academic prose."""

from __future__ import annotations

from collections import Counter

MOVE_PATTERNS: dict[str, tuple[str, ...]] = {
    "phenomenon": (
        "important",
        "central",
        "widespread",
        "substantial",
        "policy",
        "debate",
        "puzzle",
    ),
    "gap": (
        "however",
        "yet",
        "little is known",
        "remains unclear",
        "open question",
        "limited evidence",
        "not well understood",
    ),
    "question": (
        "we ask",
        "this paper asks",
        "whether",
        "how does",
        "to what extent",
        "why do",
    ),
    "design": (
        "we use",
        "we exploit",
        "using",
        "identification",
        "experiment",
        "quasi",
        "instrument",
        "difference-in-differences",
    ),
    "finding": (
        "we find",
        "results show",
        "evidence suggests",
        "estimate",
        "increase",
        "decrease",
        "effect",
    ),
    "mechanism": (
        "mechanism",
        "channel",
        "consistent with",
        "driven by",
        "explained by",
        "operate through",
    ),
    "contribution": (
        "contribute",
        "contribution",
        "advance",
        "speak to",
        "adds to",
        "builds on",
    ),
    "limitation": (
        "we cannot",
        "do not rule out",
        "limitation",
        "caution",
        "interpret",
        "suggestive",
    ),
}

HEDGES = {"may", "might", "could", "suggest", "suggests", "consistent", "likely", "appears"}
BOOSTERS = {"clearly", "prove", "proves", "undoubtedly", "always", "never", "definitive"}
TRANSITIONS = {
    "however",
    "therefore",
    "moreover",
    "nevertheless",
    "in contrast",
    "by contrast",
    "first",
    "second",
    "finally",
    "together",
    "instead",
}


def classify_sentence(sentence: str) -> str:
    lowered = sentence.lower()
    scores: Counter[str] = Counter()
    for move, patterns in MOVE_PATTERNS.items():
        for pattern in patterns:
            if pattern in lowered:
                scores[move] += 1
    if not scores:
        return "exposition"
    return scores.most_common(1)[0][0]


def move_sequence(sentences: list[str], limit: int = 8) -> list[str]:
    sequence: list[str] = []
    for sentence in sentences[:limit]:
        move = classify_sentence(sentence)
        if not sequence or sequence[-1] != move:
            sequence.append(move)
    return sequence


def stance_counts(tokens: list[str]) -> dict[str, int]:
    token_set = tokens
    return {
        "hedges": sum(1 for token in token_set if token in HEDGES),
        "boosters": sum(1 for token in token_set if token in BOOSTERS),
    }


def transition_counts(text: str) -> Counter[str]:
    lowered = f" {text.lower()} "
    counts: Counter[str] = Counter()
    for marker in TRANSITIONS:
        counts[marker] = lowered.count(f" {marker} ")
    return counts
