# Button — spec

> **Generated. Do not edit.** Source: `Button.md` v1.0 + archetype `button` v1.0 + system policy.
> **Platform-neutral** — what the component *is*, before any platform's vocabulary.
> How each requirement is *observed* per platform is in the `Button.<platform>.json` files beside this one.

**Origin** marks what is yours to change. *this component* — decided in your interview. *archetype* — a fact about what platforms provide free; changing it means a platform changed. *policy* — your design system's cross-cutting commitment.

## 1. Intent

The primary means of performing an action in place. Carries a text label, optionally preceded
by a decorative icon. Unlike Link, it does not navigate.

## 2. Structure

### Element

Which element carries the role on each platform — checked, not just documented.

| platform | element |
|---|---|
| web | `<button>` |
| ios | SwiftUI `Button` |
| android | Compose `Button` |

### Native backing

Where a platform gives you this free, and where you build it by hand.

| Platform | Native backing |
|---|---|
| web | `<button>` · `<input type=button|submit>` |
| ios | SwiftUI `Button` · `UIButton` |
| android | Compose `Button` · `android.widget.Button` |
| macos | SwiftUI `Button` · `NSButton` |

### Requirements

| when | statement | origin | id |
|---|---|---|---|
| when:icon_present | Zones are arranged along the inline axis, icon before label. | this component | id-CMP-03 |
| — | The control does not exceed the inline size of its container. | this component | id-STR-01 |
| when:touch_input | The control meets the platform's minimum touch-target size. | archetype `button` | id-BTN-11 |

### Required children

| zone | accepts | cardinality | position | if absent |
|---|---|---|---|---|
| label | text | 1 | inline-end | invalid:BTN-02 has no name source |

### Optional children

| zone | accepts | cardinality | position | if absent |
|---|---|---|---|---|
| icon | component:Icon | 0..1 | inline-start | omitted |

## 3. Appearance

### Interaction states

| state | what changes | driven by | valid because |
|---|---|---|---|
| hover | background | platform | archetype `button` |
| focus-visible | — | platform | archetype `button` |
| pressed | background | platform | archetype `button` |
| disabled | background | prop | archetype `button` |

### Tokenised properties

**Specificity:** 13 component — how much this component relies on tokens made for it, shared patterns, or system-wide meanings. Rest-token aliases are not counted.

