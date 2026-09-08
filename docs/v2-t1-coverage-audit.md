# T1 — Coverage regression audit

**Run 2026-09-08 against `contract-format-v2-proposal.md`.**

**Result: v2 fails T1 as drafted.** Six v1 sections have no v2 home, one of which breaks schema generation entirely, and the one complete v2 requirement set misses a guarantee its v1 element provided free. None of this is fatal to the idea — every gap has an obvious fix — but v2 must not be adopted in its current form.

Method, per the plan: enumerate what v1's named constructs provide implicitly, require each to map to a v2 requirement, and separately check that every v1 *section* has somewhere to live.

---

## Part A — Structural coverage: which v1 sections have a v2 home

v1 has 17 numbered sections. v2 has 6. That compression is the point, but it must be lossless.

| v1 section | v2 home | Status |
|---|---|---|
| 2.1 Semantic Markup | Structure | covered |
| 2.2 Composition Zones | Composition | covered |
| 2.3 Adaptive Layout | — | **NO HOME** |
| 3.1 Layout Props | — | **NO HOME** |
| 3.2 Visual Variants | — | **NO HOME** |
| 3.3 Behavioral Props | — | **NO HOME** |
| 4.1 Interaction States | Appearance | **weak** — only reduced motion appears |
| 4.2 Layout Policy | — | **NO HOME** |
| 4.3 Design Tokens | Appearance | covered |
| 5.1 Interactions | Behaviour | covered |
| 5.2 State Machine | BEH-06 | partial — one requirement, no transitions |
| 5.3 Events Emitted | BEH-04 | covered |
| 5.4 Events Received | — | **NO HOME** |
| 6.1 Roles & Attributes | Structure + Accessibility | covered |
| 6.2 Keyboard / Gesture | ACC-06 | partial — one requirement for a whole section |
| 6.3 Focus Management | ACC-01/02/03 | covered |
| 6.4 Screen Reader Expectations | ACC-05 | partial — only announces on open |

### G1 — v2 has no concept of props at all *(critical)*

**This is the finding that stops adoption.** v1 has three deliberately-separated prop categories — Layout Props (§3.1), Visual Variants (§3.2), Behavioral Props (§3.3) — and Phase 5 spends a whole principle on never mixing them. v2 drafted six sections and **none of them describes a component's API surface**.

Three consequences, in descending order of severity:

1. **Schema generation breaks completely.** Phase 6 derives `.schema.json` from §3.1/§3.2/§3.3 plus §2.2 cardinality. Two of those inputs no longer exist. v2 as drafted cannot produce the props schema at all — and the schema is a promised output in the README.
2. **The presence-toggle rule is lost.** v1 derives a boolean like `showCloseButton` for any fixed-content zone whose cardinality starts at 0, because such a zone cannot signal its own presence through content. v2's `CMP-04` states cardinality `0–1` and provides no way to control it.
3. **A whole class of requirement becomes unstatable** — what a *consumer* may configure, as opposed to what the component must do.

**Fix:** a seventh section, `API`, holding the three prop categories with the same separation v1 enforces. It is genuinely a different concern from the other six: Structure through Accessibility describe what the component *is and does*; API describes what a consumer may *vary*. Requirements there bind to the schema rather than to a rendered tree, which is consistent with the format — `observe: prop`, `method: schema`.

### G2 — Adaptive layout has no home *(major)*

v1 §2.3 states named space conditions and what changes under each — for Modal, "Compact → full-screen sheet, Regular → centred dialog with max-width." That eval expects it explicitly. v2 has no requirement about behaviour under constrained space.

This is not a small omission: adaptive behaviour is *observable*, is frequently where cross-platform components actually differ, and v1's §2.3 was already correctly platform-neutral (conditions are named by the design system; only the mechanism differs). It should have been the easiest section to carry over.

**Fix:** requirements of the form *"Under condition C, layout property P takes value V"*, with `observe: layout`, `kind: state`, checked by rendering at a container size that satisfies C. The condition names come from the interview, as they do today.

### G3 — Layout policy has no home *(moderate)*

v1 §4.2 holds fixed, non-configurable layout rules — a max-width constraint, clip behaviour, "only the selected panel is rendered." These are requirements in the strictest sense: always true, not consumer-varied. They map cleanly to `observe: layout, kind: state` and were simply forgotten.

### G4 — Events received has no home *(moderate)*

v2's Behaviour section covers events the component *emits* (BEH-04). v1 §5.4 also covers what it *listens for*. A component that must respond to an external event has no way to state it.

### G5 — Interaction states are nearly absent *(moderate)*

v1 §4.1 enumerates hover, focus, active, disabled, error, selected, and which are driven by props versus native response. v2's Appearance holds only tokens plus reduced motion. Nothing states that a disabled component must *look* disabled, or that a focus indicator must be visible — the latter being a WCAG requirement, not a nicety.

### G6 — Keyboard and screen-reader coverage is one requirement each *(moderate)*

`ACC-06` ("operable by the platform's primary non-pointer input") stands in for the whole of v1 §6.2, which enumerates per-key behaviour. `ACC-05` covers only announcement on open, where §6.4 covers reach, activation, state change, and error/empty. These are not *wrong*, they are **under-specified** — and under-specification is exactly the F1 failure mode this test exists to catch. A single vague requirement passes T2 bindability while failing T3 discrimination.

