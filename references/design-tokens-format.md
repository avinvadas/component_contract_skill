# Design token file formats

Source of authority: [Design Tokens Community Group (DTCG) format](https://design-tokens.github.io/community-group/format/), a W3C community group specification, plus the older but still common formats it's meant to eventually replace. This file exists so **Phase 2 Path B** (coded reference token extraction) can recognize whatever shape a given design system's token files actually take, instead of assuming CSS custom properties are the only format. Nothing here is specific to any one design system — it's a map of the formats design systems commonly use.

**Last verified:** 2026-08-25

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

- Value lives in `$value`, type in `$type` (`color`, `dimension`, `fontFamily`, `fontWeight`, `duration`, `cubicBezier`, `number`, `boolean`, `string`, or a composite type).
- Nesting expresses grouping (`color.surface.default`); the token's full name is its path.
- Aliases reference another token by path in curly braces: `{ "$value": "{color.surface.default}" }`. When you encounter an alias, resolve it to the token name being referenced — don't treat it as a raw value.
- A `$type` set on a group applies to all tokens beneath it unless overridden.

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
