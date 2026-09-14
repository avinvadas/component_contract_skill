# What a contract states, and when each part is validated

Every property a v3 contract can hold, by chapter, with where and when it is checked.
Companion to `contract-format-v3-proposal.md`. Building this surfaced five gaps, listed
at the end.

## Three validation moments, not two

| Moment | Subject | Needs an implementation? |
|---|---|---|
| **Lint** | the contract and its generated schemas, checked against each other and against L0/L1 | no |
| **Build** | source-level facts: API surface, token references | yes — compiles only |
| **Run** | rendered facts (`structure`) and driven facts (`behavior`) | yes — runs |

Lint has been mentioned piecemeal throughout (reasons are mandatory, alignment is an
invariant, archetypes must be complete) without being named as a moment. It is the cheapest
of the three and catches a whole class the others cannot: a contract that is wrong about
itself.

Conformance levels map onto the last two: **L1** = build, **L2** = build + rendered,
**L3** = build + rendered + driven. Lint runs at every level, including level 0.

---

## 0 · Frontmatter

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| `component` | — | build | 1 | `manifest.contract` must match |
| `version` | — | build | 1 | `manifest.contract_version` must match |
| source hash | — | lint | 0 | schema embeds it; a stale schema is detectable |
| `archetype` | — | lint | 0 | every archetype id must appear in the generated schema |
| `policy` | — | lint | 0 | as above |
| `platforms` | — | lint | 0 | determines which schemas must exist |

## 1 · Intent

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| intent prose | — | **never** | — | deliberately unvalidated |

One chapter with zero machine checks, and that is correct. It is what makes every
requirement below legible; it is not itself a claim about an implementation.

## 2 · Composition

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| zone id | `structure` | run | 2 | via the zone tag — `data-zone`, `accessibilityIdentifier`, `testTag`, `AutomationId` |
| zone accepts — content type | `structure` | run | 2 | what actually rendered in the zone |
| zone accepts — delegated component | `structure` | run | 2 | containment only; **the child's own conformance is a separate run** — see G3 |
| cardinality, as a consumer constraint | `api` | build | 1 | what a caller may legally pass |
| cardinality, as rendered | `structure` | run | 2 | what actually appeared — genuinely two facts, not one |
| position / arrangement | `structure` | run | 2 | geometric relation between zone boxes |
| layout constraints (max size, overflow) | `structure` | run | 2 | geometry |
| absent behaviour | `structure` | run | 2 | needs a capture with the zone absent — see G1 |
| adaptive conditions | `structure` | run | 2 | needs one capture per named condition |

## 3 · Appearance

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| token slot (property → token) | `tokens` | build | 1 | reference resolves through the named token |
| literal denial (POL-04) | `tokens` | build | 1 | deny-by-default across the declared property set |
| cascade override | `tokens` | run | 2 | **web only** — a reference present in source but overridden at render |
| state-driven appearance | `structure` | run | 2 | one capture per state: pressed, disabled, focused, error |
| motion token reference | `tokens` | build | 1 | the reference only |
| motion actually suppressed under reduced-motion | `behavior` | run | 3 | set the preference, then observe |

All of the above is **data-flow only** — that a value arrived through the named token. Not
that the value is right, not that it looks right. That boundary is stated in the proposal
and in the worked example, and it is the one most likely to drift.

## 4 · Behavior

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| interaction requirement | `behavior` | run | 3 | drive and observe |
| events emitted | `behavior` | run | 3 | signature presence is `api`/build; that it *fires* is level 3 |
| events received | `behavior` | run | 3 | dispatch the external event, observe the response |
| state machine transitions | `behavior` | run | 3 | one driven check per transition |
| no observable intermediate state | `structure` | run | 2 | a snapshot claim, despite living in this chapter |

## 5 · Accessibility

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| rendered identity | `structure` | run | 2 | the check that catches a generic element given a role |
| semantic role | `structure` | run | 2 | computed, never authored |
| accessible name | `structure` | run | 2 | computed name |
| name **source** (which zone) | `structure` | run | 2 | **web-strong, native-weak** — see G2 |
| grouping | `structure` | run | 2 | |
| traversal order | `structure` | run | 2 | accessibility-tree order |
| traversal order matches arrangement | `structure` | run | 2 | compares two facts inside one capture |
| state conveyed to AT | `structure` | run | 2 | per-state capture |
| focus policy — initial, containment, return | `behavior` | run | 3 | driven |
| announcements | `behavior` | run | 3 | driven |
| keyboard / gesture input | `behavior` | run | 3 | driven |

## 6 · API

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| prop name | `api` | build | 1 | |
| prop type | `api` | build | 1 | |
| required / optional | `api` | build | 1 | |
| default value | `api` | build | 1 | |
| enum members | `api` | build | 1 | |
| **prop category** (layout / visual / behavioral) | — | **never** | — | see G4 |

## 7 · Divergences

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| the deviation | — | lint | 0 | changes what that platform's schema requires — e.g. APP-05 becomes `n/a` on iOS |
| the reason | — | lint | 0 | **presence** is enforced; content is not and cannot be |

## Cross-cutting, lint only

| Check | Why it matters |
|---|---|
| every requirement appears in exactly one schema per platform | catches a requirement that silently stopped being checked |
| every schema constraint traces to a real requirement id | catches a constraint no requirement authorises |
| `scope` narrower than `all` carries a reason | prevents quiet platform exclusions |
| divergence carries a reason | same |
| archetype bundle is bound on every in-scope platform, or explicitly `n/a` | prevents a hard platform hiding behind omission |
| schema is byte-identical to a fresh generation | prevents hand-patched schemas |
| every requirement is failed by at least one mutation | T3 discrimination — **cannot be checked statically** |

---

## Five gaps this exercise found

**G1 — Captures are a scenario matrix, and the adapter spec does not say so.**
`structure` is not one capture. It is one per (prop configuration × interaction state ×
adaptive condition): the disabled state, the focused state, the icon-absent configuration,
the compact viewport. The Button example has three captures because it was written by hand
to have three. Nothing yet states how an adapter learns which captures to take — that must
come from `checks.json`, and the generator does not emit it yet.

**G2 — Name *source* is weakly checkable off the web.**
"The title is the accessible name source" is verifiable on Web, where the accessibility
tree exposes the labelling relationship. On iOS and Android the label is a string on the
node with no provenance — you can confirm the name matches the title's text, which is
weaker and fails when two zones hold the same string. Record it as a real ceiling rather
than assuming parity.

**G3 — Delegation is unchecked across the boundary.**
`accepts: Icon component` means Icon's contract governs that subtree. Nothing links the two
runs: a Button containing a non-conformant Icon passes Button's contract completely. The
fix is probably a manifest reference — the child's own conformance result cited by id — but
it is not designed.

**G4 — Prop category is unvalidated, and cannot be.**
Layout / visual / behavioral is a distinction v1 spends a whole principle on, and no
manifest can confirm a prop is "visual." It is real and useful — it drives schema
generation and stops the three from being mixed — but it is a **lint-and-review** fact, not
a validated one. Worth saying plainly so nobody assumes the separation is enforced.

**G5 — `structure` invites the same drift the token checks did.**
`box: {w, h}` proves a touch target meets a minimum. It would be an easy slide from there
to asserting layout *looks* right, and the first person to write an adapter will reach for
pixel comparison. The boundary must be written into the structure section before an adapter
exists: geometry is checked as a relation the contract states, never as an appearance
judgment.
