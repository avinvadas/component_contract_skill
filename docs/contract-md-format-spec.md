# The contract `.md` — format specification

**Status: spec draft.** The authoritative description of the artifact the interview produces.
Consolidates what was scattered across `contract-format-v3-proposal.md`,
`l0-archetype-spec.md`, and `contract-property-validation-map.md`.

This is the only artifact in the system a human writes or reads by choice. Everything
downstream — the canonical document, the verifiers, the reports — is plumbing that exists to
serve it.

## Source, and the resolved view

The contract `.md` is **source**: thin, deltas only, the component-specific rows and nothing
else. The archetype is **shared**: abstract by construction, because it is inherited by every
component of that kind.

Neither reads as *"what this component is"*, and that is not a flaw in either — it is the
signature property of any delta-based inheritance. CSS rules versus computed styles. A class
versus its full method list. Docker layers versus the flattened image. In every one, the
source is thin, the parent is abstract, and the thing a person wants to read is neither.

The resolution in all of those is the same, and it is **never merging the sources**:

> **`Button.md` is source. `Button.resolved.md` is the reading artifact** — generated,
> platform-neutral, complete, showing every requirement from all three layers with its
> origin.

Merging the files instead would cost both things the split is carrying. Transcribing an
archetype's rows into every contract that inherits it means nothing enforces they stay
identical, and two contracts disagreeing about what "being a button" means is the exact
failure this project exists to prevent. And the split carries information: **inherited rows
are facts about platforms; local rows are decisions your team made.** A reader asking "why
does our Button require Space activation?" needs the answer "the platform gives it free" and
not "we chose it" — because only one of those is open to revision.

So the resolved view groups by origin rather than hiding it:

| Group | Meaning |
|---|---|
| Inherited from archetype | facts about what platforms provide free — not yours to negotiate |
| From system policy | your design system's cross-cutting commitments |
| Specific to this component | decided in this contract's interview |

`docs/examples/pipeline/resolve_view.py` generates it.

## Two readers, one document

| Reader | Needs |
|---|---|
| a person | chapters that match how design decisions are actually made |
| the resolver | every non-prose cell to parse deterministically into the canonical document |

These pull against each other exactly once — in the cells that read best as prose. The
**parse contract** below is where that tension is resolved, and it is the part of this spec
most likely to be wrong.

## File shape

```
---
frontmatter
---

# Component Contract: <Name>

## 1. Intent
## 2. Structure
## 3. Composition
## 4. Appearance
## 5. Behavior
## 6. Accessibility
```

Six chapters, always in this order, always present. A chapter with nothing to say says so in
one line rather than being omitted — an absent chapter is indistinguishable from an
overlooked one.

## Frontmatter

| Field | Required | Value |
|---|---|---|
| `component` | yes | PascalCase name |
| `version` | yes | semver |
| `status` | yes | `Draft` · `Review` · `Stable` · `Deprecated` |
| `archetype` | yes | one id from the archetype library, or `none` |
| `policy` | yes | path to the L1 policy file |
| `platforms` | yes | list from `web · ios · android · macos · windows` |
| `last_updated` | yes | ISO date |

`archetype` is the highest-leverage line in the file: it inherits a whole bundle of
requirements that never appear in this document. `none` is legal and means the component has
no native archetype — correct for tabs, drag-to-reorder, and anything composed from scratch.

---

## 1 · Intent

Prose. Two to four sentences: what the component is for, and what distinguishes it from its
nearest neighbour.

**Never parsed, never validated.** It is what makes every requirement below legible, not a
claim about an implementation. One line follows it, generated rather than authored:

> Inherits: `button` archetype (BTN-01 … BTN-13) and system policy (POL-01 … POL-04).

## 2 · Structure

**What the component is, independent of what it contains.**

### 2.1 Requirements

| id | statement | observe | kind | required |
|---|---|---|---|---|

Facts about the component as a whole: its semantic identity, its own layout constraints,
what it renders above or within.

### 2.2 Adaptive layout

| condition | what changes |
|---|---|

### 2.3 Layout props

| prop | type | required | default | description |
|---|---|---|---|---|

Props that affect the component's own geometry. Kept apart from visual variants and
behavioral props, which live in chapters 4 and 5 — the separation is the point, and
physical distance is what enforces it.

## 3 · Composition

**What it contains, and on what terms.**

### 3.1 Zones

| id | zone | accepts | cardinality | position | absent |
|---|---|---|---|---|---|

### 3.2 Arrangement

| id | statement | observe | kind | required |
|---|---|---|---|---|

Relations *between* zones: axis, alignment, gap. Stated as geometry, never as a style
declaration — *zones are arranged along the inline axis*, never `flex-direction: row`. Every
platform exposes bounding boxes; none of them exposes flexbox.

