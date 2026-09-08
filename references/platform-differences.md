# Cross-platform comparison

Pure comparison content — not routing logic. This file exists so the five cross-cutting concerns that recur across every platform file can be scanned side by side, then followed into the relevant platform directory for depth. It does not decide *which* platform file applies to a given component — that's Q2 (Platform)'s job, resolved in SKILL.md's Phase 3/4, which branch to the matching platform file for every platform Q2 names.

**Last verified:** 2026-08-25

This is the multi-platform extension of the principle §5.1 already applies to interaction deltas — document what's shared once, and only split out what genuinely differs. Here, the "shared" thing is the underlying concept (e.g., "how does directionality get expressed"); each platform supplies its own answer.

| Concern | Web | iOS | Android | macOS | Windows | Linux |
|---|---|---|---|---|---|---|
| Accessibility API | WAI-ARIA roles/states/properties | `UIAccessibility` traits + label/hint/value | Compose `semantics{}` / `AccessibilityNodeInfo`, `Role` + `contentDescription` | `NSAccessibility` roles (AppKit) or shared SwiftUI modifiers | UI Automation control patterns (Invoke, Toggle, SelectionItem, Value, RangeValue…) | AT-SPI roles/states (toolkit-agnostic; GTK native, Qt via bridge) |
| Component/structure resolution | HTML element + ARIA role, from Q3+Q4 | Native SwiftUI control/presentation, from Q3+Q4 | Native Compose component, from Q3+Q4 | Same as iOS, plus macOS-only conventions (hover, context menu, sheet vs. window vs. popover) | UIA control pattern (not a specific XAML class), from Q3+Q4 | AT-SPI role (not a specific widget), from Q3+Q4 |
| Layout adaptation ("container query" equivalent) | CSS Container Queries (`@container`, container-relative) | Size Classes (compact/regular), container-relative | Window Size Classes (compact/medium/expanded), container-relative | Same mechanism as iOS; wider practical range due to user-resizable windows | `VisualStateManager` adaptive triggers on window/container width | GTK: `AdwBreakpoint`. Qt: layout managers / QML anchors — no unified equivalent |
| RTL / directionality | CSS Logical Properties (`inline-start`/`-end`) vs. `dir` attribute (content-level only) | Leading/trailing (Auto Layout, SwiftUI `.leading`/`.trailing`) | Start/end (predates CSS logical properties) | Same as iOS | `FlowDirection`, but `Margin`/`Padding` stay physical (Left/Top/Right/Bottom) — messier, often needs explicit handling | GTK4: native start/end. Qt: `LayoutDirection` + direction-aware anchoring |
| Reduced motion signal | `prefers-reduced-motion` media feature | `UIAccessibility.isReduceMotionEnabled` | System animator-duration-scale setting | `NSWorkspace.accessibilityDisplayShouldReduceMotion` | `UISettings.AnimationsEnabled` | No cross-desktop standard; GNOME/KDE each have their own setting, XDG Settings Portal emerging for sandboxed apps |

Question numbers above refer to SKILL.md's Phase 1 interview: Q2 = Platform, Q3 = action, Q4 = interaction.

## How to read the RTL/directionality row

Every platform except Windows converged on the same underlying idea — express layout in terms of "start/end" relative to reading direction rather than "left/right" absolute physical sides, and the platform resolves the physical side automatically. Windows is the outlier: `FlowDirection` flips the container's flow, but `Margin`/`Padding` values are still authored as literal Left/Top/Right/Bottom, so they don't auto-resolve the way every other platform's logical/leading-trailing/start-end properties do. When writing §2.2 Order for a multi-platform contract, this means the same logical description ("top edge, trailing edge") is directly implementable on every platform except Windows, where it additionally needs an explicit per-direction override — document that difference in the contract rather than letting a single logical phrase imply uniform automatic handling everywhere.

---

## What you are actually specifying, per platform

Reading a contract's per-platform rows is confusing if you expect every platform to describe the same *kind* of thing. They don't. This section exists to make the rows legible: for each fact a contract states, what is the unit of specification on each platform, and what does a real value look like.

**The one distinction that explains most of the confusion:** on the Web, structure and accessibility are the *same object* — `<button>` is simultaneously the thing on screen and the thing a screen reader announces. On iOS, macOS and Android they are **two layers**: you compose a view for what appears, then attach separate modifiers describing what it means. So a Web row often names one thing where a native row names a thing plus its annotations. That is not the native row being vaguer — it is the platform genuinely having two parts.

