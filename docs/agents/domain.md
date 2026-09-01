# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- `CONTEXT.md` at the repo root, if it exists
- `docs/adr/` for architecture decisions that touch the area you are about to work in

If these files do not exist, proceed silently. Do not flag their absence or suggest creating them up front. The domain-modeling flow creates them lazily when a term or decision is actually resolved.

## File structure

This repo uses the single-context layout:

```
/
├── CONTEXT.md
├── docs/adr/
├── pyschieber/
├── tests/
└── README.md
```

## Use the glossary's vocabulary

When your output names a domain concept, use the term as defined in `CONTEXT.md`. Do not drift to synonyms the glossary explicitly avoids.

If the concept you need is missing from the glossary, treat that as a signal: either you are inventing language the project does not use, or there is a real gap to note for the domain-modeling workflow.

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding it.

> Contradicts ADR-0001, but worth reopening because...
