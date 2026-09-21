---
name: component-contract
description: Creates structured component contract markdown files for design systems, and optionally generates a JSON schema for prop validation. A component contract is a formal specification that documents a UI component's semantic markup, design tokens, behavior, and accessibility requirements. Use this skill whenever a user wants to create a new component spec or contract, document a UI component formally, generate a component contract md file, specify the structure or behavior or tokens of a component, audit what tokens a component uses, or generate a JSON schema for a component. Also trigger when the user says things like "create a contract for X", "document this component", "write up the spec for [component name]", "add [component] to the design system contracts", "I need a component contract", or "generate a schema for this component". If the user mentions a Figma link, a Storybook URL, or a coded reference alongside a component name or design system task, this skill almost certainly applies.
---

## What this skill produces

One interview produces **one component contract**, capturing the design intent of a UI component across any combination of **supported** platforms (Web, iOS, Android, macOS) in a single document. Windows and Linux are on the roadmap and deliberately not supported yet — see "Supported platforms" below.

The contract is **six chapters**, in this order, so a reader always knows where a given fact lives:

| | |
|---|---|
| **1 Intent** | what it is and what need it solves |
| **2 Structure** | what the thing is, and the space it occupies |
| **3 Composition** | what it contains, and on what terms |
| **4 Appearance** | which properties are tokenised, and what varies |
| **5 Behavior** | what it does, emits, receives, and how its state moves |
| **6 Accessibility** | semantic exposure — its own chapter, reviewable as an aspect in its own right |

**A requirement is written once, in plain language, and never names a platform's vocabulary.** "The control is reachable by the platform's sequential focus navigation" is one requirement; that it is Tab on web and a swipe gesture on iOS is a **binding**, held in a companion `[Component].bindings.json`. This is what lets one document serve every platform without a column per platform or a file per platform.

**The contract inherits.** One frontmatter line — `role-archetype: button` — brings in what every platform already guarantees for that role, and the design system's policy brings in its cross-cutting commitments. Neither is restated per component.

**Three things are generated from it, never authored** (Phase 6): a `[Component].spec.md` for people, with everything inherited resolved in; one `[Component].[platform].json` per platform — a description an existing test framework can consume, not a test; and, only if asked, a props `[Component].[platform].schema.json`.

The person using this skill does not need to know HTML, ARIA, native accessibility APIs, or any platform's interaction conventions. The skill derives all technical decisions from plain-language answers about the component's purpose and how users interact with it.

---

## Supported platforms

**Supported: Web, iOS, Android, macOS.** These are the platforms Q2 offers and the only ones a contract may target.

**On the roadmap, not supported: Windows, Linux.** Their reference material stays in `references/` because the research in it is sound and reviewed — but it is *not wired into the interview*, Q2 does not offer them, and no contract should include a Windows or Linux row today.

The reason is specific rather than a matter of priority: `references/structural-fact-validation.md` has no verified way to obtain a real rendered tree for either platform, so a contract targeting them could be written but never checked. Every other supported platform has at least one demonstrated route to its real tree. Shipping a platform whose claims cannot be tested would contradict what this skill says it is accountable for.

Linux carries a second, independent gap: it has no platform-conventions file, because GNOME, elementary, and KDE each publish a separately-opinionated HIG and doing it properly means three files rather than one approximation.

Both are revisited once the four supported platforms are stable, tested, and validated — not before.

## Scripts

`scripts/` holds tools this skill runs. They locate the shipped `system/` layer relative to themselves, so they work wherever the skill is installed, and they need nothing beyond Python 3 — the context file is read with PyYAML when it is installed and with a strict built-in reader otherwise, which refuses what it cannot parse rather than guessing.

