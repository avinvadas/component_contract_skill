---
name: component-contract
description: Creates structured component contract markdown files for design systems, and optionally generates a JSON schema for prop validation. A component contract is a formal specification that documents a UI component's semantic markup, design tokens, behavior, and accessibility requirements. Use this skill whenever a user wants to create a new component spec or contract, document a UI component formally, generate a component contract md file, specify the structure or behavior or tokens of a component, audit what tokens a component uses, or generate a JSON schema for a component. Also trigger when the user says things like "create a contract for X", "document this component", "write up the spec for [component name]", "add [component] to the design system contracts", "I need a component contract", or "generate a schema for this component". If the user mentions a Figma link, a Storybook URL, or a coded reference alongside a component name or design system task, this skill almost certainly applies.
---

## What this skill produces

A complete component contract markdown file — six sections covering structure, tokens, behavior, and accessibility — and optionally a companion JSON schema for prop validation. The person using this skill does not need to know HTML, ARIA, or accessibility patterns. The skill derives all technical decisions from plain-language answers about what the component does and how users interact with it.

The contract distinguishes three variant layers that are often conflated:
- **Layout variants** — CSS-structural flexibility: direction, sizing, alignment, density, overflow
- **Visual variants** — style switching: size, emphasis, filled/outlined, etc.
- **Design tokens** — named token values from the design system

---

## Phase 1: Designer interview

Ask each question using the AskUserQuestion tool. One question per tool call — wait for the answer before calling the next. Use selectable options wherever the answer space is bounded; fall back to open text only when the answer is inherently freeform (name, purpose, zone description, token prefix).

For every question, set the `header` field to the step indicator: `Q1 / 14`, `Q2 / 14`, etc. (max 12 chars — this fits). Start the `question` text with a filled progress bar on its own line, then the question title and body. Use this exact format for the progress bar — scale the filled blocks (█) to the current step out of total:

```
█████░░░░░░░░░  3 of 14 — Composition
```

Use 15 total characters for the bar (█ for done, ░ for remaining), then ` N of Total — Question title`.

After each answer, acknowledge it in one sentence, then immediately call AskUserQuestion for the next question. No extra commentary between questions.

Skip Q10 if Q9 is single-platform (total becomes 13 — adjust bar and counter accordingly). Once all answers are collected, proceed to Phase 2.

**Q1 — Name**
Open text. Ask: "What is this component called?"

**Q2 — Purpose**
Open text. Ask: "In one sentence — what does it do, and where in the UI does it appear?"

**Q3 — Composition**
Single-select. Options:
- "Standalone — it's a self-contained element with its own content"
- "Composite shell — it wraps other named components (e.g. a tab bar + panels)"
If composite: follow up with open text asking which sub-components it contains and whether those already have contracts.

**Q4 — Zones**
Open text. Ask: "What distinct regions or elements make up this component? For each one, describe: (1) is it there to show content or to drive behaviour / navigation? (2) how many can appear? (3) is its position always fixed or can it move?"
Provide examples inline: content zones = label, description, thumbnail, badge count; interaction zones = close button, chevron, spinner, nav arrows, checkbox.

**Q5 — Variants**
Open text. Ask: "Does it come in different sizes or visual styles? List them if so (e.g. sm / md / lg, filled / outlined, primary / secondary). If not, say none."

**Q6 — Layout flexibility**
Multi-select. Header: "Layout flexibility". Ask: "Can the component arrange itself or its children differently depending on context? Select all that apply."
Options:
- "Direction can flip (e.g. horizontal ↔ vertical)"
- "Sizing can change (grows / shrinks / fixed)"
- "Alignment can change (left / centre / right)"
- "Has density or overflow modes (compact, scroll, wrap…)"
The tool automatically appends an "Other" field — do not add one manually.

**Q7 — Adaptive layout**
Single-select. Options:
- "No — layout is identical regardless of available space"
- "Yes — layout changes based on container space"
If yes: follow up with open text asking what changes and how the design system names the space conditions.

**Q8 — Interactions**
Multi-select. Header: "Interactions". Ask: "What can a user do with this component? Select all that apply."
Options:
- "Nothing — display only"
- "Click / tap to navigate (link)"
- "Click / tap to trigger an action (button)"
- "Select one or more options from it"
- "Swipe or scroll through content inside it"
- "Drag or reorder items within it"
The tool automatically appends an "Other" field — do not add one manually.

