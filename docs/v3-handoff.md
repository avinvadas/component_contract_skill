# Handoff — contract format v3

**Written 2026-09-09 on Avins-Mac-mini, to carry context to another machine.**
Read this first, then `contract-format-v3-proposal.md` for the format itself.

---

## The problem

> One human-readable design-intent document, abstract enough to hold for every platform,
> specific enough to generate a per-platform JSON Schema that validates an implementation
> at build time.

A button has the same role and essence everywhere even though it is manifested, styled,
and interacted with differently. The contract must capture that essence once, and still be
distinct enough that each platform's build can check its implementation against structure,
accessibility, appearance (correct tokens), and behaviour.

Two hard constraints, both mandatory: **human-readable first, machine-readable second**,
and the document must read as a *design* document — organized by separation of concerns,
not by anything a toolchain finds convenient.

## Where the repo stands

| | |
|---|---|
| **v1** | shipped, in `SKILL.md`. 17 sections. States platform manifestations directly (`<dialog>`, `.sheet`, `Dialog`). |
| **v2** | proposed in `contract-format-v2-proposal.md`. **Failed its own T1 coverage audit** — see `v2-t1-coverage-audit.md`, seven named gaps, one of which (no props section) breaks schema generation entirely. Not adopted. |
| **v3** | proposed in `contract-format-v3-proposal.md`, commit `911ec1f`. Current working direction. |

Supporting instruments already built and still valid: `v1-implicit-guarantees-catalogue.md`
(what each named construct buys for free, per platform) and
`contract-format-v2-validation-plan.md` (seven failure modes F1–F7, six tests T1–T6).
**Both carry over to v3 unchanged** — the catalogue becomes the source material for v3's
archetype bundles, and the test plan still applies.

---

## Reasoning chain — why v3 looks the way it does

### 1. The MVC/MVVM worry was a false constraint. Dissolved.

The concern was that four concerns (content, appearance, behavior, composition) match Web
but not native, where things are organized through MVC/MVVM.

They are different axes and do not compete. MVC/MVVM are *code-organization* patterns —
where responsibility lives between objects. The four concerns are a *specification
taxonomy* — how a description of the component-as-experienced is partitioned. Since the
contract validates rendered output and never source (`SKILL.md:469`), it cannot care where
the code lives. **The four concerns are already platform-neutral. Nothing needs
reconciling.**

### 2. What v2 actually got wrong: it never said what the schema validates.

A JSON Schema validates JSON. An implementation is Swift, Kotlin, or TypeScript. On Web
this gap is invisible because the DOM is already a queryable tree — which is precisely why
the format ended up Web-shaped and then had to be argued into the native platforms.

**Fix: a third artifact.** The schema validates a **manifest** the implementation's build
emits through an adapter. Contract → schema; source → manifest; schema × manifest →
result. That single indirection is what closes the loop on a compiled platform.

### 3. Two taxonomies, joined by requirement id.

- **Concern** (Structure/Composition, Appearance, Behavior, Accessibility, API) — organizes
  the `.md` for a human. Answers *what kind of decision is this?*
- **Section** (`api`, `tokens`, `structure`, `behavior`) — organizes the manifest for an
  extractor. Answers *what must you do to find out whether it is true?*

They cut across each other and that is fine. Appearance lands in all three of tokens,
structure, and behavior; `structure` collects facts from Structure, Appearance, and
Accessibility.

**Why sections must be by obtaining-method:** a section is *one tool's field of view*. No
XCUITest target means exactly one section is `unavailable` and everything routed there is
`unverified`. Organized by concern instead, a missing tool punches partial holes in three
sections and the honesty guard collapses into bookkeeping.

Routing is derivable, not hand-maintained:
`observe: prop → api` · `observe: token → tokens` · `kind: behavior → behavior` ·
otherwise `→ structure`. Generation is a **regroup**, not a translation.

### 4. Five layers, because most requirements are not component-specific.

v2's fix list would have pushed a mid-size component to 60–80 requirement rows, most of
them identical in every contract naming that archetype — a direct hit on the
"sufficiency as implementation context" promise.

L0 archetypes (bundle + bindings) · L1 system policy · L2 the contract · L3 generated
schemas · L4 adapters. A component says `archetype: dialog` and inherits the bundle.

This recovers v1's compression without its dishonesty: **v1 bought the bundle with one word
and tested none of it; v3 buys it with one word and tests all of it.** It also closes v2's
open question 5 — "the named element is the compliance condition" becomes "the archetype
bundle is required," same strictness, now enumerated.

Four of T1's seven gaps get absorbed by the layering rather than transcribed.

### 5. Composition absorbs layout, stated as geometry.

v1 scattered one concern across four sections (§2.2, §2.3, §3.1, §4.2), which is why T1
found three of them separately homeless.

The move that makes layout cross-platform: **state it as geometric relations between zones,
not style declarations.** Not `flex-direction: column` but *zones are arranged along the
block axis in composition order*. Every platform exposes bounding boxes, so the relation is
verifiable everywhere while the mechanism (flexbox, `VStack`, `Column`, Auto Layout) stays
invisible — as it must be.

Three kinds of layout fact: tokenized (token slot) · enumerable relation (closed set,
stated directly, no token wanted) · raw dimension (a token, or **pending** — never a
literal).

### 6. Accessibility is its own chapter. (User's call, correcting an earlier draft.)

Rationale: accessibility is reviewed *as an aspect*, by someone who needs one place to
look. A distributed a11y story is un-auditable.

The seam that avoids duplicating the zone list:
**Composition owns a zone's existence and terms. Accessibility owns its semantic exposure.**
Composition: *a title zone exists, accepts text, cardinality 1, sits first on the block
axis.* Accessibility: *the title is exposed as a heading and is the accessible name source.*

