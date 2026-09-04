# Android accessibility and interaction reference

Sources of authority: [Android Accessibility developer documentation](https://developer.android.com/guide/topics/ui/accessibility) (`AccessibilityNodeInfo`, Jetpack Compose semantics) and the [Android Developers](https://developer.android.com/design) interaction/adaptive-layout guidance. This file is Android's analog of the web's ARIA + HTML + CSS-layout files combined — one cohesive platform standard, independent of any specific design system built on top of it (including Material Design itself, which this file deliberately does not cite as the source of interaction conventions, for the same reason the Windows file avoids citing Fluent).

**Last verified:** 2026-09-04

Consulted by SKILL.md's Phase 3 ("Component / structure resolution" section) and Phase 4 ("Accessibility API" section) whenever Q8 includes Android.

---

## Accessibility API

Compose exposes accessibility through the `Modifier.semantics { }` block; the View system exposes it through `AccessibilityNodeInfo`. Both ultimately drive TalkBack:
- **`Role`** (Compose) — `Role.Button`, `Role.Checkbox`, `Role.Switch`, `Role.RadioButton`, `Role.Tab`, `Role.Image` — the role-equivalent of ARIA roles.
- **`contentDescription`** — the accessible name (ARIA `aria-label` equivalent). Required on any element with no visible text.
- **`stateDescription`** — current state announced alongside the role/name (e.g., "expanded," "3 of 5 selected") — equivalent to ARIA's `aria-expanded`/`aria-selected`/`aria-checked` family.
- **`liveRegion`** (`Polite` / `Assertive`) — direct equivalent of `aria-live`.
- **`heading()`** (`Modifier.semantics { heading() }`) — marks text as heading-like for TalkBack's heading-navigation gesture. This is Android's counterpart to a Web `<h1>`–`<h6>` or iOS's `.accessibilityAddTraits(.isHeader)` — it carries no numbered level (Compose's heading concept is binary, heading or not, same as iOS's trait), so a Title-shaped zone's Android row should read "`Text` with `Modifier.semantics { heading() }`," never a level.
- **Touch target size** — Android's accessibility guidelines set a minimum touch target independent of visual size, same concept as the WCAG 2.5.8 mapping already documented for web (`references/web/wcag-mapping.md`).

## Component / structure resolution

Where the web decision table resolves Q2 (action) + Q7 (interaction) to an HTML element, Android resolves the same inputs to a native Compose component:

| Action / interaction | Native equivalent |
|---|---|
| Shows information only, updates on its own (status/live region) | A generic container (`Box`/`Surface`) with `Modifier.semantics { liveRegion = LiveRegionMode.Polite }` — use `Assertive` for urgent/error messages |
| Shows information only, static (never updates) | A generic container with `contentDescription` set on the content; no live region, no interactive semantics |
| Triggers an action, click/tap | `Button` |
| Toggles a setting | `Switch` |
| Choose one from a list, always visible | `RadioButton` group |
| Choose one from a list, opens on demand | `DropdownMenu` or `ExposedDropdownMenuBox` |
| Opens/closes something — full task | New destination via Navigation (full-screen composable) |
| Opens/closes something — centered, blocking, arbitrary content | `androidx.compose.ui.window.Dialog` — a bare modal host with no fixed slots, for a composite shell with its own composition zones (icon/title/body/footer). Material3's `AlertDialog` is a *different*, narrower archetype: fixed title/text/confirm-dismiss-button slots, not free-form content — don't reach for it just because the component is also a "dialog" by name. |
| Opens/closes something — contextual, partial-height | `ModalBottomSheet` — edge-anchored (slides from an edge), not centered. Don't conflate this with the centered-dialog row above; a component whose Design Intent says "centered overlay" belongs in that row even if both are colloquially "modals." |
| Opens/closes something — lightweight, anchored | `Popup` / `DropdownMenu` |
| Switches between content panels, in-place | `TabRow` + content swap |
| Switches between content panels, drill-down | Navigation destination push |

A composite shell's root maps to whichever container owns it (a `Scaffold`, a custom composable wrapping a navigation host); sub-components resolve independently via their own contracts.

**Basic dialog vs. full-screen dialog — two different close-affordance and
margin conventions, not two skins of the same thing.** Material's own
guidance treats these as distinct archetypes, and a component whose Android
manifestation is `androidx.compose.ui.window.Dialog` (the centered-dialog row
above) needs to land in the right one rather than borrowing the other's
chrome:
- **Basic dialog** (a centered, content-sized surface — the shape the
  centered-`Dialog` row above produces): no icon "X" close button. Dismissal
  is via an action button in the footer (e.g., "Cancel"), tapping the scrim,
  or the back gesture/button — never a corner icon. It also always keeps a
  minimum margin from the screen edges (Material specifies 24dp) even when a
  component's own `size`/max-width prop would otherwise exceed the available
  window width; a Basic dialog spanning edge-to-edge with no margin is
  visually indistinguishable from a full-screen one and reads as a mistake,
  not a compact layout.
- **Full-screen dialog** (used for a complex task/flow, not a short
  confirm/info surface): has a top-app-bar-style header, and *that's* where
  the icon "X" close button belongs.
A component's contract may confirm a cross-platform "Close button" zone that,
on Web/iOS, renders as an icon button — that doesn't automatically carry over
to Android if Android's own manifestation resolves to a Basic dialog shape.
Flag this explicitly rather than copying the icon-button treatment over by
default; see Modal.md's §2.1 Close button row for a worked example of
documenting the resulting per-platform difference.

## Layout adaptation (feeds §2.3 Adaptive Layout)

Android's analog of container queries is **Window Size Classes** (`compact` / `medium` / `expanded`, evaluated against the window's available width and height, not the physical device) — the same container-relative principle as the web: a component in a split-screen or foldable's smaller pane adapts to the space it's actually given. The legacy View system's equivalent is configuration qualifiers (`sw600dp` resource buckets), which are viewport/device-relative rather than container-relative — note which mechanism a given codebase uses, since they don't behave identically.

## RTL (feeds §2.2 Order)

Android uses **start/end**, not left/right, as the default layout semantic — `layout_marginStart`/`layout_marginEnd` in the View system, and Compose's padding/alignment APIs default to start/end resolution based on `LocalLayoutDirection`. This is the same logical-vs-physical principle as CSS logical properties (`references/web/css-layout-and-interaction.md`) — Android had this pattern well before CSS Logical Properties existed. Record §2.2 Order in start/end terms for this platform.

## Motion (feeds §4 Appearance)

The system "Remove animations" accessibility setting (exposed via `Settings.Global.ANIMATOR_DURATION_SCALE`, readable through `ValueAnimator.areAnimatorsEnabled()`) is the reduced-motion signal — same role as `prefers-reduced-motion` on the web.