---

## Part B — The implicit bundle catalogue

What v1 bought with one element name, itemised. This is the instrument the rest of the conversion must satisfy.

### `<button>`

| Free behaviour | Must become |
|---|---|
| **Enter** activates | explicit requirement |
| **Space** activates — and suppresses page scroll | explicit requirement; the most commonly missed half |
| in sequential focus order with no `tabindex` | explicit requirement |
| focus indicator drawn by the platform | explicit requirement (also WCAG 2.4.7) |
| `disabled` removes from focus order, blocks activation, *and* is announced | three separate requirements |
| `type=submit` submits its form **without scripting** | explicit requirement where applicable |
| keyboard activation synthesises a click | covered by the activation requirements |
| announced with role and name | covered by identity + role + name |

### `<a href>`

| Free behaviour | Must become |
|---|---|
| **Enter** activates — and **Space does not** | explicit; the asymmetry with button is real and load-bearing |
| middle-click / modifier-click opens in a new context | explicit requirement |
| context menu offers copy-link and open-in-new | explicit requirement |
| destination visible before activation (status bar / long-press preview) | explicit requirement |
| reachable and followable **without scripting** | explicit requirement |
| discoverable by crawlers | explicit, or a recorded justified drop |
| visited state | explicit, or a recorded justified drop |

### `<dialog>` opened modally

| Free behaviour | v2 Modal coverage |
|---|---|
| renders in the **top layer**, above all other content regardless of stacking | **MISSING — see G7** |
| backdrop element exists and intercepts pointer input | functionally covered by STR-02 |
| Escape dismisses | BEH-02 |
| focus contained by the platform | ACC-02 |
| content outside is inert to pointer and AT | STR-02 |
| announced as a dialog with its name | STR-01 + STR-03 |
| *(focus return is **not** free — v1 required it manually)* | ACC-03 — v2 keeps it correctly |

### `<input type="radio">` in `<fieldset>`/`<legend>`

| Free behaviour | Must become |
|---|---|
| arrow keys move **and** select | explicit requirement |
| the group is one tab stop, not one per option | explicit requirement |
| exactly one selected, enforced by grouping | explicit requirement |
| group label announced with each option | explicit requirement |
| position announced ("2 of 5") | explicit requirement |
| value participates in form submission | explicit requirement |

### `<ul>`/`<li>`

| Free behaviour | Must become |
|---|---|
| announced as a list **with item count** | explicit requirement |
| each item announced with its position | explicit requirement |
| navigable by list shortcut / rotor | explicit requirement |

### Heading elements

| Free behaviour | Must become |
|---|---|
| reachable by heading navigation | explicit requirement |
| contributes to the document outline | explicit, or a recorded justified drop |

### Deliberate contrast — `role="tablist"`

The tabs pattern has **no native element on any platform**; it is composed from ARIA or from platform equivalents. Its implicit bundle is therefore *empty*, and everything about it was already explicit in v1. This is the case where v2 loses nothing at all — useful as a control, and a reminder that the bundle problem is specific to archetypes with real native elements.

### G7 — Top-layer rendering is unrequired *(major, Modal-specific)*

`<dialog>` opened modally renders in the browser's top layer: above every other element regardless of `z-index` or ancestor stacking context. **No v2 requirement states this.** A modal rendered inside a stacking context, appearing *below* a sticky header, satisfies STR-01 through ACC-06 completely — it is exposed as a modal surface, names itself, traps focus, makes the background inert — while being visibly broken.

This is the clearest single instance of F1: a guarantee that came free with the element name, invisible precisely because nobody had to write it down.

**Fix:** *"While open, the component renders above all other application content, regardless of the stacking of its container"* — `observe: layout`, `kind: state`.

---

## Part C — Verdict against the acceptance bar

**Criterion 1 (Coverage): FAIL.** Six v1 sections have no v2 home; one of them (props) breaks a promised output. One element-level guarantee (top layer) is unmapped.

The plan says failing coverage is a reason to fix v2, and failing it *again after fixes* is a reason not to adopt. So this is the expected first-round result rather than a verdict on the idea — but the fixes are substantial enough that the worked Modal example must be rewritten before T2 can run against it.

### Required before re-running T1

1. Add an `API` section for the three prop categories, with `observe: prop`, `method: schema`.
2. Add adaptive-layout requirements, with `observe: layout`.
3. Add layout-policy requirements.
4. Add events-received requirements.
5. Expand interaction states beyond reduced motion — at minimum a visible focus indicator and a distinguishable disabled appearance.
6. Expand ACC-05 and ACC-06 from one requirement each into the set v1 §6.2/§6.4 actually enumerate.
7. Add the top-layer requirement to Modal.
8. Rewrite the worked Modal example against all of the above, then re-run T1.

### What this audit vindicates

The method worked exactly as intended, and cheaply. Every one of these gaps is invisible when reading v2 on its own — the document is internally coherent and reads as complete. They only appear when checked against an enumeration of what the old format guaranteed. Had we adopted v2 on the strength of the Modal example looking right, schema generation would have broken at the first component and nobody would have known why.

That is the case for running T1 before T2 through T6, and for not accepting a format on one convincing example.
