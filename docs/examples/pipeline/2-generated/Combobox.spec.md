# Combobox — spec

> **Generated. Do not edit.** Source: `Combobox.md` v1.0 + archetype `combobox` v1.0 + system policy.
> **Platform-neutral** — what the component *is*, before any platform's vocabulary.
> How each requirement is *observed* per platform is in the `Combobox.<platform>.json` files beside this one.

**Origin** marks what is yours to change. *this component* — decided in your interview. *archetype* — a fact about what platforms provide free; changing it means a platform changed. *policy* — your design system's cross-cutting commitment.

## 1. Intent

Lets someone pick one value from a known set while still being able to type it — for when the
set is long enough to need searching but short enough to show.

## 2. Structure

### Element

Which element carries the role on each platform — checked, not just documented.

| platform | element |
|---|---|
| web | custom — an `<input>` carrying the combobox pattern; `<datalist>` cannot be styled |
| ios | custom — a `TextField` composed with a list; there is no native combobox |
| android | `ExposedDropdownMenuBox` |

### Native backing

Where a platform gives you this free, and where you build it by hand.

| Platform | Native backing |
|---|---|
| macOS | `NSComboBox` — a real native control |
| Android | `ExposedDropdownMenuBox` — close, and in the catalogue |
| Web | `role="combobox"` is an ARIA pattern; `<datalist>` is native but barely styleable |
| iOS | **none** — composed by hand every time |

### Requirements

| when | statement | origin | id |
|---|---|---|---|
| — | The entry remains editable after a candidate is committed. | archetype `combobox` | id-CBX-09 |

### Required children

| zone | accepts | cardinality | position | if absent |
|---|---|---|---|---|
| entry | text | 1 | block-start | invalid:CBX-02 has no name source |
| list | component:Listbox | 1 | block-end | invalid:CBX-04 has nothing to associate |

### Optional children

*None.*

## 3. Appearance

### Interaction states

| state | what changes | driven by | valid because |
|---|---|---|---|
| hover | — | platform | archetype `combobox` |
| focus-visible | — | platform | archetype `combobox` |
| disabled | — | prop | archetype `combobox` |
| expanded | — | prop | archetype `combobox` |

### Tokenised properties

*None.*

### Platform tokens

*None. Every platform uses the same token, spelled its own way — see the per-platform JSON beside this file for each platform's name.*

### Token gaps

*None. Every declared property resolves.*

### Requirements

| when | statement | origin | id |
|---|---|---|---|
| — | A focused control renders a focus indicator distinguishable from its unfocused appearance. | policy | id-POL-02 |

### Platform distinctions

*None recorded. Every platform satisfies the above identically.*

## 4. Behavior

### State machine

| from | event | to | origin | id |
|---|---|---|---|---|
| collapsed | open | expanded | archetype `combobox` | id-CBX-T1 |
| expanded | dismiss | collapsed | archetype `combobox` | id-CBX-T2 |
| expanded | commit | collapsed | archetype `combobox` | id-CBX-T3 |
| collapsed | commit | n/a — no candidate is reachable while the list is closed | archetype `combobox` | — |
| collapsed | type | expanded | this component | id-MCH-01 |

**Closure.** 2 states × 4 events = 8 cells. The 3 nobody wrote are each checked to change no state: `collapsed × dismiss`, `expanded × open`, `expanded × type`.

### Requirements

| when | statement | origin | id |
|---|---|---|---|
| when:expanded | The platform's list-navigation input moves between candidates. | archetype `combobox` | id-CBX-06 |
| when:following:CBX-T2 | No value is committed. | archetype `combobox` | id-CBX-07 |
| when:following:CBX-T3 | The committed candidate's value is placed in the entry. | archetype `combobox` | id-CBX-08 |

### Events

*None.*

## 5. Accessibility

Reviewable as an aspect: everything governing how the component is exposed, named, traversed and announced.

| when | statement | origin | id |
|---|---|---|---|
| — | The control is exposed to assistive technology as a combo box. | archetype `combobox` | id-CBX-01 |
| — | The control has a non-empty accessible name. | archetype `combobox` | id-CBX-02 |
| — | Whether the candidate list is open is conveyed to assistive technology. | archetype `combobox` | id-CBX-03 |
| when:expanded | The active candidate is conveyed without focus leaving the entry. | archetype `combobox` | id-CBX-05 |

### Platform distinctions

*None recorded. Every platform satisfies the above identically.*

## What a consumer may pass

| prop | type | required | default |
|---|---|---|---|
| `label` | string | yes | — |
| `options` | array | yes | — |
| `onCommit` | handler | yes | — |

---

10 requirements — 0 local, 9 inherited, 1 policy · 2 zones · 0 token cases — 0 bound, 0 gaps, 0 n/a · 3 props
