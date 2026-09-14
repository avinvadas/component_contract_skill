# What a contract draws from — file plan and structure

**Status: plan.** The layer between `references/` and a contract, which does not exist yet.

`references/` holds **external standards** — WAI-ARIA, WCAG, HIG, Material, UIA. A contract
never reads them. They are the source material from which the layer below is *authored*, once.

## Three layers, three owners

| Layer | Contents | Owner | Changes when |
|---|---|---|---|
| `references/` | external standards, one file per standard | the skill | a standard is revised |
| `system/vocabulary/`, `system/archetypes/` | the closed vocabularies and the archetype library | **shipped with the skill**, locally extensible | the format version bumps |
| `system/policy.md`, `system/context.yml`, component contracts | this design system's own decisions | **the design system** | the team decides something |

The middle layer is the missing one. Everything in it is *derived* from `references/` plus
`v1-implicit-guarantees-catalogue.md`, authored once, and read by the resolver on every run.

```
references/            external standards        (authoring input, never read by a contract)
      |
      | derived once, with per-requirement provenance
      v
system/vocabulary/     closed sets               ──┐
system/archetypes/     requirement bundles         ├─ read by the resolver
system/policy.md       cross-cutting decisions     │
system/context.yml     design-system facts       ──┘
      |
      v
Button.md              the contract
```

---

## 1 · `system/vocabulary/` — the closed sets

Small, stable, and the reason a verifier is finite work. These are what the format *is*;
changing one is a format version bump.

### `observe.yml`

The eleven observation types. Read by the resolver (to derive `needs`) and by every verifier
(to know what it is being asked for).

```yaml
role:
  means: the semantic role the platform's accessibility layer reports
  needs: [a11y-tree]
  expect: [equals, one_of]
  note: computed, never authored — reading a `role` attribute checks what someone typed
layout:
  means: geometric relations between rendered boxes
  needs: [geometry]
  expect: [min, max, max_ratio, order]
  note: a relation the contract states, never an appearance judgment
```

### `conditions.yml`

What a `required:` clause may name, and what each resolves to as a scenario predicate.

```yaml
disabled:
  scenario: { props: { disabled: true } }
  requires_prop: disabled        # lint: the contract must declare it
hardware_keyboard:
  scenario: { environment: { hardware_keyboard: true } }
  verifier_must: attach or emulate a keyboard
```

`requires_prop` is a real lint rule the pipeline example would already fail without: a
condition naming a prop no chapter declares is a dangling reference.

### `roles.yml`

The closed role set, each with what it denotes on each platform — the concept, never the
attribute. `dialog` means "exposed as a modal surface", satisfied by `<dialog>`, by a trait,
by a pane title.

### `expect.yml`

The comparison grammar, deliberately tiny: `present · equals · one_of · contains · min ·
max · order · absent_from · source`. **This file is the one to defend.** The moment it needs
expressions, the second verifier stops being cheap and the platform-neutral half of the
conformance suite becomes unspecifiable.

### `capabilities.yml`

What a verifier may declare: `a11y-tree · identity · focus · geometry · interaction ·
announcement · name-provenance · source`. The vocabulary `needs` is written in, so the
runner can reconcile the two mechanically.

---

## 2 · `system/archetypes/` — the requirement library

Two files per archetype, as specified in `l0-archetype-spec.md`. What that spec does **not**
say, and should:

### Provenance is per requirement, not per file

Accountability #3 says every concrete fact traces to an external standard, an interview
answer, or a structural inference. An archetype requirement has no interview behind it, so it
must cite:

```markdown
| id | statement | observe | kind | required | source |
|---|---|---|---|---|---|
| BTN-05 | Where a hardware keyboard exists, both standard activation keys perform the action. | event | behavior | when:hardware_keyboard | catalogue:Web/button · catalogue:Android/Button |
| BTN-07 | While focused, a focus indicator is distinguishable from the unfocused appearance. | state | state | always | wcag:2.4.7 · catalogue:Web/button |
```

