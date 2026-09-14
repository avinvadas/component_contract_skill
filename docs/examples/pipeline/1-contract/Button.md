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

| id | statement | observe | kind | required |
|---|---|---|---|---|
| STR-01 | The control does not exceed the inline size of its container. | layout | state | always |

### 2.3 Layout props

| prop | type | required | default | description |
|---|---|---|---|---|
| `fullWidth` | boolean | no | `false` | fills the container's inline size |

## 3. Composition

### 3.1 Zones

| id | zone | accepts | cardinality | position | absent |
|---|---|---|---|---|---|
| CMP-01 | label | text | 1 | inline-end | invalid:BTN-02 has no name source |
| CMP-02 | icon | component:Icon | 0..1 | inline-start | omitted |

### 3.2 Arrangement

| id | statement | observe | kind | required |
|---|---|---|---|---|
| CMP-03 | Zones are arranged along the inline axis, icon before label. | order | state | when:icon_present |

## 4. Appearance

### 4.1 Token slots

| id | property | token | required |
|---|---|---|---|
| APP-01 | background | `color.action.primary.bg` | always |
| APP-06 | background | `color.action.primary.disabled.bg` | when:disabled |

### 4.3 Visual variants

| prop | type | required | default | description |
|---|---|---|---|---|
| `variant` | primary\|secondary\|ghost | no | `primary` | emphasis level |

## 5. Behavior

### 5.2 Events

| id | direction | name | payload | when |
|---|---|---|---|---|
| BEH-01 | emitted | press | none | on activation, unless disabled |

### 5.3 Behavioral props

| prop | type | required | default | description |
|---|---|---|---|---|
| `label` | string | yes | — | the accessible name source |
| `disabled` | boolean | no | `false` | blocks activation |
| `onPress` | handler | yes | — | receives press |

## 6. Accessibility

| id | statement | observe | kind | required |
|---|---|---|---|---|
| ACC-01 | The icon contributes nothing to the accessible name. | name | state | when:icon_present |
| ACC-02 | The label is the sole source of the accessible name. | name | state | always |