**Q9 — Platform**
Single-select. Options:
- "Web browser only"
- "Mobile app only (iOS / Android)"
- "Both web and mobile"
- "Desktop application"

**Q10 — Interaction delta** *(only if Q9 = multi-platform)*
Single-select. Options:
- "No — interactions are identical across platforms"
- "Yes — some interactions or affordances differ by platform"
If yes: follow up with open text asking what differs (only what is different — shared behaviours need not be repeated).

**Q11 — States**
Multi-select. Header: "States". Ask: "Beyond its default appearance, which states does this component have?"
Options:
- "Loading / in-progress"
- "Error or validation failure"
- "Disabled / unavailable"
- "Selected / active / checked"
- "Empty (no content to show)"
The tool automatically appends an "Other" field — do not add one manually.

**Q12 — Token source**
Single-select. Header: "Token source". Options:
- "Figma link — I'll share a URL with a node-id"
- "Coded reference — Storybook URL, CSS file, or tokens.json"
- "No source — mark token map as pending"
If Figma or coded: follow up with open text to collect the URL or file path.

**Q13 — Token naming**
Open text. Ask: "What prefix or pattern does your design system use for tokens? (e.g. `ds-`, `--color-`, `color-`, `sys.color.`)"

**Q14 — JSON schema**
Single-select. Options:
- "No schema needed"
- "Yes — generate a Tabs.schema.json (JSON Schema Draft 07)"
If yes and the component has sub-components: follow up asking whether sub-component zones should use `$ref` references or inline shapes.

Wait for all answers before proceeding to Phase 2.

---

## Phase 2: Token extraction

### Path A: Figma URL

Inspect only the root element of the component — not its children (those have their own contracts).

For each property, hover over the small icon next to the value field and read the tooltip:
- **"Apply variable"** — no token is bound; record the raw numeric or hex value
- **A named token** (e.g., `color-surface-default`, `--ds-color-surface`) — record it exactly as shown using your system's naming convention

Check in this order: Auto layout gap → padding (all sides) → corner radius → fill (background) → stroke (color, width, position) → opacity → any fixed width or height.

Never infer or invent token names. "Apply variable" means unbound — record the raw value only.

**Navigation:** Open the URL (the node should be pre-selected), scroll the right-side Design panel, work top to bottom.

---

### Path B: Coded reference (Storybook, CSS, tokens file)

- **Storybook**: Navigate to the story URL. Open the Docs tab or Controls panel. Look for CSS custom property references like `var(--token-name)` in the story source or component styles.
- **CSS / SCSS / token file**: Read the file. Extract custom property declarations (`--token-name: value`) or token object keys. Note which tier they belong to (primitive / semantic / component).

For every property: record `property | token name | resolved value (if visible)`. Hardcoded values with no token reference = raw, same as "Apply variable". Note the source in the token map.

---

### Path C: Description only

Leave the token map as pending and note it clearly in the contract:

> Token map pending — no design source was provided. Supply a Figma node URL, Storybook story URL, or CSS/token file to complete this section.

---

## Phase 3: Derive semantic markup (internal — not asked)

Based on the interview answers, choose the correct HTML element(s) and ARIA roles. The designer does not need to know this logic — apply it silently and document the result in the contract.

### Decision logic

**Is it display-only with no interaction?**
→ Use the most semantically appropriate element for its content role:
- Page region with a heading: `<section aria-labelledby="...">` or `<aside>`
- Primary content area: `<main>`
- Navigation group: `<nav>`
- Plain container: `<div>`

**Does clicking/tapping take the user somewhere (a destination)?**
→ `<a href="...">` — always an anchor, never a button

**Does clicking/tapping trigger an action (submit, open, close, confirm, toggle)?**
→ `<button type="button">` (or `type="submit"` if it submits a form)
- Never use `<div>` or `<span>` with an onClick for this purpose

**Does the user type into it?**
→ `<input>`, `<textarea>`, or `<select>` depending on the input type; pair with `<label>`

**Does the user select one from a set of options?**
→ Radio group: `<fieldset>` + `<legend>` + `<input type="radio">` items
→ Single toggle: `<input type="checkbox">` or `<button aria-pressed="true/false">`
→ Dropdown: `<select>` or a custom listbox with `role="listbox"` + `role="option"`

