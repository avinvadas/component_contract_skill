---
name: component-contract
description: Creates structured component contract markdown files for design systems, and optionally generates a JSON schema for prop validation. A component contract is a formal specification that documents a UI component's semantic markup, design tokens, behavior, and accessibility requirements. Use this skill whenever a user wants to create a new component spec or contract, document a UI component formally, generate a component contract md file, specify the structure or behavior or tokens of a component, audit what tokens a component uses, or generate a JSON schema for a component. Also trigger when the user says things like "create a contract for X", "document this component", "write up the spec for [component name]", "add [component] to the design system contracts", "I need a component contract", or "generate a schema for this component". If the user mentions a Figma link, a Storybook URL, or a coded reference alongside a component name or design system task, this skill almost certainly applies.
---

## What this skill produces

A complete component contract markdown file capturing the design intent of a UI component across six sections:

1. **Purpose** — one sentence: what the component is and what need it solves
2. **Structure** — the correct semantic HTML, including required and optional children
3. **Properties** — what the component exposes, organized by layout (CSS/flow), style (visual variants), and behavior (states, flags)
4. **Appearance** — which design tokens are applied
5. **Behavior** — how it acts, what events it dispatches, what events it responds to
6. **Accessibility** — focus traps, ARIA, keyboard navigation

The person using this skill does not need to know HTML, ARIA, or accessibility patterns. The skill derives all technical decisions from plain-language answers about the component's purpose and how users interact with it.

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
question: "Where will people use it? (2 questions left)"
Single-select:
- "Web only"
- "Mobile app only"
- "Web and mobile"
- "Desktop app"
If multi-platform → single-select follow-up:
header: "§5 Behavior"
question: "Does anything work differently on mobile vs desktop?"
  - "No — same everywhere"
  - "Yes — some things differ"
  If yes → open text follow-up:
  header: "§5 Behavior"
  question: "What's different? Only describe what changes."

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

Inspect only the root element of the component — not its children (those have their own contracts).

For each property, hover over the small icon next to the value field and read the tooltip:
- **"Apply variable"** — no token is bound; record the raw numeric or hex value
- **A named token** (e.g., `color-surface-default`, `--ds-color-surface`) — record it exactly as shown

Check in this order: Auto layout gap → padding (all sides) → corner radius → fill (background) → stroke (color, width, position) → opacity → any fixed width or height.

Never infer or invent token names. "Apply variable" means unbound — record the raw value only.

**Navigation:** Open the URL (the node should be pre-selected), scroll the right-side Design panel, work top to bottom.

---

### Path B: Coded reference (Storybook, CSS, tokens file)

- **Storybook**: Navigate to the story URL. Open the Docs tab or Controls panel. Look for CSS custom property references like `var(--token-name)` in the story source or component styles.
- **CSS / SCSS / token file**: Read the file. Extract custom property declarations (`--token-name: value`) or token object keys. Note which tier they belong to (primitive / semantic / component).

For every property: record `property | token name | resolved value (if visible)`. Hardcoded values with no token reference = raw. Note the source in the token map.

---

### Path C: Description only

Leave the token map as pending and note it clearly in the contract:

> Token map pending — no design source was provided. Supply a Figma node URL, Storybook story URL, or CSS/token file to complete this section.

---

## Phase 3: Derive semantic markup (internal — not asked)

Derive all HTML elements and ARIA roles strictly from Q2 (action) and Q7 (interaction) answers. Never infer the element from the component's name — the same visual form can require completely different elements depending on what the component actually does.

### Decision table

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

---

## Phase 4: Derive accessibility (internal — not asked)

Derive all accessibility requirements from the interview answers and the markup decision. Do not ask the designer about ARIA or keyboard navigation.

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

### Deriving screen reader expectations

- **On first reach**: announce role, name, and current state
- **On activation**: announce the result
- **On async update**: the `aria-live` region announces changes without requiring focus to move
- **On state change**: announce the new state
- **Empty states**: must be inside any live region so they are announced when content updates to empty

---

## Phase 5: Generate the contract

With all phases complete, write the full contract. Fill every section from what you now know — never leave a placeholder unless the user explicitly said information is unavailable.

**Writing principles:**

**Purpose statement (§1)** — one sentence. What the component is and what need it addresses. Not a description of its parts.

**Ownership** — state clearly whether each property, behaviour, or token is owned by this component or delegated to a child. Use "delegated to [child]", "see [child] contract", "[child] manages this".

**Composite shells** — the shell owns: the root element, hard structural rules (e.g., "minimum 2 tabs required"), and platform-specific chrome (e.g., arrow navigation buttons). Everything else belongs to the sub-components.

**Raw vs. token-bound values** — never invent token names. If no token was found, document the raw value and note it as unbound.

**Three distinct prop categories — never mix them:**
- **Layout Props (§3.1)** — control spatial arrangement via CSS; no DOM change, no token reference.
- **Visual Variants (§3.2)** — switch which visual style is applied; not token values themselves.
- **Behavioral Props (§3.3)** — configure what the component does; states, feature flags, operational options.

When the user answered yes to any item in Q6 (layout flexibility), populate §3.1. If they answered "None of the above", omit §3.1.

**Interaction delta (§5.1) — no delta, no split:**
§5.1 uses a single table by default. Platform subsections appear only when Q8 confirmed an actual difference in affordances or gestures. When a delta exists, document shared behaviors once as a preamble note, then use subsections only for what genuinely differs.

**Adaptive layout (§2.3) is container-relative, never viewport-relative:**
§2.3 maps available space conditions to layout configurations. Reference §3.1 props by name when describing what changes. Omit §2.3 entirely if the component's layout is identical regardless of available space.

---

### Contract template

```markdown
# Component Contract: [Name]

> **Version:** 1.0
> **Status:** Draft
> **Last updated:** [YYYY-MM-DD]

---

## 1. Overview

[One sentence: what the component is and what need it solves. Follow with one short paragraph on what it owns and what it deliberately delegates.]

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

---

## 5. Behavior

### 5.1 Interactions

[Single table by default. Split into platform subsections only when Q8 confirmed a real interaction difference across platforms. When a split is needed, list shared behaviors once as a preamble note; subsections cover only what differs.]

| Event | Source | Action |
|-------|--------|--------|

### 5.2 State Machine

[Internal states and transitions. If the component has no internal state: "None — [what manages state instead]."]

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

Generate a `.schema.json` derived directly from the contract. Never add validation rules not stated in the contract.

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

Write the contract as `[ComponentName].md` (PascalCase). If a schema was requested, also write `[ComponentName].schema.json` to the same directory. Ask for the target directory if the user has not specified one. Confirm all file paths after writing.
