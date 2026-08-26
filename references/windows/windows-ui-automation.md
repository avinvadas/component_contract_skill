# Windows accessibility and interaction reference

Source of authority: Microsoft's [UI Automation (UIA)](https://learn.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32) control pattern model. This file deliberately grounds component/structure resolution in UIA's control patterns rather than in Fluent Design System guidance — Fluent is Microsoft's own design system, and citing it here would break the same design-system-agnostic principle that keeps this skill from assuming any one system's conventions (the same reasoning that keeps `references/android/android-material-accessibility.md` from citing Material Design as the source of truth).

**Last verified:** 2026-08-25

Consulted by SKILL.md's Phase 3 ("Component / structure resolution" section) and Phase 4 ("Accessibility API" section) whenever Q8 includes Windows.

---

## Accessibility API

UIA's **control patterns** are conceptually the closest native analog to ARIA's role/pattern model of any platform in this set — each control exposes one or more patterns describing what it can do, rather than a single fixed role:

- **Invoke** — a simple action trigger (button-equivalent).
- **Toggle** — on/off state (checkbox/switch-equivalent), exposes `ToggleState` (On/Off/Indeterminate).
- **SelectionItem** + **Selection** — an item within a selectable set (radio button, list item, tab) and its container.
- **ExpandCollapse** — disclosure/accordion-equivalent, exposes `ExpandCollapseState`.
- **Value** — a control holding an editable value (text input-equivalent).
- **RangeValue** — a bounded numeric control (slider-equivalent), exposes `Minimum`/`Maximum`/`Value`.
- **Scroll**, **Grid**, **Table** — composite/structural patterns for scrollable regions and tabular data.

In XAML, these are wired up via `AutomationProperties.Name` (accessible name — the `aria-label` equivalent), `AutomationProperties.HelpText`, and `AutomationProperties.LiveSetting` (`aria-live` equivalent: Off/Polite/Assertive).

## Component / structure resolution

Resolve Q2 (action) + Q7 (interaction) to the UIA control pattern the native control must expose, not to a specific XAML control class (since a design system may implement its own custom control rather than using a stock one) — the pattern is the accessibility contract; the visual control is implementation:

| Action / interaction | Required control pattern |
|---|---|
| Shows information only, updates on its own (status/live region) | No control pattern applies — an implementation-defined container with `AutomationProperties.LiveSetting="Polite"` (`"Assertive"` for urgent/error messages) |
| Shows information only, static (never updates) | No control pattern applies — an implementation-defined container with `AutomationProperties.Name` set; `LiveSetting="Off"` |
| Triggers an action, click/tap | Invoke |
| Toggles a setting | Toggle |
| Choose one from a list, always visible | SelectionItem (per item) + Selection (container) |
| Choose one from a list, opens on demand | Expand/Collapse on the trigger, Selection/SelectionItem inside the popup |
| Collects input (text) | Value |
| Collects input (bounded numeric — slider/stepper) | RangeValue |
| Opens/closes something | ExpandCollapse (inline) or a distinct window/flyout (`ContentDialog`/`Flyout`-equivalent) for a modal/popover-style presentation |

**Mapping onto a component contract's §2.1 vs. §6.1:** Windows doesn't have a concrete control class the way Web/iOS/Android/macOS do — the table above *is* both the structural commitment and most of the accessibility contract at once. When populating a contract's §2.1 (Semantic Markup), put the required pattern in both the Role and Tag/Control columns (e.g. Role: `Invoke`, Tag/Control: `Implementation-defined — any control exposing the Invoke pattern`). The concrete wiring — `AutomationProperties.Name`/`HelpText`/`LiveSetting` and the pattern's own state (`ToggleState`, `ExpandCollapseState`, etc.) — is what actually belongs in §6.1; don't duplicate the pattern name as if it were new information there beyond naming which state property it exposes.

## Layout adaptation (feeds §2.3 Adaptive Layout)

The nearest analog to container queries is **adaptive triggers** tied to the window's (or a container's) width/height via `VisualStateManager` — a component defines named visual states and the conditions that switch between them, which maps directly onto the contract's "named condition → layout change" structure in §2.3.

## RTL (feeds §2.2 Order) — the messiest of the platforms covered here

`FlowDirection` (`LeftToRight` / `RightToLeft`) on a XAML element and its descendants controls mirroring, but unlike CSS logical properties or iOS/Android's leading/trailing-native APIs, XAML's `Margin`/`Padding` are still expressed as (Left, Top, Right, Bottom) — there is no first-class logical-property equivalent that auto-resolves per side the way `margin-inline-start` or Android's `layout_marginStart` do. In practice this means:
- Layout panels generally mirror correctly under `FlowDirection="RightToLeft"` (the panel's own arrangement logic flips), but explicit `Margin`/`Thickness` values authored as if LTR can end up on the wrong side and often need to be set programmatically or via a converter keyed on `FlowDirection`.
- Directional icons (arrows, chevrons) do not mirror automatically and need an explicit `ScaleTransform` (`ScaleX="-1"`) or a direction-aware asset swap.
- Document this honestly in §2.2 rather than assuming the same "just use the logical form" fix that works on the other platforms — flag which zones need explicit RTL handling rather than automatic mirroring.

## Motion (feeds §4 Appearance)

`UISettings.AnimationsEnabled` (WinRT) reflects the system's "Show animations in Windows" setting — the reduced-motion signal on this platform.
