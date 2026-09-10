# L0 — Archetype file format

**Status: spec draft.** Companion to `contract-format-v3-proposal.md`.
Read `v3-handoff.md` first for why this layer exists.

## What an archetype is

A role from the closed vocabulary, plus **the bundle of guarantees that role implies** —
written out, bound per platform, and testable.

This is the layer that makes v3 viable rather than merely correct. v1 bought a bundle of
behaviour with one word (`<button>`) and tested none of it. v2's fix was to enumerate that
bundle inside every component contract, which pushes a mid-size component to 60–80 rows,
most of them identical in every contract naming that archetype. L0 enumerates it **once**.

A component then says `archetype: button` and inherits it.

### What an archetype is not

- **Not a component.** It has no tokens, no composition zones, no API surface. Those are
  component facts and belong in L2.
- **Not a platform mapping.** The bundle is stated neutrally; the binding file says how it
  is observed.
- **Not optional to satisfy.** Inheriting an archetype means meeting its bundle in full.

## Two files per archetype

```
system/archetypes/
  button.md              the bundle — human-readable, the implementer's reference
  button.bindings.json   per-platform observables for every id in the bundle
```

The `.md` is authored by a person and reviewed like a standard. The `.json` is authored
alongside it and must cover every id, on every platform in scope, or the archetype fails
its own completeness lint.

---

## Requirement anatomy

Each requirement in a bundle carries six fields.

| Field | Meaning |
|---|---|
| `id` | `BTN-04`. Stable forever. Never reused, never renumbered. |
| `statement` | One sentence, plain language, no platform vocabulary. |
| `observe` | `role` · `name` · `state` · `order` · `containment` · `focus` · `announcement` · `event` · `layout` · `token` · `prop` |
| `kind` | `state` — true in a snapshot at rest. `behavior` — only true by doing something. |
| `required` | `always`, or a named condition. |
| `scope` | `all` by default, or an explicit platform list **with a reason**. |

`observe` and `kind` together route the requirement to a manifest section with no
hand-maintained mapping: `prop → api`, `token → tokens`, `kind: behavior → behavior`,
otherwise `structure`.

### The `scope` field, and the rule that governs it

v2's rule 4 said a requirement true on only some platforms is written at the wrong level.
Working the catalogue disproves this: `<button>`'s free bundle includes **form
participation** and **operability without scripting**, which have no referent whatsoever on
iOS, Android, or macOS. They are not badly written — the concept does not exist there.

So `scope` is real. But it is also the easiest field to abuse, so it takes a hard rule:

> **Prefer a condition. Use `scope` only when the concept has no referent on the platform
> at all.**

The distinction is worth being precise about, because it is the difference between an
honest exclusion and a quiet weakening:

| Case | Wrong | Right |
|---|---|---|
| Space activates a button | `scope: [web, android]` — iOS has no Space key | `required: when the platform exposes a hardware keyboard` — iOS under Full Keyboard Access *does*, and must comply |
| A button submits its form without scripting | — | `scope: [web]`, reason: no platform-level form model exists elsewhere |

A `scope` narrower than `all` **must** carry a `reason`. A scope with no reason is a lint
failure, exactly like a divergence with no reason. "We forgot" and "it is hard on Android"
are not reasons; "the concept has no referent" is.

---

## Inheritance rules

What a component contract may do with an inherited requirement:

1. **Add.** Component-specific requirements sit alongside the bundle, numbered in the
   component's own namespace.
2. **Constrain further.** A component may make an inherited requirement stricter. No
   ceremony needed — stricter is always safe.
3. **Diverge.** A component may satisfy an inherited requirement differently on one
   platform, via an L2 Divergences entry carrying a reason. The requirement still binds;
   only the manifestation changes.
4. **Never weaken silently.** There is no mechanism to drop an inherited requirement. If an
   archetype's bundle is wrong for a whole class of component, that is a signal the
   archetype is wrong — fix L0, or the component is a different archetype.

