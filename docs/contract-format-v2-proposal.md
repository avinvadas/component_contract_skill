# Contract format v2 — requirements, not manifestations

**Status: proposal.** Raised 2026-09-08.

## The problem with v1

Today a contract states platform manifestations directly: §2.1 holds one row per platform naming `<dialog>`, `.sheet`, `Dialog`. That is a low level of abstraction, and it causes three problems that keep surfacing as separate bugs but are really one:

1. **It contradicts itself on cross-platform frameworks.** Phase 2 says a React Native view is as compliant as SwiftUI if it produces the right traits; §2.1 says the named native control *is* the compliance condition. React Native produces a generic view with traits and never a `UISegmentedControl`, so it passes one rule and fails the other.
2. **It cannot express a hybrid at all.** A WebView-wrapped app is iOS by distribution and DOM by rendering. Neither the iOS row nor the Web row fits.
3. **It forces platforms into one shape.** iOS has no declarative live region, so a row modelled on `aria-live` records a real success as an approximation.

All three come from the same root: **the contract states *how* rather than *what must be true*.**

## The v2 split

> The contract states requirements. A binding file states how each requirement is observed on one platform — whatever technology produced it.

- **`[Component].md`** — platform-neutral. Every requirement is a testable claim about observable outcomes. No markup, no API, no framework.
- **`[Component].[platform].binding.json`** — one per platform: `web`, `ios`, `macos`, `android`. Binds each requirement id to what a test must observe there.

### Rendering technology is not an axis

An app shipped on iOS is an iOS app. React Native, a WebView wrapper, Flutter, hand-written Swift — all of them are judged against the same iOS binding, because the person using the app experiences one platform and does not care what rendered it. There is no `ios-react-native` binding and no softer standard for being cross-platform. A technology that cannot meet the iOS requirements fails them.

**This forces the discipline that makes the whole format work: a binding must bind to the platform's observable surface — its accessibility tree, its runtime behaviour — and never to a widget class.** "Expect a `UISegmentedControl`" is not a legal binding, because it describes an implementation. "Expect an element exposing tab semantics" is, because every technology that ships on iOS ultimately produces entries in the same accessibility tree, and that is what a real assistive-technology user meets.

So the React Native question dissolves rather than being accommodated. It was never a question about React Native — it was v1 binding to widget classes instead of outcomes.

## Requirement anatomy

Every requirement carries five fields, so it is readable as prose and parseable as data:

| Field | Meaning |
|---|---|
| **id** | Stable handle a binding file references. Never reused, never renumbered. |
| **statement** | One sentence, plain language, no platform vocabulary. |
| **observe** | What a test must inspect: `role`, `name`, `state`, `order`, `containment`, `focus`, `announcement`, `event`, `token`. |
| **kind** | `state` — true in a snapshot at rest. `behavior` — only true by doing something and observing the result. This determines how it can be tested at all. |
| **required** | `always`, or a named condition. |

**The `kind` field is what makes the document testable without being platform-specific.** A `state` requirement is checked against a rendered tree. A `behavior` requirement is checked by triggering and observing. Which one a requirement is does not change per platform — but *how it is observed* does, and that is exactly what the binding file carries.

### The neutral role vocabulary

Requirements name roles from a closed, declared set: `button`, `link`, `tab`, `tablist`, `tabpanel`, `dialog`, `heading`, `status`, `checkbox`, `radio`, `radiogroup`, `listitem`, `list`, `image`, `text`.

These names coincide with ARIA's because ARIA has the most complete published role set — but here they denote **the concept**, not the attribute. `role: dialog` does not mean `role="dialog"`; it means "exposed to assistive technology as a modal surface", which the Web binding satisfies with `<dialog>`, iOS with a trait, Android with a pane title.

---

# Worked example — Modal

