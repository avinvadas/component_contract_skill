# Catalogue of implicit guarantees

**The instrument T1 measures against.** Every construct v1 names, and what that platform provides *for free* when you use it.

This exists because v1 buys a bundle of behaviour with a single name. `<button>` is one word that silently promises Enter *and* Space activation, focus participation, pre-scripting operability, and form submission. None of it is written anywhere, so none of it is obviously missing when a format stops naming elements.

**Scope rule:** an entry belongs here only if the platform provides it *automatically*, without the implementer doing anything. Good practice, HIG advice, and things a developer must implement are excluded — they were never free, so v2 loses nothing by not inheriting them.

Anything here that a v2 requirement set does not cover is either a gap or a deliberate drop with a written reason.

---

## Web

### Interactive

**`<button>`** — Enter activates · Space activates and page scroll is suppressed · in sequential focus order without `tabindex` · platform-drawn focus indicator · `disabled` removes from focus order, blocks activation, and is announced · `type=submit` submits its form **without scripting** · keyboard activation synthesises a click · announced with role and name.

**`<button aria-expanded>`** — everything above · expanded/collapsed state announced on every change. *No* relationship to the controlled element is free; `aria-controls` is separate and inconsistently supported.

**`<button aria-pressed>`** — everything from `<button>` · pressed state announced · semantically distinct from a checkbox, which matters for how AT describes it.

**`<a href>`** — Enter activates, and **Space does not** · in sequential focus order · middle-click and modifier-click open in a new context · context menu offers copy-link and open-in-new · destination visible before activation · reachable and followable **without scripting** · discoverable by crawlers · visited state tracked.

**`<input type="checkbox">`** — Space toggles · focus order · indeterminate state available · `<label>` association gives a click target and an accessible name · value submitted only when checked · checked state announced.

**`<input type="radio">` in `<fieldset>`/`<legend>`** — arrow keys move **and** select · the group is one tab stop, not one per option · exactly one selection enforced by shared `name` · `<legend>` announced with each option · position announced ("2 of 5") · value participates in form submission.

**`<select>`** — platform-native picker, which on mobile is a full-screen native control the page cannot replicate · type-ahead by typing · arrow keys, Home/End · closed state displays the current value · long lists scroll automatically · works **without scripting** · announced with value and option position.

### Non-interactive

**Landmarks — `<nav>` `<main>` `<aside>` `<section aria-labelledby>`** — reachable by landmark navigation · announced as a named region · `<main>` is the skip-to-content target · contribute to document structure.

**Headings `<h1>`–`<h6>`** — reachable by heading navigation · level conveyed · contribute to the document outline.

**`<ul>`/`<ol>` + `<li>`** — announced as a list **with item count** · each item announced with its position · reachable by list navigation.

**`<figure>` + `<figcaption>`** — caption programmatically associated with the figure's content · announced as a figure with its caption.

**`<div role="status">`** — implicitly polite and atomic · announced without moving focus · does not interrupt speech in progress.

**`aria-hidden="true"`** — removed from the accessibility tree. **Note the trap:** it does *not* remove the element from focus order, so a focusable descendant becomes reachable but unannounced.

### Containers

**Scroll container (`overflow:auto` + `tabindex="0"`)** — arrow keys, Page Up/Down, Home/End scroll when focused · scrollbar affordance · momentum and rubber-band on touch · announced as a scrollable region.

### Two deliberate controls — constructs with an *empty* bundle

**`role="tablist"` / `tab` / `tabpanel`** — no native element exists on any platform. Roving focus, arrow-key movement, activation mode, and panel association are all implemented by hand. **Nothing is free**, so v2 loses nothing here.

**Drag-to-reorder (`role="list"` + `listitem`)** — pointer dragging *and* the entire keyboard alternative are implemented by hand. **Nothing is free.**

These two matter as much as the full entries: they prove the bundle problem is specific to archetypes backed by real native elements, not a general property of abstraction.

---

## iOS

**`Button`** — VoiceOver double-tap activates · `.button` trait · label scales with Dynamic Type · pressed state rendered · `.notEnabled` blocks activation and is announced · reachable by Full Keyboard Access · addressable by Voice Control by its label · works with Switch Control.