Rule 4 is the one that keeps this honest. The failure mode it prevents is a component
quietly opting out of the guarantee its archetype exists to promise, which is exactly the
v1 behaviour v3 is trying to end.

---

## Worked archetype — `button`

The richest free bundle in the catalogue, and the one that forces every hard question.

```markdown
---
archetype: button
role: button
version: 1.0
platforms: [web, ios, android, macos]
source: v1-implicit-guarantees-catalogue.md § Web/Interactive, iOS, Android, macOS
---

# Archetype: button

A control that performs an action when activated. It does not navigate — that is `link`,
and the asymmetry between them is load-bearing (see `link.md`).

## Bundle

| id | statement | observe | kind | required | scope |
|---|---|---|---|---|---|
| BTN-01 | The control is exposed to assistive technology as a button. | role | state | always | all |
| BTN-02 | The control has a non-empty accessible name. | name | state | always | all |
| BTN-03 | The control is reachable by the platform's sequential focus navigation. | focus | state | always | all |
| BTN-04 | Activating the control by the platform's primary non-pointer input performs its action. | event | behavior | always | all |
| BTN-05 | Where the platform exposes a hardware keyboard, both of its standard activation keys perform the action. | event | behavior | when a hardware keyboard is present | all |
| BTN-06 | Keyboard activation does not also scroll the surrounding surface. | event | behavior | when a hardware keyboard is present | all |
| BTN-07 | While focused, the control renders a focus indicator distinguishable from its unfocused appearance. | state | state | always | all |
| BTN-08 | When disabled, the control is removed from sequential focus navigation. | focus | state | when disabled | all |
| BTN-09 | When disabled, activation performs no action. | event | behavior | when disabled | all |
| BTN-10 | When disabled, that state is conveyed to assistive technology. | state | state | when disabled | all |
| BTN-11 | The control meets the platform's minimum touch-target size. | layout | state | on touch-capable platforms | all |
| BTN-12 | The accessible name scales with the platform's user text-size setting. | state | state | always | all |
| BTN-13 | The control submits its containing form without scripting. | event | behavior | when inside a form | **web** |

> **BTN-13 is scoped, with a reason:** no platform-level form-submission model exists on
> iOS, Android, or macOS. The concept has no referent there — this is an exclusion, not a
> weakening.

> **BTN-05 is not scoped, deliberately.** iOS has no Space key by default, but under Full
> Keyboard Access it does, and must comply. A `scope: [web, android, macos]` here would
> have quietly excused a platform that can in fact meet the requirement — which is exactly
> the abuse `scope` invites.

> **BTN-06 exists separately from BTN-05** because it is the half most commonly missed. A
> patched `div` that handles `keydown` for Space almost always forgets `preventDefault`,
> so the page scrolls. Two requirements, because they fail independently.

## Empty-bundle note

Nothing here is free on any platform for a *composed* button — a generic view given a role.
That is the point: every line above is what the native control provides automatically and
what a substitute must therefore prove.
```

### `button.bindings.json`

