# Windows (Fluent/WinUI) platform conventions

Source of authority: Microsoft's Fluent Design System and WinUI component documentation — behavioral/compositional conventions only, never Fluent's own color system, Acrylic/Mica materials, or motion curves. See `windows-ui-automation.md` in this folder for the accessibility-API layer.

**How to use this file: cite, never assume.** Per Phase 1's cite-and-confirm rule — surface as a confirmable default within the question already being asked, never write it into a contract unconfirmed.

**Last verified:** 2026-09-03

## Ephemeral surface lifecycle (feeds Q3's dismissal follow-up, §3.3, §5.2)

- **Windows has a genuine platform-native answer here, unlike iOS/macOS: `InfoBar`.** It's a documented WinUI control specifically for in-app status messages, with named severities (Informational, Success, Warning, Error) and a choice between staying visible until dismissed or being closed programmatically — there's no "auto-dismiss after N seconds" default built into the control itself the way Android's Snackbar has SHORT/LONG presets. If a design system's Toast/Snackbar-shaped component targets Windows and expects auto-dismiss timing, that's a design decision layered on top of `InfoBar`, not something the platform default supplies — worth confirming rather than assuming a duration convention exists here the way it does on Android.
- **System toast notifications (via the Windows notification platform) are a separate, OS-owned surface** — they render in Action Center, are queued/stacked by the OS, and are a fundamentally different thing from an in-app `InfoBar` or a custom banner. Don't conflate the two when a component's purpose description says "toast" — confirm which one is actually meant.
- **Only one `ContentDialog` may be shown at a time per `XamlRoot`** — this is an actual API-level constraint (attempting to show a second while one is active fails or queues), not just a soft guideline. A component modeled as a WinUI dialog inherently can't stack with another instance of itself.

## Window & composition conventions (feeds §2.1, §2.2, §4.2)

- **`ContentDialog` favors up to three actions** (Primary, Secondary, Close), each with a named semantic role rather than being an arbitrary N-button footer — worth flagging if an interview's footer composition for a Windows-targeted dialog describes more than three, or doesn't distinguish which action is primary.
- **`Flyout` and `TeachingTip` are non-modal, anchored, light-dismiss-on-outside-click surfaces**, distinct from `ContentDialog`'s modal blocking behavior — if a component's Q3 answer says "opens or closes something" without specifying modal vs. non-modal, this is the fork Windows makes explicit that the interview should resolve too.
- **The title bar is a first-class customization surface in Fluent** (including extending app content into it) — relevant when a composite shell's root is a top-level window rather than an in-app overlay.

## Navigation & gesture conventions (feeds §5.1, §6.2)

- **`Escape` dismisses the frontmost dialog or flyout**; **`Alt+F4`** closes the frontmost window — both near-universal expectations worth confirming aren't silently absent from a component's §6.2.
- **`NavigationView` establishes two named top-level navigation conventions**: a collapsible pane (hamburger-triggered) for a longer or hierarchical destination list, and a top-tab layout for a short, flat one — relevant context, not a default to silently pick, if the component being contracted is itself a top-level navigation surface.
