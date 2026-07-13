"""Text loading and lightweight segmentation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".tex"}

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'’-]*|\d+(?:\.\d+)?%?")
HEADING_RE = re.compile(r"^(#{1,6}\s+|\\section\*?\{|\\subsection\*?\{)?\s*([A-Za-z][A-Za-z /&-]{2,80})\}?$")
REFERENCE_HEADINGS = {"references", "bibliography", "literature cited", "works cited"}
KNOWN_SECTION_HEADINGS = {
    "abstract",
    "introduction",
    "background",
    "literature review",
    "methods",
    "method",
    "data",
    "empirical strategy",
    "results",
    "discussion",
    "conclusion",
    *REFERENCE_HEADINGS,
}


@dataclass(frozen=True)
class Document:
    path: Path
    text: str


@dataclass(frozen=True)
class Section:
    name: str
    body: str
    start_line: int
    end_line: int


def iter_text_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if root.suffix.lower() in SUPPORTED_SUFFIXES else []
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(path)
    return sorted(files)


def read_documents(root: Path, sections: set[str] | None = None) -> list[Document]:
    documents: list[Document] = []
    for path in iter_text_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        if text.strip():
            normalized = normalize_text(text)
            selected = select_sections(strip_reference_tail(normalized), sections)
            if selected.strip():
                documents.append(Document(path=path, text=selected))
    return documents


def normalize_text(text: str) -> str:
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"%.*", " ", text)
    text = re.sub(r"\\cite[tp]?\{[^}]*\}", " ", text)
    text = re.sub(r"\\ref\{[^}]*\}", " ", text)
    text = re.sub(r"\[[0-9,\s-]+\]", " ", text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def canonical_heading(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return None

    latex = re.match(
        r"^\\(?:chapter|section|subsection)\*?(?:\[[^\]]+\])?\{([^{}]+)\}\s*$",
        stripped,
    )
    if latex:
        raw = latex.group(1)
    else:
        markdown = re.match(r"^#{1,6}\s+(.+?)\s*#*$", stripped)
        raw = markdown.group(1) if markdown else stripped

    raw = re.sub(r"^\d+(?:\.\d+)*[\).]?\s+", "", raw)
    raw = re.sub(r"[:：]\s*$", "", raw)
    heading = re.sub(r"\s+", " ", raw.strip().lower())
    aliases = {
        "reference": "references",
        "references and notes": "references",
        "bibliographic references": "references",
        "appendices": "appendix",
        "supplementary material": "supplement",
    }
    heading = aliases.get(heading, heading)
    return heading if heading in KNOWN_SECTION_HEADINGS else None


def strip_back_matter(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^\\begin\{(?:thebibliography|references)\}", stripped):
            break
        if re.match(r"^\\bibliography\{", stripped):
            break
        if re.match(r"^@[A-Za-z]+\s*\{", stripped):
            break
        heading = canonical_heading(line)
        if heading in REFERENCE_HEADINGS or heading in {"appendix", "supplement"}:
            break
        kept.append(line)
    return "\n".join(kept).strip()


def strip_reference_tail(text: str) -> str:
    return strip_back_matter(text)


def parse_sections(text: str) -> list[Section]:
    sections: list[Section] = []
    current_name: str | None = None
    current_start = 0
    current_lines: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        heading = canonical_heading(line)
        if heading:
            if current_name is not None:
                sections.append(
                    Section(
                        name=current_name,
                        body="\n".join(current_lines).strip(),
                        start_line=current_start,
                        end_line=line_number - 1,
                    )
                )
            current_name = heading
            current_start = line_number
            current_lines = []
            continue
        if current_name is not None:
            current_lines.append(line)
    if current_name is not None:
        sections.append(
            Section(
                name=current_name,
                body="\n".join(current_lines).strip(),
                start_line=current_start,
                end_line=len(text.splitlines()),
            )
        )
    return [section for section in sections if section.body.strip()]


def select_sections(text: str, sections: set[str] | None) -> str:
    if not sections:
        return text
    parsed = parse_sections(text)
    selected = [section.body for section in parsed if section.name in sections]
    return "\n\n".join(selected).strip()


def split_paragraphs(text: str) -> list[str]:
    raw = re.split(r"\n\s*\n", text)
    if len(raw) == 1:
        raw = re.split(r"(?<=\.)\s{2,}", text)
    return [p.strip() for p in raw if p.strip()]


def split_sentences(text: str) -> list[str]:
    parts = SENTENCE_RE.split(text.strip())
    sentences: list[str] = []
    for part in parts:
        cleaned = part.strip()
        if cleaned:
            sentences.append(cleaned)
    return sentences


def words(text: str) -> list[str]:
    return [match.group(0).lower().strip("'’") for match in WORD_RE.finditer(text)]


def detect_sections(text: str) -> list[str]:
    sections: list[str] = []
    for line in text.splitlines():
        match = HEADING_RE.match(line.strip())
        if not match:
            continue
        heading = match.group(2).strip().lower()
        if heading in KNOWN_SECTION_HEADINGS:
            sections.append(heading)
    return sections


def stable_doc_id(path: Path, text: str) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(str(path.name).encode("utf-8", errors="ignore"))
    digest.update(b"\0")
    digest.update(text.encode("utf-8", errors="ignore"))
    return digest.hexdigest()[:16]
