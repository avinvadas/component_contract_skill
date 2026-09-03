# iOS (Apple HIG) platform conventions

Source of authority: Apple's Human Interface Guidelines, the behavioral/compositional parts — not SF Symbols, not Apple's color system, not its type scale or motion curves. Those are Apple's own *visual* opinions and belong to Phase 2 or nowhere, never to this file. See `ios-hig-accessibility.md` in this folder for the separate accessibility-API layer.

**How to use this file: cite, never assume.** Surface the relevant fact as part of the question already being asked, worded so the designer confirms or overrides it — per Phase 1's cite-and-confirm rule, this file never writes a fact into a contract on its own.

**Last verified:** 2026-09-03

## Ephemeral surface lifecycle (feeds Q3's dismissal follow-up, §3.3, §5.2)

- **iOS has no HIG-defined native "toast/snackbar" pattern.** Unlike Android, Apple's guidelines don't specify a transient, auto-dismissing banner control — apps that want one are building a custom pattern, not following a documented platform convention. Worth surfacing explicitly rather than assuming iOS "has one the same way Android does": if the interview describes a Toast/Snackbar-shaped component targeting iOS, there's no platform default to depart from, only the design system's own choice.
- **`UIAlertController` (`.alert` style) requires explicit dismissal — it never auto-dismisses.** It's for a decision the user must make, not a status update; a component modeled as "shows information, updates on its own" that also targets iOS as an alert is a mismatch worth flagging.
- **A sheet's interactive swipe-down dismissal is on by default** and has to be deliberately turned off (`.interactiveDismissDisabled()`), typically only for a flow with unsaved-changes protection — worth confirming when a sheet's dismissal follow-up doesn't mention swipe-down at all, since its absence is the exception, not the default.

## Window & composition conventions (feeds §2.1, §2.2, §4.2)

- **Four named modal presentation styles, not a general "modal" concept:** `.sheet` (partial-height, interactive dismiss, the default), `.fullScreenCover` (blocks interactive dismiss unless the app opts in), `.popover` (anchored to a source, common on iPad/regular width), `.alert` (short, decision-only, no partial-height concept at all). A component's §2.1 root resolution should land on one of these specifically, not a generic "presents modally" — if the interview's answer doesn't clearly indicate which, that's worth a follow-up rather than a default guess.
- **`presentationDetents` governs height only, never width** — see the caution already in `ios-hig-accessibility.md`'s layout-adaptation section; a width constraint at a given size class needs a separate mechanism.
- **Safe area insets are a real platform expectation for any full-bleed content**, not an optional nicety — worth naming in §4.2 Layout Policy when a component's root is edge-to-edge.

## Navigation & gesture conventions (feeds §5.1, §6.2)

- **Edge-swipe from the left edge is the system back gesture** inside a navigation stack — a component that intercepts left-edge gestures for its own purpose (e.g., a custom drawer) is overriding a system convention, worth flagging rather than silently accepting.
- **Pull-to-refresh at the top of a scrollable list** is a near-universal convention for refreshable content — relevant context if the component being contracted is itself a scrollable list/collection.
