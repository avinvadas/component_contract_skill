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
| `role-archetype` | yes | one id from the role-archetype library, or `none` |
| `policy` | yes | path to the L1 policy file |
| `platforms` | yes | list from `web · ios · android · macos · windows` |
| `last_updated` | yes | ISO date |

**Why `role-archetype` and not `role`.** Every platform calls this a *role* — ARIA's `role`, `AXRole`, Compose's `Role`, UIA's `ControlType`; iOS is the outlier with traits. The compound name keeps that correlation visible while avoiding two collisions: `observe: role` already means *the role a platform reports*, and ARIA's own `role="none"` means *strip this element's semantics*, which is not what `role-archetype: none` means here.

`role-archetype` is the highest-leverage line in the file: it inherits a whole bundle of
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

| when | statement | observe | kind | id |
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

### 2.4 Element

| platform | element | id |
|---|---|---|

Which element carries the role, per platform — `<button>` on the web, SwiftUI `Button` on iOS.
The one table that names platform vocabulary, because the platform is its first column: the
archetype's statement stays neutral and each row is that platform's answer. Each row becomes an
`element` requirement in that platform's canonical document. Required for every platform when
the archetype is not `none`; must be one of the archetype's native backings, or say
`custom — <reason>`.

## 3 · Composition

**What it contains, and on what terms.**

### 3.1 Zones

| zone | accepts | cardinality | position | absent | id |
|---|---|---|---|---|---|

### 3.2 Arrangement

| when | statement | observe | kind | id |
|---|---|---|---|---|

Relations *between* zones: axis, alignment, gap. Stated as geometry, never as a style
declaration — *zones are arranged along the inline axis*, never `flex-direction: row`. Every
platform exposes bounding boxes; none of them exposes flexbox.

### 3.3 Delegation

A zone whose `accepts` names a component is governed by that component's contract. Record it
here and nowhere else — not again under Appearance, Behavior, or Accessibility.

## 4 · Appearance

### 4.1 Token slots

| when | property | token | scope | id |
|---|---|---|---|---|

`token` is a token path, a pattern over a visual-variant prop (`component.button.{kind}-hover`),
`n/a — <reason>`, or `—` for a case the tree has not answered — a gap. What the tree answers is
written back into the contract (`scripts/writeback.py`), so a finished contract shows its tokens.
`scope` is how specific the token is to this component — `component`, `shared:<group>` or
`semantic` — computed from the tree and checked; one row, one scope. An optional `transform`
column states `alpha N%`.

### 4.2 Interaction states

| state | what changes | driven by |
|---|---|---|

**Every interaction state valid for the component is answered** — the archetype's
`interaction-states`, plus any the contract's frontmatter adds; the closed set is
`system/vocabulary/interaction-states.json`. `what changes` lists the properties that take
their own token in that state, or `—`; a valid state with no row fails the parse. Every
property not listed keeps its rest token: the resolver generates that case per state and
variant as an alias (`alias_of`), and a verifier checks it with the state forced. `nothing` is
not an answer — it meant different things in different places.
4.1 and 4.2 agree both ways: a property listed for a state has a 4.1 slot in that state and a
rest slot, and a 4.1 slot in a state is listed here.

`driven by`: `prop` · `platform` · `both`. The distinction matters — a platform-drawn pressed
state is not something an implementation must produce, and a prop-driven one is.

A 4.1 slot without a `<prop>=<value>` condition applies to every value of the component's
visual-variant props, and the resolver expands it into one case per value; a row naming a value
overrides the general row for that value only. So every state × property × variant is a case.

### 4.3 Visual variants

| prop | type | required | default | description |
|---|---|---|---|---|

## 5 · Behavior

### 5.1 Requirements

| when | statement | observe | kind | id |
|---|---|---|---|---|

### 5.2 Events

| when | direction | name | payload | id |
|---|---|---|---|---|

`direction`: `emitted` · `received`. Both in one table — v1's §5.3/§5.4 split produced two
tables with identical columns, and T1 found `received` homeless partly because of it.

### 5.3 Behavioral props

| prop | type | required | default | description |
|---|---|---|---|---|

### 5.4 Machine

| from | event | to | id |
|---|---|---|---|

Optional — only for a component that owns state which moves. It holds **the machine as a
machine**: every transition someone cares about, in one table read at a glance. It states
state changes only; anything else that happens is an effect, written as an ordinary 5.1
requirement conditioned `when:following:<transition-id>`.

Every cell of the grid *states × events* is exactly one of:

| cell | written as | becomes in the canonical |
|---|---|---|
| authored | a row | a requirement: from `from`, the event moves to `to` |
| unreachable | `to` is `n/a — reason` | nothing — the event cannot happen in that state |
| closure | nothing | a **generated** requirement: the event changes no state |

Closure is the claim a machine makes that no row states — *these are all the transitions* —
and it is the reason to write a table rather than a list of requirements. The resolver
generates it; nobody writes it. Its ids are derived from the cell (`closure~<from>~<event>`),
never a counter, so a finding keeps its id across runs.

