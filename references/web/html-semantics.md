# HTML Living Standard — semantics reference

Source of authority: [WHATWG HTML Living Standard](https://html.spec.whatwg.org/multipage/), the [content categories](https://html.spec.whatwg.org/multipage/dom.html#content-categories) and [sectioning](https://html.spec.whatwg.org/multipage/sections.html) sections specifically. SKILL.md's Phase 3 decision table covers the common cases; consult this file for edge cases the table doesn't resolve, or to justify a markup decision against the actual spec rather than convention.

**Last verified:** 2026-08-25

## Content categories relevant to component contracts

- **Interactive content**: elements whose default behavior is a user interaction — `<a href>`, `<button>`, `<input>`, `<select>`, `<textarea>`, `<audio controls>`, `<video controls>`, `<details>` (via its summary). A tabindex-only element that isn't natively interactive doesn't belong to this category by the spec, even if it's made operable via ARIA + JS.
- **Sectioning content**: `<article>`, `<aside>`, `<nav>`, `<section>` — each introduces an entry in the accessibility tree's outline and, per spec, should have an accessible name (heading or `aria-label`/`aria-labelledby`) when there's more than one of the same type on a page. This is the basis for Phase 3's "Named landmarks require an accessible name" rule.
- **Flow content**: the general-purpose category — most elements. Not independently useful for markup decisions but relevant when deciding whether a wrapper needs to be a generic `<div>`/`<span>` (no semantic contribution) versus one of the categories above.
- **Form-associated content**: `<input>`, `<select>`, `<textarea>`, `<button>`, `<label>`, `<fieldset>`, `<output>` — elements that participate in a `<form>`'s submission and validation lifecycle. A custom "input-like" component that needs to participate in native form submission (rather than only visually resembling an input) should be built on one of these, or use the [Form-Associated Custom Elements](https://html.spec.whatwg.org/multipage/custom-elements.html#form-associated-custom-elements) mechanism if it's a genuine custom element — not simulated with a plain `<div>` plus a hidden input synced by JS, which is a common but fragile workaround.

## The interactive-content nesting rule

Per spec, interactive content must not be nested inside other interactive content — a `<button>` cannot contain an `<a>`, a `<label>` wrapping an `<input>` cannot also wrap a `<button>`, etc. This directly resolves a class of composition questions Phase 3 doesn't explicitly cover: if Q4 describes a "part" that is itself independently actionable (e.g., a link inside a card that is also a button), the card's root cannot be the interactive element — restructure so only the innermost actionable part is interactive, and the outer container is a non-interactive wrapper (or the whole card becomes the single interactive target and the inner element is demoted to non-interactive, styled to look actionable only visually).

## Headings and document outline

Sectioning elements don't automatically imply a heading level — headings (`<h1>`–`<h6>`) are chosen based on their position in the *document's* outline, not the component's internal structure in isolation. A component contract should describe the heading's *role* (e.g., "the dialog's title, referenced by `aria-labelledby`") rather than prescribing a fixed `<h2>`/`<h3>` level, since the correct level depends on where the component is mounted in a given page — that's a per-usage decision, not part of the component's own contract.

## `disabled` vs `aria-disabled`

The native `disabled` attribute (on `<button>`, `<input>`, `<select>`, `<textarea>`, `<fieldset>`) removes the element from the tab order and blocks all interaction, including focus — which also means a screen reader user tabbing through the page won't discover the control exists at all. `aria-disabled="true"` communicates the disabled state while leaving the element focusable and announced, which is the correct choice whenever the disabled reason needs to be discoverable (e.g., "why is Save greyed out") rather than a state that means "not present." Note explicitly which one a contract's Disabled state uses.

## `<template>`, `<slot>`, and composite shells

For component contracts describing a composite shell in a Web Components context, `<slot>` is the standard mechanism for the "accepts" column in §2.2 Composition Zones — a named slot corresponds to a named zone. This is optional context: most contracts describe composition in framework-agnostic terms (props/children), and this note only applies when the target implementation is literally a custom element.
