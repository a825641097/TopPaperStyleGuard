# Agent Skill

TopPaperStyleGuard ships a portable skill in [`skills/toppaperstyleguard`](../skills/toppaperstyleguard).

The skill tells agents to:

- learn from `topstyle.profile.json` or `references/profile.md`;
- revise toward abstract top-journal structure;
- avoid source-like wording;
- run `tpsg audit` before finalizing drafts, preferably with `--ignore-common-ngrams` when the guardpack was built from a large corpus;
- explain any overlap risk clearly.

The three artifacts have different jobs:

- `topstyle.profile.json`: machine-readable aggregate style profile.
- `topstyle.guard.json`: sensitive local/private overlap guardpack used by `tpsg audit`.
- `references/profile.md`: readable profile summary for agents; this is not enough to run overlap checks by itself.

Agent decision flow:

1. If `topstyle.profile.json`, `topstyle.guard.json`, and `references/profile.md` exist, read the reference and audit with the JSON artifacts.
2. If the user has a corpus and draft but no artifacts, build the artifacts before revision.
3. If only `references/profile.md` exists, revise structure only and state that overlap was not checked.
4. If the draft is pasted text, ask to save it to a file or create a temporary local file before audit.
5. If risk is `medium` or `high`, report sentence numbers first, rewrite from the underlying idea, then rerun audit.

## Codex

Copy the skill into your Codex skills directory:

```console
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/toppaperstyleguard "${CODEX_HOME:-$HOME/.codex}/skills/toppaperstyleguard"
```

## Claude Code and Other Agents

Use the same folder as a skill bundle where supported, or point the agent directly at:

```text
skills/toppaperstyleguard/SKILL.md
```

If you generated a project-specific profile reference, keep it at:

```text
skills/toppaperstyleguard/references/profile.md
```

## Recommended Prompt

```text
Use $toppaperstyleguard to revise this draft toward top-journal structure. Preserve my claims and evidence, avoid source-like phrasing, and run tpsg audit with the local profile and guardpack before finalizing.
```

Path-specific version:

```text
Use $toppaperstyleguard on drafts/introduction.md.
Read skills/toppaperstyleguard/references/profile.md if present.
Audit with --profile topstyle.profile.json and --guard topstyle.guard.json.
Preserve my claims and evidence. Do not imitate source wording.
If audit risk is medium or high, rewrite the flagged draft sentences from scratch and rerun the audit before finalizing.
```
