# Architecture — what each file is, and how they compose

Six layers. Each is owned by someone different and changes on its own cycle, which is the
constraint the whole design serves: a design system should be able to state an intent once
and have every platform check it, without the skill knowing what test framework anyone runs.

```
references/      external standards           read once, by a human, to author the layer below
system/          shipped source layer         vocabulary · role-archetypes · templates
facts + policy   THE DESIGN SYSTEM'S OWN      what it IS  +  what it has DECIDED
<contract>.md    one component                the design system's own, per component
*.json one platform's view          generated — the interchange format
3-verifiers/     someone else's toolchain     reads canonical, drives XCUITest/Playwright/Compose
```

**Facts and policy are both the design system's, and are not the same kind of thing.** A fact
says what this system *is* — the component tier is called `comp`, `bgColor` means background.
A policy says what it has *decided* — every focused control renders a focus indicator. The
difference is not tone, it is what can be done with each:

| | facts (`.claude/design-system-context.yml`) | policy (the design system's own file, `contracts.policy`) |
|---|---|---|
| detectable | **yes** — `detect_tokens.py` proposes them from the tree | **never**; no amount of reading finds a decision |
| falsifiable | **yes** — a wrong fact is lint | no; a policy can only be unwise |
| when missing | the resolver cannot read the tree | the requirement is simply not claimed |

That is why one ships a detector and the other ships a blank template.

**The skill's output ends at the canonical document.** Everything below it belongs to whoever
owns that toolchain. Every design error in this project's history was the skill reaching
further down — the v3 manifest, the v4 emitters, treating a Storybook story as a scenario.

---

## `references/` — external standards

WAI-ARIA, WCAG, the four platform HIGs, DTCG, platform event models. Nothing here is specific
to any design system, and **no contract ever reads them**. They are the source material a
human uses, once, to author `system/`. Each carries a `Last verified:` date that Phase 0A
checks for staleness.

## `system/` — the shipped source layer

### `vocabulary/` — four closed JSON files

| File | Holds | Why closed |
|---|---|---|
| `observe.json` | the 11 observation types (`role`, `name`, `state`, `focus`, `layout`, `token`, …) | each names *how a fact is obtained*, and `needs` is derived from it, so bindings stay small |
| `expect.json` | the 10-verb comparison grammar (`equals`, `one_of`, `min`, `order`, `absent_from`, …) | its own comment says **defend the size of this file** — an expression language makes a second verifier expensive and the conformance suite unspecifiable |
| `conditions.json` | the 10 condition tokens (`disabled`, `hover`, `focused`, `hardware_keyboard`, `touch_input`, `rtl`, `expanded`, …) plus `<zone>_present` | a condition resolves to a scenario **predicate** — a class of instances, never a reference to one. Resolvers **load** this file rather than restating it; two copies drifted in both directions once already |
| `capabilities.json` | the 8 things a verifier may declare it can/cannot observe, and the two strategies (`witness`, `construct`) | a runner reconciles document against declaration mechanically; anything unobservable is reported `unverified` **by name**, never passed |

JSON, not YAML, deliberately: these are read by every verifier in whatever language it is
written in, and JSON parses everywhere with no dependency. Human-first formatting belongs in
the contract `.md`, not here.

### `role-archetypes/` — a role plus what platforms give free

One `.md` per role (`button` 12 requirements, `link` 9, `combobox` 9, `heading` 3, `text` 2),
each paired with a `.bindings.json`. The `.md` holds a **Native backing** table — what each
platform provides, with `none` meaning every implementation builds the semantics by hand —
and a requirement table whose every row cites a `source`.

The rule that keeps these factual: *an entry belongs here only if the platform provides it
automatically, without the implementer doing anything.* So a bundle is an inventory of what
you get free, and therefore what you must reproduce if you substitute a generic view. **A
requirement with no source is an opinion**, and opinions live in the policy template.

A contract names one with `role-archetype: button`. Many contracts share one — `Button` and
`IconButton` both inherit the same twelve rows.

### `templates/` — shipped blank

`policy.template.md` is the design system's own cross-cutting decisions (focus indicator,
touch-target floor, literal denial and its declared property set, reduced motion, …). Every
row ships empty **on purpose**: an unfilled policy is a visible gap, the same rule as a
pending token. `context.template.yml` holds facts about *this* design system that no external
standard supplies — token prefix, naming pattern, tree location, target platforms.

## The component layer

| File | Owner | Holds |
|---|---|---|
| `Button.md` | the design system | six chapters: Intent, Structure, Composition, Appearance, Behavior, Accessibility |
| `Button.bindings.json` | the design system | only the ids *this* contract introduces, and only where `expect` is not derivable |
| the policy file, located by `contracts.policy` | the design system | the filled policy — its requirements join every contract. **In their repo, never in the skill's `system/`**, which ships blank and is replaced on update |
| the policy's `.bindings.json`, beside it | the design system | per-platform `expect` for policy ids |

Accessibility is its own chapter rather than a column, so it can be reviewed as an aspect in
its own right. Composition owns *existence*; Accessibility owns *semantic exposure*.

---

## How resolution composes them

