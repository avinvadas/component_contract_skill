# Button — resolved

> **Generated. Do not edit.** Source: `Button.md` v1.0 +
> archetype `button` v1.0 + system policy.
> Platform-neutral: this is what the component *is*, before any platform's vocabulary.

The primary means of performing an action in place. Carries a text label, optionally preceded
by a decorative icon. Unlike Link, it does not navigate.

## What this component must do

Every requirement, from all three layers, in one place. **The origin column is the point** —
inherited rows are facts about platforms and are not yours to negotiate; local rows are
decisions your team made and can revisit.

### Inherited from archetype `button`

*Facts about what platforms provide free. Changing these means changing the archetype, which means a platform guarantee changed. See `system/archetypes/button.md` for provenance and for what was deliberately left out.*

| id | statement | observe | kind | required |
|---|---|---|---|---|
| BTN-01 | The control is exposed to assistive technology as a button. | role | state | always |
| BTN-02 | The control has a non-empty accessible name. | name | state | always |
| BTN-03 | The control is reachable by the platform's sequential focus navigation. | focus | state | always |
| BTN-04 | Activating by the platform's primary non-pointer input performs the action. | event | behavior | always |
| BTN-05 | Where a hardware keyboard exists, both of its standard activation keys perform the action. | event | behavior | when:hardware_keyboard |
| BTN-06 | Keyboard activation does not also scroll the surrounding surface. | event | behavior | when:hardware_keyboard |
| BTN-08 | When disabled, the control is removed from sequential focus navigation. | focus | state | when:disabled |
| BTN-09 | When disabled, activation performs no action. | event | behavior | when:disabled |
| BTN-10 | When disabled, that state is conveyed to assistive technology. | state | state | when:disabled |
| BTN-11 | The control meets the platform's minimum touch-target size. | layout | state | when:touch_input |
| BTN-12 | The accessible label scales with the platform's user text-size setting. | state | state | always |
| BTN-13 | The control submits its containing form without scripting. | event | behavior | when:inside_form |


### From system policy

*Your design system's cross-cutting commitments. Apply to every archetype, including those with no native backing. See `system/policy.md`.*

| id | statement | observe | kind | required |
|---|---|---|---|---|
| POL-02 | A focused control renders a focus indicator distinguishable from its unfocused appearance. | state | state | always |


### Specific to this component

*Decided in this contract's interview. The only rows here that are yours to change without changing something shared.*

| id | statement | observe | kind | required |
|---|---|---|---|---|
| STR-01 | The control does not exceed the inline size of its container. | layout | state | always |
| CMP-03 | Zones are arranged along the inline axis, icon before label. | order | state | when:icon_present |
| ACC-01 | The icon contributes nothing to the accessible name. | name | state | when:icon_present |
| ACC-02 | The label is the sole source of the accessible name. | name | state | always |


## What it contains

| zone | accepts | cardinality | position | if absent |
|---|---|---|---|---|
| label | text | 1 | inline-end | invalid:BTN-02 has no name source |
| icon | component:Icon | 0..1 | inline-start | omitted |

## What it looks like

| property | token | when |
|---|---|---|
| background | `color.action.primary.bg` | always |
| background | `color.action.primary.disabled.bg` | when:disabled |

## What a consumer may pass

| prop | type | required | default |
|---|---|---|---|
| `fullWidth` | boolean | no | `false` |
| `variant` | enum:primary,secondary,ghost | no | `primary` |
| `label` | string | yes | — |
| `disabled` | boolean | no | `false` |
| `onPress` | handler | yes | — |

---

**Counts.** 12 inherited · 1 policy · 4 local =
**17 requirements**, 2 zones, 2 token
slots, 5 props.

Platform resolution — which of these bind where, and how each is observed — is in the
canonical documents, one per platform in `2-canonical/`.
