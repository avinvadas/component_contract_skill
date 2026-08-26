# macOS accessibility and interaction reference

Sources of authority: Apple's [Accessibility documentation](https://developer.apple.com/accessibility/) (`NSAccessibility` protocol for AppKit; shared SwiftUI accessibility modifiers) and the macOS-specific sections of the [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/). Kept separate from `references/ios/ios-hig-accessibility.md` even though both are Apple platforms and SwiftUI's accessibility API is shared between them — macOS has interaction conventions that genuinely differ from iOS (a pointer, hover states, right-click, window chrome, a menu bar), and someone fixing an iOS-only detail shouldn't need to touch this file or vice versa.

**Last verified:** 2026-08-25

Consulted by SKILL.md's Phase 3 ("Component / structure resolution" section) and Phase 4 ("Accessibility API" section) whenever Q8 includes macOS.

---

## Accessibility API

- **SwiftUI apps**: the same accessibility modifiers as iOS (`.accessibilityLabel`, `.accessibilityValue`, `.accessibilityHint`, `.accessibilityAddTraits`) — see `references/ios/ios-hig-accessibility.md` for the trait vocabulary, which is shared.
- **AppKit apps**: the `NSAccessibility` protocol — accessibility roles (`NSAccessibilityButtonRole`, `NSAccessibilityCheckBoxRole`, `NSAccessibilityPopUpButtonRole`, etc.), `accessibilityLabel`, `accessibilityValue`, and `accessibilityChildren` for composite structures. This is AppKit's own role/attribute model, distinct from UIKit's trait-based one even though both ultimately serve VoiceOver.

## Component / structure resolution — where macOS genuinely diverges from iOS

Same action/interaction inputs (Q2/Q7) can resolve differently here because macOS assumes a pointer and persistent window chrome, which iOS doesn't:

| Consideration | macOS-specific behavior |
|---|---|
| Hover | A real interaction state exists (`:hover`-equivalent via `onHover`/`NSTrackingArea`) — document a hover state in §4.1 for macOS even if the iOS/Android equivalents of the same component have none, since touch has no hover. |
| Secondary actions | Right-click / secondary-click context menus (`NSMenu`) are a standard affordance for revealing contextual actions — a component with several optional actions may expose them via context menu on macOS while iOS exposes the same actions as visible buttons or a swipe action. |
| Modal presentation | macOS distinguishes **sheets** (attached to a specific window, blocking only that window) from standalone **windows** and **popovers** — a "modal" in the interview (Q2: opens/closes something) needs to resolve to the correct one of these three, not a single generic "modal" concept the way a web `<dialog>` might imply. |
| Menu bar | App-level or window-level commands may belong in the menu bar rather than in-window UI at all — relevant only for composite shells that represent whole-app or whole-window chrome, not for typical leaf components. |

## Layout adaptation (feeds §2.3 Adaptive Layout)

Auto Layout (AppKit) or SwiftUI's layout system, same mechanism as iOS. The distinguishing factor on macOS is **user-resizable windows** — a component's layout may need to adapt continuously across a wide range of window widths rather than snapping between a small number of discrete size classes, and split-view sidebars can be resized or collapsed by the user directly. Document adaptive conditions the same way as iOS (named conditions, not pixel breakpoints), but expect a wider practical range of conditions to matter given user-driven resizing.

## RTL (feeds §2.2 Order)

Same leading/trailing model as iOS — Auto Layout constraints and SwiftUI's `.leading`/`.trailing` alignment resolve based on layout direction. `NSApplication.userInterfaceLayoutDirection` exposes the resolved value when a component needs to branch explicitly.

## Motion (feeds §4 Appearance)

`NSWorkspace.shared.accessibilityDisplayShouldReduceMotion` is the reduced-motion signal on this platform.
