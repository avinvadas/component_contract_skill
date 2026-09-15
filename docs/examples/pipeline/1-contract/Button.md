---
component: Button
version: 1.0
status: Draft
archetype: button
policy: system/policy.md
platforms: [web, ios, android]
last_updated: 2026-09-14
---

# Component Contract: Button

## 1. Intent

The primary means of performing an action in place. Carries a text label, optionally preceded
by a decorative icon. Unlike Link, it does not navigate.

## 2. Structure

### 2.1 Requirements

| statement | observe | kind | required | id |
|---|---|---|---|---|
| The control does not exceed the inline size of its container. | layout | state | always | <sub>id-STR-01</sub> |

### 2.3 Layout props

| prop | type | required | default | description |
|---|---|---|---|---|
| `fullWidth` | boolean | no | `false` | fills the container's inline size |

## 3. Composition

### 3.1 Zones

| zone | accepts | cardinality | position | absent | id |
|---|---|---|---|---|---|
| label | text | 1 | inline-end | invalid:BTN-02 has no name source | <sub>id-CMP-01</sub> |
| icon | component:Icon | 0..1 | inline-start | omitted | <sub>id-CMP-02</sub> |

### 3.2 Arrangement

| statement | observe | kind | required | id |
|---|---|---|---|---|
| Zones are arranged along the inline axis, icon before label. | order | state | when:icon_present | <sub>id-CMP-03</sub> |

## 4. Appearance

### 4.1 Token slots

| property | token | required | id |
|---|---|---|---|
| background | `color.action.primary.bg` | always | <sub>id-APP-01</sub> |
| background | `color.action.primary.disabled.bg` | when:disabled | <sub>id-APP-06</sub> |

### 4.3 Visual variants

| prop | type | required | default | description |
|---|---|---|---|---|
| `variant` | enum:primary,secondary,ghost | no | `primary` | emphasis level |

## 5. Behavior

### 5.2 Events

| direction | name | payload | when | id |
|---|---|---|---|---|
| emitted | press | none | on activation, unless disabled | <sub>id-BEH-01</sub> |

### 5.3 Behavioral props

| prop | type | required | default | description |
|---|---|---|---|---|
| `label` | string | yes | — | the accessible name source |
| `disabled` | boolean | no | `false` | blocks activation |
| `onPress` | handler | yes | — | receives press |

## 6. Accessibility

| statement | observe | kind | required | id |
|---|---|---|---|---|
| The icon contributes nothing to the accessible name. | name | state | when:icon_present | <sub>id-ACC-01</sub> |
| The label is the sole source of the accessible name. | name | state | always | <sub>id-ACC-02</sub> |
