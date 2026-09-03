# macOS (Apple HIG) platform conventions

Source of authority: Apple's Human Interface Guidelines' macOS-specific sections — behavioral/compositional conventions only, never colors, spacing, or motion values. See `macos-hig-accessibility.md` in this folder for the accessibility-API layer. Where a convention is shared with iOS, see `ios/ios-platform-conventions.md` instead of duplicating it here — this file covers what's genuinely different on the desktop.

**How to use this file: cite, never assume.** Per Phase 1's cite-and-confirm rule — surface as a confirmable default within the question already being asked, never write it into a contract unconfirmed.

**Last verified:** 2026-09-03

## Ephemeral surface lifecycle (feeds Q3's dismissal follow-up, §3.3, §5.2)

- **No HIG-defined in-app toast/snackbar pattern**, same situation as iOS — macOS apps that want one are building a custom convention, not following a documented default. System-level Notification Center banners exist but are OS-owned, not something an in-app component contract can assume access to or model itself on.
- **`NSAlert`-style dialogs require explicit dismissal** and follow a precise, well-established button-order convention: the default (typically affirmative) action sits at the far trailing edge, Cancel to its left; `Return`/`Enter` triggers the default action, `Escape` triggers Cancel. Worth citing explicitly if a component's footer action order or keyboard behavior is left unconfirmed.

## Window & composition conventions (feeds §2.1, §2.2, §4.2)

- **A sheet on macOS is window-modal, not app-modal.** It's attached to and blocks only the window it's presented from (visually, it drops from that window's title bar) — other windows in the same app stay fully interactive. This is a real fork from iOS's typical single-window assumption: a component's "blocks interaction with the rest of the page" language needs a macOS-specific caveat ("the rest of *this window*") rather than being carried over unchanged.
- **Multiple simultaneous windows are a normal, expected pattern** on macOS, unlike iOS/Android's effectively single-window model — relevant whenever a component's contract talks about "the app" as if there's only one surface to block or return focus to.
- **The menu bar is a persistent, separate surface from any in-app UI.** A component that duplicates a menu-bar command (e.g., a custom "Preferences" trigger) is worth flagging for redundancy, and a context menu should not be assumed to replace a corresponding menu-bar item.

## Navigation & gesture conventions (feeds §5.1, §6.2)

- **There's no macOS equivalent to iOS's system-wide edge-swipe-to-go-back gesture inside an app's own navigation.** Trackpad swipe-between-pages exists as a systemwide feature in some contexts (e.g., browser history) but isn't a general in-app navigation convention the way it is on iOS — don't assume a swipe-back gesture exists for a macOS component just because an iOS counterpart has one.
- **Keyboard interaction expectations are stronger by default than on iOS/Android.** `Tab`/`Shift+Tab` focus-ring cycling, `Escape` dismissing the frontmost sheet/popover, and `Cmd+W` closing the frontmost window are all near-universal user expectations — worth confirming a component's §6.2 doesn't silently omit keyboard paths that would be assumed present on this platform specifically.
