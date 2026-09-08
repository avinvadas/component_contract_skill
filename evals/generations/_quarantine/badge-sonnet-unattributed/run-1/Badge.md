---
component: Badge
version: 1.0
status: Draft
last_updated: 2026-09-07
platforms: Web
---

# Component Contract: Badge

## Design Intent

Badge is a small pill-shaped label that displays a status, category, or count, and appears attached to other components or inline in text.

---

## Structure

### 2.1 Semantic Markup

A non-interactive, advisory status indicator whose text can change without requiring the user's attention or focus to move.

Each platform's native equivalent:

| Platform | Tag / Control | Required | Notes |
|---|---|---|---|
| Web | `<span role="status">` | Yes | `role="status"` implicitly carries `aria-live="polite"` and `aria-atomic="true"` per WAI-ARIA — the same pattern used for advisory, non-urgent updates like a cart count. No explicit `aria-live` attribute is needed. |

> **Root element choice:** `<span>` is used rather than `<div>` because the interview (Q1) states Badge "appears attached to other components or inline in text" — `<span>` is phrasing content and is valid inside inline text flow, whereas `<div>` is not. If a given instance is always used in a block-level layout context rather than inline text, `<div role="status">` is an equally valid manifestation of the same intent.

Badge has a single zone (the Label, §2.2) that is plain text/numeric content with no independent semantic identity of its own — it is already fully covered by the root element above, so it does not get a separate block here.

### 2.2 Composition Zones

> **Cardinality** — how many instances of a zone are valid:
> - `1` — exactly one, required
>
> **Order:**
> - `Fixed` — must appear in the documented position; may be restyled but not repositioned

| Zone | Purpose | Cardinality | Accepts | Order | Absent behaviour |
|------|---------|-------------|---------|-------|-----------------|
| Label | Displays the badge's content | 1 | Text or a number | Fixed — centred within the badge | Not applicable — the Label is required and always present; Badge has no valid empty state. |

### 2.3 Adaptive Layout

Not applicable. The interview (Q8) confirmed layout is always the same, with no adaptive behavior based on available space.

### 3.1 Layout Props

Not applicable. The interview (Q8) confirmed no layout flexibility (no direction flip, size growth/shrink via prop, alignment shift, or compact/overflow mode).

### 4.2 Layout Policy

- Badge is always rendered as a pill — fully-rounded corners (per Q1).
- The Label is always centred, both horizontally and vertically, within the badge (per Q6).
- Badge holds exactly one Label instance; no other zones exist (per Q6).

---

## Appearance

### 3.2 Visual Variants

| Prop | Values | Default | Description |
|------|--------|---------|-------------|
| size | `sm`, `md`, `lg` | Not specified — flag for confirmation | Controls the badge's overall scale (padding, font size, height). This is a dimensional variant; no resolved values (e.g. exact padding/height per size) were provided in the interview — flag for confirmation before implementation. |
| variant | `neutral`, `info`, `success`, `error` | Not specified — flag for confirmation | Semantic color style. Resolved token bindings are pending — see §4.3.2. |

### 4.1 Interaction States

None beyond default. The interview (Q9) confirmed no states beyond default — Badge has no hover, focus, active, disabled, loading, error, empty, or selected state. Its entire visual presentation is determined by the `size` and `variant` props (§3.2) applied to its single default appearance. Badge is non-interactive (Q3, Q4), so no user-input-driven states apply.

### 4.3 Design Tokens

#### 4.3.1 Token Strategy

Badge stands alone (Q5) and owns all of its own visual tokens directly — background color, text color, and border (if any) per `variant`, and sizing-related values per `size`. There are no child components to delegate any token ownership to.

#### 4.3.2 Token Map

Source: description only.

> Token map pending — no design source was provided. Supply a Figma node URL, Storybook story URL, or CSS/token file to complete this section.

The designer volunteered, unprompted, that this design system's token tree is color-prefixed (e.g. `color-surface-neutral`). No other part of the naming pattern (property/element/level ordering beyond the prefix) was confirmed. Once a real token source is supplied, canonical entries for Badge's `variant`-driven properties (background, text color, and any border) should be recorded under that `color-` prefix — e.g. a background token for the `neutral` variant would be expected to canonicalize as `color-surface-neutral`-shaped, not a platform-specific spelling like `--color-surface-neutral`. This fact has been persisted to `.claude/design-system-context.yml` (`tokens.prefix: color-`) so future components don't need to re-establish it.

No properties have confirmed token bindings yet:

| Property | Token |
|----------|-------|
| (none confirmed) | — |

No raw, unbound values were provided either — every visual property depends on `size`/`variant` resolution that is itself pending.

---

## Behavior

### 3.3 Behavioral Props

None. Badge has no configurable behavior beyond its visual variants (§3.2). The Label's content (text or number) is supplied as the zone's content (§2.2), not as a behavioral prop.

### 5.1 Interactions

None. The interview (Q3, Q4) confirmed Badge shows information only, with no direct user interaction — it is not clickable, draggable, or scrollable, and does not respond to hover in a behaviorally meaningful way. Badge has no delegated zones (it stands alone, Q5), so there is nothing to document as pass-through or intercepted.

### 5.2 State Machine

None — Badge has no internal state machine. Its rendered appearance is derived entirely from the `size` and `variant` props (§3.2) supplied by the consumer. Any change to the Label's content (§2.2) is managed externally by whatever data drives the badge (e.g. a count updating); Badge itself does not track or transition between states.

### 5.3 Events Emitted

None. Badge does not emit any custom events on any platform.

### 5.4 Events Received

None. Badge does not listen for any events; its content and appearance are driven entirely by props/content, not by events it receives.

---

## Accessibility

### 6.1 Roles & Attributes

**Root (Badge):** Must be announced as an advisory status region whose text can update without requiring focus to move, and must expose its visible text content as its accessible name.

Each platform's implementation:

| Platform | Attributes | Notes |
|---|---|---|
| Web | `role="status"` | Implicitly `aria-live="polite"` and `aria-atomic="true"` — no separate `aria-live` or `aria-atomic` attribute needs to be set. The visible text content of the Label (§2.2) itself serves as the accessible name; no `aria-label` is required. |

### 6.2 Keyboard / Gesture Navigation

| Key / Gesture | Behaviour |
|-----|-----------|
| (none) | No keyboard interaction is required. Badge is display-only (Q3, Q4) and is not part of the tab order. |

### 6.3 Focus Management

- **Focus trap:** No.
- **Tab order:** Badge is not focusable and does not appear in the tab order.
- **On open:** Not applicable — Badge is not a transient or openable surface.
- **On close:** Not applicable — Badge is not a transient or openable surface.

### 6.4 Screen Reader / Assistive Technology Expectations

- **On reach:** Not applicable — Badge does not receive focus directly; when encountered, it is read as part of the surrounding content flow (e.g. inline in text, or as part of an attached component's description).
- **On activation:** Not applicable — Badge is non-interactive.
- **On state change:** When the Label's content updates, the `role="status"` live region causes assistive technology to announce the new text automatically, without moving focus.
- **On error / empty:** Not applicable — Badge has no error or empty state (Q9); the Label is always present (§2.2 cardinality of `1`).