A requirement with no `source` is not authored yet — it is an opinion. This makes the library
auditable by someone who was not there when it was written, which is the whole point of
provenance.

### The bindings file holds only what differs

Established empirically by the pipeline example: `needs` derives from `observe`, so most
entries emptied out. What remains:

- an `expect` that differs per platform — `BTN-11`'s 24 / 44 / 48
- `needs_also`, where a requirement needs more than its observe type implies
- `binds: false` with a reason, where the concept has no referent
- `also`, a second observation of the same requirement — the identity/role split

---

## 3 · `system/policy.md` — the design system's own

L1. Cross-cutting decisions inherited by every contract: focus-indicator policy, motion
policy, touch-target floor, announcement politeness, error timing, loading and empty-state
conventions.

**Owned by the design system, not shipped.** The skill ships a *template* naming the
decisions that must be made, with each one blank. An unfilled policy is a visible gap, not a
silent default — the same rule as a pending token.

## 4 · `system/context.yml` — design-system facts

Extends the existing `.claude/design-system-context.yml`: token prefix, naming pattern,
per-platform naming convention, token source path, which platforms this system targets, and
where component contracts live. Facts about *this* design system that no standard supplies.

## 5 · Sub-component contracts

A zone whose `accepts` is `component:Icon` resolves against `Icon.md`. Two things the design
has not settled, both surfaced as G3 in the property map: nothing links the two verification
runs, so a Button containing a non-conformant Icon passes Button's contract completely.

---

# Build order

Fifteen archetypes in the role vocabulary. Not all cost the same.

| Tier | Archetypes | Why this tier | Source |
|---|---|---|---|
| **1 — foundation** | `button` `link` `heading` `text` | richest catalogue entries; between them they cover most components a design system starts with. `button`/`link` are also the pair whose *asymmetry* is load-bearing — Enter activates both, Space activates only one | catalogue, dense |
| **2 — containers** | `dialog` `list` `listitem` `image` | composition, focus containment, top-layer rendering, list position announcement | catalogue, moderate |
| **3 — selection** | `checkbox` `radio` `radiogroup` `status` | grouped semantics and the announcement asymmetry that started this whole line of work | catalogue, moderate |
| **4 — composed** | `tab` `tablist` `tabpanel` | **the bundle is empty on every platform.** Nothing is free, so these are authored from the WAI-ARIA pattern rather than derived from the catalogue — different work, and a useful control | `references/web/wai-aria-patterns.md` |

Tier 4 matters more than its position suggests: it is the case where v3's layering buys
nothing, and confirming that cleanly is what stops the archetype idea from being
over-applied.

## Two known gaps, before anyone starts

**`combobox` is not in the role vocabulary.** T5 named it deliberately as the pattern
"absent from the condensed tables", and F5 predicted exactly this failure mode. It needs
either a new role plus four bindings, or a decision that it is a composed pattern like tabs.
That decision should be made before tier 1, not after tier 4, because it tests whether the
closed set can close at all.

**Drag-to-reorder has no archetype and may not need one.** The catalogue records its bundle
as empty on every platform. If it resolves as `list` + `listitem` plus component-local
requirements, that is evidence the layering is right. If it needs its own archetype, the
closed set is less closed than claimed.

Both are T5's job, and T5 is now the test that decides whether the **format** ships, not just
whether the role set is complete.

## What has to exist before the library is usable

In order:

1. `system/vocabulary/` — all five files. Nothing else can be written against a vocabulary
   that is still implicit.
2. The provenance convention applied to tier 1, so the audit trail exists from the first
   archetype rather than being retrofitted.
3. `system/policy.md` as a template, with the decision list drawn from T1's G5 and G6 —
   which is where those gaps actually belong.
4. Tier 1, then a re-run of the pipeline example against the *real* `button` archetype rather
   than the eight-requirement fixture it currently uses.

That last step is the honest checkpoint. The pipeline example currently proves the mechanism
on a hand-made archetype; it proves the library only once the library exists.
