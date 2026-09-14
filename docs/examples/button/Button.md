---
component: Button
version: 1.0
status: Draft
archetype: button
policy: system/policy.md
platforms: [web, ios, android]
---

# Component Contract: Button

## 1. Intent

The primary means of performing an action in place. Carries a text label, optionally
preceded by a decorative icon.

**Inherits:** `button` archetype (BTN-01 … BTN-13) and system policy (POL-01 … POL-03).
Only what is specific to Button appears below.

## 2. Composition

| id | zone | accepts | cardinality | position | absent |
|---|---|---|---|---|---|
| CMP-01 | label | text | 1 | inline end of icon | invalid — BTN-02 has no name source |
| CMP-02 | icon | Icon component | 0–1 | inline start | no icon shown |

| id | statement | observe | kind |
|---|---|---|---|
| CMP-03 | Zones are arranged along the inline axis, icon before label. | order | state |

## 3. Appearance

| id | property | token | required |
|---|---|---|---|
| APP-01 | background | `color.action.primary.bg` | variant = primary |
| APP-02 | label colour | `color.action.primary.fg` | variant = primary |
| APP-03 | corner radius | `radius.control` | always |
| APP-04 | icon–label gap | `space.inline.sm` | when CMP-02 present |
| APP-05 | pressed background | `color.action.primary.pressed` | while pressed |
| APP-06 | disabled background | `color.action.primary.disabled.bg` | when disabled |
| APP-07 | disabled label colour | `color.action.primary.disabled.fg` | when disabled |

## 4. Accessibility

| id | statement | observe | kind |
|---|---|---|---|
| ACC-01 | The icon is decorative and contributes nothing to the accessible name. | name | state |
| ACC-02 | The label is the sole source of the accessible name required by BTN-02. | name | state |

## 5. API

| id | prop | category | type | required | default |
|---|---|---|---|---|---|
| API-01 | `label` | behavioral | string | yes | — |
| API-02 | `variant` | visual | `primary` \| `secondary` \| `ghost` | no | `primary` |
| API-03 | `disabled` | behavioral | boolean | no | `false` |
| API-04 | `iconName` | behavioral | string | no | — |
| API-05 | `onPress` | behavioral | handler | yes | — |

## 6. Divergences

| platform | affects | deviation | reason |
|---|---|---|---|
| ios | APP-05 | no pressed-background token; the platform's automatic dimming is used | overriding it fights the system's accessibility and contrast settings, and a custom pressed fill reads as foreign on iOS |
