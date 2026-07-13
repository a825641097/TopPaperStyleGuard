# Profile Reference Placeholder

Generate a project-specific reference with:

```console
tpl build papers/top-journal-corpus \
  --profile-out toplearn.profile.json \
  --guard-out toplearn.guard.json \
  --skill-reference skills/top-paper-learn/references/profile.md
```

Agents should treat this file as structural guidance only. It must not contain source sentences from the corpus.
