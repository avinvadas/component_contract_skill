---
role-archetype: button
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


| when | statement | observe | kind | chapter | source | id |
|---|---|---|---|---|---|---|
| always | The control is exposed to assistive technology as a button. | role | state | Accessibility | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button | id-BTN-01 |
| always | The control has a non-empty accessible name. | name | state | Accessibility | catalogue:Web/button · catalogue:iOS/Button | id-BTN-02 |
| when:enabled | The control is reachable by the platform's sequential focus navigation. | focus | state | Accessibility | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button | id-BTN-03 |
| when:enabled | Activating by the platform's primary non-pointer input performs the action. | event | behavior | Behavior | catalogue:iOS/Button · catalogue:Android/Button · catalogue:Web/button | id-BTN-04 |
| when:hardware_keyboard,enabled | Both of the platform's standard activation keys perform the action. | event | behavior | Behavior | catalogue:Web/button · catalogue:Android/Button | id-BTN-05 |
| when:hardware_keyboard | Keyboard activation does not also scroll the surrounding surface. | event | behavior | Behavior | catalogue:Web/button | id-BTN-06 |
| when:disabled | The control is removed from sequential focus navigation. | focus | state | Accessibility | catalogue:Web/button | id-BTN-08 |
| when:disabled | Activation performs no action. | event | behavior | Behavior | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button | id-BTN-09 |
| when:disabled | The disabled state is conveyed to assistive technology. | state | state | Accessibility | catalogue:Web/button · catalogue:iOS/Button · catalogue:Android/Button | id-BTN-10 |
| when:touch_input | The control meets the platform's minimum touch-target size. | layout | state | Structure | catalogue:Android/Button · hig:ios/layout · wcag:2.5.8 | id-BTN-11 |
| always | The accessible label scales with the platform's user text-size setting. | state | state | Appearance | catalogue:iOS/Button | id-BTN-12 |
| when:inside_form | The control submits its containing form without scripting. | event | behavior | Behavior | catalogue:Web/button | id-BTN-13 |


## BTN-03, 04 and 05 hold only while enabled

They were `always`, beside BTN-08 and BTN-09, which say the opposite for a disabled button. For a
disabled instance the two pairs cannot both hold, and nothing noticed until a verifier that could
really move focus ran them against a disabled Carbon button: "reachable by Tab" failed on the very
instance where being skipped is correct. A requirement that holds only while the control can be
used is conditioned `when:enabled`, the complement of `when:disabled`.

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
