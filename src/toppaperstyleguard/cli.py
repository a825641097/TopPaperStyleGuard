"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .audit import audit_draft, audit_to_json, audit_to_markdown, audit_to_text
from .guard import build_guardpack, load_guardpack, write_guardpack
from .profile import build_profile, load_profile, write_profile
from .skillgen import write_profile_reference


def _parse_sections(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def _cmd_build(args: argparse.Namespace) -> int:
    sections = _parse_sections(args.sections)
    profile = build_profile(args.corpus, field=args.field, sections=sections)
    guardpack = build_guardpack(
        args.corpus,
        ngram=args.ngram,
        include_path_hints=args.include_path_hints,
        common_doc_threshold=args.common_doc_threshold,
        sections=sections,
    )
    write_profile(profile, args.profile_out)
    write_guardpack(guardpack, args.guard_out)
    if args.skill_reference:
        write_profile_reference(profile, args.skill_reference)
    print(f"Wrote profile: {args.profile_out}")
    print(f"Wrote guardpack: {args.guard_out}")
    print(f"Guardpack fingerprints: {len(guardpack['fingerprints'])}")
    print(f"Common fingerprints: {len(guardpack.get('common_fingerprints', []))}")
    if sections:
        print(f"Selected sections: {', '.join(sorted(sections))}")
    for warning in guardpack.get("warnings", []):
        print(f"Warning: {warning}")
    print("Note: guardpacks contain salted hashes and should remain local or private.")
    if args.skill_reference:
        print(f"Wrote skill reference: {args.skill_reference}")
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    if not args.guard and not args.style_only:
        print(
            "error: --guard is required for overlap auditing; use --style-only for profile-only diagnostics",
            file=sys.stderr,
        )
        return 1
    profile = load_profile(args.profile) if args.profile else None
    guardpack = load_guardpack(args.guard) if args.guard else None
    audit = audit_draft(
        args.draft,
        profile=profile,
        guardpack=guardpack,
        ignore_common_ngrams=args.ignore_common_ngrams,
        include_excerpts=args.include_excerpts,
    )
    if args.format == "json":
        output = audit_to_json(audit) + "\n"
    elif args.format == "markdown":
        output = audit_to_markdown(audit)
    else:
        output = audit_to_text(audit)
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    if args.fail_on == "none":
        return 0
    if audit["risk"] == "not_checked":
        return 0
    order = {"clear": 0, "low": 1, "medium": 2, "high": 3}
    if order[audit["risk"]] >= order[args.fail_on]:
        return 2
    return 0


def _cmd_inspect(args: argparse.Namespace) -> int:
    profile = load_profile(args.profile)
    print(f"Field: {profile.get('field')}")
    print(f"Documents: {profile.get('corpus', {}).get('document_count')}")
    print(f"Words: {profile.get('corpus', {}).get('word_count')}")
    selected = profile.get("corpus", {}).get("selected_sections", [])
    print(f"Selected sections: {', '.join(selected) if selected else 'all detected text before references'}")
    sequences = profile.get("rhetorical_moves", {}).get("top_sequences", [])
    if sequences:
        print("Top move sequences:")
        for item in sequences[:5]:
            print(f"  {item['item']} ({item['count']})")
    print("Privacy:")
    for key, value in profile.get("privacy", {}).items():
        print(f"  {key}: {value}")
    if args.guard:
        guardpack = load_guardpack(args.guard)
        print("Guardpack:")
        print(f"  ngram: {guardpack.get('ngram')}")
        print(f"  fingerprints: {len(guardpack.get('fingerprints', {}))}")
        print(f"  common_doc_threshold: {guardpack.get('common_doc_threshold')}")
        print(f"  common_fingerprints: {len(guardpack.get('common_fingerprints', []))}")
        print(f"  selected_sections: {', '.join(guardpack.get('selected_sections', [])) or 'all detected text before references'}")
        for warning in guardpack.get("warnings", []):
            print(f"  warning: {warning}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tpsg",
        description="Learn top-journal writing structure while guarding against source overlap.",
    )
    sub = parser.add_subparsers(required=True)

    build = sub.add_parser("build", help="Build a style profile and hashed guardpack from a corpus")
    build.add_argument("corpus", type=Path)
    build.add_argument("--field", default="general")
    build.add_argument(
        "--sections",
        help="Comma-separated section headings to learn from, e.g. abstract,introduction.",
    )
    build.add_argument("--profile-out", type=Path, default=Path("topstyle.profile.json"))
    build.add_argument("--guard-out", type=Path, default=Path("topstyle.guard.json"))
    build.add_argument("--skill-reference", type=Path)
    build.add_argument("--ngram", type=int, default=8)
    build.add_argument(
        "--common-doc-threshold",
        type=int,
        default=3,
        help="Mark n-grams appearing in this many source documents as common boilerplate.",
    )
    build.add_argument("--include-path-hints", action="store_true")
    build.set_defaults(func=_cmd_build)

    audit = sub.add_parser("audit", help="Audit a draft against a profile and guardpack")
    audit.add_argument("draft", type=Path)
    audit.add_argument("--profile", type=Path)
    audit.add_argument("--guard", type=Path)
    audit.add_argument(
        "--style-only",
        action="store_true",
        help="Run profile-only diagnostics without claiming overlap safety.",
    )
    audit.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    audit.add_argument("--output", type=Path)
    audit.add_argument("--fail-on", choices=["none", "low", "medium", "high"], default="high")
    audit.add_argument(
        "--ignore-common-ngrams",
        action="store_true",
        help="Ignore guardpack n-grams marked common across many corpus documents.",
    )
    audit.add_argument(
        "--include-excerpts",
        action="store_true",
        help="Include snippets from the draft in reports. Off by default to avoid leaking manuscripts.",
    )
    audit.set_defaults(func=_cmd_audit)

    inspect = sub.add_parser("inspect", help="Inspect a profile without loading source papers")
    inspect.add_argument("profile", type=Path)
    inspect.add_argument("--guard", type=Path, help="Optional guardpack to inspect alongside the profile")
    inspect.set_defaults(func=_cmd_inspect)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
