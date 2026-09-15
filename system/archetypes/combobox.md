---
archetype: combobox
version: 1.0
platforms: [web, ios, android, macos]
kind: mixed
---

# Archetype: combobox

An editable text entry paired with a list of candidate values, where the list can be opened,
navigated, and committed from without leaving the entry.

**Bundle kind: mixed** — the first in the library. `button` is native-backed on every
platform; `tab` is composed on every platform; this one is native-backed on **some**.

| Platform | Native backing |
|---|---|
| macOS | `NSComboBox` — a real native control |
| Android | `ExposedDropdownMenuBox` — close, and in the catalogue |
| Web | `role="combobox"` is an ARIA pattern; `<datalist>` is native but barely styleable |
| iOS | **none** — composed by hand every time |

## Why this needs an archetype rather than composition

The obvious alternative is composing it from `text` plus `list`/`listitem` plus
component-local requirements. That fails on the first requirement, and the reason generalises:

> **A combobox is announced by assistive technology as a combo box.** You cannot compose your
> way to a role. No arrangement of a text archetype and a list archetype produces an element
> that VoiceOver calls a combo box.

Which gives a crisp test for when the registry must be extended, replacing intuition:

> **An archetype is needed exactly when the platform's accessibility layer reports a distinct
> role for the thing.**

That criterion predicts the rest of the library correctly. `tab`, `tablist` and `tabpanel`
need archetypes despite entirely empty bundles, because assistive technology reports those
roles. **Drag-to-reorder does not**, because assistive technology reports it as a list —
which answers the other open question in `source-layer-plan.md` before anyone builds it.

## Bundle

| when | statement | observe | kind | chapter | source | id |
|---|---|---|---|---|---|---|
| always | The control is exposed to assistive technology as a combo box. | role | state | Accessibility | catalogue:macOS/NSComboBox · apg:combobox | id-CBX-01 |
| always | The control has a non-empty accessible name. | name | state | Accessibility | apg:combobox | id-CBX-02 |
| always | Whether the candidate list is open is conveyed to assistive technology. | state | state | Accessibility | catalogue:macOS/NSComboBox · apg:combobox | id-CBX-03 |
| when:expanded | The candidate list is programmatically associated with the entry. | containment | state | Composition | apg:combobox | id-CBX-04 |
| when:expanded | The active candidate is conveyed without focus leaving the entry. | state | state | Accessibility | apg:combobox | id-CBX-05 |
| when:expanded | The platform's list-navigation input moves between candidates. | event | behavior | Behavior | catalogue:macOS/NSComboBox · catalogue:Android/ExposedDropdownMenuBox | id-CBX-06 |
| when:expanded | The platform's dismissal input closes the list without committing a value. | event | behavior | Behavior | catalogue:macOS/NSComboBox · catalogue:Android/DropdownMenu | id-CBX-07 |
| when:expanded | Committing a candidate places its value in the entry and closes the list. | event | behavior | Behavior | catalogue:macOS/NSComboBox | id-CBX-08 |
| always | The entry remains editable after a candidate is committed. | state | state | Structure | catalogue:macOS/NSComboBox | id-CBX-09 |

## CBX-09 and the single-platform question

CBX-09 is sourced from **one** platform. That is a flag, not an automatic inclusion, and it
forced a refinement to the decision procedure in `source-layer-plan.md`:

> A guarantee provided by only one platform is a **candidate**, not an inheritance. The test
> is whether the behaviour is a user-facing expectation across platforms, or a convention of
> the platform that automates it.

CBX-09 passes: remaining editable is what distinguishes a combobox from a picker on every
platform, and a combobox that locks after selection is a picker wearing the wrong role.

Contrast with macOS `Window`'s *"position and size restored between launches"* — also
single-platform, and squarely a desktop convention. That one would fail the test and belongs
nowhere near a bundle.

## What is deliberately absent

**Filtering.** Typing narrows the candidate list on macOS and Android, but *what* it filters —
prefix, substring, fuzzy, server-side — is a product decision with no platform default. It is
a component-local requirement, not an archetype one.

**A required minimum number of candidates.** Cardinality, stated in the contract's §3.1.