| Script | Run it when |
|---|---|
| `scripts/check_references.py [--days N] [--json]` | Phase 0A, and on a schedule independent of any run. Reports which reference files are due to be re-checked against the standard they cite, and how each is checked. Reads dates only: no network, no judgement, no edit. Exits 1 when anything is due. |
| `scripts/schema.py <Component>.md [--out DIR]` | Phase 6, only if Q10 asked for a props schema. One file per platform, derived from the contract's own prop and zone tables. Replaces writing the schema by hand: the mapping has no judgement in it, and an authored file in `generated/` is one nothing can reproduce. |
| `scripts/check_generated.py [--exclude NAME] [--json] [--fix]` | Phase 6, only when the run decided a policy row or changed a token-reading fact — and any time someone wants to know whether the committed documents still match their inputs. Reports stale, missing, orphan and unresolvable, per contract. Rewrites nothing without `--fix`, and never deletes. |
| `scripts/detect_tokens.py <tree> [--json]` | Phase 0B — a token tree has been found. Proposes tiers and naming patterns with evidence, and lists questions. Writes nothing. |
| `scripts/resolve.py <Component>.md [--out DIR]` | A contract in the format of `docs/contract-md-format-spec.md` is to be resolved against its role-archetype, policy and token tree into one canonical document per platform. |
| `scripts/writeback.py <Component>.md` | Phase 6, after the first resolve — writes every token the tree answers into the contract's own slots, as a token or a `{variant}` pattern, with its `scope`. Asks nothing, decides nothing the tree did not. |
| `scripts/resolve_view.py <Component>.md [--out FILE]` | The same contract needs its human-readable resolved view. |
| `scripts/evidence.py <Component>.md <results.json>` | An implementation has been observed (a verifier's results). Turns what it contradicts or adds to the tree into questions. Never edits the contract. |
| `scripts/learned.py snapshot` / `diff` | At the start of a run, and at the end — reports what this run added to the design system's own layer. |
| `scripts/test_scripts.py` | After changing any script. |

Phase 5 writes the contract these consume — the six-chapter format specified in `docs/contract-md-format-spec.md` — and Phase 6 runs them.

## Reference files

`references/` holds the external, design-system-agnostic standards this skill derives from. They are not design-system content — they're the same regardless of which design system a component belongs to. SKILL.md's own tables cover the common cases inline; consult the matching reference file when a case falls outside those tables, or when you need the full attribute/keyboard set for a pattern the table only names in passing.

`references/` is organized by scope: platform-specific standards live under a directory named for that platform; standards that apply regardless of platform stay at the root.

### Universal (apply regardless of platform)

| File | Consult it when |
|---|---|
| `references/design-tokens-format.md` | Phase 2 Path B — recognizing whichever token file shape (DTCG, Style Dictionary, CSS custom properties, Tailwind config) the coded reference actually uses. |
| `references/figma-variables-model.md` | Phase 2 Path A — extracting bound tokens from Figma via structured tool access when available, or the manual-inspection fallback when it isn't. |
| `references/json-schema-draft-07.md` | Phase 6 — the full keyword reference and the Draft 07 vs. 2020-12 decision. |
| `references/token-naming-validation.md` | Phase 6 — checking a real, generated implementation's token names against chapter 4.1's token slots, when `generated_downstream` is confirmed. Not a props-schema concern; a separate check against source files, not a JSON instance. |
| `references/structural-fact-validation.md` | Writing or reviewing a **verifier**, which is where this check now lives — how to obtain a real *rendered* tree per platform (never source code) and read order from it. The skill itself no longer runs it; the canonical document describes the facts, and whoever owns that platform's toolchain checks them. |
| `references/platform-differences.md` | Comparing how a cross-cutting concern (accessibility API, layout adaptation, RTL, motion) is expressed across platforms, before following into the relevant platform directory for depth. Comparison content only — it does not decide which platform applies to a given component. |
| `references/native-events-models.md` | Phase 5 chapter 5.2 Events/chapter 5.2 Events for any non-Web platform row — the native counterpart to `web/dom-events-model.md`, covering the idiom fork on each platform (closures vs. delegates, lambdas vs. listeners, routed vs. classic .NET events, GObject signals vs. Qt signals/slots). |

### `references/web/` — consulted when Q2 includes Web

| File | Consult it when |
|---|---|
| `wai-aria-patterns.md` | Deriving markup (Phase 3) or accessibility (Phase 4) for a pattern not fully covered by the decision tables below — combobox, menu, tooltip, tree view, slider, grid, accordion, or the full keyboard set for any pattern. |
| `wcag-mapping.md` | Deriving §6 Accessibility (Phase 4), to ground a requirement in the success criterion it satisfies — optional citation, not a new question to ask the designer. |
| `html-semantics.md` | Phase 3 edge cases the decision table doesn't resolve — nested interactive content, disabled vs. aria-disabled, form-associated custom elements. |
| `css-layout-and-interaction.md` | Phase 3 chapter 3.1's position column / chapter 2.2 Adaptive layout — container queries, and CSS logical properties for RTL-safe positioning. Phase 4/5 chapter 4.2 Interaction states / chapter 6 Accessibility — the `:focus` vs. `:focus-visible` distinction, `prefers-reduced-motion` and motion tokens. |
| `dom-events-model.md` | Phase 5 chapter 5.4 Machine/chapter 5.2 Events/chapter 5.2 Events — the framework-agnostic `CustomEvent` contract, and how a contract's behavior/accessibility claims are verified against rendered DOM output rather than framework internals. |

### Other platforms — consulted when Q2 includes that platform

Q2 (Platform) is multi-select; Phase 3/4 run once per selection, and for any platform other than Web, that run consults the matching file below instead of the web-specific tables — see each file's "Component / structure resolution" and "Accessibility API" sections.

| File | Platform |
|---|---|
| `references/ios/ios-hig-accessibility.md` | iOS |
| `references/android/android-material-accessibility.md` | Android |
| `references/macos/macos-hig-accessibility.md` | macOS |
| `references/windows/windows-ui-automation.md` | Windows — **roadmap, not supported**; not reachable from Q2 |
| `references/linux/linux-atspi-accessibility.md` | Linux — **roadmap, not supported**; not reachable from Q2 |

### Platform convention files — cite-and-confirm only, never a default

A second file for four of the five platforms covers **behavioral/compositional convention** — ephemeral-surface lifecycle, window/composition patterns, navigation and gesture conventions — as published by that platform's own guidelines, strictly excluding anything visual (color, spacing, motion curves, icon sets), which stays out of scope for this skill entirely per the Conflict resolution policy. These are never applied as defaults: see "Citing a platform convention" below Q10 for the only way this material is allowed to reach a contract. Linux doesn't have one of these yet — GNOME, elementary, and KDE each publish a separately-opinionated HIG, and doing this properly for Linux means three files, not one; that's deferred rather than folded in as a single approximate file.

| File | Platform |
|---|---|
| `references/ios/ios-platform-conventions.md` | iOS |
| `references/macos/macos-platform-conventions.md` | macOS |
| `references/android/android-platform-conventions.md` | Android |
| `references/windows/windows-platform-conventions.md` | Windows — **roadmap, not supported** |

Each reference file covers exactly one external standard or concern, independent of the others — CSS mechanics, DOM events, ARIA patterns, WCAG, token file formats, JSON Schema, and each native platform's own accessibility/interaction model or convention set don't reference each other's internals. Adding coverage for a new standard means adding a new file, not expanding an existing one's scope; this keeps each file independently correctable by someone who only knows that one domain.

Every reference file carries a **`Last verified:` date** directly under its "Source of authority" line. Phase 0 uses it.

---

## Phase 0: Pre-interview checks

Three independent checks, all run once, before Phase 1, every time the skill starts. All are cheap by default and only occasionally do real work.

**Before any of them, snapshot what the design system already knows:** `python3 <skill>/scripts/learned.py snapshot`. It records the context file's facts, the policy's decided rows and any local role-archetypes, so Phase 6 can report exactly what this run added. Take it first, so that what 0B and 0C confirm counts too — on a design system's first run everything is new, and it was.

### 0A: Reference freshness check

1. Run `python3 <skill>/scripts/check_references.py --json`. It reads every file's `Last verified:` date — local and free, every file unconditionally — and reports which are due, each with **how** it is checked: `fetch` (it cites a URL), `read` (it names a source in prose), or `agrees-with-others` (it cites no external source because it aggregates the other files). Don't re-implement the date arithmetic here, and don't hardcode a file count: both drift every time a file is added, which is the staleness this check exists to catch elsewhere.
2. Nothing due — no network access, nothing to report. Say nothing.

**This check also runs on a clock, not only here.** A standard moves whether or not anyone is contracting a component, and references feed the *reasoning* in Phases 2–4, never the resolver — so what a standard implied is frozen into a contract's text when it is written, and no later re-run can notice it changed. Phase 0A is the fallback, not the mechanism. See "Keeping references current" below.
3. If 90 days or more have passed **and** web access is available in the current environment: fetch the URL(s) the file cites in its "Source of authority" line and compare against what the file currently says.
   - **`platform-differences.md` is the one exception** — it aggregates every other file rather than citing an external URL itself, so "checking" it means confirming it still agrees with whichever of those files were also due this run, not fetching anything.
   - **No material change** (the spec's version/status is the same, nothing the file describes has been renamed, deprecated, or superseded): update that file's `Last verified:` date to today and move on silently — no need to mention this to the user.
   - **Material change found** (a new spec version, a deprecated/renamed API or attribute, a new pattern that supersedes what's documented): stop and tell the user what changed and which file it affects, before proceeding to Phase 1. Ask whether to update the reference file now, defer it, or continue this session with the existing content. Never rewrite a reference file's content on your own initiative — these are curated explanations, not a scrape of the spec, and a drive-by edit from an automated check is exactly the kind of unreviewed change that principle exists to prevent.
4. If web access isn't available in the current environment, skip step 3 entirely for this run. Only mention the skip if at least one file was actually due (don't report "nothing to check" as if it were a finding) — and never block the interview from starting because a freshness check couldn't run.

This check must never be the reason someone can't generate a contract. A skipped, deferred, or inconclusive check is always a reason to proceed with what's already there, not to stop.

### 0B: Design system context

Everything in `references/` is external and generic — it's the same regardless of whose design system this is. This step is the opposite: a handful of facts specific to *this* design system that don't change component-to-component (token prefix, which platforms use which framework, naming casing, RTL support, whether existing contracts live somewhere findable) and shouldn't be re-derived or re-asked on every single invocation.

1. Look for a context file at `.claude/design-system-context.yml` in the current working directory (create the `.claude/` directory if it doesn't exist yet, when writing in step 3). This is a cheap local file check — do it unconditionally.
2. **If it exists**, load it silently. Its contents seed defaults for Phase 1 onward (e.g., a per-platform framework default that changes which concrete controls Phase 3 names for iOS/Android, a default platform set to pre-check in Q2) and supply facts later phases read directly rather than ask about (`tokens.prefix` and `tokens.patterns`, which Phase 2 normalizes extracted token names against; `tokens.format`, which tells Phase 2 what file shape it is reading) — seeding a default is not the same as skipping the question. A component can still legitimately differ from the system-wide default (not every component targets every platform the system generally supports), so nothing here should suppress a question, only pre-fill or bias its options.
3. **If it doesn't exist**, don't run a Phase-1-style sequential interview for this — these fields are independent of each other (unlike Phase 1's questions, which deliberately go one-at-a-time because later options depend on earlier answers), so there's no reason to force multiple round-trips. Instead:
   - **Detect first.** Scan the working directory before asking anything: a token file (`tokens.json`, `tailwind.config.*`, `*.tokens.json`, CSS custom-property definitions) for format, prefix, and the `naming-pattern` its canonical paths follow — read several paths, not one, since a slot order is only visible across examples; platform manifests (`Package.swift`/`Podfile` vs. `build.gradle` dependencies) for framework hints; an existing directory of files carrying this skill's frontmatter shape for where contracts already live. This costs nothing and needs no confirmation round-trip when it succeeds outright. **Read the file's actual content, not just its filename** — a `tailwind.config.js` whose colors reference `var(--token-name)` means the real source format is CSS custom properties with Tailwind only as a consumption layer, not "tailwind" as the format; recording it as plain Tailwind would be wrong even though the right filename was found.
   - **Ask everything left in one batched `AskUserQuestion` call, up to four questions.** Cover token format and prefix (the detector proposes `naming-pattern` itself — confirm its proposal rather than asking for a slot list), whether token values are ever hand-typed in components or are strictly generated downstream from the token tree (`generated_downstream` — a policy fact, not a technical detection; see references/token-naming-validation.md for what this gates), per-platform framework (SwiftUI vs. UIKit, Compose vs. View system, GTK vs. Qt — this materially changes which concrete controls Phase 3 names, not cosmetic detail), naming casing, and RTL support. Where step one detected a value — including a confident one — make it the first, pre-recommended option in that question rather than skipping confirmation entirely; a system-wide default deserves a quick confirm, not a silent guess, since every future component inherits it. If more than four fields need either confirmation or asking (a design system spanning several platforms easily exceeds four), use a second batched call rather than forcing everything into one or dropping confirmation for whichever fields didn't fit — order both calls so anything ambiguous or fully undetected comes first, confident detections last, so a second call is the one most likely to be skippable in practice, not the one most likely to matter.
   - **When a token tree is found, run the detector on it** rather than reading paths by eye: `python3 scripts/detect_tokens.py <tree> --json`. It proposes `tokens.tiers` (from the direction aliases point, not from group names), `tokens.patterns` (from the observed shapes of component-tier paths) and a list of questions, each with its evidence. It never writes anything. **Ask only the questions whose `components` is null here** — the ones that are genuinely system-wide, such as tiers. Every other question names the component(s) it concerns, and waits for one of them to be contracted: run the detector again then with `--component <name>` and ask only what that component needs. Real systems make this essential, not tidy — on Primer the unfiltered detector raises 39 questions, none system-wide, and a Button needs 8 of them. Put the detector's `suggested` property first, marked Recommended. When a design system declares `tokens.sources`, the tiers are declared, not inferred, and the detector says so. A `leaf_map` entry is written only from a confirmed answer — never from a suggestion, and never from a spelling the resolver guessed, because one wrong entry (`default: background`) mis-reads every token that ends in that segment.
   - **Never ask for `naming_convention`'s specific separator/case/prefix directly** — unlike `generated_downstream`, this isn't a fact the designer can just state; it's detected empirically from a real generated name the first time Phase 6's token-name validation runs (see references/token-naming-validation.md's "lock on first success"), then written back here so later components skip re-detection.
   - Write the result to `.claude/design-system-context.yml` when done, and confirm the path to the user. This file is meant to be checked into the design system's own repo, not treated as scratch state — it's shared context for the whole team, not a personal cache.
4. **If a later phase detects a contradiction** between this file's contents and something else (a coded reference, a direct interview answer) — that's the conflict-resolution policy's job, not this step's. See below. A confirmed correction there should update this file, not just the current contract, so the system-wide default stays accurate for the next component.

This step, like 0A, must never block the interview — if the file can't be read or written for some reason, fall back to asking the equivalent questions inline during Phase 1 instead of stopping.

### `design-system-context.yml` schema

Only include platform keys this design system actually uses — never write a placeholder for a platform it doesn't target. **`web` has no `framework` key, unlike every other platform, and that's deliberate, not an oversight** — see "Native platform technology as the stated level" below Phase 2 for why.

```yaml
design_system: [free-text name, optional]
last_updated: [YYYY-MM-DD]

tokens:
  format: dtcg | style-dictionary | css-custom-properties | tailwind  # the token FILE's shape — not a naming fact; see "Three naming facts" below
  prefix: [string, e.g. "ds-", "color-", "--ds-"]
  # naming-pattern is recorded as `patterns` below — see there. A single ordered slot list was
  # the field until a real tree disproved the "one per design system" assumption: the eval
  # fixture's component tier alone holds three shapes (`…{property}`, `…variant.{variant}.{property}`,
  # `…size.{size}.{property}`), so one list could never have parsed it.
  source: [path to the token tree, relative to the directory holding .claude/ — read by scripts/resolve.py when a contract does not name its own tree]
  tiers:  # which top-level group plays each role — proposed by scripts/detect_tokens.py from alias direction, then confirmed
    primitive: [top-level group, e.g. "core"]
    semantic: [top-level group]
    component: [top-level group — or "*" when the components ARE the top-level groups, with no namespace (`button.*`, `chip.*` beside `semantic.*`): every group no other tier claims; or a list of those groups. A group no tier claims is reported, never silently skipped]
  patterns:  # THE naming-pattern field. One template per path SHAPE, per tier, most specific first. Slots: {component} {property} {state} {*}, or any axis name ({variant}, {size}), in ANY order — `component.{component}.{property}.{state}.{variant}` is as valid as property-last; anything else is literal. Written as `component.…` even when the tree has no namespace (tier "*"). Proposed by scripts/detect_tokens.py, confirmed once. A design system with a single shape writes a single template.
    component:
      - [e.g. "component.{component}.variant.{variant}.{property}"]
      - [e.g. "component.{component}.{property}"]
  shared:  # component-tier groups that are PATTERNS, not one component — and which components draw from each. Asked once in Phase 0B (detect_tokens.py lists the groups); a component is added to a group when the resolver reports `shared_unconfirmed` and the person says yes
    [group, e.g. control]: [components, e.g. button, segmented-control]
  leaf_map:  # ONLY spellings the resolver cannot read, each from a confirmed answer, asked lazily per component — never a suggestion written unconfirmed
    [spelling]: background | foreground | border-color | focus-ring | border-width | radius | padding-inline | padding-block | gap | height | font-family | font-size | font-weight | line-height | letter-spacing | elevation | opacity | duration | easing
  generated_downstream: true | false  # confirms/denies hand-typed values as accepted practice — gates Phase 6's token-name validation entirely; see references/token-naming-validation.md
  naming_convention:  # only meaningful when generated_downstream is true — one locked convention per PLATFORM, detected once from a known-correct generated name, never guessed. Three independent axes (row, prefix, scope_depth) that must all hold; see references/token-naming-validation.md Steps 4-5.
    web: { row: dot | kebab | snake | camel | pascal | flat | screaming-snake, prefix: [string, optional], scope_depth: [integer, number of leading canonical words this platform's pipeline consistently omits — 0 if none] }
    ios: { row: dot | kebab | snake | camel | pascal | flat | screaming-snake, prefix: [string, optional], scope_depth: [integer] }
    android: { row: dot | kebab | snake | camel | pascal | flat | screaming-snake, prefix: [string, optional], scope_depth: [integer] }

platforms:
  ios:
    framework: swiftui | uikit
  android:
    framework: compose | view-system
  macos:
    framework: swiftui | appkit
  windows:
    framework: winui-xaml | other
  linux:
    toolkit: gtk | qt

naming:
  file_casing: PascalCase | kebab-case
  prop_casing: camelCase | kebab-case | snake_case

rtl_supported: true | false

contracts:  # grouped, because `archetypes` belongs beside `path`. Was `contracts_directory` at the root — two shapes for one fact, and scripts/resolve.py reads this one.
  path: [where component contracts live, relative to the directory holding .claude/ — optional, set once detected so future runs don't re-scan]
  policy: [this design system's own policy file, relative to the directory holding .claude/ — ONE per design system, so its location is recorded here rather than restated by every contract. A contract's `policy:` frontmatter overrides it for that contract only.]
  archetypes: [this design system's own role-archetype directory, optional — searched before the library shipped in system/role-archetypes/]
```

### What this skill does and does not do with tokens

This skill does not generate tokens, transform names, or replace Style Dictionary or any equivalent pipeline. Its whole involvement with tokens is two things: **state** the token's canonical identity in the contract, and **validate** that a real generated variable (a CSS custom property, a Swift constant, an Android resource) corresponds to it.

This is the same principle as "Native platform technology as the stated level" below Phase 2, applied to a second domain. There, the contract states native-level intent, verification checks the rendered outcome, and whatever framework produced that outcome sits in between and is never the thing being checked. Here, the contract states the canonical token, validation checks the generated variable, and the pipeline that produced it sits in between and is never checked. That's also why `generated_downstream` gates the check rather than being a preference: no pipeline means no generated variable, so the check has no subject at all — not a lesser check to fall back on.

**What is actually being validated: the style *logic*, end to end — not the value, and not the pixel.** The chain runs intent → the contract's stated canonical token → the variable a real implementation references. This skill checks that every link in that chain names the **same canonical token**. Three separate things live at or past the end of that chain, and none of them are in scope:

| | In scope | Owned by |
|---|---|---|
| The implementation references the token the contract stated | **Yes** — this is the whole check | this skill |
| The token's alias resolves to the intended *value* (`…bg.surface` → the right grey) | No | the design system's own tree; the pipeline generating from it |
| The rendered result looks correct | No | visual regression testing |

A correctly-referenced token pointing at a value someone later decides was wrong is **not** a finding here — the reference logic is sound, and the value is a design decision recorded elsewhere. Likewise, a component that looks right while referencing a token the contract never stated *is* a finding, even though nothing is visibly broken.

**Why this carries more weight than it looks like it should.** Three of the four concerns are grounded in an external standard — Structure in HTML/HIG/Material, Behavior in each platform's event model, Accessibility in ARIA/UIA/AT-SPI. Those are checkable knowing nothing whatsoever about a particular design system. **Appearance is the one concern with no external standard behind it.** There is no specification anywhere that says what this system's surface color should be; the token tree *is* the standard, which is exactly why the Conflict resolution policy carves tokens out as its single deliberate exception. Everything under Appearance — chapter 4.1's token slots, chapter 4.2's state treatments, chapter 4.3's dimensional variants — is expressed as a reference into that tree, so the reference chain is the only part of Appearance that anything in this skill can hold to account. That makes `naming-pattern` the schema for the one concern with nothing else to fall back on: a broken link in that chain is invisible to every other check here, and — since it may still render something plausible — invisible to visual regression too.

### Three naming facts — `naming-pattern`, naming convention, canonical path

Three distinct facts are easy to collapse into one phrase like "the naming convention." They are established at different times, by different means, and are used by different phases.

| Term | Example | Scope | Established by | Used by |
|---|---|---|---|---|
| **Canonical path** | `ds.semantic.color.bg.surface` | one per token | the token tree itself, read in Phase 2 | Phase 2, to record every Token Map entry in one syntax-neutral form |
| **`naming-pattern`** | `component.{component}.variant.{variant}.{property}` | one template per path **shape**, per tier — recorded as `tokens.patterns` | Phase 0B — proposed by `scripts/detect_tokens.py` from the tree's own shapes, then confirmed | Phase 2, as the shape every token name is recorded in; `scripts/resolve.py`, to read the tree at all; Phase 6, to report a structural mismatch as the slot that moved |
| **Naming convention** | `kebab` + prefix `--` + depth `1` → `--semantic-color-bg-surface` | one per **platform** | Phase 6 — detected empirically from a known-correct generated name, then locked (`references/token-naming-validation.md`, Steps 4–5) | Phase 6's token-name validation only |

**A naming convention is a bucket of three independent axes, not one value** — separator/case row, the platform's own added prefix, and scope depth (how many leading canonical words that platform's pipeline drops). They vary independently: kebab stays kebab whether or not a `ds` prefix is present, and either can hold while the truncation depth differs. Step 4's lock records all three because all three must hold, not because they're one fact.

**One design system can need several `naming-pattern` templates, which is why the field is a list.** It was a single ordered slot list until a real tree disproved that: the eval fixture's component tier holds three shapes at once, and `component.button.radius` cannot be parsed by the same template as `component.button.variant.primary.background`. The templates are tried in order, so the most specific comes first.

**`naming-pattern` is written hyphenated, always**, to keep it distinct from this skill's many other uses of "pattern" — WAI-ARIA patterns, the Tabs pattern, Q6's pattern references. A "pattern" unqualified in this skill is never about token names.

**`namespace` is not a synonym for canonical path.** It keeps its established meaning from `references/token-naming-validation.md`: the *leading* segments a platform's pipeline scopes away, as in the `Namespace scoping detected` finding. A namespace is a prefix concept, never the whole path.

**`tokens.format` is not a naming fact at all** — it's the token *file's* shape (DTCG, Style Dictionary, CSS custom properties, Tailwind), which is what `references/design-tokens-format.md` teaches you to recognize. It says nothing about how a name is spelled; `format: css-custom-properties` does not imply the canonical path is kebab-cased with a `--` prefix. Don't reach for it when you need a naming fact.

None of the three is a Phase 1 question, so never attribute any of them to a question number. When a contract needs to say where a canonical form came from, name the actual source: the context file, the token tree it was read from, or a form the designer volunteered.

### 0C: Where this design system's own files live

Two kinds of file are in play, and only one of them is pullable.

| Ships with the skill — identical for everyone | The design system's own — in **their** repo |
|---|---|
| `SKILL.md`, `references/`, `scripts/` | the token tree |
| `system/vocabulary/`, `system/role-archetypes/` | `.claude/design-system-context.yml` (facts) |
| `system/templates/` — blanks, never filled in place | the filled policy, and its bindings |
| | contracts and their bindings |
| | local role-archetypes, layered over the shipped library |

**Never write into the installed skill directory.** A policy written to the skill's own
`system/policy.md` is one team's decision shared with every other design system that pulls the
skill, and it is gone at the next update. The skill's `system/` and a design system's own
policy directory are different places that unfortunately read alike.

This step runs once. After it, every path is read from the context file instead of guessed or
re-asked — "which directory should this go in?" is a fact about the design system, not a
question to put to someone per component.

1. **Scaffold what the skill owns the shape of; discover what the design system owns.** No
   client's existing layout has an opinion about what a policy file looks like, so withholding
   it does not respect their repo — it just moves the failure later, into the resolver, as a
   path error. Their token tree, their existing contracts and their directory conventions are
   the opposite: locate those, never relocate them.
2. **Discover first**, as 0B does for tokens: a directory already holding files with this
   skill's frontmatter shape (`contracts.path`), a filled policy (`contracts.policy`), a local
   archetype directory (`contracts.archetypes`). Found and unambiguous means no question.
3. **Two plausible candidates is a question, never a pick.**
4. **Create only what is missing, and only with a yes.** The context file writes itself — it is
   tool state and it announces its path. A policy is a document the team owns, so it is created
   from `system/templates/policy.template.md` on confirmation, **with every row still blank**. An undecided row is not a requirement — it binds nothing and fails nothing — so a freshly scaffolded policy never breaks a contract. Each row is asked the first time a component engages it (Phase 6), which is how the policy fills in component by component. A
   filled row must come from a decision; an unfilled one is the visible gap the design depends
   on. Never overwrite an existing file: a scaffold is create-if-absent.
5. **Creating means a few files in a directory they name** — never `git init`, never moving or
   restructuring anything that already exists.
6. **Record every path in the context file**, then confirm what was created and where.

Like 0A and 0B, this must never block: an unanswered layout question means proceeding without
that path recorded, not stopping.


---

## Conflict resolution policy

**Intent — an interview answer, plus general references — is always authoritative. A provided existing implementation is something to test against that intent, not a second source of truth to reconcile it with.** This follows from how a contract actually gets built: Phase 1's interview plus Phase 3/4's derivation from `references/` are already sufficient to construct a complete, correct contract on their own, for everything except token bindings (chapter 4.1 Token slots) — no existing implementation needs to be read to get structure, props, behavior, or accessibility right; that's what the interview and the general references are for. So when an implementation is *also* provided, its role is to be checked against a contract that's already fully constructible without it — not to supply competing facts that need arbitrating case by case.

The one deliberate exception is design tokens: a token's literal binding is a genuinely arbitrary, system-specific fact that no amount of best-practice knowledge or stated intent can derive on its own — that's exactly why Phase 2 treats a coded or Figma source as a legitimate *information* source for tokens specifically, not just something to verify. Everything below assumes a non-token fact.

Use this callout format wherever a mismatch is documented in a contract, so it never gets silently absorbed either direction:

> ⚠ **Discrepancy:** [what the provided implementation does] vs. [what this contract states] — [why: general-reference precedence / doesn't match stated intent / no source covers this].

**1. Provided implementation vs. general reference (ARIA/WCAG/HTML/CSS/native platform files) — a compliance question, not a negotiation.** The general reference wins on what the contract *states*, unconditionally — never mirror a non-compliant pattern just because it's what currently exists. State the compliant answer, then flag the divergence with the callout above, so the contract does the job the README claims for it: surfacing drift, not hiding it. *(Verified in principle by hand — a component reading `<div onClick>` where the Web decision table calls for `<button>` produces exactly this callout. Still inert in practice today, since it requires reading structure from an implementation and Phase 2 only extracts tokens — but per the framing above, what's actually needed to unblock this is a narrow verification check against already-known expected facts, not a general code-ingestion capability.)*

**2. Provided implementation vs. a direct interview answer, same fact.** The interview answer is authoritative — that's what stating intent is for. A mismatch is a finding *about the implementation* (stale, incomplete, or simply wrong), not an open question to re-litigate with the designer. State what the contract requires per the interview answer, then flag the implementation's divergence with the callout — don't stop mid-flow to ask "which one should I trust." *(Inert today for the same reason as case 1.)*

**3. Multiple platform implementations disagreeing with each other on something the contract treats as shared intent (chapter 3.1 Zones, the prop tables, etc.).** Don't let two implementations negotiate the truth between themselves. The shared intent was already established once, in the interview — check each platform's implementation against *that*, independently, not against each other. If a genuine, intentional per-platform difference turns up this way, that's a signal the fact isn't actually shared intent after all — move it to a platform-specific row, don't leave it looking like agreement.

**4. No source covers this case at all (an absence, not a conflict)** — e.g. the Android/Windows status-display gap found while building the eval set. Nothing to adjudicate. The only rule: never present an improvisation as if it were grounded in a reference. State plainly that no source covers it and that judgment was used, the way Toast's contract already does.

---

## Phase 1: Designer interview

Use the `AskUserQuestion` tool for each question. One question per call — wait for the answer before asking the next.

**Formatting rules — apply to every question without exception:**
- `header`: the contract section this question feeds, in short form — see each question below. Max 12 characters.
- `question`: plain text. Start with the question. End with the progress note: `(X questions left)` for questions 1–9; `(last question)` for question 10.
- No bold prefix. No step number in the question text.

**Option rules — apply to every question without exception:**
- **Never add a catch-all option of any kind.** The AskUserQuestion tool automatically appends an "Other" free-text field. Any manually added option whose purpose is to capture unlisted input creates a duplicate. The tool's built-in "Other" is the only allowed freeform input.
- Guide the built-in "Other" field by ending the question with a scoped prompt where useful — e.g., "If your system calls it something else, name it in the field below." / "If none fit, describe the behavior."
- Use `multiSelect: true` whenever more than one answer can be true at the same time. Never offer a combined option (e.g., "A + B") when multi-select is available.
- Use single-select only when exactly one answer can apply.
- **For questions where option names draw from system-internal language** (variant names, state names, etc.): include a note in the question that the user can rename any option by typing the correct name in the free-text field below the choices.

After each answer: one short acknowledgement sentence, then immediately ask the next question. No analysis or commentary between questions.

Conditional follow-ups do not count toward the 10-question total. Once all 10 main answers are collected, proceed to Phase 2.

**The interview goes from general to specific, in the same topic order as the contract itself:** scope, then overview, then structure, then properties, then appearance. There's no dedicated question for chapter 5 Behavior or chapter 6 Accessibility — both are derived, never asked, per the whole premise of this skill. The one exception is a single conditional follow-up attached to Q4 that feeds §5 directly — see there for why it can't be asked any earlier.

Platform (Q2) comes right after Name & Purpose even though it isn't itself contract content — it's scope, not a section, and it determines how many rows every later table needs. Action and Interaction (Q3–Q4) sit next to each other because they're jointly the only two inputs Phase 3 needs to derive structure — more fundamental to what the component *is* than how it's composed, so they come before Composition/Parts, not after.

---

**Q1 — Name & purpose**
header: "Intent"
question: "What's it called, and what problem does it solve? One sentence is enough. (9 questions left)"
Open text.

**Q2 — Platform**
header: "Platform"
question: "Which platform(s) will this be used on? Select all that apply. (8 questions left)"
Multi-select:
- "Web"
- "iOS"
- "Android"
- "macOS"

This answer drives which reference file(s) Phase 3/4 consult, how many platform rows appear in the contract's per-platform tables, and how many per-platform schema files Phase 6 writes. It's scope, not chapter 5 Behavior content — no follow-up here asks about behavior differences yet; that's Q4's job, once there's an actual interaction to ask "does this differ" about.

**Q3 — Action** *(drives semantic markup derivation in Phase 3, alongside Q4)*
header: "Intent"
question: "What does it do? Pick all that apply. (7 questions left)"
Multi-select:
- "Shows information — no user action needed"
- "Takes the user to a URL"
- "Switches between content panels"
- "Triggers an action (submit, save, delete…)"
- "Opens or closes something (overlay, drawer, section)"
- "Toggles a setting on or off"
- "Collects input from the user"

If both "Takes the user to a URL" and "Switches between content panels" are selected → multi-select follow-up:
header: "Intent"
question: "Which routing modes does it support?"
  - "Swaps content in place — no URL change"
  - "Each panel has its own URL"

If "Opens or closes something (overlay, drawer, section)" is selected → multi-select follow-up:
header: "Structure"
question: "How can it be dismissed? Select all that apply."
  - "A dedicated close/dismiss control (e.g. an X in a header)"
  - "One of its own action buttons also dismisses it (e.g. Cancel, Done)"
  - "Clicking or tapping outside it"
  - "A platform-standard gesture or key (Escape, swipe-down, back gesture)"
  - "Automatically, after a delay"

  Don't infer this from the component's name or assume a header close control exists "because that's how it usually works" — a real design might rely on a footer action alone, or on the backdrop/gesture only, with no dedicated control at all. The zone only belongs in chapter 3.1 Zones if this answer actually names it. If one of Q2's selected platforms has a documented dismissal convention for this archetype (a platform convention file, per Reference files above), cite it in this question per "Citing a platform convention" below Q10 — as something to confirm or override, never a default.

  If "One of its own action buttons also dismisses it" → open text follow-up:
  header: "Behavior"
  question: "Which action(s) also dismiss it, and does dismissal happen in addition to that action's own effect or instead of it? If the zone holding it can hold more than one action (check its cardinality in Q6), also say how the dismissing one is told apart from its siblings — a fixed label like 'Cancel', a fixed position, or a flag/prop your system provides — not just that 'a footer action' dismisses, since that alone doesn't say which."

  Whether this becomes a real interception fact (contrast Phase 5's delegation principle, which defaults to pass-through) depends entirely on that distinguishing mechanism: if the design system gives the parent an actual way to recognize the dismissing child (a prop it reads, a dedicated position), document that mechanism in chapter 5.1 Requirements as genuine interception. If the answer only identifies the action by label with nothing the parent itself could check — the far more common case — the truth is that dismissal happens because the *consumer* wired that specific button's own callback to also call the close handler, not because the parent recognized or reacted to anything. State it that way in chapter 5.1 Requirements: pass-through stays the documented behavior, with a note that this pattern is commonly wired by the consumer rather than intercepted by the parent. Don't invent a detection mechanism that was never confirmed just to make the interception read as more official than it is.

**Q4 — Interaction** *(drives semantic markup derivation in Phase 3, alongside Q3 — together with Q3's dismissal follow-up above, these are the only places this interview feeds §5 Behavior directly)*
header: "Structure"
question: "How does the user interact with it? Pick all that apply. (6 questions left)"
Multi-select:
- "Click or tap"
- "Choose from a list or set of options"
- "Drag to reorder or resize"
- "Scroll or swipe"
- "No direct interaction — it updates on its own"

If "Choose from a list" → single-select follow-up:
header: "Structure"
question: "How many options can be selected at once?"
  - "Just one"
  - "Multiple"
Then single-select follow-up:
header: "Structure"
question: "Is the list always visible, or does it open on demand?"
  - "Always visible"
  - "Opens as a dropdown"

If "No direct interaction — it updates on its own" AND the component is transient rather than a persistent piece of layout (a Toast/Snackbar/notification-banner shape, not a Badge) → single-select follow-up:
header: "Behavior"
question: "If this is triggered again while one is already showing, what happens?"
  - "The new one replaces the current one immediately"
  - "It queues behind the current one and shows after"
  - "Multiple show at once (stacked)"
  - "Not applicable — this isn't a repeating/transient surface"

Cite a platform convention here (per "Citing a platform convention" below Q10) when one of Q2's selected platforms has a documented answer — Android's Snackbar queuing is the clearest current example — but ask this regardless of platform, since it's a real design decision either way, documented convention or not.

If Q2 selected two or more platforms → open text follow-up:
header: "Behavior"
question: "Does anything about this interaction work differently across those platforms — behavior or gestures specifically, not structure or accessibility (those are derived automatically per platform)? Only describe what changes; leave blank if nothing does."

Never assume the HTML element or ARIA role from the component name. Always derive from Q3 (action) and Q4 (interaction).

**Q5 — Composition**
header: "Composition"
question: "Does it stand alone, or does it hold other components inside? (5 questions left)"
Single-select:
- "Stands alone"
- "Holds other components inside"
If "Holds other components" → open text follow-up:
header: "Composition"
question: "Which components does it hold? Do any of them already have contracts?"

**Q6 — Parts**
header: "Composition"
question: "What are its visible parts? Name each one and say what it's for — showing content, or doing something. (4 questions left)"
Open text. Add in the description: Examples of content parts: label, image, badge, description. Examples of action parts: close button, chevron, checkbox, spinner.

If the answer names an action part not already covered by Q5's composition list → open text follow-up:
header: "Composition"
question: "Should any of these parts be built to match an existing component's pattern — same interaction and accessibility conventions — without embedding it as an actual instance the way Q5's composition works? Name the part and which component's pattern it should follow, or leave blank if none apply."

This is deliberately distinct from Q5: Q5 asks whether a zone *is* another component (composition — the child's own contract fully governs its structure, appearance, behavior, and accessibility). This asks whether a zone should merely *look and behave like* one, while still being specified locally in this contract — see Phase 5's pattern-reference principle for how the two render differently in the output.

**Q7 — Visual styles**
header: "Appearance"
question: "Which visual styles does it have? Check the ones your system uses. If your system calls them something different, type the correct name in the field below. (3 questions left)"

Before calling AskUserQuestion for Q7, derive 3–6 likely visual style variants from the component name and purpose given in Q1. Use them as the multi-select options. The list should reflect common conventions for that component type. Examples:
- Button-type → Filled / Outlined / Ghost / Text / Destructive
- Navigation-type → Underline / Fill / Pill / Bordered
- Badge / Tag / Chip → Filled / Subtle / Outline / Dot
- Input / Field → Default / Floating label / Inline / Borderless
- Alert / Banner / Toast → Filled / Subtle / Left-bordered / Outline
- Card → Default / Elevated / Outlined / Ghost
- List item / Row → Default / Compact / Highlighted / Disabled

Unchecked options are not part of this component's contract. The built-in free-text field handles any style not on the list, or renames one that is.
Multi-select: [derived from Q1]

**Q8 — Layout flexibility**
header: "Structure"
question: "Can its layout change? Pick all that apply. (2 questions left)"
Multi-select:
- "Direction flips (horizontal ↔ vertical)"
- "Size grows or shrinks"
- "Alignment shifts (left / centre / right)"
- "Has a compact or overflow mode"
- "Adapts to the space available"
If "Adapts to the space available" → open text follow-up:
header: "Structure"
question: "What changes when space is tight? What does your design system call those conditions?"

The first four options feed chapter 2.3 Layout props; "Adapts to the space available" and its follow-up feed chapter 2.2 Adaptive layout instead. Both land under the Structure concern either way, even though it's asked here, in the same breath as the rest of this question, since "can its layout change" is one natural conversation for the person answering it.

**Q9 — States & tokens**
header: "Appearance"
question: "Which extra states does it have? If your system names them differently, type the correct name in the field below. (1 question left)"

These are states **beyond** the interaction states its role already makes valid — a button's hover, keyboard focus, pressed and disabled are never optional, and are answered in chapter 4.2 whatever is picked here. An answer that is an interaction state (Selected) goes into the contract's `interaction-states:`; the others (Loading, Error, Empty) are component states, carried by props.
Multi-select:
- "Loading"
- "Error"
- "Disabled"
- "Selected / active"
- "Empty"

After answer → single-select follow-up:
header: "Appearance"
question: "Do you have design tokens for this component?"
  - "Yes — I have a Figma link"
  - "Yes — I have a Storybook or code link"
  - "No — skip for now"
  If yes → open text follow-up:
  header: "Appearance"
  question: "Share the link or file."

**Q10 — Output**
header: "Output"
question: "Want a JSON schema file alongside the contract? (last question)"
Single-select:
- "No thanks"
- "Yes — generate a .schema.json"
If yes and the component holds sub-components → single-select follow-up:
header: "Output"
question: "How should sub-components appear in the schema?"
  - "By reference ($ref)"
  - "Written out inline"

Wait for all answers before proceeding to Phase 2.

### Citing a platform convention

The platform convention files (Reference files, above) exist to make a question sharper when a relevant fact is already documented for one of Q2's selected platforms — never to fill in an answer on the designer's behalf. When composing a question or follow-up that a convention file speaks to (Q3's dismissal follow-up and Q4's repeat-trigger follow-up are the two currently wired this way), append the convention as something to confirm or override, in the same shape as any other option's framing — e.g., for a Toast/Snackbar-shaped component targeting Android, Q4's follow-up becomes "...Material's own Snackbar convention queues a new one behind the current one rather than showing both at once or replacing it immediately — does this match, or should it behave differently?" The answer that comes back is what goes in the contract, cited to the interview the normal way; the convention itself never appears in a contract unless an answer confirmed it. If nothing in the relevant platform's convention file bears on the question being asked, say nothing — don't manufacture a citation to seem thorough.

---

## Phase 2: Token extraction

### Path A: Figma URL

Inspect only the root element of the component — not its children (those have their own contracts). Check properties in this order: Auto layout gap → padding (all sides) → corner radius → fill (background) → stroke (color, width, position) → opacity → any fixed width or height.

Prefer structured extraction (Figma MCP / API access to variable bindings) over manually reading tooltips when it's available in the current environment. See `references/figma-variables-model.md` for the full data model (collections, modes, aliasing), the preferred structured method, and the manual-inspection fallback with its exact navigation steps.

Never infer or invent token names. An unbound property ("Apply variable" in the manual method, no binding returned in the structured method) means: record the raw value only.

---

### Path B: Coded reference (Storybook, CSS, tokens file)

- **Storybook**: Navigate to the story URL. Open the Docs tab or Controls panel. Look for token references in the story source or component styles.
- **CSS / SCSS / token file**: Read the file and extract the bound tokens.

Token files take different shapes across design systems — DTCG JSON (`$value`/`$type`), Style Dictionary (`value`/`type`), CSS custom properties, or a Tailwind theme config. See `references/design-tokens-format.md` to recognize whichever shape the source actually uses, including how tiering (primitive/semantic/component) and aliasing show up in each format — don't assume CSS custom properties are the only possibility.

For every property: record `property | token name | resolved value (if visible)`. Hardcoded values with no token reference = raw. Note the source in the token map.

Record the token by its canonical, syntax-neutral name — not the source file's platform-specific spelling. A CSS custom property's leading `--` and kebab-case, a Swift constant's camelCase, an Android XML resource's `snake_case` — these are that platform's rendering of the token, not the token's identity. If a canonical form is established — `tokens.prefix` and `tokens.patterns` in `.claude/design-system-context.yml` (Phase 0B), the shape of the token tree actually read in Path B, or a form the designer volunteered unprompted — strip the source's wrapping syntax down to that form (`--color-overlay-backdrop` → `color-overlay-backdrop` under a `color-` prefix convention). This is never a question the interview asks; if nothing establishes it, say so in the token map rather than silently adopting whichever platform happened to supply the source file as the default spelling for every platform. Don't reach for `tokens.format` here — it's the file's shape, not a naming fact — and don't confuse any of this with `tokens.naming_convention`, which is per-platform rendering. See "Three naming facts" under Phase 0B.

If a token's resolved value here contradicts the design-system context file (Phase 0B) — e.g. a different naming prefix than what's on record — never resolve it silently. Surface it with the Conflict resolution policy's callout format, and update the persisted context file if the token source turns out to be current truth. This doesn't map onto that policy's numbered cases — tokens are its deliberate exception, where both the coded reference and the persisted context are legitimate *information* sources on equal footing, not an implementation being tested against already-sufficient intent.

---

### Path C: Description only

Leave the token map as pending and note it clearly in the contract:

> Token map pending — no design source was provided. Supply a Figma node URL, Storybook story URL, or CSS/token file to complete this section.

---

### Native platform technology as the stated level — frameworks are never the thing being checked

A contract states intent, always at native-technology grounding — a real `<dialog aria-modal="true">` in the DOM, a real `.isModal`-equivalent trait in the iOS accessibility tree. Verification checks outcome — the actual rendered/runtime result — against that same native-level intent. Whatever produced the outcome sits entirely in between, and the contract has no opinion on it: React, Vue, React Native, Flutter, vanilla JS, hand-written Swift — any of them are equally valid *as long as the outcome satisfies the intent*. A React web component that dispatches a real, bubbling `dismiss` `CustomEvent` on real DOM output is exactly as compliant as vanilla JS producing that same event; a React Native view on iOS is exactly as compliant as SwiftUI if it produces the real underlying UIKit-level trait and focus behavior the contract asked for. This isn't a tolerance or an exception — it's the whole reason manifestation facts are written in native-technology terms to begin with: that's the one description a claim can be checked against regardless of which framework sits in the middle.

Concretely, this is why Phase 0B's config records a `framework`/`toolkit` choice for iOS/macOS/Android/Windows/Linux (Swift with SwiftUI or UIKit, Kotlin with Compose or the View system, GTK or Qt, and so on) — each of those genuinely changes what a *native* implementation looks like, so Phase 3 needs to know which native vocabulary to name (`Button` in SwiftUI vs. `UIButton` in UIKit). It's also why Web has no such key: there's no native-level choice to record, since the platform technology is just the DOM/HTML/CSS/JS, and no third-party library (React, Vue, or anything else) ever changes what the *native* outcome should be — see `references/web/dom-events-model.md`'s framework-agnostic `CustomEvent` grounding, which already had this right.

The same logic applies to any implementation or verification work built *from* a contract: don't restrict what tooling an implementer (or a blind-test agent) uses — restrict what gets checked. Verify against the real, rendered native-level output (actual DOM, actual accessibility tree, actual focus behavior), never against whether a particular framework's idiomatic convention was also present. A framework layering an extra convenience on top (a React `onDismiss` prop wrapping a real DOM event, say) is neither required nor forbidden by the contract — it's outside what the contract measures either way.

---

## Phase 3: Derive structure (internal — not asked)

Two different things happen in this phase, at different frequencies — don't run everything per platform by default.

### Deriving the role-archetype (runs once, not per platform)

The contract's `role-archetype:` is **derived here from Q3 and Q4**, never asked. It is the same input the structure tables below consume, resolved one level higher: not *which control is this on each platform*, but *what is this, on every platform*.

**The criterion is a single question:** does the platform's accessibility layer **convey a distinct role** for this thing? Not "does it feel like its own kind of component" — a Card feels like one and conveys nothing. Convey, not report: Compose has no `Role.Dialog`, yet Android announces a dialog through its pane title, so a field-based reading would wrongly conclude dialog is not a role.

1. **Look for an existing archetype** in the design system's own directory (`contracts.archetypes`) first, then in `system/role-archetypes/`. Match on what the component *is*, not its name — a `SubmitButton`, a `DangerButton` and an `IconButton` all resolve to `button`. One archetype serves many contracts; that fan-out is the point.
2. **If the criterion says no**, write `role-archetype: none`. That is a real answer, not a missing one — a Card, a Stack, a Divider convey no role, so nothing is inherited and every requirement is stated locally. Spell it out so a reader can tell a decision from an omission.
3. **If the criterion says yes but no archetype exists**, say so to the user before writing the contract, and offer both paths: add the archetype to the design system's own directory (it is then inherited by every future component with that role), or proceed with `none` and state the requirements locally this once. Never silently pick `none` for something that conveys a role — that is how a role's guarantees get re-derived, slightly differently, per component.

**A composite shell takes the archetype of what the shell itself is**, not of anything it contains: a Modal whose footer holds buttons is not a `button`.


****Structure resolution runs once per platform selected in Q2.**** The same Q3 (action) and Q4 (interaction) answers feed every run — what changes is which table resolves them to a concrete structure. Never infer the element/control from the component's name — the same visual form can require completely different structure depending on what the component actually does, and that holds on every platform.

- **Web** → use the decision table below.
- **iOS / Android / macOS** → use the "Component / structure resolution" table in that platform's reference file instead of the table below (`references/ios/ios-hig-accessibility.md`, `references/android/android-material-accessibility.md`, `references/macos/macos-hig-accessibility.md`, `references/windows/windows-ui-automation.md`, `references/linux/linux-atspi-accessibility.md`). Same Q3/Q4 inputs, that platform's native vocabulary as output.

Each platform's result becomes one row in the role-archetype's native backing table (see Phase 5) — never a separate document, and never merged with another platform's row even when the two values happen to match.

****Chapter 3 Composition (Setting cardinality, Setting order below) runs once, not per platform.**** Cardinality and position are statements of intent — "the Close button is optional and sits top-right" doesn't change because the implementation platform changed. **chapter 2.2 Adaptive layout** is the same: the named conditions and what changes under each are shared intent, even though the underlying mechanism differs per platform (see Phase 5 for how to record that without a full Platform column).

### Decision table (Web)

Use the combination of Q3 (action) and Q4 (interaction) to pick the right element.

**Action: Shows information only**
| Context | Element |
|---|---|
| Section or region of the page | `<section aria-labelledby="...">`, `<aside>`, `<article>`, or `<main>` |
| List of items | `<ul>` + `<li>` or `<ol>` + `<li>` |
| Figure, image, or diagram | `<figure>` + optional `<figcaption>` |
| Status info that updates on its own | `<div role="status">` or `<div aria-live="polite">` |
| Purely decorative | `<div aria-hidden="true">` |

**Action: Takes the user to a URL** (any interaction)
→ `<a href="...">` — always. Never a `<button>` or `<div>`.

**Action: Switches between content panels**
| Routing mode | Elements |
|---|---|
| In-place only (no URL change) | `role="tablist"` container, `role="tab"` triggers (`<button>`), `role="tabpanel"` panels |
| URL-based only | `<nav>` containing `<a href>` links — no tablist role |
| Both modes supported | Document both patterns in chapter 2 Structure. State the condition for each. URL routing takes semantic precedence; `<nav>` + `<a>` + `aria-current` for routed mode, tablist pattern for in-place mode. |

**Action: Triggers an action + Interaction: Click or tap**
| Action detail | Element |
|---|---|
| Submit data | `<button type="submit">` inside `<form>` |
| Open/close overlay | `<button>` that controls `<dialog aria-modal="true">` |
| Expand/collapse content | `<button aria-expanded="true/false">` |
| Toggle a setting | `<button aria-pressed="true/false">` |
| Generic (delete, add, save…) | `<button type="button">` |
Never use `<div>` or `<span>` for triggered actions.

**Action: Collects input + Interaction: Choose from a list**
| Selection | Visibility | Element |
|---|---|---|
| Just one | Always visible | `<fieldset>` + `<legend>` + `<input type="radio">` items |
| Just one | Opens as dropdown | `<select>` (native) or `role="listbox"` + `role="option"` (custom) |
| Multiple | Always visible | `<fieldset>` + `<legend>` + `<input type="checkbox">` items |
| Multiple | Opens as dropdown | Custom listbox with `aria-multiselectable="true"` |

**Interaction: Scroll or swipe**
→ Scroll container: `<div>` with `overflow: auto` and `tabindex="0"`. If items are individually navigable: `role="list"` + `role="listitem"` or arrow-key managed composite widget.

**Interaction: Drag to reorder or resize**
→ `role="list"` + `role="listitem"` with pointer-event drag and keyboard fallback (Space to grab, Arrow to move, Space or Enter to drop, Escape to cancel).

**Composite shell**
→ The root element applies to the shell only. Document sub-component markup in their own contracts — but the shell's *own* zones (chapter 3.1 Zones rows not delegated to a sub-component, e.g. a Close button or a Title) aren't sub-components and have no contract to defer to. Resolve each one against this same decision table (or the platform's own resolution table) using its own action/interaction, and give it its own block in chapter 2 Structure alongside the root. A zone that's plain inline content with no independent semantic identity (label text, a decorative wrapper) doesn't need a block of its own — only zones that are themselves interactive, or that carry accessibility weight (a control, a heading targeted by `aria-labelledby`, a live region), do.

**A heading zone's Tag/Control is its role, never a specific level.** When an owned zone is a heading (a Title targeted by `aria-labelledby`), name the element as "a heading element" and stop there — never `<h2>`, `<h3>`, or any specific level. Per `references/web/html-semantics.md`, heading level is chosen by the document's outline at the point the component is mounted, not by the component itself; no interview answer could ever resolve this correctly either, since the right level depends on a page this contract doesn't know about. State the row as `Required: Yes`, `Tag/Control: A heading element (<h1>–<h6>) — level set by the consuming page's document outline, not fixed here`. This isn't a gap to flag for confirmation (chapter 4.3's pending-value convention) — it's genuinely out of the contract's scope, and saying so explicitly is the correct, complete answer, not an incomplete one.

This only applies to zones the root's own resolution says nothing about. Some archetypes resolve to a compound pattern that already names its constituent zones' elements as part of the single root entry — a radio group's `<fieldset>` + `<legend>` + `<input type="radio">` items, or a tablist's `role="tab"` / `role="tabpanel"` pair. When a zone's element is already stated there, it doesn't get a second, separate block — that would just restate the same fact under a different heading. Owned-zone blocks exist for zones bolted onto an otherwise single-element root that the root's own resolution never mentions (a `<dialog>` says nothing about its Title or Close button), not for zones a compound pattern already accounts for.

**When multiple actions apply**, the primary action defines the root element. Inner zones follow their own rules per the table above. The primary action is what the component fundamentally *is* to the user.

**When multiple valid root elements exist**, document all options and the condition for choosing each.

### Setting cardinality (for chapter 3.1 Zones)

Use the user's answers from Q6 to fill the Cardinality column. When the user hasn't specified a maximum, use judgment:
- A label, title, or primary description → `1`
- A leading or trailing icon → `0–1`
- Action buttons in a footer → `1–3` or `0–3`
- Tags, chips, or list items → `0+` or `1+`
- Navigation steps or tabs → state the minimum (e.g., `2+` for tabs)

If not derivable from the component's purpose, note as `1+` and flag for confirmation.

**One zone per genuinely different role — don't collapse distinct roles into one "N buttons" zone just because they're all delegated to the same child component type.** Whether an action-holding zone is one row or several depends on what Q6 actually said, not on the child type: "Footer with 1–3 action buttons" (Modal's case) is genuinely one undifferentiated slot — the consumer supplies an arbitrary number of app-defined actions, none of which the contract can say anything specific about. "A footer with Cancel and Save" is different — two named, distinct roles were given, each with its own fixed identity and (per the Q3 dismissal follow-up, if applicable) possibly different behavior. Model that as two separate chapter 3.1 Zones rows (`Cancel action`, cardinality `1`; `Save action`, cardinality `1`), not one row reading "Footer: 2 Button components." Collapsing them forces every later section to bolt on an awkward disambiguation note to say which of the "2 buttons" does what; naming them separately means chapter 5.1 Requirements can just say what each one does, the same way any other zone's row already does.

### Setting order (for chapter 3.1 Zones)

Mark a zone as `Fixed` when moving it would break the user's expectation or when its position is load-bearing for meaning or accessibility:
- Close / dismiss buttons → `Fixed — top-right`
- State indicators (expand chevron, selection checkbox) → `Fixed — precedes label` or `Fixed — follows label`
- Navigation controls (prev/next arrows) → `Fixed — flanks content`
- Primary action in a footer → `Fixed — rightmost action`

Mark a zone as `Flexible` when its position is a layout preference — e.g., a thumbnail that could appear above or beside text depending on the layout variant.

When the target design system supports RTL locales, record `Fixed` positions in logical terms (leading/trailing, start/end, inline-start/inline-end — whichever vocabulary the current platform uses) rather than physical ones (`left`/`right`), since a directionality flag alone does not flip physically-positioned layout on any of the platforms covered here except where the platform's own logical-property system does the work. See `references/platform-differences.md` for how each platform expresses this, then the specific platform file for the mechanism (`references/web/css-layout-and-interaction.md` for Web). If the system is confirmed LTR-only, physical terms are fine.

### Presence toggle for a fixed-content zone (for chapter 5.3 Behavioral props)

A zone with `Cardinality` starting at `0` is normally optional "for free" — nothing needs deriving beyond the zone itself, because whether it appears is just whether the consumer supplied content for it (an icon element, footer children). That mechanism only works when the zone's *content genuinely varies per instance* — the consumer is authoring something different each time.

It breaks down for a zone whose content is fixed by the design, not authored by the consumer — nothing ever varies between one instance of the zone and the next (a Close button is always the same icon, the same accessible name, the same behavior; only whether it's there at all changes). A fixed-content zone can't signal its own presence through "what was passed in," because nothing is ever passed in — so it needs an explicit boolean prop in chapter 5.3 Behavioral props, e.g. `showCloseButton`, derived alongside the zone the same way any other optional-but-not-content-driven fact would be. This holds regardless of whether the zone's markup happens to be bespoke or reuses another component's contract (by composition or by pattern reference, per Phase 5's principles above) — reuse changes what the zone *looks like*, not how its presence gets toggled. When in doubt, ask: if this zone were removed, would the consumer be able to say why by pointing at something they didn't pass in? If yes, presence is content-driven, no prop needed. If no — there was never anything to pass — derive the boolean.

---

## Phase 4: Derive accessibility (internal — not asked)

Derive from the interview answers and each platform's Phase 3 structure decision. Do not ask the designer about ARIA, UI Automation patterns, AT-SPI roles, or keyboard/gesture navigation directly.

**chapter 6 Accessibility & Attributes runs once per platform selected in Q2** — every platform has its own vocabulary, so this always gets a row per platform, same frequency as chapter 2 Structure:
- **Web** → the ARIA-specific subsections below.
- **iOS / Android / macOS** → that platform's reference file, "Accessibility API" section, for the role/state/trait model. There is no separate decision table to duplicate here — the platform files already state what each requires.

**keyboard and gesture navigation and screen-reader expectations are shared by default.** Derive once using the web subsections below for the common cases, and add a platform-specific note only where the actual key or gesture genuinely differs (e.g. `Escape` has no touch equivalent) — not as a matter of course.

**focus management is shared** — derive once, regardless of platform count.

For Web patterns not in Phase 3's decision table (combobox, menu, tooltip, tree, slider, grid, accordion), get the full attribute and keyboard set from `references/web/wai-aria-patterns.md` rather than approximating. `references/web/wcag-mapping.md` grounds a requirement in the WCAG success criterion it satisfies when that's useful context (e.g., for an audited system) — this is optional citation, derived silently, never a question put to the designer.

### Deriving ARIA roles and attributes

- Semantic HTML provides the base role implicitly — add explicit `role=` only when overriding or when the element alone is insufficient
- Named landmarks (`<section>`, `<nav>`, `<main>`, `<aside>`) require an accessible name: `aria-label` or `aria-labelledby`
- Interactive elements that change state need state attributes: `aria-pressed` (toggle), `aria-expanded` (disclosure), `aria-selected` (tabs/options), `aria-checked` (checkboxes), `aria-disabled` (disabled controls)
- When content updates asynchronously: add `aria-live="polite"` on the updating region
- Dialogs: `aria-modal="true"`, `aria-labelledby` pointing to the dialog's heading

### Deriving keyboard navigation

| Interaction type | Required keyboard behaviour |
|---|---|
| Display only | No keyboard interaction required |
| Link | `Enter` activates |
| Button | `Enter` and `Space` both activate |
| Text input | Standard text editing keys; `Tab` moves focus in/out |
| Single select / toggle | `Space` toggles; `Enter` confirms if in a form |
| Multi-select options | `ArrowUp` / `ArrowDown` to move, `Space` to select, `Enter` to confirm |
| Tab interface | `ArrowLeft` / `ArrowRight` between tabs; `Tab` moves into the panel |
| Swipeable / scrollable list | `Arrow` keys to navigate items |
| Modal / dialog | `Tab` / `Shift+Tab` cycle within; `Escape` closes |
| Drag / reorder | `Space` to grab, `Arrow` keys to move, `Space` or `Enter` to drop, `Escape` to cancel |

### Deriving focus management

- **No special management needed**: display-only components, buttons, links, inputs — focus follows natural DOM order
- **Focus trap required**: modal dialogs and overlays — focus cycles within; nothing outside is reachable while open
- **Focus move on open**: when a panel opens, move focus to the first interactive element inside it
- **Focus restore on close**: when a dialog or panel closes, return focus to the trigger

The visible focus indicator itself should bind to `:focus-visible`, not bare `:focus` — see `references/web/css-layout-and-interaction.md` for the distinction (keyboard-only indication vs. showing a ring on every mouse click).

### Deriving screen reader expectations

- **On first reach**: announce role, name, and current state
- **On activation**: announce the result
- **On async update**: the `aria-live` region announces changes without requiring focus to move
- **On state change**: announce the new state
- **Empty states**: must be inside any live region so they are announced when content updates to empty

---

## Phase 5: Generate the contract

Two files, always, in the component's own directory:

| File | Holds |
|---|---|
| `[ComponentName].md` | six chapters of requirement rows — platform-neutral, human-first |
| `[ComponentName].bindings.json` | per-platform `expect` values, only where they are not derivable |

The `.md` is **source**, not the reading artifact. Phase 6 generates the resolved view a person reads and the canonical documents a verifier consumes; both inherit the role-archetype's and the policy's requirements, which is why this file never restates them.

**Every concrete fact needs a traceable origin — before writing anything as a requirement, name which of these three it came from:**
1. **An external, cross-system standard** — something a `references/` file actually states, specifically enough to cover the exact detail being written, not just the general pattern it sits inside. Citing a reference for the archetype ("dialogs need an accessible name via a heading") doesn't license inventing a specific value the reference never gave ("so, `<h2>`") — that's overspecifying past what the citation actually supports.
2. **An explicit interview answer** (or a persisted `.claude/design-system-context.yml` fact) — the only legitimate source for anything that could reasonably differ between two design systems, or between two components' instances of "the same" thing.
3. **A structural inference from something already established by (1) or (2)** — conditional logic, not a new fact.

A detail that fits none of the three is an invented assumption, full stop — cut it. A fourth case looks like a gap and isn't: a detail resolved by neither the reference nor any possible interview answer, because it depends on where the component is used (a heading's level, chosen by the consuming page's outline). State the role precisely and say the concrete resolution is out of scope.

### Write nothing the component inherits

The contract holds what is **specific to this component**. Three other layers already hold the rest, and repeating them creates two places to be wrong:

| Already stated by | Example | Never restate |
|---|---|---|
| the role-archetype | a button is exposed as a button; both activation keys work | in chapter 6 |
| the policy | every focused control renders a focus indicator | anywhere |
| a delegated child's contract | what the Icon inside does | in any chapter |

If a requirement you are about to write is already true of every component with this role, it belongs in the archetype, not here. If it is true of every component in the design system, it is policy. Phase 6 will fail the parse if a local id collides with an inherited one.

### One statement, and where a platform difference goes

The earlier format asked you to sort every subsection into one of three "treatments" — shared, intent-plus-per-platform-manifestation, or shared-with-exceptions. **That classification is gone, and the reason is worth understanding: it existed because the contract was the only file.** Now a requirement is written once, in plain language, and the places a platform can differ are explicit:

| The difference is | Goes in |
|---|---|
| how the fact is *checked* on that platform — a different `expect` value, a different trigger, a different threshold | `[ComponentName].bindings.json` |
| a fact with no referent on that platform at all | that binding, as `binds: false` with a stated reason |
| a genuine difference in the *requirement itself* | a **Divergences** row, in the chapter whose fact it modifies, with a reason |

So a statement never names a tag, an ARIA attribute, a Compose `Role`, or a key. `The control is reachable by the platform's sequential focus navigation` is one requirement; that it is Tab on web and a swipe on iOS is a binding. **A statement that collapses into nonsense without naming one platform's vocabulary is written at the wrong level** — that check survives from the old format and is still the most useful one.

`binds: false` is not a way to opt out. It means the platform has no referent for the fact — there is no form model off the web — and it carries its reason into every canonical document, so a platform cannot lower its own bar by omission.

### The six chapters

| Chapter | Holds | Tables |
|---|---|---|
| 1 Intent | one or two sentences: what it is, what need it solves | prose only |
| 2 Structure | what the thing is and the space it occupies | 2.1 Requirements · 2.2 Adaptive layout · 2.3 Layout props · 2.4 Element |
| 3 Composition | what it contains, and on what terms | 3.1 Zones · 3.2 Arrangement · 3.3 Delegation |
| 4 Appearance | which properties are tokenised, in every state and variant | 4.1 Token slots · 4.2 Interaction states · 4.3 Visual variants · 4.4 Platform tokens |
| 5 Behavior | what it does, emits, receives, and how its state moves | 5.1 Requirements · 5.2 Events · 5.3 Behavioral props · 5.4 Machine |
| 6 Accessibility | semantic exposure — reviewable as an aspect in its own right | requirements |

**All six chapters are always present.** A chapter with nothing to say says so in one line (`*Inherited in full from `role-archetype: button`. Nothing component-specific.*`) — an absent chapter is indistinguishable from an overlooked one.

**Composition owns a zone's existence and terms; Accessibility owns its semantic exposure.** Composition says *a title zone exists, accepts text, cardinality 1, block start*. Accessibility says *the title is the accessible name source*. Nothing is stated twice.

### Requirement rows

```
| when | statement | observe | kind | id |
```

- **`when`** leads, so a statement never restates its own condition. `always`, or `when:<condition>` from the closed vocabulary in `system/vocabulary/conditions.json` — plus `when:<zone>_present` for any zone chapter 3 declares, and `when:following:<transition-id>` for an effect of a transition chapter 5.4 declares. Never invent a condition; the resolver lint-fails an unknown one.
- **`statement`** is one sentence of plain language, stating the requirement positively.
- **`observe`** is one of the twelve types in `system/vocabulary/observe.json` — it names *how the fact is obtained*, not what kind of fact it is. `needs` is derived from it, which is why bindings stay small.
- **`kind`** is `state` or `behavior`: is this true at rest, or only after something happens?
- **`id`** is last and carries an `id-` prefix, so the eye skips it — `id-STR-01`. Number per chapter: `STR`, `CMP`, `APP`, `BEH`, `ACC`, `MCH`. The prefix is stripped downstream.

### Element (2.4)

Which element carries the role, **one row per platform** — Phase 3's structure resolution, written down:

```
| platform | element | id |
| web | `<button>` | id-STR-02 |
| ios | SwiftUI `Button` | id-STR-03 |
```

This is the one table in the contract that names platform vocabulary, and it is allowed to because a platform is its first column: the archetype's statement (*exposed as a button*) stays neutral, and this is each platform's answer to it. It is checked, not only documented — each row becomes an `element` requirement in that platform's canonical document, observed on the element that carries the role (the native `<button>` inside a custom element's shadow root, say). Names go in backticks.

- A row per platform in the frontmatter, whenever the archetype is not `none` — a missing row fails the parse.
- The element must be one of the archetype's **Native backing** for that platform. A deliberate departure is written `custom — <what carries the role, and why>`; the archetype's requirements still bind, now with nothing provided free.
- Never a fixed heading level — a heading's element is chosen by the page's outline, so name the range, not a level.

### Token slots (4.1)

Declare **which properties are tokenised**, not which token fills them:

```
| when | property | token | scope | id |
| always | background | `component.button.{kind}` | component | id-APP-01 |
| always | radius | `component.control.radius` | shared:control | id-APP-02 |
| always | elevation | n/a — this component sits in the content plane | — | id-APP-03 |
```

**`scope` — how specific a token is to this component**, one of three, computed from the tree and checked on every resolve:

| scope | means | e.g. |
|---|---|---|
| `component` | named for this component alone | `button.secondary-hover` |
| `shared:<group>` | a component-tier pattern several components use | `control.radius` — button and segmented-control tab |
| `semantic` | a system-wide meaning, tied to no component | `primary`, `focus` |

The lookup goes in that order: this component's own tokens, then the shared groups it is a member of (`tokens.shared` in the context), then semantic. One row, one scope — a row whose variants resolve to different scopes is split by write-back. The resolved view counts them (*14 component · 3 shared · 6 semantic*), which says at a glance how much a component leans on general tokens.

**A token cell may be a pattern.** `{kind}` stands for each value of that visual-variant prop the row covers; every value it produces must exist in the tree, and a value it cannot produce needs its own row.

While writing, `—` means *resolve it from the tree* — Phase 6 does that against the design system's own naming, writes back what the tree answers,, and reports one of six outcomes per slot. Write an explicit token path only to pin one deliberately; **a pinned name that is not in the tree fails the parse**, which is how an invented token name is kept out of a design system. A property that does not apply says so with a reason; it is never simply left out.

**Colour is not the only thing tokenised.** The closed property set covers type (`font-family`, `font-size`, `font-weight`, `line-height`, `letter-spacing`), space (`padding-inline`, `padding-block`, `gap`), size (`height`, `radius`, `border-width`), depth (`elevation`, `opacity`) and motion (`duration`, `easing`) beside colour (`background`, `foreground`, `border-color`, `focus-ring`). A token only fills a property of its own `$type`, and dimensions expand along the `size` axis where colours expand along `variant`.

Declare a slot for every property in the design system's declared property set that this component actually has. Never invent a token name for a value you could not find — that rule is unchanged and now enforced.

**A slot covers every variant unless it says otherwise.** `when:hover | background | —` is one row, and Phase 6 expands it into one case per value of each visual-variant prop in 4.3 — `APP-02[kind=primary]`, `APP-02[kind=ghost]`, … — each resolved against that variant's tokens and checked separately. Write the row once; the resolver does the multiplying, so no variant is silently left to the default. Where one variant differs, add a row for that value only and it overrides the general row for it alone:

```
| when:hover | background | — | id-APP-02 |
| when:hover,kind=ghost | background | n/a — a ghost button has no hover fill | id-APP-05 |
```

`<prop>=<value>` is checked against 4.3: a value that prop does not have fails the parse. A value no row covers — possible only when every row for a property and state names values — also fails, naming the uncovered values. Dimensions expand along a `size` axis instead, never along emphasis. `n/a` is one case for every value at once.

**`transform`** — an optional column. When a state is expressed as a token at a stated transform rather than its own token (shadcn's hover is `primary` at 80% alpha), write `alpha 80%` there. It is compared exactly; an unstated transform in the implementation is a mismatch.

### Platform tokens (4.4) — only where the TOKEN differs, never where the spelling does

**One tree, cross-platform.** The design system has a single DTCG token tree and the contract
names canonical paths from it — `component.button.primary` — for every platform at once.

**Spelling is the canonical document's job.** How each platform writes that token is
`tokens.naming_convention.<platform>` in the design-system context, applied when the canonical
document is generated: `--cds-button-primary` on web, `buttonPrimary` on iOS. A contract never
states a platform's spelling, and a second tree is never needed for it.

**A different TOKEN is a stated row.** Where a platform's design genuinely reaches for another
token — an iOS control tier the web does not have — chapter 4.4 says so, for that platform only:

```
| platform | when | property | token | id |
| ios | when:appearance=primary | background | `component.button.accent.background` | id-APP-30 |
```

Each row replaces the cross-platform case it names — same property, state and variant — in that
platform's canonical document only; every other platform keeps what 4.1 states, and a case 4.4
does not name is unchanged everywhere. A row for a platform the contract does not target fails
the parse. These rows are overrides, so the every-variant rule of 4.1 does not apply to them.

### Interaction states (4.2) — every valid state is answered

The role-archetype names the interaction states **valid for its role** — `interaction-states:` in its frontmatter; a button's are `hover`, `focus-visible`, `pressed`, `disabled`. The closed set, and how each state is spelled in token trees (`pressed` is `active` in Carbon), is `system/vocabulary/interaction-states.json`. Chapter 4.2 answers **every one** of them:

```
| state | what changes | driven by |
| hover | background | platform |
| focus-visible | focus-ring, border-color | platform |
| pressed | — | platform |
| disabled | background, foreground | prop |
```

- **`what changes`** lists the properties that take **their own token** in that state, from the declared property set — or `—` when none do. A valid state with no row fails the parse, naming the state.
- **A property that does not change keeps its rest token — never "nothing".** Phase 6 generates that case for every state × tokenised property × variant the contract did not write (`APP-01@pressed[kind=ghost]`: *background keeps its rest token `button.ghost`*), and a verifier checks it by forcing the state. `nothing` is refused: it meant different things in different places — policy draws the indicator, the platform draws it, it genuinely stays put — and an alias means exactly one. If the tree holds this component's own token for a state the contract aliases, the report says so (`state_token_unused`), and you ask which is intended — the tree or the contract is wrong.
- **4.1 and 4.2 must agree, both ways.** Each property 4.2 lists for a state needs a 4.1 slot in that state, and a rest (`always`) slot; a 4.1 slot in a state 4.2 does not list it for fails too. Together with per-variant expansion, that makes every state × property × variant a case the canonical document states — and a case the tree cannot express yet is a named token gap, never a quiet omission.
- **`driven by`** — `platform` (the platform produces it: hover, pressed, focus-visible), `prop` (the component is told: disabled, expanded), or `both`.
- The contract may **add** states its role does not (a selectable Chip's `selected`) with `interaction-states: [selected]` in its own frontmatter. It can never drop one the archetype makes valid.

**Where the answers come from.** The token tree first: Phase 2 has already read which states this component's tokens carry, and a state with tokens is a state that changes those properties. For each valid state the tree says nothing about, ask — one question, listing only those states:

```
header: "States"
question: "Your tokens say nothing about how [Component] looks when [pressed / focused by keyboard]. Which properties get a token of their own in each? Anything you don't name keeps its resting token."
```

Record the properties named; for the rest, write `—` and let Phase 6 generate the aliases. Never fill a state in from convention.

### State machine (5.4)

Write one only for a component that owns state which moves. It holds transitions, one per row; closure is generated by Phase 6, never written.

A machine covers **only state this component owns**. A child's state is opaque to the parent — that is what keeps the grid small, since composition turns a product into a sum. The exception is state a parent genuinely coordinates rather than delegates (a combobox's open list, with focus held in the entry), which is why that machine lives in the parent.

Anything that happens *besides* the state change — a value committed, a value left alone — is an ordinary 5.1 requirement conditioned `when:following:<transition-id>`, so the trigger that performs it is bound once.

### What carries over from the old format

These rules are unchanged; only the section they land in has moved.

**Ownership is a Composition fact, established once in 3.1 — never restated per chapter.** Cardinality and Accepts already say which children are obligatory, which optional, and that nothing else is allowed. Record delegation in 3.3 and nowhere else: that single structural statement already implies the child's appearance, behavior and accessibility live in its own contract.

**Pattern references are not composition.** Composition is ownership transfer — the zone *is* an instance of the child. A pattern reference is a zone built to another component's compliance bar without being an instance of it: it is still owned here, so it gets its own rows in full, plus one line saying which contract's conventions it reuses and anything it deliberately simplifies.

**Delegation extends to behavior, not just structure.** A delegated zone gets no rows in 5.1 or 5.2. State once, in 3.3, whether its interaction passes through untouched (the common case) or the shell genuinely intercepts it — and only write "intercepted" where the interview confirmed a real detection mechanism, naming it.

**Three prop categories, never mixed:** layout props (2.3) control spatial arrangement; visual variants (4.3) switch which style applies; behavioral props (5.3) configure what the component does.

**A duration is not automatically a token.** A motion duration (how long a state change animates) is a token, in 4.1. An interaction or lifecycle duration (auto-dismiss, debounce, show-delay) determines whether and when something happens — that is a behavioral prop in 5.3 with a stated default. WCAG 2.2.1 expects that kind of timing to be adjustable, which is the opposite of what a token is for.

**Adaptive layout (2.2) is container-relative, never viewport-relative**, and the condition is shared intent — only the plumbing differs per platform, so it belongs in bindings, not in a Platform column.

**Events (5.2)**: one table, `direction: emitted | received`. The event's *name and payload* are the shared fact; the platform idiom is the binding — `addEventListener` naming for web (see `references/web/dom-events-model.md`), and that platform's own idiom for native (see `references/native-events-models.md`, where several platforms have more than one live idiom and you must name the one in use).

---

### Contract template

Path: `[ComponentName]/[ComponentName].md`.

```markdown
---
component: [Name]
version: 1.0
status: Draft
role-archetype: [derived in Phase 3 — a library name, or `none`]
platforms: [web, ios, android]
last_updated: [YYYY-MM-DD]
---

# Component Contract: [Name]

## 1. Intent

[One or two sentences: what it is, what need it solves. Not a description of its parts.]

## 2. Structure

### 2.1 Requirements

| when | statement | observe | kind | id |
|---|---|---|---|---|

### 2.3 Layout props

| prop | type | required | default | description |
|---|---|---|---|---|

### 2.4 Element

| platform | element | id |
|---|---|---|

## 3. Composition

### 3.1 Zones

| zone | accepts | cardinality | position | absent | id |
|---|---|---|---|---|---|

## 4. Appearance

### 4.1 Token slots

| when | property | token | id |
|---|---|---|---|

### 4.2 Interaction states

| state | what changes | driven by |
|---|---|---|

### 4.3 Visual variants

| prop | type | required | default | description |
|---|---|---|---|---|

## 5. Behavior

### 5.2 Events

| when | direction | name | payload | id |
|---|---|---|---|---|

### 5.3 Behavioral props

| prop | type | required | default | description |
|---|---|---|---|---|

## 6. Accessibility

| when | statement | observe | kind | id |
|---|---|---|---|---|
```

Include 2.2, 3.2, 3.3 and 5.1/5.4 when the component has something to put in them; keep the six chapter headings regardless. **2.4 and 4.2 are never optional** when the archetype is not `none` and has interaction states: they are where every platform's element and every valid state are answered, and Phase 6 fails the parse without them.

### Bindings template

Path: `[ComponentName]/[ComponentName].bindings.json`. It holds **only the ids this contract introduces**, and within those, only what is genuinely platform-specific. Most entries are small, because `needs` is derived from `observe` — only `expect` must be authored.

```json
{
  "contract": "[Name]",
  "version": "1.0",
  "bindings": {
    "STR-01": {
      "web":     { "expect": { "max_ratio": 1.0 } },
      "ios":     { "expect": { "max_ratio": 1.0 } },
      "android": { "expect": { "max_ratio": 1.0 } }
    },
    "BEH-02": {
      "web":     { "expect": { "equals": true } },
      "ios":     { "binds": false, "reason": "no platform-level form model exists off the web" }
    }
  }
}
```

Every requirement needs a binding for every platform in `platforms`, or an explicit `binds: false` with a reason. A missing binding is a lint failure, not a default — it would otherwise be indistinguishable from a requirement nobody got to.

---

## Phase 6: Resolve, and the optional props schema

### Resolve the contract

Run the resolver on the contract just written, write back what the tree answered, and resolve again — once per component:

```bash
python3 <skill>/scripts/resolve.py      [ComponentName]/[ComponentName].md --out [ComponentName]/canonical
python3 <skill>/scripts/writeback.py    [ComponentName]/[ComponentName].md
python3 <skill>/scripts/resolve.py      [ComponentName]/[ComponentName].md --out [ComponentName]/canonical
python3 <skill>/scripts/resolve_view.py [ComponentName]/[ComponentName].md
```

**The token tree is the authority, so what it answers goes into the contract without asking.** `writeback.py` replaces each `—` the tree answers uniquely with the token — or, where each variant has its own, with the pattern they share (`component.button.{kind}-hover`) and an override row for every value that breaks it — and fills each row's `scope`. It never replaces a pinned token, never touches `n/a`, and leaves `—` wherever the tree did not answer: those stay gaps, and are asked about below. A finished contract shows its real tokens; `—` in one is always a gap.

The first emits one canonical document per platform in `platforms` — the interchange format a verifier reads. The second emits `[ComponentName].spec.md`, the artifact a **person** reads: the contract's own chapters with the role-archetype's and the policy's inherited requirements resolved in, origin as a column.

Three kinds of output come back, and they are not the same kind of thing:

| | Means | What to do |
|---|---|---|
| **lint** | the document is malformed — an unknown condition, a missing binding, a pinned token that is not in the tree, a machine with two answers for one cell | **fix it and re-run.** The resolver exits non-zero; a contract that does not resolve is not finished |
| **token gaps** | the document is fine; the **token tree** cannot express something yet | report to the user, by kind and who fixes it. Do not "fix" it by inventing a token name |
| **machine closure** | how many generated checks the state machine implies | nothing — it is information, not a finding |

**A gap is never a reason to edit the contract into silence.** `absent-from-tree` and `dimension-unmet` are tasks for whoever owns the token tree; `ambiguous` is one question for the author; `unmapped-leaf` means the tree has tokens this design system has not taught the skill to read, and the fix is a `leaf_map` entry in `.claude/design-system-context.yml` — **never a new token**, since one may already exist under a spelling nobody mapped.

### Implementation evidence: questions, never edits

When an implementation has been observed — a verifier run against the real component, a coded reference or Storybook link from Phase 2 checked against the canonical document — run:

```bash
python3 <skill>/scripts/evidence.py [ComponentName]/[ComponentName].md results.json
```

It lists where the implementation **contradicts** the tree (a different token, a literal) and where it **adds** to it (a token where the tree had no answer, or where the contract says `n/a`), in the tree's own token names. **Change nothing on the strength of it.** Ask each one, grouped as it prints, with three answers: the **contract** is wrong (edit it), the **component** is defective (report it), or the **tree**'s own statement is wrong (a description or a reading — fix it there). An implementation is evidence; only the tree and the person are authority.

### Act on what the report says the design system does not know yet

Run the resolver with `--report [ComponentName]/.resolve-report.json` and act on it before
finishing. This is where the design system's own layer grows — one component at a time, and
only from confirmed answers.

**A shared group could fill a case (`shared_unconfirmed`).** A group declared in `tokens.shared` has a token for a case this component left unresolved, and this component is not a member. Ask: *"Does [Component] draw its [property] from the shared `[group]` tokens (used by …)?"* On yes, add the component to that group in the context and re-run from the first resolve — write-back then states the token, with `scope: shared:[group]`. Membership is never assumed: the tree shows a group exists, not who uses it.

**Policy rows this component engages (`policy_to_ask`).** A policy row is asked the first time a
component *engages* it — its `engaged-by` column says when — so a Button raises token discipline,
focus indicator and touch-target floor, and never the loading or empty-state conventions. Ask
every engaged row in one batched `AskUserQuestion` call, each with **defer** as a real option.
Then record the answer where it belongs:
- **decided** — write the statement into the policy row **and** its per-platform bindings into
  the policy's `.bindings.json`. A decided row without bindings fails the parse.
- **deferred** — write `deferred — YYYY-MM-DD` as the statement. It is then not re-asked; the
  report keeps listing it under `policy_deferred`, so it stays visible without becoming noise.

Never write a decided statement the person did not give. Policy is the one layer nothing can
detect — a filled row must come from a decision.

**Property spellings the resolver cannot read (`unmapped-leaf` gaps).** These are the lazily-asked
`leaf_map` questions from Phase 0B, asked now because this component needs them. Offer the
detector's suggestion first, and write only a confirmed answer.

Re-run the resolver after recording answers, until lint is zero and nothing is left to ask. Then
report what this run taught the design system — `python3 <skill>/scripts/learned.py diff` — so the
person sees exactly what every later component will inherit. On the second component of a design
system this list should be short; on the tenth, usually empty. **A run that keeps asking what an
earlier run already answered is a defect**, and it is tested (`scripts/test_scripts.py`,
*the second component asks nothing the first settled*).

### If this run changed something shared, ask before touching any other contract

A contract's own files are yours to write. **Every other contract in the design system is not.**

Most runs change nothing shared. But two things this run may have recorded are inputs to *every* contract — a **policy row that was decided**, and a **facts change that affects token reading** (`leaf_map`, `tiers`, `patterns`). When either happened, other contracts may now resolve differently, with nothing in their own directories to say so.

Only then, run:

```bash
python3 <skill>/scripts/check_generated.py --exclude [ComponentName] --json
```

`--exclude` drops the component just finished, so what comes back names **only the others**.

- **Nothing out of date** — say nothing. This is the common case, because a policy row joins only the contracts that *engage* it, and a Button never engages a loading-state row.
- **Something out of date** — **list every affected contract before doing anything**, one line each, naming the files and what moved (`Card — Card.web.json: +1 (POL-07) requirement`). Then ask, in one `AskUserQuestion` call, whether to update them now. Offer updating all, or leaving them.

**Update only on an explicit yes**, with `python3 <skill>/scripts/check_generated.py --exclude [ComponentName] --fix`. On a no, say they stay out of date and that the same command will list them again later. **Never update another component's files without being told to** — the diff is the signal that a shared decision reached further than this component, and silently applying it destroys the only moment anyone would see that.

Two findings are never acted on automatically:

- **`orphan`** — a generated file nothing produces any more, usually a platform dropped from that contract. Report it; deleting a file because nothing regenerates it is a conclusion for a person.
- **`CANNOT CHECK`** — that contract lint-fails, so it cannot be compared. Report it as a defect in *that* contract, not as something this run caused, and never as up to date.

### What replaced `structure.json`

Earlier versions emitted `[Component].[Platform].structure.json` and checked it against a rendered tree. **The canonical document replaces it, and the check moved out of this skill.** The reasoning is the one this whole format rests on: the skill's output ends at a *description*, and executing it belongs to whoever owns that platform's toolchain. A verifier reads the canonical document, declares what it can and cannot observe, and reports `pass · fail · unverified · n/a` — anything it cannot observe is named, never passed.

`references/structural-fact-validation.md` keeps its value and changes audience: it is how a **verifier author** obtains a real rendered tree per platform (the live DOM for web, an accessibility-node dump for native) and reads order from it. Its rule still governs — check what actually rendered, never source code, because the contract deliberately refuses to require a particular implementation shape.

### Token-name validation (only if `generated_downstream` is confirmed)

Unchanged in substance, and still a different check from everything above: it asks whether a **real generated symbol** in a platform file (a CSS custom property, a Swift constant, an Android resource) corresponds to the canonical token the contract named. It runs only when `tokens.generated_downstream` is `true` — a hand-typed literal has no generated name to validate, so there is no lesser check to fall back to.

What feeds it now:
- **the resolved token slots** from chapter 4.1 — every slot Phase 6 reported as `bound`, which is the set of canonical paths this component actually binds. A slot with a gap has nothing to validate and is excluded, not failed twice.
- `tokens.naming_convention` for that platform's locked convention — all three axes — per `references/token-naming-validation.md`'s "lock on first success".
- the platform's real generated output, for the candidate names.

Run the algorithm exactly as that reference specifies; never write a per-component variant.

### Props schema (only if Q10 asked for one)

**This survives the move to canonical documents, because it checks a different subject.** The canonical document describes outcomes an implementation must produce; a props schema validates a **consumer-supplied props instance** — is this a legal set of props to pass? Neither answers the other's question, and the schema is consumed by ordinary build tooling that will never read a canonical document.

One file per platform, `[ComponentName].[platform].schema.json`, derived from the contract's prop tables:

| Contract | Schema |
|---|---|
| 4.3 Visual variants — `enum:a,b,c` type | `enum` on the property |
| 5.3 Behavioral props — type + default | `properties`, `default` |
| 5.3 / 2.3 props — `required: yes` | `required` array |
| 2.3 Layout props — type + default | `properties`, `default` |
| 3.1 Zones — `accepts: component:X`, cardinality ≥ 1 | `properties` with `$ref` or inline `object` |
| 3.1 Zones — cardinality minimum | `minItems` on the array |
| 3.1 Zones — cardinality starting at 0 | present in `properties`, absent from `required` |

Every row comes from a platform-neutral table, so don't introduce platform-to-platform variation here; if a design system genuinely needs different props per platform, flag it rather than silently encoding it.

**Don't write this file. Run it:**

```bash
python3 <skill>/scripts/schema.py [ComponentName]/[ComponentName].md
```

The mapping above has no judgement in it — it is column-to-keyword translation from tables with fixed columns — so writing it per run cost consistency (two components shaping the same situation differently) and put a file in `generated/` that nothing could reproduce, which left `check_generated.py` with an exception and made a diff there mean two things. The script implements exactly the table above, plus the rules below, and its lint names any prop type it does not know rather than guessing one.

**Schema rules**, implemented by the script: Draft 07 (`"$schema": "http://json-schema.org/draft-07/schema#"`); `"$id"` as `[component-name]-[platform]` in kebab-case; `"title"` as display name plus platform; `"description"` on every property, copied from the contract; enums as `"type": "string"` + `"enum"`; numbers with `minimum`/`maximum` **only** where the contract states bounds; child arrays as `"items": { "$ref": "[Child].[SamePlatform].schema.json" }`, always the same platform as the schema being generated.

**A `handler` prop stays in the schema, and stays in `required`, with no type.** A function is not JSON, so its shape cannot be expressed — but *"you must pass `onPress`"* is a legal fact about a props instance, and dropping the prop because its type is unexpressible would let an instance the contract forbids validate clean.

**`additionalProperties` is `true`, and is written out rather than left to the default.** The schema says what must hold for an implementation to be considered compliant; the contract is a **floor, not a ceiling**, so an implementation may carry whatever else it needs. Don't close this citing *nothing passes by accident* — that invariant is about a requirement that **exists** going unchecked, never about forbidding what the contract never claimed. It is stated explicitly because its absence reads as an oversight.

---

## Output

**Every component gets its own directory** — `[ComponentName]/` (PascalCase). Its parent is `contracts.path` from the design-system context when that is recorded; otherwise ask once, and record it, so no later component asks again.

```
[ComponentName]/
├── [ComponentName].md                          the contract — source, authored in Phase 5
├── [ComponentName].bindings.json               per-platform expect values — source
└── generated/                                  nothing here is authored or edited
    ├── [ComponentName].spec.md                 the artifact a person reads
    ├── [ComponentName].web.json                one per platform in `platforms`
    ├── [ComponentName].ios.json
    └── [ComponentName].web.schema.json         only if Q10 asked for one
```

**Everything generated goes in `generated/`, and nothing else does.** The directory is what tells a reader, with no README in front of them, which files are theirs — so never write a generated file beside the contract, and never write an authored one inside `generated/`.

The first two are authored and belong in version control. The rest are generated: regenerating them must produce identical files, so a diff after a re-run means the contract changed, not the tooling.

Confirm the full tree after writing, and report: lint (must be zero); token gaps, by kind, with who fixes each; any machine closure count; and **what this run taught the design system**, from `learned.py diff` — the facts, policy decisions and role-archetypes every later component now inherits.

`.resolve-report.json` and `.claude/.context-snapshot.json` are tool state, regenerated each run — suggest ignoring them in the design system's repository rather than committing them.
