# v5 — ship an interchange format, not generators

**Status: proposal.** Supersedes v4's emitter model. The L0/L1/L2 layering is unchanged.

## The constraint that decides this

> Send a design intent, and have it validated by each platform in its own format-of-choice
> on the other side of the tunnel. Connect to existing tools rather than replace them, and
> do not rewrite the skill whenever a new library ships.

v4 had the skill emitting XCTest files, Compose tests, Playwright specs. That makes the
skill a code generator for five ecosystems, and couples its release cycle to every test
library on every platform. Compose's test API changes, the skill changes. That is the wrong
dependency direction and it never stops.

> **v5: the skill's deliverable ends at one canonical document. Everything that touches a
> tool lives outside the skill and is versioned independently.**

## What this shape is

Not new. It is how every durable integration boundary works.

| Precedent | The invariant | What churns freely |
|---|---|---|
| **LSP** | the protocol | editors, language servers |
| **Pact** | the contract file | per-language verifier libraries |
| **SARIF** | the results schema | analyzers, CI dashboards |
| **OpenAPI** | the document | generators, validators, mocks |

In each, the format outlived most of the tools that first implemented it. That is the
property being bought.

## The five things we have to make

### 1. The canonical requirement document

The single artifact the skill emits per platform. Not results — **a checklist of what must
be true, and how to observe it here.**

```json
{
  "contract": "Button", "contract_version": "1.0", "platform": "ios",
  "requirements": [
    { "id": "BTN-10",
      "statement": "When disabled, that state is conveyed to assistive technology.",
      "observe": "state", "kind": "state",
      "scenario": { "props": { "disabled": true } },
      "expect": { "state": "disabled", "present": true },
      "needs": ["a11y-tree"] },

    { "id": "BTN-13",
      "statement": "The control submits its containing form without scripting.",
      "binds": false,
      "reason": "no platform-level form model exists off the web" }
  ]
}
```

Everything a verifier needs, nothing about any library. It must stay **small** — a large
spec never gets a second implementation.

### 2. A closed vocabulary

The reason a verifier is finite work rather than endless work.

- **observe**: `role · name · state · order · containment · focus · announcement · event · layout · token · prop`
- **roles**: the closed set already defined in v3
- **scenario dimensions**: props predicate × interaction state × adaptive condition —
  a *predicate* over declared props, never a reference to a concrete instance
- **conditions**: the closed set a `required:` clause may name

That last one is easy to miss and is a genuine gap. A contract reads
`required: when a hardware keyboard is present`, which is good prose and unparseable. A
verifier needs a token it can evaluate against its own capabilities —
`hardware_keyboard`, `touch_input`, `reduced_motion`, `disabled`, `inside_form`. Conditions
are as much a closed vocabulary as roles are, and the contract's prose must map onto them
deterministically or the resolver cannot produce a canonical document at all.

Closed vocabulary means a verifier implements *eleven observation types once* and then
handles every component the design system will ever write. A new component ships a new
document and zero new code. **That is the amortization the whole approach rests on.**

Extending the vocabulary is a format version bump — deliberate, rare, and visible.

### 3. A capability declaration

How a verifier stays honest without the skill knowing anything about tools.

```json
{ "verifier": "compose-robolectric", "format_version": "1.0",
  "can_observe": ["role","name","state","order","focus","layout","event"],
  "cannot_observe": { "announcement": "no TalkBack in a JVM test" } }
```

The runner reconciles the document against the declaration: anything requested that the
verifier cannot observe is reported `unverified` **by name, with the verifier's own reason**.

This is what preserves the honest-gap property across tools nobody here wrote. A weak
verifier produces visible gaps, never a quietly lower bar — and it does so without the skill
having any opinion about which tool is weak.

### 4. Results — deliberately not invented

Nothing new here. A verifier reports in whatever its ecosystem already emits: JUnit XML,
xcresult, Cucumber JSON, SARIF. Every CI system already consumes these.

If a cross-platform view is wanted later, define a *mapping* from those into one report —
not a new format that everyone must emit.

**Amended.** That held for per-test results and still does. What none of those formats carries
is the *claim*: which document was checked, which build was observed, by which verifier, and
what that verifier could not see. Without it a green run records that something called Button
passed, once — which is not a fact about a version, and so cannot answer "which products does
this change break". `docs/verifier-results-format.md` is that envelope, and it is additive: a
verifier keeps emitting JUnit for CI and writes this alongside.

### 5. A conformance suite for verifiers

**Who adjudicates the checklist:** the verifier does. It observes, compares against `expect`,
and reports in its own format. It has to work that way — a verifier that reports raw
observations for something central to judge is v3's manifest, which this proposal deletes.

That raises the obvious question: if every verifier does its own comparison, what stops a
lenient or buggy one from reporting green? Nothing, unless the format ships a suite that
validates implementations. Every interchange format that survived has one — the **JSON
Schema Test Suite** is the closest analogue, a shared corpus of schema + instance + expected
result that every validator runs to claim conformance. Without it a format grows dialects
within two years.

Two halves, with very different costs:

**Comparison conformance — platform-neutral, nearly free.** Given *these* observations and
*this* `expect`, what is the verdict? Pure fixture data, shared by every verifier on every
platform. It catches the main divergence risk: two implementations reading `expect`
differently.

This is where open question 4 below earns its keep. A tiny grammar — `present`, `equals`,
`one_of`, `min`, `order` — leaves almost nowhere to disagree. An expression language would
make this half impossible to specify, which is the real argument against one.

**Observation conformance — per platform, expensive, and the half that buys trust.** A
verifier claiming it can observe `role` must be shown a component that exposes it and one
that does not, and get both right. That needs reference components per platform: one
correct, several mutated.