| property | state | variant | token | scope | status |
|---|---|---|---|---|---|
| background | rest | variant=primary | `component.button.variant.primary.background` | component | bound |
| background | rest | variant=secondary | `component.button.variant.secondary.background` | component | bound |
| background | rest | variant=ghost | `component.button.variant.ghost.background` | component | bound |
| foreground | rest | variant=primary | `component.button.variant.primary.text` | component | bound |
| foreground | rest | variant=secondary | `component.button.variant.secondary.text` | component | bound |
| foreground | rest | variant=ghost | `component.button.variant.ghost.text` | component | bound |
| border-color | rest | variant=primary | `component.button.variant.primary.border` | component | bound |
| border-color | rest | variant=secondary | `component.button.variant.secondary.border` | component | bound |
| border-color | rest | variant=ghost | `component.button.variant.ghost.border` | component | bound |
| border-width | rest | — | — | — | **absent from tree** |
| radius | rest | — | `component.button.radius` | component | bound |
| padding-inline | rest | — | — | — | **ambiguous** |
| background | hover | variant=primary | `component.button.variant.primary.background-hover` | component | bound |
| background | hover | variant=secondary | `component.button.variant.secondary.background-hover` | component | bound |
| background | hover | variant=ghost | `component.button.variant.ghost.background-hover` | component | bound |
| background | pressed | variant=primary | — | — | **state unexpressed** |
| background | pressed | variant=secondary | — | — | **state unexpressed** |
| background | pressed | variant=ghost | — | — | **state unexpressed** |
| background | disabled | variant=primary | — | — | **state unexpressed** |
| background | disabled | variant=secondary | — | — | **state unexpressed** |
| background | disabled | variant=ghost | — | — | **state unexpressed** |
| elevation | rest | — | — | — | n/a — a Button sits in the content plane |
| background | focus-visible | variant=primary | `component.button.variant.primary.background` | component | bound · rest token |
| background | focus-visible | variant=secondary | `component.button.variant.secondary.background` | component | bound · rest token |
| background | focus-visible | variant=ghost | `component.button.variant.ghost.background` | component | bound · rest token |
| foreground | hover | variant=primary | `component.button.variant.primary.text` | component | bound · rest token |
| foreground | focus-visible | variant=primary | `component.button.variant.primary.text` | component | bound · rest token |
| foreground | pressed | variant=primary | `component.button.variant.primary.text` | component | bound · rest token |
| foreground | disabled | variant=primary | `component.button.variant.primary.text` | component | bound · rest token |
| foreground | hover | variant=secondary | `component.button.variant.secondary.text` | component | bound · rest token |
| foreground | focus-visible | variant=secondary | `component.button.variant.secondary.text` | component | bound · rest token |
| foreground | pressed | variant=secondary | `component.button.variant.secondary.text` | component | bound · rest token |
| foreground | disabled | variant=secondary | `component.button.variant.secondary.text` | component | bound · rest token |
| foreground | hover | variant=ghost | `component.button.variant.ghost.text` | component | bound · rest token |
| foreground | focus-visible | variant=ghost | `component.button.variant.ghost.text` | component | bound · rest token |
| foreground | pressed | variant=ghost | `component.button.variant.ghost.text` | component | bound · rest token |
| foreground | disabled | variant=ghost | `component.button.variant.ghost.text` | component | bound · rest token |
| border-color | hover | variant=primary | `component.button.variant.primary.border` | component | bound · rest token |
| border-color | focus-visible | variant=primary | `component.button.variant.primary.border` | component | bound · rest token |
| border-color | pressed | variant=primary | `component.button.variant.primary.border` | component | bound · rest token |
| border-color | disabled | variant=primary | `component.button.variant.primary.border` | component | bound · rest token |
| border-color | hover | variant=secondary | `component.button.variant.secondary.border` | component | bound · rest token |
| border-color | focus-visible | variant=secondary | `component.button.variant.secondary.border` | component | bound · rest token |
| border-color | pressed | variant=secondary | `component.button.variant.secondary.border` | component | bound · rest token |
| border-color | disabled | variant=secondary | `component.button.variant.secondary.border` | component | bound · rest token |
| border-color | hover | variant=ghost | `component.button.variant.ghost.border` | component | bound · rest token |
| border-color | focus-visible | variant=ghost | `component.button.variant.ghost.border` | component | bound · rest token |
| border-color | pressed | variant=ghost | `component.button.variant.ghost.border` | component | bound · rest token |
| border-color | disabled | variant=ghost | `component.button.variant.ghost.border` | component | bound · rest token |
| border-width | hover | — | — | — | **absent from tree** · rest token |
| border-width | focus-visible | — | — | — | **absent from tree** · rest token |
| border-width | pressed | — | — | — | **absent from tree** · rest token |
| border-width | disabled | — | — | — | **absent from tree** · rest token |
| radius | hover | — | `component.button.radius` | component | bound · rest token |
| radius | focus-visible | — | `component.button.radius` | component | bound · rest token |
| radius | pressed | — | `component.button.radius` | component | bound · rest token |
| radius | disabled | — | `component.button.radius` | component | bound · rest token |
| padding-inline | hover | — | — | — | **ambiguous** · rest token |
| padding-inline | focus-visible | — | — | — | **ambiguous** · rest token |
| padding-inline | pressed | — | — | — | **ambiguous** · rest token |
| padding-inline | disabled | — | — | — | **ambiguous** · rest token |
| elevation | hover | — | — | — | n/a — a Button sits in the content plane · rest token |
| elevation | focus-visible | — | — | — | n/a — a Button sits in the content plane · rest token |
| elevation | pressed | — | — | — | n/a — a Button sits in the content plane · rest token |
| elevation | disabled | — | — | — | n/a — a Button sits in the content plane · rest token |

