# Component Contract Skill

A Claude skill for design systems teams. 
Answer a structured interview about a UI component, and it will generate a formal **component contract**: a markdown specification that captures the component's essence and puts it into semantic markup, design tokens, behavior, and accessibility requirements, making your component work *documentation-driven* early on in the process.

## What it generates

One interview, **one contract file** per component, covering any combination of supported target platforms (Web, iOS, Android, macOS) within that single document — plus, per platform, a structure file and optionally a JSON Schema, both split per platform because each platform's build process consumes its own.

```
ComponentName/
├── ComponentName.md                     # the one contract — every platform, one document
├── ComponentName.Web.structure.json     # per platform, always
├── ComponentName.iOS.structure.json
├── ComponentName.Web.schema.json        # per platform, optional
└── ComponentName.iOS.schema.json
```

- **`ComponentName.md`** — the entire contract, opening with a short Design Intent statement and then organized under four concerns, a plain separation-of-concerns structure rather than a grab-bag "Properties" section spanning several unrelated ones:
  - **Structure** — semantic markup, composition zones and their ownership/cardinality, adaptive layout, layout props, and layout policy
  - **Appearance** — visual variants, interaction states, and design tokens
  - **Behavior** — behavioral props, interactions, the state machine, and events emitted/received
  - **Accessibility** — roles/attributes, keyboard/gesture navigation, focus management, and screen reader/assistive-technology expectations

  Sections that describe *intent* (Composition Zones, Layout Policy, Visual Variants, Design Tokens, Behavioral Props, State Machine, Focus Management) are written once. Sections that are structurally platform-specific (Semantic Markup, Events Emitted/Received, Accessibility Roles & Attributes) hold one row per targeted platform, in the same table, right next to each other — never a separate file per platform, and never a value merged across platforms or left to be inferred ("same as Web"). A handful of sections (Adaptive Layout, Interaction States, Interactions, Keyboard/Gesture Navigation, Screen Reader expectations) are shared by default and only pick up a platform-specific note where an actual difference exists. The file opens with YAML frontmatter (component name, version, status, platforms) rather than a bespoke metadata block, so both a person and an agent reading it as implementation context can rely on the same standard convention.

- **`ComponentName.[Platform].structure.json`** *(one per platform, always)* — the contract's root element, zone order, and accessibility facts, extracted into a form that can be checked against a **rendered tree**: the live DOM for Web, a runtime accessibility-node dump for native platforms. Never against source code — a contract is satisfied by React, SwiftUI, or a framework nobody has invented yet, so long as the outcome matches, and source text can't tell you what actually rendered. This one isn't gated behind the schema question, because semantic markup and accessibility aren't optional the way a props schema is.

- **`ComponentName.[Platform].schema.json`** *(optional, one per platform)* — a JSON Schema Draft file validating a **consumer-supplied props instance**: is this a legal set of props for this component? It says nothing about whether an implementation honors the contract; that's the structure file's job. Its content is typically identical across a component's platforms, since it's derived entirely from sections that don't vary by platform — it's split into separate files because each platform's build tooling consumes its own schema as a separate compile-time step, not because the data differs.

A single-platform component still gets this same directory shape, so adding a second platform later means editing the existing contract's tables to add a row and dropping in that platform's files, never restructuring what's already there.

## Why it exists

A component contract captures **design intent**: what a component is and what it does, beneath its instances. Design intent is the stable ground beneath the ongoing cycle between design and engineering, and it can show up in more ways than a single tool captures at a given moment. The contract is a stable, explicit statement of that intent.

Two separate checkable artifacts come with it, and they check different subjects — worth keeping straight, since it's easy to credit the first with the second's job. The **JSON schema** validates a consumer-supplied props instance (is this a legal set of props for this component?). The **structure file** validates a real implementation's *rendered output* — the live DOM, or a runtime accessibility tree — against the contract's semantic markup and accessibility claims.

This creates a documentation-driven process, in which design and engineering both build from — and test against — the same explicit statement of intent, instead of each inferring it separately from whatever specific artifact happens to be at hand.

## Supported platforms

**Web, iOS, Android, macOS.** Windows and Linux are on the roadmap and not supported yet: their reference material is researched and kept in `references/`, but neither is offered by the interview and no contract should target them.

The blocker is specific. `references/structural-fact-validation.md` has no verified way to obtain a real rendered tree on either platform, so a contract targeting them could be written but never checked — which would contradict the accountability below. They are revisited once the four supported platforms are stable, tested, and validated.

## What this skill is accountable for

Four things, and it's worth being explicit about them, because the fourth is easy to mistake for the whole point and then judge the rest by it.

1. **Derivation** — plain-language answers about what a component *does* produce technically correct facts. Nobody using this needs to know HTML, ARIA, `UIAccessibility`, or any platform's interaction conventions; the skill resolves those from the interview plus the standards in `references/`.
2. **Sufficiency as implementation context** — the contract is meant to be handed to a person or an agent as the thing they build from, so nothing an implementer would otherwise have to ask about is left implicit or stated as a diff against another file.
3. **Provenance** — every concrete fact traces to an external standard, an explicit interview answer, or a structural inference from one of those. Anything else is cut. Unknowns stay marked pending rather than filled with a plausible invention; an unresolved token has no name written for it.
4. **Validation** — narrower than the three above, and deliberately so. The skill checks that what was specified is what got built. It does not check that what was specified was a good idea, that a token's value is the right color, or that the result looks correct — those belong to the design system's own tree and to visual regression testing, respectively.

