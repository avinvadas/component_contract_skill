# Component Contract Skill

A Claude skill for design systems teams. 
Answer a structured interview about a UI component, and it will generate a formal **component contract**: a markdown specification that captures the component's essence and puts it into semantic markup, design tokens, behavior, and accessibility requirements, making your component work *documentation-driven* early on in the process.

## What it generates

One interview, **one contract file** per component, covering any combination of target platforms (Web, iOS, Android, macOS, Windows, Linux) within that single document — plus one JSON Schema file per platform, since schemas are consumed by each platform's own separate build process.

```
ComponentName/
├── ComponentName.md                  # the one contract — every platform, one document
├── ComponentName.Web.schema.json     # per platform, optional
└── ComponentName.iOS.schema.json
```

- **`ComponentName.md`** — the entire contract, across six sections. Sections that describe *intent* (Overview, Composition Zones, Properties, Layout Policy, Design Tokens, State Machine, Focus Management) are written once. Sections that are structurally platform-specific (Semantic Markup, Events Emitted/Received, Accessibility Roles & Attributes) hold one row per targeted platform, in the same table, right next to each other — never a separate file per platform, and never a value merged across platforms or left to be inferred ("same as Web"). A handful of sections (Adaptive Layout, Interaction States, Interactions, Keyboard/Gesture Navigation, Screen Reader expectations) are shared by default and only pick up a platform-specific note where an actual difference exists. The file opens with YAML frontmatter (component name, version, status, platforms) rather than a bespoke metadata block, so both a person and an agent reading it as implementation context can rely on the same standard convention.

- **`ComponentName.[Platform].schema.json`** *(optional, one per platform)* — a JSON Schema Draft file for prop validation. Its content is typically identical across a component's platforms, since it's derived entirely from sections that don't vary by platform — it's split into separate files because each platform's build tooling consumes its own schema as a separate compile-time step, not because the data differs.

A single-platform component still gets this same directory shape — the one contract file plus one schema file — so adding a second platform later means editing the existing contract's tables to add a row, and dropping in one more schema file, never restructuring what's already there.

## Why it exists

Component documentation decays because it lives in the wrong place — Figma descriptions, Notion pages, or engineers' heads. A component contract lives alongside the component itself and answers the questions that actually cause design–engineering drift: *Can this zone be moved? Is this element interactive or decorative? What tokens are bound here? What happens on Escape?*

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

Claude will ask 10 main questions, plus a handful of conditional follow-ups depending on your answers (e.g. how many platforms you selected, or whether the component holds sub-components), then generate the contract (and optionally the schema) directly.

## Reference material (`references/`)

The skill's technical derivations (markup, accessibility, layout mechanics, token formats, JSON Schema) are grounded in external, design-system-agnostic standards, not invented rules. `references/` is organized by scope — platform-specific standards live under a directory named for that platform; standards that apply regardless of platform stay at the root:

| File | Standard |
|---|---|
| `design-tokens-format.md` | DTCG token format, plus Style Dictionary / CSS custom properties / Tailwind |
| `figma-variables-model.md` | Figma's Collections/Modes/variable-binding model |
| `json-schema-draft-07.md` | JSON Schema Draft 07 |
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

**Each file covers exactly one standard, independently of the others.** This is deliberate, not incidental: if you're extending or correcting the skill's handling of one domain (say, adding a missing ARIA pattern, or updating iOS coverage for a new HIG pattern), you should only ever need to touch that one file. SKILL.md's phases link to specific files by name rather than inlining this material, so:
- Fixing or extending coverage of an existing standard means editing the matching file only.
- Adding coverage for a standard not listed here means adding a new file (a new platform gets a new directory), not folding it into an existing one's scope.
- No reference file should assume or depend on the contents of another — each should make sense read on its own.
