"""Hashed source-overlap guardpack."""

from __future__ import annotations

import hashlib
import json
import secrets
from collections import defaultdict
from pathlib import Path
from typing import Any

from .text import read_documents, split_sentences, stable_doc_id, words


def hash_ngram(tokens: list[str], salt: str) -> str:
    digest = hashlib.sha256()
    digest.update(salt.encode("utf-8"))
    digest.update(b"\0")
    digest.update(" ".join(tokens).encode("utf-8"))
    return digest.hexdigest()


def sentence_fingerprints(sentence: str, ngram: int) -> list[tuple[int, str]]:
    return sentence_fingerprints_with_salt(sentence, ngram, "toppaperlearn-v1")


def sentence_fingerprints_with_salt(sentence: str, ngram: int, salt: str) -> list[tuple[int, str]]:
    tokens = words(sentence)
    if len(tokens) < ngram:
        return []
    return [
        (index, hash_ngram(tokens[index : index + ngram], salt))
        for index in range(0, len(tokens) - ngram + 1)
    ]


def build_guardpack(
    corpus: Path,
    ngram: int = 8,
    include_path_hints: bool = False,
    common_doc_threshold: int = 3,
    salt: str | None = None,
    sections: set[str] | None = None,
) -> dict[str, Any]:
    if ngram < 5:
        raise ValueError("ngram must be at least 5 to avoid over-flagging common phrasing")
    documents = read_documents(corpus, sections=sections)
    if not documents:
        raise ValueError(f"No supported text files found in {corpus}")
    warnings: list[str] = []
    effective_common_doc_threshold = common_doc_threshold
    if common_doc_threshold > len(documents):
        warnings.append(
            "common_doc_threshold exceeded corpus document count; common n-gram filtering is disabled for this guardpack"
        )
        effective_common_doc_threshold = len(documents) + 1
    salt = salt or secrets.token_hex(16)

    fingerprint_counts: dict[str, int] = defaultdict(int)
    fingerprint_docs: dict[str, set[str]] = defaultdict(set)
    doc_meta: list[dict[str, Any]] = []
    for doc in documents:
        doc_id = stable_doc_id(doc.path, doc.text)
        sentences = split_sentences(doc.text)
        doc_meta.append(
            {
                "sentence_count": len(sentences),
                "path_hint": doc.path.name if include_path_hints else None,
            }
        )
        for sentence_index, sentence in enumerate(sentences):
            for _token_index, digest in sentence_fingerprints_with_salt(sentence, ngram, salt):
                fingerprint_counts[digest] += 1
                fingerprint_docs[digest].add(doc_id)

    common_fingerprints = sorted(
        digest
        for digest, doc_ids in fingerprint_docs.items()
        if effective_common_doc_threshold > 1 and len(doc_ids) >= effective_common_doc_threshold
    )

    return {
        "schema_version": "0.1",
        "created_by": "TopPaperLearn",
        "fingerprint_format_version": "salted-aggregate-v1",
        "hash_algorithm": "sha256",
        "salt_policy": "random per guardpack; stored in private guardpack for local audit",
        "privacy": {
            "stores_source_text": False,
            "stores_source_sentences": False,
            "stores_hashes_only": True,
            "guardpack_is_sensitive": True,
            "note": "Hashes do not contain raw source text, but a shared guardpack can still reveal whether guessed phrases are present. Keep it local or private.",
            "hash": "sha256(project salt + normalized ngram)",
        },
        "salt": salt,
        "ngram": ngram,
        "common_doc_threshold": common_doc_threshold,
        "effective_common_doc_threshold": effective_common_doc_threshold,
        "selected_sections": sorted(sections) if sections else [],
        "warnings": warnings,
        "common_fingerprints": common_fingerprints,
        "documents": doc_meta,
        "fingerprints": {
            digest: {
                "count": count,
                "document_count": len(fingerprint_docs[digest]),
            }
            for digest, count in fingerprint_counts.items()
        },
    }


def write_guardpack(guardpack: dict[str, Any], path: Path) -> None:
    path.write_text(json.dumps(guardpack, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_guardpack(path: Path) -> dict[str, Any]:
    guardpack = json.loads(path.read_text(encoding="utf-8"))
    if "fingerprints" not in guardpack or "ngram" not in guardpack:
        raise ValueError(f"Invalid guardpack: {path}")
    if "salt" not in guardpack:
        guardpack["fingerprint_format_version"] = "legacy-fixed-salt-v0"
        guardpack["salt"] = "toppaperlearn-v1"
    return guardpack
