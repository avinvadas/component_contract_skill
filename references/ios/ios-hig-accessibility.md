# iOS accessibility and interaction reference

Sources of authority: Apple's [Accessibility documentation](https://developer.apple.com/accessibility/) (`UIAccessibility`, SwiftUI accessibility modifiers) and the [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) for interaction conventions. This file is the iOS analog of the web's `wai-aria-patterns.md` + `html-semantics.md` + `css-layout-and-interaction.md` combined into one platform's cohesive standard — one concern (how iOS natively expresses structure, accessibility, layout adaptation, and directionality), independent of any specific design system built on top of it.

**Last verified:** 2026-09-29

**Recheck:** 30 days — this source publishes no usable date and renders its guidance in JavaScript, so nothing automated can tell whether it moved. Shorter window, human review.

Consulted by SKILL.md's Phase 3 ("Component / structure resolution" section) and Phase 4 ("Accessibility API" section) whenever Q2 (Platform) includes iOS.

---

## Accessibility API

`UIAccessibility` is iOS's equivalent of ARIA — every accessible element needs a **trait**, a **label**, and current **value/state**, mirroring the "role, name, value" triad from WCAG 4.1.2:
- **Traits** (the role equivalent): `.button`, `.link`, `.header`, `.image`, `.searchField`, `.adjustable` (sliders/steppers), `.selected`, `.notEnabled`, `.updatesFrequently` (live-region equivalent).
- **`accessibilityLabel`** — the accessible name (equivalent to `aria-label`).
- **`accessibilityHint`** — supplementary guidance on what activating the element does (no direct ARIA equivalent; used sparingly).
- **`accessibilityValue`** — current state/value for controls that have one (a slider's position, a switch's on/off state).
- **Dynamic Type**: text must scale with the user's chosen text size; a component contract's typography-bearing zones should note whether they participate in Dynamic Type scaling (almost always yes) rather than fixed pixel sizes.
- **VoiceOver rotor**: custom rotor actions are the iOS equivalent of exposing extra navigable structure (e.g., "headings," "links") beyond linear swipe navigation — relevant for composite shells with internal navigation.

## The numbers the HIG publishes (feeds §6 Accessibility and §4.2 Layout Policy)

A requirement that says "meets the platform's minimum" is unverifiable until it says which number, so these are recorded here rather than left to whoever writes the contract. **The HIG states a default and a minimum, and they are not the same figure** — a control at 28×28 pt is within guidance while being well under the familiar 44×44.

| | Default | Minimum |
|---|---|---|
| Control size (iOS, iPadOS) | 44×44 pt | 28×28 pt |
| Type size (iOS, iPadOS) | 17 pt | 11 pt |

Which of the two a contract requires is a **policy decision, not a fact** — say which, in the contract, and say it in points. Spacing guidance is separate from size and is worth stating when a zone's padding is contractual: roughly 12 pt around a bezelled element, roughly 24 pt around an unbezelled one.

Contrast, as Accessibility Inspector applies it (WCAG Level AA; the HIG also names APCA as a second standard in use, without adopting it):

| Text size | Weight | Minimum ratio |
|---|---|---|
| up to 17 pt | any | 4.5:1 |
| 18 pt | any | 3:1 |
| any | bold | 3:1 |

Dynamic Type's own target is separate from all of the above: text should be enlargeable by **at least 200%** (140% on watchOS).

## Component / structure resolution

Where the web decision table resolves Q3 (action) + Q4 (interaction) to an HTML element, iOS resolves the same inputs to a native SwiftUI control or presentation style:

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

**`presentationDetents` is a height-only API — don't describe it as controlling width.** For a `.sheet`-presented component whose §2.3 condition also constrains width (a max-width at a wider size class, for instance), that's two separate mechanisms: `.presentationDetents([...])` picks which fraction of the screen's height the sheet occupies (`.medium` ≈ half, `.large` ≈ full, or a custom fraction/height), while a width cap needs a plain `.frame(maxWidth:)` (or equivalent) applied to the sheet's content. A phrase like "a fixed-width detent" conflates the two axes and reads as coherent English while describing something the API doesn't actually do — state the height behavior and the width behavior as two separate facts in §2.3/§4.2, even when they're both driven by the same named condition.

## RTL (feeds §2.2 Order)

iOS uses **leading/trailing** semantic layout, not left/right, by default — Auto Layout constraints and SwiftUI's `.leading`/`.trailing` alignment resolve to the correct physical side based on the layout direction automatically. This is the same logical-vs-physical principle as CSS logical properties (`references/web/css-layout-and-interaction.md`) and Android's start/end (`references/android/android-material-accessibility.md`) — record §2.2 Order in leading/trailing terms for this platform, not left/right. `UIView.userInterfaceLayoutDirection` / SwiftUI's `layoutDirection` environment value expose the resolved direction when a component needs to branch explicitly (e.g., mirroring a directional icon like a "back" chevron).

## Motion (feeds §4 Appearance)

`UIAccessibility.isReduceMotionEnabled` is the reduced-motion signal — same role as `prefers-reduced-motion` on the web. A state-transition animation documented in §5.2 should have a reduced-motion alternative for this platform exactly as it would for web.