**Is it a tab interface?**
→ `role="tablist"` on the container, `role="tab"` on each tab, `role="tabpanel"` on each panel

**Does it open a modal or overlay that blocks the rest of the page?**
→ `<dialog>` (preferred) or `role="dialog"` + `aria-modal="true"`

**Is it a feed or list of items?**
→ `<ul>` + `<li>` (unordered, default)
→ `<ol>` + `<li>` only when the order is semantically meaningful (rankings, steps)
→ `<menu>` only when items are interactive commands

**Is it a composite shell wrapping named sub-components?**
→ The root element applies to the shell only; document sub-component markup in their own contracts

**When multiple root elements are valid**, document all options and the condition for choosing each.

### Classifying zones (for §2.2)

Use the answers from interview Q4 to assign each zone a type. When in doubt, apply this test: **could removing this zone break the component's behaviour or mislead the user about its state?** If yes → Interaction. If no → Content.

| If the zone… | Type |
|---|---|
| Shows a text label, description, image, or data | Content |
| Shows an icon that represents the subject matter | Content |
| Indicates a component state (expanded, loading, selected, error) | Interaction |
| Triggers or confirms an action (close, submit, clear, navigate) | Interaction |
| Affords navigation within the component (prev/next arrows, step dots) | Interaction |
| Is a selection control embedded in the component (checkbox, radio, toggle) | Interaction |
| Is a drag handle or reorder affordance | Interaction |

A zone that starts as Interaction cannot be redeclared as Content by a white-label implementation, even if the visual element looks similar. Document this in the Compliance rule column.

### Setting cardinality

Use the user's answers about "how many" to fill the Cardinality column. When the user hasn't specified a maximum, use judgment:
- A label, title, or primary description → `1` (singular by design; duplicating it would break legibility)
- A leading or trailing icon → `0–1` (optional but not repeatable)
- Action buttons in a footer → `1–3` or `0–3` depending on whether at least one is required; cap at a sensible maximum if the design implies one
- Tags, chips, or list items → `0+` or `1+` (repeating zones with no hard upper limit)
- Navigation steps or tabs → state the minimum if known (e.g., `2+` for tabs, since a single-tab interface is not valid)

If the user hasn't answered how many are allowed and it isn't derivable from the component's purpose, note it as `1+` and flag it for confirmation.

### Setting order

Mark a zone as `Fixed` when moving it would break the user's expectation of where that affordance lives, or when its position relative to another zone is load-bearing for meaning or accessibility. Common fixed positions:

- Close / dismiss buttons → `Fixed — top-right` (universal convention; users expect it there)
- State indicators (expand chevron, selection checkbox) → `Fixed — precedes label` or `Fixed — follows label` depending on the design
- Navigation controls (prev/next arrows) → `Fixed — flanks content` (left and right of the slide area)
- Primary action in a footer → `Fixed — rightmost action` (common confirmation dialog convention)

Mark a zone as `Flexible` when its position is a layout preference rather than a meaning-bearing rule — e.g., a thumbnail image that could appear above or beside the text depending on the layout variant, or a metadata line that could move between title and body.

---

## Phase 4: Derive accessibility (internal — not asked)

Derive all accessibility requirements from the interview answers and the markup decision. Do not ask the designer about ARIA or keyboard navigation. Own these decisions and document them fully.

### Deriving ARIA roles and attributes

- The semantic HTML element provides the base role implicitly — add explicit `role=` only when overriding or when the element alone is insufficient
- Named landmarks (`<section>`, `<nav>`, `<main>`, `<aside>`) require an accessible name: `aria-label="..."` or `aria-labelledby="[id]"`
- Interactive elements that change state need state attributes: `aria-pressed` (toggle buttons), `aria-expanded` (disclosure), `aria-selected` (tabs/options), `aria-checked` (checkboxes), `aria-disabled` (disabled controls)
- When content updates asynchronously (tab switch, filter change, live feed): add `aria-live="polite"` on the updating region
- Dialogs: `aria-modal="true"`, `aria-labelledby` pointing to the dialog's heading

### Deriving keyboard navigation

