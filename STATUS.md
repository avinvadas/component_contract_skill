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
facts + policy         THE DESIGN SYSTEM'S OWN, once for the whole system.
                       facts  = what it IS      (.claude/design-system-context.yml — the token
                                                 tree's shape; detectable, and a wrong one is lint)
                       policy = what it DECIDED (their own file, located by `contracts.policy`;
                                                 ships blank; nothing detects a decision)
   │
   ▼
Button.md              THE DESIGN SYSTEM AUTHORS THIS — one per component.
 + bindings            Plus its token tree, resolved through the facts above.
   │                   scripts/resolve.py
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
| `scripts/resolve.py` — contract + archetype + policy + tokens → canonical JSON, any path | **works** |
| `scripts/resolve_view.py` — the human reading artifact | **works** |
| `scripts/tokens.py` — token resolution; reads a design system's own naming from its context file | **works** |
| `scripts/detect_tokens.py` — Phase 0B: proposes tiers, naming patterns and questions from a real tree | **works, wired into SKILL.md** |
| `scripts/machine.py` — state-machine tables; closure checks generated, never written | **works** |
| `scripts/test_scripts.py` — 27 regression tests, each naming a failure that once shipped | **passing** |
| Interaction states — every state the archetype makes valid is answered in chapter 4.2, or the parse fails | **works** |
| Variants — a token slot expands to one case per variant value; an unanswered value fails the parse | **works** |
| Element — which element carries the role, per platform, is a checked Structure requirement | **works** |
| Tokens in the contract — `scripts/writeback.py` writes what the tree answers (token or `{variant}` pattern) with its `scope`: component · shared:<group> · semantic | **works** |
| Implementation evidence — `scripts/evidence.py` turns what a verifier observed into questions (contradicts / adds); never edits | **works** |
| Web verifier — stdlib, deliberately weak, declares its own gaps | **runs** |
| 5 closed vocabularies (observe, conditions, capabilities, expect, interaction states) | **complete** |
| Role-archetypes: button 12, link 9, combobox 9, heading 3, text 2 | **tier 1 only** |
| Worked example: Button + IconButton + Combobox, three platforms | **3 components** |

## What does not exist yet

**The two halves are now joined.** `SKILL.md` Phase 3 derives the role-archetype, Phase 5
writes the six-chapter contract and its bindings, and Phase 6 runs `scripts/resolve.py` and
`scripts/resolve_view.py` to produce the canonical documents and the resolved view.
`structure.json` is gone: the canonical document replaces it, and checking a rendered tree
moved to whoever owns that platform's toolchain, which is what the format exists to allow.

What that does NOT mean: the skill has not been run end to end against a real design system
since the rewrite. The eval suite's stored generations predate it.

| | |
|---|---|
| Policy | **fills in as components need it** — a row is asked the first time a component engages it; a blank policy no longer breaks resolution |
| The design system's layer building up across components | **mechanism tested** (`the_second_component_asks_nothing_the_first_settled`); **behaviour not yet tested** — parked eval case, needs `stream-json` and API calls |
| iOS and Android verifiers | **sketches, not runnable** |
| Conformance suite for verifiers (how a new one proves it is correct) | **does not exist** |
| Role-archetypes tier 2–4 (dialog, list, checkbox, tab, …) | **unbuilt** |
| The eval suite's stored generations | **predate the format** — kept as a record, not a baseline; the fixtures, cases and invariants are rebuilt |
| Superseded docs in `docs/` | **kept as history, each bannered** — they record why the design moved, and say so at the top |

So: the **format and the resolver are real and testable**. The **product is not wired**.
Anyone evaluating this should judge the first and not mistake it for the second.

## See it yourself

```bash
P=docs/examples/pipeline
python3 scripts/resolve.py      $P/1-contract/Button.md --out $P/2-canonical   # → 3 canonical documents
python3 scripts/resolve_view.py $P/1-contract/Button.md --out $P/Button.resolved.md
python3 $P/3-verifiers/web/verify.py
python3 scripts/detect_tokens.py evals/fixtures/tokens/alt-naming.tokens.json  # Phase 0B on an unfamiliar tree
```

The verifier reports `5 pass / 3 fail / 31 unverified / 1 n-a`. The failures are intended —
the demo implementation is a `<div role="button">`, and a stdlib HTML parser honestly cannot
read stylesheets. **A verifier that reported all-green here would be the bug.**
