# Worked pipeline — levels 1 → 3

One contract, three canonical documents, three verifiers. Reproduce with:

```bash
python3 docs/examples/pipeline/resolve.py            # level 1 -> 2
python3 docs/examples/pipeline/3-verifiers/web/verify.py   # level 3, runnable
```

## The four levels, and where the skill stops

| Level | Artifact | Scope | Who owns it |
|---|---|---|---|
| 1 | `Button.md` | platform-neutral — a class of valid implementations | **the skill** |
| 2 | `Button.<platform>.canonical.json` | one platform's vocabulary, still a description | **the skill** |
| 3 | verifier + capability declaration | reads the description, drives a tool | whoever owns that toolchain |
| 4 | witness | one concrete instance — a story, a preview, a mount | the product team |

**The skill's output ends at level 2.** Everything below is someone else's, versioned on its
own cycle. Every design error in this project's history has been the skill reaching down to
level 3 or 4 — the v3 manifest, the v4 emitters, and treating a Storybook story as a
scenario.

## Level 1 — the contract

[`1-contract/Button.md`](1-contract/Button.md) — six chapters, eleven rows of
component-specific fact. One frontmatter line, `archetype: button`, inherits eight
requirements that appear nowhere in the document.

Supporting it: the archetype bundle and bindings, the policy file, and
`Button.bindings.json` for ids this contract introduces.

## Level 2 — canonical documents

[`resolve.py`](resolve.py) parses the contract and emits one document per platform. Same
thirteen requirements everywhere; what differs is how each is observed, and whether it binds.

```
web      13 requirements, 13 binding, 0 n/a
ios      13 requirements, 12 binding, 1 n/a
android  13 requirements, 12 binding, 1 n/a
```

Three things to read off the emitted JSON:

**BTN-11 — the same requirement, three thresholds.** `min: 24` css-px on web, `44` pt on
iOS, `48` dp on Android. One statement, three platform standards, no per-platform contract.

**BTN-13 — scoped out, and still present.**

```json
{ "id": "BTN-13", "statement": "The control submits its containing form without scripting.",
  "binds": false, "reason": "no platform-level form model exists off the web" }
```

Present in the iOS and Android documents, with its reason, rather than absent. A platform
cannot shrink its own bar by omission because omission is not expressible.

**Conditions become scenario predicates.** `required: when:disabled` in the `.md` resolves to
`"scenario": {"props": {"disabled": true}}` — a predicate over a class of instances, never a
reference to one.

## Level 3 — verifiers

Each declares what it can and cannot observe. Anything a requirement needs that the verifier
cannot see is reported `unverified` **in the verifier's own words**, never passed.

| Verifier | Tier | Strategy | Runnable here |
|---|---|---|---|
| [`web/verify.py`](3-verifiers/web/verify.py) | static HTML parse | witness only | **yes** |
| [`ios/VerifierSketch.swift`](3-verifiers/ios/VerifierSketch.swift) | XCTest in-process | witness + construct | no — illustrative |
| [`android/VerifierSketch.kt`](3-verifiers/android/VerifierSketch.kt) | Compose + Robolectric | witness + construct | no — illustrative |

The web one is deliberately weak — stdlib HTML parsing, no browser, no layout, no
interaction. That is what makes it a useful demonstration: it has real gaps and has to
declare them.

```
web-stdlib-static  —  strategy: witness
4 pass / 3 fail / 6 unverified / 0 n-a

FAIL   BTN-01   The control is exposed to assistive technology as a button.
                -> role='button' but rendered tag is <div>, not ['button', 'input']
FAIL   BTN-08   When disabled, the control is removed from sequential focus navigation.
FAIL   BTN-10   When disabled, that state is conveyed to assistive technology.
UNVER  BTN-11   The control meets the platform's minimum touch-target size.
                -> no layout engine — this verifier parses HTML, it does not render it
UNVER  ACC-02   The label is the sole source of the accessible name.
                -> computing which node supplied the accessible name needs the browser's own name computation
```

