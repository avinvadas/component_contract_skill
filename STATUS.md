# Where this is, in one page

## What it is for

A design system states what a component **is** — once, in one platform-neutral document —
and every platform checks its own implementation against that statement using its own test
tooling. No shared test framework, no rewriting the skill when a new library ships.

## How it is supposed to work

```
references/            external standards (WAI-ARIA, WCAG, four HIGs, DTCG)
   │                   read once by a human. No contract ever reads them.
   ▼
system/                SHIPPED: 4 closed vocabularies · role-archetypes · blank templates
   │
   ▼
Button.md              THE DESIGN SYSTEM AUTHORS THIS — one per component.
 + bindings            Plus: its policy (cross-cutting decisions) and its token tree.
 + policy.md
 + token tree
   │                   resolve.py
   ▼
Button.web.canonical.json          ← THE SKILL'S OUTPUT ENDS HERE
Button.ios.canonical.json            one document per platform. An interchange format,
Button.android.canonical.json        not a test. Describes; does not execute.
   │
   ▼
verifier               SOMEONE ELSE'S TOOLCHAIN. Reads the canonical document, drives
   │                   Playwright / XCUITest / Compose. Declares what it cannot observe.
   ▼
pass · fail · unverified · n/a
```

Four ideas carry the whole thing:

1. **Inheritance.** A contract names one `role-archetype: button` and inherits twelve
   requirements about what platforms give a button for free. Many components share one.
2. **Closed vocabularies.** A requirement may only use 11 observation types, 10 comparison
   verbs, 10 conditions. Small on purpose — it is what makes a second verifier cheap.
3. **Nothing passes by accident.** Unobservable is reported `unverified` by name. A missing
   binding is a lint failure. A platform cannot lower its own bar by leaving something out.
4. **Predicates, not instances.** `when:disabled` describes a *class* of instances. A
   verifier finds a matching witness or constructs one; finding neither is not a pass.

## What actually runs today

| | |
|---|---|
| `resolve.py` — contract + archetype + policy + tokens → canonical JSON | **works** |
| `resolve_view.py` — the human reading artifact | **works** |
| `tokens.py` — token tree analysis, slot resolution, six outcome states | **works** |
| Web verifier — stdlib, deliberately weak, declares its own gaps | **runs** |
| 4 closed vocabularies | **complete** |
| Role-archetypes: button 12, link 9, combobox 9, heading 3, text 2 | **tier 1 only** |
| Worked example: Button + IconButton, three platforms | **2 components** |

## What does not exist yet

**The headline: there are two halves in this repo and they have never been joined.**
`SKILL.md` — the thing a user actually runs — contains **zero** references to `system/`,
`role-archetype`, the vocabularies, or canonical documents. It still describes the older
flow (interview → contract + per-platform structure/schema files). Everything above was
designed and built beside it, not into it.

| | |
|---|---|
| The interview does not know about policy, archetypes, or the token tree | **unwired** |
| iOS and Android verifiers | **sketches, not runnable** |
| Conformance suite for verifiers (how a new one proves it is correct) | **does not exist** |
| Role-archetypes tier 2–4 (dialog, list, checkbox, tab, …) | **unbuilt** |
| `docs/v3-handoff.md`, `validation-flow-current.md`, `contract-property-validation-map.md` | **stale, describe superseded designs** |

So: the **format and the resolver are real and testable**. The **product is not wired**.
Anyone evaluating this should judge the first and not mistake it for the second.

## See it yourself

```bash
python3 docs/examples/pipeline/resolve.py        # contract → 3 canonical documents
python3 docs/examples/pipeline/resolve_view.py   # → the readable version
python3 docs/examples/pipeline/3-verifiers/web/verify.py
```

The verifier reports `4 pass / 3 fail / 18 unverified / 1 n-a`. The failures are intended —
the demo implementation is a `<div role="button">`, and a stdlib HTML parser honestly cannot
read stylesheets. **A verifier that reported all-green here would be the bug.**
