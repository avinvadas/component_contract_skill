---
component: Button
version: 1.0
status: Draft
role-archetype: button
policy: system/policy.md
tokens: ../../../../evals/fixtures/tokens/design-tokens.json
platforms: [web, ios, android]
last_updated: 2026-09-14
---

# Component Contract: Button

## 1. Intent

The primary means of performing an action in place. Carries a text label, optionally preceded
by a decorative icon. Unlike Link, it does not navigate.

## 2. Structure

### 2.1 Requirements

| when | statement | observe | kind | id |
|---|---|---|---|---|
| always | The control does not exceed the inline size of its container. | layout | state | id-STR-01 |

### 2.3 Layout props

| prop | type | required | default | description |
|---|---|---|---|---|
| `fullWidth` | boolean | no | `false` | fills the container's inline size |

## 3. Composition

### 3.1 Zones

| zone | accepts | cardinality | position | absent | id |
|---|---|---|---|---|---|
| label | text | 1 | inline-end | invalid:BTN-02 has no name source | id-CMP-01 |
| icon | component:Icon | 0..1 | inline-start | omitted | id-CMP-02 |

### 3.2 Arrangement

| when | statement | observe | kind | id |
|---|---|---|---|---|
| when:icon_present | Zones are arranged along the inline axis, icon before label. | order | state | id-CMP-03 |

## 4. Appearance

### 4.1 Token slots

The contract declares which properties are tokenised. `—` means resolve it from the tree; an
explicit path pins a token, which is then validated rather than re-resolved. A property that
does not apply says so, with a reason — it is never simply left out.

| when | property | token | id |
|---|---|---|---|
| always | background | — | id-APP-01 |
| always | foreground | — | id-APP-02 |
| always | border-color | — | id-APP-03 |
| always | border-width | — | id-APP-04 |
| always | radius | `component.button.radius` | id-APP-05 |
| always | padding-inline | — | id-APP-06 |
| when:hover | background | — | id-APP-07 |
| when:disabled | background | — | id-APP-08 |
| always | elevation | n/a — a Button sits in the content plane | id-APP-09 |

### 4.3 Visual variants

| prop | type | required | default | description |
|---|---|---|---|---|
| `variant` | enum:primary,secondary,ghost | no | `primary` | emphasis level |

## 5. Behavior

### 5.2 Events

| direction | name | payload | when | id |
|---|---|---|---|---|
| emitted | press | none | on activation, unless disabled | id-BEH-01 |

### 5.3 Behavioral props

| prop | type | required | default | description |
|---|---|---|---|---|
| `label` | string | yes | — | the accessible name source |
| `disabled` | boolean | no | `false` | blocks activation |
| `onPress` | handler | yes | — | receives press |

## 6. Accessibility

| when | statement | observe | kind | id |
|---|---|---|---|---|
| when:icon_present | The icon contributes nothing to the accessible name. | name | state | id-ACC-01 |
| always | The label is the sole source of the accessible name. | name | state | id-ACC-02 |
