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

## The four things we have to make

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
- **scenario dimensions**: props configuration × interaction state × adaptive condition

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

## What lives outside the skill

**Verifiers.** One per (platform × toolchain), owned by whoever owns that toolchain,
versioned on its own cycle. A verifier reads the document, drives its tool, emits its
ecosystem's report.

The skill ships **reference verifiers for one or two ecosystems in separate repositories**,
to prove the format and seed adoption — never inside this one. When Compose's test API
changes, that verifier changes. The skill does not.

### Gherkin is worth considering as a renderer

A `.feature` file is a plain-text, platform-neutral rendering of the same checklist, and
mature runners already exist: Cucumber-JVM, Cucumber.js, Reqnroll on .NET. Step definitions
bind the closed vocabulary to platform code **once per platform**, never per component.

Two honest caveats. Swift's Gherkin tooling is weak — `Cucumberish` and `XCTest-Gherkin`
exist but are not well maintained — which is the same thin spot iOS has shown at every layer.
And Gherkin would be a *rendering* of the canonical JSON, not a replacement for it; the JSON
stays the machine-readable source.

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
   format has become a programming language and the second implementation stops being cheap.