```markdown
---
component: Modal
version: 2.0
status: Draft
last_updated: 2026-09-08
platforms: [web, ios, android]
---

# Component Contract: Modal

## 1. Intent

A surface that presents focused content over the rest of the interface and prevents
interaction with it until dismissed.

Everything below is a requirement. Nothing below names a platform, a markup element,
or an API — that binding lives in the per-platform files.

## 2. Structure

What the component *is*, independent of what it contains.

| id | statement | observe | kind | required |
|---|---|---|---|---|
| STR-01 | The component is exposed to assistive technology as a modal surface. | role | state | always |
| STR-02 | While it is open, content outside it is not reachable by assistive technology or by pointer. | state | state | always |
| STR-03 | The component has an accessible name taken from its title. | name | state | always |
| STR-04 | The title is exposed as a heading. | role | state | always |

> STR-04 states the title is a heading. It deliberately does not state a heading *level* —
> level is a property of the document the component is mounted in, which this contract
> cannot know. Platforms with no level concept satisfy this fully.

## 3. Composition

What it contains, and on what terms.

| id | zone | accepts | cardinality | order | absent behaviour |
|---|---|---|---|---|---|
| CMP-01 | Title | text | 1 | first in reading order | invalid — the name in STR-03 has no source |
| CMP-02 | Icon | Icon component | 0–1 | precedes Title | no icon shown |
| CMP-03 | Body | arbitrary content | 1 | follows Title | invalid |
| CMP-04 | Close control | — | 0–1 | last in reading order | dismissal relies on BEH-02/03 alone |
| CMP-05 | Footer actions | Button component | 0–3 | after Body | no footer shown |

| id | statement | observe | kind | required |
|---|---|---|---|---|
| CMP-06 | Reading order is Icon, Title, Body, Footer actions, Close control. | order | state | always |
| CMP-07 | Zones delegated to another component are governed by that component's contract, not this one. | containment | state | always |

## 4. Appearance

| id | property | token | required |
|---|---|---|---|
| APP-01 | backdrop colour | `color.overlay.backdrop` | always |
| APP-02 | surface corner radius | `radius.modal` | always |
| APP-03 | surface inset | `space.modal.padding` | always |
| APP-04 | enter/exit transition duration | `motion.duration.medium` | when motion is not reduced |

| id | statement | observe | kind | required |
|---|---|---|---|---|
| APP-05 | When the user has asked for reduced motion, the enter/exit transition does not play. | state | state | always |
| APP-06 | Every value above resolves through the named token; none is a literal. | token | state | always |

## 5. Behaviour

| id | statement | observe | kind | required |
|---|---|---|---|---|
| BEH-01 | Activating the close control dismisses the component. | event | behavior | when CMP-04 present |
| BEH-02 | Activating the platform's standard dismissal gesture or key dismisses the component. | event | behavior | always |
| BEH-03 | Activating outside the surface dismisses the component. | event | behavior | always |
| BEH-04 | Dismissal emits one event naming the cause, distinguishing close control, outside, and standard gesture. | event | behavior | always |
| BEH-05 | Footer action activation is not intercepted; each action performs only its own effect. | event | behavior | when CMP-05 present |
| BEH-06 | The component is either open or closed; there is no intermediate state observable to a consumer. | state | state | always |

> BEH-02 says "the platform's standard dismissal gesture or key" rather than naming Escape
> or a swipe. Which one it is belongs in the binding. That the component honours whichever
> one its platform defines is the requirement.

## 6. Accessibility

| id | statement | observe | kind | required |
|---|---|---|---|---|
| ACC-01 | On opening, focus moves inside the component. | focus | behavior | always |
| ACC-02 | While open, focus cannot leave the component by sequential navigation. | focus | behavior | always |
| ACC-03 | On dismissal, focus returns to the element that opened it. | focus | behavior | always |
| ACC-04 | The close control has an accessible name that conveys dismissal. | name | state | when CMP-04 present |
| ACC-05 | Opening is announced, conveying the component's accessible name. | announcement | behavior | always |
| ACC-06 | Every interactive zone is operable by the platform's primary non-pointer input. | state | behavior | always |
```

---

# The binding files

One per target. Each binds requirement ids to observables. **The contract above is identical for all of them.**

### `Modal.web.binding.json`

