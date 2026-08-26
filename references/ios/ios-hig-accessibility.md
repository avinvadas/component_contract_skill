# iOS accessibility and interaction reference

Sources of authority: Apple's [Accessibility documentation](https://developer.apple.com/accessibility/) (`UIAccessibility`, SwiftUI accessibility modifiers) and the [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) for interaction conventions. This file is the iOS analog of the web's `wai-aria-patterns.md` + `html-semantics.md` + `css-layout-and-interaction.md` combined into one platform's cohesive standard — one concern (how iOS natively expresses structure, accessibility, layout adaptation, and directionality), independent of any specific design system built on top of it.

**Last verified:** 2026-08-25

Consulted by SKILL.md's Phase 3 ("Component / structure resolution" section) and Phase 4 ("Accessibility API" section) whenever Q8 includes iOS.

---

## Accessibility API

`UIAccessibility` is iOS's equivalent of ARIA — every accessible element needs a **trait**, a **label**, and current **value/state**, mirroring the "role, name, value" triad from WCAG 4.1.2:
- **Traits** (the role equivalent): `.button`, `.link`, `.header`, `.image`, `.searchField`, `.adjustable` (sliders/steppers), `.selected`, `.notEnabled`, `.updatesFrequently` (live-region equivalent).
- **`accessibilityLabel`** — the accessible name (equivalent to `aria-label`).
- **`accessibilityHint`** — supplementary guidance on what activating the element does (no direct ARIA equivalent; used sparingly).
- **`accessibilityValue`** — current state/value for controls that have one (a slider's position, a switch's on/off state).
- **Dynamic Type**: text must scale with the user's chosen text size; a component contract's typography-bearing zones should note whether they participate in Dynamic Type scaling (almost always yes) rather than fixed pixel sizes.
- **VoiceOver rotor**: custom rotor actions are the iOS equivalent of exposing extra navigable structure (e.g., "headings," "links") beyond linear swipe navigation — relevant for composite shells with internal navigation.

## Component / structure resolution

Where the web decision table resolves Q2 (action) + Q7 (interaction) to an HTML element, iOS resolves the same inputs to a native SwiftUI control or presentation style:

| Action / interaction | Native equivalent |
|---|---|
| Triggers an action, click/tap | `Button` |
| Toggles a setting | `Toggle` |
| Choose one from a list, always visible | `Picker` (wheel or segmented style) or a list with selection |
| Choose one from a list, opens on demand | `Picker` (menu style) or a sheet-presented list |
| Opens/closes something — full task, blocks the rest of the screen | `.fullScreenCover` |
| Opens/closes something — contextual, partial-height, dismissible | `.sheet` |
| Opens/closes something — lightweight, anchored to a source | `.popover` |
| Switches between content panels, in-place | `TabView` (tab-bar style) or `Picker`-driven content switch |
| Switches between content panels, drill-down | `NavigationStack` push |

A composite shell's root maps to whichever presentation/container owns it (`NavigationStack`, `TabView`, a custom container view); sub-components resolve independently via their own contracts, same ownership principle as the web decision table.

## Layout adaptation (feeds §2.3 Adaptive Layout)

iOS's analog of container queries is **Size Classes** (`horizontalSizeClass` / `verticalSizeClass`: `.compact` / `.regular`), read from the environment at the view level — not the device, so a component adapts based on the space it's actually given (e.g., an iPad in split view reports `.compact` for the narrower pane), matching the web principle of container-relative rather than viewport-relative conditions. Auto Layout (UIKit) or SwiftUI's layout system handles the actual constraint resolution. Safe area insets are a layout concern specific to this platform — note in §4.2 Layout Policy whether a zone must respect them.

## RTL (feeds §2.2 Order)

iOS uses **leading/trailing** semantic layout, not left/right, by default — Auto Layout constraints and SwiftUI's `.leading`/`.trailing` alignment resolve to the correct physical side based on the layout direction automatically. This is the same logical-vs-physical principle as CSS logical properties (`references/web/css-layout-and-interaction.md`) and Android's start/end (`references/android/android-material-accessibility.md`) — record §2.2 Order in leading/trailing terms for this platform, not left/right. `UIView.userInterfaceLayoutDirection` / SwiftUI's `layoutDirection` environment value expose the resolved direction when a component needs to branch explicitly (e.g., mirroring a directional icon like a "back" chevron).

## Motion (feeds §4 Appearance)

`UIAccessibility.isReduceMotionEnabled` is the reduced-motion signal — same role as `prefers-reduced-motion` on the web. A state-transition animation documented in §5.2 should have a reduced-motion alternative for this platform exactly as it would for web.
