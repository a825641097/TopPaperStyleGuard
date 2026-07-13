# Profile Reference Placeholder

Generate a project-specific reference with:

```console
tpsg build papers/top-journal-corpus \
  --profile-out topstyle.profile.json \
  --guard-out topstyle.guard.json \
  --skill-reference skills/toppaperstyleguard/references/profile.md
```

Agents should treat this file as structural guidance only. It must not contain source sentences from the corpus.
