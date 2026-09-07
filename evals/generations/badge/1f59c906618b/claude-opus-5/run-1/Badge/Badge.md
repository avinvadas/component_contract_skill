---
component: Badge
version: 1.0
status: Draft
last_updated: 2026-09-07
platforms: Web
---

# Component Contract: Badge

## Design Intent

A small pill-shaped label that displays a status, category, or count, appearing attached to another component or inline within running text.

---

## Structure

### 2.1 Semantic Markup

A non-interactive piece of content that labels or counts something, and which may sit inside a line of text. It has no action of its own and is never a control.

Each platform's native equivalent:

| Platform | Tag / Control | Required | Notes |
|---|---|---|---|
| Web | `<span>` — plus `role="status"` on the same element when the instance's content updates in place after first render (see Root element choice below) | Yes | `<span>` rather than `<div>`: Q1 states the badge appears inline in text, and per `references/web/html-semantics.md`'s content-model categories a `<div>` is flow content that cannot legally be a child of phrasing content (e.g. inside a `<p>`). `<span>` is the only generic element valid in both an inline and a block context, so it satisfies both of Q1's stated placements with one element. The element carries no semantics of its own, which is correct here — the badge is not a landmark, list, or figure. |

> **Root element choice:** Two valid configurations, chosen by whether a given instance's content changes after it is first rendered — not by which platform it is on.
>
> - **Content updates in place** (a count that increments, a status that changes from "Pending" to "Approved"): `<span role="status">`. Q4 states the badge updates on its own, and `role="status"` is implicitly `aria-live="polite"`, so the change is announced without moving focus. `references/web/wai-aria-patterns.md` names "3 items in cart" as the canonical `status` case, and `references/web/wcag-mapping.md` maps exactly this to WCAG 4.1.3 (Status Messages), which cites "cart count" directly. `role="alert"` is deliberately **not** used — a badge is advisory, not urgent, and `alert` would interrupt the screen reader on every change.
> - **Content is fixed for the badge's lifetime** (a category tag such as "Design" that is set once and never rewritten): plain `<span>`, no live-region role. Marking static content as a live region risks spurious announcements when the surrounding view re-renders, and there is no status change to announce.
>
> Q1 names three content kinds — status, category, and count — with genuinely different update behaviour, which is why this resolves per instance rather than once for the component. **The interview did not establish how a consumer selects between these two configurations** (an explicit prop, or inferred by the implementation from whether content is re-supplied). No prop has been invented for it here; flag for confirmation — see §3.3.

