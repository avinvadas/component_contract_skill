---
component: Badge
version: 1.0
status: Draft
last_updated: 2026-09-07
platforms: [Web]
---

# Component Contract: Badge

## Design Intent

A small pill-shaped label that displays a status, category, or count, appearing attached to other components or inline in text.

---

## Structure

### 2.1 Semantic Markup

A non-interactive status indicator whose content may update without user action.

Each platform's native equivalent:

| Platform | Tag / Control | Required | Notes |
|---|---|---|---|
| Web | `<div role="status">` | Yes | `role="status"` carries implicit `aria-live="polite"` and `aria-atomic="true"`, ensuring screen readers announce content changes as they occur without requiring focus movement. |

### 2.2 Composition Zones

*(Shared — cardinality and position are intent, not implementation.)*

> **Cardinality** — how many instances of a zone are valid:
> - `1` — exactly one, required
>
> **Order:**
> - `Fixed` — must appear in the documented position; may be restyled but not repositioned

| Zone | Purpose | Cardinality | Accepts | Order | Absent behaviour |
|------|---------|-------------|---------|-------|-----------------|
| Label | The badge's visible text or numeric count | 1 | Text content (string or number) | Fixed — centred within badge | Invalid — a badge without a label has no content to convey |

---

## Appearance

### 3.2 Visual Variants

> Switches which visual style is applied. These select a visual mode — they are not token values.

| Prop | Values | Default | Description |
|------|--------|---------|-------------|
| `size` | `sm` \| `md` \| `lg` | `md` | Controls overall badge dimensions: padding, font size, and border-radius scale. Resolved dimensional values (padding, font-size, height) not provided — flag for confirmation. |
| `variant` | `neutral` \| `info` \| `success` \| `error` | `neutral` | Applies the semantic colour palette for the badge's surface and text. Token bindings pending — see §4.3.2. |

### 4.1 Interaction States

No interaction states beyond default — the badge is non-interactive. Visual appearance is entirely determined by the `variant` prop (§3.2) and the label's text content (§2.2); no user-triggered state change is possible.

### 4.3 Design Tokens

#### 4.3.1 Token Strategy

Badge owns its surface and text colour tokens, scoped per `variant`. The label zone contains plain text with no token of its own; no tokens are delegated to sub-components.

#### 4.3.2 Token Map

[Source: description only]

> Token map pending — no design source was provided. Supply a Figma node URL, Storybook URL, or CSS/token file to complete this section.

The designer volunteered that the token tree is color-prefixed — for example, `color-surface-neutral`. This indicates surface tokens follow a `color.surface.{variant}` canonical pattern. This has not been confirmed against a source file; it is recorded here as a pointer for when the token source is provided.

---

## Behavior

### 5.1 Interactions

None — the badge accepts no user input. It is display-only; the consumer is responsible for updating its content and `variant` prop externally.

### 5.2 State Machine

None — badge holds no internal state. Content, `size`, and `variant` are fully externally supplied.

### 5.3 Events Emitted

None.

### 5.4 Events Received

None.

---

## Accessibility

### 6.1 Roles & Attributes

**Root:** must be announced as a live status region so that assistive technology reads updated content without requiring focus movement.

Each platform's implementation:

| Platform | Attributes | Notes |
|---|---|---|
| Web | `role="status"` | Per WAI-ARIA, `role="status"` carries implicit `aria-live="polite"` and `aria-atomic="true"`. No explicit `aria-label` is required — the badge's text content is its announced value. |

### 6.2 Keyboard / Gesture Navigation

*(Shared — badge is display-only on all platforms.)*

| Key / Gesture | Behaviour |
|---|---|
| None | Badge is not focusable and accepts no keyboard input. |

### 6.3 Focus Management

*(Shared — no focus management applies to a non-interactive element.)*

- **Focus trap:** No — badge is non-interactive.
- **Tab order:** Badge is not included in the tab sequence (no `tabindex`).
- **On open:** Not applicable — badge is a persistent layout element, not an overlay.
- **On close:** Not applicable.

### 6.4 Screen Reader / Assistive Technology Expectations

*(Shared — live region behaviour is identical across all targeted platforms.)*

- **On reach:** Badge is not focusable; it is not announced on tab navigation. When a screen reader browses the page, it reads the badge's text content as static text within its surrounding context.
- **On activation:** Not applicable — badge is not interactive.
- **On state change:** When the badge's text content changes, `role="status"` triggers a polite live region announcement of the new content without requiring the user's focus to move.
- **On error / empty:** No error or empty state is defined for this component (no states confirmed beyond default — see §4.1).