The second half is the instrument this repo already uses — build the failing case alongside
the passing one — applied one level up. The mutation set from T3 in the v2 validation plan
is exactly the fixture corpus it needs, so it is less new work than existing work acquiring
a second job.

A verifier's published conformance result, alongside its capability declaration, is what
makes a third-party implementation trustworthy without anyone here having read its code.

**Started.** `scripts/check_results.py` is the first piece of this and the cheapest: it does
not adjudicate a verdict, it checks that what a verifier wrote is a claim at all — every part
present, a digest that is a digest, a summary that counts the rows beneath it. That catches a
whole class of divergence before any fixture corpus exists, and it is the shape the comparison
half would extend: fixture in, expected finding out.

## What lives outside the skill

**Verifiers.** One per (platform × toolchain), owned by whoever owns that toolchain,
versioned on its own cycle. A verifier reads the document, drives its tool, emits its
ecosystem's report.

The skill ships **reference verifiers for one or two ecosystems in separate repositories**,
to prove the format and seed adoption — never inside this one. When Compose's test API
changes, that verifier changes. The skill does not.

### Renderers: what design systems actually use

**Gherkin is a feature-pipeline tool and has almost no footing here.** Recorded because it
looks attractive at first glance and is not.

Two reasons it misfits. **Granularity** — Gherkin is written at journey level, while a
component contract operates at "this element exposes role button"; wrapping one assertion in
Given/When/Then is three lines of ceremony around one fact. **Audience** — Gherkin exists so
non-technical stakeholders can read acceptance criteria, but this document is read by
designers and engineers, both of whom read a table faster. And Cucumber's step definitions
*are* a verifier, written inside Cucumber's conventions rather than freely, so it saves none
of that work.

It stays legitimate in exactly one situation: an organisation already running Cucumber across
its stack gets results in reporting it already has, at no new infrastructure cost. That is a
per-client rendering choice, not an architectural one — which is this proposal working as
intended.

**Storybook is closer prior art, but it sits a level below the contract.** A story is a
*witness*: one concrete, single-platform instance with fully-specified args. A contract
scenario is a *predicate*: a class of instances. `when:disabled` means "in any instance where
disabled holds", not "the story named Disabled". Conflating the two pulls the contract down a
level of abstraction it exists to stay above.

Getting that right makes the mechanism better, not worse:

- **Matching is predicate satisfaction, not lookup.** A verifier asks whether a witness
  exists whose args satisfy `{disabled: true}`. There may be zero, one, or several. Check all
  of them — three stories rendering a disabled Button where one fails is a real finding.
- **Zero witnesses is a useful result.** Reported `unverified`, with a message saying no
  witness satisfies the predicate. That tells a team their scenario coverage has a hole
  exactly where their contract has a requirement, which nothing currently tells them.
- **Witness-finding cannot be the only strategy.** Stories are written for documentation and
  visual review, not contract coverage, so a verifier reading only stories will have gaps.

So a verifier satisfies a scenario by **finding a witness or constructing one**, and declares
which in its capability declaration. Finding is cheap and connects to what a team already
has; constructing is complete and platform-specific. Most verifiers should do both.

This holds identically for SwiftUI `#Preview` and Compose `@Preview`, which are witness
declarations in exactly the same sense — though neither carries interaction the way a play
function does, so they likely serve the `mounted` tier and not the `driven` one.

### Why predicates can be platform-neutral at all

A dependency worth stating, because the whole mechanism rests on it: **scenario predicates
are neutral only because the API chapter fixes prop names across platforms.**
`{disabled: true}` is meaningful on every platform precisely because the contract declares
that prop and each platform's schema, protocol or interface enforces it. If props could vary
per platform, scenarios could not be expressed once — so the API chapter is load-bearing for
far more than schema generation.

For reference, what this domain actually runs:

| Concern | Tooling |
|---|---|
| Docs and scenarios | Storybook (CSF, play functions); SwiftUI and Compose previews |
| Component tests | Testing Library + Jest/Vitest, Playwright, Compose test rule, XCTest |
| Visual regression | Chromatic, Percy, Loki; Paparazzi/Roborazzi; swift-snapshot-testing |
| Accessibility | axe-core, ATF, `performAccessibilityAudit()`, Axe.Windows |

A verifier that plugs into the first two rows is connecting to existing tools. One that asks
a team to adopt a new format is not.

## What the skill stops doing

- emitting test code for any framework
- emitting manifests, or validating them
- shipping adapters
- knowing that Playwright, XCTest, Compose, FlaUI or Robolectric exist

What it keeps: the interview, the contract, the archetype library, the policy layer, the
resolver, and the canonical document. Its dependency on the outside world reduces to **one
versioned format**.

## Open

1. **Does the closed vocabulary actually close?** T5 in the v2 validation plan — the
   archetype spread — now decides whether the format ships, not just whether the role set is
   complete. If eleven observation types cannot express a combobox or a drag-to-reorder list,
   the format is wrong and it is much cheaper to find that now.
2. **Scenario expressiveness.** `props × state × condition` is a guess at the right
   dimensions. Adaptive layout and focus containment will test it.
3. **Who writes the first verifier.** The format is unfalsifiable until two exist, and two is
   the number that matters — one can always be accidentally shaped around its own document.
4. **Whether `expect` stays declarative.** The moment it needs an expression language, the
   format has become a programming language, the second implementation stops being cheap,
   and comparison conformance stops being specifiable. Treat pressure to add expressions as
   evidence a requirement is written at the wrong level.
5. **What the web JSON Schema keeps doing.** Unchanged from v1: it validates a
   consumer-supplied props instance against the API chapter. That is a schema over data, not
   a checklist item, and it stays in the compile tier.