**`Toggle`** — state announced as on/off · VoiceOver swipe up/down changes it without activation · Switch Control support · Dynamic Type.

**`Picker` (segmented / wheel)** — `.adjustable` trait, so VoiceOver swipe up/down changes the value · current value announced on change · keyboard support on iPad · segmented control renders platform-standard.

**`.sheet`** — swipe-down dismisses · detents · VoiceOver and focus contained to the sheet · background dimmed and inert · presented above all app content · announced as modal · rotor navigation stays inside.

**`.fullScreenCover`** — containment, inert background, and modal announcement as above, but **no swipe-to-dismiss by default**. The asymmetry with `.sheet` is real and easy to miss.

**`.popover`** — dismisses on outside tap · anchored to its source · arrow/beak rendered · focus and VoiceOver contained while open.

**`TabView`** — standard tab-bar placement · selected tab announced with position · rotor navigation between tabs.

**`NavigationStack`** — back-swipe gesture from the screen edge · back button labelled with the previous title · new screen title announced on push · VoiceOver focus moves to the new screen.

---

## Android

**`Button`** — Enter/Space activate via keyboard · TalkBack double-tap activates · `Role.Button` announced · ripple feedback · Material enforces the 48dp minimum touch target · disabled state announced and blocks activation · focusable for D-pad and keyboard.

**`Switch`** — `Role.Switch` with on/off state announced · TalkBack double-tap toggles · keyboard operable.

**`RadioButton` group** — `Role.RadioButton` with selected state · single selection enforced by the group · TalkBack announces position within the group.

**`DropdownMenu` / `ExposedDropdownMenuBox`** — opens on tap and on keyboard activation · dismisses on outside tap and on Back · focus moves into the menu and returns on close · item position announced.

**`androidx.compose.ui.window.Dialog`** — system Back gesture or button dismisses · scrim rendered · focus and TalkBack contained · hosted in a window above the activity.

**`ModalBottomSheet`** — drag-to-dismiss · Back dismisses · scrim · half-expanded and expanded detents · containment as above.

**`TabRow` + `Tab`** — `Role.Tab` with selected state announced · standard indicator · swipe between tabs when paired with a pager.

**Live-region container** — `liveRegion = Polite` announces changes inside it without moving focus; `Assertive` interrupts. Declarative, unlike iOS.

---

## macOS

Everything in the iOS list applies where SwiftUI is shared. macOS adds:

**Any control** — real hover state · right-click context menu is a standard, expected affordance · Full Keyboard Access tab loop · Escape dismisses sheets and popovers.

**Sheet** — attaches to its parent window and blocks *only* that window, not the app · animates from the title bar.

**Window** — minimise, zoom, close, and user resizing · position and size restored between launches.

**Popover** — dismisses on outside click · anchored with a beak · Escape closes.

**Menu bar** — app- and window-level commands live there by convention, with automatic keyboard-shortcut registration.

---

## How to use this

For each construct a component's v1 contract names, take every clause in its entry and require a v2 requirement id to cover it. Three outcomes only:

1. **Covered** — a requirement states it. Record the id.
2. **Gap** — nothing states it. Fix before adoption.
3. **Dropped** — deliberately not carried, **with a written reason**. Crawler discoverability for an in-app component is a legitimate drop; "we forgot" is not.

The catalogue is per *construct*, not per component, so it is written once and reused for every conversion. A component naming three constructs must satisfy three entries.

### Known limits of this catalogue

Compiled from platform documentation and the reference files in this repo, not from empirical testing. Two consequences worth stating rather than discovering later:

- **Platform behaviour drifts.** Entries reflect the platforms as documented at the reference files' `Last verified` dates. A new OS version can add or remove a free guarantee.
- **Some entries are verifiable, others are assertions.** "Space activates a button" is testable in a browser in seconds; "position restored between launches" is not something this repo's harness can check. The catalogue does not distinguish these, and a requirement derived from an untested entry inherits that uncertainty.