### 3.3 Delegation

A zone whose `accepts` names a component is governed by that component's contract. Record it
here and nowhere else — not again under Appearance, Behavior, or Accessibility.

## 4 · Appearance

### 4.1 Token slots

| id | property | token | required |
|---|---|---|---|

### 4.2 Interaction states

| state | what changes | driven by |
|---|---|---|

`driven by`: `prop` · `platform` · `both`. The distinction matters — a platform-drawn pressed
state is not something an implementation must produce, and a prop-driven one is.

### 4.3 Visual variants

| prop | type | required | default | description |
|---|---|---|---|---|

## 5 · Behavior

### 5.1 Requirements

| id | statement | observe | kind | required |
|---|---|---|---|---|

### 5.2 Events

| id | direction | name | payload | when |
|---|---|---|---|---|

`direction`: `emitted` · `received`. Both in one table — v1's §5.3/§5.4 split produced two
tables with identical columns, and T1 found `received` homeless partly because of it.

### 5.3 Behavioral props

| prop | type | required | default | description |
|---|---|---|---|---|

## 6 · Accessibility

**Composition owns a zone's existence and terms. Accessibility owns its semantic exposure.**

Composition says *a title zone exists, accepts text, cardinality 1, block start*.
Accessibility says *the title is exposed as a heading and is the accessible name source*.
Nothing is stated twice.

| id | statement | observe | kind | required |
|---|---|---|---|---|

Holds: semantic exposure · name source · grouping · traversal order · focus policy ·
announcements · input beyond the archetype bundle.

**Traversal order belongs here, not in Composition.** It needs stating separately from
arrangement only because assistive technology and sequential focus traverse it — if the two
always agreed, one statement would do. So *"traversal order corresponds to visual
arrangement"* is an accessibility requirement, which is where a reviewer looks for it.

---

## Divergences

Not a seventh chapter. A divergence appears **in the chapter whose fact it modifies**, as a
final sub-table:

```markdown
### Divergences
| platform | affects | deviation | reason |
|---|---|---|---|
| ios | CMP-04 | grabber and drag-to-dismiss; no close control | `.sheet` convention — a close control duplicates the drag and reads as foreign |
```

`reason` is mandatory. A divergence without one is a lint failure, not a valid contract. It
is the most drift-prone sentence in the document and the one a future reader most needs.

## Inheritance

| Operation | Ceremony |
|---|---|
| **add** a component-specific requirement | none — number it in the component's namespace |
| **constrain** an inherited requirement further | none — stricter is always safe |
| **diverge** on one platform | a Divergences row with a reason |
| **weaken or drop** an inherited requirement | **not expressible** |

If an archetype's bundle is wrong for a whole class of component, fix L0 — or the component
is a different archetype.

---

# The parse contract

The resolver must extract the canonical document deterministically. That requires knowing
exactly which cells are prose and which are tokens.

## Exactly three prose fields exist

`statement`, `intent`, and `reason`. They are **carried verbatim and never interpreted** —
`statement` becomes the text a failing check reports, `reason` is read by humans, `intent` is
read by nobody but a person.

**Every other cell is a token from a closed vocabulary.** If a new cell needs prose, that is
evidence a vocabulary is missing, not that prose should be allowed.

## Five fields that read well and parse badly

The audit this spec exists to produce. Each was prose in the worked examples and each needs a
grammar.

### 1 · `required` — conditions

Reads: *when a hardware keyboard is present*. Parses: nothing.

```
required := always | when:<condition> | when:<condition>,<condition>
condition ∈ hardware_keyboard · touch_input · pointer_input · reduced_motion
           · disabled · inside_form · rtl · <zone>_present
```

A verifier evaluates the token against its own capability declaration. Prose here means the
resolver cannot emit a canonical document at all.

### 2 · `cardinality`

```
cardinality := <n> | <n>..<m> | <n>+
```

**Use `..`, never a dash.** The worked examples used `0–1` with an **en-dash**, which is what
a Markdown editor produces and what a naive parser splitting on `-` silently mangles. Declare
one separator and lint for the others.

### 3 · `accepts`

Reads: *text*, *Icon component*, *arbitrary content*, *Button*. Three different kinds of
thing in one column.

```
accepts := text | content | component:<Name> | component:<Name>|<Name>
```

`text` is a string the component renders. `content` is arbitrary consumer-supplied children.
`component:<Name>` is delegation and triggers §3.3.

### 4 · `position`

Reads: *inline start*, *after title*, *last in reading order*, *see Divergences*. The last is
not a position at all.

```
position := block-start | block-end | inline-start | inline-end
          | after:<zone> | before:<zone> | diverges
```

