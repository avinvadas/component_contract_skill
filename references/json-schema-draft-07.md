# JSON Schema Draft 07 — keyword reference

Source of authority: [JSON Schema Draft 07 specification](https://json-schema.org/specification-links.html#draft-7). SKILL.md's Phase 6 is deliberately pinned to Draft 07 rather than the current Draft 2020-12 — this is a stated compatibility choice (Draft 07 has the widest tool support across validators, IDEs, and CI linters as of this writing), not an oversight. If a target team needs 2020-12 instead, see "Upgrading" below before changing the schema rules in SKILL.md.

**Last verified:** 2026-08-25

## Keywords used by this skill's schema generation

| Keyword | Use |
|---|---|
| `$schema` | Always `"http://json-schema.org/draft-07/schema#"` — declares the draft so validators interpret the rest correctly. |
| `$id` | The component's kebab-case identifier. Used as the base URI for any `$ref` resolution within a set of related schemas (a shell referencing sub-component schemas). |
| `title` | Component display name, human-readable. |
| `description` | Required on every property — copied verbatim from the contract's prose, not re-authored. |
| `type` | `"string"`, `"number"`, `"boolean"`, `"object"`, `"array"`. Every property needs exactly one (or an array of allowed types if genuinely polymorphic — rare for this use case). |
| `enum` | For Layout Props and Visual Variants — the closed set of values named in §3.1/§3.2. |
| `default` | From the contract's "Default" column, when stated. |
| `required` | Array of property names, at the object level — populated from §3.3 rows marked Required = Yes, and from §2.2 zones with Cardinality ≥ 1. |
| `minimum` / `maximum` | Only when the contract states numeric bounds explicitly — never inferred. |
| `minItems` / `maxItems` | From §2.2 Cardinality on array-shaped zones (e.g., `2+` tabs → `"minItems": 2`). |
| `items` | Describes the shape of array entries — either `{ "$ref": "..." }` (reference mode) or an inline `object` schema (inline mode), per what Q10's follow-up specified. |
| `$ref` | Points at another component's schema `$id` (or a local `definitions` entry) when a zone accepts a sub-component that already has its own contract/schema. |
| `definitions` | Draft-07's name for a local map of reusable sub-schemas referenced via `#/definitions/[name]`. (Note: 2020-12 renamed this to `$defs` — see Upgrading.) |
| `additionalProperties` | Not set by default (Draft 07 defaults to allowing additional properties). Only add `"additionalProperties": false` if the contract explicitly states the prop set is closed and no framework-injected props (e.g., `className`, `style`, `data-*`) need to pass through — setting it without checking this will break real-world usage in most component libraries. |

## What NOT to add

Per SKILL.md's Phase 6 rule ("never add validation rules not stated in the contract"), do not add on your own initiative:
- `pattern` (regex) unless the contract states a format constraint.
- `format` (e.g., `"date"`, `"uri"`) unless the contract's prop type is explicitly a date/URI and the team's format convention is known.
- `oneOf` / `anyOf` / `allOf` for conditional logic between props unless the contract's prose describes a real interdependency (e.g., "Footer zone requires at least one action button when present") — and even then, prefer the simplest construct that expresses it.

## Upgrading to Draft 2020-12

If a target design system's tooling requires the current draft instead of Draft 07, the changes needed are:
- `"$schema"` → `"https://json-schema.org/draft/2020-12/schema"`.
- `definitions` → `$defs` (both the declaration and every `$ref` pointing at `#/definitions/...` → `#/$defs/...`).
- `items` for tuple-validation changes shape (2020-12 uses `prefixItems` for positional tuples) — not relevant here since this skill only uses `items` for homogeneous arrays of one sub-component shape, which is unaffected.
- `unevaluatedProperties` becomes available as a stricter, composition-aware alternative to `additionalProperties: false` — useful if a schema is built via `allOf` composition, which this skill currently doesn't generate.

This is a one-time decision to make explicitly with whoever owns schema validation on the target team, not something to silently switch component-by-component.
