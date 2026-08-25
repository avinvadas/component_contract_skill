# Figma variables data model

Source of authority: Figma's Variables feature (Collections, Modes, bound values) as exposed through the Figma REST API / Plugin API and, when available in the working environment, the Figma MCP server tools. This file exists so **Phase 2 Path A** extracts tokens from Figma reliably and structurally instead of depending on manually reading tooltips in a rendered page — a method that is slow, error-prone, and breaks if Figma's UI changes.

**Last verified:** 2026-08-25

## The data model

- **Variable**: a named value of type `COLOR`, `FLOAT` (numbers — spacing, radius, etc.), `STRING`, or `BOOLEAN`.
- **Collection**: a named group of variables (e.g., "Primitives", "Semantic Colors"). A file can have multiple collections.
- **Mode**: a named axis within a collection (e.g., "Light" / "Dark", or "Density: Compact" / "Comfortable"). Each variable in a collection has one value per mode.
- **Alias**: a variable's value can itself be a reference to another variable (e.g., a semantic-tier variable pointing at a primitive-tier one). When resolving a bound value, follow the alias chain and record the *token name*, not the alias mechanism.
- **Binding**: a node property (fill, stroke, corner radius, gap, padding, etc.) is either bound to a variable or holds a raw literal. Only bound properties correspond to design tokens; everything else is raw.

This maps directly onto the three-tier primitive/semantic/component convention described in design-tokens-format.md: Figma collections are frequently organized to mirror that tiering, but — same caveat as that file — don't assume all three tiers exist if the file's collection structure doesn't show them.

## Preferred extraction method: structured tool access

If a Figma MCP connection or equivalent API access is available in the working environment, use it instead of manual UI inspection:

- Retrieve the component node's variable bindings and resolved values directly (e.g., a `get_variable_defs` / `get_design_context`-style call scoped to the node).
- This returns, per property, the bound variable's name and its resolved value for the relevant mode — structurally, not by parsing a rendered tooltip.
- Cross-reference returned variable names against their collection to determine tier, exactly as you would from a token file's nesting (design-tokens-format.md).
- If the node has no binding for a property, the API returns the raw value only — treat this identically to the "Apply variable" case below: unbound, record the raw value, do not invent a name.

This method is authoritative when available: it reflects the actual bound variable, not a visual approximation of one.

## Fallback: manual inspection (no structured access available)

When no API/MCP access exists and the only option is visually inspecting the file in a browser:

- Inspect only the root element of the component being contracted — not its children (those have their own contracts).
- For each property, hover the small icon next to the value field in the right-side Design panel and read the tooltip:
  - **"Apply variable"** — no token is bound; record the raw numeric or hex value.
  - **A named token** (e.g., `color-surface-default`, `--ds-color-surface`) — record it exactly as shown.
- Check properties in this order: Auto layout gap → padding (all sides) → corner radius → fill (background) → stroke (color, width, position) → opacity → any fixed width or height.
- Navigate by opening the node's URL (it should arrive pre-selected) and scrolling the Design panel top to bottom.
- Never infer or invent a token name from what a value visually resembles — "Apply variable" showing means unbound, full stop.

## Modes and theming

If the component's tokens differ by mode (e.g., a different fill variable is bound per Light/Dark, or per density setting), and the design system's contract format is expected to document theming, record the token map per mode rather than collapsing to a single mode's values. Note explicitly which mode was inspected if only one was captured, so the contract doesn't silently imply mode-independence it doesn't have.
