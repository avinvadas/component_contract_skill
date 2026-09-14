# `system/` — the layer a contract draws from

`references/` holds **external standards**. A contract never reads them; they are the source
material from which this directory is authored, once.

| Directory | Owner | Changes when |
|---|---|---|
| `vocabulary/` | **shipped with the skill** | the format version bumps |
| `archetypes/` | **shipped, locally extensible** | an archetype is added or a platform guarantee changes |
| `templates/` | shipped as blanks | never — the design system fills copies |

**Why JSON and not YAML.** These files are read by the resolver and by every verifier, in
whatever language that verifier is written in. JSON parses everywhere with no dependency;
YAML would require a library on five platforms. The contract `.md` is where human-first
formatting matters — this directory is reference data for tools.

## The rule that keeps archetypes factual

From `v1-implicit-guarantees-catalogue.md`:

> an entry belongs here only if the platform provides it *automatically*, without the
> implementer doing anything.

So a bundle is an inventory of what a platform gives you free — and therefore what you must
reproduce if you substitute a generic view — not a view about good design. Every requirement
cites a `source`. A requirement with no source is an opinion, and opinions live in
`templates/policy.template.md`, which ships blank.

Where a requirement is **authored** rather than inherited — nothing is free anywhere, as with
tabs — it cites a published convention instead. Still not our opinion.
