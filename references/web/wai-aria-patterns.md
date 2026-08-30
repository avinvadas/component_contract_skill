# WAI-ARIA Authoring Practices Guide — pattern reference

Source of authority: [WAI-ARIA Authoring Practices Guide (APG)](https://www.w3.org/WAI/ARIA/apg/patterns/), current version. This file condenses the patterns relevant to component contracts. It is design-system-agnostic — it describes correct markup and keyboard behavior for an interaction shape, never a specific system's visual style.

**Last verified:** 2026-08-25

Consult this file from **Phase 3** (semantic markup) and **Phase 4** (accessibility derivation) whenever the component's action/interaction combination isn't fully covered by SKILL.md's condensed decision table, or whenever you need the full keyboard/attribute set for a pattern the table only names in passing.

## The first rule of ARIA use

Before consulting any pattern below: if a native HTML element or attribute already has the semantics and behavior a component needs, use it — never re-purpose a generic element (`<div>`, `<span>`) and patch equivalent behavior on with ARIA. This is WAI-ARIA's own foundational rule, not a style preference, and it's stricter than it looks: **a passing accessible-role check is necessary but not sufficient.** A native element bundles behavior that no amount of ARIA can replicate on a generic one — `<a href>` carries right-click "open in new tab," Cmd/Ctrl+click, the status-bar URL preview, and search-engine crawlability; a native `<button>` keeps working before JavaScript has loaded and gets keyboard, focus, and disabled-state handling for free. An ARIA-patched `<div>` that reports the correct role but lacks these has not satisfied the requirement, even though a naive accessibility-tree check might say it has.

Only re-purpose a generic element with ARIA when no native element for the needed archetype exists at all (a custom combobox, a custom-styled slider no native `<input>` can visually achieve) — and even then, replicate the *entire* pattern below, not just the role.

---

## Button

- Role: native `<button>` carries the role implicitly. A non-native element needs `role="button"` plus `tabindex="0"`.
- State: `aria-pressed` (true/false) only for toggle buttons. `aria-disabled="true"` (preferred over the `disabled` attribute when the element must remain focusable/announced).
- Keyboard: `Enter` and `Space` both activate. `Space` should trigger on keyup, not keydown, to allow cancel-by-dragging-off.

## Link

- Role: native `<a href>` carries the role implicitly. Never apply `role="link"` to a non-navigating element — if it doesn't change location, it isn't a link, regardless of visual style.
- Keyboard: `Enter` activates. No `Space` behavior (distinguishes it from button).

## Tabs

- Structure: container `role="tablist"` (labeled via `aria-label`/`aria-labelledby`) → `role="tab"` triggers → `role="tabpanel"` content regions. Each tab references its panel with `aria-controls`; each panel references its tab with `aria-labelledby`.
- State: active tab gets `aria-selected="true"`; inactive tabs `aria-selected="false"` and `tabindex="-1"`. Only the active tab is in the tab order (roving tabindex).
- Keyboard: `ArrowLeft`/`ArrowRight` (or `ArrowUp`/`ArrowDown` for vertical tabs) move selection between tabs; `Home`/`End` jump to first/last tab; `Tab` moves out of the tablist into the active panel.
- Two activation models exist — pick one and state it: **automatic activation** (arrow keys immediately select and show the panel) or **manual activation** (arrow keys move focus only; `Enter`/`Space` activates). Automatic is more common for simple content tabs; manual is preferred when switching is expensive (e.g., triggers a network request).

## Disclosure (single collapsible section)

- Trigger: `<button aria-expanded="true|false" aria-controls="[panel-id]">`.
- Panel: plain content region: no `role` required. If the panel is removed from the DOM when collapsed, `aria-controls` still points at it only while present — some implementations keep it in the DOM with `hidden` instead.
- Keyboard: `Enter`/`Space` on the trigger toggles.

## Accordion (group of disclosures)

- Structure: a heading element (`<h3>` etc., level set by document context) wraps each trigger button; each trigger is `aria-expanded` + `aria-controls` as in Disclosure above.
- Multi-open vs. single-open is a content decision, not an accessibility one — both are valid APG variants. State which one the contract uses.
- Keyboard: `ArrowDown`/`ArrowUp` move focus between triggers (optional enhancement per APG, not required); `Home`/`End` to first/last trigger; `Enter`/`Space` toggles the focused trigger.

## Dialog (Modal)

- Structure: `role="dialog"` (or `alertdialog` for confirmation prompts that require a response) with `aria-modal="true"`, and `aria-labelledby` pointing to the dialog's visible title element. Use `aria-describedby` if there's a supporting description.
- Focus: on open, move focus to the first focusable element inside (or the dialog container itself if no sensible first target — e.g., a destructive-confirm dialog where you don't want focus defaulting to "Delete"). Trap focus inside via `Tab`/`Shift+Tab` cycling. On close, restore focus to the element that opened the dialog.
- Keyboard: `Escape` closes (unless the dialog requires an explicit choice — `alertdialog` may disable `Escape`, note this explicitly if so).
- Everything outside the dialog must be inert while open (`inert` attribute, `aria-hidden="true"` on siblings, or equivalent) so assistive tech and Tab order can't reach it.

## Non-modal dialog / popover

- Same `role="dialog"` and labeling as above, but **no** `aria-modal`, no focus trap, and no inert background — the rest of the page stays operable. Used for things like a non-blocking side panel.

## Alert / Status (live regions)

- `role="alert"` — for urgent, unsolicited messages (errors, critical warnings). Implicitly `aria-live="assertive"`, interrupts the screen reader.
- `role="status"` — for advisory, non-urgent updates (e.g., "3 items in cart"). Implicitly `aria-live="polite"`, waits for a pause.
- Never nest interactive controls inside a live region that gets re-rendered — screen readers can lose track of focus. Announce content changes only; keep persistent controls outside the region or leave them untouched by the update.
- Empty content updating into a message must trigger inside the same live region so the transition is announced (a region that starts empty and gets content later fires the announcement only if it was already marked live).

## Tooltip

- Trigger: any focusable element gets `aria-describedby` pointing to the tooltip's id. The tooltip itself: `role="tooltip"`.
- Visibility: appears on `:hover` and on keyboard `:focus` — a tooltip that only shows on mouse hover is not accessible.
- Dismissal: `Escape` dismisses without moving focus off the trigger. Tooltip must not contain interactive content (if it needs a link/button, it's not a tooltip — it's a popover, and needs the non-modal dialog pattern instead).
- Never rely on tooltip content alone to convey required information — it must be supplementary to a visible or otherwise accessible label.

## Listbox (custom single/multi select, not a native `<select>`)

- Structure: `role="listbox"` container (labeled) → `role="option"` children. Multi-select: `aria-multiselectable="true"` on the listbox.
- State: selected option(s) get `aria-selected="true"`. Only one option is in the tab sequence at a time (roving tabindex) or the listbox itself is the single tab stop with `aria-activedescendant` pointing at the current option — pick one model and apply it consistently.
- Keyboard: `ArrowUp`/`ArrowDown` move selection (single-select) or move a virtual focus cursor (multi-select, confirmed with `Space`); `Home`/`End` jump to first/last; type-ahead (typing a letter jumps to the next matching option) is expected for lists of meaningful length.

## Combobox (text input + filtered/attached listbox — autocomplete, typeahead select)

This pattern has no equivalent in SKILL.md's condensed table — always consult it in full here when Q2/Q7 indicate a searchable or type-to-filter selection input.

- Structure: a text `<input>` with `role="combobox"`, `aria-expanded`, `aria-controls` (pointing to the popup listbox id), and `aria-autocomplete` (`"list"`, `"both"`, or `"none"` depending on whether typing filters/suggests). The popup is `role="listbox"` with `role="option"` children, same as Listbox above.
- The currently-highlighted option (as the user arrows through suggestions without committing) is tracked via `aria-activedescendant` on the input, referencing the option's id — focus stays on the input the entire time.
- Keyboard: `ArrowDown`/`ArrowUp` move the active suggestion; `Enter` commits the highlighted suggestion; `Escape` closes the popup (and clears typed text only if that matches the system's convention — state which); typing continues to filter.
- Never move DOM focus into the popup — combobox accessibility depends on focus remaining on the input at all times.

## Menu / Menu Button

- Structure: trigger `<button aria-haspopup="true" aria-expanded="true|false" aria-controls="[menu-id]">` → `role="menu"` container → `role="menuitem"` (or `menuitemcheckbox`/`menuitemradio` for selectable items) children. Use this only for **action menus** (a set of commands), never as a substitute for navigation links or a form selection control.
- Keyboard: `ArrowDown`/`ArrowUp` move between items; `Enter`/`Space` activates the focused item; `Escape` closes and returns focus to the trigger; typing a letter jumps to the next matching item; submenus open with `ArrowRight` and close with `ArrowLeft`.
- Focus moves into the menu on open (typically to the first item) and returns to the trigger on close.

## Radio group

- Structure: `<fieldset>` + `<legend>` (accessible group name) wrapping native `<input type="radio">` items sharing one `name`, or `role="radiogroup"` wrapping `role="radio"` items for a custom-styled equivalent.
- Keyboard: arrow keys move selection *and* select in one step (this differs from listbox/menu — radio selection is immediate on arrow, not confirmed separately); `Tab` enters/exits the group as a single stop.

## Checkbox / Switch

- Checkbox: native `<input type="checkbox">`, or `role="checkbox"` + `aria-checked` (`true`/`false`/`"mixed"` for indeterminate) on a custom element.
- Switch: `role="switch"` + `aria-checked` — use when the semantic is strictly binary on/off with immediate effect (no separate "apply" step), distinct from a checkbox which often participates in a form submitted later. If the design system doesn't distinguish them visually, still pick the role that matches the actual behavior.
- Keyboard: `Space` toggles either pattern.

## Tree View

- Structure: `role="tree"` container (labeled) → `role="treeitem"` nodes, nested `role="group"` for children of an expanded node. Expandable nodes carry `aria-expanded`.
- State: `aria-selected` on the current item if selection is supported; `aria-level`, `aria-setsize`, `aria-posinset` are required only when the DOM nesting doesn't already convey them (native nesting usually does).
- Keyboard: `ArrowDown`/`ArrowUp` move focus; `ArrowRight` expands a collapsed node or moves into its first child if already expanded; `ArrowLeft` collapses an expanded node or moves to its parent if already collapsed; `Home`/`End` jump to first/last visible item; type-ahead as in Listbox.

## Slider

- Structure: `role="slider"` on the handle (native `<input type="range">` gets this implicitly) with `aria-valuemin`, `aria-valuemax`, `aria-valuenow`, and `aria-valuetext` when the raw number isn't self-explanatory (e.g., a value that maps to a label like "Medium").
- Keyboard: `ArrowUp`/`ArrowRight` increase, `ArrowDown`/`ArrowLeft` decrease; `Home`/`End` jump to min/max; `PageUp`/`PageDown` for larger steps if the range warrants it.
- Range slider (two handles): each handle is a separate `role="slider"` with its own bounds; document how the handles constrain each other (min handle can't exceed max handle).

## Grid / Data table with interactive cells

- Use `role="grid"` (not `role="table"`) only when cells contain focusable controls or the user navigates cell-by-cell with arrow keys. A read-only data table with no cell-level interaction should stay native `<table>` markup — do not apply grid semantics to it.
- Structure: `role="grid"` → `role="row"` → `role="gridcell"` (or `columnheader`/`rowheader`).
- Keyboard: arrow keys move the active cell in all four directions; `Tab` enters/exits the grid as a single stop, with the last-focused cell remembered (roving tabindex at the cell level).

## Drag-and-drop reordering (no single official APG pattern — apply general principles)

APG does not publish one canonical pattern for reorderable lists; treat pointer drag as an enhancement layered over a fully keyboard-operable baseline, using the `list`/`listitem` roles for the container/items:

- Every draggable item must be independently operable without a pointer: `Space` or `Enter` to "pick up" (grab) the focused item, `Arrow` keys to move it within the list, `Space`/`Enter` again to "drop," `Escape` to cancel and return it to its original position.
- Announce the grab/move/drop lifecycle through a live region (`aria-live="polite"`) — e.g., "Item picked up. Position 2 of 5." / "Moved to position 3 of 5." / "Item dropped, final position 3 of 5."
- `aria-grabbed` is deprecated in ARIA 1.1+ — do not use it. Convey grabbed state through the live-region announcement and a visual/state class instead.