`diverges` is explicit and requires a matching Divergences row — never a prose pointer.

### 5 · `absent`

Reads: *invalid — BTN-02 has no name source*. That is a verdict and an explanation fused into
one cell. Split them:

```
absent := invalid:<reason> | omitted | fallback:<zone>
```

The verdict is the token; the reason rides along as prose and is reported when the lint fires.

### 6 · Any cell containing `|`

Found by generating the resolved view, not by writing the spec — which is the point of
building things.

An enum prop type reads `primary|secondary|ghost`, and `|` is the table delimiter. Markdown's
escape (`\|`) is correct authoring and a naive splitter mangles it into three broken cells.

```
type := <scalar> | enum:<value>,<value>,... | component:<Name> | handler
```

Two defences, because one is not enough. The grammar prefers `enum:a,b,c` so the hazard does
not arise; and **every parser must split on unescaped pipes only**, because a human will
write `a\|b` anyway and be right to.

Same class as the en-dash: a value whose own punctuation collides with the format's.

## Lint rules

| Rule | Why |
|---|---|
| all six chapters present, in order | an absent chapter is indistinguishable from an overlooked one |
| every non-prose cell parses against its grammar | otherwise the canonical document is incomplete and nobody notices |
| every `diverges` position has a matching Divergences row | dangling reference |
| every Divergences row has a non-empty `reason` | the rule that keeps divergence honest |
| every requirement id is unique within the component | ids are the join to everything downstream |
| no id collides with an inherited archetype or policy id | silent shadowing |
| no `component:<Name>` names a contract that does not exist | dangling delegation |
| every zone referenced by `after:` / `before:` exists | dangling reference |
| en-dash, em-dash or hyphen in a `cardinality` cell | the parse hazard above, caught explicitly |
| an unescaped `\|` inside a cell value | collides with the table delimiter; use `enum:a,b,c` or escape it |

---

## Worked example — Button

```markdown
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
The primary means of performing an action in place. Carries a text label, optionally
preceded by a decorative icon. Unlike Link, it does not navigate.

Inherits: `button` archetype (BTN-01 … BTN-13) and system policy (POL-01 … POL-04).

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
| CMP-03 | Zones are arranged along the inline axis, icon before label. | order | state | always |
| CMP-04 | The gap between icon and label is the only space between them. | layout | state | when:icon_present |

## 4. Appearance
### 4.1 Token slots
| id | property | token | required |
|---|---|---|---|
| APP-01 | background | `color.action.primary.bg` | always |
| APP-06 | background | `color.action.primary.disabled.bg` | when:disabled |
| APP-04 | gap | `space.inline.sm` | when:icon_present |

### 4.2 Interaction states
| state | what changes | driven by |
|---|---|---|
| pressed | background | both |
| disabled | background, label colour | prop |

### Divergences
| platform | affects | deviation | reason |
|---|---|---|---|
| ios | pressed | the platform's automatic dimming is used; no pressed token | overriding it fights the system's contrast and accessibility settings, and a custom pressed fill reads as foreign |

### 4.3 Visual variants
| prop | type | required | default | description |
|---|---|---|---|---|
| `variant` | `primary`\|`secondary`\|`ghost` | no | `primary` | emphasis level |

## 5. Behavior
### 5.2 Events
| id | direction | name | payload | when |
|---|---|---|---|---|
| BEH-01 | emitted | `press` | none | on activation, unless disabled |

### 5.3 Behavioral props
| prop | type | required | default | description |
|---|---|---|---|---|
| `label` | string | yes | — | the accessible name source |
| `disabled` | boolean | no | `false` | blocks activation |
| `onPress` | handler | yes | — | receives `press` |

## 6. Accessibility
| id | statement | observe | kind | required |
|---|---|---|---|---|
| ACC-01 | The icon contributes nothing to the accessible name. | name | state | when:icon_present |
| ACC-02 | The label is the sole source of the accessible name. | name | state | always |
```

Eleven rows of component-specific fact. Everything else — the whole button bundle, the whole
policy — is inherited by one line of frontmatter.

## Open

1. **Is `observe`/`kind` too much machinery for a design document?** They appear in four
   chapters and a designer will never write them. The resolver may be able to derive both
   from the chapter and the statement's verb, which would remove two columns from the
   reader's view. Worth testing before treating them as settled.
2. **Where do archetype-level requirements appear to a reader?** Nowhere in this file, which
   is the point — but a reader wanting the full picture needs the generated per-platform
   resolved requirements document. That document is not yet specified.
3. **Chapter 2 is thin for simple components.** Button has one Structure requirement. That is
   honest, but it invites padding — worth a lint that flags a chapter existing only to be
   non-empty.
