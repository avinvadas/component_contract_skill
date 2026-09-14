# What a contract draws from — file plan and structure

**Status: plan.** The layer between `references/` and a contract, which does not exist yet.

`references/` holds **external standards** — WAI-ARIA, WCAG, HIG, Material, UIA. A contract
never reads them. They are the source material from which the layer below is *authored*, once.

## Where opinion is allowed to live

The risk in a shipped vocabulary is that the skill starts telling a design system what to
think. The boundary that prevents it is already in `v1-implicit-guarantees-catalogue.md`:

> an entry belongs here only if the platform provides it *automatically*, without the
> implementer doing anything.

An archetype bundle is therefore **not** an opinion about good design. It is an inventory of
what a platform gives you free, and therefore what you must reproduce yourself if you do not
use the native control. That is a factual claim about platforms, checkable against their
documentation, and wrong in a way that can be demonstrated.

**The skill ships facts about platforms. The design system ships opinions** — in
`system/policy.md`, which is shipped blank.

Four of the five vocabularies below describe the substrate rather than design: `observe` is
what a platform's accessibility layer exposes, `capabilities` derives from it, `expect` is a
minimal comparison algebra, `conditions` is a set of named predicates. If one is incomplete
that is a bug, not a stance.

### When the platform does not provide it

The scope rule says a bundle entry must be something the platform gives automatically. That
raises the obvious question, and it hides three different situations.

**Nothing provides it anywhere.** Tabs: roving focus, arrow-key movement, panel association —
free on no platform, as the catalogue records explicitly. Still a requirement, just not an
*inherited* one. So a bundle holds two kinds of entry:

| Kind | Meaning | Provenance |
|---|---|---|
| **inherited** | the platform provides it; you must reproduce it if you substitute | `catalogue:Web/button` |
| **authored** | nobody provides it; every implementation builds it | `apg:tabs` · `hig:...` · `material:...` |

Both cite something outside the skill. That is what keeps an authored requirement from being
our opinion — it is a published convention, not a preference.

**Some platforms provide it, others do not — but the concept exists everywhere.**
**"Not free" does not mean "not required."** Live regions are declarative on Android and
imperative on iOS; both satisfy *"opening is announced"*. The requirement binds identically —
iOS simply requires code where Android requires a modifier. Free-ness decides where a
requirement is **sourced**, never whether it binds.

**The concept has no referent at all.** `binds: false` with a reason. The test is referent,
not difficulty: *"no platform-level form model exists on iOS"* qualifies; *"this is hard on
Android"* does not.

### The decision procedure

```
Is it true of every component of this archetype?
├─ no  → component-local requirement, in the contract
└─ yes → Does some platform provide it automatically?
         ├─ yes → how many platforms?
         │        ├─ several → archetype bundle, provenance = catalogue
         │        └─ exactly one → CANDIDATE, not an inheritance. Is the behaviour a
         │                          user-facing expectation across platforms, or a
         │                          convention of the platform that automates it?
         │                          ├─ expectation → archetype bundle
         │                          └─ convention  → not a bundle entry at all
         └─ no  → Does a published standard or convention specify it?
                  ├─ yes → archetype bundle, provenance = that standard
                  └─ no  → it is an opinion → policy.md, or the contract
```

**The single-platform branch was added after `combobox`.** CBX-09 — *the entry remains
editable after a candidate is committed* — is sourced only from macOS's `NSComboBox`, and it
passes: remaining editable is what distinguishes a combobox from a picker everywhere, and one
that locks after selection is a picker wearing the wrong role. Contrast macOS `Window`'s
*"position and size restored between launches"*, also single-platform and squarely a desktop
convention, which fails the same test.

Without this branch, one platform automating something would silently impose it on four.

### State it where every platform has a referent

The positive form of the scope rule, and it catches a class of problem before it becomes an
exclusion.

iOS's header trait is binary — there is no level — which is why v3's Modal states *"the title
is exposed as a heading"* and deliberately not *"as an h2"*. The first binds everywhere; the
second would have needed a `binds: false` on iOS for no gain.

**If no level of abstraction lets every platform have a referent, the requirement is
over-specified.** Cheaper to find while writing the requirement than while writing the fourth
binding — and a `binds: false` that could have been avoided by rewording is a defect in the
requirement, not an honest exclusion.

### Where the skill *is* opinionated, stated plainly

Not neutrality, and pretending otherwise would be worse than admitting it. The six chapters
are a taxonomy of concerns. The three prop categories are a stance. Mandatory divergence
reasons are a stance. So is the three-state result, and so is refusing to let a requirement
be dropped silently.

These are opinions about **documentation practice**, not about design — a design system can
disagree with every aesthetic and compositional choice it makes and still use this format.
But they are opinions, and a team that rejects them should know that up front rather than
discover it in chapter four.

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

### ~~`roles.yml`~~ — deleted; the archetype library *is* the role registry

A closed role set is the one vocabulary here that is genuinely a **taxonomy**, and taxonomies
are opinions. Naming the set *button, link, tab, dialog, heading, status…* claims what kinds
of thing components are — imported wholesale from ARIA, a web taxonomy applied to native. It
has already failed once: `combobox` is not in it.

So it does not exist as a separate list. An archetype already names a role; the role
vocabulary is nothing more than **the index of archetypes that exist**. Adding an archetype
adds a role. `text` and `image` become archetypes with near-empty bundles, which is legal —
`tab` already proves an empty bundle is a valid outcome.

**The set is then closed by cost, not by decree.** Add any archetype you like; the price is
stating what it means on each platform you target, which is work required before anything
could verify it anyway. It is not a vocabulary you are constrained to — it is a registry of
concepts whose cross-platform meaning has been established, extended by doing the
establishing.

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

**`combobox` — RESOLVED.** It needs an archetype, now built at
`system/archetypes/combobox.md`. Composing it from `text` + `list` fails immediately, and the
reason generalises into a criterion worth more than the case:

> **An archetype is needed exactly when the platform's accessibility layer reports a distinct
> role for the thing.** You cannot compose your way to a role — no arrangement of a text
> archetype and a list archetype produces something VoiceOver calls a combo box.

The registry extended by cost, exactly as designed: the price was four bindings, and paying
it was routine.

**Drag-to-reorder — PREDICTED, not yet confirmed.** The criterion above answers it without
building anything: assistive technology reports a reorderable list as a **list**, not as a
distinct role, so it should resolve as `list` + `listitem` plus component-local requirements
and needs no archetype. Worth confirming when the component is actually converted, but it is
now a prediction the model makes rather than an open question.

Both are T5's job, and T5 is now the test that decides whether the **format** ships, not just
whether the role set is complete.

## What has to exist before the library is usable

In order:

1. `system/vocabulary/` — four files, not five. Nothing else can be written against a
   vocabulary that is still implicit.
2. The provenance convention applied to tier 1, so the audit trail exists from the first
   archetype rather than being retrofitted.
3. `system/policy.md` as a template, with the decision list drawn from T1's G5 and G6 —
   which is where those gaps actually belong.
4. Tier 1, then a re-run of the pipeline example against the *real* `button` archetype rather
   than the eight-requirement fixture it currently uses.

That last step is the honest checkpoint. The pipeline example currently proves the mechanism
on a hand-made archetype; it proves the library only once the library exists.
