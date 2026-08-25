# WCAG success-criteria mapping

Source of authority: [WCAG 2.2](https://www.w3.org/TR/WCAG22/), Level AA (the common baseline target). This file maps success criteria to the parts of a component contract they bear on, so §6 Accessibility can cite *why* a requirement exists rather than asserting it unsupported. It has nothing to do with any specific design system.

**Last verified:** 2026-08-25

Consult this file from **Phase 4** when deriving §6, and note the relevant SC id(s) next to a requirement where it adds clarity (e.g., in a compliance-audited system). This is optional polish, not a new question to ask the designer — never ask the interviewee about WCAG criteria directly; derive the mapping silently.

| SC | Name | Applies when the component… | Contract impact |
|---|---|---|---|
| 1.4.3 / 1.4.11 | Contrast (Minimum) / Non-text Contrast | …has text, or has meaningful graphical elements (icons, borders indicating state, focus indicators) | Note in §4.3 Token Strategy that color pairings must resolve to the design system's compliant token pairs — this contract does not itself set contrast ratios, since that's a token-definition concern upstream. |
| 1.4.13 | Content on Hover or Focus | …reveals a tooltip or popover on hover/focus | Popup must be dismissible without moving pointer/focus (`Escape`), remain visible while pointer is over it, and persist until dismissed or no longer relevant. Feeds §6.2/§6.3. |
| 2.1.1 | Keyboard | …has any interactive affordance at all | Every interaction in §5.1 must have a keyboard equivalent in §6.2 — no operation that only works via pointer/touch. |
| 2.1.2 | No Keyboard Trap | …traps focus (modals) or manages a composite widget (grid, tree) | §6.3 must state the exit path (`Escape`, or standard `Tab` traversal) — a focus trap is only compliant if there's a documented, working way out. |
| 2.2.1 | Timing Adjustable | …auto-dismisses, auto-advances, or has any time limit (e.g., a toast that disappears after N seconds) | §5.2 State Machine must document a way to pause, extend, or dismiss the timer on user interaction (e.g., hover/focus pauses auto-dismiss) unless the timing is essential and brief (20 hours+ exception rarely applies to UI components). |
| 2.4.3 | Focus Order | …has more than one focusable element | §6.3 Tab order must follow a sequence that preserves meaning, not just DOM insertion order. |
| 2.4.7 / 2.4.11 | Focus Visible / Focus Not Obscured | …is keyboard-operable | §4.1 Interaction States must include a focus state distinct from default/hover, and it must not be visually suppressed (e.g., `outline: none` with no replacement) or hidden behind sticky headers/overlays. |
| 2.5.5 / 2.5.8 | Target Size | …is a discrete touch/click target (button, checkbox, tab, menu item) | Note in §4.2 Layout Policy if the design system enforces a minimum hit-area independent of visual size (common pattern: small visual icon, larger invisible padding for the hit target). |
| 3.2.1 / 3.2.2 | On Focus / On Input | …changes context (navigates, submits, opens something) purely from focus or a value change, without an explicit activation | Flag this in §5.1 — an interaction that fires on focus alone (rather than on a deliberate activation like Enter/click) is a common accessibility anti-pattern; document only if intentional and justified. |
| 4.1.2 | Name, Role, Value | …is any UI component at all | This is the criterion §2.1 (Semantic Markup) and §6.1 (ARIA Roles & Attributes) exist to satisfy — every interactive element needs a programmatically determinable name, role, and current state/value. |
| 4.1.3 | Status Messages | …communicates a status change without moving focus (loading, saved, error banner, cart count) | §6.1 must specify the live-region role (`status` vs `alert` — see wai-aria-patterns.md) rather than leaving async updates silent to assistive tech. |

## How to use this in the contract

Don't create a seventh section or a "WCAG" table in the output — the mapping is scaffolding for correctness, not a new deliverable. Where it's useful (audited/regulated design systems), a short parenthetical is enough, e.g.:

> Escape closes the dialog and returns focus to the trigger (WCAG 2.1.2, 2.4.3).

If the design system has no compliance requirement, derive the same requirements silently without citing SC ids — the underlying behavior is correct either way; the citation is optional context, not the source of the rule.
