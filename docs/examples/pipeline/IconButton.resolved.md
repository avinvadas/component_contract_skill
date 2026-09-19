# IconButton — resolved

> **Generated. Do not edit.** Source: `IconButton.md` v1.0 + archetype `button` v1.0 + system policy.
> **Platform-neutral** — what the component *is*, before any platform's vocabulary.
> How each requirement is *observed* per platform is in `2-canonical/`.

**Origin** marks what is yours to change. *this component* — decided in your interview. *archetype* — a fact about what platforms provide free; changing it means a platform changed. *policy* — your design system's cross-cutting commitment.

## 1. Intent

A button whose only visible content is an icon. Used where space is constrained and the
action is conventional enough to be recognised without a label — close, back, overflow.

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
| — | The control's inline and block sizes are equal. | this component | id-STR-01 |
| when:touch_input | The control meets the platform's minimum touch-target size. | archetype `button` | id-BTN-11 |

### Required children

| zone | accepts | cardinality | position | if absent |
|---|---|---|---|---|
| icon | component:Icon | 1 | block-start | invalid:the control has no visible content |

### Optional children

*None.*

## 3. Appearance

### Interaction states

| state | what changes | driven by | valid because |
|---|---|---|---|
| hover | background | platform | archetype `button` |
| focus-visible | — | platform | archetype `button` |
| pressed | — | platform | archetype `button` |
| disabled | background | prop | archetype `button` |

### Tokenised properties

**Specificity:** 1 semantic — how much this component relies on tokens made for it, shared patterns, or system-wide meanings. Rest-token aliases are not counted.

| property | state | variant | token | scope | status |
|---|---|---|---|---|---|
| background | rest | — | — | — | **ambiguous** |
| background | hover | — | `semantic.color.action.primary-hover` | semantic | bound |
| background | disabled | — | — | — | **state unexpressed** |
| background | focus-visible | — | — | — | **ambiguous** · rest token |
| background | pressed | — | — | — | **ambiguous** · rest token |

### Platform tokens

*None. Every platform uses the same token, spelled its own way — see `2-canonical/` for each platform's name.*

### Token gaps

2 properties could not resolve. These are fixed in the token tree, not in this contract — leave the cells above unbound until the tree can express them.

| property | what is wrong | what to do |
|---|---|---|
| background | 2 candidates; scope and dimension did not narrow it | pin one: `semantic.color.surface.neutral`, `semantic.color.action.primary` |
| background@disabled | `semantic.color.surface.neutral` exists but carries no `disabled` state | add a `disabled` variant of that token |

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
| — | The icon contributes nothing to the accessible name. | this component | id-ACC-01 |
| — | The accessible name is supplied by the `label` prop, since no rendered content can provide one. | this component | id-ACC-02 |
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
| `label` | string | yes | — |
| `iconName` | string | yes | — |
| `disabled` | boolean | no | `false` |
| `onPress` | handler | yes | — |

---

16 requirements — 3 local, 12 inherited, 1 policy · 1 zones · 5 token cases — 1 bound, 4 gaps, 0 n/a · 4 props
