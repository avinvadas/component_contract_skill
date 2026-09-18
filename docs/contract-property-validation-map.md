# What a contract states, and when each part is validated

> **Superseded — maps the properties of a *v3* contract.** It predates the six chapters, token
> slots and the §5.4 machine, and it assumes a compiler-emitted manifest. The current property
> set is [`contract-md-format-spec.md`](contract-md-format-spec.md); when each fact is checked
> is now a property of the canonical document and its verifier, not of a table here.

Every property a v3 contract can hold, by chapter, with where and when it is checked.
Companion to `contract-format-v3-proposal.md`. Building this surfaced five gaps, listed
at the end.

## Four validation moments

All four happen **inside one build pipeline**. None requires a deployment, a manual step, or
a person opening a simulator. "Mounted" means the component is instantiated in isolation —
a story, a preview host, a test rule — not the application it will ship in. You do not need
a working app to validate a Button; you need the Button rendered and inspectable.

| Moment | Subject | What actually runs | Typical cost |
|---|---|---|---|
| **lint** | the contract and its schemas, against each other and against L0/L1 | nothing — no implementation involved | instant |
| **compile** | source-level facts: API surface, token references | a compiler pass: TS compiler API, SwiftSyntax, KSP | milliseconds, no device |
| **mounted** | rendered facts at rest (`structure`) | component instantiated and its tree read: jsdom or headless Chrome · `UIHostingController` in a unit test · Compose + Robolectric on the JVM | seconds, **no simulator or emulator** |
| **driven** | facts only true by doing something (`behavior`) | real runtime, real input: Playwright · XCUITest in a Simulator · instrumented test on a device | tens of seconds to minutes |

Two things to read off that table.

**Lint had been mentioned piecemeal throughout** — reasons are mandatory, alignment is an
invariant, archetypes must be complete — without being named as a moment. It is the cheapest
and catches a class the others cannot: a contract that is wrong about itself. It needs no
implementation, so it runs even at conformance level 0.

**The expensive gate is narrower than "native needs a simulator" suggests.** `mounted` is
achievable cheaply on every platform via an in-process path — `UIHostingController` does not
boot a Simulator, Robolectric does not boot an emulator. Only `driven` needs the heavy
runtime. So conformance level 2 is within reach of a pipeline that would balk at level 3.

Levels map on directly: **L1** = lint + compile · **L2** = + mounted · **L3** = + driven.

Because the schema is generated from the contract, it can be committed **before any
implementation exists**, and the build fails the moment a non-conformant one appears. That
is the documentation-driven claim cashing out rather than being a slogan.

---

## Does every platform validate the same property at the same moment?

**No.** The requirement binds identically on every platform — same statement, same strength.
What differs is *when it becomes observable*, and the differences are not where you would
expect.

| Section | Web | iOS | Android | macOS |
|---|---|---|---|---|
| `api` | compile | compile | compile | compile |
| `tokens` — reference | compile | compile | compile | compile |
| `tokens` — cascade override | **mounted** | n/a | n/a | n/a |
| `structure` — role / name / state | mounted *(real browser)* | mounted *(in-process host)* | mounted *(Robolectric)* | mounted |
| `structure` — geometry | mounted *(real browser)* | mounted | mounted | mounted |
| `structure` — name provenance | mounted | **weak** | **weak** | **weak** |
| `behavior` | driven | driven | mounted **or** driven | driven |

`api` is the only section that behaves identically everywhere. Everything else diverges, in
four ways worth knowing before writing an adapter.

### 1. On every platform, the expected tool is not the best tool for `structure`

This is the finding, and it holds three for three:

| Platform | The obvious tool | What it cannot see | The better tool |
|---|---|---|---|
| Web | jsdom (already in most test suites) | no layout — `getBoundingClientRect` returns zeros; no computed accessible name or ARIA role | headless Chrome + CDP |
| iOS | XCUITest | `XCUIElement` exposes no `accessibilityTraits` property; whether `app.debugDescription`'s dump carries enough trait detail for `heading`/`adjustable` is **untested here** | possibly `UIHostingController` in a unit test — also untested |
| Android | `adb shell uiautomator dump` | Compose semantics — no `Role`, no `heading()` | Compose test rule under Robolectric |

Two of these invert the usual cost assumption. On iOS the **heavier** tool sees less: XCUITest
boots a Simulator, takes minutes, and cannot read traits, while the in-process host runs in
seconds and can. On Android, `uiautomator` is cheap to *set up* — one adb command, no test
code — but it needs a running app on a device **and** sees less than Robolectric, which needs
neither. Robolectric is both cheaper and more capable.

This corrects the "cheap tiers" note recorded earlier, which offered `uiautomator` as
Android's low-cost path. It is the low-*setup* path, not the low-cost or high-capability one.

### 2. Web's zero-tooling tier is weaker than native's