| Interaction type (from interview Q8) | Required keyboard behaviour |
|---|---|
| Display only | No keyboard interaction required |
| Link (goes somewhere) | `Enter` activates |
| Button (triggers action) | `Enter` and `Space` both activate |
| Text input | Standard text editing keys; `Tab` moves focus in/out |
| Single select / toggle | `Space` toggles; `Enter` confirms if in a form |
| Multi-select options | `ArrowUp` / `ArrowDown` to move, `Space` to select, `Enter` to confirm |
| Tab interface | `ArrowLeft` / `ArrowRight` between tabs; `Tab` moves into the panel |
| Swipeable / scrollable list | `ArrowLeft` / `ArrowRight` (or `ArrowUp` / `ArrowDown`) to navigate items |
| Modal / dialog | `Tab` / `Shift+Tab` cycle within the dialog; `Escape` closes |
| Drag / reorder | `Space` to grab, `Arrow` keys to move, `Space` or `Enter` to drop, `Escape` to cancel |

### Deriving focus management

- **No special focus management needed**: display-only components, buttons, links, inputs — focus follows natural DOM tab order, the component is fully transparent to traversal
- **Focus trap required**: modal dialogs and overlays that block the rest of the page — focus must cycle within the dialog; nothing outside should be reachable while it is open
- **Focus move on open**: when a panel or disclosure opens programmatically, move focus to the first interactive element inside it (or the panel container with `tabindex="-1"` if there are no interactive children)
- **Focus restore on close**: when a dialog or panel closes, return focus to the element that triggered it

### Deriving screen reader expectations

- **On first reach**: announce the element's role, name, and current state (e.g., "Navigation, main menu", "Button, Add to cart", "Checkbox, Subscribe to newsletter, unchecked")
- **On activation**: announce the result (e.g., "Dialog opened", "Menu expanded", "Item removed")
- **On async content update**: the `aria-live` region announces changes without requiring focus to move (e.g., "3 results found", "Loading…", "Error: required field")
- **On state change**: announce the new state (e.g., "Checkbox, Subscribe, checked", "Tab, Overview, selected")
- **Empty states**: must be inside any live region so they are announced when the content updates to empty

---

## Phase 5: Generate the contract

With all phases complete, write the full contract. Fill every section from what you now know — never leave a placeholder unless the user explicitly said information is unavailable.

Apply the writing principles throughout:

**Ownership** — state clearly whether each property, behaviour, or token is owned by this component or delegated to a child. Use "delegated to [child]", "see [child] contract", "[child] manages this".

**Composite shells** — the shell owns: the root element, hard structural rules (e.g., "minimum 2 tabs required"), and medium-specific chrome (e.g., arrow navigation buttons). Everything else belongs to the sub-components.

**Raw vs. token-bound values** — never invent token names. If no token was found, document the raw value and note it as unbound.

**Content zones vs. Interaction zones — the type is the compliance rule:**
A zone's type is determined by *why it exists*, not by *what element it renders*. An expand/collapse chevron and a category icon are both SVGs in the leading position — but one is an Interaction zone (it communicates and drives state), the other is a Content zone (it labels the subject matter). White-label implementations may restyle Interaction zones but may not substitute them with Content elements. Document this explicitly in the Compliance rule column of §2.2, especially for zones that are visually ambiguous.

**Cardinality is a compliance boundary, not a default:**
The Cardinality column in §2.2 states the valid range — not just whether a zone is present. An implementation that renders four action buttons when the contract says `1–3` is non-compliant, even if each button is individually valid. When the upper bound matters for layout integrity or accessibility, state a maximum explicitly rather than using `0+`.

**Fixed order is non-negotiable across implementations:**
If a zone's Order is `Fixed`, its position is part of the contract — it can be restyled but not moved. This applies even in white-label contexts where the visual design is entirely custom. A close button marked `Fixed — top-right` must remain in the top-right; an implementer cannot move it to the bottom-left without forking the contract. When documenting Fixed zones, always include the position descriptor so the rule is unambiguous.

**Interaction delta (§5.1) — no delta, no split:**
§5.1 uses a single behavior table by default. Platform subsections appear only when Q10 confirmed an actual difference in affordances or gestures across platforms. When a delta exists, document shared behaviors once as a preamble note, then use subsections only for what genuinely differs. Do not duplicate shared events into both subsections — that obscures which behaviors are platform-specific and which are universal. A pointer event that works identically on desktop and mobile is shared behavior; an arrow button that only appears on desktop is a delta.

