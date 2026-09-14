# Worked example — Button, on web / iOS / Android

A runnable demonstration of v3: one contract, three platforms, four outcomes.

```bash
python3 docs/examples/button/generate.py    # contract -> one schema per platform
python3 docs/examples/button/validate.py    # manifest x schema -> per-requirement report
```

## The files, and who writes each

| File | Layer | Author |
|---|---|---|
| `system/policy.md` | L1 | the design system, once |
| `system/archetypes/button.md` | L0 | shipped with the skill, once |
| `Button.md` | L2 | **the skill, from the interview** |
| `Button.{platform}.schema.json` | L3 | generated — never hand-edited |
| `manifests/Button.{platform}.manifest.json` | — | **the client's build**, via an adapter |
| `validate.py` | — | the reporter |

Note what is *not* in `Button.md`: any markup, any API, any framework, and — critically —
any of the twelve `BTN-*` requirements. It says `archetype: button` and inherits them.
That one line is what keeps a design document readable.

## How intent sinks down — trace one requirement

Follow **BTN-10** from a sentence a designer said to a failing build.

**1 · The designer answers the interview.**
> "It's a button. It can be disabled."

They say nothing about accessibility. They do not know what a trait is. That is the point —
accountability #1 in the README is that plain answers produce correct technical facts.

**2 · The archetype supplies the guarantee.** `button.md`, written once, for every component
that will ever be a button:

> `BTN-10` — when disabled, that state is conveyed to assistive technology.

This is one line of the bundle `<button>` gave v1 for free and v1 never tested.

**3 · The contract inherits it.** `Button.md` frontmatter says `archetype: button`, and
BTN-10 appears nowhere in the document. The contract states only what is specific to
Button: two composition zones, five token slots, five props, one divergence.

**4 · Generation makes it checkable.** `generate.py` emits, into all three schemas:

```json
"states": {
  "$comment": "BTN-10",
  "title": "when disabled, that state is conveyed to assistive technology",
  "type": "array",
  "contains": { "const": "disabled" }
}
```

The `$comment` is the thread back to the requirement; the `title` is the sentence a human
will be shown when it fails.

**5 · The build emits what it actually produced.** The iOS adapter captures the component
in its disabled state:

```json
"disabled": { "tree": { "states": [], "focusable": true, ... } }
```

The implementer dimmed the button with `.opacity(0.4)` and guarded the action closure. They
never called `.disabled(true)`.

**6 · The report names it, in the contract's own words.**

```
FAIL   BTN-10   when disabled, that state is conveyed to assistive technology
                -> None of [] are valid under the given schema
FAIL   BTN-08   when disabled, the control is removed from sequential focus navigation
                -> False was expected
```

**Why this is the case worth showing:** on screen the button looks correct — it is visibly
dimmed — and it behaves correctly, so `BTN-09` (*activation performs no action*) **passes**.
A screenshot test passes. A click test passes. Only the accessibility tree knows the button
is still focusable and still announces itself as enabled. That is the class of defect this
whole apparatus exists to catch, and it is the same class an XCUITest run in this repo found
by hand.

## Four outcomes, and why none collapses into another

```
WEB      25 pass /  0 fail /  0 unverified / 0 n-a     conformance level 3
IOS      21 pass /  2 fail /  0 unverified / 2 n-a     conformance level 3
ANDROID  19 pass /  0 fail /  5 unverified / 1 n-a     conformance level 2
```

| Outcome | Meaning | Example here |
|---|---|---|
| **pass** | the schema proved it | web, throughout |
| **fail** | the schema disproved it | iOS BTN-08, BTN-10 |
| **unverified** | it applies, and could not be checked | Android BTN-04/05/06/09 — no instrumented test; BTN-01 — `uiautomator` cannot see Compose `Role` |
| **n/a** | it does not apply here, with a reason | BTN-13 off the web; APP-05 on iOS, per the L2 divergence |

**Android is not passing 24 of 25.** It is passing 19, with five things nobody looked at.
That distinction is the entire honesty guard, and it was a real bug in the first run of this
example: the reporter recovered a requirement's section by guessing at the JSON Schema path,
matched the wrong element, and reported all four behaviour requirements as passing on a
platform whose behaviour section never ran. Fixed by tracking the section while descending
rather than inferring it afterwards — but worth recording, because a validator that
over-reports passes is worse than no validator.

**n/a is not pass, either.** A requirement that does not bind stays *visible* in the schema
carrying `x-not-applicable` and its reason, rather than being dropped. Dropping it would let
a hard platform quietly shrink its own bar — which was the second bug found here.

## What this example does and does not prove

**Does:** the contract is platform-neutral and readable; requirements route to manifest
sections mechanically; generation is a regroup, not a translation; divergence and scope flow
through to the schema; failure is reported in the designer's own sentence; and the three-state
result survives contact with a real validator.

**Does not:** `generate.py` reads a hand-transcribed requirement set rather than parsing
`Button.md` — parsing is the remaining work, and it is the part that decides whether the
`.md` stays as readable as it is now. The manifests are hand-written to represent three real
build outcomes; no adapter exists yet. Nothing here has been run against a real
implementation, though `contracts/SegmentedControl/implementations/` has three waiting.
