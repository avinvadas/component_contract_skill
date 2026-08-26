# CSS layout and interaction reference

Sources of authority: [CSS Containment Module Level 3 — Container Queries](https://www.w3.org/TR/css-contain-3/), [CSS Logical Properties and Values Level 1](https://www.w3.org/TR/css-logical-1/), [Selectors Level 4](https://www.w3.org/TR/selectors-4/) (`:focus-visible`, `:dir()`), and the `prefers-reduced-motion` media feature ([Media Queries Level 5](https://www.w3.org/TR/mediaqueries-5/)). This file covers CSS mechanisms the contract format assumes but never names outright. It is one concern — how CSS actually implements the layout/interaction/directionality behaviors a contract describes — kept separate from the DOM event/testing concern in `references/web/dom-events-model.md` and from token file formats in `references/design-tokens-format.md`.

**Last verified:** 2026-08-25

Consult this file from **Phase 3** (§2.2 Order, §2.3 Adaptive Layout) and **Phase 4/5** (§4.1 Interaction States, §6.3 Focus Management).

---

## Container queries (feeds §2.3 Adaptive Layout)

§2.3's instruction — "container-relative, never viewport-relative," conditions named by the design system, no pixel values or media query syntax — describes CSS Container Queries by behavior without naming the mechanism. Know what it actually is so the conditions you record are implementable:

- A container query needs an ancestor opted in via `container-type` (`inline-size`, `size`, or `normal`) and, optionally, `container-name`.
- `@container [name] (condition) { ... }` then queries that ancestor's size — most commonly `min-width`/`max-width` against its inline size, occasionally `aspect-ratio`.
- This is fundamentally different from a media query, which only ever sees the viewport — a component queried by container size behaves consistently regardless of where it's placed on the page, which is exactly why §2.3 insists on it.
- A design system's named conditions (e.g., "Compact," "Comfortable") are a mapping the *system* owns onto real `@container` width ranges — the contract records the condition names and what changes under each, not the breakpoint values themselves (those belong to the token/config layer, same reasoning as never inventing a token value).

## Interaction pseudo-classes (feeds §4.1 Interaction States, §6.3 Focus Management)

The states named in §4.1 (default, hover, focus, active, disabled, error, selected) map onto real CSS selectors, and one distinction matters enough to get wrong constantly:

- **`:hover`** — pointer is over the element. No keyboard equivalent; never the sole indicator of an interactive affordance (see WCAG 1.4.13 in `references/web/wcag-mapping.md`).
- **`:focus`** — matches whenever the element has focus, regardless of input method (mouse click, keyboard, or programmatic).
- **`:focus-visible`** — matches only when the browser's heuristic determines focus should be visibly indicated (typically: keyboard navigation, not a mouse click). This is what §6.3's "Focus Management" and the WCAG 2.4.7 mapping actually depend on — styling the visible focus ring on `:focus-visible` rather than bare `:focus` is what avoids showing a focus ring on every mouse click while still showing one for keyboard users. If a contract's §4.1 lists a "focus" state, note in the contract which selector it's meant to bind to; don't let it default to `:focus` by omission.
- **`:focus-within`** — matches a container when any descendant has focus. Relevant for composite shells (e.g., a search field wrapper that should look "focused" when its inner `<input>` has focus).
- **`:active`** — matches during activation (pointer down, or keyboard activation per browser behavior). Momentary; not a state that persists in the state machine (§5.2).
- **`:disabled`** — only matches elements using the native `disabled` attribute (see `references/web/html-semantics.md` for `disabled` vs. `aria-disabled`). An element disabled only via `aria-disabled` needs a corresponding attribute selector or class, not `:disabled`.
- **`:checked`** — native checkbox/radio state; a custom-styled equivalent needs an attribute selector (`[aria-checked="true"]`) instead, since `:checked` only applies to the native form elements.

## CSS Logical Properties and RTL (feeds §2.2 Order)

The `dir` attribute (HTML) establishes directionality and drives the native bidi algorithm for text and some default alignment, but it does **not** make component-authored layout (margin, padding, positioning, border) flip automatically. Physical properties — `margin-left`, `padding-right`, `left`/`right`, `text-align: left`/`right` — ignore `dir` entirely. Only two things respond to it:

1. Flexbox/Grid main-axis behavior (`flex-direction: row` visually reverses under `dir="rtl"`).
2. **CSS Logical Properties** — `margin-inline-start`/`-end`, `padding-block`, `inset-inline-start`, `border-inline-start`, `text-align: start`/`end` — which resolve to the correct physical side based on `direction` and `writing-mode` at render time.

This is why §2.2's "Order" column should be recorded in **logical**, not physical, terms whenever the target design system supports RTL locales: `Fixed — top-right` should be written as `Fixed — block-start, inline-end` (or in plain language, "top edge, trailing edge") so the implementer reaches for `inset-inline-end` rather than hardcoding `right`, which would sit on the wrong side once `dir="rtl"` is set. If the design system is confirmed LTR-only, physical terms are fine — don't add RTL ceremony to a system that doesn't need it; ask or infer from context rather than defaulting to logical-properties phrasing unconditionally.

`:dir(rtl)` / `:dir(ltr)` (Selectors Level 4) lets a stylesheet select on resolved directionality without JS — relevant only when `dir="auto"` leaves direction unknown until content is evaluated; most design systems set `dir` explicitly at a high level and never need this.

## Motion (feeds §4 Appearance)

Nothing in the current phases addresses motion, and most real design systems have a motion token category (duration, easing) plus a reduced-motion policy:

- `prefers-reduced-motion: reduce` is a media feature reflecting a user's OS-level setting. Any animation or transition tied to a state change (open/close, loading spinner, auto-dismiss countdown) should have a reduced-motion alternative — typically an instant state change or a much shorter/simpler transition, never nothing at all if the motion was conveying information (e.g., a loading spinner still needs *some* indication that loading is happening).
- If the design system exposes motion tokens (duration, easing curve), they belong in §4.3 Token Map like any other token — don't treat motion as exempt from the "never invent a token name" rule.
- Record which state transitions are animated in §5.2 State Machine (the *transition* itself is behavior); record the resolved duration/easing tokens and the reduced-motion fallback in §4.3.