**Adaptive layout (§2.3) is container-relative, never viewport-relative:**
The component does not know what device or viewport it is on — it only knows how much space it has been given. §2.3 maps space conditions to layout configurations. Conditions are defined by the design system in terms of the available container space, not device categories or pixel breakpoints. Reference §3.1 props by name when describing what changes at each condition. Zone order changes belong here only for zones marked `Responsive` in §2.2. Omit §2.3 entirely if the component's layout is identical regardless of available space.

**Three distinct prop categories — never mix them:**
- **Layout Props (§3.1)** — control spatial arrangement via CSS; no DOM change, no token reference.
- **Visual Variants (§3.2)** — switch which visual style is applied; not token values themselves.
- **Behavioral Props (§3.3)** — configure what the component does; feature flags, state control, operational options.

When the user answered yes to any item in interview Q6 (layout flexibility), populate §3.1. If they answered "None of the above", omit §3.1 entirely.

**Medium specificity** — if interactions differ across platforms, always split into separate subsections. Never mix them in one table.

---

### Contract template

```markdown
# Component Contract: [Name]

> **Version:** 1.0
> **Status:** Draft
> **Last updated:** [YYYY-MM-DD]

---

## 1. Overview

[One paragraph: what the component does, what it is responsible for, and what it deliberately does not own.]

---

## 2. Structure

### 2.1 Semantic Markup

| Role | Tag / Role | ARIA | Required | Notes |
|------|-----------|------|----------|-------|

> **Root element choice:** [If multiple valid roots exist, explain when to use each.]

### 2.2 Composition Zones

> **Type** — determines what governs compliance, not what element renders:
> - **Content** — exists to communicate information. What it shows can vary within the stated constraints. May be substituted with equivalent content elements.
> - **Interaction** — exists because of what the component does. Its presence, meaning, and behaviour are fixed by the interaction contract. Cannot be substituted with a content element even if both share the same visual form (e.g., a state-indicating chevron cannot be replaced by a decorative category icon just because both are SVGs).
>
> **Cardinality** — expresses how many instances of a zone are valid:
> - `1` — exactly one, required
> - `1+` — one or more, no upper limit
> - `2–5` — minimum two, maximum five (use actual numbers)
> - `0–1` — optional, at most one
> - `0+` — optional, no upper limit
>
> **Order** — states whether the zone's position relative to other zones is part of the compliance contract:
> - `Fixed` — must appear in the documented position regardless of available space; may be restyled but not repositioned
> - `Flexible` — position may vary across implementations
> - `Responsive` — position is fixed per space condition; append both states using your system's condition names: `Responsive — left of label ([condition-A]) / above label ([condition-B])`
> - When Fixed or Responsive, always include a position descriptor so the rule is unambiguous

| Zone | Type | Cardinality | Accepts | Order | Absent behaviour | Compliance rule |
|------|------|-------------|---------|-------|-----------------|-----------------|
[One row per zone. Cover all named regions — both content areas and embedded functional elements.]

### 2.3 Adaptive Layout

> Documents how the component's layout changes based on the space available to it. The component is self-managing — it responds to the real estate provided by its container, not the device or viewport. Conditions are named by the design system; do not use pixel values or media query syntax here.
>
> Omit this section if the component's layout is identical regardless of available space.

| Condition | Layout prop changes | Zone order changes |
|-----------|--------------------|--------------------|
[One row per space condition that produces a layout change.
Layout prop changes: reference the prop name and new value from §3.1 (e.g., `direction → vertical`).
Zone order changes: name the zone and describe the position shift (e.g., `Image zone: above text (was: left of text)`). Write `—` if no zones move at this condition.]

---

## 3. Properties

### 3.1 Layout Props

> Props that control how the component arranges itself or its children in space. Implemented via CSS — no DOM change, no token reference. If the component has no layout flexibility, omit this section.

| Prop | Values | Default | What changes |
|------|--------|---------|--------------|
[One row per layout-flexible axis: direction, sizing, alignment, density, overflow, reverse, etc.]

### 3.2 Visual Variants

> Props that switch which visual style is applied — size, style, emphasis, or any other appearance modifier. These select a visual mode; they are not token values themselves.

| Prop | Values | Default | Description |
|------|--------|---------|-------------|

### 3.3 Behavioral Props

> Props that configure what the component does — feature flags, state control, and operational options. If the component has no configurable behavior beyond its visual variants, omit this section.

| Prop | Type | Default | Required | Description |
|------|------|---------|----------|-------------|

---

## 4. Appearance

### 4.1 Interaction States

[Visual states on the component's own root element: hover, focus, active, disabled, error, selected. Note which states are driven by Behavioral Props (e.g., disabled is set via a prop) and which are pure CSS responses to user input. If all states are owned by children, say so.]

### 4.2 Layout Policy

[Fixed layout rules this component always enforces — not configurable via props. Examples: a max-width constraint, an alignment anchoring rule, clip behaviour. Omit if none.]

### 4.3 Design Tokens

#### 4.4.1 Token Strategy

[What tier of tokens this component uses, which properties it owns, which are delegated to children.]

#### 4.4.2 Token Map

[Source: Figma / Storybook / tokens.json / description-only — state clearly]

[Tokens confirmed:]
| Property | Token |
|----------|-------|

[All raw/unbound:]
| Property | Raw value | Token |
|----------|-----------|-------|

[No source:]
> Token map pending — supply a Figma node URL, Storybook URL, or CSS/token file to complete this section.

---

## 5. Behavior

### 5.1 Interactions

[**Default — no interaction delta confirmed (Q10 = No, or single platform):**
Use a single table. Do not split into platform subsections.]

| Event | Source | Action |
|-------|--------|--------|

[**Only when an interaction delta was confirmed in Q10:**
Document shared behaviors once in an introductory note, then use subsections only for what actually differs. Do not repeat shared events in both subsections.]

> The following behaviors are the same on all platforms: [list shared events briefly]

#### 5.1.1 [Platform with unique affordance — e.g., Desktop / Mouse]

| Event | Source | Action |
|-------|--------|--------|

#### 5.1.2 [Platform with unique affordance — e.g., Mobile / Touch]

| Event | Source | Action |
|-------|--------|--------|

### 5.2 State Machine

[Internal states and transitions. If the component has no internal state: "None — [what manages state instead]."]

### 5.3 Events Emitted

[Events this component emits to its parent. If none: "None."]

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
- **Focus interference:** [None / describe any deliberate manipulation]
- **Tab order:** [Describe the expected focus sequence]
- **On open/close:** [Describe focus movement when the component opens or closes, if applicable]

### 6.4 Screen Reader Expectations

- [What is announced when the component is first reached]
- [What is announced when the user activates or interacts with it]
- [What is announced when state changes or content updates]
- [What is announced for empty states or errors]
```

