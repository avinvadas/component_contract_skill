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


| id | statement | observe | kind | required | chapter | source |
|---|---|---|---|---|---|---|
| BTN-01 | The control is exposed to assistive technology as a button. | role | state | always | Accessibility | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button |
| BTN-02 | The control has a non-empty accessible name. | name | state | always | Accessibility | catalogue:Web/button · catalogue:iOS/Button |
| BTN-03 | The control is reachable by the platform's sequential focus navigation. | focus | state | always | Accessibility | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button |
| BTN-04 | Activating by the platform's primary non-pointer input performs the action. | event | behavior | always | Behavior | catalogue:iOS/Button · catalogue:Android/Button · catalogue:Web/button |
| BTN-05 | Where a hardware keyboard exists, both of its standard activation keys perform the action. | event | behavior | when:hardware_keyboard | Behavior | catalogue:Web/button · catalogue:Android/Button |
| BTN-06 | Keyboard activation does not also scroll the surrounding surface. | event | behavior | when:hardware_keyboard | Behavior | catalogue:Web/button |
| BTN-08 | When disabled, the control is removed from sequential focus navigation. | focus | state | when:disabled | Accessibility | catalogue:Web/button |
| BTN-09 | When disabled, activation performs no action. | event | behavior | when:disabled | Behavior | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button |
| BTN-10 | When disabled, that state is conveyed to assistive technology. | state | state | when:disabled | Accessibility | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button |
| BTN-11 | The control meets the platform's minimum touch-target size. | layout | state | when:touch_input | Structure | catalogue:Android/Button · hig:ios/layout · wcag:2.5.8 |
| BTN-12 | The accessible label scales with the platform's user text-size setting. | state | state | always | Appearance | catalogue:iOS/Button |
| BTN-13 | The control submits its containing form without scripting. | event | behavior | when:inside_form | Behavior | catalogue:Web/button |

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