**Maturity, stated plainly:** the first three are exercised on every run. The validation layer is the newest part of this repo and the least exercised — two checks have been run by hand against real artifacts (a rendered Android accessibility tree, and an iOS XCUITest run that surfaced a genuine accessibility defect invisible to visual inspection), and the token-name algorithm has not yet been run against a real generated token file at all. Native platforms carry documented tooling ceilings that Web does not: some facts need instrumented tests rather than a command-line dump, and those limits are recorded in `references/structural-fact-validation.md` rather than smoothed over.

## Three distinctions the format enforces

The contract format enforces three distinctions that informal documentation skips:
- **Content vs. Interaction zones**: A close button and a category icon are both SVGs, but only one can be omitted without breaking the component
- **What the component owns vs. what it delegates**: Composite shells reference sub-component contracts rather than re-specifying them
- **Confirmed tokens vs. pending tokens**: No invented names; if the source wasn't provided, the map is marked pending

## Usage

Trigger it in Claude with phrases like:
- *"Create a component contract for the Badge component"*
- *"Document this component"*
- *"Write up the spec for [component name]"*
- *"Add [component] to the design system contracts"*

Claude will ask 10 main questions, plus a handful of conditional follow-ups depending on your answers (e.g. how many platforms you selected, or whether the component holds sub-components), then generate the contract, one structure file per platform, and — if you asked for one — a JSON schema per platform.

## Reference material (`references/`)

The skill's technical derivations (markup, accessibility, layout mechanics, token formats, JSON Schema) are grounded in external, design-system-agnostic standards, not invented rules. `references/` is organized by scope — platform-specific standards live under a directory named for that platform; standards that apply regardless of platform stay at the root:

| File | Standard |
|---|---|
| `design-tokens-format.md` | DTCG token format, plus Style Dictionary / CSS custom properties / Tailwind |
| `figma-variables-model.md` | Figma's Collections/Modes/variable-binding model |
| `json-schema-draft-07.md` | JSON Schema Draft 07 |
| `token-naming-validation.md` | No external standard — a synthesized algorithm, since every design system configures its own downstream naming. Checks a generated variable's name against the canonical token tree's shape. Documents what it deliberately does not check: token values, pipeline output, rendered result |
| `structural-fact-validation.md` | No external standard — a synthesized mechanism for checking a rendered tree against the contract's markup and accessibility facts, with each platform's real tooling ceiling recorded from hands-on runs |
| `platform-differences.md` | Cross-platform comparison of accessibility API, layout adaptation, RTL, and motion — comparison content only, not routing logic |
| `native-events-models.md` | The native counterpart to `web/dom-events-model.md` — event/callback idioms for iOS, Android, macOS, Windows, and Linux, each with more than one live convention and no single canonical spec |
| `web/wai-aria-patterns.md` | WAI-ARIA Authoring Practices Guide |
| `web/wcag-mapping.md` | WCAG 2.2 success criteria |
| `web/html-semantics.md` | WHATWG HTML Living Standard |
| `web/css-layout-and-interaction.md` | CSS Container Queries, Logical Properties, Selectors Level 4, `prefers-reduced-motion` |
| `web/dom-events-model.md` | WHATWG DOM `CustomEvent` and rendered-output verification |
| `ios/ios-hig-accessibility.md` | `UIAccessibility` + Apple Human Interface Guidelines |
| `android/android-material-accessibility.md` | Compose/View accessibility semantics + Android adaptive-layout guidance |
| `macos/macos-hig-accessibility.md` | `NSAccessibility` + macOS-specific HIG conventions |
| `windows/windows-ui-automation.md` | Microsoft UI Automation control patterns |
| `linux/linux-atspi-accessibility.md` | AT-SPI, with the GTK/Qt toolkit split documented explicitly rather than picking one as canonical |
| `ios/ios-platform-conventions.md`, `macos/macos-platform-conventions.md`, `android/android-platform-conventions.md`, `windows/windows-platform-conventions.md` | Each platform's own behavioral/compositional conventions (ephemeral-surface lifecycle, window/composition, navigation and gesture) — never colors, spacing, or motion values. Cited to the designer for confirmation within a relevant interview question; never applied as a silent default. Linux doesn't have one of these yet — GNOME, elementary, and KDE each publish a separately-opinionated HIG, so doing this properly means three files, not one. |

**Each file covers exactly one standard, independently of the others.** This is deliberate, not incidental: if you're extending or correcting the skill's handling of one domain (say, adding a missing ARIA pattern, or updating iOS coverage for a new HIG pattern), you should only ever need to touch that one file. SKILL.md's phases link to specific files by name rather than inlining this material, so:
- Fixing or extending coverage of an existing standard means editing the matching file only.
- Adding coverage for a standard not listed here means adding a new file (a new platform gets a new directory), not folding it into an existing one's scope.
- No reference file should assume or depend on the contents of another — each should make sense read on its own.
