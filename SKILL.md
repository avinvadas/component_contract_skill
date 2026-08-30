---
name: component-contract
description: Creates structured component contract markdown files for design systems, and optionally generates a JSON schema for prop validation. A component contract is a formal specification that documents a UI component's semantic markup, design tokens, behavior, and accessibility requirements. Use this skill whenever a user wants to create a new component spec or contract, document a UI component formally, generate a component contract md file, specify the structure or behavior or tokens of a component, audit what tokens a component uses, or generate a JSON schema for a component. Also trigger when the user says things like "create a contract for X", "document this component", "write up the spec for [component name]", "add [component] to the design system contracts", "I need a component contract", or "generate a schema for this component". If the user mentions a Figma link, a Storybook URL, or a coded reference alongside a component name or design system task, this skill almost certainly applies.
---

## What this skill produces

One interview produces **one component contract file**, capturing the design intent of a UI component across six sections, covering any combination of target platforms (Web, iOS, Android, macOS, Windows, Linux) within that single document. Sections that describe intent (Overview, Properties, most of Appearance, the shared parts of Behavior) are written once; sections that describe platform-native implementation (Structure's markup/control, most of Accessibility, the platform-specific parts of Behavior) hold one row per targeted platform inside the same section, rather than living in a separate file per platform. The document is meant to work as direct context for an agent implementing or generating the component, not only as something a person reads top to bottom — so nothing in it is inferred or left implicit that an implementer would need to ask about.

1. **Purpose** — one sentence: what the component is and what need it solves
2. **Structure** — the correct native markup/control per platform, including required and optional children
3. **Properties** — what the component exposes, organized by layout (CSS/flow), style (visual variants), and behavior (states, flags)
4. **Appearance** — which design tokens are applied
5. **Behavior** — how it acts, what events it dispatches, what events it responds to — per platform wherever that genuinely varies
6. **Accessibility** — focus traps, native accessibility roles/states per platform, keyboard/gesture navigation

A JSON Schema file is generated separately, one per targeted platform, if requested (Phase 6) — schemas are consumed by each platform's own build process, so they stay split even though the contract itself doesn't.

The person using this skill does not need to know HTML, ARIA, native accessibility APIs, or any platform's interaction conventions. The skill derives all technical decisions from plain-language answers about the component's purpose and how users interact with it.

---

## Reference files

`references/` holds the external, design-system-agnostic standards this skill derives from. They are not design-system content — they're the same regardless of which design system a component belongs to. SKILL.md's own tables cover the common cases inline; consult the matching reference file when a case falls outside those tables, or when you need the full attribute/keyboard set for a pattern the table only names in passing.

`references/` is organized by scope: platform-specific standards live under a directory named for that platform; standards that apply regardless of platform stay at the root.

### Universal (apply regardless of platform)

| File | Consult it when |
|---|---|
| `references/design-tokens-format.md` | Phase 2 Path B — recognizing whichever token file shape (DTCG, Style Dictionary, CSS custom properties, Tailwind config) the coded reference actually uses. |
| `references/figma-variables-model.md` | Phase 2 Path A — extracting bound tokens from Figma via structured tool access when available, or the manual-inspection fallback when it isn't. |
| `references/json-schema-draft-07.md` | Phase 6 — the full keyword reference and the Draft 07 vs. 2020-12 decision. |
| `references/platform-differences.md` | Comparing how a cross-cutting concern (accessibility API, layout adaptation, RTL, motion) is expressed across platforms, before following into the relevant platform directory for depth. Comparison content only — it does not decide which platform applies to a given component. |
| `references/native-events-models.md` | Phase 5 §5.3/§5.4 for any non-Web platform row — the native counterpart to `web/dom-events-model.md`, covering the idiom fork on each platform (closures vs. delegates, lambdas vs. listeners, routed vs. classic .NET events, GObject signals vs. Qt signals/slots). |

### `references/web/` — consulted when Q2 includes Web

| File | Consult it when |
|---|---|
| `wai-aria-patterns.md` | Deriving markup (Phase 3) or accessibility (Phase 4) for a pattern not fully covered by the decision tables below — combobox, menu, tooltip, tree view, slider, grid, accordion, or the full keyboard set for any pattern. |
| `wcag-mapping.md` | Deriving §6 Accessibility (Phase 4), to ground a requirement in the success criterion it satisfies — optional citation, not a new question to ask the designer. |
| `html-semantics.md` | Phase 3 edge cases the decision table doesn't resolve — nested interactive content, disabled vs. aria-disabled, form-associated custom elements. |
| `css-layout-and-interaction.md` | Phase 3 §2.2 Order / §2.3 Adaptive Layout — container queries, and CSS logical properties for RTL-safe positioning. Phase 4/5 §4.1 / §6.3 — the `:focus` vs. `:focus-visible` distinction, `prefers-reduced-motion` and motion tokens. |
| `dom-events-model.md` | Phase 5 §5.2/§5.3/§5.4 — the framework-agnostic `CustomEvent` contract, and how a contract's behavior/accessibility claims are verified against rendered DOM output rather than framework internals. |

### Other platforms — consulted when Q2 includes that platform

Q2 (Platform) is multi-select; Phase 3/4 run once per selection, and for any platform other than Web, that run consults the matching file below instead of the web-specific tables — see each file's "Component / structure resolution" and "Accessibility API" sections.

| File | Platform |
|---|---|
| `references/ios/ios-hig-accessibility.md` | iOS |
| `references/android/android-material-accessibility.md` | Android |
| `references/macos/macos-hig-accessibility.md` | macOS |
| `references/windows/windows-ui-automation.md` | Windows |
| `references/linux/linux-atspi-accessibility.md` | Linux |

Each reference file covers exactly one external standard or concern, independent of the others — CSS mechanics, DOM events, ARIA patterns, WCAG, token file formats, JSON Schema, and each native platform's own accessibility/interaction model don't reference each other's internals. Adding coverage for a new standard means adding a new file, not expanding an existing one's scope; this keeps each file independently correctable by someone who only knows that one domain.

Every reference file carries a **`Last verified:` date** directly under its "Source of authority" line. Phase 0 uses it.

---

## Phase 0: Pre-interview checks

Two independent checks, both run once, before Phase 1, every time the skill starts. Both are cheap by default and only occasionally do real work.

### 0A: Reference freshness check

1. For every file under `references/`, read its `Last verified:` date. Comparing dates is local and free — do this for all 15 files unconditionally.
2. If today is less than **90 days** after that date, the file isn't due. Skip it — no network access, nothing to report.
3. If 90 days or more have passed **and** web access is available in the current environment: fetch the URL(s) the file cites in its "Source of authority" line and compare against what the file currently says.
   - **`platform-differences.md` is the one exception** — it aggregates the other 13 files rather than citing an external URL itself, so "checking" it means confirming it still agrees with whichever of those files were also due this run, not fetching anything.
   - **No material change** (the spec's version/status is the same, nothing the file describes has been renamed, deprecated, or superseded): update that file's `Last verified:` date to today and move on silently — no need to mention this to the user.
   - **Material change found** (a new spec version, a deprecated/renamed API or attribute, a new pattern that supersedes what's documented): stop and tell the user what changed and which file it affects, before proceeding to Phase 1. Ask whether to update the reference file now, defer it, or continue this session with the existing content. Never rewrite a reference file's content on your own initiative — these are curated explanations, not a scrape of the spec, and a drive-by edit from an automated check is exactly the kind of unreviewed change that principle exists to prevent.
4. If web access isn't available in the current environment, skip step 3 entirely for this run. Only mention the skip if at least one file was actually due (don't report "nothing to check" as if it were a finding) — and never block the interview from starting because a freshness check couldn't run.

This check must never be the reason someone can't generate a contract. A skipped, deferred, or inconclusive check is always a reason to proceed with what's already there, not to stop.

### 0B: Design system context

Everything in `references/` is external and generic — it's the same regardless of whose design system this is. This step is the opposite: a handful of facts specific to *this* design system that don't change component-to-component (token prefix, which platforms use which framework, naming casing, RTL support, whether existing contracts live somewhere findable) and shouldn't be re-derived or re-asked on every single invocation.

1. Look for a context file at `.claude/design-system-context.yml` in the current working directory (create the `.claude/` directory if it doesn't exist yet, when writing in step 3). This is a cheap local file check — do it unconditionally.
2. **If it exists**, load it silently. Its contents seed defaults for Phase 1 onward (e.g., a token-naming convention default for Q9, a per-platform framework default that changes which concrete controls Phase 3 names for iOS/Android, a default platform set to pre-check in Q2) — seeding a default is not the same as skipping the question. A component can still legitimately differ from the system-wide default (not every component targets every platform the system generally supports), so nothing here should suppress a question, only pre-fill or bias its options.
3. **If it doesn't exist**, don't run a Phase-1-style sequential interview for this — these fields are independent of each other (unlike Phase 1's questions, which deliberately go one-at-a-time because later options depend on earlier answers), so there's no reason to force multiple round-trips. Instead:
   - **Detect first.** Scan the working directory before asking anything: a token file (`tokens.json`, `tailwind.config.*`, `*.tokens.json`, CSS custom-property definitions) for format and prefix; platform manifests (`Package.swift`/`Podfile` vs. `build.gradle` dependencies) for framework hints; an existing directory of files carrying this skill's frontmatter shape for where contracts already live. This costs nothing and needs no confirmation round-trip when it succeeds outright. **Read the file's actual content, not just its filename** — a `tailwind.config.js` whose colors reference `var(--token-name)` means the real source format is CSS custom properties with Tailwind only as a consumption layer, not "tailwind" as the format; recording it as plain Tailwind would be wrong even though the right filename was found.
   - **Ask everything left in one batched `AskUserQuestion` call, up to four questions.** Cover token naming convention/format, per-platform framework (SwiftUI vs. UIKit, Compose vs. View system, GTK vs. Qt — this materially changes which concrete controls Phase 3 names, not cosmetic detail), naming casing, and RTL support. Where step one detected a value — including a confident one — make it the first, pre-recommended option in that question rather than skipping confirmation entirely; a system-wide default deserves a quick confirm, not a silent guess, since every future component inherits it. If more than four fields need either confirmation or asking (a design system spanning several platforms easily exceeds four), use a second batched call rather than forcing everything into one or dropping confirmation for whichever fields didn't fit — order both calls so anything ambiguous or fully undetected comes first, confident detections last, so a second call is the one most likely to be skippable in practice, not the one most likely to matter.
   - Write the result to `.claude/design-system-context.yml` when done, and confirm the path to the user. This file is meant to be checked into the design system's own repo, not treated as scratch state — it's shared context for the whole team, not a personal cache.
4. **If a later phase detects a contradiction** between this file's contents and something else (a coded reference, a direct interview answer) — that's the conflict-resolution policy's job, not this step's. See below. A confirmed correction there should update this file, not just the current contract, so the system-wide default stays accurate for the next component.

This step, like 0A, must never block the interview — if the file can't be read or written for some reason, fall back to asking the equivalent questions inline during Phase 1 instead of stopping.

### `design-system-context.yml` schema

Only include platform keys this design system actually uses — never write a placeholder for a platform it doesn't target.

```yaml
design_system: [free-text name, optional]
last_updated: [YYYY-MM-DD]

tokens:
  format: dtcg | style-dictionary | css-custom-properties | tailwind
  prefix: [string, e.g. "ds-", "color-", "--ds-"]

platforms:
  web:
    framework: react | vue | web-components | vanilla
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

contracts_directory: [path relative to repo root, optional — set once detected, so future runs don't re-scan]
```

---

## Conflict resolution policy

**Intent — an interview answer, plus general references — is always authoritative. A provided existing implementation is something to test against that intent, not a second source of truth to reconcile it with.** This follows from how a contract actually gets built: Phase 1's interview plus Phase 3/4's derivation from `references/` are already sufficient to construct a complete, correct contract on their own, for everything except token bindings (§4.3) — no existing implementation needs to be read to get structure, props, behavior, or accessibility right; that's what the interview and the general references are for. So when an implementation is *also* provided, its role is to be checked against a contract that's already fully constructible without it — not to supply competing facts that need arbitrating case by case.

The one deliberate exception is design tokens: a token's literal binding is a genuinely arbitrary, system-specific fact that no amount of best-practice knowledge or stated intent can derive on its own — that's exactly why Phase 2 treats a coded or Figma source as a legitimate *information* source for tokens specifically, not just something to verify. Everything below assumes a non-token fact.

Use this callout format wherever a mismatch is documented in a contract, so it never gets silently absorbed either direction:

> ⚠ **Discrepancy:** [what the provided implementation does] vs. [what this contract states] — [why: general-reference precedence / doesn't match stated intent / no source covers this].

**1. Provided implementation vs. general reference (ARIA/WCAG/HTML/CSS/native platform files) — a compliance question, not a negotiation.** The general reference wins on what the contract *states*, unconditionally — never mirror a non-compliant pattern just because it's what currently exists. State the compliant answer, then flag the divergence with the callout above, so the contract does the job the README claims for it: surfacing drift, not hiding it. *(Verified in principle by hand — a component reading `<div onClick>` where the Web decision table calls for `<button>` produces exactly this callout. Still inert in practice today, since it requires reading structure from an implementation and Phase 2 only extracts tokens — but per the framing above, what's actually needed to unblock this is a narrow verification check against already-known expected facts, not a general code-ingestion capability.)*

**2. Provided implementation vs. a direct interview answer, same fact.** The interview answer is authoritative — that's what stating intent is for. A mismatch is a finding *about the implementation* (stale, incomplete, or simply wrong), not an open question to re-litigate with the designer. State what the contract requires per the interview answer, then flag the implementation's divergence with the callout — don't stop mid-flow to ask "which one should I trust." *(Inert today for the same reason as case 1.)*

**3. Multiple platform implementations disagreeing with each other on something the contract treats as shared intent (§2.2, §3, etc.).** Don't let two implementations negotiate the truth between themselves. The shared intent was already established once, in the interview — check each platform's implementation against *that*, independently, not against each other. If a genuine, intentional per-platform difference turns up this way, that's a signal the fact isn't actually shared intent after all — move it to a platform-specific row, don't leave it looking like agreement.

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

**The interview goes from general to specific, in the same topic order as the contract itself:** scope, then overview, then structure, then properties, then appearance. There's no dedicated question for §5 Behavior or §6 Accessibility — both are derived, never asked, per the whole premise of this skill. The one exception is a single conditional follow-up attached to Q4 that feeds §5 directly — see there for why it can't be asked any earlier.

Platform (Q2) comes right after Name & Purpose even though it isn't itself contract content — it's scope, not a section, and it determines how many rows every later table needs. Action and Interaction (Q3–Q4) sit next to each other because they're jointly the only two inputs Phase 3 needs to derive structure — more fundamental to what the component *is* than how it's composed, so they come before Composition/Parts, not after.

---

**Q1 — Name & purpose**
header: "§1 Overview"
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
- "Windows"
- "Linux"

This answer drives which reference file(s) Phase 3/4 consult, how many platform rows appear in the contract's per-platform tables, and how many per-platform schema files Phase 6 writes. It's scope, not §5 Behavior content — no follow-up here asks about behavior differences yet; that's Q4's job, once there's an actual interaction to ask "does this differ" about.

**Q3 — Action** *(drives semantic markup derivation in Phase 3, alongside Q4)*
header: "§1 Overview"
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
header: "§1 Overview"
question: "Which routing modes does it support?"
  - "Swaps content in place — no URL change"
  - "Each panel has its own URL"

**Q4 — Interaction** *(drives semantic markup derivation in Phase 3, alongside Q3 — its conditional follow-up below is the only place this interview feeds §5 Behavior directly)*
header: "§2 Structure"
question: "How does the user interact with it? Pick all that apply. (6 questions left)"
Multi-select:
- "Click or tap"
- "Choose from a list or set of options"
- "Drag to reorder or resize"
- "Scroll or swipe"
- "No direct interaction — it updates on its own"

If "Choose from a list" → single-select follow-up:
header: "§2 Structure"
question: "How many options can be selected at once?"
  - "Just one"
  - "Multiple"
Then single-select follow-up:
header: "§2 Structure"
question: "Is the list always visible, or does it open on demand?"
  - "Always visible"
  - "Opens as a dropdown"

If Q2 selected two or more platforms → open text follow-up:
header: "§5 Behavior"
question: "Does anything about this interaction work differently across those platforms — behavior or gestures specifically, not structure or accessibility (those are derived automatically per platform)? Only describe what changes; leave blank if nothing does."

Never assume the HTML element or ARIA role from the component name. Always derive from Q3 (action) and Q4 (interaction).

**Q5 — Composition**
header: "§2 Structure"
question: "Does it stand alone, or does it hold other components inside? (5 questions left)"
Single-select:
- "Stands alone"
- "Holds other components inside"
If "Holds other components" → open text follow-up:
header: "§2 Structure"
question: "Which components does it hold? Do any of them already have contracts?"

**Q6 — Parts**
header: "§2 Structure"
question: "What are its visible parts? Name each one and say what it's for — showing content, or doing something. (4 questions left)"
Open text. Add in the description: Examples of content parts: label, image, badge, description. Examples of action parts: close button, chevron, checkbox, spinner.

**Q7 — Visual styles**
header: "§3 Properties"
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
header: "§3 Properties"
question: "Can its layout change? Pick all that apply. (2 questions left)"
Multi-select:
- "Direction flips (horizontal ↔ vertical)"
- "Size grows or shrinks"
- "Alignment shifts (left / centre / right)"
- "Has a compact or overflow mode"
- "Adapts to the space available"
If "Adapts to the space available" → open text follow-up:
header: "§3 Properties"
question: "What changes when space is tight? What does your design system call those conditions?"

The first four options feed §3.1 Layout Props. "Adapts to the space available" and its follow-up feed §2.3 Adaptive Layout instead — a Structure concern, not Properties — even though it's asked here, in the same breath as the rest of this question, since "can its layout change" is one natural conversation for the person answering it.

**Q9 — States & tokens**
header: "§4 Appearance"
question: "Which extra states does it have? If your system names them differently, type the correct name in the field below. (1 question left)"
Multi-select:
- "Loading"
- "Error"
- "Disabled"
- "Selected / active"
- "Empty"

After answer → single-select follow-up:
header: "§4 Appearance"
question: "Do you have design tokens for this component?"
  - "Yes — I have a Figma link"
  - "Yes — I have a Storybook or code link"
  - "No — skip for now"
  If yes → open text follow-up:
  header: "§4 Appearance"
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

If a token's resolved value here contradicts the design-system context file (Phase 0B) — e.g. a different naming prefix than what's on record — never resolve it silently. Surface it with the Conflict resolution policy's callout format, and update the persisted context file if the token source turns out to be current truth. This doesn't map onto that policy's numbered cases — tokens are its deliberate exception, where both the coded reference and the persisted context are legitimate *information* sources on equal footing, not an implementation being tested against already-sufficient intent.

---

### Path C: Description only

Leave the token map as pending and note it clearly in the contract:

> Token map pending — no design source was provided. Supply a Figma node URL, Storybook story URL, or CSS/token file to complete this section.

---

## Phase 3: Derive structure (internal — not asked)

Two different things happen in this phase, at different frequencies — don't run everything per platform by default.

**§2.1 Semantic Markup runs once per platform selected in Q2.** The same Q3 (action) and Q4 (interaction) answers feed every run — what changes is which table resolves them to a concrete structure. Never infer the element/control from the component's name — the same visual form can require completely different structure depending on what the component actually does, and that holds on every platform.

- **Web** → use the decision table below.
- **iOS / Android / macOS / Windows / Linux** → use the "Component / structure resolution" table in that platform's reference file instead of the table below (`references/ios/ios-hig-accessibility.md`, `references/android/android-material-accessibility.md`, `references/macos/macos-hig-accessibility.md`, `references/windows/windows-ui-automation.md`, `references/linux/linux-atspi-accessibility.md`). Same Q3/Q4 inputs, that platform's native vocabulary as output.

Each platform's result becomes one row in §2.1's table (see Phase 5) — never a separate document, and never merged with another platform's row even when the two values happen to match.

**§2.2 Composition Zones (Setting cardinality, Setting order below) runs once, not per platform.** Cardinality and position are statements of intent — "the Close button is optional and sits top-right" doesn't change because the implementation platform changed. **§2.3 Adaptive Layout** is the same: the named conditions and what changes under each are shared intent, even though the underlying mechanism differs per platform (see Phase 5 for how to record that without a full Platform column).

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
| Both modes supported | Document both patterns in §2.1. State the condition for each. URL routing takes semantic precedence; `<nav>` + `<a>` + `aria-current` for routed mode, tablist pattern for in-place mode. |

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
→ The root element applies to the shell only. Document sub-component markup in their own contracts.

**When multiple actions apply**, the primary action defines the root element. Inner zones follow their own rules per the table above. The primary action is what the component fundamentally *is* to the user.

**When multiple valid root elements exist**, document all options and the condition for choosing each.

### Setting cardinality (for §2.2)

Use the user's answers from Q6 to fill the Cardinality column. When the user hasn't specified a maximum, use judgment:
- A label, title, or primary description → `1`
- A leading or trailing icon → `0–1`
- Action buttons in a footer → `1–3` or `0–3`
- Tags, chips, or list items → `0+` or `1+`
- Navigation steps or tabs → state the minimum (e.g., `2+` for tabs)

If not derivable from the component's purpose, note as `1+` and flag for confirmation.

### Setting order (for §2.2)

Mark a zone as `Fixed` when moving it would break the user's expectation or when its position is load-bearing for meaning or accessibility:
- Close / dismiss buttons → `Fixed — top-right`
- State indicators (expand chevron, selection checkbox) → `Fixed — precedes label` or `Fixed — follows label`
- Navigation controls (prev/next arrows) → `Fixed — flanks content`
- Primary action in a footer → `Fixed — rightmost action`

Mark a zone as `Flexible` when its position is a layout preference — e.g., a thumbnail that could appear above or beside text depending on the layout variant.

When the target design system supports RTL locales, record `Fixed` positions in logical terms (leading/trailing, start/end, inline-start/inline-end — whichever vocabulary the current platform uses) rather than physical ones (`left`/`right`), since a directionality flag alone does not flip physically-positioned layout on any of the platforms covered here except where the platform's own logical-property system does the work. See `references/platform-differences.md` for how each platform expresses this, then the specific platform file for the mechanism (`references/web/css-layout-and-interaction.md` for Web). If the system is confirmed LTR-only, physical terms are fine.

---

## Phase 4: Derive accessibility (internal — not asked)

Derive from the interview answers and each platform's Phase 3 structure decision. Do not ask the designer about ARIA, UI Automation patterns, AT-SPI roles, or keyboard/gesture navigation directly.

**§6.1 Roles & Attributes runs once per platform selected in Q2** — every platform has its own vocabulary, so this always gets a row per platform, same frequency as §2.1:
- **Web** → the ARIA-specific subsections below.
- **iOS / Android / macOS / Windows / Linux** → that platform's reference file, "Accessibility API" section, for the role/state/trait model. There is no separate decision table to duplicate here — the platform files already state what each requires.

**§6.2 Keyboard/Gesture Navigation and §6.4 Screen Reader / Assistive Technology Expectations are shared by default.** Derive once using the web subsections below for the common cases, and add a platform-specific note only where the actual key or gesture genuinely differs (e.g. `Escape` has no touch equivalent) — not as a matter of course.

**§6.3 Focus Management is shared** — derive once, regardless of platform count.

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

With all phases complete, write the contract as **one file**, regardless of how many platforms it targets. Fill every section from what you now know — never leave a placeholder unless the user explicitly said information is unavailable. Nothing should be left for a reader (human or agent) to infer or ask about — nothing in this file, ever, is a diff against another file, since there is no other file.

**Every subsection falls into exactly one of three treatments — decide which before writing it, don't default to one:**

1. **Always shared, no Platform column** — §1 Overview, §2.2 Composition Zones, §3 Properties (all of it), §4.2 Layout Policy, §4.3 Design Tokens, §5.2 State Machine, §6.3 Focus Management. These describe intent, not implementation — cardinality, purpose, token bindings, and internal state don't change because the target platform changed.
2. **State the intent once, then one manifestation row per platform** — §2.1 Semantic Markup, §5.3 Events Emitted, §5.4 Events Received, §6.1 Roles & Attributes. These sections have two distinct layers, and conflating them is the mistake to avoid: an **intent layer** (the abstract interaction archetype, or what an event/accessibility requirement means) that's genuinely platform-agnostic — the same "button-ness" or "announces on dismissal" regardless of platform — and a **manifestation layer** (the concrete tag, event signature, or attribute syntax) that's structurally platform-specific because every platform has its own vocabulary for expressing the same archetype. State the intent once, in plain language, at the top of the subsection — but never label it "Intent" or the table below "Manifestation" in the output itself; this is how you organize the derivation, not vocabulary to hand the reader. A plain opening sentence followed by "Each platform's [equivalent/event/implementation]:" carries the same structure without requiring anyone reading the finished contract to learn a framework they never asked for.

   **This is purely an internal organizing distinction — it never surfaces in Phase 1.** The interview only ever asks intent-level questions (what it does, how it's interacted with, what it's called) — it was never going to ask someone to name a tag or an ARIA attribute, so nothing here changes what gets asked. It only changes how what's already derived gets written up in Phase 5.

   Three checks for sorting any given fact into the right layer, useful when a case isn't obvious:
   - **Translation check** — can it be stated in plain language with zero tag names, API names, or attribute strings? If yes, intent. If the sentence collapses into nonsense without naming a specific platform's vocabulary, manifestation.
   - **Swap check** — if this platform's expression were replaced by a different, equally valid one on the *same* platform, would the plain-language statement still hold? If it survives the swap, the statement was intent and the swapped things were manifestations of it.
   - **Fidelity check** — is this the yardstick something gets checked against, or the thing being checked? Yardstick = intent; the thing being measured = manifestation.

   Two nuances worth knowing: a manifestation fact can have a smaller intent-level decision embedded in it (`aria-live="polite"` vs. `AutomationProperties.LiveSetting="Polite"` are both manifestations of one intent, but *which* urgency level — polite vs. assertive — is itself a real decision and belongs in the intent sentence, not re-decided per platform). And a manifestation fact that would be identical for *every* component in the design system (naming casing, framework choice) has drifted out of this contract's scope entirely — that's Phase 0B's job, not a per-component table.

   **A third nuance specific to §2.1: "manifestation" doesn't mean "any technique that produces an equivalent accessible role."** Passing an accessibility-tree check is necessary but not sufficient — see `references/web/wai-aria-patterns.md`'s first rule of ARIA use. A native element bundles behavior (keyboard handling with no JS dependency, right-click/Cmd-click on links, crawlability) that a re-purposed generic element patched with ARIA cannot replicate, even when both report the same role. So for §2.1 specifically, the named native element *is* the compliance condition, not an example among role-equivalent alternatives — only fall back to a re-purposed generic element when no native equivalent exists for the archetype at all.

   Then give every platform its own manifestation row *underneath* the stated intent — never merge two platforms into one row or write "same as Web," even when the concrete expression happens to be identical, since the manifestation table's job is to show each platform's own expression, not to economize on typing. This matters as much for an agent reading the file as context for implementation as it does for a person: neither should have to resolve a cross-reference to know what applies to their platform, and neither should see the same intent restated six times as if it were six independent facts.

   A platform's manifestation isn't chosen freely — it's checked for fidelity to the stated intent. If a platform's native vocabulary can't fully carry what the intent requires (a required behavior has no real equivalent, or is only approximated), say so explicitly in that row's Notes rather than listing an imperfect match as if it were clean.
3. **Shared by default, platform-specific only where a real difference exists** — §2.3 Adaptive Layout, §4.1 Interaction States, §5.1 Interactions, §6.2 Keyboard/Gesture Navigation, §6.4 Screen Reader / Assistive Technology Expectations. Write one shared version first. Add a platform note or column only when there's an actual divergence to record (Q4's cross-platform follow-up surfaces most of these for §5.1; the others come up rarely — hover not existing on touch platforms, `Escape` having no gesture equivalent). Don't add a Platform column pre-emptively "just in case."

   **For the two of these that are tables (§5.1, §6.2), "note or column" is not a free choice — it depends on how many rows actually diverge, and it must be deterministic:**
   - If every row in the table would carry the same value regardless of platform, there's no divergence — leave the table exactly as it is, no column, no note.
   - If a genuine divergence exists, add **one Platform column to the whole table** — never a column bolted onto only the differing rows, and never a prose note standing in for what the table itself should say. Every row gets a Platform value, including the rows that don't differ.
   - For a row whose content is identical across two or more platforms, write that row **once** with a comma-separated platform list (e.g. `Web, Windows`) — don't duplicate the row per platform. This is the opposite of treatment 2's rule, deliberately: treatment 2 sections never have a genuinely identical value across platforms (an ARIA role and a Compose `Role` are never literally the same string), so merging there would hide a real difference; here the content can be truly, literally identical, so merging is honest, not lossy. Only give a row of its own to a platform whose content actually differs from the rest.
   - §4.1 and §6.4 aren't tables in the template — a platform-scoped exception there is a sentence ("applies to Web and Windows, not Android"), not a column, and needs no further rule than that.

**Metadata as YAML frontmatter, not a blockquote.** Open the file with a frontmatter block (`component`, `version`, `status`, `last_updated`, `platforms`) rather than a bulleted blockquote — see the template below. This is a standard, widely-parsed convention (the same one SKILL.md's own frontmatter uses), which matters for the same reason as the rest of this phase: something other than a human may need to read this file's metadata without being told how.

**Purpose statement (§1)** — one sentence. What the component is and what need it addresses. Not a description of its parts.

**Ownership** — state clearly whether each property, behaviour, or token is owned by this component or delegated to a child. Use "delegated to [child]", "see [child] contract", "[child] manages this". Reference a child by component name only, e.g. "delegated to Icon" — the child has its own single contract file (`Icon.md`), so there's no platform-specific resolution to worry about anymore.

**Composite shells** — the shell owns: the root element, hard structural rules (e.g., "minimum 2 tabs required"), and platform-specific chrome (e.g., arrow navigation buttons). Everything else belongs to the sub-components. Platform-specific chrome shows up as that platform's own row in the relevant table (§2.1, etc.), same as any other platform-specific fact — it doesn't need special handling beyond the three treatments above.

**Raw vs. token-bound values** — never invent token names. If no token was found, document the raw value and note it as unbound.

**Three distinct prop categories — never mix them:**
- **Layout Props (§3.1)** — control spatial arrangement via CSS; no DOM change, no token reference.
- **Visual Variants (§3.2)** — switch which visual style is applied; not token values themselves.
- **Behavioral Props (§3.3)** — configure what the component does; states, feature flags, operational options.

When the user answered yes to any item in Q8 (layout flexibility), populate §3.1. If they answered "None of the above", omit §3.1.

**§2.3 Adaptive Layout is container-relative, never viewport-relative — and it's a treatment-3 section:**
§2.3 maps available space conditions to layout configurations, and that mapping is shared intent (see treatment 1/2/3 above). Reference §3.1 props by name when describing what changes. Omit §2.3 entirely if the component's layout is identical regardless of available space. If it's useful to name which mechanism each platform uses to implement the same shared condition (CSS Container Queries for Web, Size Classes for iOS, etc.), add that as a short bulleted list under the table, not a Platform column — the condition and its effect don't change per platform, only the plumbing does. See `references/platform-differences.md` for the comparison, then the specific platform file.

**Events Emitted/Received (§5.3/§5.4): the intent is shared, the manifestation is always per-platform (treatment 2) — ground each manifestation row in that platform's own idiom:**
For a **Web** row, record the event name as it would appear in `addEventListener`, not a framework's handler-prop convention — see `references/web/dom-events-model.md` for the `CustomEvent` contract and why this keeps the row verifiable against rendered output regardless of implementation framework. For a native platform's row, see `references/native-events-models.md` for that platform's own idiom (closures vs. delegate protocols on iOS/macOS, lambda callbacks vs. listener interfaces on Android, routed vs. classic .NET events on Windows, GObject signals vs. Qt signals/slots on Linux) — several platforms have more than one live idiom with no single canonical spec, so name the one actually in use rather than defaulting to whichever is more familiar.

---

### Contract template

One file per component, regardless of how many platforms it targets. Path: `[ComponentName]/[ComponentName].md` — see Output for the full directory shape.

```markdown
---
component: [Name]
version: 1.0
status: Draft
last_updated: [YYYY-MM-DD]
platforms: [list every platform selected in Q2, e.g. Web, iOS, Android]
---

# Component Contract: [Name]

## 1. Overview

[One sentence: what the component is and what need it solves. Follow with one short paragraph on what it owns and what it deliberately delegates.]

---

## 2. Structure

### 2.1 Semantic Markup

*(Always one row per platform — see Phase 5, treatment 2. State the archetype once; don't repeat it per platform row. This section is the structural commitment only — the actual accessibility attribute wiring belongs in §6.1, not here.)*

[One sentence: what this root fundamentally is, independent of platform — e.g. "A simple, generic trigger," "Navigates to a URL," "A modal overlay." Every platform below implements this same thing.]

Each platform's native equivalent:

| Platform | Tag / Control | Required | Notes |
|---|---|---|---|
[One row per platform listed in `platforms`. Web's Tag/Control column holds an HTML tag; most native platforms hold their native control name (see Phase 3). Never merge two platforms into one row, even when the value is identical. If a platform's manifestation can't fully carry the stated intent (a required behavior has no equivalent, or is only approximated), say so explicitly in Notes rather than listing it as a clean match.

The native element named here **is** the compliance condition, not one example among alternatives that would produce an equivalent accessible role. Per `references/web/wai-aria-patterns.md`'s first rule of ARIA use: a re-purposed generic element patched with ARIA to report the same role is not equally compliant, even if an accessibility-tree check alone would pass it — it's missing the native behavior (keyboard handling before JS loads, right-click/Cmd-click on links, crawlability, and more) that comes bundled with the real element and isn't visible to a role check. Only accept a re-purposed generic element in this table when the reference material confirms no native equivalent exists for the archetype at all.

Windows and Linux don't have a concrete "control" the way the other platforms do — their reference files ground structure in an accessibility pattern/role, not a control class. For those two, Tag/Control *is* the pattern/role itself (e.g. Windows: `Implementation-defined — any control exposing the Invoke pattern`; Linux: `GTK: GtkButton / Qt: QPushButton`, or `unspecified` if the target toolkit isn't known) — that's not an exception to stating intent separately, just a case where the platform's manifestation and its accessibility identity happen to be the same thing. The concrete wiring (`AutomationProperties.Name` for Windows, the toolkit's accessible-name API for Linux) still goes in §6.1.]

> **Root element choice:** [If multiple valid manifestations exist for a single platform, explain when to use each.]

### 2.2 Composition Zones

*(Shared — cardinality and position are intent, not implementation. See Phase 5, treatment 1.)*

> **Cardinality** — how many instances of a zone are valid:
> - `1` — exactly one, required
> - `1+` — one or more
> - `2–5` — minimum two, maximum five (use actual numbers)
> - `0–1` — optional, at most one
> - `0+` — optional, no upper limit
>
> **Order:**
> - `Fixed` — must appear in the documented position; may be restyled but not repositioned
> - `Flexible` — position may vary across implementations
> - `Responsive` — position is fixed per space condition; append both states: `Responsive — left of label ([condition-A]) / above label ([condition-B])`

| Zone | Purpose | Cardinality | Accepts | Order | Absent behaviour |
|------|---------|-------------|---------|-------|-----------------|
[One row per visible part. Cover all named parts from Q6.]

### 2.3 Adaptive Layout

*(Shared conditions, treatment 3 — see Phase 5. Omit this section if layout is identical regardless of available space.)*

> How the component's layout changes based on available space. Conditions are named by the design system — do not use pixel values or media query syntax.

| Condition | Layout prop changes | Zone position changes |
|-----------|--------------------|-----------------------|

[Only if useful — name each platform's underlying mechanism as a short list, not a table column:]
- Web: via CSS Container Queries
- iOS: via Size Classes

---

## 3. Properties

### 3.1 Layout Props

> Controls spatial arrangement via CSS — no DOM change, no token reference. Omit if the component has no layout flexibility.

| Prop | Values | Default | What changes |
|------|--------|---------|--------------|

### 3.2 Visual Variants

> Switches which visual style is applied. These select a visual mode — they are not token values.

| Prop | Values | Default | Description |
|------|--------|---------|-------------|

### 3.3 Behavioral Props

> Configures what the component does — states, feature flags, operational options. Omit if no configurable behavior beyond visual variants.

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|

---

## 4. Appearance

### 4.1 Interaction States

*(Shared by default, treatment 3 — see Phase 5.)*

[Visual states on the component's root element: default, hover, focus, active, disabled, error, selected. Note which are driven by Behavioral Props and which are pure CSS/native responses to user input. If all states are owned by children, say so. Note which platforms a state applies to only if it's not universal (e.g. hover) — don't add a Platform column if every state applies everywhere.]

### 4.2 Layout Policy

[Fixed layout rules always enforced — not configurable via props. Examples: a max-width constraint, clip behaviour. Omit if none.]

### 4.3 Design Tokens

#### 4.3.1 Token Strategy

[What tier of tokens this component uses, which properties it owns, which are delegated to children.]

#### 4.3.2 Token Map

[Source: Figma / Storybook / tokens.json / description-only — state clearly]

[Token-bound properties — the same conceptual token regardless of platform:]
| Property | Token |
|----------|-------|

[Unbound properties:]
| Property | Raw value |
|----------|-----------|

[Only if this design system's naming convention genuinely differs by platform (per `.claude/design-system-context.yml`, Phase 0B) — show what each token is actually called on each platform, rather than assuming one string works everywhere:]

| Token | Web | iOS | Android |
|---|---|---|---|

[Omit this table entirely when naming is consistent across platforms — most design systems won't need it, and it shouldn't appear pre-emptively "just in case."]

[No source provided:]
> Token map pending — supply a Figma node URL, Storybook URL, or CSS/token file to complete this section.

---

## 5. Behavior

### 5.1 Interactions

*(Shared by default, treatment 3 — add a Platform column only if Q4's follow-up confirmed a genuine difference.)*

| Event | Source | Action |
|-------|--------|--------|

### 5.2 State Machine

*(Shared — see Phase 5, treatment 1.)*

[Internal states and transitions. If the component has no internal state: "None — [what manages state instead]."]

### 5.3 Events Emitted

*(Always one row per platform — see Phase 5, treatment 2. State each distinct event's intent once; repeat the block if the component emits more than one conceptually distinct event.)*

[One sentence: what this event announces and what it means, independent of platform — e.g. "Announces that the component has been dismissed, and why (timeout vs. manual)." If there's no event to emit, say "None" once and omit the table below.]

Each platform's event:

| Platform | Signature | Notes |
|---|---|---|
[One row per platform. Web rows ground the signature in the DOM `CustomEvent` name as it would appear in `addEventListener`, per `references/web/dom-events-model.md`; native rows use that platform's own idiom per `references/native-events-models.md`. If the component emits nothing, state that once above instead of writing "None" per platform row.]

### 5.4 Events Received

*(Same shape as 5.3 — state what's listened for once, then each platform's implementation.)*

[One sentence: what this component listens for and how it responds, independent of platform. If it receives nothing, say "None" once and omit the table below.]

Each platform's implementation:

| Platform | Signature | Notes |
|---|---|---|

---

## 6. Accessibility

### 6.1 Roles & Attributes

*(Always one row per platform — see Phase 5, treatment 2. State each element's accessibility requirement once, then how each platform meets it. Repeat the block below once per element that needs distinct accessibility treatment — the root and an internal close button are two separate requirements, not one.)*

**[Element]:** [What this must convey to assistive technology, in plain language, independent of platform — e.g. "Must be announced as a live status region when its content changes, without requiring focus to move" or "Must expose button semantics."]

Each platform's implementation:

| Platform | Attributes | Notes |
|---|---|---|
[One row per platform. Web rows use ARIA roles/attributes; native rows use that platform's own vocabulary — see that platform's reference file. Never merge two platforms into one row. Repeat the intent-plus-manifestation block above for each additional element needing its own accessibility treatment.]

### 6.2 Keyboard / Gesture Navigation

*(Shared by default, treatment 3 — add a platform note or column only where the actual key or gesture differs.)*

| Key / Gesture | Behaviour |
|-----|-----------|

### 6.3 Focus Management

*(Shared — see Phase 5, treatment 1.)*

- **Focus trap:** [Yes — explain / No]
- **Tab order:** [Expected focus sequence]
- **On open:** [Where focus moves when the component opens, if applicable]
- **On close:** [Where focus returns when the component closes, if applicable]

### 6.4 Screen Reader / Assistive Technology Expectations

*(Shared intent by default, treatment 3 — note per platform only if the announcement mechanism differs.)*

- **On reach:** [What is announced when the component first receives focus]
- **On activation:** [What is announced when the user triggers it]
- **On state change:** [What is announced when state changes or content updates]
- **On error / empty:** [What is announced for error or empty states]
```

---

## Phase 6: JSON schema generation (if requested)

**Generate one `.schema.json` per platform selected in Q2.** This isn't because the content differs — it usually won't, since both §3 Properties and §2.2 Composition Zones are shared sections in the one contract file now, so every platform's schema is typically generated from the exact same inputs. The split exists because each platform's build process consumes its own schema file as a separate step — a compile-time concern, not a content concern. Never add validation rules not stated in the contract. See `references/json-schema-draft-07.md` for the full keyword reference, what NOT to add on your own initiative, and the Draft 07 vs. 2020-12 decision this skill deliberately pins.

### Mapping contract to schema

| Contract source | Schema construct |
|---|---|
| §3.1 Layout Props — values | `enum` on the property |
| §3.2 Visual Variants — values | `enum` on the property |
| §3.3 Behavioral Props — type + default | `properties`, `default` |
| §3.3 Behavioral Props — Required = Yes | `required` array |
| §2.2 Zones — required (Cardinality ≥ 1) with sub-components | `properties` with `$ref` or inline `object` |
| §2.2 Zones — Cardinality minimum | `minItems` on the array |
| §2.2 Zones — optional (Cardinality starts at 0) | present in `properties`, absent from `required` |

Every row above comes from a section that's shared across platforms, so don't expect (or introduce) platform-to-platform variation here — if a design system genuinely does need different props per platform, that's unusual enough to flag to the user rather than silently encode.

### Schema rules

- JSON Schema Draft 07 (`"$schema": "http://json-schema.org/draft-07/schema#"`)
- `"$id"`: `[component-name]-[platform]` in kebab-case, e.g. `modal-ios` — platform-scoped even though the content is typically shared, so build tooling can address one platform's file unambiguously
- `"title"`: component display name plus platform, e.g. `"Modal (iOS)"`
- `"description"` on every property, copied from the contract
- Enum props: `"type": "string"` + `"enum": [...]`
- Boolean props: `"type": "boolean"`
- Number props: `"type": "number"` with `"minimum"` / `"maximum"` only if the contract states bounds
- Child arrays referencing a sub-component, in `$ref` mode: `"items": { "$ref": "[Child].[SamePlatform].schema.json" }` — always the same platform as the schema currently being generated, so the wiring stays predictable
- Child arrays, in inline mode: `"type": "array"` + `"minItems"` where stated + an inline `object` shape instead of `$ref`

---

## Output

**Every component gets its own directory** — `[ComponentName]/` (PascalCase) — holding everything this interview produced. Ask for the parent directory to create it in if the user hasn't specified one; never scatter a component's files loose into a directory shared with other components' output.

Inside `[ComponentName]/`, always this shape, even for a single platform:
- `[ComponentName].md` — the one contract file, covering every platform selected in Q2 within its own structure (see Phase 5).
- `[ComponentName].[Platform].schema.json` — one per platform, only if Q10 requested a schema (see Phase 6).

Confirm the full directory tree after writing.