### Platform tokens

*None. Every platform uses the same token, spelled its own way — see the per-platform JSON beside this file for each platform's name.*

### Token gaps

8 properties could not resolve. These are fixed in the token tree, not in this contract — leave the cells above unbound until the tree can express them.

| property | what is wrong | what to do |
|---|---|---|
| border-width | no token anywhere expresses this property | add `semantic.border-width.default` |
| padding-inline | 3 candidates; scope and dimension did not narrow it | pin one: `component.button.size.sm.padding-inline`, `component.button.size.md.padding-inline`, `component.button.size.lg.padding-inline` |
| background@pressed | `component.button.variant.primary.background` exists but carries no `pressed` state | add a `pressed` variant of that token |
| background@pressed | `component.button.variant.primary.background` exists but carries no `pressed` state | add a `pressed` variant of that token |
| background@pressed | `component.button.variant.primary.background` exists but carries no `pressed` state | add a `pressed` variant of that token |
| background@disabled | `component.button.variant.primary.background` exists but carries no `disabled` state | add a `disabled` variant of that token |
| background@disabled | `component.button.variant.primary.background` exists but carries no `disabled` state | add a `disabled` variant of that token |
| background@disabled | `component.button.variant.primary.background` exists but carries no `disabled` state | add a `disabled` variant of that token |

### Requirements

| when | statement | origin | id |
|---|---|---|---|
| — | The accessible label scales with the platform's user text-size setting. | archetype `button` | id-BTN-12 |
| — | A focused control renders a focus indicator distinguishable from its unfocused appearance. | policy | id-POL-02 |

### Platform distinctions

*None recorded. Every platform satisfies the above identically.*

## 4. Behavior

### State machine

*No state machine.*

### Requirements

| when | statement | origin | id |
|---|---|---|---|
| when:enabled | Activating by the platform's primary non-pointer input performs the action. | archetype `button` | id-BTN-04 |
| when:hardware_keyboard,enabled | Both of the platform's standard activation keys perform the action. | archetype `button` | id-BTN-05 |
| when:hardware_keyboard | Keyboard activation does not also scroll the surrounding surface. | archetype `button` | id-BTN-06 |
| when:disabled | Activation performs no action. | archetype `button` | id-BTN-09 |
| when:inside_form | The control submits its containing form without scripting. | archetype `button` | id-BTN-13 |

### Events

| when | direction | name | payload |
|---|---|---|---|
| on activation, unless disabled | emitted | press | none |

## 5. Accessibility

Reviewable as an aspect: everything governing how the component is exposed, named, traversed and announced.

| when | statement | origin | id |
|---|---|---|---|
| when:icon_present | The icon contributes nothing to the accessible name. | this component | id-ACC-01 |
| — | The label is the sole source of the accessible name. | this component | id-ACC-02 |
| — | The control is exposed to assistive technology as a button. | archetype `button` | id-BTN-01 |
| — | The control has a non-empty accessible name. | archetype `button` | id-BTN-02 |
| when:enabled | The control is reachable by the platform's sequential focus navigation. | archetype `button` | id-BTN-03 |
| when:disabled | The control is removed from sequential focus navigation. | archetype `button` | id-BTN-08 |
| when:disabled | The disabled state is conveyed to assistive technology. | archetype `button` | id-BTN-10 |

### Platform distinctions

*None recorded. Every platform satisfies the above identically.*

## What a consumer may pass

| prop | type | required | default |
|---|---|---|---|
| `fullWidth` | boolean | no | `false` |
| `variant` | enum:primary,secondary,ghost | no | `primary` |
| `label` | string | yes | — |
| `disabled` | boolean | no | `false` |
| `onPress` | handler | yes | — |

---

17 requirements — 4 local, 12 inherited, 1 policy · 2 zones · 65 token cases — 44 bound, 16 gaps, 5 n/a · 5 props
