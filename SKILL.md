---
name: component-contract
description: Creates structured component contract markdown files for design systems, and optionally generates a JSON schema for prop validation. A component contract is a formal specification that documents a UI component's semantic markup, design tokens, behavior, and accessibility requirements. Use this skill whenever a user wants to create a new component spec or contract, document a UI component formally, generate a component contract md file, specify the structure or behavior or tokens of a component, audit what tokens a component uses, or generate a JSON schema for a component. Also trigger when the user says things like "create a contract for X", "document this component", "write up the spec for [component name]", "add [component] to the design system contracts", "I need a component contract", or "generate a schema for this component". If the user mentions a Figma link, a Storybook URL, or a coded reference alongside a component name or design system task, this skill almost certainly applies.
---

## What this skill produces

One interview produces one shared contract file plus one file per target platform (Web, iOS, Android, macOS, Windows, Linux — any combination), capturing the design intent of a UI component across six sections:

1. **Purpose** — one sentence: what the component is and what need it solves *(shared)*
2. **Structure** — the correct native markup/control for the platform, including required and optional children *(per platform)*
3. **Properties** — what the component exposes, organized by layout (CSS/flow), style (visual variants), and behavior (states, flags) *(shared)*
4. **Appearance** — which design tokens are applied *(shared)*
5. **Behavior** — how it acts, what events it dispatches, what events it responds to *(per platform)*
6. **Accessibility** — focus traps, native accessibility roles/states, keyboard/gesture navigation *(per platform)*

This shape is deliberate and always the same, even for a single-platform component: one shared file, one platform file per target — so adding a platform to an existing component later never means restructuring what's already there.

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

### `references/web/` — consulted when Q8 includes Web

| File | Consult it when |
|---|---|
| `wai-aria-patterns.md` | Deriving markup (Phase 3) or accessibility (Phase 4) for a pattern not fully covered by the decision tables below — combobox, menu, tooltip, tree view, slider, grid, accordion, or the full keyboard set for any pattern. |
| `wcag-mapping.md` | Deriving §6 Accessibility (Phase 4), to ground a requirement in the success criterion it satisfies — optional citation, not a new question to ask the designer. |
| `html-semantics.md` | Phase 3 edge cases the decision table doesn't resolve — nested interactive content, disabled vs. aria-disabled, form-associated custom elements. |
| `css-layout-and-interaction.md` | Phase 3 §2.2 Order / §2.3 Adaptive Layout — container queries, and CSS logical properties for RTL-safe positioning. Phase 4/5 §4.1 / §6.3 — the `:focus` vs. `:focus-visible` distinction, `prefers-reduced-motion` and motion tokens. |
| `dom-events-model.md` | Phase 5 §5.2/§5.3/§5.4 — the framework-agnostic `CustomEvent` contract, and how a contract's behavior/accessibility claims are verified against rendered DOM output rather than framework internals. |

### Other platforms — consulted when Q8 includes that platform

Q8 (Platform) is multi-select; Phase 3/4 run once per selection, and for any platform other than Web, that run consults the matching file below instead of the web-specific tables — see each file's "Component / structure resolution" and "Accessibility API" sections.

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

## Phase 0: Reference freshness check

Run this once, before Phase 1, every time the skill starts. It is a cheap check that only occasionally does real work — most runs, it should cost nothing.

