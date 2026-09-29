# Design token file formats

Source of authority: [Design Tokens Format Module 2025.10](https://www.designtokens.org/TR/2025.10/format/) — a **Final Community Group Report**, published 28 October 2025, which is the format's first stable version. It is published by the Design Tokens Community Group and is expressly **not a W3C Standard and not on the W3C Standards Track**; cite it as a community specification, never as a W3C recommendation. Alongside it, the older but still common formats it is meant to eventually replace. This file exists so **Phase 2 Path B** (coded reference token extraction) can recognize whatever shape a given design system's token files actually take, instead of assuming CSS custom properties are the only format. Nothing here is specific to any one design system — it's a map of the formats design systems commonly use.

Cite the dated `TR/2025.10/` URL and not the group's working draft. The old
`design-tokens.github.io/community-group/format/` address now redirects, twice, to a preview
draft that says of itself: do not refer to this document directly, and do not implement anything
in it. A version-pinned citation also dates itself, which is what lets the freshness check read
it instead of guessing.

**Last verified:** 2026-09-29

## Format 1: DTCG JSON

```json
{
  "color": {
    "surface": {
      "default": { "$value": "#F5F5F5", "$type": "color", "$description": "Default surface background" }
    }
  }
}
```

- Every property this format defines is prefixed with `$`. `$value` is **required**; `$type` and `$description` are optional.
- `$type` is one of exactly thirteen: `color`, `dimension`, `fontFamily`, `fontWeight`, `duration`, `cubicBezier`, `number` (the seven simple types), and `strokeStyle`, `border`, `transition`, `shadow`, `gradient`, `typography` (the six composite types, whose `$value` is an object of sub-values rather than a scalar).
  **`boolean` and `string` are not DTCG types**, though both appear in files in the wild — a file using them is using a dialect, so record what it says and don't treat the name as spec-defined.
- Nesting expresses grouping (`color.surface.default`); the token's full name is its path.
- Aliases reference another token by path in curly braces: `{ "$value": "{color.surface.default}" }`. When you encounter an alias, resolve it to the token name being referenced — don't treat it as a raw value.
- A `$type` set on a group applies to all tokens beneath it unless overridden. Resolution order is stated: a reference takes the resolved type of the token it points at; otherwise the type is inherited from the **closest** parent group that sets one.
- **`$extensions`** holds tool-, team- or vendor-specific data. Expect proprietary keys under it and do not read them as tokens — this is where a design system's own bookkeeping legitimately lives.
- **`$deprecated`** is `true`, `false`, or a string explaining what to use instead. A deprecated token is still a token: record it, and note the deprecation rather than dropping it.
- Detection: the file extension is `.tokens` or `.tokens.json`, and the MIME type `application/design-tokens+json` (falling back to `application/json`). A `$value` anywhere in a JSON tree is the surer signal, since plenty of real files are named `tokens.json` without following the spec.

## Format 2: Style Dictionary (pre-DTCG, still widespread)

```json
{
  "color": {
    "surface": {
      "default": { "value": "#F5F5F5", "type": "color", "comment": "Default surface background" }
    }
  }
}
```

Same shape, different key names: `value` instead of `$value`, `type` instead of `$type`, `comment` instead of `$description`. References use `{color.surface.default.value}` dot-path syntax rather than DTCG's bare path. Treat this as functionally identical to DTCG for extraction purposes — record the same `property | token name | resolved value` triple regardless of which key names the source file uses.

## Format 3: CSS custom properties

```css
:root {
  --color-surface-default: #F5F5F5;
}
.component {
  background: var(--color-surface-default);
}
```

- The declaration (`--token-name: value`) is the source of truth for the resolved value; the `var()` usage site is where you confirm the component actually consumes that token.
- A property with a literal value and no `var()` wrapper is unbound/raw — same rule as the Figma path: never invent a token name for it.

## Format 4: Tailwind config / utility classes

Tokens may live in a `theme` or `theme.extend` object in a Tailwind config (JS/TS), consumed via utility classes (e.g., `bg-surface-default`) rather than a `var()` call at the point of use. When the coded reference is a Tailwind-based component:
- Read the config file for the token's resolved value.
- Record the token name as the semantic key path in the config (`colors.surface.default`), not the utility class name — the class name is an application of the token, not the token's identity.

## Tiering conventions (primitive / semantic / component)

A common but not universal convention layers tokens in three tiers:
- **Primitive** — raw values with no semantic meaning (`gray-100`, `blue-500`).
- **Semantic** — meaning-bound aliases to primitives (`color-surface-default` → `gray-100`).
- **Component** — component-specific aliases to semantic tokens (`button-bg-primary` → `color-action-default`).

Not every design system uses all three tiers — some go straight from primitive to component, some have only one flat tier. When recording tier in the token map (Phase 2 Path B), infer it from the naming pattern and nesting depth of the source file rather than assuming three tiers exist. If the system's tiering is ambiguous or the source only exposes resolved values with no visible aliasing chain, note the tier as "unspecified" rather than guessing.

## What "unbound" means across formats

Across all four formats, a value counts as **raw/unbound** — never assigned an invented token name — when:
- CSS: a literal value with no `var()` wrapper.
- DTCG/Style Dictionary JSON: the property isn't present in the token file at all, or the component's styles reference a value that doesn't correspond to any `$value`/`value` in the file.
- Tailwind: an arbitrary-value utility (e.g., `bg-[#f5f5f5]`) rather than a theme-mapped class.

This mirrors the Figma path's "Apply variable" tooltip rule (see figma-variables-model.md) — the underlying principle (never fabricate a name for something that isn't actually bound to a token) is the same regardless of source format.