The usual assumption is that web is always easiest. At full fidelity it is — headless Chrome
is trivial to run. But the tier that costs *nothing new* is jsdom, which does no layout and
does not compute accessible names, so geometry and name requirements report `unverified`.
The native equivalent — a `UIHostingController` or a Compose test rule — does real layout and
real semantics. So at the zero-new-tooling tier, **native sees more than web**.

### 3. `behavior` is reachable in-process on Android, and possibly on iOS

Compose's test rule supports `performClick()` and `performKeyPress()` under Robolectric, so a
meaningful share of Android's `behavior` section is reachable at JVM speed with no device.

The iOS equivalent — calling `accessibilityActivate()` on an element hosted in-process — is
plausible and **unverified**; it is recorded here as a thing to test, not a thing to rely on.
Some behaviour genuinely needs the full runtime everywhere: real gesture recognition, system
Back, VoiceOver actually running.

### 4. Two capabilities are web-only, for opposite reasons

**Cascade override** (`tokens`, mounted) exists because CSS has a cascade that can silently
defeat a correct token reference. No other platform has that failure mode, so its absence
elsewhere is not a gap.

**Name provenance** — *which* zone supplied the accessible name — is exposed by the web
accessibility tree through labelling relationships. On native the label is a bare string on
the node. You can confirm the name *matches* the title's text, which is weaker and fails when
two zones hold the same string. That one **is** a gap, recorded as G2.

### What this means for an adapter

Do not write one extractor per platform and assume a tier order. Write one per
**(platform × moment)**, and expect at least iOS to need two for `structure` alone —
in-process for semantics, XCUITest for anything requiring a real app. The moment matrix
above is the spec for which combinations must exist.

---

## 0 · Frontmatter

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| `component` | — | compile | 1 | `manifest.contract` must match |
| `version` | — | compile | 1 | `manifest.contract_version` must match |
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
| zone id | `structure` | mounted | 2 | via the zone tag — `data-zone`, `accessibilityIdentifier`, `testTag`, `AutomationId` |
| zone accepts — content type | `structure` | mounted | 2 | what actually rendered in the zone |
| zone accepts — delegated component | `structure` | mounted | 2 | containment only; **the child's own conformance is a separate run** — see G3 |
| cardinality, as a consumer constraint | `api` | compile | 1 | what a caller may legally pass |
| cardinality, as rendered | `structure` | mounted | 2 | what actually appeared — genuinely two facts, not one |
| position / arrangement | `structure` | mounted | 2 | geometric relation between zone boxes |
| layout constraints (max size, overflow) | `structure` | mounted | 2 | geometry |
| absent behaviour | `structure` | mounted | 2 | needs a capture with the zone absent — see G1 |
| adaptive conditions | `structure` | mounted | 2 | needs one capture per named condition |

## 3 · Appearance

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| token slot (property → token) | `tokens` | compile | 1 | reference resolves through the named token |
| literal denial (POL-04) | `tokens` | compile | 1 | deny-by-default across the declared property set |
| cascade override | `tokens` | mounted | 2 | **web only** — a reference present in source but overridden at render |
| state-driven appearance | `structure` | mounted | 2 | one capture per state: pressed, disabled, focused, error |
| motion token reference | `tokens` | compile | 1 | the reference only |
| motion actually suppressed under reduced-motion | `behavior` | driven | 3 | set the preference, then observe |

All of the above is **data-flow only** — that a value arrived through the named token. Not
that the value is right, not that it looks right. That boundary is stated in the proposal
and in the worked example, and it is the one most likely to drift.

## 4 · Behavior

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| interaction requirement | `behavior` | driven | 3 | drive and observe |
| events emitted | `behavior` | driven | 3 | signature presence is `api`/build; that it *fires* is level 3 |
| events received | `behavior` | driven | 3 | dispatch the external event, observe the response |
| state machine transitions | `behavior` | driven | 3 | one driven check per transition |
| no observable intermediate state | `structure` | mounted | 2 | a snapshot claim, despite living in this chapter |

## 5 · Accessibility

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| rendered identity | `structure` | mounted | 2 | the check that catches a generic element given a role |
| semantic role | `structure` | mounted | 2 | computed, never authored |
| accessible name | `structure` | mounted | 2 | computed name |
| name **source** (which zone) | `structure` | mounted | 2 | **web-strong, native-weak** — see G2 |
| grouping | `structure` | mounted | 2 | |
| traversal order | `structure` | mounted | 2 | accessibility-tree order |
| traversal order matches arrangement | `structure` | mounted | 2 | compares two facts inside one capture |
| state conveyed to AT | `structure` | mounted | 2 | per-state capture |
| focus policy — initial, containment, return | `behavior` | driven | 3 | driven |
| announcements | `behavior` | driven | 3 | driven |
| keyboard / gesture input | `behavior` | driven | 3 | driven |

## 6 · API

| Property | Section | Moment | Level | Notes |
|---|---|---|---|---|
| prop name | `api` | compile | 1 | |
| prop type | `api` | compile | 1 | |
| required / optional | `api` | compile | 1 | |
| default value | `api` | compile | 1 | |
| enum members | `api` | compile | 1 | |
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
