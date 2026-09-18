# Component Contract Skill

A Claude skill for design systems teams. 
Answer a structured interview about a UI component, and it will generate a formal **component contract**: a markdown specification that captures the component's essence and puts it into semantic markup, design tokens, behavior, and accessibility requirements, making your component work *documentation-driven* early on in the process.

## What it generates

One interview, **one contract** per component, covering any combination of supported platforms (Web, iOS, Android, macOS) in a single document — plus the files generated from it.

```
ComponentName/
├── ComponentName.md                              # the contract — authored, six chapters
├── ComponentName.bindings.json                   # how each platform checks it
├── ComponentName.resolved.md                     # generated — what a person reads
├── canonical/
│   ├── ComponentName.web.canonical.json          # generated — one per platform
│   └── ComponentName.ios.canonical.json
└── ComponentName.Web.schema.json                 # optional props schema
```

- **`ComponentName.md`** — six chapters: **Intent**, **Structure**, **Composition**, **Appearance**, **Behavior**, **Accessibility**. Accessibility is its own chapter rather than a column, so it can be reviewed as an aspect in its own right. A requirement is written **once**, in plain language, and never names a platform's vocabulary: *"the control is reachable by the platform's sequential focus navigation"* is the requirement; that it is Tab on web and a swipe on iOS is a binding. One frontmatter line — `role-archetype: button` — inherits what every platform already guarantees for that role, so no contract restates it.

- **`ComponentName.bindings.json`** — per-platform `expect` values, and only where they are not derivable. A requirement with no referent on a platform carries `binds: false` **with a reason**, and still appears in that platform's output, so nothing can lower its own bar by omission.

- **`ComponentName.resolved.md`** *(generated)* — the reading artifact: the contract's own chapters with everything inherited resolved in, origin as a column, and any token gaps named with who fixes them.

- **`canonical/ComponentName.[platform].canonical.json`** *(generated, one per platform)* — an **interchange format**, not a test. It describes what must hold and what each fact needs in order to be observed; a verifier built on that platform's own tooling reads it, declares what it can and cannot observe, and reports `pass · fail · unverified · n/a`. Anything it cannot observe is named, never passed.

- **`ComponentName.[Platform].schema.json`** *(optional)* — JSON Schema validating a **consumer-supplied props instance**: is this a legal set of props? A different subject from everything above, and consumed by ordinary build tooling.

## Why it exists

A component contract captures **design intent**: what a component is and what it does, beneath its instances. Design intent is the stable ground beneath the ongoing cycle between design and engineering, and it can show up in more ways than a single tool captures at a given moment. The contract is a stable, explicit statement of that intent.

Two checkable artifacts come with it, and they check different subjects — worth keeping straight, since it's easy to credit one with the other's job. The **JSON schema** validates a consumer-supplied props instance (is this a legal set of props?). The **canonical document** describes what a real implementation must produce, for a verifier running that platform's own test framework to check against its rendered output — the live DOM, or a runtime accessibility tree — never against source code.

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
