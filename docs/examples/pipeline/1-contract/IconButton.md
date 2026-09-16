---
component: IconButton
version: 1.0
status: Draft
role-archetype: button
policy: system/policy.md
tokens: ../../../../evals/fixtures/tokens/design-tokens.json
platforms: [web, ios, android]
last_updated: 2026-09-16
---

# Component Contract: IconButton

## 1. Intent

A button whose only visible content is an icon. Used where space is constrained and the
action is conventional enough to be recognised without a label — close, back, overflow.

## 2. Structure

### 2.1 Requirements

| when | statement | observe | kind | id |
|---|---|---|---|---|
| always | The control's inline and block sizes are equal. | layout | state | id-STR-01 |

## 3. Composition

### 3.1 Zones

| zone | accepts | cardinality | position | absent | id |
|---|---|---|---|---|---|
| icon | component:Icon | 1 | block-start | invalid:the control has no visible content | id-CMP-01 |

## 4. Appearance

### 4.1 Token slots

| when | property | token | id |
|---|---|---|---|
| always | background | — | id-APP-01 |
| when:disabled | background | — | id-APP-06 |

## 5. Behavior

### 5.2 Events

| when | direction | name | payload | id |
|---|---|---|---|---|
| on activation, unless disabled | emitted | press | none | id-BEH-01 |

### 5.3 Behavioral props

| prop | type | required | default | description |
|---|---|---|---|---|
| `label` | string | yes | — | the accessible name; never rendered visibly |
| `iconName` | string | yes | — | which icon to render |
| `disabled` | boolean | no | `false` | blocks activation |
| `onPress` | handler | yes | — | receives press |

## 6. Accessibility

| when | statement | observe | kind | id |
|---|---|---|---|---|
| always | The accessible name is supplied by the `label` prop, since no rendered content can provide one. | name | state | id-ACC-02 |
| always | The icon contributes nothing to the accessible name. | name | state | id-ACC-01 |
