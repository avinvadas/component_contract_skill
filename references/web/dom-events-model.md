# DOM events and rendered-output verification

Source of authority: the [WHATWG DOM Standard](https://dom.spec.whatwg.org/) — specifically `CustomEvent` and event dispatch/bubbling — plus the accessibility-tree model already documented in `references/web/wai-aria-patterns.md`. This file covers one concern: how a contract's behavioral claims (§5.3 Events Emitted, §5.4 Events Received, §5.2 State Machine, §6 Accessibility) are expressed and verified as **rendered DOM output**, independent of whatever framework produced it. It is kept separate from CSS concerns (`references/web/css-layout-and-interaction.md`) and token formats (`references/design-tokens-format.md`) — a contract's event contract, layout mechanism, and token bindings are three independent things and should be editable independently.

**Last verified:** 2026-08-25

Consult this file from **Phase 5** when writing §5.3/§5.4, and whenever the target team asks how a contract can be checked automatically at build time.

---

## The event contract, framework-independent

Every UI framework's event system ultimately either dispatches, or can be observed as, a real DOM event once the component is rendered in a browser (or a browser-like environment such as jsdom). That's the common denominator this skill should describe in §5.3/§5.4, rather than any one framework's callback-prop or emit convention:

- **`CustomEvent`** is the standard shape for a component-authored event: `new CustomEvent(name, { detail, bubbles, composed, cancelable })`.
  - `bubbles: true` — the event propagates up through ancestors, so a parent can listen at a distance rather than requiring a direct prop wired at every level.
  - `composed: true` — required if the event needs to cross a Shadow DOM boundary (relevant to Web Components; irrelevant for frameworks that don't use shadow roots, but harmless to set).
  - `cancelable: true` — only if a listener should be able to call `preventDefault()` to stop the component's default handling (e.g., cancel a dismiss).
  - `detail` — the event's payload. Record its shape in §5.3 the same way a prop's type is recorded in §3.3.
- **Naming**: record the event name as it would appear in `addEventListener(name, ...)` — a plain string, not a framework-specific handler prop name (`onClose` is a React convention for wiring up a listener; the underlying event this skill documents is the DOM-level `close` or `dismiss` event that convention wires to).

## Events Received (§5.4)

Two distinct things get documented here — don't conflate them:
1. **Native DOM events the component listens to directly** — `keydown`, `focusin`/`focusout`, `input`, `change`, `pointerdown`, etc. These are platform-standard; no invention needed.
2. **Custom events raised by a child sub-component** — e.g., a Modal shell listening for a `dismiss` event bubbling up from its own Close-button sub-component. Reference the child's contract for the event's exact name/shape rather than re-specifying it (same ownership principle Phase 5 already applies to props and tokens).

## Verifying the contract against rendered output

The point of grounding events in the DOM model rather than a framework's API is that it makes the contract checkable the same way regardless of implementation:

- **Structure and ARIA (§2.1, §6.1)** — query the rendered DOM tree and, where the check needs to reflect what assistive tech actually perceives, the accessibility tree (role, accessible name, `aria-*` state) rather than raw markup. This is the same information `references/web/wai-aria-patterns.md` and `references/web/wcag-mapping.md` describe as required attributes — those tables are the assertion checklist.
- **Behavior (§5.2, §5.3, §5.4)** — attach a real `addEventListener` to the rendered root, trigger the documented interaction (a real or simulated `click`/`keydown`), and assert the expected `CustomEvent` fires with the expected `detail` — and, separately, assert the expected DOM/attribute state change happened (e.g., `aria-expanded` flipped, a class was added, focus moved).
- **Appearance (§4.1)** — read computed style (`getComputedStyle`) on the relevant pseudo-class/state rather than asserting against a specific class name, since class naming is an implementation detail the contract deliberately doesn't own.

None of this requires or assumes a specific test runner, framework, or component-testing library — it only assumes the thing under test is real, rendered DOM (a live browser, or a browser-equivalent environment) rather than framework source or a mocked render tree. That's what keeps verification framework-agnostic: the contract is a claim about rendered output, so it's checked against rendered output, regardless of what produced it.
