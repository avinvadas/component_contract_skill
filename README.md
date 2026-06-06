# Component Contract Skill

A Claude skill for design systems teams. 
Answer a structured interview about a UI component, and it will generate a formal **component contract**: a markdown specification that captures the component's essence and puts it into semantic markup, design tokens, behavior, and accessibility requirements, making your component work *documentation-driven* early on in the process.

## What it generates

- **`ComponentName.md`**: a six-section specification:
  1. Overview: What the component is and what its purpose is. What it owns and what it delegates.
  2. Structure: Semantic HTML, ARIA, and composition zones (each zone typed as Content or Interaction, with cardinality and position rules)
  3. Properties: Layout props, visual variants, behavioral props (only what applies)
  4. Appearance: Interaction states, layout policy, design token map
  5. Behavior: Interaction events, state machine, emitted events
  6. Accessibility: ARIA roles, keyboard navigation, focus management, screen reader expectations

- **`ComponentName.schema.json`** *(optional)* — a JSON Schema Draft file for prop validation, derived directly from the contract

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

Claude will ask 14 structured questions, then generate the contract (and optionally the schema) directly.