**Closure is computed on the resolved machine**: archetype rows and contract rows together. A
role-archetype supplies what the platform provides (a combobox opens, dismisses, commits); a
contract adds product decisions (typing opens the list). Computed per file, each half would
forbid the other's transitions.

**A machine covers only state its own component owns.** A child's state is opaque to the
parent and checked by the child's own contract. This is what keeps grids small: composition
turns the parent's multiplication into addition. The one exception is state a parent
genuinely coordinates — a combobox's open list with focus held in the entry — which is why
that machine lives in the parent.

**Bindings.** A `machine` block in any bindings file, merged across layers like everything
else: per platform, how each state is observed and which trigger performs each event. An
effect never restates a trigger — `following:` names the transition that performs it.

```json
"machine": {
  "states": { "expanded": { "web": { "contains": "expanded" } } },
  "events": { "dismiss":  { "web": "key:Escape", "android": "system:back" } }
}
```

## 6 · Accessibility

**Composition owns a zone's existence and terms. Accessibility owns its semantic exposure.**

Composition says *a title zone exists, accepts text, cardinality 1, block start*.
Accessibility says *the title is exposed as a heading and is the accessible name source*.
Nothing is stated twice.

| when | statement | observe | kind | id |
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

## `when` leads; a statement never restates its condition

Column order in every requirement table is **`when`, `statement`, … , `id`** — condition
first, predicate second, metadata last.

That ordering exists to enforce a rule, not merely to read nicely:

> **A statement must not restate its condition.** The `when` column supplies the context; the
> statement supplies only what must be true.

Before the `when` column existed, statements carried their own context and said it twice:

| | |
|---|---|
| was | `When disabled, activation performs no action.` · `when:disabled` |
| now | `when:disabled` · `Activation performs no action.` |

Statements become shorter, directly comparable, and — the real gain — **a predicate rather
than a sentence**. Two requirements differing only in condition now differ only in one cell.

**Lint heuristic:** a statement beginning *When*, *While*, *Where* or *If* is almost always
restating its condition. Not always wrong, but always worth a look.

Two consequences to carry through:

**A report must compose them.** Since the statement no longer stands alone, a failing check
prints the scenario with it — `[disabled=True] The control is removed from sequential focus
navigation.` — which is better than the old form anyway, because it names which scenario
failed rather than implying it.

**`always` stays explicit in the source and renders as `—` in the view.** Explicit is
lintable and unambiguous; in a chapter where most rows are unconditional, a column of the
word "always" is ink with no signal.

## The id column is metadata, and is presented as such

Requirement ids join every artifact downstream, but a reader scanning a chapter does not
want a row to *begin* with one. So in the `.md` the id column:

- sits **last**, not first — the statement is what the eye should land on
- carries an **`id-` prefix**, which labels it as machine metadata rather than content

```
| statement | observe | kind | required | chapter | source | id |
|---|---|---|---|---|---|---|
| The content is available to assistive technology as text. | name | state | always | Accessibility | catalogue:Web/text | id-TXT-01 |
```

**Visual de-emphasis is deliberately not attempted.** Plain Markdown has no colour, and the
options — `<sub>`, italics, backticks — each trade something: `<sub>` is HTML a strict
renderer may strip, italics collide with emphasis used for meaning, backticks imply code.
Position plus prefix already does most of the work. Revisit only if real documents prove it
insufficient; the parser tolerates the decorated forms in the meantime, so adding one later
breaks nothing.

**None of that decoration travels.** The parser strips tags and prefix, and canonical
documents, test names and reports carry the bare `TXT-01`, where the extra characters would
be pure noise. Lenient parse, strict lint: accept `TXT-01`, `id-TXT-01`, `` `id-TXT-01` `` and
the ghosted form; lint the authored files to one.

Strip in **two passes** — tags first, then the prefix. A single pass with an anchored `^id-`
never matches, because at that point the string still starts with `<sub>`. That bug shipped
once already.

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
| every `following:<id>` names a declared transition | dangling reference |
| no machine state is a zone name or dotted into a child | a parent's grid that includes child state is their product, and closure inflates |
| no two machine rows share `(from, event)` with different `to` | two machines, not one |
| no self-transition (`from` equals `to`) | closure already implies it; if it has an effect, that is a requirement |
| every unreachable cell has a reason | the rule that keeps exclusions honest |
| every machine state and event has a binding on every platform | a transition with no trigger cannot be checked or excused |

---

## Worked example — Button

**Copied verbatim from `docs/examples/pipeline/1-contract/Button.md`,** which the
resolver actually parses. Kept identical on purpose: a spec whose example has drifted
from the thing it specifies is worse than no example, and this one had — it still
showed `id` first and `required` where the rules above say `when`.

```markdown
---
component: Button
version: 1.0
status: Draft
archetype: button
policy: design-system/policy.md   # optional — `contracts.policy` in the design-system context is the default
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

| property | token | required | id |
|---|---|---|---|
| background | `color.action.primary.bg` | always | id-APP-01 |
| background | `color.action.primary.disabled.bg` | when:disabled | id-APP-06 |

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
```

Eleven rows of component-specific fact. Everything else — the whole `button` bundle,
the whole policy layer — arrives through one line of frontmatter.

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