1. For every file under `references/`, read its `Last verified:` date. Comparing dates is local and free — do this for all 14 files unconditionally.
2. If today is less than **90 days** after that date, the file isn't due. Skip it — no network access, nothing to report.
3. If 90 days or more have passed **and** web access is available in the current environment: fetch the URL(s) the file cites in its "Source of authority" line and compare against what the file currently says.
   - **`platform-differences.md` is the one exception** — it aggregates the other 13 files rather than citing an external URL itself, so "checking" it means confirming it still agrees with whichever of those files were also due this run, not fetching anything.
   - **No material change** (the spec's version/status is the same, nothing the file describes has been renamed, deprecated, or superseded): update that file's `Last verified:` date to today and move on silently — no need to mention this to the user.
   - **Material change found** (a new spec version, a deprecated/renamed API or attribute, a new pattern that supersedes what's documented): stop and tell the user what changed and which file it affects, before proceeding to Phase 1. Ask whether to update the reference file now, defer it, or continue this session with the existing content. Never rewrite a reference file's content on your own initiative — these are curated explanations, not a scrape of the spec, and a drive-by edit from an automated check is exactly the kind of unreviewed change that principle exists to prevent.
4. If web access isn't available in the current environment, skip step 3 entirely for this run. Only mention the skip if at least one file was actually due (don't report "nothing to check" as if it were a finding) — and never block the interview from starting because a freshness check couldn't run.

This check must never be the reason someone can't generate a contract. A skipped, deferred, or inconclusive check is always a reason to proceed with what's already there, not to stop.

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

The interview order mirrors the contract: Overview (Q1–Q2) → Structure (Q3–Q4) → Properties (Q5–Q6) → Behavior (Q7–Q8) → Appearance (Q9) → Output (Q10).

---

**Q1 — Name & purpose**
header: "§1 Overview"
question: "What's it called, and what problem does it solve? One sentence is enough. (9 questions left)"
Open text.

**Q2 — Action** *(drives semantic markup derivation in Phase 3)*
header: "§1 Overview"
question: "What does it do? Pick all that apply. (8 questions left)"
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

**Q3 — Composition**
header: "§2 Structure"
question: "Does it stand alone, or does it hold other components inside? (7 questions left)"
Single-select:
- "Stands alone"
- "Holds other components inside"
If "Holds other components" → open text follow-up:
header: "§2 Structure"
question: "Which components does it hold? Do any of them already have contracts?"

**Q4 — Parts**
header: "§2 Structure"
question: "What are its visible parts? Name each one and say what it's for — showing content, or doing something. (6 questions left)"
Open text. Add in the description: Examples of content parts: label, image, badge, description. Examples of action parts: close button, chevron, checkbox, spinner.

**Q5 — Visual styles**
header: "§3 Properties"
question: "Which visual styles does it have? Check the ones your system uses. If your system calls them something different, type the correct name in the field below. (5 questions left)"

Before calling AskUserQuestion for Q5, derive 3–6 likely visual style variants from the component name and purpose given in Q1. Use them as the multi-select options. The list should reflect common conventions for that component type. Examples:
- Button-type → Filled / Outlined / Ghost / Text / Destructive
- Navigation-type → Underline / Fill / Pill / Bordered
- Badge / Tag / Chip → Filled / Subtle / Outline / Dot
- Input / Field → Default / Floating label / Inline / Borderless
- Alert / Banner / Toast → Filled / Subtle / Left-bordered / Outline
- Card → Default / Elevated / Outlined / Ghost
- List item / Row → Default / Compact / Highlighted / Disabled

Unchecked options are not part of this component's contract. The built-in free-text field handles any style not on the list, or renames one that is.
Multi-select: [derived from Q1]

**Q6 — Layout flexibility**
header: "§3 Properties"
question: "Can its layout change? Pick all that apply. (4 questions left)"
Multi-select:
- "Direction flips (horizontal ↔ vertical)"
- "Size grows or shrinks"
- "Alignment shifts (left / centre / right)"
- "Has a compact or overflow mode"
- "Adapts to the space available"
If "Adapts to the space available" → open text follow-up:
header: "§3 Properties"
question: "What changes when space is tight? What does your design system call those conditions?"

**Q7 — Interaction** *(feeds §5 Behavior — events, state machine)*
header: "§5 Behavior"
question: "How does the user interact with it? Pick all that apply. (3 questions left)"
Multi-select:
- "Click or tap"
- "Choose from a list or set of options"
- "Drag to reorder or resize"
- "Scroll or swipe"
- "No direct interaction — it updates on its own"

If "Choose from a list" → single-select follow-up:
header: "§5 Behavior"
question: "How many options can be selected at once?"
  - "Just one"
  - "Multiple"
Then single-select follow-up:
header: "§5 Behavior"
question: "Is the list always visible, or does it open on demand?"
  - "Always visible"
  - "Opens as a dropdown"

Never assume the HTML element or ARIA role from the component name. Always derive from Q2 (action) and Q7 (interaction).

**Q8 — Platform**
header: "§5 Behavior"
question: "Which platform(s) will this be used on? Select all that apply. (2 questions left)"
Multi-select:
- "Web"
- "iOS"
- "Android"
- "macOS"
- "Windows"
- "Linux"

This answer drives which reference file(s) Phase 3/4 consult and how many contract files Phase 5 writes — one per platform selected, plus one shared file. It is not just a behavior note.

If two or more platforms are selected → open text follow-up:
header: "§5 Behavior"
question: "Does anything work differently across these platforms — behavior or gestures specifically, not structure or accessibility (those are derived automatically per platform)? Only describe what changes; leave blank if nothing does."

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

---

### Path C: Description only

Leave the token map as pending and note it clearly in the contract:

> Token map pending — no design source was provided. Supply a Figma node URL, Storybook story URL, or CSS/token file to complete this section.

---

## Phase 3: Derive structure (internal — not asked)

**Run this phase once per platform selected in Q8.** The same Q2 (action) and Q7 (interaction) answers feed every run — what changes is which table resolves them to a concrete structure. Never infer the element/control from the component's name — the same visual form can require completely different structure depending on what the component actually does, and that holds on every platform.

- **Web** → use the decision table below.
- **iOS / Android / macOS / Windows / Linux** → use the "Component / structure resolution" table in that platform's reference file instead of the table below (`references/ios/ios-hig-accessibility.md`, `references/android/android-material-accessibility.md`, `references/macos/macos-hig-accessibility.md`, `references/windows/windows-ui-automation.md`, `references/linux/linux-atspi-accessibility.md`). Same Q2/Q7 inputs, that platform's native vocabulary as output.

Each platform's result becomes that platform's §2 Structure (see Phase 5's platform contract template). The subsections below the web table — Setting cardinality, Setting order — are not web-specific; apply them once per platform too, since composition zones and their positioning exist on every platform even though the underlying mechanism differs.

### Decision table (Web)

Use the combination of Q2 (action) and Q7 (interaction) to pick the right element.

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

Use the user's answers from Q4 to fill the Cardinality column. When the user hasn't specified a maximum, use judgment:
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

**Run this phase once per platform selected in Q8**, same as Phase 3 — derive from the interview answers and each platform's Phase 3 structure decision. Do not ask the designer about ARIA, UI Automation patterns, AT-SPI roles, or keyboard/gesture navigation directly.

- **Web** → the ARIA-specific subsections below.
- **iOS / Android / macOS / Windows / Linux** → that platform's reference file, "Accessibility API" section, for the role/state/trait model, plus its layout/motion sections for focus-equivalent and reduced-motion behavior. There is no separate decision table to duplicate here — the platform files already state what each requires.

The web subsections below cover the common cases inline. For the patterns not in Phase 3's decision table (combobox, menu, tooltip, tree, slider, grid, accordion) get the full attribute and keyboard set from `references/web/wai-aria-patterns.md` rather than approximating. `references/web/wcag-mapping.md` grounds a requirement in the WCAG success criterion it satisfies when that's useful context (e.g., for an audited system) — this is optional citation, derived silently, never a question put to the designer.

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

With all phases complete, write the contract. Fill every section from what you now know — never leave a placeholder unless the user explicitly said information is unavailable.

**Every component produces one shared file plus one file per platform selected in Q8 — always this shape, even when only one platform was selected.** A single-platform component still gets a shared file and one platform file, not one flat file. This is deliberate: it means adding a second platform to an existing component later is purely additive (write one more platform file) rather than a restructuring of what's already there, and it means there's exactly one file shape to automate against regardless of how many platforms a given component targets.

The split is by whole numbered section, never a section split across files:
- **Shared file** (`[ComponentName].md`) — §1 Overview, §3 Properties, §4 Appearance. Nothing here varies by platform enough to justify per-platform copies — see the exception note under §4.1 below.
- **Platform file** (`[ComponentName].[Platform].md`, one per Q8 selection) — §2 Structure, §5 Behavior, §6 Accessibility. These are the sections Phase 3/4 derived per platform; each platform file is that platform's own complete answer for these three sections, not a diff against another platform's file.

**Writing principles:**

**Purpose statement (§1)** — one sentence. What the component is and what need it addresses. Not a description of its parts.

**Ownership** — state clearly whether each property, behaviour, or token is owned by this component or delegated to a child. Use "delegated to [child]", "see [child] contract", "[child] manages this". Reference a child by component name only, e.g. "delegated to Icon" — never name a specific platform file. Whoever is reading a given platform file resolves "Icon" to `Icon.[SamePlatform].md` themselves, following the same naming convention; the contract shouldn't hardcode that resolution.

**Composite shells** — the shell owns: the root element, hard structural rules (e.g., "minimum 2 tabs required"), and platform-specific chrome (e.g., arrow navigation buttons). Everything else belongs to the sub-components. This applies per platform file — a shell's iOS file states its iOS-specific chrome, its Android file states Android's, etc.

**Cross-referencing the shared file from a platform file** — open every platform file with a one-line pointer back to the shared file, e.g.: `> Shared Overview, Properties, and Appearance: see [ComponentName].md.` Don't restate or summarize shared content inside a platform file; point to it.

**Raw vs. token-bound values** — never invent token names. If no token was found, document the raw value and note it as unbound.

**Three distinct prop categories — never mix them:**
- **Layout Props (§3.1)** — control spatial arrangement via CSS; no DOM change, no token reference.
- **Visual Variants (§3.2)** — switch which visual style is applied; not token values themselves.
- **Behavioral Props (§3.3)** — configure what the component does; states, feature flags, operational options.

When the user answered yes to any item in Q6 (layout flexibility), populate §3.1. If they answered "None of the above", omit §3.1.

**§4.1 Interaction States is shared, with one exception worth naming explicitly:** hover is not a state every platform has — touch-only platforms (iOS, Android without a pointer) have no hover equivalent. List it in the shared file's §4.1 anyway if any selected platform supports it, but note which platforms it applies to rather than implying it's universal just because the section lives in the shared file.

**§5.1 Interactions lives entirely in each platform file — there is no cross-platform delta table anymore.** Each platform file states its own interactions in full. When two platforms genuinely behave the same way, it's fine for their §5.1 tables to say the same thing in each file — that small duplication is the deliberate trade-off for keeping every platform file a complete, standalone answer rather than requiring a reader to cross-reference another platform's file to understand this one. Q8's "does anything work differently" follow-up is what surfaces the cases where they don't say the same thing.

**§5.2 State Machine** — same duplication principle as §5.1: write it fully in each platform file even if the states and transitions are identical across platforms. If the component has no internal state, say so in each file rather than pointing to another platform's file for the answer.

**Adaptive layout (§2.3) is container-relative, never viewport-relative — and the mechanism is platform-specific:**
§2.3 maps available space conditions to layout configurations. Reference §3.1 props by name when describing what changes (§3.1 is in the shared file; §2.3 is in the platform file — this is a normal cross-file reference, not a violation of the file split). Omit §2.3 entirely if the component's layout is identical regardless of available space. Web's version of this is CSS Container Queries (`references/web/css-layout-and-interaction.md`); other platforms have their own mechanism — see `references/platform-differences.md` for the comparison, then the specific platform file.

**Events Emitted/Received (§5.3/§5.4) — ground them in whichever platform file they're in:**
For a **Web** platform file, record event names as they'd appear in `addEventListener`, not a framework's handler-prop convention — see `references/web/dom-events-model.md` for the `CustomEvent` contract and why this keeps the file verifiable against rendered output regardless of implementation framework. For a native platform file, describe the event in that platform's own native idiom instead (a delegate callback, a closure parameter, an emitted signal) — there isn't yet a dedicated reference file for native event models; use plain, unambiguous language rather than forcing DOM vocabulary onto a platform that doesn't have DOM events.

---

### Shared contract template

Written once per component, regardless of how many platforms it targets. File name: `[ComponentName].md`.

```markdown
# Component Contract: [Name]

> **Version:** 1.0
> **Status:** Draft
> **Last updated:** [YYYY-MM-DD]
> **Platforms:** [list every platform selected in Q8, e.g. Web, iOS, Android — each has its own `[Name].[Platform].md` alongside this file]

---

## 1. Overview

[One sentence: what the component is and what need it solves. Follow with one short paragraph on what it owns and what it deliberately delegates.]

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

[Visual states on the component's root element: default, hover, focus, active, disabled, error, selected. Note which are driven by Behavioral Props and which are pure CSS responses to user input. If all states are owned by children, say so.]

### 4.2 Layout Policy

[Fixed layout rules always enforced — not configurable via props. Examples: a max-width constraint, clip behaviour. Omit if none.]

### 4.3 Design Tokens

#### 4.3.1 Token Strategy

[What tier of tokens this component uses, which properties it owns, which are delegated to children.]

#### 4.3.2 Token Map

[Source: Figma / Storybook / tokens.json / description-only — state clearly]

[Token-bound properties:]
| Property | Token |
|----------|-------|

[Unbound properties:]
| Property | Raw value |
|----------|-----------|

[No source provided:]
> Token map pending — supply a Figma node URL, Storybook URL, or CSS/token file to complete this section.
```

---

### Platform contract template

Written once per platform selected in Q8. File name: `[ComponentName].[Platform].md` (e.g. `Modal.iOS.md`, `Modal.Web.md`) — `[Platform]` is exactly one of the six Q8 option labels (Web, iOS, Android, macOS, Windows, Linux).

```markdown
# Component Contract: [Name] — [Platform]

> Shared Overview, Properties, and Appearance: see [Name].md.

---

## 2. Structure

### 2.1 Semantic Markup

| Role | Tag / Role | ARIA | Required | Notes |
|------|-----------|------|----------|-------|

> **Root element choice:** [If multiple valid roots exist, explain when to use each.]

### 2.2 Composition Zones

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
[One row per visible part. Cover all named parts from Q4.]

### 2.3 Adaptive Layout

> How the component's layout changes based on available space. Conditions are named by the design system — do not use pixel values or media query syntax.
>
> Omit this section if layout is identical regardless of available space.

| Condition | Layout prop changes | Zone position changes |
|-----------|--------------------|-----------------------|

---

## 5. Behavior

### 5.1 Interactions

[This platform's interactions in full — not a diff against another platform's file. If Q8's follow-up confirmed a difference from another platform, that's where it shows up; if not, it's fine for this table to match another platform's table exactly.]

| Event | Source | Action |
|-------|--------|--------|

### 5.2 State Machine

[Internal states and transitions, written out in full here even if identical to another platform's file. If the component has no internal state: "None — [what manages state instead]."]

### 5.3 Events Emitted

[Events this component emits to its parent. If none: "None."]

### 5.4 Events Received

[Events or prop changes this component responds to from its parent or environment. If none: "None."]

---

## 6. Accessibility

### 6.1 ARIA Roles & Attributes

| Element | Tag / Role | Attributes | Notes |
|---------|-----------|------------|-------|

### 6.2 Keyboard Navigation

| Key | Behaviour |
|-----|-----------|

### 6.3 Focus Management

- **Focus trap:** [Yes — explain / No]
- **Tab order:** [Expected focus sequence]
- **On open:** [Where focus moves when the component opens, if applicable]
- **On close:** [Where focus returns when the component closes, if applicable]

### 6.4 Screen Reader Expectations

- **On reach:** [What is announced when the component first receives focus]
- **On activation:** [What is announced when the user triggers it]
- **On state change:** [What is announced when state changes or content updates]
- **On error / empty:** [What is announced for error or empty states]
```

---

## Phase 6: JSON schema generation (if requested)

Generate one `.schema.json` for the component regardless of how many platforms it targets — schema describes §3 Properties, which lives in the shared file and doesn't vary by platform. Never add validation rules not stated in the contract. See `references/json-schema-draft-07.md` for the full keyword reference, what NOT to add on your own initiative, and the Draft 07 vs. 2020-12 decision this skill deliberately pins.

The one exception is §2.2 Zones, used below for child/array shape — that section now lives in each platform file, not the shared one. Composition zones (what parts exist, how many, what they accept) are expected to be the same idea regardless of platform even though §2.1/§2.3 (the markup and adaptive-layout mechanism) aren't. Before generating, confirm §2.2 actually agrees across every selected platform's file; if it doesn't, don't silently pick one — surface the discrepancy instead of guessing which platform's zone structure the schema should follow.

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

### Schema rules

- JSON Schema Draft 07 (`"$schema": "http://json-schema.org/draft-07/schema#"`)
- `"$id"`: component name in kebab-case
- `"title"`: component display name
- `"description"` on every property, copied from the contract
- Enum props: `"type": "string"` + `"enum": [...]`
- Boolean props: `"type": "boolean"`
- Number props: `"type": "number"` with `"minimum"` / `"maximum"` only if the contract states bounds
- Child arrays: `"type": "array"` + `"minItems"` where stated + `"items": { "$ref": "[name]" }` in $ref mode, or inline object in inline mode

---

## Output

Write one shared file, `[ComponentName].md` (PascalCase), plus one platform file per platform selected in Q8, `[ComponentName].[Platform].md` — always this shape, even for a single platform. If a schema was requested, also write one `[ComponentName].schema.json` to the same directory (one file regardless of platform count — see Phase 6). Ask for the target directory if the user has not specified one. Confirm all file paths after writing, grouped clearly as shared vs. per-platform so the output structure is obvious at a glance.
