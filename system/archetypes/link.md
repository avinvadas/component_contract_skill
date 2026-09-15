---
archetype: link
version: 1.0
platforms: [web, ios, android, macos]
kind: native-backed
---

# Archetype: link

A control that navigates to a destination. **The asymmetry with `button` is the point:** Enter
activates both; Space activates only a button. A link implemented as a button that calls
`navigate()` satisfies neither this bundle nor a user's expectations.
## Native backing

What each platform provides. `none` means every implementation builds the semantics by hand — the requirements below still bind.

| Platform | Native backing |
|---|---|
| web | `<a href>` |
| ios | **none** — composed from a tappable label |
| android | **none** — composed; `Role.Button` with link semantics applied by hand |
| macos | `NSTextView` link attributes, partial |


| statement | observe | kind | required | chapter | source | id |
|---|---|---|---|---|---|---|
| The control is exposed to assistive technology as a link. | role | state | always | Accessibility | catalogue:Web/a-href | id-LNK-01 |
| The control has a non-empty accessible name. | name | state | always | Accessibility | catalogue:Web/a-href | id-LNK-02 |
| The control is reachable by the platform's sequential focus navigation. | focus | state | always | Accessibility | catalogue:Web/a-href | id-LNK-03 |
| Activation by the platform's primary confirm input navigates to the destination. | event | behavior | always | Behavior | catalogue:Web/a-href | id-LNK-04 |
| The secondary activation key does **not** navigate. | event | behavior | when:hardware_keyboard | Behavior | catalogue:Web/a-href | id-LNK-05 |
| The destination is available to the user before activation. | name | state | always | Accessibility | catalogue:Web/a-href | id-LNK-06 |
| The platform's convention for opening in a new context is available. | event | behavior | when:pointer_input | Behavior | catalogue:Web/a-href | id-LNK-07 |
| The destination is reachable and followable without scripting. | event | behavior | always | Behavior | catalogue:Web/a-href | id-LNK-08 |
| A previously-visited destination is distinguishable from an unvisited one. | state | state | always | Appearance | catalogue:Web/a-href | id-LNK-09 |

## Deliberate drops

The catalogue requires anything unmapped to be a gap **or** a written drop. These are drops.

| Free behaviour | Dropped because |
|---|---|
| discoverable by crawlers | a property of a *document*, not of a component. A design system's Link component has no control over whether the page hosting it is indexed, so a requirement here would be unfalsifiable by the component's own implementation. |

## Note on LNK-05

A **negative** requirement, and one of the few. It only becomes visible by enumerating a
bundle — nobody writes "Space must not activate" from memory, which is exactly why a link
built out of a button passes every positive check and still behaves wrongly.