*(No per-zone markup blocks: Q6 names a single zone, the label, which is plain inline content with no independent semantic identity — no control, no heading, no separately-named region. Its markup is the root element's own text content.)*

### 2.2 Composition Zones

> **Cardinality** — how many instances of a zone are valid:
> - `1` — exactly one, required
>
> **Order:**
> - `Fixed` — must appear in the documented position; may be restyled but not repositioned

| Zone | Purpose | Cardinality | Accepts | Order | Absent behaviour |
|------|---------|-------------|---------|-------|-----------------|
| Label | Displays the badge's content — a status, a category, or a count | `1` | Text or a number, as plain content. No sub-components — Q5 confirms the Badge stands alone, so nothing here is delegated to another contract. | `Fixed` — the sole zone, centred within the badge on both axes | N/A — cardinality is `1`, so absence is not a valid state. A badge with no content has nothing to convey and is not rendered. |

*(§2.3 Adaptive Layout is omitted: Q8 confirms the layout is identical regardless of available space.)*

*(§3.1 Layout Props is omitted: Q8 confirms no layout flexibility — no direction flip, no size/alignment props, no compact or overflow mode.)*

### 4.2 Layout Policy

Fixed rules, always enforced, not configurable via props:

- **Label centring** — the label is centred within the badge on both axes, in every size and every variant (Q6).
- **Pill shape** — the badge's corner radius is fully rounded, so its ends are semicircular regardless of content length (Q1: "pill-shaped"). The resolved radius value is unestablished — see §3.2 and §4.3.2.

**Not established by the interview — flag for confirmation:** what happens to a label longer than the badge's intended width. Truncation, wrapping, and unbounded growth are all plausible and produce visibly different components; no source covers this, so nothing is asserted here rather than picking one.

---

## Appearance

### 3.2 Visual Variants

> Switches which visual style is applied. These select a visual mode — they are not token values.

Q7 supplied the value sets for both variants. It did not supply the **prop names** or the **defaults**; the names below are this contract's own labels for the sets the designer named, and both defaults are recorded as unestablished rather than assumed.

| Prop | Values | Default | Description |
|------|--------|---------|-------------|
| `size` | `sm` \| `md` \| `lg` | Not established — flag for confirmation | **Dimensional variant.** Selects the badge's scale. **No resolved values were provided for any of the three** — height, padding, font size, and corner radius are all unknown, because the token source was description-only (Q9). The enum is complete; the values it maps to are not. Do not implement from this row alone — see §4.3.2. |
| `variant` | `neutral` \| `info` \| `success` \| `error` | Not established — flag for confirmation | Semantic colour style. Each value selects a surface/text colour pairing; those pairings resolve to design tokens that are pending — see §4.3.2. Purely stylistic, so no dimensional value is missing here beyond what `size` already covers. |

### 4.1 Interaction States

**Default only.** Q9 confirms no states beyond default, and Q4 confirms no direct interaction — the badge is not focusable and is not a pointer target, so `:hover`, `:focus-visible`, `:active`, and `:disabled` have no meaning for it and no treatment is defined. There is no focus indicator to specify (§6.3), and no state is driven by a behavioural prop, because none exist (§3.3).

Content changing is not an interaction state — it is a content update, handled in §2.1's live-region configuration and §6.4.

### 4.3 Design Tokens

#### 4.3.1 Token Strategy

The Badge stands alone (Q5), so it owns every visual property it uses — nothing is delegated to a child contract. It consumes two families:

- **Colour**, per `variant` — a surface colour and a text colour for each of `neutral`, `info`, `success`, `error`.
- **Dimension**, per `size` — height/padding, font size, and corner radius for each of `sm`, `md`, `lg`.

Note per `references/web/wcag-mapping.md` (WCAG 1.4.3 / 1.4.11): each variant's surface/text pairing must resolve to a contrast-compliant pair in the design system's own token tree. This contract does not set contrast ratios — that is a token-definition concern upstream of it.

#### 4.3.2 Token Map

**Source: description only (Q9).** No Figma node, Storybook story, or token file was supplied.

> **Token map pending** — supply a Figma node URL, Storybook URL, or CSS/token file to complete this section.

**Canonical naming form.** The designer volunteered, unprompted, that the token tree is `color-` prefixed. That establishes the prefix this component's colour tokens will be recorded under once a source is supplied. Two limits on what that licenses:

- The illustrative example given alongside it (`color-surface-neutral`) demonstrates the prefix's *shape*. It is **not** recorded as a binding for this component — no token name here has been confirmed against a real token tree, and inventing one from a prefix convention would be exactly the fabrication this section is pending to avoid.
- No `.claude/design-system-context.yml` exists in this working directory, and a Phase 0B scan found no token file, no platform manifest, and no design system to detect one from. So `tokens.naming_pattern` — the ordered slot list canonical paths follow — is **not** established. The `color-` prefix alone does not imply the rest of the path's slot order.

Every property below is unresolved. None is listed as a raw value either, because no raw values were provided:

| Property | Status |
|----------|--------|
| Surface colour (per `variant`: neutral, info, success, error) | Pending — no source |
| Text colour (per `variant`: neutral, info, success, error) | Pending — no source |
| Height / padding (per `size`: sm, md, lg) | Pending — no source |
| Font size (per `size`: sm, md, lg) | Pending — no source |
| Corner radius (per `size`: sm, md, lg) | Pending — no source; §4.2 fixes the shape as fully rounded, not the value |

*(No per-platform token naming table: only one platform is targeted, and no naming convention has been detected or locked.)*

---

## Behavior

### 3.3 Behavioral Props

**None established by the interview.** Q3 confirms the Badge takes no action and Q4 confirms no direct interaction, so there is no operational option, feature flag, or lifecycle timing to configure. The label's content is a composition zone (§2.2), not a behavioural prop, and `size`/`variant` are visual variants (§3.2).

One open item belongs here if it is resolved: §2.1's Root element choice depends on whether a given instance's content updates in place, and the interview did not establish how that is selected. If the design system wants it chosen per instance, that is a behavioural prop to add here. No prop has been invented for it — flag for confirmation.

### 5.1 Interactions

**None.** Q4 confirms no direct interaction: the badge is not clickable, not focusable, and not a drag or scroll target.

No pass-through or interception statement is needed, because Q5 confirms the Badge stands alone — there is no delegated zone whose interaction could pass through it.

### 5.2 State Machine

**None** — the Badge holds no internal state. Its content, `size`, and `variant` are all supplied by the consumer, and it re-renders when they change. "Updates on its own" (Q4) describes the badge's content being changed by the surrounding application, not the badge transitioning between states it manages itself.

### 5.3 Events Emitted

**None.** The Badge has no interaction to report (Q4) and no internal state transition to announce (§5.2), so there is nothing for a consumer to listen for.

### 5.4 Events Received

**None.** The Badge does not subscribe to any event. Its content changes because the consumer re-renders it with new content — it does not listen for an update signal of its own. This is the mechanism behind Q4's "updates on its own"; the accessibility consequence of that update is handled by §2.1's live-region configuration, not by an event this component receives.

---

## Accessibility

### 6.1 Roles & Attributes

**Badge root:** Must convey its text content to assistive technology as ordinary content in the reading order. When the instance's content changes in place, that change must additionally be announced without requiring focus to move — politely, so it never interrupts.

Each platform's implementation:

| Platform | Attributes | Notes |
|---|---|---|
| Web | **Updating content:** `role="status"` on the root `<span>` (implicitly `aria-live="polite"`, `aria-atomic="true"`). **Fixed content:** no role and no ARIA attributes — the `<span>`'s text content is exposed as-is. No `aria-hidden`, and no `tabindex` in either configuration. | Satisfies WCAG 4.1.3 (Status Messages) for the updating case, per `references/web/wcag-mapping.md`. `role="status"` is chosen over `role="alert"` deliberately: a badge is advisory, so it must wait for a pause rather than interrupt. Per `references/web/wai-aria-patterns.md`, the live region must already be present and marked live *before* the content changes — a badge rendered into the DOM at the moment its value first appears will not announce. `tabindex` is absent because the badge is not interactive (Q3, Q4); making it focusable would put a non-actionable stop in the tab order. |

**Accessible name of a numeric badge — flag for confirmation.** Q1 states the badge may show a count and may be attached to another component. A badge whose content is a bare number ("3") announces as "3", which conveys nothing on its own about what is being counted. The requirement is that the count's meaning be programmatically available — either by giving the badge itself a descriptive accessible name (e.g. `aria-label="3 unread messages"`, with the visible "3" then exposed only through that name), or by having the host component's own accessible name incorporate the count. **The interview did not establish which**, and the two produce materially different announcements, so neither is asserted here. This does not apply to a badge whose visible text is already self-describing ("Approved", "Design").

### 6.2 Keyboard / Gesture Navigation

**No keyboard or gesture interaction.** The Badge is display-only (Q3, Q4), so it is not focusable and does not appear in the tab order. There is no key or gesture that acts on it, and none is required — WCAG 2.1.1 applies to interactive affordances, and the Badge has none.

### 6.3 Focus Management

- **Focus trap:** No — the Badge is not focusable and contains nothing focusable.
- **Tab order:** Not present in the tab order. It carries no `tabindex`.
- **On open:** N/A — the Badge does not open or close.
- **On close:** N/A — the Badge does not open or close.

### 6.4 Screen Reader / Assistive Technology Expectations

- **On reach:** The badge's text content is announced as part of the surrounding reading order when a screen reader's virtual cursor passes over it. It is not announced "on focus", because it never receives focus (§6.3). In the updating configuration, `role="status"` is announced as a status region.
- **On activation:** N/A — the Badge cannot be activated (Q3, Q4).
- **On state change:** In the updating configuration, a change to the badge's content is announced politely, without moving focus, once the screen reader reaches a pause. In the fixed-content configuration nothing is announced, because nothing changes. A numeric badge's announcement is only meaningful if the accessible-name question in §6.1 has been resolved.
- **On error / empty:** No error state and no empty state exist — Q9 confirms no states beyond default, and §2.2 makes the label required, so a badge with no content is not rendered rather than rendered empty.
