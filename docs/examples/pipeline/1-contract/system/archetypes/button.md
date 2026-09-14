---
archetype: button
role: button
version: 1.0
---

# Archetype: button

| id | statement | observe | kind | required |
|---|---|---|---|---|
| BTN-01 | The control is exposed to assistive technology as a button. | role | state | always |
| BTN-02 | The control has a non-empty accessible name. | name | state | always |
| BTN-03 | The control is reachable by sequential focus navigation. | focus | state | always |
| BTN-05 | Where a hardware keyboard exists, both standard activation keys perform the action. | event | behavior | when:hardware_keyboard |
| BTN-08 | When disabled, the control is removed from sequential focus navigation. | focus | state | when:disabled |
| BTN-10 | When disabled, that state is conveyed to assistive technology. | state | state | when:disabled |
| BTN-11 | The control meets the platform's minimum touch-target size. | layout | state | when:touch_input |
| BTN-13 | The control submits its containing form without scripting. | event | behavior | when:inside_form |