```json
{
  "target": "web",
  "contract": "Modal.md",
  "contract_version": "2.0",
  "observe_via": "rendered DOM + computed accessibility tree",
  "bindings": [
    { "id": "STR-01", "observe": "role",   "expect": "dialog",        "note": "native <dialog> preferred; role must resolve to dialog" },
    { "id": "STR-02", "observe": "state",  "expect": "aria-modal=true and background inert" },
    { "id": "STR-03", "observe": "name",   "expect": "accessible name non-empty, sourced from title node" },
    { "id": "STR-04", "observe": "role",   "expect": "heading", "note": "any level; level is out of contract scope" },
    { "id": "CMP-06", "observe": "order",  "expect": ["icon","title","body","footer","close"] },
    { "id": "BEH-02", "observe": "event",  "trigger": "key:Escape", "expect": "dismiss event fires" },
    { "id": "ACC-02", "observe": "focus",  "trigger": "Tab x N", "expect": "focus never leaves subtree" }
  ]
}
```

### `Modal.ios.binding.json`

```json
{
  "target": "ios",
  "contract": "Modal.md",
  "contract_version": "2.0",
  "observe_via": "XCUITest accessibility tree",
  "bindings": [
    { "id": "STR-01", "observe": "role",  "expect": "element is a modally-presented surface" },
    { "id": "STR-02", "observe": "state", "expect": "elements outside the sheet are not accessibility-visible" },
    { "id": "STR-04", "observe": "role",  "expect": "header trait present", "note": "iOS heading is binary; STR-04 fully satisfied" },
    { "id": "BEH-02", "observe": "event", "trigger": "gesture:swipe-down", "expect": "dismiss event fires",
      "note": "iOS standard dismissal is the sheet drag, not a key" },
    { "id": "ACC-05", "observe": "announcement", "trigger": "open",
      "expect": "announcement posted containing the accessible name",
      "note": "iOS has no declarative live region; announcement is posted imperatively. ACC-05 is a behavior requirement, so this is a clean match, not an approximation." }
  ]
}
```

Note what is *not* in that file: any mention of `.sheet`, `UIViewController`, or any other class. Every expectation is phrased against what the accessibility tree exposes. That is what lets a React Native or WebView-hosted implementation be tested by the identical binding — it either produces those semantics or it does not, and if it does not, it fails as an iOS app should.

---

## What this buys

**One source of intent.** The `.md` is the only place a requirement is stated. Adding a platform adds a file; it never edits the contract.

**Requirements survive platform churn.** A new SwiftUI API changes a binding, not the contract.

**Testability is explicit.** `kind` says whether a requirement can be checked from a snapshot at all. The harness stops guessing.

**Honest cross-platform difference.** A platform meeting a requirement differently binds it differently. Nothing is recorded as approximate unless the requirement is genuinely unmet.

**Machine-readable without ceasing to be human-readable.** Every table row is a record; every statement is a sentence.

## What it costs

**The contract can no longer tell an implementer what to type.** v1's §2.1 handed you `<dialog aria-modal="true">`. v2 hands you "exposed as a modal surface" and expects the binding, or the implementer's platform knowledge, to supply the rest. For a skill whose stated promise is that the reader *"does not need to know HTML, ARIA, or native accessibility APIs"*, this is a real regression in one direction — and needs a decision, not a hand-wave. The likely answer is that the binding file becomes the implementer's reference, which means bindings must be generated with the same care §2.1 rows are today.

**More files.** One contract plus one binding per platform — the same count v1 already produces in `structure.json` files.

**The role vocabulary must be maintained.** A closed set is what makes binding possible; it also means an archetype outside the set has nowhere to go until the set grows.

## Open questions

1. Does the interview change? Probably not much — it already asks intent-level questions, and Q2 still asks for platforms.
2. Do bindings get generated per component, or once per target as a reusable mapping? Much of a binding is archetype-level, not component-level.
3. What happens to the existing `structure.json`? It becomes the binding file, with a wider remit.
4. Is `required: always` ever conditional on platform? It should not be — a requirement true only on some platforms is a sign it was written at the wrong level.
5. **What replaces §2.1's compliance-condition rule?** v1 says the named native element *is* the condition, not one option among role-equivalents — imported from the first rule of ARIA use. Under v2 that rule cannot survive as written, because bindings name outcomes rather than elements. The concern behind it is real, though: a generic view patched with semantics does not inherit the keyboard handling, Dynamic Type, and rotor behaviour a native control gives for free. The answer is probably that those become their own explicit requirements rather than being smuggled in by naming a class — which is more honest anyway, since today they are assumed rather than tested.
