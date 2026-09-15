---
archetype: button
version: 1.0
platforms: [web, ios, android, macos]
kind: native-backed
---

# Archetype: button

A control that performs an action in place. It does not navigate — that is `link`, and the
asymmetry between them is load-bearing rather than incidental.

**Bundle kind: inherited.** Every requirement below is something at least one platform
provides automatically when you use its native control. That is what you must reproduce if
you substitute a generic view.
## Native backing

What each platform provides. `none` means every implementation builds the semantics by hand — the requirements below still bind.

| Platform | Native backing |
|---|---|
| web | `<button>` · `<input type=button|submit>` |
| ios | SwiftUI `Button` · `UIButton` |
| android | Compose `Button` · `android.widget.Button` |
| macos | SwiftUI `Button` · `NSButton` |


| statement | observe | kind | required | chapter | source | id |
|---|---|---|---|---|---|---|
| The control is exposed to assistive technology as a button. | role | state | always | Accessibility | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button | <sub>id-BTN-01</sub> |
| The control has a non-empty accessible name. | name | state | always | Accessibility | catalogue:Web/button · catalogue:iOS/Button | <sub>id-BTN-02</sub> |
| The control is reachable by the platform's sequential focus navigation. | focus | state | always | Accessibility | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button | <sub>id-BTN-03</sub> |
| Activating by the platform's primary non-pointer input performs the action. | event | behavior | always | Behavior | catalogue:iOS/Button · catalogue:Android/Button · catalogue:Web/button | <sub>id-BTN-04</sub> |
| Where a hardware keyboard exists, both of its standard activation keys perform the action. | event | behavior | when:hardware_keyboard | Behavior | catalogue:Web/button · catalogue:Android/Button | <sub>id-BTN-05</sub> |
| Keyboard activation does not also scroll the surrounding surface. | event | behavior | when:hardware_keyboard | Behavior | catalogue:Web/button | <sub>id-BTN-06</sub> |
| When disabled, the control is removed from sequential focus navigation. | focus | state | when:disabled | Accessibility | catalogue:Web/button | <sub>id-BTN-08</sub> |
| When disabled, activation performs no action. | event | behavior | when:disabled | Behavior | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button | <sub>id-BTN-09</sub> |
| When disabled, that state is conveyed to assistive technology. | state | state | when:disabled | Accessibility | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button | <sub>id-BTN-10</sub> |
| The control meets the platform's minimum touch-target size. | layout | state | when:touch_input | Structure | catalogue:Android/Button · hig:ios/layout · wcag:2.5.8 | <sub>id-BTN-11</sub> |
| The accessible label scales with the platform's user text-size setting. | state | state | always | Appearance | catalogue:iOS/Button | <sub>id-BTN-12</sub> |
| The control submits its containing form without scripting. | event | behavior | when:inside_form | Behavior | catalogue:Web/button | <sub>id-BTN-13</sub> |

## Deferred to policy

| Free behaviour | Deferred because |
|---|---|
| a platform-drawn focus indicator (`catalogue:Web/button` · `wcag:2.4.7`) | this is true of **every** focusable control, not of buttons specifically, so it belongs to system policy (POL-02). Restating it here would report one defect twice — F6 in the validation plan. The catalogue citation is preserved so the guarantee is not lost, only relocated. |

An archetype requirement that duplicates a policy requirement is a collision, and policy
wins: policy is what makes the rule non-negotiable across archetypes that have no native
backing at all.

## Notes on three entries

**BTN-05 is a condition, not a scope.** iOS has no Space key by default, but does under Full
Keyboard Access, and must comply there. Scoping it to `[web, android]` would excuse a platform
that can in fact meet the requirement.

**BTN-06 is separate from BTN-05 because they fail independently.** A generic element handling
`keydown` for Space almost always forgets to suppress the default, so the surface scrolls
while the action fires.

**BTN-13 is the only scoped entry.** No platform-level form-submission model exists off the
web — the concept has no referent, which is an exclusion rather than a weakening.