Traversal order belongs to **Accessibility**, not Composition — it needs stating separately
from arrangement only because AT and sequential focus traverse it. So *"traversal order
corresponds to visual arrangement"* is an accessibility requirement, which is where a
reviewer looks for it, and it is one of the defects most reliably invisible until someone
tests with a screen reader.

Costs nothing machine-side: those requirements still route by their own `observe`/`kind`.

### 7. Divergence is a decision, not a translation artifact.

Both v1 and v2 assume one intent, N vocabularies. True for Button; false for the things
teams actually argue about — an iOS sheet has a grabber and detents where a Web dialog has
a close button; Android's system Back is a first-class dismissal with no Web analogue.

v1 treats a genuine difference as bookkeeping (`SKILL.md:216` — "move it to a
platform-specific row"); v2 rule 4 forbids it outright. v3 makes it first-class:
`{ platform, affects, deviation, reason }`, and **a deviation with no reason is a lint
failure**. The reason is the most drift-prone sentence in the document.

### 8. Schemas will not be human-readable, and that is the wrong target.

Three humans touch this; only one opens a schema — the person whose build failed, and they
read an *error*. So: provenance on every constraint (`$comment` = requirement id, `title` =
the designer's sentence verbatim), plus a thin layer resolving a failing subschema back to
it, because stock validators emit poor errors and `anyOf`/`oneOf` cascades into noise.

Alignment is enforced as a **bidirectional invariant**, not trusted: every requirement
appears in exactly one schema per platform, and every constraint traces to a real
requirement id. Schemas are generated-only; CI regenerates and diffs.

### 9. Client tooling and lock-in — the objection that reshaped adoption.

Raised late and correctly: you cannot assume clients have Playwright, XCUITest, Compose
instrumented tests, FlaUI, AT-SPI — and a format whose value depends on winning an argument
in someone else's CI config is not shippable. The governance shape: **the design system
team owns the contract, app teams own their pipelines.**

Two answers, both now in the proposal:

- **The manifest shape is the interface; adapters are replaceable.** The format demands a
  JSON file in a documented shape, not any particular tool. A documented file boundary is
  the opposite of lock-in.
- **Conformance levels 0–3**, declared per run. `unverified` promoted from a
  per-requirement detail to an adoption concept. A client adopts at whatever level their
  pipeline supports and the report says which level it reached.

Consequence worth keeping visible: three of the four things the README holds this skill
accountable for — derivation, sufficiency, provenance — need **no tooling at all**. A
client at level 0 or 1 loses one of four, and knows which.

---

## Rejected, and why — do not re-litigate without new information

| Rejected | Why |
|---|---|
| v2 as drafted | failed T1; seven gaps, one breaks schema generation |
| v2 rule 4 (no platform-conditional requirements) | contradicts the guarantees catalogue — form participation, pre-scripting operability, and crawler discoverability have no iOS/Android referent. Resolve with scoped requirements carrying a written reason |
| Making schemas human-readable | wrong target; optimize for legible failure instead |
| Dropping rendered validation to avoid the tooling ask | throws away the demonstrated value — an XCUITest run in this repo surfaced a real a11y defect invisible to visual inspection |
| Building six adapters up front | build two (Web, then Android — Compose gives traits directly where iOS makes you fight for them); ship the rest as documented shapes |
| Enumerating archetype bundles per component | the 60–80-row explosion; that is what L0 exists to prevent |

## Two framings that live only in conversation

1. **The contract is the only artifact nobody must touch to ship.** Figma changes when
   design ships; code changes when engineering ships; the contract changes when someone
   remembers. That is the standard rot condition for a third artifact, and it is
   independent of format quality — which is why the alignment invariant and CI enforcement
   are not optional polish. Open question underneath: is the contract a *source* that
   something enforces conformance to, or a *derivative* that should be generated? It is
   currently positioned as source with no enforcement hook into anyone's workflow.
2. **Continuity breaks at the policy level, not the component level.** Nobody drifts on
   what a button is. What drifts: dismissal conventions, focus and announcement policy,
   validation timing, loading/empty conventions, motion policy, touch-target floors. That
   is what L1 exists for, and why T1's G5/G6 read as "under-specified" — they were system
   facts with no home.

---

## Where to pick up

In rough priority order:

1. **Spec the L0 archetype file format.** The heaviest-loaded piece: it must hold a
   requirement bundle plus four platform bindings, stay readable enough to serve as the
   implementer's reference, and be what `v1-implicit-guarantees-catalogue.md` converts
   into. Nothing else can be finalized before this.
2. **Pressure-test against SegmentedControl.** Real implementations already exist in this
   repo for Web, Apple, and Android (`contracts/SegmentedControl/implementations/`) — the
   cheapest available check on whether the normalized node shape and zone-tagging
   precondition survive contact with real code.
3. **Re-run T1 against v3.** The audit's method is sound and cheap; v3 changed enough that
   the result is not predictable from v2's.
4. **Build the Web reference adapter.** Proves the manifest end to end at the lowest cost,
   and makes the format falsifiable in practice rather than on paper.
5. Decide the interview delta — likely one added question (deliberate divergence and its
   reason) and several removed, since archetype and policy answer them.

## Open decisions carried forward

- Who owns the archetype library — proposed: shipped with the skill, extensible by the
  system, additions requiring a bundle *and* four bindings.
- Scoped requirements: what syntax, and what makes a scope justified rather than lazy.
- Whether `structure` extraction at build time is honestly two gates on native (a
  compile-time gate on `api`/`tokens`, a test gate on `structure`/`behavior`) — it is, and
  the docs should promise both rather than one.
- Adapter trust: a third-party adapter is trusted to tell the truth. `checks.json` making
  a missing check a schema failure is the mitigation; whether that is sufficient is untested.