### The unit of specification

| What the contract states | Web | iOS (SwiftUI) | macOS (SwiftUI) | Android (Compose) |
|---|---|---|---|---|
| **The root itself** | An HTML element in the DOM | A `View` value | A `View` value | A `@Composable` function |
| | `<button>` | `Button { }` | `Button { }` | `Button( )` |
| **Children** | Nested elements inside the parent tag | Views nested in the parent's closure | Same as iOS | Composables called inside the parent's lambda |
| | `<div><span>…</span></div>` | `HStack { Text("Hi") }` | `HStack { Text("Hi") }` | `Row { Text("Hi") }` |
| **Role / what it is** | Implicit in the element; `role=` only to override | A **trait** attached to the view | Trait (SwiftUI) or `NSAccessibility` role (AppKit) | A `Role` inside `Modifier.semantics { }` |
| | `role="tab"` | `.accessibilityAddTraits(.isButton)` | `NSAccessibilityRadioButtonRole` | `Modifier.semantics { role = Role.Tab }` |
| **Accessible name** | An attribute, or the element's own text | A modifier | A modifier | A semantics property |
| | `aria-label="Close"` | `.accessibilityLabel("Close")` | `.accessibilityLabel("Close")` | `contentDescription = "Close"` |
| **State (selected, disabled)** | An attribute per state | A trait, or `accessibilityValue` | Same as iOS | `stateDescription`, or a `Role`-specific flag |
| | `aria-selected="true"` | `.accessibilityAddTraits(.isSelected)` | `.accessibilityAddTraits(.isSelected)` | `stateDescription = "selected"` |
| **Announcing a change** | A **property on a container** — set once, system handles it | An **action taken at the moment of change** — no declarative container | Same as iOS | A **property on a container**, like Web |
| | `aria-live="polite"` | `AccessibilityNotification.Announcement(…).post()` | same | `liveRegion = LiveRegionMode.Polite` |
| **Heading** | A numbered level, chosen by the page | A binary trait — no level exists | Binary trait | Binary marker — no level exists |
| | `<h2>` (level set by the mounting page) | `.accessibilityAddTraits(.isHeader)` | `.accessibilityAddTraits(.isHeader)` | `Modifier.semantics { heading() }` |
| **Focus** | Tab order + `tabindex`; CSS `:focus-visible` | `@FocusState` binding | `@FocusState`; richer, keyboard is primary | `FocusRequester` / `Modifier.focusable()` |
| **Events out** | A `CustomEvent` dispatched on the element | A closure the caller passes in | A closure | A lambda the caller passes in |
| | `dispatchEvent(new CustomEvent("dismiss"))` | `onDismiss: () -> Void` | `onDismiss: () -> Void` | `onDismiss: () -> Unit` |
| **Adapting to space** | Container queries — measured against the container | Size Classes — compact/regular | Size Classes, but windows resize freely | Window Size Classes — compact/medium/expanded |
| **Where a token lands** | A CSS custom property | A generated Swift constant | Same as iOS | A generated Kotlin/XML resource |
| | `var(--color-surface)` | `Tokens.colorSurface` | `Tokens.colorSurface` | `R.color.color_surface` |

### Three asymmetries worth recognising in an output

**Announcing a change is the sharp one.** Web and Android set a flag on a container and the system announces anything that changes inside it. iOS and macOS have no such flag — the app must actively post an announcement each time. So an iOS row for a status component reads as an instruction about *when to act*, where the Web row reads as a *property to set*. Both fully satisfy "the user learns of the change without moving focus." The iOS row is not a weaker version of the Web one.

**Heading level exists only on the Web.** iOS, macOS and Android have a binary "this is a heading" marker with no number. So a Title zone's Web row says "a heading element, level set by the consuming page" while the native rows say only "marked as a header" — and there is no missing information in the native rows.

**Windows and Linux are absent from this table on purpose.** They are on the roadmap and not supported (see SKILL.md's "Supported platforms"). Their reference files remain, but no contract should carry a row for them today.

### How to read a row that looks thin

A native row with fewer specifics than its Web counterpart is usually correct, not lazy. Ask which of these it is:

- **The platform has no equivalent concept** (heading levels) — the row is complete as written.
- **The platform meets the intent differently** (announcements) — the row is complete, and should not be phrased as an approximation.
- **The platform genuinely cannot meet the intent** — this is the only case where the row's Notes should say so outright.

Only the third is a shortfall. The first two are the row doing its job.
