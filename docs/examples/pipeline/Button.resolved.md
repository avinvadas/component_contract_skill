# Button — resolved

> **Generated. Do not edit.** Source: `Button.md` v1.0 + archetype `button` v1.0 + system policy.
> **Platform-neutral** — what the component *is*, before any platform's vocabulary.
> How each requirement is *observed* per platform is in `2-canonical/`.

**Origin** marks what is yours to change. *this component* — decided in your interview. *archetype* — a fact about what platforms provide free; changing it means a platform changed. *policy* — your design system's cross-cutting commitment.

## 1. Intent

The primary means of performing an action in place. Carries a text label, optionally preceded
by a decorative icon. Unlike Link, it does not navigate.

## 2. Structure

### Native backing

Where a platform gives you this free, and where you build it by hand.

| Platform | Native backing |
|---|---|
| web | `<button>` · `<input type=button|submit>` |
| ios | SwiftUI `Button` · `UIButton` |
| android | Compose `Button` · `android.widget.Button` |
| macos | SwiftUI `Button` · `NSButton` |

### Requirements

| statement | when | origin | id |
|---|---|---|---|
| Zones are arranged along the inline axis, icon before label. | when:icon_present | this component | id-CMP-03 |
| The control does not exceed the inline size of its container. | always | this component | id-STR-01 |
| The control meets the platform's minimum touch-target size. | when:touch_input | archetype `button` | id-BTN-11 |

### Required children

| zone | accepts | cardinality | position | if absent |
|---|---|---|---|---|
| label | text | 1 | inline-end | invalid:BTN-02 has no name source |

### Optional children

| zone | accepts | cardinality | position | if absent |
|---|---|---|---|---|
| icon | component:Icon | 0..1 | inline-start | omitted |

## 3. Appearance

### Tokenised properties

| property | token | when |
|---|---|---|
| background | `color.action.primary.bg` | always |
| background | `color.action.primary.disabled.bg` | when:disabled |

### Requirements

| statement | when | origin | id |
|---|---|---|---|
| The accessible label scales with the platform's user text-size setting. | always | archetype `button` | id-BTN-12 |
| A focused control renders a focus indicator distinguishable from its unfocused appearance. | always | policy | id-POL-02 |

### Platform distinctions

*None recorded. Every platform satisfies the above identically.*

## 4. Behavior

### Requirements

| statement | when | origin | id |
|---|---|---|---|
| Activating by the platform's primary non-pointer input performs the action. | always | archetype `button` | id-BTN-04 |
| Where a hardware keyboard exists, both of its standard activation keys perform the action. | when:hardware_keyboard | archetype `button` | id-BTN-05 |
| Keyboard activation does not also scroll the surrounding surface. | when:hardware_keyboard | archetype `button` | id-BTN-06 |
| When disabled, activation performs no action. | when:disabled | archetype `button` | id-BTN-09 |
| The control submits its containing form without scripting. | when:inside_form | archetype `button` | id-BTN-13 |

### Events

| direction | name | payload | when |
|---|---|---|---|
| emitted | press | none | on activation, unless disabled |

## 5. Accessibility

Reviewable as an aspect: everything governing how the component is exposed, named, traversed and announced.

| statement | when | origin | id |
|---|---|---|---|
| The icon contributes nothing to the accessible name. | when:icon_present | this component | id-ACC-01 |
| The label is the sole source of the accessible name. | always | this component | id-ACC-02 |
| The control is exposed to assistive technology as a button. | always | archetype `button` | id-BTN-01 |
| The control has a non-empty accessible name. | always | archetype `button` | id-BTN-02 |
| The control is reachable by the platform's sequential focus navigation. | always | archetype `button` | id-BTN-03 |
| When disabled, the control is removed from sequential focus navigation. | when:disabled | archetype `button` | id-BTN-08 |
| When disabled, that state is conveyed to assistive technology. | when:disabled | archetype `button` | id-BTN-10 |

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

17 requirements — 4 local, 12 inherited, 1 policy · 2 zones · 2 token slots · 5 props
