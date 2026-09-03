# Android (Material Design) platform conventions

Source of authority: Material Design's own component specifications (material.io) and the platform behaviors they document for Android — not this skill's own inference. This file is **behavioral/compositional convention only**: it never states a color, a spacing number, an elevation value, a motion curve, or an icon — those are Material's own *visual* opinions, not universal facts about running on Android, and belong to Phase 2 (the target design system's own tokens) or nowhere, never to this file. See `android-material-accessibility.md` in this folder for the separate accessibility-API layer.

**How to use this file: cite, never assume.** Everything below is a documented platform convention, not a default this skill applies on its own. Per Phase 1's cite-and-confirm rule, surface the relevant fact as part of the question already being asked, worded so the designer confirms or overrides it — never write it into a contract as fact without an answer behind it.

**Last verified:** 2026-09-03

## Ephemeral surface lifecycle (feeds Q3's dismissal follow-up, §3.3, §5.2)

- **Snackbars queue — they don't stack or get silently replaced.** If a new Snackbar is triggered while one is showing, Material's convention is a FIFO queue: the current one finishes its lifecycle (shown, then dismissed) before the next one appears. Never simultaneously visible, and a newly-triggered one doesn't cut the current one short by default.
- **Two named duration presets, not a free-form number:** `SHORT` (~1.5s) and `LONG` (~2.75s), plus an `INDEFINITE` option that requires explicit dismissal (typically paired with an action). If a design system's interview answer gives a raw duration, it's worth confirming whether it's meant to map to one of these presets or is a deliberate departure.
- **Only one modal surface is expected at a time.** Android has no platform convention for stacking multiple dialogs, bottom sheets, or full-screen overlays — opening a second one while one is active is generally read as a bug, not a supported pattern, unless the design system explicitly intends a stack (e.g., a wizard).

## Window & composition conventions (feeds §2.2 Composition Zones, §4.2 Layout Policy)

- **Dialogs favor at most two action buttons** (a confirming and a dismissing action); a third or more is a documented anti-pattern in Material's own dialog guidance, not just a style preference — worth flagging if a design system's dialog composition calls for 3+.
- **Modal vs. persistent bottom sheets are different components in Material's own model**, not one component with a "modal" toggle — a modal bottom sheet dims and blocks the rest of the screen; a persistent one coexists with an active main surface. If an interview describes both behaviors for what's being modeled as a single component, that's worth surfacing as a real fork, not a variant.

## Navigation & gesture conventions (feeds §5.1, §6.2)

- **System Back dismisses the topmost open modal surface first**, before it does anything else (navigating back in the app's own stack, exiting the app). Any modal, bottom sheet, or drawer archetype should treat the system Back gesture/button as an implicit dismissal path, on top of whatever the interview names explicitly — worth confirming it wasn't left out of Q3's dismissal follow-up by omission.
- **Navigation Drawer vs. Bottom Navigation** are Material's two named top-level navigation conventions, chosen by destination count and hierarchy depth (Drawer for 5+ or nested destinations, Bottom Navigation for 3–5 flat top-level ones) — relevant context if the component being contracted is a top-level nav surface, not a hint to silently pick one over the other.