`scripts/resolve.py` — contract + role-archetype + policy → one canonical document per platform.

**Bindings layer, later overriding earlier.** Three sources, one per ownership layer:

```
system/role-archetypes/button.bindings.json   shipped with the skill
<policy>.bindings.json                        the design system's
Button.bindings.json                          this contract's own
```

**`needs` is derived, never authored.** `observe: role` implies `needs: ["a11y-tree"]`. A
binding carries `needs_also` only where a requirement needs more. Most bindings were
boilerplate until this table existed.

**Conditions become predicates.** `when:disabled` resolves to `{"props": {"disabled": true}}`
— a class of instances. A verifier satisfies it by finding a witness or constructing one;
finding neither is `unverified`, not a pass.

**Nothing may be excused by omission.** A requirement with no binding for a platform is a
lint failure. A requirement that genuinely has no referent there carries `binds: false` with
a stated reason and still appears in that platform's document — so a platform cannot lower
its own bar by leaving something out.

`scripts/tokens.py` — the token tree, and slot resolution.

Reads the design system's token tree and resolves each declared property. The split that
keeps it honest: **structure** (tiers, component scopes, dimension axes) is read from paths
and is reliable; **leaf meaning** is not readable from paths at all and is derived from the
alias graph, where a component leaf annotates the semantic token it consumes. Roles are keyed
on full paths — keying on the leaf derives `primary → background`, which is wrong everywhere
else in the tree — and primitives are excluded, being meaning-free by construction.

A slot lands in one of six states, and only two mean nothing is wrong:

```
bound · not-applicable          no action
absent-from-tree                token tree owner adds a token
dimension-unmet                 token tree owner adds a state variant
ambiguous                       contract author pins one
unmapped-leaf                   extend the leaf map
```

`unmapped-leaf` stays separate from `absent-from-tree` deliberately: merged, the tool would
tell someone to add a token that already exists under a name it failed to parse, polluting
the tree it exists to protect. A **pinned name absent from the tree is a lint failure**, not
a gap — it is the one path by which an invented token name enters a design system.

`scripts/machine.py` — state machines.

A component that owns moving state writes its transitions as one table. Every cell of the grid
*states × events* is authored, marked unreachable with a reason, or left empty — and every
empty cell becomes a generated check that the event changes nothing. That is **closure**, the
claim a machine makes that no row states. It is computed on the merged machine, archetype plus
contract, and kept small by composition: a machine covers only its own component's state, so a
parent never multiplies its children's grids. An effect of a transition is an ordinary
requirement conditioned `when:following:<transition>`, so a trigger is bound once.

`scripts/detect_tokens.py` and the design-system context — naming a tree the skill has never seen.

The resolver reads a design system's naming from `.claude/design-system-context.yml`: which
top-level group is each tier, one template per path shape, and a map for property spellings it
cannot read (`bgColor → background`). Phase 0B proposes the first two from the tree itself —
tiers from the direction aliases point, patterns from observed shapes decided by sibling
evidence — and confirms them once. Spellings are asked lazily, per component. With no facts
the heuristics run unchanged; a fact never switches guessing on, and a wrong fact is lint.

`scripts/resolve_view.py` — the reading artifact.

The contract `.md` is *source*; this is what a person reads. Organised by the contract's own
chapters, with **origin as a column** — chapters answer *what kind of fact is this*, origin
answers *is this mine to change*. Inherited archetype and policy requirements appear here,
resolved, though they appear nowhere in the contract file.

It renders **two** token states, not six, plus a gap table saying what is wrong and who fixes
it. A reader needs to know who acts, not a taxonomy; the canonical document carries the full
six-way state because a machine routes on it.

---

## The invariants

**0. Every check validates a LOGIC OUTCOME, as the end environment holds it.** The rendered DOM
and accessibility tree are the structural logic's outcome — which element carries the role, what
is in the tab order, whether the form submits. The applied cascade is the style logic's outcome —
which token each property references, followed through `var()` chains, with any transform
(`color-mix(in oklab, var(--primary) 80%, transparent)` is `primary` at 80%). Never the
**production path** (React, Lit, `button.tsx`, class lists) and never the **rendered values**
(computed colours, pixels): a literal that equals the token's value is still a failure. The
capability that reads the cascade is `applied-styles`; `source` now means only a component's
declared props.

1. **Nothing passes by accident.** A gap emits `pending` with no `expect`, so a verifier has
   nothing to compare and reports `unverified`. An unresolved token cannot produce a pass.
2. **Lint and gaps are different animals.** Lint means the *document* is malformed and fails
   the parse. A gap means the document is fine and the *token tree* cannot express something
   yet. Both print; only lint exits non-zero.
3. **Unobservable is said out loud.** A verifier declares its capabilities; anything a
   requirement needs that the verifier lacks is reported unverified **in the verifier's own
   words**.
4. **No name is invented.** An unresolved token has no name written for it. A suggested path
   in a gap report is addressed to the tree owner and never enters the `token` column.
5. **Every concrete fact has a provenance** — an external standard, an interview answer, or a
   structural inference from one of those. Anything else is cut.