Six unverified, each naming the capability it lacked. A weak verifier produces **visible
gaps**, never a quietly lower bar — and the skill has no opinion about which verifier is
weak, because it never knew any of them existed.

The two sketches show the same loop in each platform's idiom, and both get the three-state
result natively: `XCTSkip` on iOS, JUnit `Assume` on Android, both carrying the reason into
xcresult and JUnit XML with no custom reporting.

---

## Two contracts, one archetype

`IconButton` was added to make the fan-out visible, because with a single component the
archetype looks like per-component indirection. It is not — there is **one archetype file per
archetype**, not per contract.

```bash
python3 resolve.py IconButton && python3 resolve_view.py IconButton
```

| | Button | IconButton |
|---|---|---|
| inherited from `button` | 12 | 12 |
| local requirements | 4 | 3 |
| zones | 2 | 1 |
| archetype files read | **the same one** | **the same one** |

Neither contract restates a single `BTN-*` requirement, and neither can weaken one. Add
ToggleButton, SplitButton and a FAB and the count of archetype files stays at one.

### Three tiers of rule, and only one is conditional

| Rule | Applies to | Lives in | Count in a ~40-component system |
|---|---|---|---|
| format — six chapters, `when` first, closed vocabularies | every contract | the spec | 1 |
| policy — focus indicator, token discipline, touch targets | every contract | `policy.md` | 1 |
| **archetype bundle** | **contracts of that kind** | `archetypes/<name>.md` | ~12 |

A Modal does not inherit button requirements; a Link does not inherit dialog requirements.
That conditionality is exactly why a bundle cannot be folded into the spec or into policy,
both of which apply unconditionally.

### What the second contract exposed

IconButton has **no visible text**, so `BTN-02` — *the control has a non-empty accessible
name* — has no rendered content to draw from. Button satisfies it from its label zone;
IconButton has to satisfy it from a required `label` prop that is never rendered.

Same inherited requirement, two different name sources, and the difference lives entirely in
each contract's own Accessibility chapter. Nothing about the archetype changed. That is the
layering doing the job it exists for, and it only became visible at the second component.

## What building this found

Four things, in ascending order of how much they changed the design.

**1 · Component-local requirements had no binding home.** The resolver's first run reported
`STR-01: no binding for web — cannot be checked or excused` on all three platforms. The
archetype bindings file covers inherited ids; nothing covered ids a contract introduces.
Fixed by a component-level bindings file that overrides the archetype's.

**2 · `needs` is derivable from `observe`, and most bindings were boilerplate.** `role` always
needs an a11y tree; `layout` always needs geometry. Deriving it emptied most binding entries,
leaving the file holding only what is genuinely platform-specific — a differing threshold, or
an explicit n/a.

**3 · But derivation is not complete.** `ACC-02` (*the label is the sole source of the
accessible name*) needs `name-provenance` **on top of** the a11y tree, and `POL-02` needs
geometry on top of state. Stripping `needs` entirely lost both, and they silently became
checkable by a verifier that could not actually check them. Bindings now carry `needs_also`.

**4 · The verifier claimed a capability and never used it.** `BTN-01` initially **passed** on
`<div role="button">` — the classic defect the identity/role split exists to catch. The
verifier declared `identity` in its capability file and then only ever read the `role`
attribute. Nothing in the pipeline noticed.

That is precisely the failure the **conformance suite** in the v5 proposal exists to prevent,
arriving on its own within an hour of the first verifier existing. A verifier's capability
declaration is a *claim*, and an unaudited claim is worth nothing — a verifier that
over-reports passes is worse than no verifier. Item 5 of v5 is not optional, and this is the
evidence.

## What this does not prove

- The two native verifiers are sketches. Nothing has been compiled or run.
- No conformance suite exists yet, which is what makes finding 4 uncomfortable rather than
  merely interesting.
- One component, one archetype. The closed vocabulary has not met a combobox or a
  drag-to-reorder list, which is T5's job and still outstanding.
