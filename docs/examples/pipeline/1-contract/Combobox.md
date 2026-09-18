---
component: Combobox
version: 1.0
status: Draft
role-archetype: combobox
policy: design-system/policy.md
platforms: [web, ios, android]
last_updated: 2026-09-17
---

# Component Contract: Combobox

## 1. Intent

Lets someone pick one value from a known set while still being able to type it — for when the
set is long enough to need searching but short enough to show.

## 2. Structure

*Inherited in full from `role-archetype: combobox`. Nothing component-specific.*

## 3. Composition

### 3.1 Zones

| zone | accepts | cardinality | position | absent | id |
|---|---|---|---|---|---|
| entry | text | 1 | block-start | invalid:CBX-02 has no name source | id-CMP-01 |
| list | component:Listbox | 1 | block-end | invalid:CBX-04 has nothing to associate | id-CMP-02 |

## 4. Appearance

*No component-specific requirements.*

## 5. Behavior

### 5.4 Machine

The archetype supplies open, dismiss and commit. This contract adds one transition: typing
into a closed entry opens the list. That is a product decision — the archetype says nothing
about typing — so it lives here, and closure is computed over both sets of rows together.

| from | event | to | id |
|---|---|---|---|
| collapsed | type | expanded | id-MCH-01 |

### 5.3 Behavioral props

| prop | type | required | default | description |
|---|---|---|---|---|
| `label` | string | yes | — | the accessible name source |
| `options` | array | yes | — | the candidate values |
| `onCommit` | handler | yes | — | receives the committed value |

## 6. Accessibility

*Inherited in full from `role-archetype: combobox` and policy.*