---

## Phase 6: JSON schema generation (if requested)

Generate a `.schema.json` derived directly from the contract. Never add validation rules that are not stated in the contract.

### Mapping contract to schema

| Contract source | Schema construct |
|---|---|
| §3.1 Layout Props — values | `enum` on the property |
| §3.2 Visual Variants — values | `enum` on the property |
| §3.3 Behavioral Props — type + default | `properties`, `default` |
| §3.3 Behavioral Props — Required = Yes | `required` array |
| §2.2 Composition Zones — required zones with sub-components (Cardinality ≥ 1) | `properties` with `$ref` or inline `object` |
| §2.2 Composition Zones — Cardinality minimum | `minItems` on the array |
| §2.2 Composition Zones — optional zones (Cardinality starts at 0) | `properties` entry omitted from `required` |

### Schema rules

- Default: JSON Schema Draft 07 (`"$schema": "http://json-schema.org/draft-07/schema#"`)
- `"$id"`: component name in kebab-case
- `"title"`: component display name
- `"description"` on every property, copied from the contract's Description column
- Enum props: `"type": "string"` + `"enum": [...]`
- Boolean props: `"type": "boolean"`
- Number props: `"type": "number"` with `"minimum"` / `"maximum"` only if the contract states bounds
- Child arrays: `"type": "array"` + `"minItems"` where stated + `"items": { "$ref": "[name]" }` in $ref mode, or inline object shape in inline mode
- Optional children: present in `properties`, absent from `required`

---

## Output

Write the contract as `[ComponentName].md` (PascalCase). If a schema was requested, also write `[ComponentName].schema.json` to the same directory. Ask for the target directory if the user has not specified one. Confirm all file paths after writing.
