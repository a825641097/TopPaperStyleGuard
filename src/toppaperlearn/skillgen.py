"""Generate project-specific skill references from a profile."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def profile_to_markdown(profile: dict[str, Any]) -> str:
    style = profile.get("style", {})
    moves = profile.get("rhetorical_moves", {})
    transitions = ", ".join(item["item"] for item in style.get("top_transitions", [])[:8])
    sequences = moves.get("top_sequences", [])
    sequence_lines = "\n".join(
        f"- {item['item']} ({item['count']})" for item in sequences[:5]
    ) or "- No sequence detected"

    return f"""# TopPaperLearn Profile Reference

Field: {profile.get("field", "general")}
Documents: {profile.get("corpus", {}).get("document_count", 0)}
Words: {profile.get("corpus", {}).get("word_count", 0)}
Selected sections: {", ".join(profile.get("corpus", {}).get("selected_sections", [])) or "all detected text before references"}

## Privacy Contract

This reference is derived from aggregate statistics. It must not include source sentences from the corpus.

## Style Targets

- Sentence words: median {style.get("sentence_words", {}).get("median", 0)}, interquartile range {style.get("sentence_words", {}).get("p25", 0)}-{style.get("sentence_words", {}).get("p75", 0)}.
- Paragraph sentences: median {style.get("paragraph_sentences", {}).get("median", 0)}.
- Hedge-to-booster ratio: {style.get("hedge_to_booster_ratio", 0)}.
- Common transition markers: {transitions or "not enough evidence"}.

## Common Opening Move Sequences

{sequence_lines}

## Agent Rule

Use these as structural targets only. Do not infer or recreate source wording.
"""


def write_profile_reference(profile: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(profile_to_markdown(profile), encoding="utf-8")
