---
archetype: button
role: button
version: 1.0
platforms: [web, ios, android, macos]
source: v1-implicit-guarantees-catalogue.md
---

# Archetype: button

A control that performs an action when activated. It does not navigate — that is `link`.

| id | statement | observe | kind | required | scope |
|---|---|---|---|---|---|
| BTN-01 | The control is exposed to assistive technology as a button. | role | state | always | all |
| BTN-02 | The control has a non-empty accessible name. | name | state | always | all |
| BTN-03 | The control is reachable by the platform's sequential focus navigation. | focus | state | always | all |
| BTN-04 | Activating by the platform's primary non-pointer input performs the action. | event | behavior | always | all |
| BTN-05 | Where a hardware keyboard exists, both standard activation keys perform the action. | event | behavior | when a hardware keyboard is present | all |
| BTN-06 | Keyboard activation does not also scroll the surrounding surface. | event | behavior | when a hardware keyboard is present | all |
| BTN-07 | While focused, a focus indicator is distinguishable from the unfocused appearance. | state | state | always | all |
| BTN-08 | When disabled, the control is removed from sequential focus navigation. | focus | state | when disabled | all |
| BTN-09 | When disabled, activation performs no action. | event | behavior | when disabled | all |
| BTN-10 | When disabled, that state is conveyed to assistive technology. | state | state | when disabled | all |
| BTN-11 | The control meets the platform's minimum touch-target size. | layout | state | on touch-capable platforms | all |
| BTN-13 | The control submits its containing form without scripting. | event | behavior | when inside a form | **web** |

> BTN-13 is scoped: no platform-level form model exists off the web. The concept has no
> referent there — an exclusion, not a weakening.
> BTN-05 is deliberately *not* scoped: iOS has no Space key by default, but does under
> Full Keyboard Access, and must comply. A condition, not an exclusion.