```json
{
  "archetype": "button",
  "version": "1.0",
  "web": {
    "BTN-01": { "observe": "role",  "method": "axtree", "expect": "computed role = button" },
    "BTN-01b":{ "observe": "identity","method": "dom",  "expect": "tagName in [button, input[type=button|submit]]",
                "note": "rendered tag, separate from role — this is what catches a patched div" },
    "BTN-03": { "observe": "focus",  "method": "dom",   "expect": "reachable by sequential Tab without authored tabindex" },
    "BTN-05": { "observe": "event",  "method": "interaction", "trigger": ["key:Enter", "key:Space"], "expect": "action fires for both" },
    "BTN-06": { "observe": "event",  "method": "interaction", "trigger": "key:Space", "expect": "scrollY unchanged" },
    "BTN-11": { "observe": "layout", "method": "dom",   "expect": "hit area >= 24x24 CSS px", "note": "WCAG 2.2 SC 2.5.8" },
    "BTN-13": { "observe": "event",  "method": "interaction", "trigger": "activate with scripting disabled", "expect": "form submits" }
  },
  "ios": {
    "BTN-01": { "observe": "role",  "method": "inprocess-ax", "expect": ".button trait present",
                "note": "XCUITest does not expose accessibilityTraits; needs the in-process extractor" },
    "BTN-03": { "observe": "focus", "method": "xcuitest", "expect": "reachable under Full Keyboard Access" },
    "BTN-05": { "observe": "event", "method": "xcuitest", "trigger": ["key:Return", "key:Space"],
                "expect": "action fires for both", "requires": "hardware keyboard attached" },
    "BTN-11": { "observe": "layout","method": "xcuitest", "expect": "frame >= 44x44 pt", "note": "Apple HIG" },
    "BTN-12": { "observe": "state", "method": "xcuitest", "expect": "label reflows at largest Dynamic Type size" },
    "BTN-13": { "scope": "n/a" }
  },
  "android": {
    "BTN-01": { "observe": "role",  "method": "compose-semantics", "expect": "Role.Button" },
    "BTN-11": { "observe": "layout","method": "uiautomator", "expect": "bounds >= 48x48 dp", "note": "Material" },
    "BTN-13": { "scope": "n/a" }
  },
  "macos": {
    "BTN-01": { "observe": "role",  "method": "axapi", "expect": "AXRole = AXButton" },
    "BTN-11": { "scope": "n/a", "note": "no touch input; BTN-11's condition is unmet, not excused" },
    "BTN-13": { "scope": "n/a" }
  }
}
```

Two things to read off that file.

**`BTN-01b` is not a numbering mistake.** Identity and role are separate observations of one
requirement on Web, because that separation is the only thing that catches a `<div>` patched
to report `role="button"`. A binding may add observations; it may never remove one.

**`scope: "n/a"` is distinct from `unverified`.** `n/a` means the requirement does not apply
here and the platform is not penalised. `unverified` means it applies and could not be
checked. Collapsing the two would let a hard platform hide behind exclusions — which is the
failure mode this whole layer is built to prevent.

---

## Converting the catalogue into a bundle

Mechanical, and it should stay that way so it can be audited:

1. Take one construct's entry from `v1-implicit-guarantees-catalogue.md`.
2. Split every clause into its own requirement. `disabled` is three, not one — it removes
   from focus order, blocks activation, and is announced, and those fail independently.
3. Restate each without platform vocabulary. If it cannot be restated, it is a `scope`
   candidate — check the referent test before accepting that.
4. Assign `observe` and `kind`. If neither fits, the vocabulary needs extending; record it
   rather than forcing a fit.
5. Write the binding on all four platforms. **A requirement that cannot be bound anywhere
   is written at the wrong level** — this is T2, run per archetype instead of per component.
6. Union the platform entries. Anything present on one platform and absent on the others is
   either a scoped requirement or a gap in the catalogue.

Step 5 is where most errors will surface, and it is cheap. Doing it once per archetype
rather than once per component is the entire economic argument for L0.

## Completeness lint

An archetype is well-formed only if:

- every id in the `.md` appears in every in-scope platform's bindings, or is explicitly `n/a`
- every `scope` narrower than `all` carries a `reason`
- every binding names a `method` that exists in the method table
- no two ids in the same bundle state the same fact (T6 overlap check)
- every id is reachable from at least one mutation that fails it (T3 discrimination —
  the one that separates requirements from decoration)

The last is the expensive one and cannot be checked statically. It is the archetype-level
form of T3, and doing it here means it is done once per archetype rather than once per
component — the same amortization argument as everything else in this layer.

## Open

1. **Archetype composition.** Is `tablist` an archetype containing `tab` archetypes, or a
   pattern with its own flat bundle? The catalogue notes tabs have an *empty* free bundle
   on every platform, which argues for flat.
2. **Versioning.** A bundle gaining a requirement is a breaking change for every component
   inheriting it. Needs a policy: probably additive-only within a major, with new
   requirements landing as `required: when …` until adopted.
3. **Who may author one.** Proposed: shipped with the skill; a design system may add, but
   an addition needs a bundle *and* bindings for every platform it claims.
